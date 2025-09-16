# backend/app/dependencies.py

from fastapi import Request
from fastapi_limiter.depends import RateLimiter
from app.core.config import settings

# A flag global continua sendo útil para ser verificada pela dependência
RATE_LIMITER_AVAILABLE = False

async def conditional_rate_limiter(request: Request):
    """
    Dependência que aplica o rate limiting de forma condicional.
    Esta função é executada a cada nova requisição.
    """
    if RATE_LIMITER_AVAILABLE:
        # Se o Redis estiver disponível, cria e executa o limiter
        limiter = RateLimiter(
            times=settings.RATE_LIMIT_PER_MINUTE, 
            seconds=settings.RATE_LIMIT_WINDOW
        )
        await limiter(request)
