"""
Application configuration settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application settings
    APP_NAME: str = "AInBox API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))  # Google Cloud Run sets PORT automatically
    
    # CORS settings - Configuração mais permissiva para ferramentas externas
    ALLOWED_ORIGINS: str = "*"  # Permite qualquer origem para ferramentas de teste
    
    # Google Gemini API settings
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS: int = 100
    
    # File processing settings
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB per file
    MAX_TOTAL_SIZE: int = 100 * 1024 * 1024  # 100MB total
    MAX_FILES_PER_REQUEST: int = 20
    MAX_STRINGS_PER_REQUEST: int = 20
    ALLOWED_FILE_TYPES: str = ".txt,.pdf"
    
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = 5
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_BURST: int = 3  # burst allowance
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_SSL: bool = False
    REDIS_TTL: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list"""
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(",") if file_type.strip()]


# Create settings instance
settings = Settings()
