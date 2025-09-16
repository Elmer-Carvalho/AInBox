# backend/app/dependencies.py

from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from app.core.config import settings

# A flag global continua sendo a fonte da verdade sobre o estado do Redis
RATE_LIMITER_AVAILABLE = False

async def rate_limit_dependency(request: Request, response: Response):
    """
    Uma única dependência que aplica o rate limiting de forma condicional.
    
    Esta função é chamada pelo FastAPI a cada requisição e recebe
    automaticamente os objetos 'request' e 'response'.
    """
    if RATE_LIMITER_AVAILABLE:
        # Se o Redis estiver disponível, instanciamos o limiter e o executamos
        # com os argumentos corretos que a biblioteca espera.
        limiter = RateLimiter(
            times=settings.RATE_LIMIT_PER_MINUTE,
            seconds=settings.RATE_LIMIT_WINDOW
        )
        
        try:
            # Chamamos o limiter manualmente, passando os argumentos necessários
            await limiter(request, response)
        except Exception as e:
            # Se o limiter levantar uma exceção (ex: limite excedido),
            # o FastAPI a capturará e retornará um erro 429 Too Many Requests.
            raise e