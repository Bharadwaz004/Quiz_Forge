"""
Data models for the AI service API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    answer: str


class QuizResponse(BaseModel):
    session_id: str
    topic: str
    questions: List[QuizQuestion]
    source_chunks_used: int
    status: str = "success"


class InsufficientContextResponse(BaseModel):
    session_id: str
    topic: str
    status: str = "INSUFFICIENT_CONTEXT"
    message: str = "Not enough relevant content in the document to generate quiz questions on this topic."


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    num_chunks: int
    status: str = "success"
    message: str


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None


class QuizDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
