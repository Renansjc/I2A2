#!/usr/bin/env python3
"""
Supabase setup script for AI Agents Invoice Analysis System
Run this script to configure your Supabase environment
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from utils.config import settings
from utils.supabase_setup import setup_supabase_environment
from utils.database import get_db_connection
from utils.file_security import validate_and_secure_file
import structlog

logger = structlog.get_logger()


def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        return False
    
    print("✅ All required environment variables are set")
    return True


def display_sql_setup_instructions():
    """Display SQL setup instructions for Supabase"""
    print("\n" + "="*60)
    print("📋 SUPABASE SQL SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Execute the following SQL scripts in order:")
    
    sql_files = [
        "database/schema/01_create_tables.sql",
        "database/schema/02_nfe_tables.sql", 
        "database/schema/03_nfse_tables.sql",
        "database/schema/04_views.sql",
        "database/schema/05_indexes.sql",
        "database/schema/06_rls_policies.sql"
    ]
    
    for i, sql_file in enumerate(sql_files, 1):
        print(f"   {i}. {sql_file}")
    
    print("\n4. Create the following additional tables for file upload:")
    
    additional_sql = """
-- File upload tracking tables
CREATE TABLE IF NOT EXISTS fiscal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    document_type VARCHAR(10) NOT NULL,
    xml_content TEXT NOT NULL,
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    cnpj_emitente VARCHAR(14),
    nome_emitente VARCHAR(255),
    cnpj_destinatario VARCHAR(14),
    nome_destinatario VARCHAR(255),
    numero_documento VARCHAR(50),
    serie_documento VARCHAR(10),
    data_emissao TIMESTAMPTZ,
    valor_total DECIMAL(15,2),
    valor_tributos DECIMAL(15,2),
    natureza_operacao VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    result_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE fiscal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can access their own documents" ON fiscal_documents
FOR ALL USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can access their own document metadata" ON document_metadata
FOR ALL USING (
    document_id IN (
        SELECT id FROM fiscal_documents WHERE user_id::text = auth.uid()::text
    )
);

CREATE POLICY "Users can access their own processing results" ON processing_results
FOR ALL USING (
    document_id IN (
        SELECT id FROM fiscal_documents WHERE user_id::text = auth.uid()::text
    )
);
"""
    
    print(additional_sql)
    
    print("\n5. Set up Storage bucket:")
    print("   - Go to Storage in Supabase dashboard")
    print("   - Create a new bucket named 'invoice-xmls'")
    print("   - Set it as private (not public)")
    print("   - Configure RLS policies for the bucket")


def display_storage_setup_instructions():
    """Display storage setup instructions"""
    print("\n" + "="*60)
    print("🗄️  SUPABASE STORAGE SETUP")
    print("="*60)
    
    print("\n1. Create Storage Bucket:")
    print("   - Bucket name: invoice-xmls")
    print("   - Public: No (private bucket)")
    print("   - File size limit: 10MB")
    print("   - Allowed MIME types: application/xml, text/xml")
    
    print("\n2. Set up Storage RLS Policies (execute in SQL Editor):")
    
    storage_policies = f"""
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
    
    print(storage_policies)


async def test_database_connection():
    """Test database connection"""
    try:
        print("\n🔍 Testing database connection...")
        db = await get_db_connection()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def test_file_validation():
    """Test file validation system"""
    try:
        print("\n🔍 Testing file validation system...")
        
        # Test with sample XML content
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<infNFe>
    <ide>
        <cUF>42</cUF>
        <cNF>12345678</cNF>
    </ide>
    <emit>
        <CNPJ>12345678000195</CNPJ>
        <xNome>Empresa Teste</xNome>
    </emit>
</infNFe>"""
        
        result = validate_and_secure_file(
            "test_nfe.xml", 
            sample_xml.encode('utf-8'), 
            "test_user_123"
        )
        
        if result['valid']:
            print("✅ File validation system working correctly")
            return True
        else:
            print(f"❌ File validation failed: {result['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ File validation test failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("🚀 Supabase Setup for AI Agents Invoice Analysis System")
    print("="*60)
    
    # Check environment variables
    if not check_environment_variables():
        return False
    
    # Test file validation
    if not test_file_validation():
        print("\n⚠️  File validation system has issues, but continuing...")
    
    # Display setup instructions
    display_sql_setup_instructions()
    display_storage_setup_instructions()
    
    print("\n" + "="*60)
    print("✅ SETUP INSTRUCTIONS DISPLAYED")
    print("="*60)
    
    print("\nNext steps:")
    print("1. Execute the SQL scripts in your Supabase dashboard")
    print("2. Create the storage bucket as instructed")
    print("3. Test your setup by running the backend server")
    print("4. Upload a test XML file through the API")
    
    print(f"\nYour configuration:")
    print(f"- Supabase URL: {settings.supabase_url}")
    print(f"- Storage Bucket: {settings.storage_bucket}")
    print(f"- Environment: {'Development' if settings.debug else 'Production'}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)