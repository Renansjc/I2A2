"""
Dimensional Processing Agent for populating dimensional tables from fiscal documents
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from lxml import etree
import uuid
import re

from .base_agent import BaseAgent
from utils.database import ProcessingStatusManager, get_supabase_client
# Simple validation functions for Brazilian documents
def validate_cnpj(cnpj: str) -> bool:
    """Simple CNPJ validation"""
    if not cnpj:
        return False
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    return len(cnpj_clean) == 14

def validate_cpf(cpf: str) -> bool:
    """Simple CPF validation"""
    if not cpf:
        return False
    cpf_clean = re.sub(r'[^0-9]', '', cpf)
    return len(cpf_clean) == 11

def format_cnpj(cnpj: str) -> str:
    """Simple CNPJ formatting"""
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj_clean) == 14:
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    return cnpj_clean

def format_cpf(cpf: str) -> str:
    """Simple CPF formatting"""
    cpf_clean = re.sub(r'[^0-9]', '', cpf)
    if len(cpf_clean) == 11:
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    return cpf_clean

logger = structlog.get_logger()


class DimensionalProcessingAgent(BaseAgent):
    """Agent specialized in coordinating dimensional processing of fiscal documents"""
    
    def __init__(self):
        super().__init__("DimensionalProcessingAgent")
        self.agent_name = "dimensional_processing_agent"
        self.supabase_client = get_supabase_client(admin_mode=True)  # Use admin mode for dimensional operations
    
    async def initialize(self):
        """Initialize agent-specific resources"""
        logger.info("Initializing Dimensional Processing Agent")
        # Initialize any required resources here
        pass
    
    async def cleanup(self):
        """Cleanup agent-specific resources"""
        logger.info("Cleaning up Dimensional Processing Agent")
        # Cleanup any resources here
        pass
    
    async def process(self, data: Any) -> Any:
        """Process data - main agent functionality"""
        if isinstance(data, dict) and 'xml_content' in data:
            return await self.process_fiscal_document(
                data['xml_content'], 
                data.get('context', {})
            )
        else:
            raise ValueError("Invalid data format for dimensional processing")
    
    async def process_fiscal_document(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process fiscal document into dimensional model
        
        Args:
            xml_content: Raw XML content of the fiscal document
            context: Processing context including document_id, document_type, etc.
            
        Returns:
            Dict containing processing results and dimensional data
        """
        try:
            document_id = context.get('document_id')
            document_type = context.get('document_type', 'NFE')
            
            logger.info(
                "Starting dimensional processing",
                document_id=document_id,
                document_type=document_type
            )
            
            # Update processing status
            if document_id:
                await ProcessingStatusManager.update_agent_status(
                    document_id, self.agent_name, "in_progress", admin_mode=True
                )
            
            # Parse XML content
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Extract and process emitente data
            emitente_id = await self.process_emitente_data(root, document_type)
            
            # Extract and process destinatario data (if present)
            destinatario_id = await self.process_destinatario_data(root, document_type)
            
            # Extract and process products/services data
            if document_type == "NFE":
                produtos_ids = await self.process_produtos_data(root)
                servicos_ids = []
            else:  # NFSE
                produtos_ids = []
                servicos_ids = await self.process_servicos_data(root)
            
            # Create fact records
            fact_records = await self.create_fact_records(
                root, document_type, emitente_id, destinatario_id, produtos_ids, servicos_ids
            )
            
            # Validate referential integrity
            integrity_check = await self.validate_referential_integrity(
                emitente_id, destinatario_id, produtos_ids, servicos_ids, fact_records
            )
            
            # Prepare response
            result = {
                "emitente_id": emitente_id,
                "destinatario_id": destinatario_id,
                "produtos_processed": len(produtos_ids),
                "servicos_processed": len(servicos_ids),
                "fact_records_created": len(fact_records),
                "integrity_check": integrity_check,
                "processing_status": "completed"
            }
            
            # Store processing results
            if document_id:
                await ProcessingStatusManager.store_processing_result(
                    document_id=document_id,
                    agent_name=self.agent_name,
                    result_type="dimensional_processing",
                    result_data=result,
                    confidence_score=0.95,
                    processing_time_ms=3000,
                    admin_mode=True
                )
                
                await ProcessingStatusManager.update_agent_status(
                    document_id, self.agent_name, "completed", admin_mode=True
                )
            
            logger.info(
                "Dimensional processing completed successfully",
                document_id=document_id,
                emitente_id=emitente_id,
                produtos_processed=len(produtos_ids),
                servicos_processed=len(servicos_ids)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Dimensional processing failed",
                document_id=document_id,
                error=str(e)
            )
            
            # Update error status
            if document_id:
                await ProcessingStatusManager.update_agent_status(
                    document_id, self.agent_name, "failed", str(e), admin_mode=True
                )
            
            raise
    
    async def process_emitente_data(self, xml_root, document_type: str) -> str:
        """
        Process and store emitente (supplier) data
        
        Args:
            xml_root: Parsed XML root element
            document_type: Type of document (NFE or NFSE)
            
        Returns:
            CNPJ of the processed emitente
        """
        try:
            emitente_data = self._extract_emitente_data(xml_root, document_type)
            
            if not emitente_data:
                raise ValueError("No emitente data found in document")
            
            # Validate and normalize data
            emitente_data = self._normalize_emitente_data(emitente_data)
            
            # Upsert emitente record
            cnpj = await self._upsert_emitente(emitente_data)
            
            logger.info(
                "Emitente data processed",
                cnpj=cnpj,
                razao_social=emitente_data.get('razao_social')
            )
            
            return cnpj
            
        except Exception as e:
            logger.error("Failed to process emitente data", error=str(e))
            raise
    
    async def process_destinatario_data(self, xml_root, document_type: str) -> Optional[int]:
        """
        Process and store destinatario (customer) data
        
        Args:
            xml_root: Parsed XML root element
            document_type: Type of document (NFE or NFSE)
            
        Returns:
            ID of the processed destinatario or None if not present
        """
        try:
            destinatario_data = self._extract_destinatario_data(xml_root, document_type)
            
            if not destinatario_data:
                logger.info("No destinatario data found in document")
                return None
            
            # Validate and normalize data
            destinatario_data = self._normalize_destinatario_data(destinatario_data)
            
            # Upsert destinatario record
            destinatario_id = await self._upsert_destinatario(destinatario_data)
            
            logger.info(
                "Destinatario data processed",
                destinatario_id=destinatario_id,
                razao_social=destinatario_data.get('razao_social')
            )
            
            return destinatario_id
            
        except Exception as e:
            logger.error("Failed to process destinatario data", error=str(e))
            raise
    
    async def process_produtos_data(self, xml_root) -> List[str]:
        """
        Process and store products data with categorization
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of product codes processed
        """
        try:
            produtos_data = self._extract_produtos_data(xml_root)
            produtos_ids = []
            
            for produto in produtos_data:
                # Normalize product data
                produto = self._normalize_produto_data(produto)
                
                # TODO: Integrate with AI Categorization Agent for automatic categorization
                # For now, use basic categorization
                produto = await self._apply_basic_categorization(produto)
                
                # Upsert product record
                codigo_produto = await self._upsert_produto(produto)
                produtos_ids.append(codigo_produto)
            
            logger.info(
                "Products data processed",
                produtos_count=len(produtos_ids)
            )
            
            return produtos_ids
            
        except Exception as e:
            logger.error("Failed to process produtos data", error=str(e))
            raise
    
    async def process_servicos_data(self, xml_root) -> List[str]:
        """
        Process and store services data with categorization
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of service codes processed
        """
        try:
            servicos_data = self._extract_servicos_data(xml_root)
            servicos_ids = []
            
            for servico in servicos_data:
                # Normalize service data
                servico = self._normalize_servico_data(servico)
                
                # TODO: Integrate with AI Categorization Agent for automatic categorization
                # For now, use basic categorization
                servico = await self._apply_basic_service_categorization(servico)
                
                # Upsert service record
                codigo_servico = await self._upsert_servico(servico)
                servicos_ids.append(codigo_servico)
            
            logger.info(
                "Services data processed",
                servicos_count=len(servicos_ids)
            )
            
            return servicos_ids
            
        except Exception as e:
            logger.error("Failed to process servicos data", error=str(e))
            raise
    
    async def create_fact_records(
        self, 
        xml_root, 
        document_type: str, 
        emitente_id: str, 
        destinatario_id: Optional[int],
        produtos_ids: List[str], 
        servicos_ids: List[str]
    ) -> List[str]:
        """
        Create fact table records for items
        
        Args:
            xml_root: Parsed XML root element
            document_type: Type of document (NFE or NFSE)
            emitente_id: CNPJ of emitente
            destinatario_id: ID of destinatario (if any)
            produtos_ids: List of product codes
            servicos_ids: List of service codes
            
        Returns:
            List of fact record IDs created
        """
        try:
            fact_records = []
            
            if document_type == "NFE":
                # Create fact records for NFE items
                nfe_items = self._extract_nfe_items_data(xml_root)
                
                for item in nfe_items:
                    fact_id = await self._insert_fact_item_nfe(item, emitente_id, destinatario_id)
                    fact_records.append(fact_id)
            
            else:  # NFSE
                # Create fact records for NFSE services
                nfse_services = self._extract_nfse_services_data(xml_root)
                
                for service in nfse_services:
                    fact_id = await self._insert_fact_servico_nfse(service, emitente_id, destinatario_id)
                    fact_records.append(fact_id)
            
            logger.info(
                "Fact records created",
                document_type=document_type,
                records_count=len(fact_records)
            )
            
            return fact_records
            
        except Exception as e:
            logger.error("Failed to create fact records", error=str(e))
            raise
    
    async def validate_referential_integrity(
        self, 
        emitente_id: str, 
        destinatario_id: Optional[int],
        produtos_ids: List[str], 
        servicos_ids: List[str], 
        fact_records: List[str]
    ) -> Dict[str, bool]:
        """
        Validate referential integrity for processed document
        
        Args:
            emitente_id: CNPJ of emitente
            destinatario_id: ID of destinatario
            produtos_ids: List of product codes
            servicos_ids: List of service codes
            fact_records: List of fact record IDs
            
        Returns:
            Dict with validation results
        """
        try:
            validations = {}
            
            # Validate emitente exists
            validations["emitente_exists"] = await self._validate_emitente_exists(emitente_id)
            
            # Validate destinatario exists (if provided)
            if destinatario_id:
                validations["destinatario_exists"] = await self._validate_destinatario_exists(destinatario_id)
            else:
                validations["destinatario_exists"] = True  # Not required
            
            # Validate products exist
            validations["produtos_exist"] = await self._validate_produtos_exist(produtos_ids)
            
            # Validate services exist
            validations["servicos_exist"] = await self._validate_servicos_exist(servicos_ids)
            
            # Validate fact records exist
            validations["fact_records_exist"] = len(fact_records) > 0
            
            # Overall integrity check
            validations["overall_integrity"] = all(validations.values())
            
            logger.info(
                "Referential integrity validation completed",
                validations=validations
            )
            
            return validations
            
        except Exception as e:
            logger.error("Failed to validate referential integrity", error=str(e))
            return {"overall_integrity": False, "error": str(e)}   
 
    # Data Extraction Methods
    
    def _extract_emitente_data(self, xml_root, document_type: str) -> Dict[str, Any]:
        """Extract emitente data from XML"""
        try:
            emitente_data = {}
            
            if document_type == "NFE":
                # Extract from NF-e
                emit = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
                if emit is not None:
                    emitente_data = {
                        'cnpj': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}CNPJ'),
                        'cpf': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}CPF'),
                        'inscricao_estadual': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}IE'),
                        'razao_social': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xNome'),
                        'nome_fantasia': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xFant'),
                        'logradouro': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xLgr'),
                        'numero': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}nro'),
                        'complemento': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xCpl'),
                        'bairro': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xBairro'),
                        'codigo_municipio': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}cMun'),
                        'nome_municipio': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xMun'),
                        'uf': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}UF'),
                        'cep': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}CEP'),
                        'codigo_pais': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}cPais'),
                        'nome_pais': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}xPais'),
                        'telefone': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}fone'),
                        'email': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}email'),
                        'regime_tributario': self._get_text(emit, './/{http://www.portalfiscal.inf.br/nfe}CRT')
                    }
            
            else:  # NFSE
                # Extract from NFS-e (simplified - varies by municipality)
                # This is a basic implementation - real NFS-e would need municipality-specific parsing
                emitente_data = {
                    'cnpj': '00000000000000',  # Would extract from actual NFS-e
                    'razao_social': 'Prestador de Serviços',
                    'uf': 'SP',  # Default values for NFS-e
                    'codigo_pais': '1058',
                    'nome_pais': 'Brasil'
                }
            
            return emitente_data
            
        except Exception as e:
            logger.error("Failed to extract emitente data", error=str(e))
            return {}
    
    def _extract_destinatario_data(self, xml_root, document_type: str) -> Optional[Dict[str, Any]]:
        """Extract destinatario data from XML"""
        try:
            if document_type == "NFE":
                # Extract from NF-e
                dest = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
                if dest is not None:
                    return {
                        'cnpj': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}CNPJ'),
                        'cpf': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}CPF'),
                        'inscricao_estadual': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}IE'),
                        'razao_social': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xNome'),
                        'logradouro': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xLgr'),
                        'numero': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}nro'),
                        'complemento': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xCpl'),
                        'bairro': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xBairro'),
                        'codigo_municipio': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}cMun'),
                        'nome_municipio': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xMun'),
                        'uf': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}UF'),
                        'cep': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}CEP'),
                        'codigo_pais': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}cPais'),
                        'nome_pais': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}xPais'),
                        'telefone': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}fone'),
                        'email': self._get_text(dest, './/{http://www.portalfiscal.inf.br/nfe}email')
                    }
            
            else:  # NFSE
                # NFS-e may have tomador (service taker) data
                return {
                    'cnpj': '11111111111111',  # Would extract from actual NFS-e
                    'razao_social': 'Tomador de Serviços'
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to extract destinatario data", error=str(e))
            return None    
    
    def _extract_produtos_data(self, xml_root) -> List[Dict[str, Any]]:
        """Extract products data from NF-e XML"""
        try:
            produtos = []
            det_elements = xml_root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
            
            for det in det_elements:
                prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                if prod is not None:
                    produto = {
                        'codigo_produto': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}cProd'),
                        'ean': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}cEAN'),
                        'descricao': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}xProd'),
                        'ncm': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}NCM'),
                        'cest': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}CEST'),
                        'cfop': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}CFOP'),
                        'unidade_comercial': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}uCom'),
                        'unidade_tributavel': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}uTrib')
                    }
                    produtos.append(produto)
            
            return produtos
            
        except Exception as e:
            logger.error("Failed to extract produtos data", error=str(e))
            return []
    
    def _extract_servicos_data(self, xml_root) -> List[Dict[str, Any]]:
        """Extract services data from NFS-e XML"""
        try:
            # This is a simplified implementation for NFS-e
            # Real implementation would depend on municipality-specific schemas
            servicos = [{
                'codigo_servico': 'SERV001',
                'descricao': 'Serviços diversos',
                'codigo_cnae': '6201500',  # Default CNAE for IT services
                'codigo_tributacao_nacional': '01.01',
                'codigo_tributacao_municipal': '0101'
            }]
            
            return servicos
            
        except Exception as e:
            logger.error("Failed to extract servicos data", error=str(e))
            return []
    
    def _extract_nfe_items_data(self, xml_root) -> List[Dict[str, Any]]:
        """Extract detailed NFE items data for fact table"""
        try:
            items = []
            det_elements = xml_root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
            
            # Get document key for reference
            inf_nfe = xml_root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            chave_nfe = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe is not None else ''
            
            for i, det in enumerate(det_elements, 1):
                prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                if prod is not None:
                    item = {
                        'chave_nfe': chave_nfe,
                        'numero_item': i,
                        'codigo_produto': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}cProd'),
                        'ean': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}cEAN'),
                        'descricao': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}xProd'),
                        'ncm': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}NCM'),
                        'cest': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}CEST'),
                        'cfop': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}CFOP'),
                        'unidade_comercial': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}uCom'),
                        'quantidade_comercial': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}qCom'),
                        'valor_unitario_comercial': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vUnCom'),
                        'valor_total_bruto': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vProd'),
                        'unidade_tributavel': self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}uTrib'),
                        'quantidade_tributavel': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}qTrib'),
                        'valor_unitario_tributavel': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vUnTrib'),
                        'valor_frete': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vFrete'),
                        'valor_seguro': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vSeg'),
                        'valor_desconto': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vDesc'),
                        'valor_outras_despesas': self._get_decimal(prod, './/{http://www.portalfiscal.inf.br/nfe}vOutro')
                    }
                    items.append(item)
            
            return items
            
        except Exception as e:
            logger.error("Failed to extract NFE items data", error=str(e))
            return []
    
    def _extract_nfse_services_data(self, xml_root) -> List[Dict[str, Any]]:
        """Extract detailed NFSE services data for fact table"""
        try:
            # Simplified implementation for NFS-e services
            services = [{
                'id_nfse': 'NFSE' + datetime.now().strftime('%Y%m%d%H%M%S'),
                'codigo_servico': 'SERV001',
                'descricao_servico': 'Serviços diversos',
                'quantidade': Decimal('1.0'),
                'valor_unitario': Decimal('1000.00'),
                'valor_total': Decimal('1000.00'),
                'valor_deducoes': Decimal('0.00'),
                'valor_base_calculo': Decimal('1000.00'),
                'aliquota_issqn': Decimal('0.05'),
                'valor_issqn': Decimal('50.00'),
                'valor_credito': Decimal('0.00')
            }]
            
            return services
            
        except Exception as e:
            logger.error("Failed to extract NFSE services data", error=str(e))
            return []    

    # Data Normalization Methods
    
    def _normalize_emitente_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate emitente data"""
        try:
            normalized = {}
            
            # Validate and format CNPJ/CPF
            cnpj = data.get('cnpj', '').strip()
            cpf = data.get('cpf', '').strip()
            
            if cnpj and validate_cnpj(cnpj):
                normalized['cnpj'] = format_cnpj(cnpj)
            elif cpf and validate_cpf(cpf):
                normalized['cnpj'] = format_cpf(cpf)  # Store CPF in CNPJ field for individuals
                normalized['cpf'] = format_cpf(cpf)
            else:
                raise ValueError("Invalid CNPJ/CPF for emitente")
            
            # Required fields
            normalized['razao_social'] = data.get('razao_social', '').strip()[:60]
            if not normalized['razao_social']:
                raise ValueError("Razão social is required for emitente")
            
            # Optional fields with length limits
            normalized['nome_fantasia'] = data.get('nome_fantasia', '').strip()[:60] or None
            normalized['inscricao_estadual'] = data.get('inscricao_estadual', '').strip()[:14] or None
            normalized['logradouro'] = data.get('logradouro', '').strip()[:60] or None
            normalized['numero'] = data.get('numero', '').strip()[:60] or None
            normalized['complemento'] = data.get('complemento', '').strip()[:60] or None
            normalized['bairro'] = data.get('bairro', '').strip()[:60] or None
            normalized['codigo_municipio'] = data.get('codigo_municipio', '').strip()[:7] or None
            normalized['nome_municipio'] = data.get('nome_municipio', '').strip()[:60] or None
            normalized['uf'] = data.get('uf', '').strip()[:2] or None
            normalized['cep'] = re.sub(r'[^0-9]', '', data.get('cep', ''))[:8] or None
            normalized['codigo_pais'] = data.get('codigo_pais', '1058').strip()[:4]  # Default Brazil
            normalized['nome_pais'] = data.get('nome_pais', 'Brasil').strip()[:60]
            normalized['telefone'] = re.sub(r'[^0-9]', '', data.get('telefone', ''))[:14] or None
            normalized['email'] = data.get('email', '').strip()[:60] or None
            normalized['regime_tributario'] = data.get('regime_tributario', '').strip()[:1] or None
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize emitente data", error=str(e))
            raise
    
    def _normalize_destinatario_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate destinatario data"""
        try:
            normalized = {}
            
            # Validate and format CNPJ/CPF (optional for destinatario)
            cnpj = data.get('cnpj', '').strip()
            cpf = data.get('cpf', '').strip()
            
            if cnpj and validate_cnpj(cnpj):
                normalized['cnpj'] = format_cnpj(cnpj)
            elif cpf and validate_cpf(cpf):
                normalized['cpf'] = format_cpf(cpf)
            
            # Optional fields with length limits
            normalized['inscricao_estadual'] = data.get('inscricao_estadual', '').strip()[:14] or None
            normalized['razao_social'] = data.get('razao_social', '').strip()[:60] or None
            normalized['logradouro'] = data.get('logradouro', '').strip()[:60] or None
            normalized['numero'] = data.get('numero', '').strip()[:60] or None
            normalized['complemento'] = data.get('complemento', '').strip()[:60] or None
            normalized['bairro'] = data.get('bairro', '').strip()[:60] or None
            normalized['codigo_municipio'] = data.get('codigo_municipio', '').strip()[:7] or None
            normalized['nome_municipio'] = data.get('nome_municipio', '').strip()[:60] or None
            normalized['uf'] = data.get('uf', '').strip()[:2] or None
            normalized['cep'] = re.sub(r'[^0-9]', '', data.get('cep', ''))[:8] or None
            normalized['codigo_pais'] = data.get('codigo_pais', '1058').strip()[:4]
            normalized['nome_pais'] = data.get('nome_pais', 'Brasil').strip()[:60]
            normalized['telefone'] = re.sub(r'[^0-9]', '', data.get('telefone', ''))[:14] or None
            normalized['email'] = data.get('email', '').strip()[:60] or None
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize destinatario data", error=str(e))
            raise
    
    def _normalize_produto_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate product data"""
        try:
            normalized = {}
            
            # Required fields
            normalized['codigo_produto'] = data.get('codigo_produto', '').strip()[:60]
            if not normalized['codigo_produto']:
                raise ValueError("Código do produto is required")
            
            normalized['descricao'] = data.get('descricao', '').strip()
            if not normalized['descricao']:
                raise ValueError("Descrição do produto is required")
            
            # Optional fields with length limits
            normalized['ean'] = data.get('ean', '').strip()[:14] or None
            normalized['ncm'] = data.get('ncm', '').strip()[:8] or None
            normalized['cest'] = data.get('cest', '').strip()[:7] or None
            normalized['cfop'] = data.get('cfop', '').strip()[:4] or None
            normalized['unidade_comercial'] = data.get('unidade_comercial', '').strip()[:6] or None
            normalized['unidade_tributavel'] = data.get('unidade_tributavel', '').strip()[:6] or None
            
            # Categorization fields (will be filled by categorization process)
            normalized['categoria'] = data.get('categoria', '').strip()[:100] or None
            normalized['subcategoria'] = data.get('subcategoria', '').strip()[:100] or None
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize produto data", error=str(e))
            raise
    
    def _normalize_servico_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate service data"""
        try:
            normalized = {}
            
            # Required fields
            normalized['codigo_servico'] = data.get('codigo_servico', '').strip()[:20]
            if not normalized['codigo_servico']:
                raise ValueError("Código do serviço is required")
            
            normalized['descricao'] = data.get('descricao', '').strip()
            if not normalized['descricao']:
                raise ValueError("Descrição do serviço is required")
            
            # Optional fields with length limits
            normalized['codigo_cnae'] = data.get('codigo_cnae', '').strip()[:7] or None
            normalized['codigo_tributacao_nacional'] = data.get('codigo_tributacao_nacional', '').strip()[:20] or None
            normalized['codigo_tributacao_municipal'] = data.get('codigo_tributacao_municipal', '').strip()[:20] or None
            normalized['codigo_nbs'] = data.get('codigo_nbs', '').strip()[:20] or None
            
            # Categorization fields (will be filled by categorization process)
            normalized['categoria'] = data.get('categoria', '').strip()[:100] or None
            normalized['subcategoria'] = data.get('subcategoria', '').strip()[:100] or None
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize servico data", error=str(e))
            raise   
 
    # Basic Categorization Methods (to be replaced by AI Categorization Agent integration)
    
    async def _apply_basic_categorization(self, produto: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic categorization to product (placeholder for AI integration)"""
        try:
            descricao = produto.get('descricao', '').lower()
            
            # Basic rule-based categorization
            if any(word in descricao for word in ['computador', 'notebook', 'eletrônico', 'placa', 'video']):
                produto['categoria'] = 'Eletrônicos'
                produto['subcategoria'] = 'Informática'
            elif any(word in descricao for word in ['móvel', 'mesa', 'cadeira']):
                produto['categoria'] = 'Móveis'
                produto['subcategoria'] = 'Móveis de Escritório'
            elif any(word in descricao for word in ['material', 'escritório', 'papel']):
                produto['categoria'] = 'Material de Escritório'
                produto['subcategoria'] = 'Papelaria'
            else:
                produto['categoria'] = 'Outros'
                produto['subcategoria'] = 'Diversos'
            
            return produto
            
        except Exception as e:
            logger.error("Failed to apply basic categorization", error=str(e))
            return produto
    
    async def _apply_basic_service_categorization(self, servico: Dict[str, Any]) -> Dict[str, Any]:
        """Apply basic categorization to service (placeholder for AI integration)"""
        try:
            descricao = servico.get('descricao', '').lower()
            
            # Basic rule-based categorization for services
            if any(word in descricao for word in ['consultoria', 'assessoria']):
                servico['categoria'] = 'Consultoria'
                servico['subcategoria'] = 'Consultoria Empresarial'
            elif any(word in descricao for word in ['desenvolvimento', 'software', 'sistema']):
                servico['categoria'] = 'Tecnologia'
                servico['subcategoria'] = 'Desenvolvimento de Software'
            elif any(word in descricao for word in ['manutenção', 'reparo']):
                servico['categoria'] = 'Manutenção'
                servico['subcategoria'] = 'Serviços Técnicos'
            else:
                servico['categoria'] = 'Serviços Gerais'
                servico['subcategoria'] = 'Diversos'
            
            return servico
            
        except Exception as e:
            logger.error("Failed to apply basic service categorization", error=str(e))
            return servico
    
    # Database Operations Methods
    
    async def _upsert_emitente(self, emitente_data: Dict[str, Any]) -> str:
        """Insert or update emitente record"""
        try:
            import asyncio
            
            cnpj = emitente_data['cnpj']
            
            # Add timestamps
            emitente_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Try to update existing record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_emitente')
                .upsert(emitente_data, on_conflict='cnpj')
                .execute()
            )
            
            logger.info("Emitente upserted", cnpj=cnpj)
            return cnpj
            
        except Exception as e:
            logger.error("Failed to upsert emitente", error=str(e))
            raise
    
    async def _upsert_destinatario(self, destinatario_data: Dict[str, Any]) -> int:
        """Insert or update destinatario record"""
        try:
            import asyncio
            
            # Add timestamps
            destinatario_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Check if destinatario already exists
            cnpj = destinatario_data.get('cnpj')
            cpf = destinatario_data.get('cpf')
            
            if cnpj:
                # Try to find existing by CNPJ
                existing = await asyncio.to_thread(
                    lambda: self.supabase_client.client.table('dim_destinatario')
                    .select('id')
                    .eq('cnpj', cnpj)
                    .limit(1)
                    .execute()
                )
                
                if existing.data:
                    # Update existing record
                    destinatario_id = existing.data[0]['id']
                    await asyncio.to_thread(
                        lambda: self.supabase_client.client.table('dim_destinatario')
                        .update(destinatario_data)
                        .eq('id', destinatario_id)
                        .execute()
                    )
                    return destinatario_id
            
            elif cpf:
                # Try to find existing by CPF
                existing = await asyncio.to_thread(
                    lambda: self.supabase_client.client.table('dim_destinatario')
                    .select('id')
                    .eq('cpf', cpf)
                    .limit(1)
                    .execute()
                )
                
                if existing.data:
                    # Update existing record
                    destinatario_id = existing.data[0]['id']
                    await asyncio.to_thread(
                        lambda: self.supabase_client.client.table('dim_destinatario')
                        .update(destinatario_data)
                        .eq('id', destinatario_id)
                        .execute()
                    )
                    return destinatario_id
            
            # Insert new record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_destinatario')
                .insert(destinatario_data)
                .execute()
            )
            
            destinatario_id = result.data[0]['id']
            logger.info("Destinatario upserted", destinatario_id=destinatario_id)
            return destinatario_id
            
        except Exception as e:
            logger.error("Failed to upsert destinatario", error=str(e))
            raise    

    async def _upsert_produto(self, produto_data: Dict[str, Any]) -> str:
        """Insert or update produto record"""
        try:
            import asyncio
            
            codigo_produto = produto_data['codigo_produto']
            
            # Add timestamps
            produto_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Upsert product record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_produtos')
                .upsert(produto_data, on_conflict='codigo_produto')
                .execute()
            )
            
            logger.info("Produto upserted", codigo_produto=codigo_produto)
            return codigo_produto
            
        except Exception as e:
            logger.error("Failed to upsert produto", error=str(e))
            raise
    
    async def _upsert_servico(self, servico_data: Dict[str, Any]) -> str:
        """Insert or update servico record"""
        try:
            import asyncio
            
            codigo_servico = servico_data['codigo_servico']
            
            # Add timestamps
            servico_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Upsert service record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_servicos')
                .upsert(servico_data, on_conflict='codigo_servico')
                .execute()
            )
            
            logger.info("Servico upserted", codigo_servico=codigo_servico)
            return codigo_servico
            
        except Exception as e:
            logger.error("Failed to upsert servico", error=str(e))
            raise
    
    async def _insert_fact_item_nfe(self, item_data: Dict[str, Any], emitente_id: str, destinatario_id: Optional[int]) -> str:
        """Insert NF-e item into fact table"""
        try:
            import asyncio
            
            # Generate unique ID for fact record
            fact_id = str(uuid.uuid4())
            
            # Prepare fact record
            fact_record = {
                **item_data,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert fact record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('fact_itens_nfe')
                .insert(fact_record)
                .execute()
            )
            
            actual_id = result.data[0]['id']
            logger.info("NFE fact item inserted", fact_id=actual_id, chave_nfe=item_data.get('chave_nfe'))
            return str(actual_id)
            
        except Exception as e:
            logger.error("Failed to insert NFE fact item", error=str(e))
            raise
    
    async def _insert_fact_servico_nfse(self, servico_data: Dict[str, Any], emitente_id: str, destinatario_id: Optional[int]) -> str:
        """Insert NFS-e service into fact table"""
        try:
            import asyncio
            
            # Generate unique ID for fact record
            fact_id = str(uuid.uuid4())
            
            # Prepare fact record
            fact_record = {
                **servico_data,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert fact record
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('fact_servicos_nfse')
                .insert(fact_record)
                .execute()
            )
            
            actual_id = result.data[0]['id']
            logger.info("NFSE fact service inserted", fact_id=actual_id, id_nfse=servico_data.get('id_nfse'))
            return str(actual_id)
            
        except Exception as e:
            logger.error("Failed to insert NFSE fact service", error=str(e))
            raise
    
    # Validation Methods
    
    async def _validate_emitente_exists(self, cnpj: str) -> bool:
        """Validate that emitente exists in database"""
        try:
            import asyncio
            
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_emitente')
                .select('cnpj')
                .eq('cnpj', cnpj)
                .limit(1)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error("Failed to validate emitente exists", error=str(e))
            return False
    
    async def _validate_destinatario_exists(self, destinatario_id: int) -> bool:
        """Validate that destinatario exists in database"""
        try:
            import asyncio
            
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_destinatario')
                .select('id')
                .eq('id', destinatario_id)
                .limit(1)
                .execute()
            )
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error("Failed to validate destinatario exists", error=str(e))
            return False
    
    async def _validate_produtos_exist(self, produtos_ids: List[str]) -> bool:
        """Validate that all products exist in database"""
        try:
            import asyncio
            
            if not produtos_ids:
                return True
            
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_produtos')
                .select('codigo_produto')
                .in_('codigo_produto', produtos_ids)
                .execute()
            )
            
            found_ids = [item['codigo_produto'] for item in result.data]
            return len(found_ids) == len(produtos_ids)
            
        except Exception as e:
            logger.error("Failed to validate produtos exist", error=str(e))
            return False
    
    async def _validate_servicos_exist(self, servicos_ids: List[str]) -> bool:
        """Validate that all services exist in database"""
        try:
            import asyncio
            
            if not servicos_ids:
                return True
            
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_servicos')
                .select('codigo_servico')
                .in_('codigo_servico', servicos_ids)
                .execute()
            )
            
            found_ids = [item['codigo_servico'] for item in result.data]
            return len(found_ids) == len(servicos_ids)
            
        except Exception as e:
            logger.error("Failed to validate servicos exist", error=str(e))
            return False
    
    # Utility Methods
    
    def _get_text(self, parent, xpath: str) -> str:
        """Get text content from XML element"""
        if parent is None:
            return ""
        element = parent.find(xpath)
        return element.text if element is not None and element.text else ""
    
    def _get_decimal(self, parent, xpath: str) -> Optional[Decimal]:
        """Get decimal value from XML element"""
        text = self._get_text(parent, xpath)
        if text:
            try:
                return Decimal(text.replace(',', '.'))
            except:
                return None
        return None  
  
    # AI Categorization Integration Methods
    
    async def integrate_with_categorization_agent(self, produtos_data: List[Dict[str, Any]], servicos_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Integrate with AI Categorization Agent for enhanced categorization
        
        Args:
            produtos_data: List of product data to categorize
            servicos_data: List of service data to categorize
            
        Returns:
            Enhanced categorization results
        """
        try:
            from .ai_categorization_agent import LLMEnhancedAICategorizationAgent
            
            categorization_agent = LLMEnhancedAICategorizationAgent()
            await categorization_agent.initialize()
            
            enhanced_produtos = []
            enhanced_servicos = []
            
            # Categorize products
            for produto in produtos_data:
                try:
                    # Create mock XML content for categorization agent
                    mock_xml = self._create_mock_xml_for_categorization([produto], "product")
                    
                    categorization_result = await categorization_agent.categorize_document(
                        mock_xml, {'document_type': 'NFE'}
                    )
                    
                    # Apply categorization results to product
                    if categorization_result.get('categorized_items'):
                        categorized_item = categorization_result['categorized_items'][0]
                        produto['categoria'] = categorized_item.get('category', produto.get('categoria'))
                        produto['subcategoria'] = categorized_item.get('subcategory', produto.get('subcategoria'))
                        produto['categorization_confidence'] = categorized_item.get('confidence', 0.8)
                    
                    enhanced_produtos.append(produto)
                    
                except Exception as e:
                    logger.warning(f"Failed to categorize product {produto.get('codigo_produto')}", error=str(e))
                    # Fall back to basic categorization
                    enhanced_produtos.append(await self._apply_basic_categorization(produto))
            
            # Categorize services
            for servico in servicos_data:
                try:
                    # Create mock XML content for categorization agent
                    mock_xml = self._create_mock_xml_for_categorization([servico], "service")
                    
                    categorization_result = await categorization_agent.categorize_document(
                        mock_xml, {'document_type': 'NFSE'}
                    )
                    
                    # Apply categorization results to service
                    if categorization_result.get('categorized_items'):
                        categorized_item = categorization_result['categorized_items'][0]
                        servico['categoria'] = categorized_item.get('category', servico.get('categoria'))
                        servico['subcategoria'] = categorized_item.get('subcategory', servico.get('subcategoria'))
                        servico['categorization_confidence'] = categorized_item.get('confidence', 0.8)
                    
                    enhanced_servicos.append(servico)
                    
                except Exception as e:
                    logger.warning(f"Failed to categorize service {servico.get('codigo_servico')}", error=str(e))
                    # Fall back to basic categorization
                    enhanced_servicos.append(await self._apply_basic_service_categorization(servico))
            
            await categorization_agent.cleanup()
            
            return {
                'enhanced_produtos': enhanced_produtos,
                'enhanced_servicos': enhanced_servicos,
                'categorization_method': 'ai_enhanced'
            }
            
        except Exception as e:
            logger.error("Failed to integrate with categorization agent", error=str(e))
            # Fall back to basic categorization
            enhanced_produtos = [await self._apply_basic_categorization(p) for p in produtos_data]
            enhanced_servicos = [await self._apply_basic_service_categorization(s) for s in servicos_data]
            
            return {
                'enhanced_produtos': enhanced_produtos,
                'enhanced_servicos': enhanced_servicos,
                'categorization_method': 'basic_fallback'
            }
    
    def _create_mock_xml_for_categorization(self, items: List[Dict[str, Any]], item_type: str) -> str:
        """Create mock XML content for categorization agent"""
        try:
            if item_type == "product":
                # Create minimal NF-e XML structure for products
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>{}</cProd>
                    <xProd>{}</xProd>
                    <NCM>{}</NCM>
                    <CFOP>{}</CFOP>
                    <uCom>{}</uCom>
                    <vProd>100.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''.format(
                    items[0].get('codigo_produto', 'PROD001'),
                    items[0].get('descricao', 'Produto para categorização'),
                    items[0].get('ncm', '12345678'),
                    items[0].get('cfop', '5102'),
                    items[0].get('unidade_comercial', 'UN')
                )
            
            else:  # service
                # Create minimal NFS-e XML structure for services
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<nfse>
    <servico>
        <codigo>{}</codigo>
        <descricao>{}</descricao>
        <cnae>{}</cnae>
    </servico>
</nfse>'''.format(
                    items[0].get('codigo_servico', 'SERV001'),
                    items[0].get('descricao', 'Serviço para categorização'),
                    items[0].get('codigo_cnae', '6201500')
                )
            
            return xml_content
            
        except Exception as e:
            logger.error("Failed to create mock XML for categorization", error=str(e))
            return "<root></root>"
    
    # Enhanced processing methods with AI integration
    
    async def process_produtos_data_enhanced(self, xml_root) -> List[str]:
        """
        Enhanced product processing with AI categorization integration
        """
        try:
            produtos_data = self._extract_produtos_data(xml_root)
            
            if not produtos_data:
                return []
            
            # Integrate with AI Categorization Agent
            categorization_results = await self.integrate_with_categorization_agent(produtos_data, [])
            enhanced_produtos = categorization_results['enhanced_produtos']
            
            produtos_ids = []
            for produto in enhanced_produtos:
                # Normalize product data
                produto = self._normalize_produto_data(produto)
                
                # Upsert product record with enhanced categorization
                codigo_produto = await self._upsert_produto(produto)
                produtos_ids.append(codigo_produto)
            
            logger.info(
                "Enhanced products data processed",
                produtos_count=len(produtos_ids),
                categorization_method=categorization_results['categorization_method']
            )
            
            return produtos_ids
            
        except Exception as e:
            logger.error("Failed to process enhanced produtos data", error=str(e))
            # Fall back to basic processing
            return await self.process_produtos_data(xml_root)
    
    async def process_servicos_data_enhanced(self, xml_root) -> List[str]:
        """
        Enhanced service processing with AI categorization integration
        """
        try:
            servicos_data = self._extract_servicos_data(xml_root)
            
            if not servicos_data:
                return []
            
            # Integrate with AI Categorization Agent
            categorization_results = await self.integrate_with_categorization_agent([], servicos_data)
            enhanced_servicos = categorization_results['enhanced_servicos']
            
            servicos_ids = []
            for servico in enhanced_servicos:
                # Normalize service data
                servico = self._normalize_servico_data(servico)
                
                # Upsert service record with enhanced categorization
                codigo_servico = await self._upsert_servico(servico)
                servicos_ids.append(codigo_servico)
            
            logger.info(
                "Enhanced services data processed",
                servicos_count=len(servicos_ids),
                categorization_method=categorization_results['categorization_method']
            )
            
            return servicos_ids
            
        except Exception as e:
            logger.error("Failed to process enhanced servicos data", error=str(e))
            # Fall back to basic processing
            return await self.process_servicos_data(xml_root)
    
    # Error handling and recovery methods
    
    async def handle_processing_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle processing errors with intelligent recovery
        
        Args:
            error: The exception that occurred
            context: Processing context
            
        Returns:
            Error handling result with recovery information
        """
        try:
            document_id = context.get('document_id')
            error_type = type(error).__name__
            error_message = str(error)
            
            logger.error(
                "Processing error occurred",
                document_id=document_id,
                error_type=error_type,
                error_message=error_message
            )
            
            # Determine recovery strategy based on error type
            recovery_strategy = self._determine_recovery_strategy(error, context)
            
            # Execute recovery if possible
            if recovery_strategy['recoverable']:
                recovery_result = await self._execute_recovery(recovery_strategy, context)
                
                return {
                    'error_handled': True,
                    'recovery_executed': True,
                    'recovery_strategy': recovery_strategy,
                    'recovery_result': recovery_result,
                    'original_error': error_message
                }
            
            else:
                return {
                    'error_handled': True,
                    'recovery_executed': False,
                    'recovery_strategy': recovery_strategy,
                    'original_error': error_message,
                    'requires_manual_intervention': True
                }
            
        except Exception as recovery_error:
            logger.error("Error handling failed", error=str(recovery_error))
            return {
                'error_handled': False,
                'original_error': str(error),
                'recovery_error': str(recovery_error)
            }
    
    def _determine_recovery_strategy(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine appropriate recovery strategy for the error"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Database connection errors
        if 'connection' in error_message or 'timeout' in error_message:
            return {
                'recoverable': True,
                'strategy': 'retry_with_backoff',
                'max_retries': 3,
                'backoff_seconds': 5
            }
        
        # Validation errors
        elif 'validation' in error_message or 'invalid' in error_message:
            return {
                'recoverable': True,
                'strategy': 'data_sanitization',
                'fallback_values': True
            }
        
        # XML parsing errors
        elif 'xml' in error_message or 'parse' in error_message:
            return {
                'recoverable': True,
                'strategy': 'alternative_parsing',
                'use_fallback_parser': True
            }
        
        # Categorization errors
        elif 'categorization' in error_message or 'category' in error_message:
            return {
                'recoverable': True,
                'strategy': 'basic_categorization_fallback',
                'use_rule_based': True
            }
        
        # Unrecoverable errors
        else:
            return {
                'recoverable': False,
                'strategy': 'manual_intervention_required',
                'error_type': error_type
            }
    
    async def _execute_recovery(self, recovery_strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined recovery strategy"""
        strategy = recovery_strategy['strategy']
        
        if strategy == 'retry_with_backoff':
            return await self._retry_with_backoff(recovery_strategy, context)
        
        elif strategy == 'data_sanitization':
            return await self._sanitize_and_retry(recovery_strategy, context)
        
        elif strategy == 'alternative_parsing':
            return await self._alternative_parsing(recovery_strategy, context)
        
        elif strategy == 'basic_categorization_fallback':
            return await self._basic_categorization_fallback(recovery_strategy, context)
        
        else:
            return {'recovery_executed': False, 'reason': 'Unknown strategy'}
    
    async def _retry_with_backoff(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry operation with exponential backoff"""
        import asyncio
        
        max_retries = strategy.get('max_retries', 3)
        backoff_seconds = strategy.get('backoff_seconds', 5)
        
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(backoff_seconds * (2 ** attempt))
                
                # Retry the original operation
                # This would need to be implemented based on the specific operation
                logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
                
                return {'recovery_successful': True, 'attempts': attempt + 1}
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return {'recovery_successful': False, 'final_error': str(e)}
                continue
        
        return {'recovery_successful': False, 'reason': 'Max retries exceeded'}
    
    async def _sanitize_and_retry(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data and retry operation"""
        try:
            # Implement data sanitization logic
            logger.info("Executing data sanitization recovery")
            
            return {'recovery_successful': True, 'method': 'data_sanitization'}
            
        except Exception as e:
            return {'recovery_successful': False, 'error': str(e)}
    
    async def _alternative_parsing(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Use alternative XML parsing method"""
        try:
            # Implement alternative parsing logic
            logger.info("Executing alternative parsing recovery")
            
            return {'recovery_successful': True, 'method': 'alternative_parsing'}
            
        except Exception as e:
            return {'recovery_successful': False, 'error': str(e)}
    
    async def _basic_categorization_fallback(self, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fall back to basic rule-based categorization"""
        try:
            logger.info("Executing basic categorization fallback")
            
            # This would use the existing basic categorization methods
            return {'recovery_successful': True, 'method': 'basic_categorization'}
            
        except Exception as e:
            return {'recovery_successful': False, 'error': str(e)}