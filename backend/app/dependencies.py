# backend/app/dependencies.py

from fastapi_limiter.depends import RateLimiter
from app.core.config import settings

# A flag global que controla a disponibilidade do Redis
RATE_LIMITER_AVAILABLE = False

# Criamos uma instância única e reutilizável do limiter real
_rate_limiter = RateLimiter(
    times=settings.RATE_LIMIT_PER_MINUTE,
    seconds=settings.RATE_LIMIT_WINDOW
)

# Criamos uma dependência "falsa" que não faz nada, para ser usada quando o Redis falha
async def _dummy_limiter():
    pass

def get_rate_limiter():
    """
    Fábrica de dependências.

    Esta função é chamada pelo FastAPI para cada requisição. Ela verifica o estado
    da conexão com o Redis e retorna a dependência apropriada:
    - O limiter real se o Redis estiver online.
    - A função dummy se o Redis estiver offline.
    """
    if RATE_LIMITER_AVAILABLE:
        return _rate_limiter
    else:
        return _dummy_limiter