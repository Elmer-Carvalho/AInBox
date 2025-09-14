"""
Rate limiting middleware
Applies rate limiting to API endpoints
"""

import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from app.services.rate_limiter import rate_limiter


class RateLimitMiddleware:
    """
    Middleware for rate limiting API requests
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/api/v1/health"):
            await self.app(scope, receive, send)
            return
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        rate_limit_result = rate_limiter.is_allowed(client_ip)
        
        if not rate_limit_result["allowed"]:
            # Log rate limit violation
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            # Create rate limit response
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": rate_limit_result.get("message", "Too many requests"),
                    "retry_after": rate_limit_result.get("reset_time", 60),
                    "remaining": rate_limit_result.get("remaining", 0)
                },
                headers={
                    "Retry-After": str(rate_limit_result.get("reset_time", 60)),
                    "X-RateLimit-Limit": str(10),
                    "X-RateLimit-Remaining": str(rate_limit_result.get("remaining", 0)),
                    "X-RateLimit-Reset": str(rate_limit_result.get("reset_time", 60))
                }
            )
            
            await response(scope, receive, send)
            return
        
        # Add rate limit headers to response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers.extend([
                    (b"x-ratelimit-limit", str(10).encode()),
                    (b"x-ratelimit-remaining", str(rate_limit_result.get("remaining", 0)).encode()),
                    (b"x-ratelimit-reset", str(rate_limit_result.get("reset_time", 60)).encode())
                ])
                message["headers"] = list(headers.items())
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
