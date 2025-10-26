"""
Database utilities for Supabase integration
Mock implementation for testing
"""

import structlog
from typing import Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger()


class DatabaseManager:
    """Mock Database Manager for testing"""
    
    def __init__(self):
        self.connected = False
    
    async def connect(self):
        """Mock database connection"""
        self.connected = True
        logger.info("Database connected (mock)")
    
    async def disconnect(self):
        """Mock database disconnection"""
        self.connected = False
        logger.info("Database disconnected (mock)")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None):
        """Mock query execution"""
        logger.info("Query executed (mock)", query=query[:100])
        return {"rows": [], "count": 0}


async def get_db_connection():
    """Mock database connection function"""
    return DatabaseManager()


class ProcessingStatusManager:
    """Mock Processing Status Manager for testing"""
    
    @staticmethod
    async def update_agent_status(
        document_id: str, 
        agent_name: str, 
        status: str, 
        error_message: Optional[str] = None
    ):
        """Update agent processing status"""
        logger.info(
            "Agent status updated",
            document_id=document_id,
            agent_name=agent_name,
            status=status,
            error_message=error_message
        )
    
    @staticmethod
    async def store_processing_result(
        document_id: str,
        agent_name: str,
        result_type: str,
        result_data: Dict[str, Any],
        confidence_score: float,
        processing_time_ms: int
    ):
        """Store processing result"""
        logger.info(
            "Processing result stored",
            document_id=document_id,
            agent_name=agent_name,
            result_type=result_type,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms
        )