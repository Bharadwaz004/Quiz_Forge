"""
AI Service - RAG-powered Quiz Generation Engine
================================================
FastAPI microservice handling:
  - PDF upload & text extraction
  - Document chunking & embedding generation
  - ChromaDB vector storage
  - Context retrieval with MMR
  - LLM-based quiz generation with strict guardrails
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers import upload, quiz
from app.services.vector_store import VectorStoreService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    logger.info("Initializing AI Service...")
    # Initialize the vector store singleton
    VectorStoreService.get_instance()
    logger.info("AI Service ready.")
    yield
    logger.info("Shutting down AI Service.")


app = FastAPI(
    title="Quiz Platform - AI Service",
    description="RAG-powered quiz generation from uploaded documents",
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

app.include_router(upload.router, prefix="/api", tags=["Document Upload"])
app.include_router(quiz.router, prefix="/api", tags=["Quiz Generation"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-service"}
