"""
AInBox Backend - Email Analysis System with AI
Main FastAPI application entry point
"""

import os
import json
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
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
            redis=redis_url,
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
    
    # Configure CORS - Configuração otimizada para WebSockets e Google Cloud Run
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permite qualquer origem
        allow_credentials=False,  # Deve ser False quando allow_origins=["*"]
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Origin",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
            "Sec-WebSocket-Key",
            "Sec-WebSocket-Version",
            "Sec-WebSocket-Protocol",
            "Sec-WebSocket-Extensions",
            "Sec-WebSocket-Accept",
            "Connection",
            "Upgrade",
            "Cache-Control",
            "Pragma"
        ],
        expose_headers=[
            "Sec-WebSocket-Accept",
            "Sec-WebSocket-Protocol",
            "Connection",
            "Upgrade"
        ]
    )
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Em produção, especifique os domínios exatos
    )
    
    # Middleware específico para Google Cloud Run e WebSockets
    @app.middleware("http")
    async def cloud_run_websocket_middleware(request: Request, call_next):
        """
        Middleware para otimizar WebSockets no Google Cloud Run
        """
        # Adicionar headers específicos para WebSocket
        if request.url.path == "/ws":
            response = Response()
            response.headers["Upgrade"] = "websocket"
            response.headers["Connection"] = "Upgrade"
            response.headers["Sec-WebSocket-Accept"] = "websocket"
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Pragma"] = "no-cache"
            return response
        
        # Para outras rotas, processar normalmente
        response = await call_next(request)
        
        # Adicionar headers CORS para todas as respostas
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "Sec-WebSocket-Accept, Sec-WebSocket-Protocol, Connection, Upgrade"
        
        return response
    
    # Rate limiting is handled by fastapi-limiter decorators
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # WebSocket status endpoint
    @app.get("/ws-status")
    async def websocket_status():
        """
        Endpoint para verificar status do WebSocket
        """
        return {
            "websocket_available": True,
            "endpoint": "/ws",
            "active_connections": websocket_manager.get_connection_count(),
            "connection_ids": websocket_manager.get_connection_ids(),
            "cors_enabled": True,
            "cloud_run_optimized": True,
            "supported_origins": ["*"],
            "supported_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
            "supported_headers": [
                "Accept", "Accept-Language", "Content-Language", "Content-Type",
                "Authorization", "X-Requested-With", "Origin",
                "Sec-WebSocket-Key", "Sec-WebSocket-Version", "Sec-WebSocket-Protocol",
                "Sec-WebSocket-Extensions", "Sec-WebSocket-Accept", "Connection", "Upgrade",
                "Cache-Control", "Pragma"
            ],
            "test_url": "wss://ainbox-backend-356969755759.southamerica-east1.run.app/ws"
        }
    
    # Endpoint de diagnóstico para WebSocket
    @app.get("/ws-diagnostic")
    async def websocket_diagnostic(request: Request):
        """
        Endpoint de diagnóstico detalhado para WebSocket
        """
        return {
            "request_info": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown"
            },
            "websocket_config": {
                "endpoint": "/ws",
                "protocol": "wss",
                "cors_headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Expose-Headers": "Sec-WebSocket-Accept, Sec-WebSocket-Protocol, Connection, Upgrade"
                }
            },
            "cloud_run_info": {
                "environment": "Google Cloud Run",
                "region": "southamerica-east1",
                "service": "ainbox-backend",
                "websocket_support": True
            }
        }
    
    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket):
        """
        WebSocket endpoint for real-time communication
        Otimizado para Google Cloud Run e ferramentas externas
        """
        connection_id = None
        try:
            # Log de tentativa de conexão
            logger.info(f"🔌 Tentativa de conexão WebSocket")
            logger.info(f"🔌 Client headers: {dict(websocket.headers)}")
            logger.info(f"🔌 Client origin: {websocket.headers.get('origin', 'unknown')}")
            
            # Conectar ao manager (que já aceita a conexão)
            connection_id = await websocket_manager.connect(websocket)
            logger.info(f"🔌 WebSocket connected: {connection_id}")
            
            # Enviar mensagem de boas-vindas
            await websocket_manager.send_personal_message({
                "type": "welcome",
                "message": "Conexão WebSocket estabelecida com sucesso!",
                "connection_id": connection_id,
                "server": "AInBox API",
                "version": "1.0.0",
                "cloud_run": True
            }, connection_id)
            
            # Loop principal de mensagens
            while True:
                try:
                    # Receber mensagem com timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
                    logger.debug(f"📨 Received WebSocket message: {data}")
                    
                    # Processar mensagem
                    try:
                        message_data = json.loads(data)
                        message_type = message_data.get("type", "unknown")
                    except json.JSONDecodeError:
                        message_type = "text"
                        message_data = {"type": "text", "content": data}
                    
                    # Echo back com informações adicionais
                    response = {
                        "type": "echo",
                        "original_message": message_data,
                        "connection_id": connection_id,
                        "timestamp": time.time(),
                        "server_response": f"Processado: {message_type}"
                    }
                    
                    await websocket_manager.send_personal_message(response, connection_id)
                    
                except asyncio.TimeoutError:
                    # Enviar ping para manter conexão viva
                    await websocket_manager.send_personal_message({
                        "type": "ping",
                        "message": "Conexão ativa",
                        "connection_id": connection_id
                    }, connection_id)
                    
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            logger.error(f"  - Error type: {type(e).__name__}")
            logger.error(f"  - Error details: {str(e)}")
            logger.error(f"  - Connection ID: {connection_id}")
            
            # Tentar enviar mensagem de erro se possível
            if connection_id:
                try:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": f"Erro na conexão: {str(e)}",
                        "connection_id": connection_id
                    }, connection_id)
                except:
                    pass
        finally:
            if connection_id:
                await websocket_manager.disconnect(websocket)
                logger.info(f"🔌 WebSocket disconnected: {connection_id}")
    
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
