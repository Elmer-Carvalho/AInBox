# backend/app/dependencies.py

from fastapi import Depends
from fastapi_limiter.depends import RateLimiter
from app.core.config import settings

# A variável que controla o status do rate limiter agora vive aqui
RATE_LIMITER_AVAILABLE = False

def get_rate_limiter():
    """
    Obtém a dependência do rate limiter se estiver disponível, caso contrário, retorna None.
    """
    if RATE_LIMITER_AVAILABLE:
        return Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=settings.RATE_LIMIT_WINDOW))
    else:
        # Retorna uma dependência que não faz nada (bypass do rate limiting)
        def no_rate_limit():
            return None
        return Depends(no_rate_limit)
