"""
File security and validation utilities for XML uploads
"""

import structlog
import hashlib
import mimetypes
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import re
from datetime import datetime, timezone

from .config import settings

logger = structlog.get_logger()


class FileValidator:
    """File validation and security utilities"""
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.xml'}
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {'application/xml', 'text/xml'}
    
    # Brazilian fiscal document patterns
    NFE_PATTERNS = [
        r'<infNFe',  # NF-e root element
        r'<ide>',    # Identification element
        r'<emit>',   # Emitter element
        r'<dest>',   # Destination element
    ]
    
    NFSE_PATTERNS = [
        r'<InfNfse',     # NFS-e info element
        r'<IdentificacaoNfse>',  # NFS-e identification
        r'<PrestadorServico>',   # Service provider
        r'<TomadorServico>',     # Service taker
    ]
    
    @staticmethod
    def validate_file_basic(filename: str, file_size: int, content: bytes) -> Dict[str, Any]:
        """Basic file validation (size, extension, MIME type)"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {
                'filename': filename,
                'size': file_size,
                'extension': None,
                'mime_type': None,
                'hash': None
            }
        }
        
        try:
            # Check file size
            if file_size > FileValidator.MAX_FILE_SIZE:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"Arquivo muito grande. Tamanho máximo permitido: {FileValidator.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            
            # Check file extension
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            validation_result['file_info']['extension'] = extension
            
            if extension not in FileValidator.ALLOWED_EXTENSIONS:
                validation_result['valid'] = False
                validation_result['errors'].append(
                    f"Extensão de arquivo não permitida: {extension}. Extensões permitidas: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}"
                )
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            validation_result['file_info']['mime_type'] = mime_type
            
            if mime_type not in FileValidator.ALLOWED_MIME_TYPES:
                validation_result['warnings'].append(
                    f"Tipo MIME não reconhecido: {mime_type}. Continuando com validação XML."
                )
            
            # Generate file hash for integrity
            file_hash = hashlib.sha256(content).hexdigest()
            validation_result['file_info']['hash'] = file_hash
            
            logger.info(
                "Basic file validation completed",
                filename=filename,
                size=file_size,
                valid=validation_result['valid'],
                errors=len(validation_result['errors'])
            )
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Erro na validação básica do arquivo: {str(e)}")
            logger.error("Basic file validation failed", error=str(e), filename=filename)
        
        return validation_result
    
    @staticmethod
    def validate_xml_structure(content: str) -> Dict[str, Any]:
        """Validate XML structure and detect document type"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'document_info': {
                'type': None,
                'root_element': None,
                'encoding': None,
                'well_formed': False,
                'fiscal_document': False
            }
        }
        
        try:
            # Parse XML to check if it's well-formed
            root = ET.fromstring(content)
            validation_result['document_info']['well_formed'] = True
            validation_result['document_info']['root_element'] = root.tag
            
            # Detect encoding
            if content.startswith('<?xml'):
                encoding_match = re.search(r'encoding=["\']([^"\']+)["\']', content[:200])
                if encoding_match:
                    validation_result['document_info']['encoding'] = encoding_match.group(1)
            
            # Detect document type based on content patterns
            content_lower = content.lower()
            
            # Check for NF-e patterns
            nfe_matches = sum(1 for pattern in FileValidator.NFE_PATTERNS if re.search(pattern, content, re.IGNORECASE))
            
            # Check for NFS-e patterns
            nfse_matches = sum(1 for pattern in FileValidator.NFSE_PATTERNS if re.search(pattern, content, re.IGNORECASE))
            
            if nfe_matches >= 3:  # At least 3 NF-e patterns found
                validation_result['document_info']['type'] = 'NFE'
                validation_result['document_info']['fiscal_document'] = True
            elif nfse_matches >= 2:  # At least 2 NFS-e patterns found
                validation_result['document_info']['type'] = 'NFSE'
                validation_result['document_info']['fiscal_document'] = True
            else:
                validation_result['warnings'].append(
                    "Documento XML não foi reconhecido como NF-e ou NFS-e. Continuando processamento."
                )
            
            logger.info(
                "XML structure validation completed",
                root_element=root.tag,
                document_type=validation_result['document_info']['type'],
                fiscal_document=validation_result['document_info']['fiscal_document']
            )
            
        except ET.ParseError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"XML mal formado: {str(e)}")
            logger.error("XML parsing failed", error=str(e))
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Erro na validação XML: {str(e)}")
            logger.error("XML validation failed", error=str(e))
        
        return validation_result
    
    @staticmethod
    def validate_content_security(content: str) -> Dict[str, Any]:
        """Security validation for XML content"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'security_info': {
                'suspicious_patterns': [],
                'external_references': [],
                'script_content': False,
                'size_check': True
            }
        }
        
        try:
            # Check for suspicious patterns
            suspicious_patterns = [
                (r'<!ENTITY', 'XML Entity declaration found'),
                (r'SYSTEM\s+["\']', 'External system reference found'),
                (r'<script', 'Script tag found'),
                (r'javascript:', 'JavaScript protocol found'),
                (r'data:', 'Data protocol found'),
                (r'file://', 'File protocol found'),
                (r'ftp://', 'FTP protocol found'),
            ]
            
            for pattern, description in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    validation_result['security_info']['suspicious_patterns'].append(description)
                    validation_result['warnings'].append(f"Padrão suspeito detectado: {description}")
            
            # Check for external references
            external_refs = re.findall(r'http[s]?://[^\s<>"\']+', content, re.IGNORECASE)
            if external_refs:
                validation_result['security_info']['external_references'] = external_refs[:5]  # Limit to first 5
                validation_result['warnings'].append(
                    f"Referências externas encontradas: {len(external_refs)} URLs"
                )
            
            # Check content size (additional security measure)
            if len(content) > FileValidator.MAX_FILE_SIZE:
                validation_result['valid'] = False
                validation_result['security_info']['size_check'] = False
                validation_result['errors'].append("Conteúdo XML excede o tamanho máximo permitido")
            
            logger.info(
                "Content security validation completed",
                suspicious_patterns=len(validation_result['security_info']['suspicious_patterns']),
                external_references=len(validation_result['security_info']['external_references']),
                valid=validation_result['valid']
            )
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Erro na validação de segurança: {str(e)}")
            logger.error("Content security validation failed", error=str(e))
        
        return validation_result
    
    @staticmethod
    def comprehensive_validation(filename: str, content: bytes) -> Dict[str, Any]:
        """Comprehensive file validation combining all checks"""
        logger.info("Starting comprehensive file validation", filename=filename)
        
        # Convert bytes to string for XML processing
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = content.decode('latin-1')
            except UnicodeDecodeError:
                return {
                    'valid': False,
                    'errors': ['Não foi possível decodificar o arquivo. Encoding não suportado.'],
                    'warnings': [],
                    'validation_timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        # Run all validations
        basic_validation = FileValidator.validate_file_basic(filename, len(content), content)
        xml_validation = FileValidator.validate_xml_structure(content_str)
        security_validation = FileValidator.validate_content_security(content_str)
        
        # Combine results
        combined_result = {
            'valid': basic_validation['valid'] and xml_validation['valid'] and security_validation['valid'],
            'errors': basic_validation['errors'] + xml_validation['errors'] + security_validation['errors'],
            'warnings': basic_validation['warnings'] + xml_validation['warnings'] + security_validation['warnings'],
            'file_info': basic_validation['file_info'],
            'document_info': xml_validation['document_info'],
            'security_info': security_validation['security_info'],
            'validation_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(
            "Comprehensive validation completed",
            filename=filename,
            valid=combined_result['valid'],
            errors=len(combined_result['errors']),
            warnings=len(combined_result['warnings']),
            document_type=combined_result['document_info'].get('type')
        )
        
        return combined_result


class FileSecurityManager:
    """Manager for file security operations"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = Path(sanitized).stem, Path(sanitized).suffix
            sanitized = name[:255-len(ext)] + ext
        
        # Ensure it's not empty
        if not sanitized or sanitized.isspace():
            sanitized = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        return sanitized
    
    @staticmethod
    def generate_secure_path(user_id: str, document_id: str, filename: str) -> str:
        """Generate secure file path for storage"""
        sanitized_filename = FileSecurityManager.sanitize_filename(filename)
        
        # Create path with user isolation
        secure_path = f"{user_id}/{document_id}/{sanitized_filename}"
        
        return secure_path
    
    @staticmethod
    def create_backup_policy() -> Dict[str, Any]:
        """Define backup and retention policy"""
        policy = {
            'retention_days': 365,  # Keep files for 1 year
            'backup_frequency': 'daily',
            'backup_location': 'supabase_backup_bucket',
            'compression': True,
            'encryption': True,
            'access_logging': True
        }
        
        logger.info("Backup policy created", policy=policy)
        return policy
    
    @staticmethod
    def setup_access_logging() -> Dict[str, Any]:
        """Setup access logging configuration"""
        logging_config = {
            'log_uploads': True,
            'log_downloads': True,
            'log_deletions': True,
            'log_access_attempts': True,
            'retention_days': 90,
            'alert_on_suspicious_activity': True
        }
        
        logger.info("Access logging configured", config=logging_config)
        return logging_config


def validate_and_secure_file(filename: str, content: bytes, user_id: str) -> Dict[str, Any]:
    """Main function to validate and secure an uploaded file"""
    logger.info("Starting file validation and security check", filename=filename, user_id=user_id)
    
    # Comprehensive validation
    validation_result = FileValidator.comprehensive_validation(filename, content)
    
    if validation_result['valid']:
        # Generate secure filename and path
        secure_filename = FileSecurityManager.sanitize_filename(filename)
        
        # Add security metadata
        validation_result['security'] = {
            'original_filename': filename,
            'secure_filename': secure_filename,
            'user_id': user_id,
            'validation_passed': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info("File validation and security check passed", filename=secure_filename)
    else:
        logger.warning(
            "File validation failed",
            filename=filename,
            errors=validation_result['errors']
        )
    
    return validation_result