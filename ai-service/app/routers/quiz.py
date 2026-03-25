"""
Quiz Router — generates quiz questions from stored document context.
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.services.quiz_generator import get_quiz_generator
from app.models.schemas import ErrorResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/generate-quiz",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_quiz(
    session_id: str = Query(..., description="Session ID from document upload"),
    topic: str = Query(..., min_length=2, description="Topic for quiz generation"),
    num_questions: int = Query(5, ge=1, le=20, description="Number of questions to generate"),
):
    """
    Generate quiz questions using RAG.

    Retrieves relevant chunks from the uploaded document,
    then uses the LLM to generate multiple-choice questions.
    Strict guardrails prevent hallucination.
    """
    logger.info(f"Quiz request: session={session_id}, topic='{topic}', n={num_questions}")

    try:
        generator = get_quiz_generator()
        result = generator.generate_quiz(
            session_id=session_id,
            topic=topic,
            num_questions=num_questions,
        )

        if result["status"] == "INSUFFICIENT_CONTEXT":
            return {
                "status": "INSUFFICIENT_CONTEXT",
                "session_id": session_id,
                "topic": topic,
                "message": result["message"],
                "questions": [],
            }

        return {
            "status": "success",
            "session_id": session_id,
            "topic": topic,
            "questions": result["questions"],
            "source_chunks_used": result["source_chunks_used"],
        }

    except Exception as e:
        logger.exception(f"Quiz generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {e}")
