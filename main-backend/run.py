#!/usr/bin/env python3
"""Run the main backend (with Socket.IO)."""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Use socket_app which wraps FastAPI with Socket.IO ASGI middleware
    uvicorn.run(
        "app.main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
