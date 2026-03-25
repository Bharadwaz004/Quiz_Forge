"""
Leaderboard Router
==================
Fetch current leaderboard standings for a quiz session.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.core.database import get_db
from app.models.schemas import LeaderboardResponse, ErrorResponse
from app.services.leaderboard import compute_leaderboard

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/leaderboard/{session_id}",
    response_model=LeaderboardResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_leaderboard(session_id: str):
    """Get the current leaderboard for a quiz session."""
    db = get_db()

    session = await db.sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    leaderboard = await compute_leaderboard(session_id)

    return LeaderboardResponse(
        session_id=session_id,
        leaderboard=leaderboard,
        total_questions=session.get("num_questions", 0),
    )
