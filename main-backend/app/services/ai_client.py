"""
AI Service Client
=================
HTTP client for communicating with the AI microservice.
Handles PDF upload forwarding and quiz generation requests.
"""

import logging
import httpx
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# No timeout — CPU inference on Qwen2.5-3B can take 15-20 minutes
TIMEOUT = httpx.Timeout(timeout=None, connect=30.0)


async def upload_document(file_content: bytes, filename: str) -> Dict:
    """Forward PDF upload to AI service and return session_id + metadata."""
    url = f"{settings.AI_SERVICE_URL}/api/upload"
    print(f"[DEBUG ai_client.upload] POST {url}, file={filename}, size={len(file_content)}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        files = {"file": (filename, file_content, "application/pdf")}
        response = await client.post(url, files=files)
        print(f"[DEBUG ai_client.upload] Response: {response.status_code}")

        if response.status_code != 200:
            print(f"[DEBUG ai_client.upload] ERROR: {response.text[:500]}")
            detail = response.json().get("detail", response.text)
            raise Exception(f"AI service error: {detail}")

        result = response.json()
        print(f"[DEBUG ai_client.upload] Result: {result}")
        return result


async def generate_quiz(session_id: str, topic: str, num_questions: int = 5) -> Dict:
    """Request quiz generation from the AI service."""
    url = f"{settings.AI_SERVICE_URL}/api/generate-quiz"
    params = {
        "session_id": session_id,
        "topic": topic,
        "num_questions": num_questions,
    }
    print(f"[DEBUG ai_client.generate_quiz] GET {url}, params={params}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params)
        print(f"[DEBUG ai_client.generate_quiz] Response: {response.status_code}")

        if response.status_code != 200:
            print(f"[DEBUG ai_client.generate_quiz] ERROR: {response.text[:500]}")
            detail = response.json().get("detail", response.text)
            raise Exception(f"AI service error: {detail}")

        result = response.json()
        print(f"[DEBUG ai_client.generate_quiz] Result status: {result.get('status')}, questions: {len(result.get('questions', []))}")
        return result