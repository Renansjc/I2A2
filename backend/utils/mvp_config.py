"""
MVP Configuration for Sistema Simplificado de Análise Fiscal
Simplified configuration without complex authentication
"""

import os
from typing import List
from pydantic import BaseSettings, Field


class MVPSettings(BaseSettings):
    """MVP Settings for simplified deployment"""
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Supabase Configuration (simplified - always use service key)
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    storage_bucket: str = Field(default="invoice-xmls", env="STORAGE_BUCKET")
    
    # OpenAI Configuration (from alternative project)
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_DEFAULT_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # Alternative: OpenRouter for cost-effective LLM (from alternative project)
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="deepseek/deepseek-chat-v3.1:free", env="OPENROUTER_MODEL")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="ALLOWED_ORIGINS"
    )
    
    # File Processing
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(default=[".xml"], env="ALLOWED_FILE_TYPES")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CrewAI Configuration (from alternative project)
    crewai_telemetry_opt_out: bool = Field(default=True, env="CREWAI_TELEMETRY_OPT_OUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
mvp_settings = MVPSettings()


def get_mvp_settings() -> MVPSettings:
    """Get MVP settings instance"""
    return mvp_settings