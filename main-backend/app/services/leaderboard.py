"""
Leaderboard Service
===================
Computes and returns ranked leaderboards from MongoDB answer data.
"""

import logging
from typing import List, Dict

from app.core.database import get_db

logger = logging.getLogger(__name__)


async def compute_leaderboard(session_id: str) -> List[Dict]:
    """
    Aggregate answers for a session into a ranked leaderboard.
    Returns list sorted by score desc, then accuracy desc.
    """
    db = get_db()

    pipeline = [
        {"$match": {"session_id": session_id}},
        {
            "$group": {
                "_id": "$user_name",
                "score": {"$sum": {"$cond": ["$correct", 1, 0]}},
                "total_answered": {"$sum": 1},
            }
        },
        {
            "$project": {
                "user_name": "$_id",
                "score": 1,
                "total_answered": 1,
                "accuracy": {
                    "$round": [
                        {"$multiply": [{"$divide": ["$score", "$total_answered"]}, 100]},
                        1,
                    ]
                },
                "_id": 0,
            }
        },
        {"$sort": {"score": -1, "accuracy": -1}},
    ]

    cursor = db.answers.aggregate(pipeline)
    leaderboard = await cursor.to_list(length=100)
    return leaderboard
