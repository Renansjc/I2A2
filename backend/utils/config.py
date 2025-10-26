"""
Configuration settings for the AI Agents system
"""

import os
from typing import List, Optional
from pydantic import Field, ConfigDict

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with Supabase integration"""
    
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Application Settings
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database Configuration
    database_url: str
    
    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str = Field(alias="SUPABASE_KEY")
    supabase_service_key: str
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"]
    )
    
    # XML Processing Directories
    xml_watch_directory: str = Field(default="./xml_files")
    xml_processed_directory: str = Field(default="./xml_processed")
    xml_error_directory: str = Field(default="./xml_errors")
    
    # Agent Configuration
    agent_timeout: int = Field(default=300)
    max_concurrent_agents: int = Field(default=10)
    
    # Logging
    log_level: str = Field(default="INFO")
    sentry_dsn: Optional[str] = Field(default=None)
    
    # File Storage
    storage_bucket: str = Field(default="invoice-xmls")
    
    # Machine Learning
    ml_model_path: str = Field(default="./models")
    spacy_model: str = Field(default="pt_core_news_sm")
    
    # OpenAI Configuration
    openai_api_key: str
    openai_default_model: str = Field(default="gpt-4o-mini")
    openai_fallback_model: str = Field(default="gpt-3.5-turbo")
    openai_max_tokens: int = Field(default=4000)
    openai_temperature: float = Field(default=0.1)
    openai_max_retries: int = Field(default=3)
    openai_timeout: int = Field(default=60)
    openai_rate_limit_rpm: int = Field(default=3500)
    openai_rate_limit_tpm: int = Field(default=90000)
    openai_enable_caching: bool = Field(default=True)
    openai_cache_ttl: int = Field(default=3600)


# Global settings instance
settings = Settings()