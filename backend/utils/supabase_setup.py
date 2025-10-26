"""
Supabase setup utilities for bucket creation and RLS policies
"""

import structlog
from typing import Dict, Any, Optional
from supabase import create_client, Client

from .config import settings

logger = structlog.get_logger()


class SupabaseSetup:
    """Utilities for setting up Supabase storage and security"""
    
    def __init__(self):
        # Use service key for admin operations
        self.admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    def create_storage_bucket(self) -> bool:
        """Create storage bucket for XML files"""
        try:
            # Check if bucket already exists
            buckets = self.admin_client.storage.list_buckets()
            bucket_names = [bucket.name for bucket in buckets]
            
            if settings.storage_bucket in bucket_names:
                logger.info("Storage bucket already exists", bucket=settings.storage_bucket)
                return True
            
            # Create new bucket
            result = self.admin_client.storage.create_bucket(
                id=settings.storage_bucket,
                name=settings.storage_bucket,
                options={
                    'public': False,  # Private bucket for security
                    'allowedMimeTypes': ['application/xml', 'text/xml'],
                    'fileSizeLimit': 10485760  # 10MB limit
                }
            )
            
            logger.info("Storage bucket created successfully", bucket=settings.storage_bucket)
            return True
            
        except Exception as e:
            logger.error("Failed to create storage bucket", error=str(e), bucket=settings.storage_bucket)
            return False
    
    def setup_storage_policies(self) -> bool:
        """Set up RLS policies for storage bucket"""
        try:
            # Note: Storage policies are typically set up through the Supabase dashboard
            # or using SQL commands. The Python client doesn't directly support policy creation.
            
            policies_sql = f"""
            -- Enable RLS on storage.objects
            ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
            
            -- Policy for users to upload their own files
            CREATE POLICY "Users can upload their own files" ON storage.objects
            FOR INSERT WITH CHECK (
                bucket_id = '{settings.storage_bucket}' 
                AND auth.uid()::text = (storage.foldername(name))[1]
            );
            
            -- Policy for users to view their own files
            CREATE POLICY "Users can view their own files" ON storage.objects
            FOR SELECT USING (
                bucket_id = '{settings.storage_bucket}' 
                AND auth.uid()::text = (storage.foldername(name))[1]
            );
            
            -- Policy for users to update their own files
            CREATE POLICY "Users can update their own files" ON storage.objects
            FOR UPDATE USING (
                bucket_id = '{settings.storage_bucket}' 
                AND auth.uid()::text = (storage.foldername(name))[1]
            );
            
            -- Policy for users to delete their own files
            CREATE POLICY "Users can delete their own files" ON storage.objects
            FOR DELETE USING (
                bucket_id = '{settings.storage_bucket}' 
                AND auth.uid()::text = (storage.foldername(name))[1]
            );
            """
            
            logger.info(
                "Storage RLS policies SQL generated. Execute this in Supabase SQL editor:",
                sql=policies_sql
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to setup storage policies", error=str(e))
            return False
    
    def setup_database_rls(self) -> bool:
        """Set up RLS policies for database tables"""
        try:
            rls_policies_sql = """
            -- Enable RLS on fiscal_documents table
            ALTER TABLE fiscal_documents ENABLE ROW LEVEL SECURITY;
            
            -- Policy for users to access their own documents
            CREATE POLICY "Users can access their own documents" ON fiscal_documents
            FOR ALL USING (auth.uid()::text = user_id);
            
            -- Enable RLS on document_metadata table
            ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
            
            -- Policy for users to access metadata of their own documents
            CREATE POLICY "Users can access their own document metadata" ON document_metadata
            FOR ALL USING (
                document_id IN (
                    SELECT id FROM fiscal_documents WHERE user_id = auth.uid()::text
                )
            );
            
            -- Enable RLS on processing_results table
            ALTER TABLE processing_results ENABLE ROW LEVEL SECURITY;
            
            -- Policy for users to access results of their own documents
            CREATE POLICY "Users can access their own processing results" ON processing_results
            FOR ALL USING (
                document_id IN (
                    SELECT id FROM fiscal_documents WHERE user_id = auth.uid()::text
                )
            );
            """
            
            logger.info(
                "Database RLS policies SQL generated. Execute this in Supabase SQL editor:",
                sql=rls_policies_sql
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to setup database RLS policies", error=str(e))
            return False
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate Supabase configuration"""
        results = {
            'connection': False,
            'bucket_exists': False,
            'tables_exist': False
        }
        
        try:
            # Test connection
            buckets = self.admin_client.storage.list_buckets()
            results['connection'] = True
            logger.info("Supabase connection successful")
            
            # Check if bucket exists
            bucket_names = [bucket.name for bucket in buckets]
            results['bucket_exists'] = settings.storage_bucket in bucket_names
            
            # Test table access (this will fail if tables don't exist)
            try:
                test_query = self.admin_client.table('fiscal_documents').select('id').limit(1).execute()
                results['tables_exist'] = True
            except Exception:
                results['tables_exist'] = False
            
        except Exception as e:
            logger.error("Supabase configuration validation failed", error=str(e))
        
        return results
    
    def setup_file_validation(self) -> Dict[str, Any]:
        """Setup file validation rules"""
        validation_config = {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_extensions': ['.xml'],
            'allowed_mime_types': ['application/xml', 'text/xml'],
            'virus_scanning': False,  # Would require external service
            'content_validation': True  # Validate XML structure
        }
        
        logger.info("File validation configuration", config=validation_config)
        return validation_config


def setup_supabase_environment():
    """Main setup function for Supabase environment"""
    logger.info("Starting Supabase environment setup")
    
    setup = SupabaseSetup()
    
    # Validate configuration
    validation_results = setup.validate_configuration()
    logger.info("Configuration validation results", results=validation_results)
    
    if not validation_results['connection']:
        logger.error("Cannot connect to Supabase. Check your configuration.")
        return False
    
    # Create storage bucket
    if not validation_results['bucket_exists']:
        setup.create_storage_bucket()
    
    # Setup policies (generates SQL for manual execution)
    setup.setup_storage_policies()
    setup.setup_database_rls()
    
    # Setup file validation
    setup.setup_file_validation()
    
    logger.info("Supabase environment setup completed")
    return True


if __name__ == "__main__":
    setup_supabase_environment()