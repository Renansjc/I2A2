# Supabase Integration Guide

## Overview

This document describes the Supabase integration for the AI Agents Invoice Analysis System, including database setup, file storage, authentication, and security configurations.

## Prerequisites

- Supabase account and project
- Python 3.13.9 with required dependencies
- Environment variables configured

## Environment Configuration

### Required Environment Variables

Add these variables to your `backend/.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Storage Configuration
STORAGE_BUCKET=invoice-xmls
```

### Getting Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to Settings > API
3. Copy the following:
   - Project URL → `SUPABASE_URL`
   - anon/public key → `SUPABASE_ANON_KEY`
   - service_role key → `SUPABASE_SERVICE_KEY`

## Database Setup

### 1. Execute Database Schema

Run the following SQL scripts in your Supabase SQL Editor in order:

1. `database/schema/01_create_tables.sql`
2. `database/schema/02_nfe_tables.sql`
3. `database/schema/03_nfse_tables.sql`
4. `database/schema/04_views.sql`
5. `database/schema/05_indexes.sql`
6. `database/schema/06_rls_policies.sql`

### 2. Create File Upload Tables

Execute this SQL in Supabase SQL Editor:

```sql
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
```

### 3. Enable Row Level Security (RLS)

```sql
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
```

## Storage Setup

### 1. Create Storage Bucket

1. Go to Storage in Supabase dashboard
2. Click "Create bucket"
3. Name: `invoice-xmls`
4. Set as Private (not public)
5. Configure settings:
   - File size limit: 10MB
   - Allowed MIME types: `application/xml`, `text/xml`

### 2. Storage RLS Policies

Execute in Supabase SQL Editor:

```sql
-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy for users to upload their own files
CREATE POLICY "Users can upload their own files" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'invoice-xmls' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy for users to view their own files
CREATE POLICY "Users can view their own files" ON storage.objects
FOR SELECT USING (
    bucket_id = 'invoice-xmls' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy for users to update their own files
CREATE POLICY "Users can update their own files" ON storage.objects
FOR UPDATE USING (
    bucket_id = 'invoice-xmls' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Policy for users to delete their own files
CREATE POLICY "Users can delete their own files" ON storage.objects
FOR DELETE USING (
    bucket_id = 'invoice-xmls' 
    AND auth.uid()::text = (storage.foldername(name))[1]
);
```

## Authentication Setup

### User Registration and Login

The system uses Supabase Auth for user management. Users can:

1. Register with email/password
2. Sign in with email/password
3. Reset passwords
4. Manage sessions

### API Authentication

All API endpoints require authentication via JWT tokens:

```python
from fastapi import Depends
from utils.auth_integration import get_current_user

@app.post("/api/documents/upload")
async def upload_document(
    current_user: dict = Depends(get_current_user)
):
    # User is authenticated
    user_id = current_user['id']
```

## File Upload Security

### Validation Features

- **File size limit**: 10MB maximum
- **File type validation**: Only XML files allowed
- **Content scanning**: Checks for malicious content
- **Filename sanitization**: Removes dangerous characters
- **Virus scanning**: Placeholder for future implementation

### Security Measures

- **User isolation**: Files stored in user-specific folders
- **Access logging**: All file operations logged
- **RLS policies**: Database-level access control
- **Input sanitization**: All inputs validated and sanitized

## API Endpoints

### File Upload

```http
POST /api/documents/upload
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: <xml_file>
```

### Document Management

```http
GET /api/documents
Authorization: Bearer <jwt_token>

GET /api/documents/{document_id}
Authorization: Bearer <jwt_token>

GET /api/documents/{document_id}/results
Authorization: Bearer <jwt_token>
```

## Testing the Integration

### 1. Run Setup Script

```bash
cd backend
python setup_supabase.py
```

### 2. Test Database Connection

```python
from utils.database import get_db_connection

async def test_connection():
    db = await get_db_connection()
    print("Connection successful!")
```

### 3. Test File Upload

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer <your_jwt_token>" \
  -F "file=@path/to/your/file.xml"
```

## Monitoring and Logging

### Access Logging

All file operations are logged with:
- User ID
- File path
- Operation type (upload, download, delete)
- Timestamp
- Success/failure status

### Security Events

Security events are logged including:
- Failed authentication attempts
- Suspicious file uploads
- Access violations
- Rate limiting triggers

### Performance Monitoring

Monitor these metrics:
- File upload times
- Database query performance
- Storage usage
- API response times

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check environment variables
   - Verify Supabase project is active
   - Check network connectivity

2. **Authentication Errors**
   - Verify JWT token format
   - Check token expiration
   - Ensure user exists in Supabase

3. **File Upload Failures**
   - Check file size (max 10MB)
   - Verify file type (XML only)
   - Check storage bucket permissions

4. **RLS Policy Issues**
   - Verify policies are enabled
   - Check policy syntax
   - Test with different users

### Debug Mode

Enable debug logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Health Checks

The system provides health check endpoints:

```http
GET /health
GET /health/database
GET /health/storage
```

## Security Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **Token Management**: Implement token rotation
3. **Access Control**: Use principle of least privilege
4. **Monitoring**: Set up alerts for security events
5. **Backups**: Regular database and storage backups
6. **Updates**: Keep Supabase client library updated

## Production Deployment

### Environment Configuration

- Use production Supabase project
- Set strong service role key
- Configure proper CORS origins
- Enable audit logging

### Performance Optimization

- Enable connection pooling
- Configure caching strategies
- Set up CDN for static assets
- Monitor resource usage

### Backup Strategy

- Daily database backups
- File storage replication
- Configuration backups
- Disaster recovery plan

## Support

For issues with this integration:

1. Check the troubleshooting section
2. Review Supabase documentation
3. Check system logs
4. Contact development team

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://pydantic-docs.helpmanual.io/usage/settings/)