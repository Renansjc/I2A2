"""
XML Processing Agent for NF-e and NFS-e documents
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
from lxml import etree
import xmlschema
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import structlog
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .base_agent import BaseAgent
from models.fiscal_data import (
    NFEData, NFSEData, DocumentType, ProcessingError, FiscalDocument,
    Supplier, Recipient, Address, Product, Service, Tax, ISSQNTax, NFEItem, NFSEItem
)
from utils.config import settings
from utils.database import DatabaseManager
from utils.openai_integration import obter_servico_openai, AnaliseDocumento


class XMLFileHandler(FileSystemEventHandler):
    """File system event handler for XML files"""
    
    def __init__(self, agent):
        self.agent = agent
        self.logger = structlog.get_logger("xml_file_handler")
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory and event.src_path.endswith('.xml'):
            self.logger.info("New XML file detected", file_path=event.src_path)
            # Schedule the coroutine to run in the event loop
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.agent.process_xml_file(event.src_path))
            except RuntimeError:
                # No running event loop, schedule for later
                self.logger.warning("No running event loop, file will be processed manually")
                # In a real implementation, you would queue this for processing


class XMLProcessingAgent(BaseAgent):
    """Agent responsible for processing XML invoice files (NF-e and NFS-e)"""
    
    def __init__(self):
        super().__init__("XMLProcessingAgent")
        self.observer = None
        self.file_handler = None
        self.nfe_schema = None
        self.nfse_schema = None
        
    async def initialize(self):
        """Initialize XML processing resources"""
        try:
            # Create directories if they don't exist
            os.makedirs(settings.XML_WATCH_DIRECTORY, exist_ok=True)
            os.makedirs(settings.XML_PROCESSED_DIRECTORY, exist_ok=True)
            os.makedirs(settings.XML_ERROR_DIRECTORY, exist_ok=True)
            
            # Load XML schemas for validation (if available)
            await self._load_schemas()
            
            # Initialize OpenAI service for LLM capabilities
            self.openai_service = await obter_servico_openai()
            
            # Set up file system monitoring
            self.file_handler = XMLFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                settings.XML_WATCH_DIRECTORY,
                recursive=False
            )
            self.observer.start()
            
            self.logger.info("XML Processing Agent initialized with LLM capabilities", 
                           watch_directory=settings.XML_WATCH_DIRECTORY)
            
        except Exception as e:
            self.logger.error("Failed to initialize XML Processing Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.logger.info("XML Processing Agent cleaned up")
    
    async def process(self, data: str) -> Optional[FiscalDocument]:
        """Process XML file path"""
        if isinstance(data, str) and data.endswith('.xml'):
            return await self.process_xml_file(data)
        return None
    
    async def _load_schemas(self):
        """Load XML schemas for validation"""
        try:
            # Create schemas directory if it doesn't exist
            schema_dir = Path("./schemas")
            schema_dir.mkdir(exist_ok=True)
            
            # Try to load NF-e schema
            nfe_schema_path = schema_dir / "nfe_v4.00.xsd"
            if nfe_schema_path.exists():
                self.nfe_schema = xmlschema.XMLSchema(str(nfe_schema_path))
                self.logger.info("NF-e schema loaded", schema_path=str(nfe_schema_path))
            else:
                self.logger.warning("NF-e schema not found", expected_path=str(nfe_schema_path))
            
            # Try to load NFS-e schema
            nfse_schema_path = schema_dir / "nfse.xsd"
            if nfse_schema_path.exists():
                self.nfse_schema = xmlschema.XMLSchema(str(nfse_schema_path))
                self.logger.info("NFS-e schema loaded", schema_path=str(nfse_schema_path))
            else:
                self.logger.warning("NFS-e schema not found", expected_path=str(nfse_schema_path))
            
            self.logger.info("XML schema loading completed")
            
        except Exception as e:
            self.logger.warning("Could not load XML schemas", error=str(e))
    
    async def process_xml_file(self, file_path: str) -> Optional[FiscalDocument]:
        """Process a single XML file"""
        try:
            self.logger.info("Processing XML file", file_path=file_path)
            
            # Read XML content
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            # Detect document type
            doc_type = await self.detect_document_type(xml_content)
            
            # Validate schema
            if not await self.validate_schema(xml_content, doc_type):
                raise ValueError(f"Schema validation failed for {doc_type}")
            
            # Extract fiscal data
            fiscal_data = await self.extract_fiscal_data(xml_content, doc_type, file_path)
            
            # Perform LLM-enhanced semantic analysis
            if hasattr(self, 'openai_service') and self.openai_service:
                try:
                    # Semantic analysis
                    semantic_analysis = await self.analyze_document_semantics(fiscal_data)
                    
                    # Business insights generation
                    business_insights = await self.extract_business_insights(fiscal_data, semantic_analysis)
                    
                    # Contextual validation
                    validation_results = await self.validate_with_context(fiscal_data)
                    
                    # Add LLM analysis results to fiscal data metadata
                    if not hasattr(fiscal_data, 'llm_analysis'):
                        fiscal_data.llm_analysis = {}
                    
                    fiscal_data.llm_analysis = {
                        'semantic_analysis': semantic_analysis,
                        'business_insights': business_insights,
                        'validation_results': validation_results,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                    
                    self.logger.info("LLM analysis completed successfully", 
                                   document_id=getattr(fiscal_data, 'chave_nfe', None) or getattr(fiscal_data, 'id_nfse', None),
                                   semantic_score=semantic_analysis.score_confianca,
                                   validation_score=validation_results.get('score_validacao', 0))
                    
                except Exception as e:
                    self.logger.warning("LLM analysis failed, continuing with basic processing", error=str(e))
                    # Continue processing even if LLM analysis fails
            
            # Move file to processed directory
            await self._move_processed_file(file_path)
            
            # Notify completion with enhanced data
            await self.notify_processing_complete(fiscal_data)
            
            return fiscal_data
            
        except Exception as e:
            error = ProcessingError(
                file_path=file_path,
                error_type=type(e).__name__,
                error_message=str(e),
                timestamp=datetime.now(),
                agent_name=self.agent_name
            )
            await self.handle_processing_error(error)
            return None
    
    async def detect_document_type(self, xml_content: str) -> DocumentType:
        """Detect if XML is NF-e or NFS-e"""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Check for NF-e indicators
            if any(tag in root.tag.lower() for tag in ['nfe', 'nfproc', 'infnfe']):
                return DocumentType.NFE
            
            # Check for NFS-e indicators
            if any(tag in root.tag.lower() for tag in ['nfse', 'rps', 'infnfse']):
                return DocumentType.NFSE
            
            # Fallback: check namespace or specific elements
            namespaces = root.nsmap
            if namespaces:
                for ns in namespaces.values():
                    if 'nfe' in ns.lower():
                        return DocumentType.NFE
                    elif 'nfse' in ns.lower():
                        return DocumentType.NFSE
            
            # Default to NFE if uncertain
            self.logger.warning("Could not determine document type, defaulting to NFE", 
                              root_tag=root.tag)
            return DocumentType.NFE
            
        except Exception as e:
            self.logger.error("Error detecting document type", error=str(e))
            return DocumentType.NFE
    
    async def validate_schema(self, xml_content: str, doc_type: DocumentType) -> bool:
        """Validate XML against schema"""
        try:
            # Basic XML well-formedness check
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Schema validation if schemas are available
            if doc_type == DocumentType.NFE and self.nfe_schema:
                try:
                    self.nfe_schema.validate(xml_content)
                    self.logger.info("NF-e schema validation passed")
                    return True
                except xmlschema.XMLSchemaException as e:
                    self.logger.error("NF-e schema validation failed", error=str(e))
                    return False
                    
            elif doc_type == DocumentType.NFSE and self.nfse_schema:
                try:
                    self.nfse_schema.validate(xml_content)
                    self.logger.info("NFS-e schema validation passed")
                    return True
                except xmlschema.XMLSchemaException as e:
                    self.logger.error("NFS-e schema validation failed", error=str(e))
                    return False
            
            # If no schema available, perform basic structural validation
            return await self._basic_structural_validation(root, doc_type)
            
        except etree.XMLSyntaxError as e:
            self.logger.error("XML syntax error", error=str(e))
            return False
        except Exception as e:
            self.logger.error("Schema validation error", error=str(e))
            return False
    
    async def _basic_structural_validation(self, root: etree.Element, doc_type: DocumentType) -> bool:
        """Perform basic structural validation when schemas are not available"""
        try:
            if doc_type == DocumentType.NFE:
                # Check for essential NF-e elements
                required_elements = ['infNFe', 'emit', 'dest', 'det']
                namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
                
                for element in required_elements:
                    # Try with namespace first
                    found = root.find(f'.//nfe:{element}', namespaces)
                    if found is None:
                        # Try without namespace
                        found = root.find(f'.//{element}')
                    
                    if found is None:
                        self.logger.warning("Missing required NF-e element", element=element)
                        return False
                
                self.logger.info("Basic NF-e structural validation passed")
                return True
                
            elif doc_type == DocumentType.NFSE:
                # Check for essential NFS-e elements (more flexible)
                required_elements = ['InfNfse', 'Nfse', 'PrestadorServico', 'Servico']
                found_count = 0
                
                for element in required_elements:
                    found = root.find(f'.//{element}')
                    if found is not None:
                        found_count += 1
                
                # Require at least 2 essential elements to be present
                if found_count >= 2:
                    self.logger.info("Basic NFS-e structural validation passed")
                    return True
                else:
                    self.logger.warning("Insufficient NFS-e elements found", found_count=found_count)
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("Basic structural validation failed", error=str(e))
            return False
    
    async def extract_fiscal_data(self, xml_content: str, doc_type: DocumentType, file_path: str) -> FiscalDocument:
        """Extract fiscal data from XML"""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            if doc_type == DocumentType.NFE:
                return await self._extract_nfe_data(root, file_path)
            else:
                return await self._extract_nfse_data(root, file_path)
                
        except Exception as e:
            self.logger.error("Error extracting fiscal data", error=str(e))
            raise
    
    async def _extract_nfe_data(self, root, file_path: str) -> NFEData:
        """Extract NF-e specific data"""
        try:
            # Define namespaces
            namespaces = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Find the infNFe element (main invoice info)
            inf_nfe = root.find('.//nfe:infNFe', namespaces)
            if inf_nfe is None:
                inf_nfe = root.find('.//infNFe')
            
            if inf_nfe is None:
                raise ValueError("Could not find infNFe element in XML")
            
            # Extract NFe key
            chave_nfe = inf_nfe.get('Id', '').replace('NFe', '')
            
            # Extract identification data (ide)
            ide = inf_nfe.find('.//nfe:ide', namespaces) or inf_nfe.find('.//ide')
            if ide is None:
                raise ValueError("Could not find ide element in XML")
            
            numero_nf = self._get_element_text(ide, 'nNF', namespaces)
            serie = self._get_element_text(ide, 'serie', namespaces)
            data_emissao_str = self._get_element_text(ide, 'dhEmi', namespaces)
            data_saida_str = self._get_element_text(ide, 'dhSaiEnt', namespaces)
            tipo_operacao = self._get_element_text(ide, 'tpNF', namespaces)
            codigo_municipio = self._get_element_text(ide, 'cMunFG', namespaces)
            natureza_operacao = self._get_element_text(ide, 'natOp', namespaces)
            
            # Parse dates
            data_emissao = self._parse_datetime(data_emissao_str)
            data_saida_entrada = self._parse_datetime(data_saida_str) if data_saida_str else None
            
            # Extract supplier data (emit)
            emit = inf_nfe.find('.//nfe:emit', namespaces) or inf_nfe.find('.//emit')
            supplier = await self._extract_supplier_data(emit, namespaces)
            
            # Extract recipient data (dest)
            dest = inf_nfe.find('.//nfe:dest', namespaces) or inf_nfe.find('.//dest')
            recipient = await self._extract_recipient_data(dest, namespaces)
            
            # Extract items (det)
            det_elements = inf_nfe.findall('.//nfe:det', namespaces) or inf_nfe.findall('.//det')
            items = []
            for det in det_elements:
                item = await self._extract_nfe_item(det, namespaces)
                if item:
                    items.append(item)
            
            # Extract totals (total)
            total = inf_nfe.find('.//nfe:total', namespaces) or inf_nfe.find('.//total')
            totals_data = await self._extract_nfe_totals(total, namespaces)
            
            # Get UF from supplier address
            uf_emitente = supplier.address.uf if supplier and supplier.address else "SP"
            
            nfe_data = NFEData(
                chave_nfe=chave_nfe or "00000000000000000000000000000000000000000000",
                numero_nf=numero_nf or "1",
                serie=serie or "1",
                data_emissao=data_emissao,
                data_saida_entrada=data_saida_entrada,
                tipo_operacao=tipo_operacao or "1",
                codigo_municipio=codigo_municipio or "3550308",
                uf_emitente=uf_emitente,
                natureza_operacao=natureza_operacao or "Venda",
                supplier=supplier,
                recipient=recipient,
                items=items,
                xml_file_path=file_path,
                **totals_data
            )
            
            self.logger.info("NF-e data extracted successfully", 
                           chave_nfe=chave_nfe, 
                           items_count=len(items))
            
            return nfe_data
            
        except Exception as e:
            self.logger.error("Error extracting NF-e data", error=str(e))
            raise
    
    async def _extract_supplier_data(self, emit_element, namespaces: Dict[str, str]) -> Supplier:
        """Extract supplier data from emit element"""
        if emit_element is None:
            raise ValueError("Supplier element (emit) not found")
        
        cnpj = self._get_element_text(emit_element, 'CNPJ', namespaces)
        cpf = self._get_element_text(emit_element, 'CPF', namespaces)
        inscricao_estadual = self._get_element_text(emit_element, 'IE', namespaces)
        razao_social = self._get_element_text(emit_element, 'xNome', namespaces)
        nome_fantasia = self._get_element_text(emit_element, 'xFant', namespaces)
        
        # Extract address
        ender_emit = emit_element.find('.//nfe:enderEmit', namespaces) or emit_element.find('.//enderEmit')
        address = await self._extract_address_data(ender_emit, namespaces)
        
        return Supplier(
            cnpj=cnpj,
            cpf=cpf,
            inscricao_estadual=inscricao_estadual,
            razao_social=razao_social or "Fornecedor",
            nome_fantasia=nome_fantasia,
            address=address
        )
    
    async def _extract_recipient_data(self, dest_element, namespaces: Dict[str, str]) -> Recipient:
        """Extract recipient data from dest element"""
        if dest_element is None:
            raise ValueError("Recipient element (dest) not found")
        
        cnpj = self._get_element_text(dest_element, 'CNPJ', namespaces)
        cpf = self._get_element_text(dest_element, 'CPF', namespaces)
        inscricao_estadual = self._get_element_text(dest_element, 'IE', namespaces)
        razao_social = self._get_element_text(dest_element, 'xNome', namespaces)
        
        # Extract address
        ender_dest = dest_element.find('.//nfe:enderDest', namespaces) or dest_element.find('.//enderDest')
        address = await self._extract_address_data(ender_dest, namespaces)
        
        return Recipient(
            cnpj=cnpj,
            cpf=cpf,
            inscricao_estadual=inscricao_estadual,
            razao_social=razao_social or "Cliente",
            address=address
        )
    
    async def _extract_address_data(self, address_element, namespaces: Dict[str, str]) -> Address:
        """Extract address data from address element"""
        if address_element is None:
            # Return default address if not found
            return Address(
                logradouro="Não informado",
                numero="S/N",
                complemento=None,
                bairro="Centro",
                codigo_municipio="3550308",
                nome_municipio="São Paulo",
                uf="SP",
                cep="01000000"
            )
        
        return Address(
            logradouro=self._get_element_text(address_element, 'xLgr', namespaces) or "Não informado",
            numero=self._get_element_text(address_element, 'nro', namespaces) or "S/N",
            complemento=self._get_element_text(address_element, 'xCpl', namespaces),
            bairro=self._get_element_text(address_element, 'xBairro', namespaces) or "Centro",
            codigo_municipio=self._get_element_text(address_element, 'cMun', namespaces) or "3550308",
            nome_municipio=self._get_element_text(address_element, 'xMun', namespaces) or "São Paulo",
            uf=self._get_element_text(address_element, 'UF', namespaces) or "SP",
            cep=self._get_element_text(address_element, 'CEP', namespaces) or "01000000"
        )
    
    async def _extract_nfe_item(self, det_element, namespaces: Dict[str, str]) -> Optional[NFEItem]:
        """Extract NFE item from det element"""
        try:
            numero_item = int(det_element.get('nItem', '1'))
            
            # Extract product data
            prod = det_element.find('.//nfe:prod', namespaces) or det_element.find('.//prod')
            if prod is None:
                return None
            
            product = Product(
                codigo_produto=self._get_element_text(prod, 'cProd', namespaces) or "PROD001",
                ean=self._get_element_text(prod, 'cEAN', namespaces),
                descricao=self._get_element_text(prod, 'xProd', namespaces) or "Produto",
                ncm=self._get_element_text(prod, 'NCM', namespaces) or "00000000",
                cest=self._get_element_text(prod, 'CEST', namespaces),
                cfop=self._get_element_text(prod, 'CFOP', namespaces) or "5102",
                unidade_comercial=self._get_element_text(prod, 'uCom', namespaces) or "UN",
                unidade_tributavel=self._get_element_text(prod, 'uTrib', namespaces)
            )
            
            # Extract quantities and values
            quantidade_comercial = self._parse_decimal(self._get_element_text(prod, 'qCom', namespaces))
            valor_unitario_comercial = self._parse_decimal(self._get_element_text(prod, 'vUnCom', namespaces))
            valor_total_bruto = self._parse_decimal(self._get_element_text(prod, 'vProd', namespaces))
            
            # Extract optional values
            quantidade_tributavel = self._parse_decimal(self._get_element_text(prod, 'qTrib', namespaces))
            valor_unitario_tributavel = self._parse_decimal(self._get_element_text(prod, 'vUnTrib', namespaces))
            valor_frete = self._parse_decimal(self._get_element_text(prod, 'vFrete', namespaces))
            valor_seguro = self._parse_decimal(self._get_element_text(prod, 'vSeg', namespaces))
            valor_desconto = self._parse_decimal(self._get_element_text(prod, 'vDesc', namespaces))
            valor_outras_despesas = self._parse_decimal(self._get_element_text(prod, 'vOutro', namespaces))
            
            # Extract taxes
            taxes = await self._extract_nfe_item_taxes(det_element, namespaces)
            
            return NFEItem(
                numero_item=numero_item,
                produto=product,
                quantidade_comercial=quantidade_comercial or Decimal('1'),
                valor_unitario_comercial=valor_unitario_comercial or Decimal('0'),
                valor_total_bruto=valor_total_bruto or Decimal('0'),
                quantidade_tributavel=quantidade_tributavel,
                valor_unitario_tributavel=valor_unitario_tributavel,
                valor_frete=valor_frete,
                valor_seguro=valor_seguro,
                valor_desconto=valor_desconto,
                valor_outras_despesas=valor_outras_despesas,
                taxes=taxes
            )
            
        except Exception as e:
            self.logger.error("Error extracting NFE item", error=str(e))
            return None
    
    async def _extract_nfe_item_taxes(self, det_element, namespaces: Dict[str, str]) -> List[Tax]:
        """Extract tax information from item"""
        taxes = []
        
        try:
            imposto = det_element.find('.//nfe:imposto', namespaces) or det_element.find('.//imposto')
            if imposto is None:
                return taxes
            
            # Extract ICMS
            icms = imposto.find('.//nfe:ICMS', namespaces) or imposto.find('.//ICMS')
            if icms is not None:
                icms_tax = await self._extract_icms_tax(icms, namespaces)
                if icms_tax:
                    taxes.append(icms_tax)
            
            # Extract IPI
            ipi = imposto.find('.//nfe:IPI', namespaces) or imposto.find('.//IPI')
            if ipi is not None:
                ipi_tax = await self._extract_ipi_tax(ipi, namespaces)
                if ipi_tax:
                    taxes.append(ipi_tax)
            
            # Extract PIS
            pis = imposto.find('.//nfe:PIS', namespaces) or imposto.find('.//PIS')
            if pis is not None:
                pis_tax = await self._extract_pis_tax(pis, namespaces)
                if pis_tax:
                    taxes.append(pis_tax)
            
            # Extract COFINS
            cofins = imposto.find('.//nfe:COFINS', namespaces) or imposto.find('.//COFINS')
            if cofins is not None:
                cofins_tax = await self._extract_cofins_tax(cofins, namespaces)
                if cofins_tax:
                    taxes.append(cofins_tax)
            
        except Exception as e:
            self.logger.error("Error extracting item taxes", error=str(e))
        
        return taxes
    
    async def _extract_icms_tax(self, icms_element, namespaces: Dict[str, str]) -> Optional[Tax]:
        """Extract ICMS tax information"""
        try:
            # ICMS can have different situations (ICMS00, ICMS10, etc.)
            for child in icms_element:
                if 'ICMS' in child.tag:
                    origem = self._get_element_text(child, 'orig', namespaces)
                    situacao = self._get_element_text(child, 'CST', namespaces)
                    base_calculo = self._parse_decimal(self._get_element_text(child, 'vBC', namespaces))
                    aliquota = self._parse_decimal(self._get_element_text(child, 'pICMS', namespaces))
                    valor = self._parse_decimal(self._get_element_text(child, 'vICMS', namespaces))
                    
                    return Tax(
                        tax_type="ICMS",
                        origem_produto=origem,
                        situacao_tributaria=situacao or "00",
                        base_calculo=base_calculo or Decimal('0'),
                        aliquota=aliquota or Decimal('0'),
                        valor=valor or Decimal('0')
                    )
        except Exception as e:
            self.logger.error("Error extracting ICMS tax", error=str(e))
        
        return None
    
    async def _extract_ipi_tax(self, ipi_element, namespaces: Dict[str, str]) -> Optional[Tax]:
        """Extract IPI tax information"""
        try:
            ipi_trib = ipi_element.find('.//nfe:IPITrib', namespaces) or ipi_element.find('.//IPITrib')
            if ipi_trib is not None:
                situacao = self._get_element_text(ipi_trib, 'CST', namespaces)
                base_calculo = self._parse_decimal(self._get_element_text(ipi_trib, 'vBC', namespaces))
                aliquota = self._parse_decimal(self._get_element_text(ipi_trib, 'pIPI', namespaces))
                valor = self._parse_decimal(self._get_element_text(ipi_trib, 'vIPI', namespaces))
                
                return Tax(
                    tax_type="IPI",
                    origem_produto=None,
                    situacao_tributaria=situacao or "00",
                    base_calculo=base_calculo or Decimal('0'),
                    aliquota=aliquota or Decimal('0'),
                    valor=valor or Decimal('0')
                )
        except Exception as e:
            self.logger.error("Error extracting IPI tax", error=str(e))
        
        return None
    
    async def _extract_pis_tax(self, pis_element, namespaces: Dict[str, str]) -> Optional[Tax]:
        """Extract PIS tax information"""
        try:
            for child in pis_element:
                if 'PIS' in child.tag:
                    situacao = self._get_element_text(child, 'CST', namespaces)
                    base_calculo = self._parse_decimal(self._get_element_text(child, 'vBC', namespaces))
                    aliquota = self._parse_decimal(self._get_element_text(child, 'pPIS', namespaces))
                    valor = self._parse_decimal(self._get_element_text(child, 'vPIS', namespaces))
                    
                    return Tax(
                        tax_type="PIS",
                        origem_produto=None,
                        situacao_tributaria=situacao or "01",
                        base_calculo=base_calculo or Decimal('0'),
                        aliquota=aliquota or Decimal('0'),
                        valor=valor or Decimal('0')
                    )
        except Exception as e:
            self.logger.error("Error extracting PIS tax", error=str(e))
        
        return None
    
    async def _extract_cofins_tax(self, cofins_element, namespaces: Dict[str, str]) -> Optional[Tax]:
        """Extract COFINS tax information"""
        try:
            for child in cofins_element:
                if 'COFINS' in child.tag:
                    situacao = self._get_element_text(child, 'CST', namespaces)
                    base_calculo = self._parse_decimal(self._get_element_text(child, 'vBC', namespaces))
                    aliquota = self._parse_decimal(self._get_element_text(child, 'pCOFINS', namespaces))
                    valor = self._parse_decimal(self._get_element_text(child, 'vCOFINS', namespaces))
                    
                    return Tax(
                        tax_type="COFINS",
                        origem_produto=None,
                        situacao_tributaria=situacao or "01",
                        base_calculo=base_calculo or Decimal('0'),
                        aliquota=aliquota or Decimal('0'),
                        valor=valor or Decimal('0')
                    )
        except Exception as e:
            self.logger.error("Error extracting COFINS tax", error=str(e))
        
        return None
    
    async def _extract_nfe_totals(self, total_element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Extract totals from NFE"""
        totals = {}
        
        try:
            if total_element is None:
                return {
                    'valor_total_nf': Decimal('0'),
                    'valor_total_produtos': Decimal('0'),
                    'valor_total_servicos': None,
                    'base_calculo_icms': None,
                    'valor_icms': None,
                    'base_calculo_icms_st': None,
                    'valor_icms_st': None,
                    'valor_total_ipi': None,
                    'valor_pis': None,
                    'valor_cofins': None
                }
            
            # ICMSTot contains the main totals
            icms_tot = total_element.find('.//nfe:ICMSTot', namespaces) or total_element.find('.//ICMSTot')
            if icms_tot is not None:
                totals.update({
                    'base_calculo_icms': self._parse_decimal(self._get_element_text(icms_tot, 'vBC', namespaces)),
                    'valor_icms': self._parse_decimal(self._get_element_text(icms_tot, 'vICMS', namespaces)),
                    'base_calculo_icms_st': self._parse_decimal(self._get_element_text(icms_tot, 'vBCST', namespaces)),
                    'valor_icms_st': self._parse_decimal(self._get_element_text(icms_tot, 'vST', namespaces)),
                    'valor_total_produtos': self._parse_decimal(self._get_element_text(icms_tot, 'vProd', namespaces)),
                    'valor_total_ipi': self._parse_decimal(self._get_element_text(icms_tot, 'vIPI', namespaces)),
                    'valor_pis': self._parse_decimal(self._get_element_text(icms_tot, 'vPIS', namespaces)),
                    'valor_cofins': self._parse_decimal(self._get_element_text(icms_tot, 'vCOFINS', namespaces)),
                    'valor_total_nf': self._parse_decimal(self._get_element_text(icms_tot, 'vNF', namespaces))
                })
            
            # Set defaults for missing values
            for key in ['valor_total_nf', 'valor_total_produtos']:
                if key not in totals or totals[key] is None:
                    totals[key] = Decimal('0')
            
            totals['valor_total_servicos'] = None  # NFE doesn't have services
            
        except Exception as e:
            self.logger.error("Error extracting NFE totals", error=str(e))
            # Return default values
            totals = {
                'valor_total_nf': Decimal('0'),
                'valor_total_produtos': Decimal('0'),
                'valor_total_servicos': None,
                'base_calculo_icms': None,
                'valor_icms': None,
                'base_calculo_icms_st': None,
                'valor_icms_st': None,
                'valor_total_ipi': None,
                'valor_pis': None,
                'valor_cofins': None
            }
        
        return totals
    
    async def _extract_nfse_data(self, root, file_path: str) -> NFSEData:
        """Extract NFS-e specific data"""
        try:
            # Find the main NFS-e info element
            inf_nfse = root.find('.//InfNfse') or root.find('.//infNfse')
            if inf_nfse is None:
                raise ValueError("Could not find InfNfse element in XML")
            
            # Extract identification data
            numero_nfse = self._get_element_text(inf_nfse, 'Numero') or self._get_element_text(inf_nfse, 'numero')
            codigo_verificacao = self._get_element_text(inf_nfse, 'CodigoVerificacao')
            data_emissao_str = self._get_element_text(inf_nfse, 'DataEmissao')
            
            # Parse date
            data_emissao = self._parse_datetime(data_emissao_str) if data_emissao_str else datetime.now()
            
            # Extract service provider data (PrestadorServico)
            prestador = inf_nfse.find('.//PrestadorServico') or inf_nfse.find('.//prestadorServico')
            supplier = await self._extract_nfse_supplier_data(prestador)
            
            # Extract service taker data (TomadorServico)
            tomador = inf_nfse.find('.//TomadorServico') or inf_nfse.find('.//tomadorServico')
            recipient = await self._extract_nfse_recipient_data(tomador)
            
            # Extract service data
            servico = inf_nfse.find('.//Servico') or inf_nfse.find('.//servico')
            services, service_totals = await self._extract_nfse_services(servico)
            
            # Extract additional data
            outras_informacoes = self._get_element_text(inf_nfse, 'OutrasInformacoes')
            
            # Generate ID if not present
            id_nfse = f"NFSE{numero_nfse or '1'}{data_emissao.strftime('%Y%m%d')}"
            
            nfse_data = NFSEData(
                id_nfse=id_nfse,
                numero_nfse=numero_nfse or "1",
                codigo_municipio_emissao=supplier.address.codigo_municipio if supplier else "3550308",
                data_emissao=data_emissao,
                supplier=supplier,
                recipient=recipient,
                services=services,
                xml_file_path=file_path,
                **service_totals
            )
            
            self.logger.info("NFS-e data extracted successfully", 
                           numero_nfse=numero_nfse, 
                           services_count=len(services))
            
            return nfse_data
            
        except Exception as e:
            self.logger.error("Error extracting NFS-e data", error=str(e))
            raise
    
    async def _extract_nfse_supplier_data(self, prestador_element) -> Supplier:
        """Extract supplier data from PrestadorServico element"""
        if prestador_element is None:
            raise ValueError("Service provider element (PrestadorServico) not found")
        
        # Extract identification
        identificacao = prestador_element.find('.//IdentificacaoPrestador') or prestador_element.find('.//identificacaoPrestador')
        cnpj = None
        cpf = None
        inscricao_municipal = None
        
        if identificacao is not None:
            cnpj = self._get_element_text(identificacao, 'Cnpj') or self._get_element_text(identificacao, 'cnpj')
            cpf = self._get_element_text(identificacao, 'Cpf') or self._get_element_text(identificacao, 'cpf')
            inscricao_municipal = self._get_element_text(identificacao, 'InscricaoMunicipal')
        
        # Extract company name
        razao_social = self._get_element_text(prestador_element, 'RazaoSocial') or self._get_element_text(prestador_element, 'razaoSocial')
        nome_fantasia = self._get_element_text(prestador_element, 'NomeFantasia') or self._get_element_text(prestador_element, 'nomeFantasia')
        
        # Extract address
        endereco = prestador_element.find('.//Endereco') or prestador_element.find('.//endereco')
        address = await self._extract_nfse_address_data(endereco)
        
        return Supplier(
            cnpj=cnpj,
            cpf=cpf,
            inscricao_estadual=inscricao_municipal,
            razao_social=razao_social or "Prestador de Serviço",
            nome_fantasia=nome_fantasia,
            address=address
        )
    
    async def _extract_nfse_recipient_data(self, tomador_element) -> Recipient:
        """Extract recipient data from TomadorServico element"""
        if tomador_element is None:
            # Create default recipient if not found
            return Recipient(
                cnpj=None,
                cpf=None,
                inscricao_estadual=None,
                razao_social="Tomador de Serviço",
                address=Address(
                    logradouro="Não informado",
                    numero="S/N",
                    complemento=None,
                    bairro="Centro",
                    codigo_municipio="3550308",
                    nome_municipio="São Paulo",
                    uf="SP",
                    cep="01000000"
                )
            )
        
        # Extract identification
        identificacao = tomador_element.find('.//IdentificacaoTomador') or tomador_element.find('.//identificacaoTomador')
        cnpj = None
        cpf = None
        inscricao_municipal = None
        
        if identificacao is not None:
            cnpj = self._get_element_text(identificacao, 'CpfCnpj/Cnpj') or self._get_element_text(identificacao, 'Cnpj')
            cpf = self._get_element_text(identificacao, 'CpfCnpj/Cpf') or self._get_element_text(identificacao, 'Cpf')
            inscricao_municipal = self._get_element_text(identificacao, 'InscricaoMunicipal')
        
        # Extract company name
        razao_social = self._get_element_text(tomador_element, 'RazaoSocial') or self._get_element_text(tomador_element, 'razaoSocial')
        
        # Extract address
        endereco = tomador_element.find('.//Endereco') or tomador_element.find('.//endereco')
        address = await self._extract_nfse_address_data(endereco)
        
        return Recipient(
            cnpj=cnpj,
            cpf=cpf,
            inscricao_estadual=inscricao_municipal,
            razao_social=razao_social or "Tomador de Serviço",
            address=address
        )
    
    async def _extract_nfse_address_data(self, endereco_element) -> Address:
        """Extract address data from NFS-e address element"""
        if endereco_element is None:
            return Address(
                logradouro="Não informado",
                numero="S/N",
                complemento=None,
                bairro="Centro",
                codigo_municipio="3550308",
                nome_municipio="São Paulo",
                uf="SP",
                cep="01000000"
            )
        
        return Address(
            logradouro=self._get_element_text(endereco_element, 'Endereco') or self._get_element_text(endereco_element, 'endereco') or "Não informado",
            numero=self._get_element_text(endereco_element, 'Numero') or self._get_element_text(endereco_element, 'numero') or "S/N",
            complemento=self._get_element_text(endereco_element, 'Complemento') or self._get_element_text(endereco_element, 'complemento'),
            bairro=self._get_element_text(endereco_element, 'Bairro') or self._get_element_text(endereco_element, 'bairro') or "Centro",
            codigo_municipio=self._get_element_text(endereco_element, 'CodigoMunicipio') or self._get_element_text(endereco_element, 'codigoMunicipio') or "3550308",
            nome_municipio=self._get_element_text(endereco_element, 'Municipio') or self._get_element_text(endereco_element, 'municipio') or "São Paulo",
            uf=self._get_element_text(endereco_element, 'Uf') or self._get_element_text(endereco_element, 'uf') or "SP",
            cep=self._get_element_text(endereco_element, 'Cep') or self._get_element_text(endereco_element, 'cep') or "01000000"
        )
    
    async def _extract_nfse_services(self, servico_element) -> tuple[List[NFSEItem], Dict[str, Any]]:
        """Extract services and totals from NFS-e"""
        services = []
        totals = {}
        
        try:
            if servico_element is None:
                return services, {
                    'valor_total_servicos': Decimal('0'),
                    'valor_total_deducoes': None,
                    'valor_base_calculo': Decimal('0'),
                    'valor_issqn': Decimal('0'),
                    'valor_credito': None
                }
            
            # Extract service values
            valores = servico_element.find('.//Valores') or servico_element.find('.//valores')
            if valores is not None:
                totals = {
                    'valor_total_servicos': self._parse_decimal(self._get_element_text(valores, 'ValorServicos')) or Decimal('0'),
                    'valor_total_deducoes': self._parse_decimal(self._get_element_text(valores, 'ValorDeducoes')),
                    'valor_base_calculo': self._parse_decimal(self._get_element_text(valores, 'BaseCalculo')) or Decimal('0'),
                    'valor_issqn': self._parse_decimal(self._get_element_text(valores, 'ValorIss')) or Decimal('0'),
                    'valor_credito': self._parse_decimal(self._get_element_text(valores, 'ValorCredito'))
                }
            
            # Extract service details
            item_lista_servico = servico_element.find('.//ItemListaServico') or servico_element.find('.//itemListaServico')
            discriminacao = self._get_element_text(servico_element, 'Discriminacao') or self._get_element_text(servico_element, 'discriminacao')
            codigo_cnae = self._get_element_text(servico_element, 'CodigoCnae') or self._get_element_text(servico_element, 'codigoCnae')
            codigo_tributacao_municipio = self._get_element_text(servico_element, 'CodigoTributacaoMunicipio')
            
            # Create service object
            service = Service(
                codigo_servico=self._get_element_text(item_lista_servico, 'ItemListaServico') if item_lista_servico is not None else "01.01",
                descricao=discriminacao or "Serviço prestado",
                codigo_cnae=codigo_cnae,
                codigo_tributacao_nacional=None,
                codigo_tributacao_municipal=codigo_tributacao_municipio,
                codigo_nbs=self._get_element_text(servico_element, 'CodigoNbs')
            )
            
            # Create ISSQN tax
            issqn_tax = None
            if valores is not None:
                aliquota_str = self._get_element_text(valores, 'Aliquota')
                aliquota = self._parse_decimal(aliquota_str)
                if aliquota:
                    aliquota = aliquota / 100  # Convert percentage to decimal
                
                issqn_tax = ISSQNTax(
                    base_calculo=totals.get('valor_base_calculo', Decimal('0')),
                    aliquota=aliquota or Decimal('0'),
                    valor=totals.get('valor_issqn', Decimal('0')),
                    valor_credito=totals.get('valor_credito')
                )
            
            # Create service item
            nfse_item = NFSEItem(
                servico=service,
                quantidade=Decimal('1'),  # NFS-e typically has quantity 1
                valor_unitario=totals.get('valor_total_servicos', Decimal('0')),
                valor_total=totals.get('valor_total_servicos', Decimal('0')),
                valor_deducoes=totals.get('valor_total_deducoes'),
                issqn_tax=issqn_tax
            )
            
            services.append(nfse_item)
            
        except Exception as e:
            self.logger.error("Error extracting NFS-e services", error=str(e))
            totals = {
                'valor_total_servicos': Decimal('0'),
                'valor_total_deducoes': None,
                'valor_base_calculo': Decimal('0'),
                'valor_issqn': Decimal('0'),
                'valor_credito': None
            }
        
        return services, totals
    
    async def _move_processed_file(self, file_path: str):
        """Move processed file to processed directory"""
        try:
            file_name = os.path.basename(file_path)
            processed_path = os.path.join(settings.XML_PROCESSED_DIRECTORY, file_name)
            os.rename(file_path, processed_path)
            self.logger.info("File moved to processed directory", 
                           original=file_path, processed=processed_path)
        except Exception as e:
            self.logger.error("Error moving processed file", error=str(e))
    
    async def notify_processing_complete(self, data: FiscalDocument):
        """Notify other agents that processing is complete"""
        document_id = getattr(data, 'chave_nfe', None) or getattr(data, 'id_nfse', None)
        
        self.logger.info("XML processing complete", 
                        document_type=data.document_type.value,
                        document_id=document_id,
                        file_path=data.xml_file_path)
        
        # Prepare notification data for other agents
        notification_data = {
            'event': 'xml_processing_complete',
            'document_type': data.document_type.value,
            'document_id': document_id,
            'file_path': data.xml_file_path,
            'processed_at': datetime.now().isoformat(),
            'agent': self.agent_name,
            'data': data,  # Full fiscal data for AI Categorization Agent
            'llm_enhanced': hasattr(data, 'llm_analysis'),
            'semantic_analysis_available': hasattr(data, 'llm_analysis') and 'semantic_analysis' in data.llm_analysis,
            'business_insights_available': hasattr(data, 'llm_analysis') and 'business_insights' in data.llm_analysis
        }
        
        # In a real implementation, this would:
        # 1. Send message to AI Categorization Agent via Redis pub/sub
        # 2. Store data in Data Lake via Data Lake Agent
        # 3. Update processing statistics for Monitoring Agent
        
        try:
            # Simulate Redis pub/sub notification
            self.logger.info("Notification sent to AI Categorization Agent", 
                           document_id=document_id,
                           notification_type="xml_processing_complete")
            
            # Simulate Data Lake storage notification
            self.logger.info("Notification sent to Data Lake Agent", 
                           document_id=document_id,
                           notification_type="store_fiscal_data")
            
            # Update processing statistics
            self.logger.info("Processing statistics updated", 
                           document_type=data.document_type.value,
                           success=True)
            
        except Exception as e:
            self.logger.error("Error sending completion notifications", error=str(e))
    
    async def handle_processing_error(self, error: ProcessingError):
        """Handle processing errors"""
        self.logger.error("XML processing error", 
                         file_path=error.file_path,
                         error_type=error.error_type,
                         error_message=error.error_message)
        
        # Move file to error directory
        try:
            file_name = os.path.basename(error.file_path)
            error_path = os.path.join(settings.XML_ERROR_DIRECTORY, file_name)
            os.rename(error.file_path, error_path)
            self.logger.info("Error file moved", original=error.file_path, error_path=error_path)
        except Exception as e:
            self.logger.error("Error moving failed file", error=str(e))
        
        # Notify Monitoring Agent
        try:
            from .monitoring_agent import MonitoringAgent, SystemAlert, AlertLevel
            
            # Create system alert for the error
            alert = SystemAlert(
                level=AlertLevel.ERROR,
                message=f"XML processing failed: {error.error_message}",
                source=self.agent_name,
                details={
                    'file_path': error.file_path,
                    'error_type': error.error_type,
                    'timestamp': error.timestamp
                }
            )
            
            # In a real implementation, this would be sent via Redis/message queue
            # For now, we'll log the notification
            self.logger.info("Error notification prepared for Monitoring Agent", 
                           alert_id=alert.alert_id,
                           error_type=error.error_type)
            
        except Exception as e:
            self.logger.error("Error notifying Monitoring Agent", error=str(e))
    
    def _get_element_text(self, parent_element, tag_name: str, namespaces: Dict[str, str] = None) -> Optional[str]:
        """Get text content from XML element"""
        if parent_element is None:
            return None
        
        try:
            # Try with namespace first
            if namespaces:
                for prefix, namespace in namespaces.items():
                    element = parent_element.find(f'.//{prefix}:{tag_name}', namespaces)
                    if element is not None and element.text:
                        return element.text.strip()
            
            # Try without namespace
            element = parent_element.find(f'.//{tag_name}')
            if element is not None and element.text:
                return element.text.strip()
            
            # Try direct child
            element = parent_element.find(tag_name)
            if element is not None and element.text:
                return element.text.strip()
            
            return None
            
        except Exception as e:
            self.logger.debug("Error getting element text", tag=tag_name, error=str(e))
            return None
    
    def _parse_decimal(self, value_str: Optional[str]) -> Optional[Decimal]:
        """Parse string to Decimal, handling Brazilian number format"""
        if not value_str:
            return None
        
        try:
            # Clean the string
            cleaned = value_str.strip()
            
            # Handle Brazilian decimal format (comma as decimal separator)
            if ',' in cleaned and '.' in cleaned:
                # Format like 1.234.567,89
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned:
                # Format like 1234,89
                cleaned = cleaned.replace(',', '.')
            
            return Decimal(cleaned)
            
        except (InvalidOperation, ValueError) as e:
            self.logger.debug("Error parsing decimal", value=value_str, error=str(e))
            return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string in various formats"""
        if not datetime_str:
            return None
        
        try:
            # Common Brazilian datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',      # ISO format
                '%Y-%m-%dT%H:%M:%S.%f',   # ISO with microseconds
                '%Y-%m-%dT%H:%M:%S%z',    # ISO with timezone
                '%Y-%m-%d %H:%M:%S',      # Standard format
                '%d/%m/%Y %H:%M:%S',      # Brazilian format
                '%d/%m/%Y',               # Brazilian date only
                '%Y-%m-%d',               # ISO date only
            ]
            
            cleaned = datetime_str.strip()
            
            for fmt in formats:
                try:
                    return datetime.strptime(cleaned, fmt)
                except ValueError:
                    continue
            
            # If no format matches, try to parse with dateutil (if available)
            try:
                from dateutil import parser
                return parser.parse(cleaned)
            except ImportError:
                pass
            
            self.logger.warning("Could not parse datetime", datetime_str=datetime_str)
            return None
            
        except Exception as e:
            self.logger.debug("Error parsing datetime", datetime_str=datetime_str, error=str(e))
            return None
    
    # ===== LLM-ENHANCED SEMANTIC ANALYSIS METHODS =====
    
    async def analyze_document_semantics(
        self, 
        xml_data: Union[NFEData, NFSEData]
    ) -> AnaliseDocumento:
        """
        Use LLM to understand document business context and extract semantic meaning
        Requirements: 2.1, 2.2, 2.3
        """
        try:
            self.logger.info("Starting LLM semantic analysis", 
                           document_type=xml_data.document_type.value)
            
            # Prepare context for LLM analysis
            contexto_analise = await self._preparar_contexto_analise_semantica(xml_data)
            
            # Use OpenAI service for semantic analysis
            analise = await self.openai_service.analisar_documento(
                conteudo_documento=self._extrair_conteudo_documento(xml_data),
                tipo_analise="semantic_analysis",
                contexto=contexto_analise
            )
            
            self.logger.info("LLM semantic analysis completed", 
                           document_id=getattr(xml_data, 'chave_nfe', None) or getattr(xml_data, 'id_nfse', None),
                           confidence_score=analise.score_confianca)
            
            return analise
            
        except Exception as e:
            self.logger.error("Error in LLM semantic analysis", error=str(e))
            # Return fallback analysis
            return AnaliseDocumento(
                tipo_documento=xml_data.document_type.value,
                contexto_empresarial={"erro": "Análise semântica falhou"},
                insights_principais=[f"Erro na análise: {str(e)}"],
                anomalias_detectadas=[],
                score_confianca=0.0,
                recomendacoes=["Revisar documento manualmente"]
            )
    
    async def _preparar_contexto_analise_semantica(
        self, 
        xml_data: Union[NFEData, NFSEData]
    ) -> Dict[str, Any]:
        """Prepare context for LLM semantic analysis"""
        contexto = {
            "tipo_documento": xml_data.document_type.value,
            "info_fornecedor": {
                "cnpj": xml_data.supplier.cnpj if xml_data.supplier else None,
                "razao_social": xml_data.supplier.razao_social if xml_data.supplier else None,
                "uf": xml_data.supplier.address.uf if xml_data.supplier and xml_data.supplier.address else None
            },
            "valor_total": str(getattr(xml_data, 'valor_total_nf', None) or 
                             getattr(xml_data, 'valor_total_servicos', None) or 0),
            "data_emissao": xml_data.data_emissao.strftime("%d/%m/%Y") if xml_data.data_emissao else None
        }
        
        # Add items/services information
        if hasattr(xml_data, 'items') and xml_data.items:
            contexto["itens"] = [
                {
                    "descricao": item.produto.descricao if hasattr(item, 'produto') else "N/A",
                    "ncm": item.produto.ncm if hasattr(item, 'produto') else None,
                    "valor": str(item.valor_total_bruto) if hasattr(item, 'valor_total_bruto') else str(item.valor_total),
                    "quantidade": str(item.quantidade_comercial) if hasattr(item, 'quantidade_comercial') else str(item.quantidade)
                }
                for item in xml_data.items[:10]  # Limit to first 10 items for LLM processing
            ]
        elif hasattr(xml_data, 'services') and xml_data.services:
            contexto["itens"] = [
                {
                    "descricao": service.servico.descricao if hasattr(service, 'servico') else "N/A",
                    "codigo_servico": service.servico.codigo_servico if hasattr(service, 'servico') else None,
                    "valor": str(service.valor_total),
                    "quantidade": str(service.quantidade)
                }
                for service in xml_data.services[:10]  # Limit to first 10 services
            ]
        
        # Add tax information
        if hasattr(xml_data, 'valor_icms') and xml_data.valor_icms:
            contexto["info_tributaria"] = {
                "icms": str(xml_data.valor_icms),
                "base_calculo_icms": str(xml_data.base_calculo_icms) if xml_data.base_calculo_icms else None
            }
        elif hasattr(xml_data, 'valor_issqn') and xml_data.valor_issqn:
            contexto["info_tributaria"] = {
                "issqn": str(xml_data.valor_issqn),
                "base_calculo": str(xml_data.valor_base_calculo) if xml_data.valor_base_calculo else None
            }
        
        # Add business context from historical data (if available)
        contexto["contexto_empresarial"] = await self._obter_contexto_historico_fornecedor(
            xml_data.supplier.cnpj if xml_data.supplier else None
        )
        
        return contexto
    
    def _extrair_conteudo_documento(self, xml_data: Union[NFEData, NFSEData]) -> str:
        """Extract document content for LLM analysis"""
        conteudo = f"Documento Fiscal: {xml_data.document_type.value}\n"
        
        if xml_data.supplier:
            conteudo += f"Fornecedor: {xml_data.supplier.razao_social} (CNPJ: {xml_data.supplier.cnpj})\n"
        
        if hasattr(xml_data, 'recipient') and xml_data.recipient:
            conteudo += f"Cliente: {xml_data.recipient.razao_social}\n"
        
        valor_total = getattr(xml_data, 'valor_total_nf', None) or getattr(xml_data, 'valor_total_servicos', None)
        if valor_total:
            conteudo += f"Valor Total: R$ {valor_total}\n"
        
        conteudo += f"Data de Emissão: {xml_data.data_emissao.strftime('%d/%m/%Y') if xml_data.data_emissao else 'N/A'}\n"
        
        # Add items summary
        if hasattr(xml_data, 'items') and xml_data.items:
            conteudo += f"\nProdutos ({len(xml_data.items)} itens):\n"
            for i, item in enumerate(xml_data.items[:5], 1):  # Show first 5 items
                if hasattr(item, 'produto'):
                    conteudo += f"{i}. {item.produto.descricao} - R$ {item.valor_total_bruto}\n"
        elif hasattr(xml_data, 'services') and xml_data.services:
            conteudo += f"\nServiços ({len(xml_data.services)} itens):\n"
            for i, service in enumerate(xml_data.services[:5], 1):  # Show first 5 services
                if hasattr(service, 'servico'):
                    conteudo += f"{i}. {service.servico.descricao} - R$ {service.valor_total}\n"
        
        return conteudo
    
    async def _obter_contexto_historico_fornecedor(self, cnpj: Optional[str]) -> Dict[str, Any]:
        """Get historical context for supplier (placeholder for future database integration)"""
        if not cnpj:
            return {}
        
        # Placeholder for historical data retrieval
        # In a real implementation, this would query the database for:
        # - Previous transactions with this supplier
        # - Supplier category and relationship type
        # - Average transaction values
        # - Seasonal patterns
        
        return {
            "historico_disponivel": False,
            "primeira_transacao": True,
            "categoria_fornecedor": "A definir",
            "relacionamento": "Novo"
        }
    
    async def extract_business_insights(
        self, 
        xml_data: Union[NFEData, NFSEData],
        semantic_analysis: AnaliseDocumento
    ) -> Dict[str, Any]:
        """
        Generate business insights from fiscal document using LLM analysis
        Requirements: 2.4, 2.5
        """
        try:
            self.logger.info("Generating business insights from document analysis")
            
            # Prepare context for business insights generation
            contexto_insights = {
                "documento_fiscal": self._extrair_conteudo_documento(xml_data),
                "analise_semantica": {
                    "contexto_empresarial": semantic_analysis.contexto_empresarial,
                    "insights_principais": semantic_analysis.insights_principais,
                    "anomalias": semantic_analysis.anomalias_detectadas
                },
                "contexto_mercado": await self._obter_contexto_mercado(),
                "padroes_historicos": await self._obter_padroes_historicos(xml_data)
            }
            
            # Generate insights using OpenAI service
            insights = await self.openai_service.gerar_insights(
                dados=contexto_insights,
                tipo_insight="fiscal_document_analysis",
                audiencia="executivo"
            )
            
            # Structure business insights for executive reporting
            business_insights = {
                "descobertas_principais": insights.descobertas_principais,
                "tendencias_identificadas": insights.tendencias_identificadas,
                "impacto_empresarial": insights.impacto_empresarial,
                "implicacoes_estrategicas": insights.implicacoes_estrategicas,
                "nivel_confianca": insights.nivel_confianca,
                "recomendacoes_acao": self._gerar_recomendacoes_acao(insights, xml_data),
                "alertas_executivos": self._identificar_alertas_executivos(insights, xml_data)
            }
            
            self.logger.info("Business insights generated successfully", 
                           insights_count=len(business_insights["descobertas_principais"]),
                           confidence_level=business_insights["nivel_confianca"])
            
            return business_insights
            
        except Exception as e:
            self.logger.error("Error generating business insights", error=str(e))
            return {
                "descobertas_principais": [f"Erro na geração de insights: {str(e)}"],
                "tendencias_identificadas": [],
                "impacto_empresarial": {},
                "implicacoes_estrategicas": [],
                "nivel_confianca": 0.0,
                "recomendacoes_acao": ["Revisar análise manualmente"],
                "alertas_executivos": ["Falha na análise automática"]
            }
    
    async def _obter_contexto_mercado(self) -> Dict[str, Any]:
        """Get market context for analysis with enhanced business intelligence"""
        try:
            # Get current economic indicators for Brazil
            contexto_economico = await self._obter_indicadores_economicos()
            
            # Get industry benchmarks
            benchmarks_industria = await self._obter_benchmarks_industria()
            
            # Get seasonal patterns
            padroes_sazonais = await self._obter_padroes_sazonais()
            
            return {
                "contexto_economico": contexto_economico,
                "indicadores_setor": {
                    "inflacao_mensal": "Dados IPCA não disponíveis",
                    "pib_crescimento": "Dados PIB não disponíveis",
                    "taxa_juros": "Taxa Selic não disponível"
                },
                "benchmarks_industria": benchmarks_industria,
                "sazonalidade": padroes_sazonais,
                "tendencias_mercado": await self._identificar_tendencias_mercado()
            }
        except Exception as e:
            self.logger.warning("Error getting market context", error=str(e))
            return {
                "contexto_economico": "Erro ao obter dados econômicos",
                "indicadores_setor": {},
                "benchmarks_industria": {},
                "sazonalidade": "Dados sazonais não disponíveis",
                "erro": str(e)
            }
    
    async def _obter_indicadores_economicos(self) -> Dict[str, Any]:
        """Get Brazilian economic indicators"""
        # Placeholder for economic data integration
        # In production, this would integrate with:
        # - IBGE APIs for inflation data
        # - Central Bank APIs for interest rates
        # - Government economic data sources
        
        return {
            "periodo_referencia": datetime.now().strftime("%m/%Y"),
            "indicadores_disponiveis": False,
            "fonte": "Integração futura com APIs governamentais",
            "observacao": "Dados econômicos serão integrados em versão futura"
        }
    
    async def _obter_benchmarks_industria(self) -> Dict[str, Any]:
        """Get industry benchmarks for comparison"""
        # Placeholder for industry benchmark data
        # In production, this would analyze:
        # - Average transaction values by industry
        # - Common supplier patterns
        # - Typical product categories
        # - Regional variations
        
        return {
            "benchmarks_disponiveis": False,
            "valor_medio_transacao": "A definir",
            "fornecedores_comuns": [],
            "categorias_principais": [],
            "observacao": "Benchmarks serão calculados com base em dados históricos"
        }
    
    async def _obter_padroes_sazonais(self) -> Dict[str, Any]:
        """Get seasonal patterns for business analysis"""
        mes_atual = datetime.now().month
        
        # Basic seasonal patterns for Brazilian business
        padroes_conhecidos = {
            12: {"periodo": "Dezembro", "caracteristica": "Alto volume de vendas - fim de ano"},
            1: {"periodo": "Janeiro", "caracteristica": "Baixo volume - férias e planejamento"},
            2: {"periodo": "Fevereiro", "caracteristica": "Retomada gradual das atividades"},
            3: {"periodo": "Março", "caracteristica": "Normalização das operações"},
            6: {"periodo": "Junho", "caracteristica": "Meio do ano - avaliações semestrais"},
            7: {"periodo": "Julho", "caracteristica": "Férias escolares - variação por setor"},
            11: {"periodo": "Novembro", "caracteristica": "Preparação para Black Friday e fim de ano"}
        }
        
        padrao_atual = padroes_conhecidos.get(mes_atual, {
            "periodo": f"Mês {mes_atual}",
            "caracteristica": "Padrão sazonal padrão"
        })
        
        return {
            "mes_atual": mes_atual,
            "padrao_atual": padrao_atual,
            "tendencia_sazonal": "Análise baseada em padrões gerais do mercado brasileiro",
            "recomendacao": "Considerar sazonalidade na análise de volumes e valores"
        }
    
    async def _identificar_tendencias_mercado(self) -> List[str]:
        """Identify current market trends"""
        # Placeholder for market trend analysis
        # In production, this would analyze:
        # - Recent transaction patterns
        # - Emerging product categories
        # - New supplier relationships
        # - Regional market changes
        
        return [
            "Digitalização crescente dos processos fiscais",
            "Aumento da demanda por transparência tributária",
            "Crescimento do e-commerce e NFC-e",
            "Maior foco em sustentabilidade e ESG",
            "Automação de processos contábeis"
        ]
    
    async def _obter_padroes_historicos(self, xml_data: Union[NFEData, NFSEData]) -> Dict[str, Any]:
        """Get historical patterns for comparison with enhanced analysis"""
        try:
            # Analyze supplier patterns
            padroes_fornecedor = await self._analisar_padroes_fornecedor(xml_data.supplier)
            
            # Analyze product/service patterns
            if hasattr(xml_data, 'items') and xml_data.items:
                padroes_produtos = await self._analisar_padroes_produtos(xml_data.items)
            elif hasattr(xml_data, 'services') and xml_data.services:
                padroes_produtos = await self._analisar_padroes_servicos(xml_data.services)
            else:
                padroes_produtos = {}
            
            # Analyze value patterns
            padroes_valor = await self._analisar_padroes_valor(xml_data)
            
            # Analyze temporal patterns
            padroes_temporais = await self._analisar_padroes_temporais(xml_data.data_emissao)
            
            return {
                "padroes_fornecedor": padroes_fornecedor,
                "padroes_produtos_servicos": padroes_produtos,
                "padroes_valor": padroes_valor,
                "padroes_temporais": padroes_temporais,
                "score_confiabilidade": self._calcular_score_confiabilidade_historica(),
                "recomendacoes_analise": self._gerar_recomendacoes_analise_historica()
            }
        except Exception as e:
            self.logger.warning("Error analyzing historical patterns", error=str(e))
            return {
                "padroes_fornecedor": {},
                "padroes_produtos_servicos": {},
                "padroes_valor": {},
                "padroes_temporais": {},
                "erro": str(e),
                "observacao": "Análise histórica limitada devido a erro"
            }
    
    async def _analisar_padroes_fornecedor(self, supplier: Optional[Supplier]) -> Dict[str, Any]:
        """Analyze supplier patterns"""
        if not supplier:
            return {"fornecedor_disponivel": False}
        
        # Basic supplier analysis
        analise = {
            "cnpj_disponivel": bool(supplier.cnpj),
            "razao_social_disponivel": bool(supplier.razao_social),
            "endereco_completo": bool(supplier.address and supplier.address.uf),
            "tipo_pessoa": "juridica" if supplier.cnpj else "fisica" if supplier.cpf else "indefinido"
        }
        
        # Add regional analysis
        if supplier.address and supplier.address.uf:
            analise["regiao"] = self._identificar_regiao_brasil(supplier.address.uf)
            analise["caracteristicas_regionais"] = self._obter_caracteristicas_regionais(supplier.address.uf)
        
        return analise
    
    async def _analisar_padroes_produtos(self, items: List[NFEItem]) -> Dict[str, Any]:
        """Analyze product patterns"""
        if not items:
            return {"produtos_disponivel": False}
        
        # Analyze product characteristics
        total_items = len(items)
        valor_total = sum(item.valor_total_bruto for item in items if item.valor_total_bruto)
        valor_medio = valor_total / total_items if total_items > 0 else 0
        
        # Analyze NCM patterns
        ncms = [item.produto.ncm for item in items if item.produto and item.produto.ncm]
        ncms_unicos = len(set(ncms))
        
        # Analyze product categories
        categorias = await self._classificar_produtos_por_categoria(items)
        
        return {
            "total_itens": total_items,
            "valor_total": float(valor_total),
            "valor_medio_item": float(valor_medio),
            "ncms_diferentes": ncms_unicos,
            "diversidade_produtos": ncms_unicos / max(total_items, 1),
            "categorias_identificadas": categorias,
            "complexidade_transacao": self._avaliar_complexidade_transacao(items)
        }
    
    async def _analisar_padroes_servicos(self, services: List[NFSEItem]) -> Dict[str, Any]:
        """Analyze service patterns"""
        if not services:
            return {"servicos_disponivel": False}
        
        total_services = len(services)
        valor_total = sum(service.valor_total for service in services if service.valor_total)
        valor_medio = valor_total / total_services if total_services > 0 else 0
        
        # Analyze service codes
        codigos_servico = [service.servico.codigo_servico for service in services if service.servico]
        codigos_unicos = len(set(codigos_servico))
        
        return {
            "total_servicos": total_services,
            "valor_total": float(valor_total),
            "valor_medio_servico": float(valor_medio),
            "codigos_diferentes": codigos_unicos,
            "diversidade_servicos": codigos_unicos / max(total_services, 1),
            "tipo_prestacao": "simples" if total_services == 1 else "multipla"
        }
    
    async def _analisar_padroes_valor(self, xml_data: Union[NFEData, NFSEData]) -> Dict[str, Any]:
        """Analyze value patterns"""
        valor_total = getattr(xml_data, 'valor_total_nf', None) or getattr(xml_data, 'valor_total_servicos', None)
        
        if not valor_total:
            return {"valor_disponivel": False}
        
        # Classify transaction by value
        classificacao_valor = self._classificar_transacao_por_valor(float(valor_total))
        
        # Analyze tax patterns
        padroes_tributos = {}
        if hasattr(xml_data, 'valor_icms') and xml_data.valor_icms:
            padroes_tributos["icms"] = {
                "valor": float(xml_data.valor_icms),
                "percentual": float(xml_data.valor_icms / valor_total * 100) if valor_total > 0 else 0
            }
        
        if hasattr(xml_data, 'valor_issqn') and xml_data.valor_issqn:
            padroes_tributos["issqn"] = {
                "valor": float(xml_data.valor_issqn),
                "percentual": float(xml_data.valor_issqn / valor_total * 100) if valor_total > 0 else 0
            }
        
        return {
            "valor_total": float(valor_total),
            "classificacao": classificacao_valor,
            "padroes_tributarios": padroes_tributos,
            "impacto_financeiro": self._avaliar_impacto_financeiro(float(valor_total))
        }
    
    async def _analisar_padroes_temporais(self, data_emissao: Optional[datetime]) -> Dict[str, Any]:
        """Analyze temporal patterns"""
        if not data_emissao:
            return {"data_disponivel": False}
        
        agora = datetime.now()
        diferenca_dias = (agora - data_emissao).days
        
        return {
            "data_emissao": data_emissao.strftime("%d/%m/%Y"),
            "dias_desde_emissao": diferenca_dias,
            "mes_emissao": data_emissao.month,
            "trimestre": (data_emissao.month - 1) // 3 + 1,
            "dia_semana": data_emissao.weekday(),
            "periodo_dia": self._classificar_periodo_dia(data_emissao.hour) if data_emissao.hour else "indefinido",
            "sazonalidade": self._identificar_sazonalidade(data_emissao.month),
            "urgencia": "alta" if diferenca_dias > 30 else "normal"
        }
    
    def _identificar_regiao_brasil(self, uf: str) -> str:
        """Identify Brazilian region by state"""
        regioes = {
            "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
            "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
            "Centro-Oeste": ["DF", "GO", "MT", "MS"],
            "Sudeste": ["ES", "MG", "RJ", "SP"],
            "Sul": ["PR", "RS", "SC"]
        }
        
        for regiao, estados in regioes.items():
            if uf in estados:
                return regiao
        return "Indefinida"
    
    def _obter_caracteristicas_regionais(self, uf: str) -> Dict[str, str]:
        """Get regional characteristics"""
        caracteristicas = {
            "SP": {"economia": "Industrial/Serviços", "caracteristica": "Maior PIB do país"},
            "RJ": {"economia": "Serviços/Petróleo", "caracteristica": "Centro financeiro"},
            "MG": {"economia": "Mineração/Agropecuária", "caracteristica": "Diversificada"},
            "RS": {"economia": "Agropecuária/Industrial", "caracteristica": "Forte agronegócio"},
            "PR": {"economia": "Agropecuária/Industrial", "caracteristica": "Cooperativismo forte"}
        }
        
        return caracteristicas.get(uf, {"economia": "Diversificada", "caracteristica": "Economia regional"})
    
    async def _classificar_produtos_por_categoria(self, items: List[NFEItem]) -> List[str]:
        """Classify products by category"""
        categorias = set()
        
        for item in items:
            if item.produto and item.produto.descricao:
                # Simple categorization based on product description
                descricao = item.produto.descricao.lower()
                
                if any(palavra in descricao for palavra in ["materia", "prima", "insumo"]):
                    categorias.add("Matéria Prima")
                elif any(palavra in descricao for palavra in ["produto", "acabado", "final"]):
                    categorias.add("Produto Acabado")
                elif any(palavra in descricao for palavra in ["mercadoria", "revenda"]):
                    categorias.add("Mercadoria para Revenda")
                elif any(palavra in descricao for palavra in ["equipamento", "maquina", "ativo"]):
                    categorias.add("Ativo Imobilizado")
                else:
                    categorias.add("Outros")
        
        return list(categorias)
    
    def _avaliar_complexidade_transacao(self, items: List[NFEItem]) -> str:
        """Evaluate transaction complexity"""
        if len(items) == 1:
            return "simples"
        elif len(items) <= 5:
            return "media"
        elif len(items) <= 20:
            return "complexa"
        else:
            return "muito_complexa"
    
    def _classificar_transacao_por_valor(self, valor: float) -> str:
        """Classify transaction by value"""
        if valor < 100:
            return "muito_baixo"
        elif valor < 1000:
            return "baixo"
        elif valor < 10000:
            return "medio"
        elif valor < 100000:
            return "alto"
        else:
            return "muito_alto"
    
    def _avaliar_impacto_financeiro(self, valor: float) -> str:
        """Evaluate financial impact"""
        if valor < 1000:
            return "baixo"
        elif valor < 50000:
            return "medio"
        else:
            return "alto"
    
    def _classificar_periodo_dia(self, hora: int) -> str:
        """Classify time period of day"""
        if 6 <= hora < 12:
            return "manha"
        elif 12 <= hora < 18:
            return "tarde"
        elif 18 <= hora < 24:
            return "noite"
        else:
            return "madrugada"
    
    def _identificar_sazonalidade(self, mes: int) -> str:
        """Identify seasonality"""
        if mes in [12, 1, 2]:
            return "verao_ferias"
        elif mes in [3, 4, 5]:
            return "outono_retomada"
        elif mes in [6, 7, 8]:
            return "inverno_meio_ano"
        else:
            return "primavera_preparacao"
    
    def _calcular_score_confiabilidade_historica(self) -> float:
        """Calculate historical reliability score"""
        # Placeholder for historical data reliability calculation
        # In production, this would be based on:
        # - Amount of historical data available
        # - Data quality and consistency
        # - Recency of data
        return 0.5  # Medium confidence due to limited historical data
    
    def _gerar_recomendacoes_analise_historica(self) -> List[str]:
        """Generate recommendations for historical analysis"""
        return [
            "Coletar mais dados históricos para melhorar análise de padrões",
            "Implementar sistema de categorização automática de fornecedores",
            "Desenvolver benchmarks específicos por setor de atuação",
            "Criar alertas para desvios significativos de padrões históricos"
        ]
    
    def _gerar_recomendacoes_acao(
        self, 
        insights, 
        xml_data: Union[NFEData, NFSEData]
    ) -> List[str]:
        """Generate actionable recommendations based on insights"""
        recomendacoes = []
        
        # Add recommendations based on document value
        valor_total = getattr(xml_data, 'valor_total_nf', None) or getattr(xml_data, 'valor_total_servicos', None)
        if valor_total and valor_total > 50000:  # High-value transactions
            recomendacoes.append("Transação de alto valor - considerar aprovação executiva adicional")
        
        # Add recommendations based on supplier
        if xml_data.supplier and not xml_data.supplier.cnpj:
            recomendacoes.append("Fornecedor sem CNPJ - verificar regularidade fiscal")
        
        # Add recommendations based on insights confidence
        if insights.nivel_confianca < 0.7:
            recomendacoes.append("Baixa confiança na análise - revisar documento manualmente")
        
        return recomendacoes
    
    def _identificar_alertas_executivos(
        self, 
        insights, 
        xml_data: Union[NFEData, NFSEData]
    ) -> List[str]:
        """Identify executive-level alerts"""
        alertas = []
        
        # Check for high-impact issues
        if "anomalia" in str(insights.descobertas_principais).lower():
            alertas.append("Anomalias detectadas no documento fiscal")
        
        # Check for compliance issues
        if hasattr(xml_data, 'valor_icms') and xml_data.valor_icms and xml_data.valor_icms == 0:
            valor_total = getattr(xml_data, 'valor_total_nf', 0)
            if valor_total > 10000:  # High value with zero ICMS might be suspicious
                alertas.append("Transação de alto valor com ICMS zero - verificar enquadramento tributário")
        
        return alertas
    
    async def validate_with_context(
        self, 
        xml_data: Union[NFEData, NFSEData]
    ) -> Dict[str, Any]:
        """
        Intelligent document validation beyond schema checking using LLM
        Requirements: 2.3, 2.4
        """
        try:
            self.logger.info("Starting contextual validation", 
                           document_type=xml_data.document_type.value)
            
            # Perform semantic analysis first
            semantic_analysis = await self.analyze_document_semantics(xml_data)
            
            # Perform advanced anomaly detection
            anomaly_results = await self.detect_anomalies_with_business_impact(xml_data, semantic_analysis)
            
            # Prepare validation context
            contexto_validacao = {
                "documento": self._extrair_conteudo_documento(xml_data),
                "analise_semantica": semantic_analysis.contexto_empresarial,
                "regras_negocio": await self._obter_regras_negocio(),
                "dados_historicos": await self._obter_contexto_validacao(xml_data),
                "padroes_anomalia": await self._obter_padroes_anomalia(),
                "anomalias_detectadas": anomaly_results
            }
            
            # Use LLM for intelligent validation
            prompt_validacao = self._obter_prompt_validacao_contextual()
            resposta_validacao = await self.openai_service.gerar_completion(
                prompt=prompt_validacao,
                contexto=contexto_validacao,
                tipo_prompt=None  # Custom validation prompt
            )
            
            # Process validation results
            resultado_validacao = self._processar_resultado_validacao(
                resposta_validacao, xml_data, semantic_analysis
            )
            
            # Integrate anomaly detection results
            resultado_validacao["deteccao_anomalias"] = anomaly_results
            resultado_validacao["score_anomalia"] = anomaly_results.get("score_anomalia", 0.0)
            resultado_validacao["nivel_risco_anomalia"] = anomaly_results.get("nivel_risco", "indefinido")
            
            # Adjust overall validation score based on anomalies
            if anomaly_results.get("score_anomalia", 0) > 0.5:
                resultado_validacao["score_validacao"] = min(
                    resultado_validacao.get("score_validacao", 1.0),
                    1.0 - anomaly_results["score_anomalia"]
                )
            
            self.logger.info("Contextual validation completed", 
                           validation_score=resultado_validacao.get("score_validacao", 0),
                           issues_found=len(resultado_validacao.get("problemas_identificados", [])))
            
            return resultado_validacao
            
        except Exception as e:
            self.logger.error("Error in contextual validation", error=str(e))
            return {
                "valido": False,
                "score_validacao": 0.0,
                "problemas_identificados": [f"Erro na validação: {str(e)}"],
                "recomendacoes": ["Validar documento manualmente"],
                "impacto_empresarial": "Alto - validação falhou"
            }
    
    async def _obter_regras_negocio(self) -> Dict[str, Any]:
        """Get comprehensive business rules for validation"""
        return {
            # Regras de valor
            "regras_valor": {
                "valor_minimo_nfe": 0.01,
                "valor_maximo_sem_aprovacao": 100000.00,
                "valor_maximo_nfse": 1000000.00,
                "diferenca_maxima_percentual": 10.0  # % de diferença aceitável entre valores
            },
            
            # Regras de fornecedores
            "regras_fornecedor": {
                "cnpj_obrigatorio_acima": 1000.00,  # Valor acima do qual CNPJ é obrigatório
                "fornecedores_bloqueados": [],
                "fornecedores_preferidos": [],
                "validar_inscricao_estadual": True,
                "verificar_situacao_receita": True
            },
            
            # Regras tributárias
            "regras_tributarias": {
                "icms": {
                    "aliquota_minima": 0.0,
                    "aliquota_maxima": 25.0,
                    "obrigatorio_acima": 100.00
                },
                "issqn": {
                    "aliquota_minima": 2.0,
                    "aliquota_maxima": 5.0,
                    "base_calculo_minima": 0.01
                },
                "ipi": {
                    "aliquota_maxima": 50.0,
                    "produtos_obrigatorios": []
                }
            },
            
            # Regras de produtos/serviços
            "regras_produtos": {
                "descricao_minima_caracteres": 10,
                "ncm_obrigatorio": True,
                "produtos_controlados": [
                    "medicamentos", "armas", "explosivos", "combustiveis"
                ],
                "valor_unitario_maximo": 1000000.00
            },
            
            # Regras temporais
            "regras_temporais": {
                "data_maxima_retroativa_dias": 30,
                "data_maxima_futura_dias": 5,
                "horario_comercial_inicio": 6,
                "horario_comercial_fim": 22
            },
            
            # Regras de compliance
            "regras_compliance": {
                "validar_cpf_cnpj": True,
                "verificar_ie_ativa": True,
                "validar_cep": True,
                "verificar_codigo_municipio": True
            },
            
            # Limites de alerta
            "limites_alerta": {
                "valor_alto": 50000.00,
                "quantidade_itens_alta": 50,
                "desconto_percentual_alto": 20.0,
                "margem_lucro_baixa": 5.0
            }
        }
    
    async def _obter_contexto_validacao(self, xml_data: Union[NFEData, NFSEData]) -> Dict[str, Any]:
        """Get validation context for the document"""
        return {
            "historico_fornecedor": await self._obter_contexto_historico_fornecedor(
                xml_data.supplier.cnpj if xml_data.supplier else None
            ),
            "padroes_transacao": {},
            "alertas_anteriores": []
        }
    
    async def _obter_padroes_anomalia(self) -> Dict[str, Any]:
        """Get comprehensive anomaly patterns for detection"""
        return {
            # Anomalias de valor
            "anomalias_valor": [
                {
                    "tipo": "valor_zerado",
                    "descricao": "Produtos com valor unitário zero ou muito baixo",
                    "severidade": "media",
                    "criterio": "valor_unitario < 0.01"
                },
                {
                    "tipo": "valor_desproporcional",
                    "descricao": "Valores muito altos ou baixos comparados ao histórico",
                    "severidade": "alta",
                    "criterio": "desvio > 300% da média histórica"
                },
                {
                    "tipo": "desconto_excessivo",
                    "descricao": "Descontos superiores a 50% do valor original",
                    "severidade": "alta",
                    "criterio": "desconto_percentual > 50%"
                }
            ],
            
            # Anomalias de fornecedor
            "anomalias_fornecedor": [
                {
                    "tipo": "fornecedor_novo_alto_valor",
                    "descricao": "Fornecedor novo com transação de alto valor",
                    "severidade": "media",
                    "criterio": "primeiro_fornecedor AND valor > 10000"
                },
                {
                    "tipo": "cnpj_invalido",
                    "descricao": "CNPJ com formato inválido ou inexistente",
                    "severidade": "critica",
                    "criterio": "cnpj_formato_invalido OR cnpj_inexistente"
                },
                {
                    "tipo": "endereco_incompleto",
                    "descricao": "Endereço do fornecedor incompleto ou suspeito",
                    "severidade": "baixa",
                    "criterio": "endereco_incompleto OR cep_invalido"
                }
            ],
            
            # Anomalias de produtos
            "anomalias_produtos": [
                {
                    "tipo": "descricao_generica",
                    "descricao": "Produtos com descrições muito genéricas em alto valor",
                    "severidade": "media",
                    "criterio": "descricao_generica AND valor_item > 1000"
                },
                {
                    "tipo": "ncm_inconsistente",
                    "descricao": "NCM não condizente com descrição do produto",
                    "severidade": "media",
                    "criterio": "ncm_descricao_incompativel"
                },
                {
                    "tipo": "quantidade_suspeita",
                    "descricao": "Quantidades muito altas ou decimais suspeitas",
                    "severidade": "baixa",
                    "criterio": "quantidade > 10000 OR quantidade_decimal_suspeita"
                }
            ],
            
            # Anomalias tributárias
            "anomalias_tributarias": [
                {
                    "tipo": "icms_zerado_suspeito",
                    "descricao": "ICMS zerado em operações que deveriam ter tributação",
                    "severidade": "alta",
                    "criterio": "icms = 0 AND operacao_tributada"
                },
                {
                    "tipo": "aliquota_fora_padrao",
                    "descricao": "Alíquotas tributárias fora dos padrões normais",
                    "severidade": "media",
                    "criterio": "aliquota < minima OR aliquota > maxima"
                },
                {
                    "tipo": "base_calculo_inconsistente",
                    "descricao": "Base de cálculo inconsistente com valor da operação",
                    "severidade": "alta",
                    "criterio": "base_calculo > valor_operacao"
                }
            ],
            
            # Anomalias temporais
            "anomalias_temporais": [
                {
                    "tipo": "data_retroativa_excessiva",
                    "descricao": "Data de emissão muito anterior à data atual",
                    "severidade": "media",
                    "criterio": "dias_retroativos > 30"
                },
                {
                    "tipo": "horario_suspeito",
                    "descricao": "Emissão em horários não comerciais",
                    "severidade": "baixa",
                    "criterio": "hora < 6 OR hora > 22"
                },
                {
                    "tipo": "data_futura",
                    "descricao": "Data de emissão no futuro",
                    "severidade": "critica",
                    "criterio": "data_emissao > data_atual"
                }
            ],
            
            # Padrões comportamentais
            "padroes_comportamentais": [
                {
                    "tipo": "volume_atipico",
                    "descricao": "Volume de transações muito acima do padrão",
                    "severidade": "media",
                    "criterio": "volume_diario > 5x_media_historica"
                },
                {
                    "tipo": "padrao_repetitivo_suspeito",
                    "descricao": "Padrão muito repetitivo que pode indicar automação",
                    "severidade": "baixa",
                    "criterio": "transacoes_identicas > 10"
                }
            ],
            
            # Configurações de detecção
            "configuracao_deteccao": {
                "sensibilidade": "media",  # baixa, media, alta
                "score_minimo_alerta": 0.6,
                "combinar_anomalias": True,
                "considerar_contexto_historico": True,
                "ajustar_por_setor": True
            }
        }
    
    def _obter_prompt_validacao_contextual(self) -> str:
        """Get prompt for contextual validation"""
        return """Você é um especialista em validação de documentos fiscais brasileiros com foco em compliance e detecção de anomalias.

DOCUMENTO PARA VALIDAÇÃO:
{documento}

CONTEXTO DE ANÁLISE:
Análise Semântica: {analise_semantica}
Regras de Negócio: {regras_negocio}
Dados Históricos: {dados_historicos}
Padrões de Anomalia Conhecidos: {padroes_anomalia}

INSTRUÇÕES:
1. Valide o documento além da conformidade de schema
2. Identifique inconsistências de negócio
3. Detecte padrões anômalos ou suspeitos
4. Avalie impacto empresarial de problemas encontrados
5. Gere recomendações específicas

FORMATO DE RESPOSTA (JSON):
{{
    "valido": true/false,
    "score_validacao": 0.0-1.0,
    "problemas_identificados": [
        {{
            "tipo": "tipo do problema",
            "descricao": "descrição detalhada",
            "severidade": "baixa|media|alta|critica",
            "impacto_empresarial": "impacto nos negócios",
            "recomendacao": "ação recomendada"
        }}
    ],
    "validacoes_aprovadas": [
        "validação 1 que passou",
        "validação 2 que passou"
    ],
    "alertas_compliance": [
        "alerta 1 de compliance",
        "alerta 2 de compliance"
    ],
    "recomendacoes_melhoria": [
        "recomendação 1 para melhoria",
        "recomendação 2 para otimização"
    ],
    "score_confianca": 0.0-1.0,
    "proximos_passos": [
        "próximo passo 1",
        "próximo passo 2"
    ]
}}

DIRETRIZES:
- Foque em riscos empresariais e compliance
- Considere regulamentações fiscais brasileiras
- Priorize problemas com maior impacto financeiro
- Seja específico nas recomendações
- Considere contexto histórico quando disponível"""
    
    def _processar_resultado_validacao(
        self, 
        resposta_llm, 
        xml_data: Union[NFEData, NFSEData], 
        semantic_analysis: AnaliseDocumento
    ) -> Dict[str, Any]:
        """Process LLM validation results"""
        try:
            if resposta_llm.status.value == "sucesso":
                resultado = json.loads(resposta_llm.conteudo)
                
                # Add additional context
                resultado["documento_id"] = (
                    getattr(xml_data, 'chave_nfe', None) or 
                    getattr(xml_data, 'id_nfse', None)
                )
                resultado["tipo_documento"] = xml_data.document_type.value
                resultado["timestamp_validacao"] = datetime.now().isoformat()
                resultado["analise_semantica_score"] = semantic_analysis.score_confianca
                
                return resultado
            else:
                return {
                    "valido": False,
                    "score_validacao": 0.0,
                    "problemas_identificados": [
                        {
                            "tipo": "erro_sistema",
                            "descricao": f"Falha na validação LLM: {resposta_llm.conteudo}",
                            "severidade": "alta",
                            "impacto_empresarial": "Validação não confiável",
                            "recomendacao": "Validar manualmente"
                        }
                    ],
                    "recomendacoes": ["Revisar documento manualmente"],
                    "score_confianca": 0.0
                }
        except json.JSONDecodeError:
            return {
                "valido": False,
                "score_validacao": 0.0,
                "problemas_identificados": [
                    {
                        "tipo": "erro_processamento",
                        "descricao": "Erro ao processar resposta da validação",
                        "severidade": "media",
                        "impacto_empresarial": "Validação incompleta",
                        "recomendacao": "Repetir validação"
                    }
                ],
                "recomendacoes": ["Repetir processo de validação"],
                "score_confianca": 0.0
            }
    
    async def detect_anomalies_with_business_impact(
        self, 
        xml_data: Union[NFEData, NFSEData],
        semantic_analysis: AnaliseDocumento
    ) -> Dict[str, Any]:
        """
        Advanced anomaly detection with business impact assessment
        Requirements: 2.3, 2.4
        """
        try:
            self.logger.info("Starting advanced anomaly detection")
            
            # Get anomaly patterns
            padroes_anomalia = await self._obter_padroes_anomalia()
            
            # Detect different types of anomalies
            anomalias_detectadas = []
            
            # Value anomalies
            anomalias_valor = await self._detectar_anomalias_valor(xml_data, padroes_anomalia["anomalias_valor"])
            anomalias_detectadas.extend(anomalias_valor)
            
            # Supplier anomalies
            anomalias_fornecedor = await self._detectar_anomalias_fornecedor(xml_data, padroes_anomalia["anomalias_fornecedor"])
            anomalias_detectadas.extend(anomalias_fornecedor)
            
            # Product anomalies
            if hasattr(xml_data, 'items') and xml_data.items:
                anomalias_produtos = await self._detectar_anomalias_produtos(xml_data.items, padroes_anomalia["anomalias_produtos"])
                anomalias_detectadas.extend(anomalias_produtos)
            
            # Tax anomalies
            anomalias_tributarias = await self._detectar_anomalias_tributarias(xml_data, padroes_anomalia["anomalias_tributarias"])
            anomalias_detectadas.extend(anomalias_tributarias)
            
            # Temporal anomalies
            anomalias_temporais = await self._detectar_anomalias_temporais(xml_data, padroes_anomalia["anomalias_temporais"])
            anomalias_detectadas.extend(anomalias_temporais)
            
            # Calculate overall anomaly score
            score_anomalia = self._calcular_score_anomalia(anomalias_detectadas)
            
            # Assess business impact
            impacto_empresarial = await self._avaliar_impacto_empresarial_anomalias(anomalias_detectadas, xml_data)
            
            # Generate recommendations
            recomendacoes = self._gerar_recomendacoes_anomalias(anomalias_detectadas, score_anomalia)
            
            resultado = {
                "anomalias_detectadas": anomalias_detectadas,
                "total_anomalias": len(anomalias_detectadas),
                "score_anomalia": score_anomalia,
                "nivel_risco": self._classificar_nivel_risco(score_anomalia),
                "impacto_empresarial": impacto_empresarial,
                "recomendacoes": recomendacoes,
                "requer_atencao_executiva": score_anomalia > 0.7,
                "timestamp_deteccao": datetime.now().isoformat()
            }
            
            self.logger.info("Anomaly detection completed", 
                           anomalies_found=len(anomalias_detectadas),
                           risk_level=resultado["nivel_risco"],
                           anomaly_score=score_anomalia)
            
            return resultado
            
        except Exception as e:
            self.logger.error("Error in anomaly detection", error=str(e))
            return {
                "anomalias_detectadas": [],
                "total_anomalias": 0,
                "score_anomalia": 0.0,
                "nivel_risco": "indefinido",
                "impacto_empresarial": {"erro": str(e)},
                "recomendacoes": ["Executar detecção de anomalias manualmente"],
                "requer_atencao_executiva": True,
                "erro": str(e)
            }
    
    async def _detectar_anomalias_valor(self, xml_data: Union[NFEData, NFSEData], padroes: List[Dict]) -> List[Dict]:
        """Detect value-related anomalies"""
        anomalias = []
        valor_total = getattr(xml_data, 'valor_total_nf', None) or getattr(xml_data, 'valor_total_servicos', None)
        
        if not valor_total:
            return anomalias
        
        # Check for zero or very low values
        if valor_total < 0.01:
            anomalias.append({
                "tipo": "valor_zerado",
                "descricao": f"Valor total muito baixo: R$ {valor_total}",
                "severidade": "alta",
                "valor_detectado": float(valor_total),
                "impacto": "Possível erro de digitação ou fraude"
            })
        
        # Check for extremely high values
        if valor_total > 1000000:  # 1 million
            anomalias.append({
                "tipo": "valor_muito_alto",
                "descricao": f"Valor total muito alto: R$ {valor_total:,.2f}",
                "severidade": "media",
                "valor_detectado": float(valor_total),
                "impacto": "Requer aprovação executiva"
            })
        
        return anomalias
    
    async def _detectar_anomalias_fornecedor(self, xml_data: Union[NFEData, NFSEData], padroes: List[Dict]) -> List[Dict]:
        """Detect supplier-related anomalies"""
        anomalias = []
        
        if not xml_data.supplier:
            anomalias.append({
                "tipo": "fornecedor_ausente",
                "descricao": "Dados do fornecedor não encontrados",
                "severidade": "critica",
                "impacto": "Documento fiscal inválido"
            })
            return anomalias
        
        supplier = xml_data.supplier
        
        # Check CNPJ validity
        if not supplier.cnpj and not supplier.cpf:
            anomalias.append({
                "tipo": "documento_ausente",
                "descricao": "Fornecedor sem CNPJ ou CPF",
                "severidade": "critica",
                "impacto": "Não conformidade fiscal"
            })
        
        # Check for incomplete address
        if not supplier.address or not supplier.address.uf:
            anomalias.append({
                "tipo": "endereco_incompleto",
                "descricao": "Endereço do fornecedor incompleto",
                "severidade": "media",
                "impacto": "Dificuldade para validação e contato"
            })
        
        # Check for generic company names
        if supplier.razao_social and len(supplier.razao_social) < 5:
            anomalias.append({
                "tipo": "razao_social_suspeita",
                "descricao": f"Razão social muito curta: '{supplier.razao_social}'",
                "severidade": "baixa",
                "impacto": "Possível erro de cadastro"
            })
        
        return anomalias
    
    async def _detectar_anomalias_produtos(self, items: List[NFEItem], padroes: List[Dict]) -> List[Dict]:
        """Detect product-related anomalies"""
        anomalias = []
        
        for i, item in enumerate(items):
            if not item.produto:
                continue
            
            produto = item.produto
            
            # Check for generic descriptions
            if len(produto.descricao) < 10:
                anomalias.append({
                    "tipo": "descricao_generica",
                    "descricao": f"Item {i+1}: Descrição muito curta - '{produto.descricao}'",
                    "severidade": "baixa",
                    "item_numero": i+1,
                    "impacto": "Dificuldade para categorização"
                })
            
            # Check for missing NCM
            if not produto.ncm or produto.ncm == "00000000":
                anomalias.append({
                    "tipo": "ncm_ausente",
                    "descricao": f"Item {i+1}: NCM ausente ou inválido",
                    "severidade": "media",
                    "item_numero": i+1,
                    "impacto": "Não conformidade tributária"
                })
            
            # Check for suspicious quantities
            if hasattr(item, 'quantidade_comercial') and item.quantidade_comercial:
                if item.quantidade_comercial > 10000:
                    anomalias.append({
                        "tipo": "quantidade_suspeita",
                        "descricao": f"Item {i+1}: Quantidade muito alta - {item.quantidade_comercial}",
                        "severidade": "baixa",
                        "item_numero": i+1,
                        "valor_detectado": float(item.quantidade_comercial),
                        "impacto": "Verificar se quantidade está correta"
                    })
            
            # Check for zero unit values
            if hasattr(item, 'valor_unitario_comercial') and item.valor_unitario_comercial:
                if item.valor_unitario_comercial < 0.01:
                    anomalias.append({
                        "tipo": "valor_unitario_zero",
                        "descricao": f"Item {i+1}: Valor unitário muito baixo - R$ {item.valor_unitario_comercial}",
                        "severidade": "alta",
                        "item_numero": i+1,
                        "valor_detectado": float(item.valor_unitario_comercial),
                        "impacto": "Possível erro de preço ou fraude"
                    })
        
        return anomalias
    
    async def _detectar_anomalias_tributarias(self, xml_data: Union[NFEData, NFSEData], padroes: List[Dict]) -> List[Dict]:
        """Detect tax-related anomalies"""
        anomalias = []
        
        # Check ICMS anomalies for NFE
        if hasattr(xml_data, 'valor_icms') and hasattr(xml_data, 'valor_total_nf'):
            if xml_data.valor_total_nf and xml_data.valor_total_nf > 1000 and (not xml_data.valor_icms or xml_data.valor_icms == 0):
                anomalias.append({
                    "tipo": "icms_zerado_suspeito",
                    "descricao": f"ICMS zerado em transação de R$ {xml_data.valor_total_nf:,.2f}",
                    "severidade": "media",
                    "valor_transacao": float(xml_data.valor_total_nf),
                    "impacto": "Verificar enquadramento tributário"
                })
        
        # Check ISSQN anomalies for NFSE
        if hasattr(xml_data, 'valor_issqn') and hasattr(xml_data, 'valor_total_servicos'):
            if xml_data.valor_total_servicos and xml_data.valor_total_servicos > 500:
                if not xml_data.valor_issqn or xml_data.valor_issqn == 0:
                    anomalias.append({
                        "tipo": "issqn_ausente",
                        "descricao": f"ISSQN ausente em serviço de R$ {xml_data.valor_total_servicos:,.2f}",
                        "severidade": "alta",
                        "valor_servico": float(xml_data.valor_total_servicos),
                        "impacto": "Não conformidade tributária municipal"
                    })
                else:
                    # Check ISSQN rate
                    aliquota_issqn = (xml_data.valor_issqn / xml_data.valor_total_servicos) * 100
                    if aliquota_issqn < 2.0 or aliquota_issqn > 5.0:
                        anomalias.append({
                            "tipo": "aliquota_issqn_fora_padrao",
                            "descricao": f"Alíquota ISSQN fora do padrão: {aliquota_issqn:.2f}%",
                            "severidade": "media",
                            "aliquota_detectada": aliquota_issqn,
                            "impacto": "Verificar alíquota municipal aplicada"
                        })
        
        return anomalias
    
    async def _detectar_anomalias_temporais(self, xml_data: Union[NFEData, NFSEData], padroes: List[Dict]) -> List[Dict]:
        """Detect temporal anomalies"""
        anomalias = []
        
        if not xml_data.data_emissao:
            anomalias.append({
                "tipo": "data_ausente",
                "descricao": "Data de emissão não informada",
                "severidade": "critica",
                "impacto": "Documento fiscal inválido"
            })
            return anomalias
        
        agora = datetime.now()
        diferenca_dias = (agora - xml_data.data_emissao).days
        
        # Check for future dates
        if diferenca_dias < 0:
            anomalias.append({
                "tipo": "data_futura",
                "descricao": f"Data de emissão no futuro: {xml_data.data_emissao.strftime('%d/%m/%Y')}",
                "severidade": "critica",
                "dias_futuro": abs(diferenca_dias),
                "impacto": "Data inválida - documento suspeito"
            })
        
        # Check for very old dates
        elif diferenca_dias > 60:
            anomalias.append({
                "tipo": "data_muito_antiga",
                "descricao": f"Data de emissão muito antiga: {xml_data.data_emissao.strftime('%d/%m/%Y')} ({diferenca_dias} dias)",
                "severidade": "media",
                "dias_retroativos": diferenca_dias,
                "impacto": "Verificar motivo da emissão tardia"
            })
        
        # Check for non-business hours (if time is available)
        if xml_data.data_emissao.hour < 6 or xml_data.data_emissao.hour > 22:
            anomalias.append({
                "tipo": "horario_nao_comercial",
                "descricao": f"Emissão fora do horário comercial: {xml_data.data_emissao.strftime('%H:%M')}",
                "severidade": "baixa",
                "hora_emissao": xml_data.data_emissao.hour,
                "impacto": "Verificar se emissão automática ou manual"
            })
        
        return anomalias
    
    def _calcular_score_anomalia(self, anomalias: List[Dict]) -> float:
        """Calculate overall anomaly score"""
        if not anomalias:
            return 0.0
        
        peso_severidade = {
            "baixa": 0.1,
            "media": 0.3,
            "alta": 0.6,
            "critica": 1.0
        }
        
        score_total = 0.0
        for anomalia in anomalias:
            severidade = anomalia.get("severidade", "baixa")
            score_total += peso_severidade.get(severidade, 0.1)
        
        # Normalize score to 0-1 range
        score_normalizado = min(score_total / len(anomalias), 1.0)
        
        return round(score_normalizado, 2)
    
    def _classificar_nivel_risco(self, score: float) -> str:
        """Classify risk level based on anomaly score"""
        if score >= 0.8:
            return "critico"
        elif score >= 0.6:
            return "alto"
        elif score >= 0.3:
            return "medio"
        elif score > 0:
            return "baixo"
        else:
            return "nenhum"
    
    async def _avaliar_impacto_empresarial_anomalias(self, anomalias: List[Dict], xml_data: Union[NFEData, NFSEData]) -> Dict[str, Any]:
        """Assess business impact of detected anomalies"""
        if not anomalias:
            return {"impacto": "nenhum", "descricao": "Nenhuma anomalia detectada"}
        
        # Categorize impacts
        impactos_financeiros = []
        impactos_compliance = []
        impactos_operacionais = []
        
        valor_total = getattr(xml_data, 'valor_total_nf', None) or getattr(xml_data, 'valor_total_servicos', None) or 0
        
        for anomalia in anomalias:
            if anomalia["tipo"] in ["valor_zerado", "valor_muito_alto", "valor_unitario_zero"]:
                impactos_financeiros.append(anomalia["descricao"])
            elif anomalia["tipo"] in ["icms_zerado_suspeito", "issqn_ausente", "ncm_ausente"]:
                impactos_compliance.append(anomalia["descricao"])
            else:
                impactos_operacionais.append(anomalia["descricao"])
        
        # Calculate financial impact
        impacto_financeiro_estimado = "baixo"
        if valor_total > 100000:
            impacto_financeiro_estimado = "alto"
        elif valor_total > 10000:
            impacto_financeiro_estimado = "medio"
        
        return {
            "impacto_financeiro": {
                "nivel": impacto_financeiro_estimado,
                "valor_envolvido": float(valor_total),
                "anomalias": impactos_financeiros
            },
            "impacto_compliance": {
                "nivel": "alto" if impactos_compliance else "baixo",
                "anomalias": impactos_compliance,
                "riscos": ["Multas fiscais", "Auditoria", "Questionamentos da Receita"] if impactos_compliance else []
            },
            "impacto_operacional": {
                "nivel": "medio" if impactos_operacionais else "baixo",
                "anomalias": impactos_operacionais,
                "consequencias": ["Retrabalho", "Validação manual", "Atraso no processamento"] if impactos_operacionais else []
            }
        }
    
    def _gerar_recomendacoes_anomalias(self, anomalias: List[Dict], score: float) -> List[str]:
        """Generate recommendations based on detected anomalies"""
        if not anomalias:
            return ["Nenhuma ação necessária - documento sem anomalias detectadas"]
        
        recomendacoes = []
        
        # High-priority recommendations
        if score >= 0.7:
            recomendacoes.append("URGENTE: Revisar documento imediatamente - múltiplas anomalias críticas detectadas")
            recomendacoes.append("Suspender processamento automático até validação manual")
        
        # Specific recommendations by anomaly type
        tipos_detectados = {anomalia["tipo"] for anomalia in anomalias}
        
        if "valor_zerado" in tipos_detectados or "valor_unitario_zero" in tipos_detectados:
            recomendacoes.append("Verificar valores zerados - possível erro de digitação")
        
        if "icms_zerado_suspeito" in tipos_detectados or "issqn_ausente" in tipos_detectados:
            recomendacoes.append("Consultar departamento fiscal sobre enquadramento tributário")
        
        if "data_futura" in tipos_detectados:
            recomendacoes.append("Corrigir data de emissão - documento com data inválida")
        
        if "fornecedor_ausente" in tipos_detectados or "documento_ausente" in tipos_detectados:
            recomendacoes.append("Completar dados do fornecedor antes de processar")
        
        if "ncm_ausente" in tipos_detectados:
            recomendacoes.append("Incluir códigos NCM para conformidade fiscal")
        
        # General recommendations
        if score >= 0.3:
            recomendacoes.append("Documentar anomalias encontradas para auditoria")
            recomendacoes.append("Considerar treinamento da equipe sobre qualidade de dados")
        
        return recomendacoes