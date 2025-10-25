"""
Configuration settings for the AI Agents Invoice Analysis System
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "AI Agents Invoice Analysis System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # Redis (for agent communication and caching)
    REDIS_URL: str = "redis://localhost:6379"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # XML Processing
    XML_WATCH_DIRECTORY: str = "./xml_files"
    XML_PROCESSED_DIRECTORY: str = "./xml_processed"
    XML_ERROR_DIRECTORY: str = "./xml_errors"
    
    # Agent Configuration
    AGENT_TIMEOUT: int = 300  # 5 minutes
    MAX_CONCURRENT_AGENTS: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""
    
    # File Storage
    STORAGE_BUCKET: str = "invoice-xmls"
    
    # Machine Learning
    ML_MODEL_PATH: str = "./models"
    SPACY_MODEL: str = "pt_core_news_sm"
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_DEFAULT_MODEL: str = "gpt-4"
    OPENAI_FALLBACK_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT: int = 60
    OPENAI_RATE_LIMIT_RPM: int = 3500  # Requests per minute
    OPENAI_RATE_LIMIT_TPM: int = 90000  # Tokens per minute
    OPENAI_ENABLE_CACHING: bool = True
    OPENAI_CACHE_TTL: int = 3600  # Cache TTL in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()