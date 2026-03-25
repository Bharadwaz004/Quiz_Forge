"""
Answers Router
==============
Handles answer submission, scoring, and triggers real-time leaderboard updates.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.core.database import get_db
from app.models.schemas import SubmitAnswerRequest, AnswerResponse, ErrorResponse
from app.services.leaderboard import compute_leaderboard
from app.services.realtime import broadcast_leaderboard, broadcast_answer_submitted

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/submit-answer",
    response_model=AnswerResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def submit_answer(req: SubmitAnswerRequest):
    """
    Submit an answer for a quiz question.
      1. Validate session and question index
      2. Check for duplicate submissions
      3. Score the answer
      4. Store in MongoDB
      5. Broadcast updated leaderboard via Socket.IO
    """
    db = get_db()

    # Fetch session
    session = await db.sessions.find_one({"session_id": req.session_id})
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found.")

    questions = session.get("questions", [])
    if req.question_index < 0 or req.question_index >= len(questions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid question index {req.question_index}. Session has {len(questions)} questions.",
        )

    # Prevent duplicate answers for the same question by the same user
    existing = await db.answers.find_one({
        "session_id": req.session_id,
        "user_name": req.user_name,
        "question_index": req.question_index,
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"User '{req.user_name}' already answered question {req.question_index}.",
        )

    # Score the answer
    correct_answer = questions[req.question_index]["answer"]
    is_correct = req.selected_answer.strip() == correct_answer.strip()

    # Store answer
    answer_doc = {
        "session_id": req.session_id,
        "user_name": req.user_name,
        "question_index": req.question_index,
        "selected_answer": req.selected_answer,
        "correct": is_correct,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.answers.insert_one(answer_doc)

    logger.info(
        f"Answer: user='{req.user_name}' session={req.session_id} "
        f"q={req.question_index} correct={is_correct}"
    )

    # Compute and broadcast updated leaderboard
    try:
        lb = await compute_leaderboard(req.session_id)
        await broadcast_leaderboard(req.session_id, lb)
        await broadcast_answer_submitted(req.session_id, req.user_name, req.question_index)
    except Exception as e:
        logger.warning(f"Leaderboard broadcast failed (non-fatal): {e}")

    return AnswerResponse(
        correct=is_correct,
        correct_answer=correct_answer,
        user_name=req.user_name,
        question_index=req.question_index,
    )
