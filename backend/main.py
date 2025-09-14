"""
AInBox Backend - Email Analysis System with AI
Main FastAPI application entry point
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.api.routes import api_router
from app.websocket.manager import websocket_manager
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting AInBox Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize rate limiter
    try:
        await FastAPILimiter.init(
            redis_url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL
        )
        logger.info("Rate limiter initialized successfully")
    except Exception as e:
        logger.warning(f"Rate limiter initialization failed: {e}. Using fallback mode.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AInBox Backend...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title="AInBox API",
        description="Email Analysis System with AI using Google Gemini",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rate limiting is handled by fastapi-limiter decorators
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket):
        """
        WebSocket endpoint for real-time communication
        """
        await websocket_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket_manager.disconnect(websocket)
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
