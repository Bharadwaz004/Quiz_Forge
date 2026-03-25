"""
Real-Time Service (Socket.IO)
=============================
Handles WebSocket connections for:
  - Players joining quiz session rooms
  - Broadcasting leaderboard updates on answer submission
  - Session-scoped event routing
"""

import logging
import socketio

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=False,
    engineio_logger=False,
)

# Track connected users per session: {session_id: {sid: user_name}}
session_users: dict[str, dict[str, str]] = {}


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit("connected", {"sid": sid}, to=sid)


@sio.event
async def disconnect(sid):
    # Remove user from all session rooms they were in
    for session_id, users in list(session_users.items()):
        if sid in users:
            user_name = users.pop(sid)
            logger.info(f"User '{user_name}' left session {session_id}")
            await sio.emit(
                "player_left",
                {"user_name": user_name, "players": list(users.values())},
                room=session_id,
            )
            if not users:
                del session_users[session_id]
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def join_session(sid, data):
    """
    Player joins a quiz session room.
    Expected data: {"session_id": "abc123", "user_name": "Alice"}
    """
    session_id = data.get("session_id")
    user_name = data.get("user_name")

    if not session_id or not user_name:
        await sio.emit("error", {"message": "session_id and user_name required"}, to=sid)
        return

    # Join the Socket.IO room
    sio.enter_room(sid, session_id)

    # Track user
    if session_id not in session_users:
        session_users[session_id] = {}
    session_users[session_id][sid] = user_name

    players = list(session_users[session_id].values())
    logger.info(f"User '{user_name}' joined session {session_id} ({len(players)} players)")

    # Notify the room
    await sio.emit(
        "player_joined",
        {"user_name": user_name, "players": players},
        room=session_id,
    )


@sio.event
async def leave_session(sid, data):
    """Player leaves a quiz session room."""
    session_id = data.get("session_id")
    if session_id and session_id in session_users:
        user_name = session_users[session_id].pop(sid, None)
        sio.leave_room(sid, session_id)
        if user_name:
            players = list(session_users[session_id].values())
            await sio.emit(
                "player_left",
                {"user_name": user_name, "players": players},
                room=session_id,
            )


async def broadcast_leaderboard(session_id: str, leaderboard: list):
    """
    Broadcast updated leaderboard to all users in a session room.
    Called by the answer submission endpoint.
    """
    await sio.emit(
        "leaderboard_update",
        {"session_id": session_id, "leaderboard": leaderboard},
        room=session_id,
    )
    logger.info(f"Leaderboard broadcast to session {session_id} ({len(leaderboard)} entries)")


async def broadcast_answer_submitted(session_id: str, user_name: str, question_index: int):
    """Notify room that a player submitted an answer (for live activity feed)."""
    await sio.emit(
        "answer_submitted",
        {
            "session_id": session_id,
            "user_name": user_name,
            "question_index": question_index,
        },
        room=session_id,
    )
