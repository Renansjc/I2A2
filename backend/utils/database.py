"""
Database connection and utilities for PostgreSQL/Supabase
"""

import asyncpg
from supabase import create_client, Client
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json
import uuid
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


class FileUploadManager:
    """Manager for file upload tracking and metadata operations"""
    
    @staticmethod
    def _generate_file_hash(content: str) -> str:
        """Generate SHA-256 hash for file content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    async def create_fiscal_document(
        user_id: str,
        filename: str,
        file_size: int,
        document_type: str,
        xml_content: str
    ) -> str:
        """Create a new fiscal document record and return document ID"""
        document_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO fiscal_documents (
            id, user_id, filename, file_size, document_type, xml_content
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                query, document_id, user_id, filename, file_size, document_type, xml_content
            )
            
        logger.info(
            "Created fiscal document record",
            document_id=document_id,
            filename=filename,
            document_type=document_type
        )
        
        return result['id']
    
    @staticmethod
    async def create_file_metadata(
        document_id: str,
        original_filename: str,
        mime_type: str = "application/xml",
        xml_content: str = ""
    ) -> str:
        """Create file metadata record"""
        file_hash = FileUploadManager._generate_file_hash(xml_content)
        file_extension = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
        
        query = """
        INSERT INTO file_metadata (
            document_id, original_filename, file_extension, mime_type, 
            file_hash, encoding, validation_status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                query, document_id, original_filename, file_extension, 
                mime_type, file_hash, 'UTF-8', 'pending'
            )
            
        logger.info(
            "Created file metadata record",
            document_id=document_id,
            file_hash=file_hash[:16] + "..."
        )
        
        return result['id']
    
    @staticmethod
    async def create_document_metadata(
        document_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Create document metadata extracted from XML"""
        query = """
        INSERT INTO document_metadata (
            document_id, cnpj_emitente, nome_emitente, inscricao_estadual_emitente,
            cnpj_destinatario, nome_destinatario, inscricao_estadual_destinatario,
            numero_documento, serie_documento, data_emissao, data_saida_entrada,
            valor_total, valor_tributos, valor_produtos, valor_servicos,
            natureza_operacao, tipo_operacao, codigo_municipio, uf, 
            ambiente_gerador, forma_pagamento
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, 
            $16, $17, $18, $19, $20, $21
        )
        RETURNING id
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                query,
                document_id,
                metadata.get('cnpj_emitente'),
                metadata.get('nome_emitente'),
                metadata.get('inscricao_estadual_emitente'),
                metadata.get('cnpj_destinatario'),
                metadata.get('nome_destinatario'),
                metadata.get('inscricao_estadual_destinatario'),
                metadata.get('numero_documento'),
                metadata.get('serie_documento'),
                metadata.get('data_emissao'),
                metadata.get('data_saida_entrada'),
                metadata.get('valor_total'),
                metadata.get('valor_tributos'),
                metadata.get('valor_produtos'),
                metadata.get('valor_servicos'),
                metadata.get('natureza_operacao'),
                metadata.get('tipo_operacao'),
                metadata.get('codigo_municipio'),
                metadata.get('uf'),
                metadata.get('ambiente_gerador'),
                metadata.get('forma_pagamento')
            )
            
        logger.info(
            "Created document metadata record",
            document_id=document_id,
            emitente=metadata.get('nome_emitente', 'Unknown')
        )
        
        return result['id']
    
    @staticmethod
    async def update_processing_status(
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update document processing status"""
        query = """
        UPDATE fiscal_documents 
        SET processing_status = $2,
            processing_started_at = CASE 
                WHEN $2 = 'processing' AND processing_started_at IS NULL 
                THEN NOW() 
                ELSE processing_started_at 
            END,
            processing_completed_at = CASE 
                WHEN $2 IN ('completed', 'error', 'cancelled') 
                THEN NOW() 
                ELSE processing_completed_at 
            END,
            error_message = $3,
            updated_at = NOW()
        WHERE id = $1
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, document_id, status, error_message)
            
        logger.info(
            "Updated document processing status",
            document_id=document_id,
            status=status,
            has_error=error_message is not None
        )
    
    @staticmethod
    async def get_document_by_id(document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get fiscal document by ID for specific user"""
        query = """
        SELECT fd.*, dm.*, fm.original_filename, fm.file_hash, fm.validation_status
        FROM fiscal_documents fd
        LEFT JOIN document_metadata dm ON fd.id = dm.document_id
        LEFT JOIN file_metadata fm ON fd.id = fm.document_id
        WHERE fd.id = $1 AND fd.user_id = $2
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, document_id, user_id)
            
        return dict(result) if result else None
    
    @staticmethod
    async def list_user_documents(
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List fiscal documents for a user with optional status filter"""
        base_query = """
        SELECT fd.id, fd.filename, fd.document_type, fd.processing_status,
               fd.upload_timestamp, fd.file_size,
               dm.nome_emitente, dm.valor_total, dm.data_emissao
        FROM fiscal_documents fd
        LEFT JOIN document_metadata dm ON fd.id = dm.document_id
        WHERE fd.user_id = $1
        """
        
        params = [user_id]
        param_count = 1
        
        if status_filter:
            param_count += 1
            base_query += f" AND fd.processing_status = ${param_count}"
            params.append(status_filter)
        
        base_query += f" ORDER BY fd.upload_timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, skip])
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch(base_query, *params)
            
        return [dict(row) for row in results]
    
    @staticmethod
    async def check_duplicate_file(file_hash: str) -> Optional[str]:
        """Check if file with same hash already exists"""
        query = """
        SELECT fd.id, fd.filename, fd.processing_status
        FROM file_metadata fm
        JOIN fiscal_documents fd ON fm.document_id = fd.id
        WHERE fm.file_hash = $1
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, file_hash)
            
        return dict(result) if result else None


class ProcessingStatusManager:
    """Manager for agent processing status tracking"""
    
    @staticmethod
    async def initialize_agent_statuses(document_id: str, agent_names: List[str]) -> None:
        """Initialize processing status for all agents"""
        query = """
        INSERT INTO document_processing_status (document_id, agent_name, status)
        VALUES ($1, $2, 'pending')
        ON CONFLICT (document_id, agent_name) DO NOTHING
        """
        
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                for agent_name in agent_names:
                    await conn.execute(query, document_id, agent_name)
        
        logger.info(
            "Initialized agent processing statuses",
            document_id=document_id,
            agent_count=len(agent_names)
        )
    
    @staticmethod
    async def update_agent_status(
        document_id: str,
        agent_name: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update processing status for specific agent"""
        query = """
        UPDATE document_processing_status 
        SET status = $3,
            started_at = CASE 
                WHEN $3 = 'in_progress' AND started_at IS NULL 
                THEN NOW() 
                ELSE started_at 
            END,
            completed_at = CASE 
                WHEN $3 IN ('completed', 'failed', 'skipped') 
                THEN NOW() 
                ELSE completed_at 
            END,
            error_message = $4,
            updated_at = NOW()
        WHERE document_id = $1 AND agent_name = $2
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, document_id, agent_name, status, error_message)
            
        logger.info(
            "Updated agent processing status",
            document_id=document_id,
            agent_name=agent_name,
            status=status
        )
    
    @staticmethod
    async def get_document_processing_status(document_id: str) -> List[Dict[str, Any]]:
        """Get processing status for all agents for a document"""
        query = """
        SELECT agent_name, status, started_at, completed_at, error_message, retry_count
        FROM document_processing_status
        WHERE document_id = $1
        ORDER BY created_at
        """
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, document_id)
            
        return [dict(row) for row in results]
    
    @staticmethod
    async def store_processing_result(
        document_id: str,
        agent_name: str,
        result_type: str,
        result_data: Dict[str, Any],
        confidence_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """Store processing result from an agent"""
        query = """
        INSERT INTO processing_results (
            document_id, agent_name, result_type, result_data,
            confidence_score, processing_time_ms
        ) VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (document_id, agent_name, result_type) 
        DO UPDATE SET 
            result_data = EXCLUDED.result_data,
            confidence_score = EXCLUDED.confidence_score,
            processing_time_ms = EXCLUDED.processing_time_ms,
            created_at = NOW()
        RETURNING id
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                query, document_id, agent_name, result_type,
                json.dumps(result_data), confidence_score, processing_time_ms
            )
            
        logger.info(
            "Stored processing result",
            document_id=document_id,
            agent_name=agent_name,
            result_type=result_type,
            confidence_score=confidence_score
        )
        
        return result['id']
    
    @staticmethod
    async def get_processing_results(
        document_id: str,
        agent_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get processing results for a document, optionally filtered by agent"""
        base_query = """
        SELECT agent_name, result_type, result_data, confidence_score,
               processing_time_ms, created_at
        FROM processing_results
        WHERE document_id = $1
        """
        
        params = [document_id]
        
        if agent_name:
            base_query += " AND agent_name = $2"
            params.append(agent_name)
            
        base_query += " ORDER BY created_at DESC"
        
        async with db_pool.acquire() as conn:
            results = await conn.fetch(base_query, *params)
            
        return [dict(row) for row in results]

class
 SupabaseStorageManager:
    """Manager for Supabase Storage operations"""
    
    @staticmethod
    def upload_xml_file(
        file_content: str,
        filename: str,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Upload XML file to Supabase Storage"""
        try:
            client = get_supabase_client()
            
            # Create file path with user and document organization
            file_path = f"{user_id}/{document_id}/{filename}"
            
            # Upload file to storage bucket
            result = client.storage.from_(settings.STORAGE_BUCKET).upload(
                file_path,
                file_content.encode('utf-8'),
                file_options={
                    "content-type": "application/xml",
                    "cache-control": "3600"
                }
            )
            
            if result.error:
                logger.error(
                    "Failed to upload file to Supabase Storage",
                    error=result.error,
                    filename=filename,
                    document_id=document_id
                )
                raise Exception(f"Storage upload failed: {result.error}")
            
            # Get public URL for the uploaded file
            public_url = client.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
            
            logger.info(
                "Successfully uploaded file to Supabase Storage",
                filename=filename,
                document_id=document_id,
                file_path=file_path
            )
            
            return {
                "file_path": file_path,
                "public_url": public_url,
                "bucket": settings.STORAGE_BUCKET
            }
            
        except Exception as e:
            logger.error(
                "Error uploading file to Supabase Storage",
                error=str(e),
                filename=filename,
                document_id=document_id
            )
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """Get public URL for a file in Supabase Storage"""
        try:
            client = get_supabase_client()
            return client.storage.from_(settings.STORAGE_BUCKET).get_public_url(file_path)
        except Exception as e:
            logger.error("Error getting file URL", error=str(e), file_path=file_path)
            raise
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            client = get_supabase_client()
            result = client.storage.from_(settings.STORAGE_BUCKET).remove([file_path])
            
            if result.error:
                logger.error(
                    "Failed to delete file from Supabase Storage",
                    error=result.error,
                    file_path=file_path
                )
                return False
            
            logger.info("Successfully deleted file from Supabase Storage", file_path=file_path)
            return True
            
        except Exception as e:
            logger.error("Error deleting file", error=str(e), file_path=file_path)
            return False
    
    @staticmethod
    def list_user_files(user_id: str) -> List[Dict[str, Any]]:
        """List all files for a user in Supabase Storage"""
        try:
            client = get_supabase_client()
            result = client.storage.from_(settings.STORAGE_BUCKET).list(user_id)
            
            if result.error:
                logger.error(
                    "Failed to list user files",
                    error=result.error,
                    user_id=user_id
                )
                return []
            
            return result.data or []
            
        except Exception as e:
            logger.error("Error listing user files", error=str(e), user_id=user_id)
            return []


class DocumentLinkingManager:
    """Manager for linking uploaded documents to processed fiscal documents"""
    
    @staticmethod
    async def link_to_nfe(document_id: str, chave_nfe: str) -> None:
        """Link fiscal document to processed NF-e"""
        query = """
        UPDATE fiscal_documents 
        SET chave_nfe = $2, updated_at = NOW()
        WHERE id = $1
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, document_id, chave_nfe)
            
        logger.info(
            "Linked document to NF-e",
            document_id=document_id,
            chave_nfe=chave_nfe
        )
    
    @staticmethod
    async def link_to_nfse(document_id: str, id_nfse: str) -> None:
        """Link fiscal document to processed NFS-e"""
        query = """
        UPDATE fiscal_documents 
        SET id_nfse = $2, updated_at = NOW()
        WHERE id = $1
        """
        
        async with db_pool.acquire() as conn:
            await conn.execute(query, document_id, id_nfse)
            
        logger.info(
            "Linked document to NFS-e",
            document_id=document_id,
            id_nfse=id_nfse
        )
    
    @staticmethod
    async def get_linked_documents(document_id: str) -> Dict[str, Any]:
        """Get linked fiscal document data"""
        query = """
        SELECT fd.chave_nfe, fd.id_nfse,
               nfe.numero_nf as nfe_numero, nfe.valor_total_nf as nfe_valor_total,
               nfse.numero_nfse, nfse.valor_total_servicos as nfse_valor_total
        FROM fiscal_documents fd
        LEFT JOIN nfe_main nfe ON fd.chave_nfe = nfe.chave_nfe
        LEFT JOIN nfse_main nfse ON fd.id_nfse = nfse.id_nfse
        WHERE fd.id = $1
        """
        
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, document_id)
            
        return dict(result) if result else {}