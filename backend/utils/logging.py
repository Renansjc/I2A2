"""
Logging configuration for the AI Agents Invoice Analysis System
"""

import structlog
import logging
import sys
from typing import Any, Dict
from .config import settings

def configure_logging():
    """Configure structured logging for the application"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class AgentLogger:
    """Logger for agent activities"""
    
    def __init__(self, agent_name: str):
        self.logger = structlog.get_logger(agent_name)
        self.agent_name = agent_name
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, agent=self.agent_name, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, agent=self.agent_name, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, agent=self.agent_name, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, agent=self.agent_name, **kwargs)
    
    def log_processing_start(self, file_path: str, **kwargs):
        """Log processing start"""
        self.info("Processing started", file_path=file_path, **kwargs)
    
    def log_processing_complete(self, file_path: str, duration: float, **kwargs):
        """Log processing completion"""
        self.info("Processing completed", file_path=file_path, duration=duration, **kwargs)
    
    def log_processing_error(self, file_path: str, error: str, **kwargs):
        """Log processing error"""
        self.error("Processing failed", file_path=file_path, error=error, **kwargs)

def get_agent_logger(agent_name: str) -> AgentLogger:
    """Get logger for specific agent"""
    return AgentLogger(agent_name)