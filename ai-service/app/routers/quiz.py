"""
Quiz Router — generates quiz questions from stored document context.
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.services.quiz_generator import get_quiz_generator
from app.services.vector_store import VectorStoreService
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
    print(f"\n[DEBUG /generate-quiz] REQUEST RECEIVED: session={session_id}, topic='{topic}', n={num_questions}")

    try:
        print(f"[DEBUG /generate-quiz] Getting quiz generator...")
        generator = get_quiz_generator()
        print(f"[DEBUG /generate-quiz] Generator ready, calling generate_quiz...")
        result = generator.generate_quiz(
            session_id=session_id,
            topic=topic,
            num_questions=num_questions,
        )
        print(f"[DEBUG /generate-quiz] generate_quiz returned: status={result.get('status')}, questions={len(result.get('questions', []))}")

        if result["status"] == "INSUFFICIENT_CONTEXT":
            print(f"[DEBUG /generate-quiz] Returning INSUFFICIENT_CONTEXT")
            return {
                "status": "INSUFFICIENT_CONTEXT",
                "session_id": session_id,
                "topic": topic,
                "message": result["message"],
                "questions": [],
            }

        print(f"[DEBUG /generate-quiz] Returning SUCCESS with {len(result['questions'])} questions")

        # Cleanup: delete ChromaDB vectors — questions are generated, vectors no longer needed
        try:
            vs = VectorStoreService.get_instance()
            vs.delete_session(session_id)
            print(f"[CLEANUP] Deleted ChromaDB vectors for session {session_id}")
        except Exception as e:
            print(f"[CLEANUP] Could not delete vectors: {e}")

        return {
            "status": "success",
            "session_id": session_id,
            "topic": topic,
            "questions": result["questions"],
            "source_chunks_used": result["source_chunks_used"],
        }

    except Exception as e:
        print(f"[DEBUG /generate-quiz] EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {e}")