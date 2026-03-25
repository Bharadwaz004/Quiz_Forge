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
│   SentenceTransformers · HuggingFace Transformers               │
│                        Port 8001                                │
└─────────────────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     [ChromaDB]   [MongoDB]     [Redis]
     (vectors)    (sessions)   (pub/sub)
```

## Tech Stack

| Layer       | Technology                                              |
|-------------|---------------------------------------------------------|
| Frontend    | React 18, Vite, Tailwind CSS, Socket.IO Client          |
| Backend     | FastAPI, Python-SocketIO, Motor (MongoDB), httpx         |
| AI / RAG    | SentenceTransformers, ChromaDB, HuggingFace Transformers |
| Database    | MongoDB 7                                                |
| Cache       | Redis 7                                                  |
| Deployment  | Docker, Docker Compose, Nginx                            |

## Anti-Hallucination Guardrails (3-Layer System)

1. **Retrieval Gate**: Top-k=5 with MMR re-ranking. If no chunks pass the minimum relevance score (0.3), returns `INSUFFICIENT_CONTEXT`.
2. **Prompt Constraint**: The LLM prompt explicitly forbids using external knowledge. It must output `INSUFFICIENT_CONTEXT` if context is insufficient.
3. **Output Validation**: JSON extraction with regex fallbacks, structural validation (4 options, 1 answer), and up to 3 retry attempts. A deterministic fallback generates questions directly from chunks if the LLM fails.

---

## Quick Start (Docker)

```bash
# Clone and enter the project
cd quiz-platform

# Build and start all services
docker compose up --build

# Services will be available at:
#   Frontend:     http://localhost:3000
#   Main Backend: http://localhost:8000
#   AI Service:   http://localhost:8001
#   MongoDB:      localhost:27017
#   Redis:        localhost:6379
```

> **Note**: First run downloads the embedding model (~90MB) and LLM (~2GB). Allow 5–10 minutes.

## Local Development (Without Docker)

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB running locally
- Redis running locally (optional)

### 1. AI Service

```bash
cd ai-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if needed

python run.py
# → Running on http://localhost:8001
```

### 2. Main Backend

```bash
cd main-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if needed

python run.py
# → Running on http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → Running on http://localhost:5173
```

---

## API Documentation

### AI Service (Port 8001)

#### `POST /api/upload`
Upload a PDF document for processing.

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
Generate quiz questions using RAG.

| Parameter       | Type   | Description |
|-----------------|--------|-------------|
| `session_id`    | string | From upload response |
| `topic`         | string | Quiz topic |
| `num_questions` | int    | 1–20, default 5 |

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
  "source_chunks_used": 5
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

#### `POST /api/create-session`
Create a quiz session (uploads PDF + generates quiz).

| Parameter       | Type   | Description |
|-----------------|--------|-------------|
| `file`          | File   | PDF document |
| `topic`         | string | Quiz topic |
| `num_questions` | int    | 1–20, default 5 |

#### `GET /api/session/{session_id}`
Fetch session details including questions.

#### `POST /api/session/{session_id}/join?user_name=Alice`
Join a session as a player. Returns questions **without answers**.

#### `POST /api/submit-answer`
Submit an answer and receive immediate feedback.

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

#### `GET /api/leaderboard/{session_id}`
Fetch the current leaderboard.

---

### Socket.IO Events

| Event               | Direction | Payload |
|---------------------|-----------|---------|
| `join_session`      | Client→Server | `{session_id, user_name}` |
| `leave_session`     | Client→Server | `{session_id}` |
| `player_joined`     | Server→Room   | `{user_name, players[]}` |
| `player_left`       | Server→Room   | `{user_name, players[]}` |
| `leaderboard_update`| Server→Room   | `{session_id, leaderboard[]}` |
| `answer_submitted`  | Server→Room   | `{session_id, user_name, question_index}` |

---

## MongoDB Collections

### `sessions`
```json
{
  "session_id": "a1b2c3d4e5f6",
  "topic": "Machine Learning",
  "questions": [{ "question": "...", "options": [...], "answer": "..." }],
  "num_questions": 5,
  "created_at": "2024-01-01T00:00:00Z",
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
  "submitted_at": "2024-01-01T00:01:00Z"
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
│   │   │   ├── upload.py       # PDF upload endpoint
│   │   │   └── quiz.py         # Quiz generation endpoint
│   │   ├── services/
│   │   │   ├── pdf_processor.py    # Text extraction + chunking
│   │   │   ├── vector_store.py     # ChromaDB + embeddings + MMR
│   │   │   └── quiz_generator.py   # LLM quiz gen + guardrails
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
├── main-backend/               # Session + leaderboard service
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # Settings
│   │   │   └── database.py     # MongoDB connection
│   │   ├── models/schemas.py   # Pydantic models
│   │   ├── routers/
│   │   │   ├── sessions.py     # Create/fetch sessions
│   │   │   ├── answers.py      # Submit + score answers
│   │   │   └── leaderboard.py  # Leaderboard endpoint
│   │   ├── services/
│   │   │   ├── ai_client.py    # HTTP client for AI service
│   │   │   ├── leaderboard.py  # Aggregation pipeline
│   │   │   └── realtime.py     # Socket.IO events
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── run.py
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx
│   │   │   ├── Leaderboard.jsx
│   │   │   └── QuestionCard.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   ├── OrganizerPage.jsx
│   │   │   ├── PlayerPage.jsx
│   │   │   └── QuizPage.jsx
│   │   ├── hooks/useSocket.js
│   │   ├── lib/api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
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
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `LLM_MODEL` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | HuggingFace LLM |
| `LLM_DEVICE` | `cpu` | `cpu` or `cuda` |
| `CHUNK_SIZE` | `512` | Text chunk size |
| `RETRIEVAL_TOP_K` | `5` | Chunks retrieved per query |

### Main Backend
| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `AI_SERVICE_URL` | `http://localhost:8001` | AI service address |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |

---

## License

MIT
