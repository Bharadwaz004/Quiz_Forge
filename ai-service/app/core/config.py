"""
Configuration — all settings loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # --- Service ---
    SERVICE_NAME: str = "ai-service"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = False

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_PREFIX: str = "quiz_docs"

    # --- Embedding Model ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # --- LLM (Qwen2.5-3B-Instruct — local HuggingFace) ---
    LLM_MODEL: str = "Qwen/Qwen2.5-3B-Instruct"
    LLM_DEVICE: str = "cpu"
    LLM_MAX_NEW_TOKENS: int = 600
    LLM_TEMPERATURE: float = 0.3

    # --- RAG ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    RETRIEVAL_TOP_K: int = 3
    MIN_RELEVANCE_SCORE: float = 0.3

    # --- Upload ---
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

print(f"[DEBUG CONFIG] LLM_MODEL: {settings.LLM_MODEL}")
print(f"[DEBUG CONFIG] LLM_DEVICE: {settings.LLM_DEVICE}")
print(f"[DEBUG CONFIG] LLM_MAX_NEW_TOKENS: {settings.LLM_MAX_NEW_TOKENS}")
print(f"[DEBUG CONFIG] LLM_TEMPERATURE: {settings.LLM_TEMPERATURE}")
print(f"[DEBUG CONFIG] RETRIEVAL_TOP_K: {settings.RETRIEVAL_TOP_K}")