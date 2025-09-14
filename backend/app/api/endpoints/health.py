"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from app.core.config import settings
from app.websocket.manager import websocket_manager
from app.services.security_validator import security_validator
from loguru import logger


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    environment: str
    websocket_connections: int
    uptime: float


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint
    
    Returns:
        HealthResponse: Application health status
    """
    logger.info("🏥 Health check endpoint called")
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        websocket_connections=websocket_manager.get_connection_count(),
        uptime=asyncio.get_event_loop().time()
    )


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with more information
    
    Returns:
        Dict[str, Any]: Detailed health information
    """
    return {
        "status": "healthy",
        "application": {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "websocket": {
            "active_connections": websocket_manager.get_connection_count(),
            "connection_ids": websocket_manager.get_connection_ids()
        },
        "configuration": {
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "max_total_size_mb": settings.MAX_TOTAL_SIZE / (1024 * 1024),
            "max_files_per_request": settings.MAX_FILES_PER_REQUEST,
            "max_strings_per_request": settings.MAX_STRINGS_PER_REQUEST,
            "allowed_file_types": settings.allowed_file_types_list,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE
        },
        "security": {
            "validation_stats": security_validator.get_validation_stats()
        }
    }


