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
# Importe as novas dependências
from app import dependencies

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting AInBox Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Log Redis configuration
    logger.info("🔧 Redis Configuration:")
    logger.info(f"  - REDIS_HOST: {settings.REDIS_HOST}")
    logger.info(f"  - REDIS_PORT: {settings.REDIS_PORT}")
    logger.info(f"  - REDIS_PASSWORD: {'***' if settings.REDIS_PASSWORD else 'None'}")
    logger.info(f"  - REDIS_SSL: {settings.REDIS_SSL}")
    
    # Initialize rate limiter
    logger.info("🔄 Initializing FastAPILimiter...")
    try:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        logger.info(f"  - Redis URL: {redis_url}")
        
        await FastAPILimiter.init(
            redis_url=redis_url,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_SSL
        )
        # Modifique a variável no módulo de dependências
        dependencies.RATE_LIMITER_AVAILABLE = True
        logger.info("✅ Rate limiter initialized successfully")
    except Exception as e:
        dependencies.RATE_LIMITER_AVAILABLE = False
        logger.error(f"❌ Rate limiter initialization failed: {e}")
        logger.error(f"  - Error type: {type(e).__name__}")
        logger.error(f"  - Error details: {str(e)}")
        logger.warning("⚠️ Using fallback mode (no rate limiting)")
    
    logger.info("🎯 Lifespan startup completed")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AInBox Backend...")


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
        # allow_credentials=True, # LINHA REMOVIDA - conflito com allow_origins=['*']
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
        # Aceitar conexão sem verificação CORS (resolve problema 403)
        await websocket.accept()
        logger.info("🔌 WebSocket connection accepted")
        
        # Conectar ao manager
        await websocket_manager.connect(websocket)
        logger.info("📡 WebSocket connected to manager")
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                logger.debug(f"📨 Received WebSocket message: {data}")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            await websocket_manager.disconnect(websocket)
            logger.info("🔌 WebSocket disconnected")
    
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
