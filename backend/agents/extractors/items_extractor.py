"""
ItemsExtractor for extracting products and services data from fiscal documents
Extrator de dados de produtos e serviços para documentos fiscais brasileiros
"""

import structlog
from typing import Dict, Any, List, Optional
from lxml import etree
from decimal import Decimal, InvalidOperation
import re

from utils.brazilian_business_validation import ValidadorNegociosBrasil
from utils.brazilian_formatting import FormatadorBrasileiro

logger = structlog.get_logger()


class ItemsExtractor:
    """Specialized extractor for products and services data from fiscal documents"""
    
    def __init__(self):
        self.validador = ValidadorNegociosBrasil()
        self.formatador = FormatadorBrasileiro()
    
    def extract_produtos_from_nfe(self, xml_root) -> List[Dict[str, Any]]:
        """
        Extract products from NF-e items with all fiscal fields
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of product data dictionaries
        """
        try:
            produtos = []
            nfe_ns = "http://www.portalfiscal.inf.br/nfe"
            
            # Find all item details (det elements)
            det_elements = xml_root.findall(f'.//{{{nfe_ns}}}det')
            
            if not det_elements:
                logger.warning("No det elements found in NF-e")
                return []
            
            for i, det in enumerate(det_elements, 1):
                try:
                    # Find product element
                    prod = det.find(f'.//{{{nfe_ns}}}prod')
                    if prod is None:
                        logger.warning(f"No prod element found in det {i}")
                        continue
                    
                    # Extract basic product data
                    produto = {
                        'codigo_produto': self._get_text(prod, f'.//{{{nfe_ns}}}cProd'),
                        'ean': self._get_text(prod, f'.//{{{nfe_ns}}}cEAN'),
                        'descricao': self._get_text(prod, f'.//{{{nfe_ns}}}xProd'),
                        'ncm': self._get_text(prod, f'.//{{{nfe_ns}}}NCM'),
                        'cest': self._get_text(prod, f'.//{{{nfe_ns}}}CEST'),
                        'cfop': self._get_text(prod, f'.//{{{nfe_ns}}}CFOP'),
                        'unidade_comercial': self._get_text(prod, f'.//{{{nfe_ns}}}uCom'),
                        'unidade_tributavel': self._get_text(prod, f'.//{{{nfe_ns}}}uTrib'),
                        'ex_tipi': self._get_text(prod, f'.//{{{nfe_ns}}}EXTIPI'),
                        'genero': self._get_text(prod, f'.//{{{nfe_ns}}}genero'),
                        'codigo_beneficio': self._get_text(prod, f'.//{{{nfe_ns}}}cBenef')
                    }
                    
                    # Extract tax information
                    imposto_data = self._extract_tax_info_nfe(det, nfe_ns)
                    produto.update(imposto_data)
                    
                    # Extract additional product information
                    adicional_data = self._extract_additional_product_info_nfe(prod, nfe_ns)
                    produto.update(adicional_data)
                    
                    produtos.append(produto)
                    
                except Exception as e:
                    logger.error(f"Failed to extract product {i} from NF-e", error=str(e))
                    continue
            
            logger.info(f"Extracted {len(produtos)} products from NF-e")
            return produtos
            
        except Exception as e:
            logger.error("Failed to extract produtos from NF-e", error=str(e))
            return []
    
    def extract_servicos_from_nfse(self, xml_root) -> List[Dict[str, Any]]:
        """
        Extract services from NFS-e with municipal codes and taxation
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of service data dictionaries
        """
        try:
            servicos = []
            
            # NFS-e can have different schemas - try common patterns
            service_elements = [
                './/Servico', './/servico', './/ServicoValores',
                './/ItensServico', './/ItemServico', './/ListaServicos'
            ]
            
            servico_root = None
            for element_path in service_elements:
                servico_root = xml_root.find(element_path)
                if servico_root is not None:
                    break
            
            if servico_root is None:
                logger.warning("No service elements found in NFS-e")
                return []
            
            # Try to extract service data
            servico = {
                'codigo_servico': self._get_text_multiple_paths(servico_root, [
                    './/CodigoServico', './/codigoServico', './/ItemListaServico'
                ]),
                'descricao': self._get_text_multiple_paths(servico_root, [
                    './/Discriminacao', './/discriminacao', './/DescricaoServico',
                    './/descricaoServico', './/Descricao'
                ]),
                'codigo_cnae': self._get_text_multiple_paths(servico_root, [
                    './/CodigoCnae', './/codigoCnae', './/CNAE'
                ]),
                'codigo_tributacao_nacional': self._get_text_multiple_paths(servico_root, [
                    './/CodigoTributacaoMunicipio', './/ItemListaServico'
                ]),
                'codigo_tributacao_municipal': self._get_text_multiple_paths(servico_root, [
                    './/CodigoTributacaoMunicipio', './/codigoTributacaoMunicipio'
                ]),
                'codigo_nbs': self._get_text_multiple_paths(servico_root, [
                    './/CodigoNbs', './/codigoNbs', './/NBS'
                ])
            }
            
            # Extract tax information for services
            tax_data = self._extract_service_tax_info_nfse(servico_root)
            servico.update(tax_data)
            
            # Extract additional service information
            adicional_data = self._extract_additional_service_info_nfse(servico_root)
            servico.update(adicional_data)
            
            if servico.get('codigo_servico') or servico.get('descricao'):
                servicos.append(servico)
            
            logger.info(f"Extracted {len(servicos)} services from NFS-e")
            return servicos
            
        except Exception as e:
            logger.error("Failed to extract servicos from NFS-e", error=str(e))
            return []
    
    def extract_nfe_items_for_fact_table(self, xml_root) -> List[Dict[str, Any]]:
        """
        Extract detailed NFE items data for fact table with all values and calculations
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of detailed item data for fact table
        """
        try:
            items = []
            nfe_ns = "http://www.portalfiscal.inf.br/nfe"
            
            # Get document key for reference
            inf_nfe = xml_root.find(f'.//{{{nfe_ns}}}infNFe')
            chave_nfe = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe is not None else ''
            
            # Find all item details
            det_elements = xml_root.findall(f'.//{{{nfe_ns}}}det')
            
            for i, det in enumerate(det_elements, 1):
                try:
                    prod = det.find(f'.//{{{nfe_ns}}}prod')
                    if prod is None:
                        continue
                    
                    # Extract detailed item data
                    item = {
                        'chave_nfe': chave_nfe,
                        'numero_item': i,
                        'codigo_produto': self._get_text(prod, f'.//{{{nfe_ns}}}cProd'),
                        'ean': self._get_text(prod, f'.//{{{nfe_ns}}}cEAN'),
                        'descricao': self._get_text(prod, f'.//{{{nfe_ns}}}xProd'),
                        'ncm': self._get_text(prod, f'.//{{{nfe_ns}}}NCM'),
                        'cest': self._get_text(prod, f'.//{{{nfe_ns}}}CEST'),
                        'cfop': self._get_text(prod, f'.//{{{nfe_ns}}}CFOP'),
                        'unidade_comercial': self._get_text(prod, f'.//{{{nfe_ns}}}uCom'),
                        'quantidade_comercial': self._get_decimal(prod, f'.//{{{nfe_ns}}}qCom'),
                        'valor_unitario_comercial': self._get_decimal(prod, f'.//{{{nfe_ns}}}vUnCom'),
                        'valor_total_bruto': self._get_decimal(prod, f'.//{{{nfe_ns}}}vProd'),
                        'unidade_tributavel': self._get_text(prod, f'.//{{{nfe_ns}}}uTrib'),
                        'quantidade_tributavel': self._get_decimal(prod, f'.//{{{nfe_ns}}}qTrib'),
                        'valor_unitario_tributavel': self._get_decimal(prod, f'.//{{{nfe_ns}}}vUnTrib'),
                        'valor_frete': self._get_decimal(prod, f'.//{{{nfe_ns}}}vFrete'),
                        'valor_seguro': self._get_decimal(prod, f'.//{{{nfe_ns}}}vSeg'),
                        'valor_desconto': self._get_decimal(prod, f'.//{{{nfe_ns}}}vDesc'),
                        'valor_outras_despesas': self._get_decimal(prod, f'.//{{{nfe_ns}}}vOutro')
                    }
                    
                    # Extract detailed tax information
                    tax_details = self._extract_detailed_tax_info_nfe(det, nfe_ns)
                    item.update(tax_details)
                    
                    # Calculate total values and validate consistency
                    item = self._calculate_and_validate_totals(item)
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.error(f"Failed to extract detailed item {i} from NF-e", error=str(e))
                    continue
            
            logger.info(f"Extracted {len(items)} detailed items for fact table from NF-e")
            return items
            
        except Exception as e:
            logger.error("Failed to extract detailed NFE items", error=str(e))
            return []
    
    def extract_nfse_services_for_fact_table(self, xml_root) -> List[Dict[str, Any]]:
        """
        Extract detailed NFSE services data for fact table
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            List of detailed service data for fact table
        """
        try:
            services = []
            
            # Try to find NFS-e identification
            nfse_id = self._get_text_multiple_paths(xml_root, [
                './/Numero', './/numero', './/NumeroNfse', './/numeroNfse'
            ])
            
            if not nfse_id:
                nfse_id = f"NFSE_{hash(str(xml_root))}"
            
            # Extract service values
            servico_root = xml_root.find('.//Servico') or xml_root.find('.//servico')
            if servico_root is None:
                logger.warning("No service root found in NFS-e")
                return []
            
            # Extract detailed service data
            service = {
                'id_nfse': nfse_id,
                'codigo_servico': self._get_text_multiple_paths(servico_root, [
                    './/CodigoServico', './/codigoServico', './/ItemListaServico'
                ]),
                'descricao_servico': self._get_text_multiple_paths(servico_root, [
                    './/Discriminacao', './/discriminacao', './/DescricaoServico'
                ]),
                'quantidade': self._get_decimal_multiple_paths(servico_root, [
                    './/Quantidade', './/quantidade'
                ]) or Decimal('1.0'),
                'valor_unitario': self._get_decimal_multiple_paths(servico_root, [
                    './/ValorUnitario', './/valorUnitario'
                ]),
                'valor_total': self._get_decimal_multiple_paths(servico_root, [
                    './/ValorServicos', './/valorServicos', './/ValorTotal'
                ]),
                'valor_desconto': self._get_decimal_multiple_paths(servico_root, [
                    './/DescontoIncondicionado', './/descontoIncondicionado',
                    './/DescontoCondicionado', './/descontoCondicionado'
                ]),
                'valor_deducoes': self._get_decimal_multiple_paths(servico_root, [
                    './/ValorDeducoes', './/valorDeducoes'
                ]),
                'valor_base_calculo': self._get_decimal_multiple_paths(servico_root, [
                    './/BaseCalculo', './/baseCalculo'
                ]),
                'aliquota_issqn': self._get_decimal_multiple_paths(servico_root, [
                    './/Aliquota', './/aliquota'
                ]),
                'valor_issqn': self._get_decimal_multiple_paths(servico_root, [
                    './/ValorIss', './/valorIss', './/ValorISSQN'
                ]),
                'valor_credito': self._get_decimal_multiple_paths(servico_root, [
                    './/ValorCredito', './/valorCredito'
                ])
            }
            
            # Calculate missing values if possible
            service = self._calculate_service_values(service)
            
            services.append(service)
            
            logger.info(f"Extracted {len(services)} detailed services for fact table from NFS-e")
            return services
            
        except Exception as e:
            logger.error("Failed to extract detailed NFSE services", error=str(e))
            return []
    
    def normalize_produto_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize product data for database insertion
        
        Args:
            raw_data: Raw extracted product data
            
        Returns:
            Normalized and validated product data
        """
        try:
            normalized = {}
            
            # Required fields
            normalized['codigo_produto'] = raw_data.get('codigo_produto', '').strip()[:60]
            if not normalized['codigo_produto']:
                raise ValueError("Código do produto is required")
            
            normalized['descricao'] = raw_data.get('descricao', '').strip()
            if not normalized['descricao']:
                raise ValueError("Descrição do produto is required")
            
            # Optional fields with validation
            ean = raw_data.get('ean', '').strip()
            if ean and ean != 'SEM GTIN':
                normalized['ean'] = ean[:14]
            else:
                normalized['ean'] = None
            
            # NCM validation
            ncm = raw_data.get('ncm', '').strip()
            if ncm:
                ncm_validation = self.validador.validar_ncm(ncm)
                if ncm_validation['valido']:
                    normalized['ncm'] = ncm[:8]
                else:
                    normalized['ncm'] = None
                    logger.warning("Invalid NCM", ncm=ncm, errors=ncm_validation['erros'])
            else:
                normalized['ncm'] = None
            
            # CEST validation
            cest = raw_data.get('cest', '').strip()
            if cest:
                normalized['cest'] = cest[:7]
            else:
                normalized['cest'] = None
            
            # CFOP validation
            cfop = raw_data.get('cfop', '').strip()
            if cfop:
                cfop_validation = self.validador.validar_cfop(cfop, '1')  # Assume saída
                if cfop_validation['valido']:
                    normalized['cfop'] = cfop[:4]
                else:
                    normalized['cfop'] = None
                    logger.warning("Invalid CFOP", cfop=cfop, errors=cfop_validation['erros'])
            else:
                normalized['cfop'] = None
            
            # Unit fields
            normalized['unidade_comercial'] = raw_data.get('unidade_comercial', '').strip()[:6] or None
            normalized['unidade_tributavel'] = raw_data.get('unidade_tributavel', '').strip()[:6] or None
            
            # Additional fields
            normalized['ex_tipi'] = raw_data.get('ex_tipi', '').strip()[:3] or None
            normalized['genero'] = raw_data.get('genero', '').strip()[:2] or None
            normalized['codigo_beneficio'] = raw_data.get('codigo_beneficio', '').strip()[:10] or None
            
            # Categorization fields (will be filled by categorization process)
            normalized['categoria'] = raw_data.get('categoria', '').strip()[:100] or None
            normalized['subcategoria'] = raw_data.get('subcategoria', '').strip()[:100] or None
            
            logger.info(
                "Product data normalized",
                codigo_produto=normalized['codigo_produto'],
                descricao=normalized['descricao'][:50] + "..." if len(normalized['descricao']) > 50 else normalized['descricao']
            )
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize product data", error=str(e))
            raise
    
    def normalize_servico_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize service data for database insertion
        
        Args:
            raw_data: Raw extracted service data
            
        Returns:
            Normalized and validated service data
        """
        try:
            normalized = {}
            
            # Required fields
            normalized['codigo_servico'] = raw_data.get('codigo_servico', '').strip()[:20]
            if not normalized['codigo_servico']:
                # Generate a default code if missing
                normalized['codigo_servico'] = 'SERV_DEFAULT'
            
            normalized['descricao'] = raw_data.get('descricao', '').strip()
            if not normalized['descricao']:
                normalized['descricao'] = 'Serviço não especificado'
            
            # Optional fields with validation
            normalized['codigo_cnae'] = raw_data.get('codigo_cnae', '').strip()[:7] or None
            normalized['codigo_tributacao_nacional'] = raw_data.get('codigo_tributacao_nacional', '').strip()[:20] or None
            normalized['codigo_tributacao_municipal'] = raw_data.get('codigo_tributacao_municipal', '').strip()[:20] or None
            normalized['codigo_nbs'] = raw_data.get('codigo_nbs', '').strip()[:20] or None
            
            # Categorization fields (will be filled by categorization process)
            normalized['categoria'] = raw_data.get('categoria', '').strip()[:100] or None
            normalized['subcategoria'] = raw_data.get('subcategoria', '').strip()[:100] or None
            
            logger.info(
                "Service data normalized",
                codigo_servico=normalized['codigo_servico'],
                descricao=normalized['descricao'][:50] + "..." if len(normalized['descricao']) > 50 else normalized['descricao']
            )
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize service data", error=str(e))
            raise
    
    def _extract_tax_info_nfe(self, det_element, namespace: str) -> Dict[str, Any]:
        """Extract tax information from NF-e item"""
        try:
            tax_data = {}
            
            # Find imposto element
            imposto = det_element.find(f'.//{{{namespace}}}imposto')
            if imposto is None:
                return tax_data
            
            # ICMS information
            icms_elements = [
                f'.//{{{namespace}}}ICMS00',
                f'.//{{{namespace}}}ICMS10',
                f'.//{{{namespace}}}ICMS20',
                f'.//{{{namespace}}}ICMS30',
                f'.//{{{namespace}}}ICMS40',
                f'.//{{{namespace}}}ICMS51',
                f'.//{{{namespace}}}ICMS60',
                f'.//{{{namespace}}}ICMS70',
                f'.//{{{namespace}}}ICMS90'
            ]
            
            for icms_path in icms_elements:
                icms = imposto.find(icms_path)
                if icms is not None:
                    tax_data['cst_icms'] = self._get_text(icms, f'.//{{{namespace}}}CST') or self._get_text(icms, f'.//{{{namespace}}}CSOSN')
                    tax_data['aliquota_icms'] = self._get_decimal(icms, f'.//{{{namespace}}}pICMS')
                    tax_data['valor_icms'] = self._get_decimal(icms, f'.//{{{namespace}}}vICMS')
                    break
            
            # IPI information
            ipi = imposto.find(f'.//{{{namespace}}}IPI')
            if ipi is not None:
                tax_data['cst_ipi'] = self._get_text(ipi, f'.//{{{namespace}}}CST')
                tax_data['aliquota_ipi'] = self._get_decimal(ipi, f'.//{{{namespace}}}pIPI')
                tax_data['valor_ipi'] = self._get_decimal(ipi, f'.//{{{namespace}}}vIPI')
            
            # PIS information
            pis = imposto.find(f'.//{{{namespace}}}PIS')
            if pis is not None:
                tax_data['cst_pis'] = self._get_text(pis, f'.//{{{namespace}}}CST')
                tax_data['aliquota_pis'] = self._get_decimal(pis, f'.//{{{namespace}}}pPIS')
                tax_data['valor_pis'] = self._get_decimal(pis, f'.//{{{namespace}}}vPIS')
            
            # COFINS information
            cofins = imposto.find(f'.//{{{namespace}}}COFINS')
            if cofins is not None:
                tax_data['cst_cofins'] = self._get_text(cofins, f'.//{{{namespace}}}CST')
                tax_data['aliquota_cofins'] = self._get_decimal(cofins, f'.//{{{namespace}}}pCOFINS')
                tax_data['valor_cofins'] = self._get_decimal(cofins, f'.//{{{namespace}}}vCOFINS')
            
            return tax_data
            
        except Exception as e:
            logger.error("Failed to extract tax info from NF-e", error=str(e))
            return {}
    
    def _extract_additional_product_info_nfe(self, prod_element, namespace: str) -> Dict[str, Any]:
        """Extract additional product information from NF-e"""
        try:
            additional_data = {}
            
            # Additional product fields
            additional_data['codigo_ean_tributavel'] = self._get_text(prod_element, f'.//{{{namespace}}}cEANTrib')
            additional_data['informacoes_adicionais'] = self._get_text(prod_element, f'.//{{{namespace}}}xPed')
            additional_data['numero_pedido'] = self._get_text(prod_element, f'.//{{{namespace}}}nItemPed')
            additional_data['numero_fci'] = self._get_text(prod_element, f'.//{{{namespace}}}nFCI')
            
            return additional_data
            
        except Exception as e:
            logger.error("Failed to extract additional product info", error=str(e))
            return {}
    
    def _extract_service_tax_info_nfse(self, servico_element) -> Dict[str, Any]:
        """Extract tax information from NFS-e service"""
        try:
            tax_data = {}
            
            # ISSQN information
            tax_data['aliquota_issqn'] = self._get_decimal_multiple_paths(servico_element, [
                './/Aliquota', './/aliquota'
            ])
            tax_data['valor_issqn'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorIss', './/valorIss', './/ValorISSQN'
            ])
            tax_data['base_calculo_issqn'] = self._get_decimal_multiple_paths(servico_element, [
                './/BaseCalculo', './/baseCalculo'
            ])
            
            # Other municipal taxes
            tax_data['valor_inss'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorInss', './/valorInss'
            ])
            tax_data['valor_ir'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorIr', './/valorIr'
            ])
            tax_data['valor_csll'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorCsll', './/valorCsll'
            ])
            tax_data['valor_cofins'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorCofins', './/valorCofins'
            ])
            tax_data['valor_pis'] = self._get_decimal_multiple_paths(servico_element, [
                './/ValorPis', './/valorPis'
            ])
            
            return tax_data
            
        except Exception as e:
            logger.error("Failed to extract service tax info", error=str(e))
            return {}
    
    def _extract_additional_service_info_nfse(self, servico_element) -> Dict[str, Any]:
        """Extract additional service information from NFS-e"""
        try:
            additional_data = {}
            
            # Service location and execution
            additional_data['municipio_prestacao'] = self._get_text_multiple_paths(servico_element, [
                './/MunicipioPrestacaoServico', './/municipioPrestacaoServico'
            ])
            additional_data['codigo_obra'] = self._get_text_multiple_paths(servico_element, [
                './/CodigoObra', './/codigoObra'
            ])
            additional_data['art'] = self._get_text_multiple_paths(servico_element, [
                './/ArtObra', './/artObra'
            ])
            
            return additional_data
            
        except Exception as e:
            logger.error("Failed to extract additional service info", error=str(e))
            return {}
    
    def _extract_detailed_tax_info_nfe(self, det_element, namespace: str) -> Dict[str, Any]:
        """Extract detailed tax information for fact table"""
        try:
            tax_details = {}
            
            imposto = det_element.find(f'.//{{{namespace}}}imposto')
            if imposto is None:
                return tax_details
            
            # Detailed ICMS
            icms_elements = imposto.findall(f'.//{{{namespace}}}ICMS//*')
            for icms in icms_elements:
                if icms.tag.endswith('}CST') or icms.tag.endswith('}CSOSN'):
                    tax_details['situacao_tributaria_icms'] = icms.text
                elif icms.tag.endswith('}pICMS'):
                    tax_details['aliquota_icms'] = self._to_decimal(icms.text)
                elif icms.tag.endswith('}vICMS'):
                    tax_details['valor_icms'] = self._to_decimal(icms.text)
                elif icms.tag.endswith('}vBC'):
                    tax_details['base_calculo_icms'] = self._to_decimal(icms.text)
            
            # Detailed IPI
            ipi = imposto.find(f'.//{{{namespace}}}IPI')
            if ipi is not None:
                tax_details['situacao_tributaria_ipi'] = self._get_text(ipi, f'.//{{{namespace}}}CST')
                tax_details['aliquota_ipi'] = self._get_decimal(ipi, f'.//{{{namespace}}}pIPI')
                tax_details['valor_ipi'] = self._get_decimal(ipi, f'.//{{{namespace}}}vIPI')
                tax_details['base_calculo_ipi'] = self._get_decimal(ipi, f'.//{{{namespace}}}vBC')
            
            # Detailed PIS
            pis = imposto.find(f'.//{{{namespace}}}PIS')
            if pis is not None:
                tax_details['situacao_tributaria_pis'] = self._get_text(pis, f'.//{{{namespace}}}CST')
                tax_details['aliquota_pis'] = self._get_decimal(pis, f'.//{{{namespace}}}pPIS')
                tax_details['valor_pis'] = self._get_decimal(pis, f'.//{{{namespace}}}vPIS')
                tax_details['base_calculo_pis'] = self._get_decimal(pis, f'.//{{{namespace}}}vBC')
            
            # Detailed COFINS
            cofins = imposto.find(f'.//{{{namespace}}}COFINS')
            if cofins is not None:
                tax_details['situacao_tributaria_cofins'] = self._get_text(cofins, f'.//{{{namespace}}}CST')
                tax_details['aliquota_cofins'] = self._get_decimal(cofins, f'.//{{{namespace}}}pCOFINS')
                tax_details['valor_cofins'] = self._get_decimal(cofins, f'.//{{{namespace}}}vCOFINS')
                tax_details['base_calculo_cofins'] = self._get_decimal(cofins, f'.//{{{namespace}}}vBC')
            
            return tax_details
            
        except Exception as e:
            logger.error("Failed to extract detailed tax info", error=str(e))
            return {}
    
    def _calculate_and_validate_totals(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate and validate item totals for consistency"""
        try:
            # Calculate net value
            valor_bruto = item.get('valor_total_bruto') or Decimal('0')
            valor_desconto = item.get('valor_desconto') or Decimal('0')
            valor_frete = item.get('valor_frete') or Decimal('0')
            valor_seguro = item.get('valor_seguro') or Decimal('0')
            valor_outras_despesas = item.get('valor_outras_despesas') or Decimal('0')
            
            valor_liquido = valor_bruto - valor_desconto + valor_frete + valor_seguro + valor_outras_despesas
            item['valor_liquido_item'] = valor_liquido
            
            # Calculate total taxes
            valor_icms = item.get('valor_icms') or Decimal('0')
            valor_ipi = item.get('valor_ipi') or Decimal('0')
            valor_pis = item.get('valor_pis') or Decimal('0')
            valor_cofins = item.get('valor_cofins') or Decimal('0')
            
            total_impostos = valor_icms + valor_ipi + valor_pis + valor_cofins
            item['total_impostos'] = total_impostos
            
            # Validate quantity and unit value consistency
            quantidade = item.get('quantidade_comercial')
            valor_unitario = item.get('valor_unitario_comercial')
            
            if quantidade and valor_unitario and valor_bruto:
                valor_calculado = quantidade * valor_unitario
                diferenca = abs(valor_bruto - valor_calculado)
                
                if diferenca > Decimal('0.01'):
                    logger.warning(
                        "Value inconsistency in item",
                        codigo_produto=item.get('codigo_produto'),
                        valor_bruto=valor_bruto,
                        valor_calculado=valor_calculado,
                        diferenca=diferenca
                    )
                    item['inconsistencia_valores'] = True
                else:
                    item['inconsistencia_valores'] = False
            
            return item
            
        except Exception as e:
            logger.error("Failed to calculate and validate totals", error=str(e))
            return item
    
    def _calculate_service_values(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate missing service values if possible"""
        try:
            # Calculate unit value if missing
            if not service.get('valor_unitario') and service.get('valor_total') and service.get('quantidade'):
                service['valor_unitario'] = service['valor_total'] / service['quantidade']
            
            # Calculate total if missing
            if not service.get('valor_total') and service.get('valor_unitario') and service.get('quantidade'):
                service['valor_total'] = service['valor_unitario'] * service['quantidade']
            
            # Calculate base de cálculo if missing
            if not service.get('valor_base_calculo') and service.get('valor_total'):
                valor_desconto = service.get('valor_desconto') or Decimal('0')
                valor_deducoes = service.get('valor_deducoes') or Decimal('0')
                service['valor_base_calculo'] = service['valor_total'] - valor_desconto - valor_deducoes
            
            # Calculate ISSQN if missing
            if not service.get('valor_issqn') and service.get('valor_base_calculo') and service.get('aliquota_issqn'):
                service['valor_issqn'] = service['valor_base_calculo'] * (service['aliquota_issqn'] / Decimal('100'))
            
            return service
            
        except Exception as e:
            logger.error("Failed to calculate service values", error=str(e))
            return service
    
    def _get_text(self, parent, xpath: str) -> str:
        """Get text content from XML element"""
        if parent is None:
            return ""
        element = parent.find(xpath)
        return element.text.strip() if element is not None and element.text else ""
    
    def _get_text_multiple_paths(self, parent, xpaths: list) -> str:
        """Get text content trying multiple XPath expressions"""
        if parent is None:
            return ""
        
        for xpath in xpaths:
            element = parent.find(xpath)
            if element is not None and element.text:
                return element.text.strip()
        
        return ""
    
    def _get_decimal(self, parent, xpath: str) -> Optional[Decimal]:
        """Get decimal value from XML element"""
        text = self._get_text(parent, xpath)
        return self._to_decimal(text)
    
    def _get_decimal_multiple_paths(self, parent, xpaths: list) -> Optional[Decimal]:
        """Get decimal value trying multiple XPath expressions"""
        text = self._get_text_multiple_paths(parent, xpaths)
        return self._to_decimal(text)
    
    def _to_decimal(self, text: str) -> Optional[Decimal]:
        """Convert text to Decimal with error handling"""
        if not text:
            return None
        
        try:
            # Handle Brazilian decimal format (comma as decimal separator)
            text_clean = text.replace(',', '.')
            return Decimal(text_clean)
        except (InvalidOperation, ValueError):
            logger.warning("Failed to convert to decimal", text=text)
            return None