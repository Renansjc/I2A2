"""
Configuration settings for the AI Agents system
"""

import os
from typing import List, Optional
from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with Supabase integration"""
    
    # Application Settings
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database Configuration
    database_url: str = Field(env="DATABASE_URL")
    
    # Supabase Configuration
    supabase_url: str = Field(env="SUPABASE_URL")
    supabase_anon_key: str = Field(env="SUPABASE_ANON_KEY", alias="SUPABASE_KEY")
    supabase_service_key: str = Field(env="SUPABASE_SERVICE_KEY")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="ALLOWED_ORIGINS"
    )
    
    # XML Processing Directories
    xml_watch_directory: str = Field(default="./xml_files", env="XML_WATCH_DIRECTORY")
    xml_processed_directory: str = Field(default="./xml_processed", env="XML_PROCESSED_DIRECTORY")
    xml_error_directory: str = Field(default="./xml_errors", env="XML_ERROR_DIRECTORY")
    
    # Agent Configuration
    agent_timeout: int = Field(default=300, env="AGENT_TIMEOUT")
    max_concurrent_agents: int = Field(default=10, env="MAX_CONCURRENT_AGENTS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # File Storage
    storage_bucket: str = Field(default="invoice-xmls", env="STORAGE_BUCKET")
    
    # Machine Learning
    ml_model_path: str = Field(default="./models", env="ML_MODEL_PATH")
    spacy_model: str = Field(default="pt_core_news_sm", env="SPACY_MODEL")
    
    # OpenAI Configuration
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_default_model: str = Field(default="gpt-4", env="OPENAI_DEFAULT_MODEL")
    openai_fallback_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_FALLBACK_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    openai_max_retries: int = Field(default=3, env="OPENAI_MAX_RETRIES")
    openai_timeout: int = Field(default=60, env="OPENAI_TIMEOUT")
    openai_rate_limit_rpm: int = Field(default=3500, env="OPENAI_RATE_LIMIT_RPM")
    openai_rate_limit_tpm: int = Field(default=90000, env="OPENAI_RATE_LIMIT_TPM")
    openai_enable_caching: bool = Field(default=True, env="OPENAI_ENABLE_CACHING")
    openai_cache_ttl: int = Field(default=3600, env="OPENAI_CACHE_TTL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()