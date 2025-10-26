#!/usr/bin/env python3
"""
MVP Setup Script for Sistema Simplificado de Análise Fiscal
Initialize database schema and storage configuration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from utils.mvp_config import mvp_settings
from utils.mvp_database import get_mvp_db, mvp_supabase
import structlog

logger = structlog.get_logger()


async def setup_database():
    """Setup database tables"""
    try:
        logger.info("Setting up MVP database...")
        
        # Test connection
        db = await get_mvp_db()
        logger.info("Database connection successful")
        
        # Note: The actual table creation should be done via Supabase SQL Editor
        # using the mvp_setup.sql file
        
        logger.info("Database setup completed. Please run mvp_setup.sql in Supabase SQL Editor.")
        return True
        
    except Exception as e:
        logger.error("Database setup failed", error=str(e))
        return False


def setup_storage():
    """Setup storage bucket and policies"""
    try:
        logger.info("Setting up MVP storage...")
        
        # Test storage connection
        client = mvp_supabase.client
        
        # Check if bucket exists
        try:
            buckets = client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if mvp_settings.storage_bucket in bucket_names:
                logger.info("Storage bucket already exists", bucket=mvp_settings.storage_bucket)
            else:
                logger.warning("Storage bucket not found. Please create it manually in Supabase.", bucket=mvp_settings.storage_bucket)
                
        except Exception as e:
            logger.error("Failed to check storage buckets", error=str(e))
            return False
        
        logger.info("Storage setup completed")
        return True
        
    except Exception as e:
        logger.error("Storage setup failed", error=str(e))
        return False


def verify_environment():
    """Verify environment configuration"""
    try:
        logger.info("Verifying MVP environment configuration...")
        
        # Check required environment variables
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_SERVICE_KEY',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error("Missing required environment variables", missing=missing_vars)
            logger.info("Please copy .env.mvp.example to .env and configure the missing variables")
            return False
        
        # Test Supabase connection
        try:
            client = mvp_supabase.client
            logger.info("Supabase connection successful", url=mvp_settings.supabase_url)
        except Exception as e:
            logger.error("Supabase connection failed", error=str(e))
            return False
        
        logger.info("Environment verification completed successfully")
        return True
        
    except Exception as e:
        logger.error("Environment verification failed", error=str(e))
        return False


def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("MVP Sistema Simplificado de Análise Fiscal - Setup Instructions")
    print("="*60)
    print("\n1. Environment Configuration:")
    print("   - Copy .env.mvp.example to .env")
    print("   - Configure SUPABASE_URL and SUPABASE_SERVICE_KEY")
    print("   - Configure OPENAI_API_KEY or OPENROUTER_API_KEY")
    
    print("\n2. Database Setup:")
    print("   - Go to your Supabase project SQL Editor")
    print("   - Run the contents of database/mvp_setup.sql")
    print("   - This will create the simplified tables for MVP")
    
    print("\n3. Storage Setup:")
    print("   - Go to your Supabase project Storage")
    print("   - Create a new bucket named 'invoice-xmls'")
    print("   - Set it as public bucket")
    print("   - Run database/schema/mvp_storage_setup.sql for policies")
    
    print("\n4. Test the Setup:")
    print("   - Run: python setup_mvp.py --test")
    print("   - This will verify all connections")
    
    print("\n5. Start the MVP:")
    print("   - Run: python main.py")
    print("   - Access: http://localhost:8000")
    
    print("\n" + "="*60)


async def test_setup():
    """Test the complete setup"""
    try:
        logger.info("Testing MVP setup...")
        
        # Test environment
        if not verify_environment():
            return False
        
        # Test database
        if not await setup_database():
            return False
        
        # Test storage
        if not setup_storage():
            return False
        
        logger.info("MVP setup test completed successfully!")
        return True
        
    except Exception as e:
        logger.error("Setup test failed", error=str(e))
        return False


async def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MVP Setup Script")
    parser.add_argument("--test", action="store_true", help="Test the setup")
    parser.add_argument("--instructions", action="store_true", help="Show setup instructions")
    
    args = parser.parse_args()
    
    if args.instructions:
        print_setup_instructions()
        return
    
    if args.test:
        success = await test_setup()
        if success:
            print("\n✅ MVP setup test passed! You're ready to start the application.")
        else:
            print("\n❌ MVP setup test failed. Please check the logs and configuration.")
        return
    
    # Default: show instructions
    print_setup_instructions()


if __name__ == "__main__":
    asyncio.run(main())