"""
API routes configuration
"""

from fastapi import APIRouter
from app.api.endpoints import analysis, health

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
