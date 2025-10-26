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
    
    def __init__(self, use_service_key: bool = False):
        self._client: Optional[Client] = None
        self._connected = False
        self._use_service_key = use_service_key
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            # Use service key for administrative operations (bypasses RLS)
            # Use anon key for regular user operations (respects RLS)
            api_key = settings.supabase_service_key if self._use_service_key else settings.supabase_anon_key
            
            self._client = create_client(
                settings.supabase_url,
                api_key,
                options=ClientOptions(
                    postgrest_client_timeout=10,
                    storage_client_timeout=10
                )
            )
            self._connected = True
            key_type = "service" if self._use_service_key else "anon"
            logger.info("Supabase client initialized", url=settings.supabase_url, key_type=key_type)
        return self._client
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client is not None


# Global Supabase client instances
supabase_client = SupabaseClient(use_service_key=False)  # For regular operations
supabase_admin_client = SupabaseClient(use_service_key=True)  # For admin/test operations


def get_supabase_client(admin_mode: bool = False) -> SupabaseClient:
    """Get appropriate Supabase client based on context"""
    return supabase_admin_client if admin_mode else supabase_client


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
        user_id: Optional[str] = None,
        admin_mode: bool = False
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
            
            # Use admin client for test operations to bypass RLS
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('fiscal_documents').insert(document_data).execute()
            )
            
            logger.info(
                "Document record created",
                document_id=document_id,
                filename=filename,
                document_type=document_type,
                admin_mode=admin_mode
            )
            
            return document_id
            
        except Exception as e:
            logger.error("Failed to create document record", error=str(e), filename=filename)
            raise
    
    @staticmethod
    async def create_fiscal_document(
        user_id: str,
        filename: str,
        file_size: int,
        document_type: str,
        xml_content: str,
        admin_mode: bool = False
    ) -> str:
        """Create a fiscal document record (alias for create_document_record)"""
        return await FileUploadManager.create_document_record(
            filename=filename,
            file_size=file_size,
            document_type=document_type,
            xml_content=xml_content,
            user_id=user_id,
            admin_mode=admin_mode
        )
    
    @staticmethod
    async def create_file_metadata(
        document_id: str,
        original_filename: str,
        mime_type: str,
        xml_content: str,
        admin_mode: bool = False
    ):
        """Create file metadata record"""
        try:
            import hashlib
            
            # Generate file hash
            file_hash = hashlib.sha256(xml_content.encode('utf-8')).hexdigest()
            
            metadata_data = {
                'id': str(uuid.uuid4()),
                'document_id': document_id,
                'original_filename': original_filename,
                'file_extension': '.xml',
                'mime_type': mime_type,
                'file_hash': file_hash,
                'encoding': 'UTF-8',
                'xml_version': '1.0',
                'xml_encoding': 'UTF-8',
                'validation_status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('file_metadata').insert(metadata_data).execute()
            )
            
            logger.info("File metadata created", document_id=document_id, admin_mode=admin_mode)
            
        except Exception as e:
            logger.error("Failed to create file metadata", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def create_document_metadata(
        document_id: str,
        metadata: Dict[str, Any]
    ):
        """Create document metadata record (alias for store_document_metadata)"""
        await FileUploadManager.store_document_metadata(document_id, metadata)
    
    @staticmethod
    async def store_document_metadata(
        document_id: str,
        metadata: Dict[str, Any],
        admin_mode: bool = False
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
                'data_emissao': metadata.get('data_emissao').isoformat() if metadata.get('data_emissao') else None,
                'valor_total': float(metadata['valor_total']) if metadata.get('valor_total') else None,
                'valor_tributos': float(metadata['valor_tributos']) if metadata.get('valor_tributos') else None,
                'natureza_operacao': metadata.get('natureza_operacao'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('document_metadata').insert(metadata_data).execute()
            )
            
            logger.info("Document metadata stored", document_id=document_id, admin_mode=admin_mode)
            
        except Exception as e:
            logger.error("Failed to store document metadata", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def update_processing_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update document processing status"""
        await ProcessingStatusManager.update_document_status(document_id, status, error_message)
    
    @staticmethod
    async def list_user_documents(
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List documents for a user with optional filtering"""
        try:
            query = supabase_client.client.table('fiscal_documents').select('''
                *,
                document_metadata (
                    nome_emitente,
                    valor_total,
                    data_emissao
                )
            ''')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            if status_filter:
                query = query.eq('processing_status', status_filter)
            
            result = await asyncio.to_thread(
                lambda: query.range(skip, skip + limit - 1).order('created_at', desc=True).execute()
            )
            
            # Flatten the nested metadata
            documents = []
            for doc in result.data:
                flattened_doc = dict(doc)
                if doc.get('document_metadata') and len(doc['document_metadata']) > 0:
                    metadata = doc['document_metadata'][0]
                    flattened_doc.update({
                        'nome_emitente': metadata.get('nome_emitente'),
                        'valor_total': metadata.get('valor_total'),
                        'data_emissao': metadata.get('data_emissao')
                    })
                # Remove the nested metadata
                flattened_doc.pop('document_metadata', None)
                documents.append(flattened_doc)
            
            return documents
            
        except Exception as e:
            logger.error("Failed to list user documents", error=str(e), user_id=user_id)
            raise
    
    @staticmethod
    async def get_document_by_id(
        document_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID with optional user filtering"""
        try:
            query = supabase_client.client.table('fiscal_documents').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = await asyncio.to_thread(
                lambda: query.eq('id', document_id).single().execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get document by ID", error=str(e), document_id=document_id)
            return None


class ProcessingStatusManager:
    """Manager for processing status tracking"""
    
    @staticmethod
    async def update_document_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None,
        admin_mode: bool = False
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
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('fiscal_documents')
                .update(update_data)
                .eq('id', document_id)
                .execute()
            )
            
            logger.info(
                "Document status updated",
                document_id=document_id,
                status=status,
                error_message=error_message,
                admin_mode=admin_mode
            )
            
        except Exception as e:
            logger.error("Failed to update document status", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def update_agent_status(
        document_id: str, 
        agent_name: str, 
        status: str, 
        error_message: Optional[str] = None,
        admin_mode: bool = False
    ):
        """Update agent processing status"""
        try:
            # Update or insert agent status record
            status_data = {
                'document_id': document_id,
                'agent_name': agent_name,
                'status': status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if status == 'in_progress':
                status_data['started_at'] = datetime.now(timezone.utc).isoformat()
            elif status in ['completed', 'failed']:
                status_data['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            if error_message:
                status_data['error_message'] = error_message
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            # Try to update existing record, if not exists, insert new one
            try:
                result = await asyncio.to_thread(
                    lambda: client.client.table('document_processing_status')
                    .update(status_data)
                    .eq('document_id', document_id)
                    .eq('agent_name', agent_name)
                    .execute()
                )
                
                # If no rows were updated, insert new record
                if not result.data:
                    status_data['id'] = str(uuid.uuid4())
                    status_data['created_at'] = datetime.now(timezone.utc).isoformat()
                    
                    result = await asyncio.to_thread(
                        lambda: client.client.table('document_processing_status')
                        .insert(status_data)
                        .execute()
                    )
                    
            except Exception:
                # If update fails, try insert
                status_data['id'] = str(uuid.uuid4())
                status_data['created_at'] = datetime.now(timezone.utc).isoformat()
                
                result = await asyncio.to_thread(
                    lambda: client.client.table('document_processing_status')
                    .insert(status_data)
                    .execute()
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
    async def initialize_agent_statuses(
        document_id: str,
        agent_names: List[str],
        admin_mode: bool = False
    ):
        """Initialize agent statuses for a document"""
        try:
            for agent_name in agent_names:
                await ProcessingStatusManager.update_agent_status(
                    document_id, agent_name, "pending", admin_mode=admin_mode
                )
            
            logger.info(
                "Agent statuses initialized",
                document_id=document_id,
                agents=agent_names,
                admin_mode=admin_mode
            )
            
        except Exception as e:
            logger.error("Failed to initialize agent statuses", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def get_document_processing_status(
        document_id: str,
        admin_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get processing status for all agents of a document"""
        try:
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('document_processing_status')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at', desc=True)
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get document processing status", error=str(e), document_id=document_id)
            return []
    
    @staticmethod
    async def get_processing_results(
        document_id: str,
        admin_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get processing results for a document"""
        try:
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('processing_results')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at', desc=True)
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get processing results", error=str(e), document_id=document_id)
            return []
    
    @staticmethod
    async def store_processing_result(
        document_id: str,
        agent_name: str,
        result_type: str,
        result_data: Dict[str, Any],
        confidence_score: float,
        processing_time_ms: int,
        admin_mode: bool = False
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
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('processing_results').insert(result_record).execute()
            )
            
            logger.info(
                "Processing result stored",
                document_id=document_id,
                agent_name=agent_name,
                result_type=result_type,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                admin_mode=admin_mode
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
        limit: int = 100,
        admin_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get list of documents for a user"""
        try:
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            query = client.client.table('fiscal_documents').select('*')
            
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
        user_id: Optional[str] = None,
        admin_mode: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a document"""
        try:
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            query = client.client.table('fiscal_documents').select('*')
            
            if user_id and not admin_mode:  # Skip user filtering in admin mode
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
        user_id: Optional[str] = None,
        admin_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """Get processing results for a document"""
        try:
            # First verify user has access to the document (skip in admin mode)
            if user_id and not admin_mode:
                doc = await DocumentManager.get_document_details(document_id, user_id, admin_mode)
                if not doc:
                    return []
            
            # Use admin client for test operations
            client = get_supabase_client(admin_mode)
            
            result = await asyncio.to_thread(
                lambda: client.client.table('processing_results')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at', desc=True)
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get processing results", error=str(e), document_id=document_id)
            raise