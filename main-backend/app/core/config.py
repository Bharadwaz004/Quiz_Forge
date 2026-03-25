"""
Configuration for main backend service.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    SERVICE_NAME: str = "main-backend"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "quiz_platform"

    # AI Service URL
    AI_SERVICE_URL: str = "http://localhost:8001"


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
