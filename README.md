# QuizForge — Multi-User RAG-Based Quiz Platform

A production-ready full-stack application where organizers upload a PDF, the system generates quiz questions **exclusively from the document** using RAG (Retrieval-Augmented Generation), and multiple users compete in real-time with a live leaderboard.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│   Vite · Tailwind CSS · Socket.IO Client · Framer Motion        │
│                        Port 5173 / 3000                         │
└──────────────────────┬──────────────────┬───────────────────────┘
                       │ REST             │ WebSocket
                       ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MAIN BACKEND (FastAPI)                         │
│   Session CRUD · Answer Scoring · Leaderboard · Socket.IO       │
│   Motor (async MongoDB) · httpx (AI service client)             │
│                        Port 8000                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (FastAPI)                          │
│   PDF Extract · Chunking · Embeddings · ChromaDB · LLM Gen     │
│   SentenceTransformers · Qwen2.5-3B-Instruct                   │
│                        Port 8001                                │
└─────────────────────────────────────────────────────────────────┘
                       │
          ┌────────────┘
          ▼            ▼
     [ChromaDB]   [MongoDB]
     (vectors*)   (sessions)

* ChromaDB vectors are auto-deleted after quiz generation
```

## Tech Stack

| Layer       | Technology                                              |
|-------------|---------------------------------------------------------|
| Frontend    | React 18, Vite, Tailwind CSS, Socket.IO Client, Framer Motion |
| Backend     | FastAPI, Python-SocketIO, Motor (async MongoDB), httpx  |
| AI / RAG    | SentenceTransformers (`all-MiniLM-L6-v2`), ChromaDB, Qwen2.5-3B-Instruct |
| Database    | MongoDB 7                                                |
| Deployment  | Docker, Docker Compose, Nginx                            |

## LLM: Qwen2.5-3B-Instruct

The platform uses [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) for quiz generation. This model was chosen because:

- **Excellent structured output** — reliably produces valid JSON on the first attempt
- **Native chat template** — uses ChatML format via `tokenizer.apply_chat_template()` for proper instruction following
- **3B parameter size** — runs on CPU without a GPU (though generation takes ~2-4 minutes per quiz)
- **First download is ~6GB** — cached locally after the initial run

> **Note**: On CPU, quiz generation takes approximately 2-4 minutes for 3 questions. For faster generation, consider using a GPU (`LLM_DEVICE=cuda`) or switching to an API-based LLM.

## Anti-Hallucination Guardrails (3-Layer System)

1. **Retrieval Gate**: Top-k=3 with MMR (Maximal Marginal Relevance) re-ranking. If no chunks pass the minimum relevance score (0.3 cosine similarity), returns `INSUFFICIENT_CONTEXT`.
2. **Prompt Constraint**: The system prompt explicitly forbids using external knowledge. The LLM must only use the provided context and output `INSUFFICIENT_CONTEXT` if context is insufficient.
3. **Output Validation**: JSON extraction with 4-stage fallback (direct parse → markdown strip → regex → brace extraction), structural validation (4 options per question, 1 correct answer), and up to 2 retry attempts. A deterministic fallback generates questions directly from chunks if the LLM fails.

## Auto-Cleanup

The platform automatically cleans up temporary data to avoid disk bloat:

- **PDF files** — deleted immediately after text extraction and embedding (in `/upload`)
- **ChromaDB vectors** — deleted immediately after quiz questions are generated (in `/generate-quiz`)
- **Quiz data** — questions and answers persist in MongoDB for active gameplay

---

## Quick Start (Docker)

```bash
# Clone the project
git clone https://github.com/Bharadwaz004/Quiz_Forge.git
cd Quiz_Forge

# Build and start all services
docker compose up --build

# Services will be available at:
#   Frontend:     http://localhost:3000
#   Main Backend: http://localhost:8000
#   AI Service:   http://localhost:8001
#   MongoDB:      localhost:27017
```

> **Note**: First run downloads the embedding model (~90MB) and LLM (~6GB). Allow 10-15 minutes.

## Local Development (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB running locally
- Git

#### Start MongoDB

If MongoDB isn't installed locally, run it via Docker:

```bash
docker run -d -p 27017:27017 --name quiz-mongo mongo:7
```

### 1. AI Service

**Linux / macOS:**
```bash
cd ai-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
# → Running on http://localhost:8001
```

**Windows (CMD):**
```cmd
cd ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

**Windows (PowerShell):**
```powershell
cd ai-service
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py
```

> If your `.env` file isn't loading (common in VS Code terminals), set environment variables directly:
> ```cmd
> set LLM_MODEL=Qwen/Qwen2.5-3B-Instruct
> set LLM_MAX_NEW_TOKENS=600
> set LLM_TEMPERATURE=0.3
> set RETRIEVAL_TOP_K=3
> python run.py
> ```

### 2. Main Backend (separate terminal)

**Linux / macOS:**
```bash
cd main-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ensure MONGO_URI=mongodb://localhost:27017
python run.py
# → Running on http://localhost:8000
```

**Windows (CMD):**
```cmd
cd main-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

> Make sure `.env` has:
> ```
> MONGO_URI=mongodb://localhost:27017
> AI_SERVICE_URL=http://localhost:8001
> ```

### 3. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
# → Running on http://localhost:5173
```

### Using the App

1. Open **http://localhost:5173**
2. Click **"Create a Quiz"** → upload a PDF + enter a topic
3. Wait for quiz generation (~2-4 min on CPU) — the progress indicator shows the current step
4. Copy the **Session ID** and share with players
5. Players click **"Join a Session"** → enter the Session ID + their name
6. Answer questions one-by-one with instant correct/incorrect feedback
7. Live leaderboard updates in real-time via WebSocket

---

## API Documentation

### AI Service (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/api/upload` | POST | Upload PDF for processing |
| `/api/generate-quiz` | GET | Generate quiz from document |

#### `POST /api/upload`
Upload a PDF document for processing. The PDF is **auto-deleted** after text extraction.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file`    | File | PDF document (max 20MB) |

**Response:**
```json
{
  "session_id": "a1b2c3d4e5f6",
  "filename": "document.pdf",
  "num_chunks": 42,
  "status": "success",
  "message": "Document processed successfully. 42 chunks indexed."
}
```

#### `GET /api/generate-quiz`
Generate quiz questions using RAG. ChromaDB vectors are **auto-deleted** after generation.

| Parameter       | Type   | Description |
|-----------------|--------|-------------|
| `session_id`    | string | From upload response |
| `topic`         | string | Quiz topic |
| `num_questions` | int    | 1–20 (capped at 3 on CPU for speed) |

**Response (success):**
```json
{
  "status": "success",
  "session_id": "a1b2c3d4e5f6",
  "topic": "Machine Learning",
  "questions": [
    {
      "question": "What is supervised learning?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "A) ..."
    }
  ],
  "source_chunks_used": 3
}
```

**Response (insufficient context):**
```json
{
  "status": "INSUFFICIENT_CONTEXT",
  "message": "No relevant content found in the uploaded document for this topic."
}
```

---

### Main Backend (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/api/create-session` | POST | Upload PDF + generate quiz + store session |
| `/api/session/{id}` | GET | Fetch session details |
| `/api/session/{id}/join` | POST | Join as a player (returns questions without answers) |
| `/api/submit-answer` | POST | Submit answer + get instant feedback |
| `/api/leaderboard/{id}` | GET | Get current leaderboard |

#### `POST /api/create-session`
Create a quiz session (orchestrates upload → generation → storage).

| Parameter       | Type   | Description |
|-----------------|--------|-------------|
| `file`          | File   | PDF document |
| `topic`         | string | Quiz topic |
| `num_questions` | int    | 1–20, default 5 |

#### `POST /api/submit-answer`

```json
{
  "session_id": "a1b2c3d4e5f6",
  "user_name": "Alice",
  "question_index": 0,
  "selected_answer": "A) ..."
}
```

**Response:**
```json
{
  "correct": true,
  "correct_answer": "A) ...",
  "user_name": "Alice",
  "question_index": 0
}
```

---

### Socket.IO Events (Real-Time)

| Event               | Direction | Payload |
|---------------------|-----------|---------|
| `join_session`      | Client → Server | `{session_id, user_name}` |
| `leave_session`     | Client → Server | `{session_id}` |
| `player_joined`     | Server → Room   | `{user_name, players[]}` |
| `player_left`       | Server → Room   | `{user_name, players[]}` |
| `leaderboard_update`| Server → Room   | `{session_id, leaderboard[]}` |
| `answer_submitted`  | Server → Room   | `{session_id, user_name, question_index}` |

---

## MongoDB Collections

### `sessions`
```json
{
  "session_id": "a1b2c3d4e5f6",
  "topic": "Machine Learning",
  "questions": [{ "question": "...", "options": [...], "answer": "..." }],
  "num_questions": 3,
  "created_at": "2026-03-25T00:00:00Z",
  "status": "active",
  "players": ["Alice", "Bob"],
  "filename": "ml_textbook.pdf"
}
```

### `answers`
```json
{
  "session_id": "a1b2c3d4e5f6",
  "user_name": "Alice",
  "question_index": 0,
  "selected_answer": "A) ...",
  "correct": true,
  "submitted_at": "2026-03-25T00:01:00Z"
}
```

---

## Folder Structure

```
quiz-platform/
├── ai-service/                 # RAG microservice
│   ├── app/
│   │   ├── core/config.py      # Settings (env vars)
│   │   ├── models/schemas.py   # Pydantic models
│   │   ├── routers/
│   │   │   ├── upload.py       # PDF upload + auto-cleanup
│   │   │   └── quiz.py         # Quiz generation + vector cleanup
│   │   ├── services/
│   │   │   ├── pdf_processor.py    # Text extraction + chunking
│   │   │   ├── vector_store.py     # ChromaDB + embeddings + MMR
│   │   │   └── quiz_generator.py   # Qwen2.5 quiz gen + guardrails
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
├── main-backend/               # Session + leaderboard service
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # Settings
│   │   │   └── database.py     # MongoDB async connection
│   │   ├── models/schemas.py   # Pydantic models
│   │   ├── routers/
│   │   │   ├── sessions.py     # Create/fetch/join sessions
│   │   │   ├── answers.py      # Submit + score answers
│   │   │   └── leaderboard.py  # Leaderboard aggregation
│   │   ├── services/
│   │   │   ├── ai_client.py    # HTTP client for AI service
│   │   │   ├── leaderboard.py  # MongoDB aggregation pipeline
│   │   │   └── realtime.py     # Socket.IO events + rooms
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx      # Nav + footer
│   │   │   ├── Leaderboard.jsx # Animated leaderboard
│   │   │   └── QuestionCard.jsx# Question display + answer feedback
│   │   ├── pages/
│   │   │   ├── HomePage.jsx    # Landing page
│   │   │   ├── OrganizerPage.jsx # Upload PDF + create session
│   │   │   ├── PlayerPage.jsx  # Join a session
│   │   │   └── QuizPage.jsx    # Quiz gameplay + live leaderboard
│   │   ├── hooks/useSocket.js  # Socket.IO React hook
│   │   ├── lib/api.js          # Axios API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css           # Tailwind + custom styles
│   ├── Dockerfile
│   ├── nginx.conf              # Nginx config for SPA + API proxy
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Environment Variables

### AI Service

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `Qwen/Qwen2.5-3B-Instruct` | HuggingFace model ID |
| `LLM_DEVICE` | `cpu` | `cpu` or `cuda` for GPU |
| `LLM_MAX_NEW_TOKENS` | `600` | Max generation length |
| `LLM_TEMPERATURE` | `0.3` | Sampling temperature |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `CHUNK_SIZE` | `512` | Text chunk size for splitting |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `3` | Number of chunks retrieved per query |
| `MIN_RELEVANCE_SCORE` | `0.3` | Minimum cosine similarity threshold |
| `MAX_UPLOAD_SIZE_MB` | `20` | Max PDF file size |

### Main Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `quiz_platform` | Database name |
| `AI_SERVICE_URL` | `http://localhost:8001` | AI service address |

---

## Troubleshooting

**`.env` file not loading in VS Code?**
Set env vars directly in CMD before running: `set LLM_MODEL=Qwen/Qwen2.5-3B-Instruct`

**ChromaDB telemetry error?**
The `Failed to send telemetry event` error is harmless — it's just analytics failing to send. Does not affect functionality.

**Quiz generation is slow?**
On CPU, Qwen2.5-3B takes ~2-4 minutes for 3 questions. Options: use a GPU (`LLM_DEVICE=cuda`), switch to a GGUF quantized model, or use an API-based LLM (Anthropic/OpenAI) for near-instant generation.

**MongoDB connection refused?**
Make sure MongoDB is running: `docker run -d -p 27017:27017 --name quiz-mongo mongo:7`

---

## License

MIT