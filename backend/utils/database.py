"""
Database connection and utilities for PostgreSQL/Supabase
"""

import asyncpg
from supabase import create_client, Client
import structlog
from typing import Optional
from .config import settings

logger = structlog.get_logger()

# Global database connection pool
db_pool: Optional[asyncpg.Pool] = None
supabase_client: Optional[Client] = None

async def init_db():
    """Initialize database connections"""
    global db_pool, supabase_client
    
    try:
        # Initialize asyncpg connection pool for direct PostgreSQL access
        if settings.DATABASE_URL:
            db_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool initialized")
        
        # Initialize Supabase client for auth and storage
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized")
            
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
        raise

async def get_db_connection():
    """Get database connection from pool"""
    if not db_pool:
        raise RuntimeError("Database pool not initialized")
    return await db_pool.acquire()

async def close_db():
    """Close database connections"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connections closed")

def get_supabase_client() -> Client:
    """Get Supabase client"""
    if not supabase_client:
        raise RuntimeError("Supabase client not initialized")
    return supabase_client

class DatabaseManager:
    """Database operations manager"""
    
    @staticmethod
    async def execute_query(query: str, *args):
        """Execute a query and return results"""
        async with db_pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    @staticmethod
    async def execute_command(command: str, *args):
        """Execute a command (INSERT, UPDATE, DELETE)"""
        async with db_pool.acquire() as conn:
            return await conn.execute(command, *args)
    
    @staticmethod
    async def execute_transaction(commands: list):
        """Execute multiple commands in a transaction"""
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                results = []
                for command, args in commands:
                    result = await conn.execute(command, *args)
                    results.append(result)
                return results