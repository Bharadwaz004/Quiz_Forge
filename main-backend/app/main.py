"""
Main Backend Service
====================
FastAPI + Socket.IO server handling:
  - Quiz session lifecycle (create, join, fetch)
  - Answer submission and scoring
  - Real-time leaderboard via Socket.IO
  - MongoDB persistence
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socketio

from app.core.config import settings
from app.core.database import connect_db, close_db
from app.routers import sessions, answers, leaderboard
from app.services.realtime import sio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to MongoDB on startup, disconnect on shutdown."""
    await connect_db()
    logger.info("Main Backend ready.")
    yield
    await close_db()
    logger.info("Main Backend shut down.")


# --- FastAPI app ---
app = FastAPI(
    title="Quiz Platform - Main Backend",
    description="Session management, scoring, and real-time leaderboard",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers ---
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(answers.router, prefix="/api", tags=["Answers"])
app.include_router(leaderboard.router, prefix="/api", tags=["Leaderboard"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "main-backend"}


# --- Socket.IO integration ---
# Wrap FastAPI with Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, app)