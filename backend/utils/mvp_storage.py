"""
MVP Storage Manager for XML file handling
Simplified storage with validation and backup features
"""

import structlog
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from pathlib import Path

from .mvp_config import mvp_settings
from .mvp_database import mvp_supabase

logger = structlog.get_logger()


class MVPStorageManager:
    """Simplified storage manager for MVP XML file handling"""
    
    @staticmethod
    def validate_xml_file(file_content: str, filename: str) -> Dict[str, Any]:
        """Validate XML file content and structure"""
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        try:
            # Check file extension
            if not filename.lower().endswith('.xml'):
                validation_result['errors'].append('File must have .xml extension')
                return validation_result
            
            # Check file size
            file_size = len(file_content.encode('utf-8'))
            if file_size > mvp_settings.max_file_size:
                validation_result['errors'].append(f'File size ({file_size} bytes) exceeds limit ({mvp_settings.max_file_size} bytes)')
                return validation_result
            
            # Validate XML structure
            try:
                root = ET.fromstring(file_content)
                validation_result['file_info']['root_tag'] = root.tag
                validation_result['file_info']['namespace'] = root.tag.split('}')[0][1:] if '}' in root.tag else None
            except ET.ParseError as e:
                validation_result['errors'].append(f'Invalid XML structure: {str(e)}')
                return validation_result
            
            # Check for Brazilian fiscal document indicators
            fiscal_indicators = [
                'NFe',  # NF-e
                'nfeProc',  # NF-e processed
                'CompNfse',  # NFS-e
                'nfse',  # NFS-e
                'infNFe',  # NF-e info
                'infNfse'   # NFS-e info
            ]
            
            xml_content_lower = file_content.lower()
            found_indicators = [indicator for indicator in fiscal_indicators if indicator.lower() in xml_content_lower]
            
            if not found_indicators:
                validation_result['warnings'].append('File does not appear to be a Brazilian fiscal document (NF-e/NFS-e)')
            else:
                validation_result['file_info']['document_type'] = 'NFE' if any('nfe' in ind.lower() for ind in found_indicators) else 'NFSE'
            
            # Generate file hash for duplicate detection
            file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
            validation_result['file_info']['file_hash'] = file_hash
            validation_result['file_info']['file_size'] = file_size
            validation_result['file_info']['mime_type'] = 'application/xml'
            
            validation_result['is_valid'] = True
            logger.info("XML file validated successfully", filename=filename, file_size=file_size)
            
        except Exception as e:
            validation_result['errors'].append(f'Validation error: {str(e)}')
            logger.error("XML file validation failed", error=str(e), filename=filename)
        
        return validation_result
    
    @staticmethod
    async def upload_xml_file(
        file_content: str,
        filename: str,
        document_id: str
    ) -> Dict[str, Any]:
        """Upload XML file to Supabase Storage with validation"""
        try:
            # Validate file first
            validation = MVPStorageManager.validate_xml_file(file_content, filename)
            if not validation['is_valid']:
                raise ValueError(f"File validation failed: {', '.join(validation['errors'])}")
            
            # Create organized file path
            timestamp = datetime.now(timezone.utc).strftime('%Y/%m/%d')
            file_path = f"xml_files/{timestamp}/{document_id}/{filename}"
            
            # Upload to Supabase Storage
            result = mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).upload(
                path=file_path,
                file=file_content.encode('utf-8'),
                file_options={
                    'content-type': 'application/xml',
                    'upsert': True,
                    'cache-control': '3600'  # Cache for 1 hour
                }
            )
            
            # Get public URL
            public_url = mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).get_public_url(file_path)
            
            upload_result = {
                'success': True,
                'file_path': file_path,
                'public_url': public_url,
                'bucket': mvp_settings.storage_bucket,
                'file_info': validation['file_info'],
                'validation_warnings': validation['warnings']
            }
            
            logger.info(
                "XML file uploaded successfully",
                filename=filename,
                document_id=document_id,
                file_path=file_path,
                file_size=validation['file_info']['file_size']
            )
            
            return upload_result
            
        except Exception as e:
            logger.error("Failed to upload XML file", error=str(e), filename=filename, document_id=document_id)
            raise
    
    @staticmethod
    def get_file_url(file_path: str) -> str:
        """Get public URL for a file"""
        try:
            return mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).get_public_url(file_path)
        except Exception as e:
            logger.error("Failed to get file URL", error=str(e), file_path=file_path)
            raise
    
    @staticmethod
    def download_file(file_path: str) -> bytes:
        """Download file content from storage"""
        try:
            result = mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).download(file_path)
            logger.info("File downloaded successfully", file_path=file_path)
            return result
        except Exception as e:
            logger.error("Failed to download file", error=str(e), file_path=file_path)
            raise
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Delete file from storage"""
        try:
            result = mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).remove([file_path])
            logger.info("File deleted successfully", file_path=file_path)
            return True
        except Exception as e:
            logger.error("Failed to delete file", error=str(e), file_path=file_path)
            return False
    
    @staticmethod
    def list_files(
        prefix: str = "",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List files in storage bucket"""
        try:
            result = mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).list(
                path=prefix,
                limit=limit,
                offset=offset
            )
            
            logger.info("Files listed successfully", prefix=prefix, count=len(result))
            return result
        except Exception as e:
            logger.error("Failed to list files", error=str(e), prefix=prefix)
            raise
    
    @staticmethod
    async def check_duplicate_file(file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file with same hash already exists"""
        try:
            # This would require a custom function or metadata table
            # For MVP, we'll implement a simple check
            logger.info("Checking for duplicate file", file_hash=file_hash[:16])
            
            # For now, return None (no duplicate found)
            # In a full implementation, this would query a metadata table
            return None
            
        except Exception as e:
            logger.error("Failed to check duplicate file", error=str(e), file_hash=file_hash[:16])
            return None
    
    @staticmethod
    def get_storage_stats() -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            # Get bucket info
            files = MVPStorageManager.list_files(limit=1000)
            
            total_files = len(files)
            total_size = sum(file.get('metadata', {}).get('size', 0) for file in files)
            
            stats = {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': mvp_settings.storage_bucket,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info("Storage stats retrieved", **stats)
            return stats
            
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            raise


class MVPBackupManager:
    """Simple backup manager for MVP"""
    
    @staticmethod
    def create_backup_copy(file_path: str, document_id: str) -> str:
        """Create a backup copy of an important file"""
        try:
            # Create backup path
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            backup_path = f"backups/{document_id}/{timestamp}_{Path(file_path).name}"
            
            # Download original file
            file_content = MVPStorageManager.download_file(file_path)
            
            # Upload to backup location
            mvp_supabase.client.storage.from_(mvp_settings.storage_bucket).upload(
                path=backup_path,
                file=file_content,
                file_options={
                    'content-type': 'application/xml',
                    'upsert': False  # Don't overwrite backups
                }
            )
            
            logger.info("Backup created successfully", original_path=file_path, backup_path=backup_path)
            return backup_path
            
        except Exception as e:
            logger.error("Failed to create backup", error=str(e), file_path=file_path)
            raise
    
    @staticmethod
    def cleanup_old_backups(days_to_keep: int = 30):
        """Clean up old backup files"""
        try:
            # List backup files
            backup_files = MVPStorageManager.list_files(prefix="backups/")
            
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 60 * 60)
            deleted_count = 0
            
            for file_info in backup_files:
                if file_info.get('created_at'):
                    file_date = datetime.fromisoformat(file_info['created_at'].replace('Z', '+00:00')).timestamp()
                    if file_date < cutoff_date:
                        MVPStorageManager.delete_file(file_info['name'])
                        deleted_count += 1
            
            logger.info("Backup cleanup completed", deleted_files=deleted_count, days_to_keep=days_to_keep)
            
        except Exception as e:
            logger.error("Failed to cleanup old backups", error=str(e))
            raise