"""
Configuration settings for the AI Agents system
"""

from typing import Any

class Settings:
    """Mock settings class for testing"""
    
    def __init__(self):
        self.database_url = "mock://database"
        self.openai_api_key = "mock_key"
        self.debug = True

settings = Settings()