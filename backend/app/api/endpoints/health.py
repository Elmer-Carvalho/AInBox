"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from app.core.config import settings
from app.websocket.manager import websocket_manager
from app.services.rate_limiter import rate_limiter
from app.services.security_validator import security_validator


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
            "allowed_file_types": settings.ALLOWED_FILE_TYPES,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE
        },
        "security": {
            "validation_stats": security_validator.get_validation_stats(),
            "rate_limiter_available": rate_limiter.redis_client is not None
        }
    }


@router.get("/rate-limit/{client_ip}")
async def get_rate_limit_status(client_ip: str) -> Dict[str, Any]:
    """
    Get rate limiting status for a specific client IP
    
    Args:
        client_ip: Client IP address
        
    Returns:
        Dict[str, Any]: Rate limiting status
    """
    try:
        stats = rate_limiter.get_client_stats(client_ip)
        return stats
    except Exception as e:
        return {
            "error": f"Error getting rate limit status: {str(e)}",
            "client_ip": client_ip
        }


@router.post("/rate-limit/{client_ip}/reset")
async def reset_rate_limit(client_ip: str) -> Dict[str, Any]:
    """
    Reset rate limit for a specific client IP (admin function)
    
    Args:
        client_ip: Client IP address
        
    Returns:
        Dict[str, Any]: Reset result
    """
    try:
        success = rate_limiter.reset_client_limit(client_ip)
        return {
            "success": success,
            "client_ip": client_ip,
            "message": "Rate limit reset successfully" if success else "Failed to reset rate limit"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error resetting rate limit: {str(e)}",
            "client_ip": client_ip
        }
