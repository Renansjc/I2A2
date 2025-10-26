"""
DestinatarioExtractor for extracting customer data from fiscal documents
Extrator de dados de destinatário para documentos fiscais brasileiros
"""

import structlog
from typing import Dict, Any, Optional
from lxml import etree
import re

from utils.brazilian_business_validation import ValidadorNegociosBrasil
from utils.brazilian_formatting import FormatadorBrasileiro

logger = structlog.get_logger()


class DestinatarioExtractor:
    """Specialized extractor for destinatario (customer) data from fiscal documents"""
    
    def __init__(self):
        self.validador = ValidadorNegociosBrasil()
        self.formatador = FormatadorBrasileiro()
    
    def extract_from_nfe(self, xml_root) -> Optional[Dict[str, Any]]:
        """
        Extract destinatario data from NF-e XML (when present)
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            Dict containing extracted destinatario data or None if not present
        """
        try:
            # NF-e namespace
            nfe_ns = "http://www.portalfiscal.inf.br/nfe"
            
            # Find destinatario element
            dest = xml_root.find(f'.//{{{nfe_ns}}}dest')
            if dest is None:
                logger.info("No destinatario element found in NF-e")
                return None
            
            # Extract basic identification data
            destinatario_data = {
                'cnpj': self._get_text(dest, f'.//{{{nfe_ns}}}CNPJ'),
                'cpf': self._get_text(dest, f'.//{{{nfe_ns}}}CPF'),
                'id_estrangeiro': self._get_text(dest, f'.//{{{nfe_ns}}}idEstrangeiro'),
                'inscricao_estadual': self._get_text(dest, f'.//{{{nfe_ns}}}IE'),
                'inscricao_suframa': self._get_text(dest, f'.//{{{nfe_ns}}}ISUF'),
                'inscricao_municipal': self._get_text(dest, f'.//{{{nfe_ns}}}IM'),
                'razao_social': self._get_text(dest, f'.//{{{nfe_ns}}}xNome'),
                'indicador_ie': self._get_text(dest, f'.//{{{nfe_ns}}}indIEDest')
            }
            
            # Extract address data
            endereco_data = self._extract_endereco_nfe(dest, nfe_ns)
            destinatario_data.update(endereco_data)
            
            # Extract contact data
            contato_data = self._extract_contato_nfe(dest, nfe_ns)
            destinatario_data.update(contato_data)
            
            # Check if we have meaningful data
            if not any([
                destinatario_data.get('cnpj'),
                destinatario_data.get('cpf'),
                destinatario_data.get('id_estrangeiro'),
                destinatario_data.get('razao_social')
            ]):
                logger.info("No meaningful destinatario data found in NF-e")
                return None
            
            logger.info(
                "Destinatario data extracted from NF-e",
                cnpj=destinatario_data.get('cnpj'),
                cpf=destinatario_data.get('cpf'),
                razao_social=destinatario_data.get('razao_social')
            )
            
            return destinatario_data
            
        except Exception as e:
            logger.error("Failed to extract destinatario data from NF-e", error=str(e))
            return None
    
    def extract_from_nfse(self, xml_root) -> Optional[Dict[str, Any]]:
        """
        Extract destinatario (tomador) data from NFS-e XML
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            Dict containing extracted destinatario data or None if not present
        """
        try:
            # NFS-e can have different schemas depending on municipality
            # Try different common element names for tomador
            tomador_elements = [
                './/TomadorServico',
                './/Tomador',
                './/tomador',
                './/IdentificacaoTomador',
                './/DadosTomador'
            ]
            
            tomador = None
            for element_path in tomador_elements:
                tomador = xml_root.find(element_path)
                if tomador is not None:
                    break
            
            if tomador is None:
                logger.info("No tomador element found in NFS-e")
                return None
            
            # Extract basic identification data
            destinatario_data = {
                'cnpj': self._get_text_multiple_paths(tomador, [
                    './/Cnpj', './/CNPJ', './/cnpj'
                ]),
                'cpf': self._get_text_multiple_paths(tomador, [
                    './/Cpf', './/CPF', './/cpf'
                ]),
                'inscricao_estadual': self._get_text_multiple_paths(tomador, [
                    './/InscricaoEstadual', './/IE', './/ie'
                ]),
                'inscricao_municipal': self._get_text_multiple_paths(tomador, [
                    './/InscricaoMunicipal', './/IM', './/im'
                ]),
                'razao_social': self._get_text_multiple_paths(tomador, [
                    './/RazaoSocial', './/razaoSocial', './/xNome', './/Nome'
                ]),
                'nome_fantasia': self._get_text_multiple_paths(tomador, [
                    './/NomeFantasia', './/nomeFantasia', './/xFant'
                ])
            }
            
            # Extract address data for NFS-e
            endereco_data = self._extract_endereco_nfse(tomador)
            destinatario_data.update(endereco_data)
            
            # Extract contact data for NFS-e
            contato_data = self._extract_contato_nfse(tomador)
            destinatario_data.update(contato_data)
            
            # Check if we have meaningful data
            if not any([
                destinatario_data.get('cnpj'),
                destinatario_data.get('cpf'),
                destinatario_data.get('razao_social')
            ]):
                logger.info("No meaningful destinatario data found in NFS-e")
                return None
            
            logger.info(
                "Destinatario data extracted from NFS-e",
                cnpj=destinatario_data.get('cnpj'),
                cpf=destinatario_data.get('cpf'),
                razao_social=destinatario_data.get('razao_social')
            )
            
            return destinatario_data
            
        except Exception as e:
            logger.error("Failed to extract destinatario data from NFS-e", error=str(e))
            return None
    
    def _extract_endereco_nfe(self, dest_element, namespace: str) -> Dict[str, Any]:
        """Extract address data from NF-e destinatario element"""
        try:
            endereco_data = {
                'logradouro': self._get_text(dest_element, f'.//{{{namespace}}}xLgr'),
                'numero': self._get_text(dest_element, f'.//{{{namespace}}}nro'),
                'complemento': self._get_text(dest_element, f'.//{{{namespace}}}xCpl'),
                'bairro': self._get_text(dest_element, f'.//{{{namespace}}}xBairro'),
                'codigo_municipio': self._get_text(dest_element, f'.//{{{namespace}}}cMun'),
                'nome_municipio': self._get_text(dest_element, f'.//{{{namespace}}}xMun'),
                'uf': self._get_text(dest_element, f'.//{{{namespace}}}UF'),
                'cep': self._get_text(dest_element, f'.//{{{namespace}}}CEP'),
                'codigo_pais': self._get_text(dest_element, f'.//{{{namespace}}}cPais'),
                'nome_pais': self._get_text(dest_element, f'.//{{{namespace}}}xPais')
            }
            
            # Set default values for Brazil if not present
            if not endereco_data['codigo_pais']:
                endereco_data['codigo_pais'] = '1058'
            if not endereco_data['nome_pais']:
                endereco_data['nome_pais'] = 'Brasil'
            
            return endereco_data
            
        except Exception as e:
            logger.error("Failed to extract endereco from NF-e destinatario", error=str(e))
            return {}
    
    def _extract_endereco_nfse(self, tomador_element) -> Dict[str, Any]:
        """Extract address data from NFS-e tomador element"""
        try:
            # Try to find endereco element
            endereco_elements = [
                './/Endereco', './/endereco', './/EnderecoCompleto',
                './/DadosEndereco', './/EnderecoTomador'
            ]
            
            endereco = None
            for element_path in endereco_elements:
                endereco = tomador_element.find(element_path)
                if endereco is not None:
                    break
            
            if endereco is None:
                # Try to extract directly from tomador element
                endereco = tomador_element
            
            endereco_data = {
                'logradouro': self._get_text_multiple_paths(endereco, [
                    './/Endereco', './/endereco', './/Logradouro', './/logradouro'
                ]),
                'numero': self._get_text_multiple_paths(endereco, [
                    './/Numero', './/numero', './/nro'
                ]),
                'complemento': self._get_text_multiple_paths(endereco, [
                    './/Complemento', './/complemento', './/xCpl'
                ]),
                'bairro': self._get_text_multiple_paths(endereco, [
                    './/Bairro', './/bairro', './/xBairro'
                ]),
                'codigo_municipio': self._get_text_multiple_paths(endereco, [
                    './/CodigoMunicipio', './/codigoMunicipio', './/cMun'
                ]),
                'nome_municipio': self._get_text_multiple_paths(endereco, [
                    './/Cidade', './/cidade', './/xMun', './/Municipio'
                ]),
                'uf': self._get_text_multiple_paths(endereco, [
                    './/Uf', './/UF', './/uf', './/Estado'
                ]),
                'cep': self._get_text_multiple_paths(endereco, [
                    './/Cep', './/CEP', './/cep'
                ]),
                'codigo_pais': '1058',  # Default Brazil
                'nome_pais': 'Brasil'   # Default Brazil
            }
            
            return endereco_data
            
        except Exception as e:
            logger.error("Failed to extract endereco from NFS-e tomador", error=str(e))
            return {}
    
    def _extract_contato_nfe(self, dest_element, namespace: str) -> Dict[str, Any]:
        """Extract contact data from NF-e destinatario element"""
        try:
            contato_data = {
                'telefone': self._get_text(dest_element, f'.//{{{namespace}}}fone'),
                'email': self._get_text(dest_element, f'.//{{{namespace}}}email')
            }
            
            return contato_data
            
        except Exception as e:
            logger.error("Failed to extract contato from NF-e destinatario", error=str(e))
            return {}
    
    def _extract_contato_nfse(self, tomador_element) -> Dict[str, Any]:
        """Extract contact data from NFS-e tomador element"""
        try:
            contato_data = {
                'telefone': self._get_text_multiple_paths(tomador_element, [
                    './/Telefone', './/telefone', './/fone'
                ]),
                'email': self._get_text_multiple_paths(tomador_element, [
                    './/Email', './/email', './/Email'
                ])
            }
            
            return contato_data
            
        except Exception as e:
            logger.error("Failed to extract contato from NFS-e tomador", error=str(e))
            return {}
    
    def normalize_destinatario_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize destinatario data for database insertion
        
        Args:
            raw_data: Raw extracted data
            
        Returns:
            Normalized and validated data
        """
        try:
            normalized = {}
            
            # Handle different types of identification
            cnpj = raw_data.get('cnpj', '').strip()
            cpf = raw_data.get('cpf', '').strip()
            id_estrangeiro = raw_data.get('id_estrangeiro', '').strip()
            
            # Validate and format CNPJ/CPF (optional for destinatario)
            if cnpj:
                cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
                if len(cnpj_clean) == 14 and self._validate_cnpj_digits(cnpj_clean):
                    normalized['cnpj'] = self.formatador.formatar_documento(cnpj_clean, 'cnpj')
                else:
                    logger.warning("Invalid CNPJ for destinatario", cnpj=cnpj)
                    
            elif cpf:
                cpf_clean = re.sub(r'[^0-9]', '', cpf)
                if len(cpf_clean) == 11 and self._validate_cpf_digits(cpf_clean):
                    normalized['cpf'] = self.formatador.formatar_documento(cpf_clean, 'cpf')
                else:
                    logger.warning("Invalid CPF for destinatario", cpf=cpf)
                    
            elif id_estrangeiro:
                # For foreign customers
                normalized['id_estrangeiro'] = id_estrangeiro[:20]
            
            # Optional identification fields
            normalized['inscricao_estadual'] = raw_data.get('inscricao_estadual', '').strip()[:14] or None
            normalized['inscricao_municipal'] = raw_data.get('inscricao_municipal', '').strip()[:15] or None
            normalized['inscricao_suframa'] = raw_data.get('inscricao_suframa', '').strip()[:9] or None
            
            # Indicator for IE (Inscrição Estadual)
            indicador_ie = raw_data.get('indicador_ie', '').strip()
            if indicador_ie in ['1', '2', '9']:  # 1=Contribuinte, 2=Isento, 9=Não contribuinte
                normalized['indicador_ie'] = indicador_ie
            else:
                normalized['indicador_ie'] = None
            
            # Name fields (optional for destinatario)
            normalized['razao_social'] = raw_data.get('razao_social', '').strip()[:60] or None
            normalized['nome_fantasia'] = raw_data.get('nome_fantasia', '').strip()[:60] or None
            
            # Address fields (all optional for destinatario)
            normalized['logradouro'] = raw_data.get('logradouro', '').strip()[:60] or None
            normalized['numero'] = raw_data.get('numero', '').strip()[:60] or None
            normalized['complemento'] = raw_data.get('complemento', '').strip()[:60] or None
            normalized['bairro'] = raw_data.get('bairro', '').strip()[:60] or None
            normalized['codigo_municipio'] = raw_data.get('codigo_municipio', '').strip()[:7] or None
            normalized['nome_municipio'] = raw_data.get('nome_municipio', '').strip()[:60] or None
            
            # UF validation (optional)
            uf = raw_data.get('uf', '').strip().upper()
            if uf and uf in self.validador.UFS_VALIDAS:
                normalized['uf'] = uf
            else:
                normalized['uf'] = None
                if uf:
                    logger.warning("Invalid UF for destinatario", uf=uf)
            
            # CEP formatting (optional)
            cep = raw_data.get('cep', '').strip()
            if cep:
                cep_clean = re.sub(r'[^0-9]', '', cep)
                if len(cep_clean) == 8:
                    normalized['cep'] = self.formatador.formatar_documento(cep_clean, 'cep')
                else:
                    normalized['cep'] = None
                    logger.warning("Invalid CEP length for destinatario", cep=cep)
            else:
                normalized['cep'] = None
            
            # Country data
            normalized['codigo_pais'] = raw_data.get('codigo_pais', '1058').strip()[:4]
            normalized['nome_pais'] = raw_data.get('nome_pais', 'Brasil').strip()[:60]
            
            # Contact data (optional)
            telefone = raw_data.get('telefone', '').strip()
            if telefone:
                telefone_clean = re.sub(r'[^0-9]', '', telefone)
                if len(telefone_clean) >= 10:
                    normalized['telefone'] = self.formatador.formatar_documento(telefone_clean, 'telefone')
                else:
                    normalized['telefone'] = None
                    logger.warning("Invalid telefone length for destinatario", telefone=telefone)
            else:
                normalized['telefone'] = None
            
            # Email validation (basic, optional)
            email = raw_data.get('email', '').strip()
            if email and '@' in email and '.' in email:
                normalized['email'] = email[:60]
            else:
                normalized['email'] = None
                if email:
                    logger.warning("Invalid email format for destinatario", email=email)
            
            # Validate address if present (optional validation)
            if any(normalized.get(field) for field in ['logradouro', 'bairro', 'nome_municipio', 'uf']):
                endereco_validation = self.validador.validar_endereco_brasileiro({
                    'logradouro': normalized.get('logradouro', ''),
                    'bairro': normalized.get('bairro', ''),
                    'nome_municipio': normalized.get('nome_municipio', ''),
                    'uf': normalized.get('uf', ''),
                    'cep': normalized.get('cep', ''),
                    'codigo_municipio': normalized.get('codigo_municipio', '')
                })
                
                if not endereco_validation['valido']:
                    logger.info(
                        "Destinatario address validation issues (non-critical)",
                        errors=endereco_validation['erros'],
                        warnings=endereco_validation['avisos']
                    )
            
            # Check if we have at least some identification
            has_identification = any([
                normalized.get('cnpj'),
                normalized.get('cpf'),
                normalized.get('id_estrangeiro'),
                normalized.get('razao_social')
            ])
            
            if not has_identification:
                logger.warning("Destinatario has no meaningful identification data")
                return None
            
            logger.info(
                "Destinatario data normalized",
                cnpj=normalized.get('cnpj'),
                cpf=normalized.get('cpf'),
                razao_social=normalized.get('razao_social')
            )
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize destinatario data", error=str(e))
            raise
    
    def handle_incomplete_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incomplete destinatario data with fallback strategies
        
        Args:
            raw_data: Raw extracted data that may be incomplete
            
        Returns:
            Processed data with fallbacks applied
        """
        try:
            processed_data = raw_data.copy()
            
            # If no name but has CNPJ/CPF, try to create a generic name
            if not processed_data.get('razao_social'):
                if processed_data.get('cnpj'):
                    processed_data['razao_social'] = f"Cliente CNPJ {processed_data['cnpj']}"
                elif processed_data.get('cpf'):
                    processed_data['razao_social'] = f"Cliente CPF {processed_data['cpf']}"
                elif processed_data.get('id_estrangeiro'):
                    processed_data['razao_social'] = f"Cliente Estrangeiro {processed_data['id_estrangeiro']}"
            
            # If no address but has municipality code, try to get basic location
            if not processed_data.get('nome_municipio') and processed_data.get('codigo_municipio'):
                # This could be enhanced with a municipality lookup table
                processed_data['nome_municipio'] = f"Município {processed_data['codigo_municipio']}"
            
            # Set default country if missing
            if not processed_data.get('codigo_pais'):
                processed_data['codigo_pais'] = '1058'
                processed_data['nome_pais'] = 'Brasil'
            
            logger.info(
                "Incomplete destinatario data handled with fallbacks",
                original_fields=len([k for k, v in raw_data.items() if v]),
                processed_fields=len([k for k, v in processed_data.items() if v])
            )
            
            return processed_data
            
        except Exception as e:
            logger.error("Failed to handle incomplete destinatario data", error=str(e))
            return raw_data
    
    def _validate_cnpj_digits(self, cnpj: str) -> bool:
        """Validate CNPJ check digits"""
        try:
            if len(cnpj) != 14:
                return False
            
            # Check for known invalid patterns
            if cnpj == cnpj[0] * 14:
                return False
            
            # Calculate first check digit
            weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            if int(cnpj[12]) != digit1:
                return False
            
            # Calculate second check digit
            weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            return int(cnpj[13]) == digit2
            
        except Exception as e:
            logger.error("CNPJ validation error", cnpj=cnpj, error=str(e))
            return False
    
    def _validate_cpf_digits(self, cpf: str) -> bool:
        """Validate CPF check digits"""
        try:
            if len(cpf) != 11:
                return False
            
            # Check for known invalid patterns
            if cpf == cpf[0] * 11:
                return False
            
            # Calculate first check digit
            sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
            remainder1 = sum1 % 11
            digit1 = 0 if remainder1 < 2 else 11 - remainder1
            
            if int(cpf[9]) != digit1:
                return False
            
            # Calculate second check digit
            sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
            remainder2 = sum2 % 11
            digit2 = 0 if remainder2 < 2 else 11 - remainder2
            
            return int(cpf[10]) == digit2
            
        except Exception as e:
            logger.error("CPF validation error", cpf=cpf, error=str(e))
            return False
    
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