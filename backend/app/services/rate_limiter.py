"""
Rate limiting service using Redis
Implements request rate limiting with fallback mechanisms
"""

import time
import json
from typing import Optional, Dict, Any
import redis
from loguru import logger

from app.core.config import settings


class RateLimiter:
    """
    Rate limiting service using Redis with fallback to in-memory storage
    """
    
    def __init__(self):
        """Initialize rate limiter with Redis connection"""
        self.redis_client = None
        self.fallback_storage = {}  # In-memory fallback
        self.fallback_cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        self._connect_redis()
        logger.info("Rate limiter initialized")
    
    def _connect_redis(self) -> None:
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_SSL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using fallback storage.")
            self.redis_client = None
    
    def is_allowed(self, client_ip: str) -> Dict[str, Any]:
        """
        Check if request is allowed for given client IP
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Dict[str, Any]: Rate limit status and information
        """
        current_time = int(time.time())
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        try:
            if self.redis_client:
                return self._check_redis_rate_limit(client_ip, current_time, window_start)
            else:
                return self._check_fallback_rate_limit(client_ip, current_time, window_start)
                
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return {
                "allowed": True,
                "remaining": settings.RATE_LIMIT_PER_MINUTE,
                "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                "error": str(e)
            }
    
    def _check_redis_rate_limit(self, client_ip: str, current_time: int, window_start: int) -> Dict[str, Any]:
        """Check rate limit using Redis"""
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Key for this IP
            key = f"rate_limit:{client_ip}"
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, settings.REDIS_TTL)
            
            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= settings.RATE_LIMIT_PER_MINUTE:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                    "message": "Rate limit exceeded. Try again later."
                }
            else:
                return {
                    "allowed": True,
                    "remaining": settings.RATE_LIMIT_PER_MINUTE - current_count - 1,
                    "reset_time": current_time + settings.RATE_LIMIT_WINDOW
                }
                
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to in-memory storage
            return self._check_fallback_rate_limit(client_ip, current_time, window_start)
    
    def _check_fallback_rate_limit(self, client_ip: str, current_time: int, window_start: int) -> Dict[str, Any]:
        """Check rate limit using in-memory fallback storage"""
        try:
            # Clean up old entries periodically
            if current_time - self.last_cleanup > self.fallback_cleanup_interval:
                self._cleanup_fallback_storage(current_time, window_start)
                self.last_cleanup = current_time
            
            # Get or create client data
            if client_ip not in self.fallback_storage:
                self.fallback_storage[client_ip] = []
            
            # Remove old requests
            self.fallback_storage[client_ip] = [
                req_time for req_time in self.fallback_storage[client_ip]
                if req_time > window_start
            ]
            
            # Check current count
            current_count = len(self.fallback_storage[client_ip])
            
            if current_count >= settings.RATE_LIMIT_PER_MINUTE:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                    "message": "Rate limit exceeded. Try again later.",
                    "fallback": True
                }
            else:
                # Add current request
                self.fallback_storage[client_ip].append(current_time)
                
                return {
                    "allowed": True,
                    "remaining": settings.RATE_LIMIT_PER_MINUTE - current_count - 1,
                    "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"Fallback rate limiting error: {e}")
            # Fail open
            return {
                "allowed": True,
                "remaining": settings.RATE_LIMIT_PER_MINUTE,
                "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                "error": str(e)
            }
    
    def _cleanup_fallback_storage(self, current_time: int, window_start: int) -> None:
        """Clean up old entries from fallback storage"""
        try:
            for client_ip in list(self.fallback_storage.keys()):
                self.fallback_storage[client_ip] = [
                    req_time for req_time in self.fallback_storage[client_ip]
                    if req_time > window_start
                ]
                
                # Remove empty entries
                if not self.fallback_storage[client_ip]:
                    del self.fallback_storage[client_ip]
                    
        except Exception as e:
            logger.error(f"Fallback cleanup error: {e}")
    
    def get_client_stats(self, client_ip: str) -> Dict[str, Any]:
        """
        Get rate limiting statistics for a client
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Dict[str, Any]: Client statistics
        """
        current_time = int(time.time())
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        try:
            if self.redis_client:
                key = f"rate_limit:{client_ip}"
                current_count = self.redis_client.zcard(key)
                ttl = self.redis_client.ttl(key)
            else:
                current_count = len(self.fallback_storage.get(client_ip, []))
                ttl = settings.REDIS_TTL
            
            return {
                "client_ip": client_ip,
                "current_requests": current_count,
                "max_requests": settings.RATE_LIMIT_PER_MINUTE,
                "remaining": max(0, settings.RATE_LIMIT_PER_MINUTE - current_count),
                "reset_time": current_time + settings.RATE_LIMIT_WINDOW,
                "ttl": ttl,
                "using_redis": self.redis_client is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting client stats: {e}")
            return {
                "client_ip": client_ip,
                "error": str(e)
            }
    
    def reset_client_limit(self, client_ip: str) -> bool:
        """
        Reset rate limit for a specific client (admin function)
        
        Args:
            client_ip: Client IP address
            
        Returns:
            bool: Success status
        """
        try:
            if self.redis_client:
                key = f"rate_limit:{client_ip}"
                self.redis_client.delete(key)
            else:
                if client_ip in self.fallback_storage:
                    del self.fallback_storage[client_ip]
            
            logger.info(f"Rate limit reset for client: {client_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit for {client_ip}: {e}")
            return False


# Global rate limiter instance
rate_limiter = RateLimiter()
