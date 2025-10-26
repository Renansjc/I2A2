"""
Database utilities for Supabase integration
"""

import structlog
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import json

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from .config import settings

logger = structlog.get_logger()


class SupabaseClient:
    """Supabase client wrapper with connection management"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._connected = False
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10
                )
            )
            self._connected = True
            logger.info("Supabase client initialized", url=settings.supabase_url)
        return self._client
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client is not None


# Global Supabase client instance
supabase_client = SupabaseClient()


class DatabaseManager:
    """Database Manager with Supabase integration"""
    
    def __init__(self):
        self.supabase = supabase_client
    
    async def connect(self):
        """Initialize database connection"""
        try:
            # Test connection with a simple query
            result = await asyncio.to_thread(
                lambda: self.supabase.client.table('fiscal_documents').select('id').limit(1).execute()
            )
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        # Supabase client doesn't need explicit disconnection
        logger.info("Database disconnected")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None):
        """Execute raw SQL query (for complex operations)"""
        try:
            # Note: Supabase doesn't directly support raw SQL from client
            # This would typically be done through stored procedures or RPC calls
            logger.warning("Raw SQL execution not directly supported in Supabase client")
            return {"rows": [], "count": 0}
        except Exception as e:
            logger.error("Query execution failed", query=query[:100], error=str(e))
            raise


async def get_db_connection():
    """Get database connection"""
    db_manager = DatabaseManager()
    await db_manager.connect()
    return db_manager


class FileUploadManager:
    """Manager for file upload operations"""
    
    @staticmethod
    async def create_document_record(
        filename: str,
        file_size: int,
        document_type: str,
        xml_content: str,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new document record in the database"""
        try:
            document_id = str(uuid.uuid4())
            
            document_data = {
                'id': document_id,
                'user_id': user_id,
                'filename': filename,
                'file_size': file_size,
                'document_type': document_type,
                'xml_content': xml_content,
                'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                'processing_status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: supabase_client.client.table('fiscal_documents').insert(document_data).execute()
            )
            
            logger.info(
                "Document record created",
                document_id=document_id,
                filename=filename,
                document_type=document_type
            )
            
            return document_id
            
        except Exception as e:
            logger.error("Failed to create document record", error=str(e), filename=filename)
            raise
    
    @staticmethod
    async def store_document_metadata(
        document_id: str,
        metadata: Dict[str, Any]
    ):
        """Store document metadata"""
        try:
            metadata_data = {
                'id': str(uuid.uuid4()),
                'document_id': document_id,
                'cnpj_emitente': metadata.get('cnpj_emitente'),
                'nome_emitente': metadata.get('nome_emitente'),
                'cnpj_destinatario': metadata.get('cnpj_destinatario'),
                'nome_destinatario': metadata.get('nome_destinatario'),
                'numero_documento': metadata.get('numero_documento'),
                'serie_documento': metadata.get('serie_documento'),
                'data_emissao': metadata.get('data_emissao'),
                'valor_total': float(metadata['valor_total']) if metadata.get('valor_total') else None,
                'valor_tributos': float(metadata['valor_tributos']) if metadata.get('valor_tributos') else None,
                'natureza_operacao': metadata.get('natureza_operacao'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: supabase_client.client.table('document_metadata').insert(metadata_data).execute()
            )
            
            logger.info("Document metadata stored", document_id=document_id)
            
        except Exception as e:
            logger.error("Failed to store document metadata", error=str(e), document_id=document_id)
            raise


class ProcessingStatusManager:
    """Manager for processing status tracking"""
    
    @staticmethod
    async def update_document_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update document processing status"""
        try:
            update_data = {
                'processing_status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if status == 'processing':
                update_data['processing_started_at'] = datetime.now(timezone.utc).isoformat()
            elif status == 'completed':
                update_data['processing_completed_at'] = datetime.now(timezone.utc).isoformat()
            elif status == 'error':
                update_data['error_message'] = error_message
            
            result = await asyncio.to_thread(
                lambda: supabase_client.client.table('fiscal_documents')
                .update(update_data)
                .eq('id', document_id)
                .execute()
            )
            
            logger.info(
                "Document status updated",
                document_id=document_id,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error("Failed to update document status", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def update_agent_status(
        document_id: str, 
        agent_name: str, 
        status: str, 
        error_message: Optional[str] = None
    ):
        """Update agent processing status"""
        try:
            # This could be stored in a separate agent_status table if needed
            # For now, we'll log it and update the main document status
            await ProcessingStatusManager.update_document_status(
                document_id, status, error_message
            )
            
            logger.info(
                "Agent status updated",
                document_id=document_id,
                agent_name=agent_name,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error("Failed to update agent status", error=str(e), document_id=document_id)
            raise
    
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
        try:
            result_record = {
                'id': str(uuid.uuid4()),
                'document_id': document_id,
                'agent_name': agent_name,
                'result_type': result_type,
                'result_data': json.dumps(result_data),
                'confidence_score': confidence_score,
                'processing_time_ms': processing_time_ms,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: supabase_client.client.table('processing_results').insert(result_record).execute()
            )
            
            logger.info(
                "Processing result stored",
                document_id=document_id,
                agent_name=agent_name,
                result_type=result_type,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error("Failed to store processing result", error=str(e), document_id=document_id)
            raise


class SupabaseStorageManager:
    """Manager for Supabase Storage operations"""
    
    @staticmethod
    def upload_xml_file(
        file_content: str,
        filename: str,
        document_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload XML file to Supabase Storage"""
        try:
            # Create file path with user organization
            file_path = f"{user_id or 'anonymous'}/{document_id}/{filename}"
            
            # Upload file to storage bucket
            result = supabase_client.client.storage.from_(settings.storage_bucket).upload(
                path=file_path,
                file=file_content.encode('utf-8'),
                file_options={
                    'content-type': 'application/xml',
                    'upsert': True
                }
            )
            
            logger.info(
                "File uploaded to Supabase Storage",
                filename=filename,
                document_id=document_id,
                file_path=file_path
            )
            
            return {
                'file_path': file_path,
                'bucket': settings.storage_bucket,
                'public_url': supabase_client.client.storage.from_(settings.storage_bucket).get_public_url(file_path)
            }
            
        except Exception as e:
            logger.error("Failed to upload file to Supabase Storage", error=str(e), filename=filename)
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """Get public URL for a file in storage"""
        try:
            return supabase_client.client.storage.from_(settings.storage_bucket).get_public_url(file_path)
        except Exception as e:
            logger.error("Failed to get file URL", error=str(e), file_path=file_path)
            raise
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file from storage"""
        try:
            result = supabase_client.client.storage.from_(settings.storage_bucket).remove([file_path])
            logger.info("File deleted from storage", file_path=file_path)
            return True
        except Exception as e:
            logger.error("Failed to delete file from storage", error=str(e), file_path=file_path)
            return False


class DocumentManager:
    """Manager for document operations"""
    
    @staticmethod
    async def get_documents(
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get list of documents for a user"""
        try:
            query = supabase_client.client.table('fiscal_documents').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = await asyncio.to_thread(
                lambda: query.range(skip, skip + limit - 1).order('created_at', desc=True).execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get documents", error=str(e), user_id=user_id)
            raise
    
    @staticmethod
    async def get_document_details(
        document_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a document"""
        try:
            query = supabase_client.client.table('fiscal_documents').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = await asyncio.to_thread(
                lambda: query.eq('id', document_id).single().execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get document details", error=str(e), document_id=document_id)
            return None
    
    @staticmethod
    async def get_processing_results(
        document_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get processing results for a document"""
        try:
            # First verify user has access to the document
            if user_id:
                doc = await DocumentManager.get_document_details(document_id, user_id)
                if not doc:
                    return []
            
            result = await asyncio.to_thread(
                lambda: supabase_client.client.table('processing_results')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at', desc=True)
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get processing results", error=str(e), document_id=document_id)
            raise