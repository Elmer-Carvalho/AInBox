"""
AInBox Backend - Email Analysis System with AI
Main FastAPI application entry point
"""

import os
import ssl
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import redis.asyncio as redis

from app.core.config import settings
from app.api.routes import api_router
from app.websocket.manager import websocket_manager
from fastapi_limiter import FastAPILimiter
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
    redis_pool = None
    try:
        # Aumentar o timeout de conexão para 30 segundos durante o startup
        # Isso dá mais tempo para a rede do Google Cloud se estabelecer
        connect_timeout = 30
        
        # Define o protocolo com base na configuração de SSL
        protocol = "rediss" if settings.REDIS_SSL else "redis"
        
        # Constrói o URL de conexão completo
        redis_connection_url = f"{protocol}://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        
        # Cria a conexão a partir do URL (compatível com redis==5.0.1)
        redis_pool = redis.from_url(
            redis_connection_url,
            encoding="utf-8", 
            decode_responses=True,
            socket_connect_timeout=connect_timeout
        )
        
        # Testa a conexão com PING
        await redis_pool.ping()
        logger.info(f"✅ Redis connection successful (PING successful within {connect_timeout}s timeout)")
        
        # Inicialização correta do FastAPILimiter
        await FastAPILimiter.init(redis_pool)
        
        dependencies.RATE_LIMITER_AVAILABLE = True
        logger.info("✅ Rate limiter initialized successfully")
    except Exception as e:
        dependencies.RATE_LIMITER_AVAILABLE = False
        logger.error(f"❌ Rate limiter initialization failed: {e}")
        logger.warning("⚠️ Using fallback mode (no rate limiting)")
    
    logger.info("🎯 Lifespan startup completed")
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AInBox Backend...")
    if redis_pool:
        await redis_pool.close()


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
    
    # Configuração de CORS simples, correta e funcional
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Incluir as rotas da API
    app.include_router(api_router, prefix="/api/v1")
    
    # Endpoint do WebSocket com validação de origem
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        WebSocket endpoint for real-time communication.
        Handles origin validation for secure connections.
        """
        # Validação de Origem
        origin = websocket.headers.get('origin')
        allowed_origins = settings.allowed_origins_list
        
        # Permite todas as origens se a configuração for "*"
        if "*" not in allowed_origins and origin not in allowed_origins:
            logger.warning(f"Conexão WebSocket rejeitada da origem não permitida: {origin}")
            await websocket.close(code=1008) # Policy Violation
            return

        # Procede com a conexão se a origem for válida
        connection_id = await websocket_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message on {connection_id}: {data}")
        except Exception as e:
            logger.error(f"WebSocket error on {connection_id}: {e}")
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
