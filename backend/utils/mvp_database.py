"""
MVP Database utilities for simplified Supabase integration
Simplified version without RLS for MVP deployment
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


class MVPSupabaseClient:
    """Simplified Supabase client for MVP without RLS complexity"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._connected = False
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client using service key for direct access"""
        if self._client is None:
            # Use service key for direct database access (bypasses RLS)
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key,  # Always use service key for MVP
                options=ClientOptions(
                    postgrest_client_timeout=30,
                    storage_client_timeout=30
                )
            )
            self._connected = True
            logger.info("MVP Supabase client initialized", url=settings.supabase_url)
        return self._client
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self._client is not None


# Global MVP Supabase client
mvp_supabase = MVPSupabaseClient()


class MVPDatabaseManager:
    """Simplified Database Manager for MVP"""
    
    def __init__(self):
        self.supabase = mvp_supabase
    
    async def connect(self):
        """Initialize database connection"""
        try:
            # Test connection with a simple query
            result = await asyncio.to_thread(
                lambda: self.supabase.client.table('fiscal_documents').select('id').limit(1).execute()
            )
            logger.info("MVP Database connected successfully")
            return True
        except Exception as e:
            logger.error("Failed to connect to MVP database", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        logger.info("MVP Database disconnected")


class MVPDocumentManager:
    """Simplified document manager for MVP"""
    
    @staticmethod
    async def create_document(
        filename: str,
        file_path: str,
        status: str = 'uploaded'
    ) -> str:
        """Create a new fiscal document record"""
        try:
            document_id = str(uuid.uuid4())
            
            document_data = {
                'id': document_id,
                'filename': filename,
                'file_path': file_path,
                'status': status,
                'processing_progress': 0,
                'uploaded_at': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('fiscal_documents').insert(document_data).execute()
            )
            
            logger.info(
                "MVP Document created",
                document_id=document_id,
                filename=filename,
                status=status
            )
            
            return document_id
            
        except Exception as e:
            logger.error("Failed to create MVP document", error=str(e), filename=filename)
            raise
    
    @staticmethod
    async def update_document_status(
        document_id: str,
        status: str,
        processing_progress: Optional[int] = None
    ):
        """Update document processing status"""
        try:
            update_data = {
                'status': status
            }
            
            if processing_progress is not None:
                update_data['processing_progress'] = processing_progress
            
            if status == 'completed':
                update_data['processed_at'] = datetime.now(timezone.utc).isoformat()
            
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('fiscal_documents')
                .update(update_data)
                .eq('id', document_id)
                .execute()
            )
            
            logger.info(
                "MVP Document status updated",
                document_id=document_id,
                status=status,
                progress=processing_progress
            )
            
        except Exception as e:
            logger.error("Failed to update MVP document status", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def get_documents(
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of documents"""
        try:
            query = mvp_supabase.client.table('fiscal_documents').select('*')
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            result = await asyncio.to_thread(
                lambda: query.range(skip, skip + limit - 1).order('created_at', desc=True).execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get MVP documents", error=str(e))
            raise
    
    @staticmethod
    async def get_document_by_id(document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('fiscal_documents')
                .select('*')
                .eq('id', document_id)
                .single()
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get MVP document by ID", error=str(e), document_id=document_id)
            return None


class MVPExtractedDataManager:
    """Manager for extracted data from XML documents"""
    
    @staticmethod
    async def store_extracted_data(
        document_id: str,
        emitente: Dict[str, Any],
        destinatario: Dict[str, Any],
        valor_total: Decimal,
        total_impostos: Decimal,
        data_emissao: datetime,
        numero_nota: str,
        chave_acesso: str
    ) -> str:
        """Store extracted data from XML processing"""
        try:
            extracted_id = str(uuid.uuid4())
            
            extracted_data = {
                'id': extracted_id,
                'document_id': document_id,
                'emitente': json.dumps(emitente),
                'destinatario': json.dumps(destinatario),
                'valor_total': float(valor_total),
                'total_impostos': float(total_impostos),
                'data_emissao': data_emissao.date().isoformat(),
                'numero_nota': numero_nota,
                'chave_acesso': chave_acesso,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('extracted_data').insert(extracted_data).execute()
            )
            
            logger.info(
                "MVP Extracted data stored",
                document_id=document_id,
                extracted_id=extracted_id,
                valor_total=float(valor_total)
            )
            
            return extracted_id
            
        except Exception as e:
            logger.error("Failed to store MVP extracted data", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def get_extracted_data(document_id: str) -> Optional[Dict[str, Any]]:
        """Get extracted data for a document"""
        try:
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('extracted_data')
                .select('*')
                .eq('document_id', document_id)
                .single()
                .execute()
            )
            
            # Parse JSONB fields
            data = result.data
            if data:
                data['emitente'] = json.loads(data['emitente']) if isinstance(data['emitente'], str) else data['emitente']
                data['destinatario'] = json.loads(data['destinatario']) if isinstance(data['destinatario'], str) else data['destinatario']
            
            return data
            
        except Exception as e:
            logger.error("Failed to get MVP extracted data", error=str(e), document_id=document_id)
            return None


class MVPDocumentItemsManager:
    """Manager for document items (products/services)"""
    
    @staticmethod
    async def store_document_items(
        document_id: str,
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """Store document items with AI categorization"""
        try:
            item_ids = []
            
            for item in items:
                item_id = str(uuid.uuid4())
                
                item_data = {
                    'id': item_id,
                    'document_id': document_id,
                    'descricao': item['descricao'],
                    'quantidade': float(item.get('quantidade', 1)),
                    'valor_unitario': float(item['valor_unitario']),
                    'valor_total': float(item['valor_total']),
                    'categoria': item.get('categoria'),
                    'categoria_confianca': float(item.get('categoria_confianca', 0)) if item.get('categoria_confianca') else None,
                    'ncm': item.get('ncm'),
                    'cfop': item.get('cfop'),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                result = await asyncio.to_thread(
                    lambda: mvp_supabase.client.table('document_items').insert(item_data).execute()
                )
                
                item_ids.append(item_id)
            
            logger.info(
                "MVP Document items stored",
                document_id=document_id,
                items_count=len(items)
            )
            
            return item_ids
            
        except Exception as e:
            logger.error("Failed to store MVP document items", error=str(e), document_id=document_id)
            raise
    
    @staticmethod
    async def get_document_items(document_id: str) -> List[Dict[str, Any]]:
        """Get items for a document"""
        try:
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('document_items')
                .select('*')
                .eq('document_id', document_id)
                .order('created_at')
                .execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get MVP document items", error=str(e), document_id=document_id)
            return []


class MVPExecutiveReportsManager:
    """Manager for executive reports"""
    
    @staticmethod
    async def create_report(
        title: str,
        file_path: str,
        report_type: str = 'executive_summary',
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        generation_time_ms: Optional[int] = None
    ) -> str:
        """Create a new executive report record"""
        try:
            report_id = str(uuid.uuid4())
            
            report_data = {
                'id': report_id,
                'title': title,
                'file_path': file_path,
                'report_type': report_type,
                'period_start': period_start.date().isoformat() if period_start else None,
                'period_end': period_end.date().isoformat() if period_end else None,
                'generation_time_ms': generation_time_ms,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = await asyncio.to_thread(
                lambda: mvp_supabase.client.table('executive_reports').insert(report_data).execute()
            )
            
            logger.info(
                "MVP Executive report created",
                report_id=report_id,
                title=title,
                report_type=report_type
            )
            
            return report_id
            
        except Exception as e:
            logger.error("Failed to create MVP executive report", error=str(e), title=title)
            raise
    
    @staticmethod
    async def get_reports(
        skip: int = 0,
        limit: int = 50,
        report_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of executive reports"""
        try:
            query = mvp_supabase.client.table('executive_reports').select('*')
            
            if report_type:
                query = query.eq('report_type', report_type)
            
            result = await asyncio.to_thread(
                lambda: query.range(skip, skip + limit - 1).order('generated_at', desc=True).execute()
            )
            
            return result.data
            
        except Exception as e:
            logger.error("Failed to get MVP executive reports", error=str(e))
            raise


class MVPStorageManager:
    """Simplified storage manager for MVP"""
    
    @staticmethod
    def upload_xml_file(
        file_content: str,
        filename: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Upload XML file to Supabase Storage"""
        try:
            # Create simple file path
            file_path = f"xml_files/{document_id}/{filename}"
            
            # Upload file to storage bucket
            result = mvp_supabase.client.storage.from_(settings.storage_bucket).upload(
                path=file_path,
                file=file_content.encode('utf-8'),
                file_options={
                    'content-type': 'application/xml',
                    'upsert': True
                }
            )
            
            logger.info(
                "MVP File uploaded to storage",
                filename=filename,
                document_id=document_id,
                file_path=file_path
            )
            
            return {
                'file_path': file_path,
                'bucket': settings.storage_bucket,
                'public_url': mvp_supabase.client.storage.from_(settings.storage_bucket).get_public_url(file_path)
            }
            
        except Exception as e:
            logger.error("Failed to upload MVP file to storage", error=str(e), filename=filename)
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """Get public URL for a file in storage"""
        try:
            return mvp_supabase.client.storage.from_(settings.storage_bucket).get_public_url(file_path)
        except Exception as e:
            logger.error("Failed to get MVP file URL", error=str(e), file_path=file_path)
            raise


# Convenience function to get MVP database manager
async def get_mvp_db() -> MVPDatabaseManager:
    """Get MVP database manager"""
    db_manager = MVPDatabaseManager()
    await db_manager.connect()
    return db_manager