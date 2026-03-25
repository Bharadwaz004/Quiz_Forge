"""
Sessions Router
===============
Endpoints for creating and fetching quiz sessions.
Orchestrates PDF upload → AI service → quiz generation → MongoDB storage.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from app.core.database import get_db
from app.services import ai_client
from app.models.schemas import SessionResponse, ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/create-session",
    response_model=SessionResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_session(
    file: UploadFile = File(..., description="PDF document to generate quiz from"),
    topic: str = Form(..., min_length=2, max_length=200, description="Quiz topic"),
    num_questions: int = Form(5, ge=1, le=20, description="Number of questions"),
):
    """
    Create a new quiz session:
      1. Upload PDF to AI service → get session_id
      2. Generate quiz questions via RAG
      3. Store session in MongoDB
      4. Return session details
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    db = get_db()
    content = await file.read()

    try:
        # Step 1: Upload document to AI service
        logger.info(f"Uploading document '{file.filename}' for topic '{topic}'")
        upload_result = await ai_client.upload_document(content, file.filename)
        session_id = upload_result["session_id"]

        # Step 2: Generate quiz
        logger.info(f"Generating quiz: session={session_id}, topic='{topic}'")
        quiz_result = await ai_client.generate_quiz(session_id, topic, num_questions)

        if quiz_result.get("status") == "INSUFFICIENT_CONTEXT":
            raise HTTPException(
                status_code=400,
                detail="The document doesn't contain enough relevant content for this topic. Try a different topic or a more detailed document.",
            )

        questions = quiz_result.get("questions", [])
        if not questions:
            raise HTTPException(status_code=400, detail="No questions could be generated.")

        # Step 3: Store in MongoDB
        session_doc = {
            "session_id": session_id,
            "topic": topic,
            "questions": questions,
            "num_questions": len(questions),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "players": [],
            "filename": file.filename,
        }
        await db.sessions.insert_one(session_doc)
        logger.info(f"Session created: {session_id} with {len(questions)} questions")

        return SessionResponse(
            session_id=session_id,
            topic=topic,
            questions=questions,
            num_questions=len(questions),
            created_at=session_doc["created_at"],
            status="active",
            players=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}")


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_session(session_id: str):
    """Fetch a quiz session by ID."""
    db = get_db()
    session = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})

    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionResponse(**session)


@router.post("/session/{session_id}/join")
async def join_session(session_id: str, user_name: str = Query(..., min_length=1, max_length=50)):
    """Register a player in a quiz session."""
    db = get_db()
    session = await db.sessions.find_one({"session_id": session_id})

    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    # Add player if not already in list
    if user_name not in session.get("players", []):
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$addToSet": {"players": user_name}},
        )

    # Return session without answers (players shouldn't see correct answers up front)
    questions_no_answers = [
        {"question": q["question"], "options": q["options"]}
        for q in session["questions"]
    ]

    return {
        "session_id": session_id,
        "topic": session["topic"],
        "questions": questions_no_answers,
        "num_questions": session["num_questions"],
        "status": session["status"],
    }
