"""
Configuration settings for The Grey Tutor backend.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "The Grey Tutor"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
        "exp://localhost:19000",
        "exp://192.168.1.100:19000"  # Add your local IP for mobile testing
    ]
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default
    
    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: Optional[str] = None
    
    # AI Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: str = "us-west1-gcp-free"
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 30
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    FALLBACK_MODEL: str = "gpt-3.5-turbo"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    FREE_TIER_DAILY_LIMIT: int = 20
    SUPPORTER_TIER_DAILY_LIMIT: int = 50
    
    # Privacy and Security
    ENCRYPTION_KEY: Optional[str] = None
    GDPR_COMPLIANCE: bool = True
    DATA_RETENTION_DAYS: int = 365
    ANONYMOUS_MODE_ENABLED: bool = True
    
    # Monitoring and Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = True
    PROMETHEUS_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None
    
    # File Storage
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".pdf", ".docx", ".md"]
    
    # Ko-fi Integration
    KOFI_WEBHOOK_SECRET: Optional[str] = None
    KOFI_VERIFICATION_TOKEN: Optional[str] = None
    
    # Middle Earth Content
    CONTENT_BASE_PATH: str = str(Path(__file__).parent.parent.parent.parent / "docs" / "sources")
    ENABLE_CONTENT_UPDATES: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate required settings in production
        if self.ENVIRONMENT == "production":
            self._validate_production_settings()
    
    def _validate_production_settings(self):
        """Validate that required settings are present in production."""
        required_settings = [
            "SECRET_KEY",
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "ENCRYPTION_KEY"
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not getattr(self, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ValueError(
                f"Missing required production settings: {', '.join(missing_settings)}"
            )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        return "postgresql://localhost/thegreytutor"
    
    @property
    def database_url_async(self) -> str:
        """Get asynchronous database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "postgresql+asyncpg://localhost/thegreytutor"

# Global settings instance
settings = Settings()
