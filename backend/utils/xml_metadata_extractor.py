"""
XML Metadata Extraction Utilities for Brazilian Fiscal Documents
Extracts key metadata from NF-e and NFS-e XML files for database storage
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
import re

logger = structlog.get_logger()

class XMLMetadataExtractor:
    """Extracts metadata from Brazilian fiscal XML documents"""
    
    # XML namespaces for NF-e and NFS-e
    NFE_NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe'
    }
    
    NFSE_NAMESPACES = {
        'nfse': 'http://www.abrasf.org.br/nfse.xsd'
    }
    
    @staticmethod
    def detect_document_type(xml_content: str) -> str:
        """Detect if XML is NF-e or NFS-e"""
        try:
            # Simple detection based on root element or key elements
            if 'nfeProc' in xml_content or 'NFe' in xml_content:
                return 'NFE'
            elif 'CompNfse' in xml_content or 'nfse' in xml_content.lower():
                return 'NFSE'
            else:
                # Try to parse and check root element
                root = ET.fromstring(xml_content)
                root_tag = root.tag.lower()
                
                if 'nfe' in root_tag:
                    return 'NFE'
                elif 'nfse' in root_tag or 'compnfse' in root_tag:
                    return 'NFSE'
                else:
                    logger.warning("Could not detect document type from XML", root_tag=root.tag)
                    return 'NFE'  # Default to NFE
                    
        except Exception as e:
            logger.error("Error detecting document type", error=str(e))
            return 'NFE'  # Default to NFE
    
    @staticmethod
    def extract_nfe_metadata(xml_content: str) -> Dict[str, Any]:
        """Extract metadata from NF-e XML"""
        try:
            root = ET.fromstring(xml_content)
            metadata = {}
            
            # Find the infNFe element (can be in different structures)
            inf_nfe = None
            
            # Try different possible paths
            possible_paths = [
                './/infNFe',
                './/nfe:infNFe',
                './/NFe/infNFe',
                './/nfeProc/NFe/infNFe'
            ]
            
            for path in possible_paths:
                try:
                    inf_nfe = root.find(path, XMLMetadataExtractor.NFE_NAMESPACES)
                    if inf_nfe is not None:
                        break
                except:
                    continue
            
            if inf_nfe is None:
                logger.warning("Could not find infNFe element in XML")
                return metadata
            
            # Extract identification data
            ide = inf_nfe.find('.//ide')
            if ide is not None:
                metadata['numero_documento'] = XMLMetadataExtractor._get_text(ide, 'nNF')
                metadata['serie_documento'] = XMLMetadataExtractor._get_text(ide, 'serie')
                metadata['data_emissao'] = XMLMetadataExtractor._parse_date(
                    XMLMetadataExtractor._get_text(ide, 'dhEmi')
                )
                metadata['data_saida_entrada'] = XMLMetadataExtractor._parse_date(
                    XMLMetadataExtractor._get_text(ide, 'dhSaiEnt')
                )
                metadata['natureza_operacao'] = XMLMetadataExtractor._get_text(ide, 'natOp')
                metadata['tipo_operacao'] = XMLMetadataExtractor._get_text(ide, 'tpNF')
                metadata['codigo_municipio'] = XMLMetadataExtractor._get_text(ide, 'cMunFG')
                metadata['forma_pagamento'] = XMLMetadataExtractor._get_text(ide, 'indPag')
            
            # Extract emitter data
            emit = inf_nfe.find('.//emit')
            if emit is not None:
                metadata['cnpj_emitente'] = XMLMetadataExtractor._get_text(emit, 'CNPJ')
                metadata['nome_emitente'] = XMLMetadataExtractor._get_text(emit, 'xNome')
                metadata['inscricao_estadual_emitente'] = XMLMetadataExtractor._get_text(emit, 'IE')
                
                # Extract address info
                ender_emit = emit.find('enderEmit')
                if ender_emit is not None:
                    metadata['uf'] = XMLMetadataExtractor._get_text(ender_emit, 'UF')
            
            # Extract recipient data
            dest = inf_nfe.find('.//dest')
            if dest is not None:
                metadata['cnpj_destinatario'] = XMLMetadataExtractor._get_text(dest, 'CNPJ')
                metadata['nome_destinatario'] = XMLMetadataExtractor._get_text(dest, 'xNome')
                metadata['inscricao_estadual_destinatario'] = XMLMetadataExtractor._get_text(dest, 'IE')
            
            # Extract totals
            total = inf_nfe.find('.//total/ICMSTot')
            if total is not None:
                metadata['valor_total'] = XMLMetadataExtractor._parse_decimal(
                    XMLMetadataExtractor._get_text(total, 'vNF')
                )
                metadata['valor_produtos'] = XMLMetadataExtractor._parse_decimal(
                    XMLMetadataExtractor._get_text(total, 'vProd')
                )
                metadata['valor_tributos'] = XMLMetadataExtractor._parse_decimal(
                    XMLMetadataExtractor._get_text(total, 'vTotTrib')
                )
            
            logger.info(
                "Successfully extracted NF-e metadata",
                numero_documento=metadata.get('numero_documento'),
                emitente=metadata.get('nome_emitente')
            )
            
            return metadata
            
        except Exception as e:
            logger.error("Error extracting NF-e metadata", error=str(e))
            return {}
    
    @staticmethod
    def extract_nfse_metadata(xml_content: str) -> Dict[str, Any]:
        """Extract metadata from NFS-e XML"""
        try:
            root = ET.fromstring(xml_content)
            metadata = {}
            
            # Find the main NFS-e element (structure varies by municipality)
            nfse_elem = None
            
            # Try different possible paths
            possible_paths = [
                './/Nfse',
                './/CompNfse',
                './/nfse:CompNfse',
                './/InfNfse'
            ]
            
            for path in possible_paths:
                try:
                    nfse_elem = root.find(path, XMLMetadataExtractor.NFSE_NAMESPACES)
                    if nfse_elem is not None:
                        break
                except:
                    continue
            
            if nfse_elem is None:
                logger.warning("Could not find NFS-e element in XML")
                return metadata
            
            # Extract identification data
            inf_nfse = nfse_elem.find('.//InfNfse') or nfse_elem
            
            if inf_nfse is not None:
                metadata['numero_documento'] = XMLMetadataExtractor._get_text(inf_nfse, './/Numero')
                metadata['data_emissao'] = XMLMetadataExtractor._parse_date(
                    XMLMetadataExtractor._get_text(inf_nfse, './/DataEmissao')
                )
                metadata['codigo_municipio'] = XMLMetadataExtractor._get_text(
                    inf_nfse, './/CodigoMunicipio'
                )
            
            # Extract service provider data (emitter)
            prestador = inf_nfse.find('.//PrestadorServico') if inf_nfse else None
            if prestador is not None:
                metadata['cnpj_emitente'] = XMLMetadataExtractor._get_text(prestador, './/Cnpj')
                metadata['nome_emitente'] = XMLMetadataExtractor._get_text(prestador, './/RazaoSocial')
                metadata['inscricao_estadual_emitente'] = XMLMetadataExtractor._get_text(
                    prestador, './/InscricaoMunicipal'
                )
            
            # Extract service taker data (recipient)
            tomador = inf_nfse.find('.//TomadorServico') if inf_nfse else None
            if tomador is not None:
                metadata['cnpj_destinatario'] = XMLMetadataExtractor._get_text(tomador, './/Cnpj')
                metadata['nome_destinatario'] = XMLMetadataExtractor._get_text(tomador, './/RazaoSocial')
            
            # Extract service values
            servico = inf_nfse.find('.//Servico') if inf_nfse else None
            if servico is not None:
                valores = servico.find('Valores')
                if valores is not None:
                    metadata['valor_servicos'] = XMLMetadataExtractor._parse_decimal(
                        XMLMetadataExtractor._get_text(valores, 'ValorServicos')
                    )
                    metadata['valor_total'] = metadata['valor_servicos']  # For NFS-e, total = services
                    metadata['valor_tributos'] = XMLMetadataExtractor._parse_decimal(
                        XMLMetadataExtractor._get_text(valores, 'ValorIss')
                    )
            
            logger.info(
                "Successfully extracted NFS-e metadata",
                numero_documento=metadata.get('numero_documento'),
                prestador=metadata.get('nome_emitente')
            )
            
            return metadata
            
        except Exception as e:
            logger.error("Error extracting NFS-e metadata", error=str(e))
            return {}
    
    @staticmethod
    def extract_metadata(xml_content: str) -> Dict[str, Any]:
        """Extract metadata from XML based on document type"""
        document_type = XMLMetadataExtractor.detect_document_type(xml_content)
        
        if document_type == 'NFE':
            return XMLMetadataExtractor.extract_nfe_metadata(xml_content)
        elif document_type == 'NFSE':
            return XMLMetadataExtractor.extract_nfse_metadata(xml_content)
        else:
            logger.warning("Unknown document type", document_type=document_type)
            return {}
    
    @staticmethod
    def _get_text(element: ET.Element, tag: str) -> Optional[str]:
        """Safely get text content from XML element"""
        if element is None:
            return None
        
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        
        return None
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try different date formats
            date_formats = [
                '%Y-%m-%dT%H:%M:%S%z',  # ISO format with timezone
                '%Y-%m-%dT%H:%M:%S',    # ISO format without timezone
                '%Y-%m-%d',             # Date only
                '%d/%m/%Y',             # Brazilian format
                '%Y-%m-%d %H:%M:%S'     # Standard datetime
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            logger.warning("Could not parse date", date_str=date_str)
            return None
            
        except Exception as e:
            logger.error("Error parsing date", date_str=date_str, error=str(e))
            return None
    
    @staticmethod
    def _parse_decimal(value_str: Optional[str]) -> Optional[float]:
        """Parse decimal string to float"""
        if not value_str:
            return None
        
        try:
            # Clean the string and convert to float
            cleaned = re.sub(r'[^\d.,]', '', value_str)
            # Handle Brazilian decimal format (comma as decimal separator)
            if ',' in cleaned and '.' in cleaned:
                # Both comma and dot present, assume dot is thousands separator
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                # Only comma present, assume it's decimal separator
                cleaned = cleaned.replace(',', '.')
            
            return float(cleaned)
            
        except Exception as e:
            logger.error("Error parsing decimal", value_str=value_str, error=str(e))
            return None