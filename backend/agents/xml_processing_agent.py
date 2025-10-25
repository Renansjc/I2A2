"""
XML Processing Agent for NF-e and NFS-e documents
"""

import os
import asyncio
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
            
            # Set up file system monitoring
            self.file_handler = XMLFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                settings.XML_WATCH_DIRECTORY,
                recursive=False
            )
            self.observer.start()
            
            self.logger.info("XML Processing Agent initialized", 
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
            
            # Move file to processed directory
            await self._move_processed_file(file_path)
            
            # Notify completion
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
            'data': data  # Full fiscal data for AI Categorization Agent
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