"""
Data models for the main backend API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ───────────────────── Session ─────────────────────

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    answer: str


class CreateSessionRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=200)


class SessionResponse(BaseModel):
    session_id: str
    topic: str
    questions: List[QuizQuestion]
    num_questions: int
    created_at: str
    status: str  # "active", "completed"
    players: List[str] = []


class SessionListItem(BaseModel):
    session_id: str
    topic: str
    num_questions: int
    created_at: str
    status: str
    player_count: int


# ───────────────────── Answer ─────────────────────

class SubmitAnswerRequest(BaseModel):
    session_id: str
    user_name: str = Field(..., min_length=1, max_length=50)
    question_index: int = Field(..., ge=0)
    selected_answer: str


class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    user_name: str
    question_index: int


# ───────────────────── Leaderboard ─────────────────────

class LeaderboardEntry(BaseModel):
    user_name: str
    score: int
    total_answered: int
    accuracy: float  # percentage


class LeaderboardResponse(BaseModel):
    session_id: str
    leaderboard: List[LeaderboardEntry]
    total_questions: int


# ───────────────────── Errors ─────────────────────

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
