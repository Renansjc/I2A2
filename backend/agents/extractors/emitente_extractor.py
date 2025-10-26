"""
EmitenteExtractor for extracting supplier data from fiscal documents
Extrator de dados de emitente para documentos fiscais brasileiros
"""

import structlog
from typing import Dict, Any, Optional
from lxml import etree
import re

from utils.brazilian_business_validation import ValidadorNegociosBrasil
from utils.brazilian_formatting import FormatadorBrasileiro

logger = structlog.get_logger()


class EmitenteExtractor:
    """Specialized extractor for emitente (supplier) data from fiscal documents"""
    
    def __init__(self):
        self.validador = ValidadorNegociosBrasil()
        self.formatador = FormatadorBrasileiro()
    
    def extract_from_nfe(self, xml_root) -> Dict[str, Any]:
        """
        Extract emitente data from NF-e XML using correct namespace
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            Dict containing extracted emitente data
        """
        try:
            # NF-e namespace
            nfe_ns = "http://www.portalfiscal.inf.br/nfe"
            
            # Find emitente element
            emit = xml_root.find(f'.//{{{nfe_ns}}}emit')
            if emit is None:
                logger.warning("No emitente element found in NF-e")
                return {}
            
            # Extract basic identification data
            emitente_data = {
                'cnpj': self._get_text(emit, f'.//{{{nfe_ns}}}CNPJ'),
                'cpf': self._get_text(emit, f'.//{{{nfe_ns}}}CPF'),
                'inscricao_estadual': self._get_text(emit, f'.//{{{nfe_ns}}}IE'),
                'razao_social': self._get_text(emit, f'.//{{{nfe_ns}}}xNome'),
                'nome_fantasia': self._get_text(emit, f'.//{{{nfe_ns}}}xFant'),
                'regime_tributario': self._get_text(emit, f'.//{{{nfe_ns}}}CRT')
            }
            
            # Extract address data
            endereco_data = self._extract_endereco_nfe(emit, nfe_ns)
            emitente_data.update(endereco_data)
            
            # Extract contact data
            contato_data = self._extract_contato_nfe(emit, nfe_ns)
            emitente_data.update(contato_data)
            
            logger.info(
                "Emitente data extracted from NF-e",
                cnpj=emitente_data.get('cnpj'),
                razao_social=emitente_data.get('razao_social')
            )
            
            return emitente_data
            
        except Exception as e:
            logger.error("Failed to extract emitente data from NF-e", error=str(e))
            return {}
    
    def extract_from_nfse(self, xml_root) -> Dict[str, Any]:
        """
        Extract emitente (prestador) data from NFS-e XML
        
        Args:
            xml_root: Parsed XML root element
            
        Returns:
            Dict containing extracted emitente data
        """
        try:
            # NFS-e can have different schemas depending on municipality
            # This implementation covers common patterns
            
            # Try different common element names for prestador
            prestador_elements = [
                './/PrestadorServico',
                './/Prestador',
                './/prestador',
                './/IdentificacaoPrestador'
            ]
            
            prestador = None
            for element_path in prestador_elements:
                prestador = xml_root.find(element_path)
                if prestador is not None:
                    break
            
            if prestador is None:
                logger.warning("No prestador element found in NFS-e")
                return {}
            
            # Extract basic identification data
            emitente_data = {
                'cnpj': self._get_text_multiple_paths(prestador, [
                    './/Cnpj', './/CNPJ', './/cnpj'
                ]),
                'cpf': self._get_text_multiple_paths(prestador, [
                    './/Cpf', './/CPF', './/cpf'
                ]),
                'inscricao_estadual': self._get_text_multiple_paths(prestador, [
                    './/InscricaoEstadual', './/IE', './/ie'
                ]),
                'razao_social': self._get_text_multiple_paths(prestador, [
                    './/RazaoSocial', './/razaoSocial', './/xNome', './/Nome'
                ]),
                'nome_fantasia': self._get_text_multiple_paths(prestador, [
                    './/NomeFantasia', './/nomeFantasia', './/xFant'
                ]),
                'inscricao_municipal': self._get_text_multiple_paths(prestador, [
                    './/InscricaoMunicipal', './/IM', './/im'
                ])
            }
            
            # Extract address data for NFS-e
            endereco_data = self._extract_endereco_nfse(prestador)
            emitente_data.update(endereco_data)
            
            # Extract contact data for NFS-e
            contato_data = self._extract_contato_nfse(prestador)
            emitente_data.update(contato_data)
            
            logger.info(
                "Emitente data extracted from NFS-e",
                cnpj=emitente_data.get('cnpj'),
                razao_social=emitente_data.get('razao_social')
            )
            
            return emitente_data
            
        except Exception as e:
            logger.error("Failed to extract emitente data from NFS-e", error=str(e))
            return {}
    
    def _extract_endereco_nfe(self, emit_element, namespace: str) -> Dict[str, Any]:
        """Extract address data from NF-e emitente element"""
        try:
            endereco_data = {
                'logradouro': self._get_text(emit_element, f'.//{{{namespace}}}xLgr'),
                'numero': self._get_text(emit_element, f'.//{{{namespace}}}nro'),
                'complemento': self._get_text(emit_element, f'.//{{{namespace}}}xCpl'),
                'bairro': self._get_text(emit_element, f'.//{{{namespace}}}xBairro'),
                'codigo_municipio': self._get_text(emit_element, f'.//{{{namespace}}}cMun'),
                'nome_municipio': self._get_text(emit_element, f'.//{{{namespace}}}xMun'),
                'uf': self._get_text(emit_element, f'.//{{{namespace}}}UF'),
                'cep': self._get_text(emit_element, f'.//{{{namespace}}}CEP'),
                'codigo_pais': self._get_text(emit_element, f'.//{{{namespace}}}cPais'),
                'nome_pais': self._get_text(emit_element, f'.//{{{namespace}}}xPais')
            }
            
            # Set default values for Brazil if not present
            if not endereco_data['codigo_pais']:
                endereco_data['codigo_pais'] = '1058'
            if not endereco_data['nome_pais']:
                endereco_data['nome_pais'] = 'Brasil'
            
            return endereco_data
            
        except Exception as e:
            logger.error("Failed to extract endereco from NF-e", error=str(e))
            return {}
    
    def _extract_endereco_nfse(self, prestador_element) -> Dict[str, Any]:
        """Extract address data from NFS-e prestador element"""
        try:
            # Try to find endereco element
            endereco_elements = [
                './/Endereco', './/endereco', './/EnderecoCompleto'
            ]
            
            endereco = None
            for element_path in endereco_elements:
                endereco = prestador_element.find(element_path)
                if endereco is not None:
                    break
            
            if endereco is None:
                # Try to extract directly from prestador element
                endereco = prestador_element
            
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
            logger.error("Failed to extract endereco from NFS-e", error=str(e))
            return {}
    
    def _extract_contato_nfe(self, emit_element, namespace: str) -> Dict[str, Any]:
        """Extract contact data from NF-e emitente element"""
        try:
            contato_data = {
                'telefone': self._get_text(emit_element, f'.//{{{namespace}}}fone'),
                'email': self._get_text(emit_element, f'.//{{{namespace}}}email')
            }
            
            return contato_data
            
        except Exception as e:
            logger.error("Failed to extract contato from NF-e", error=str(e))
            return {}
    
    def _extract_contato_nfse(self, prestador_element) -> Dict[str, Any]:
        """Extract contact data from NFS-e prestador element"""
        try:
            contato_data = {
                'telefone': self._get_text_multiple_paths(prestador_element, [
                    './/Telefone', './/telefone', './/fone'
                ]),
                'email': self._get_text_multiple_paths(prestador_element, [
                    './/Email', './/email', './/Email'
                ])
            }
            
            return contato_data
            
        except Exception as e:
            logger.error("Failed to extract contato from NFS-e", error=str(e))
            return {}
    
    def normalize_emitente_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize emitente data for database insertion
        
        Args:
            raw_data: Raw extracted data
            
        Returns:
            Normalized and validated data
        """
        try:
            normalized = {}
            
            # Validate and format CNPJ/CPF
            cnpj = raw_data.get('cnpj', '').strip()
            cpf = raw_data.get('cpf', '').strip()
            
            if cnpj:
                cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
                if len(cnpj_clean) == 14:
                    normalized['cnpj'] = self.formatador.formatar_documento(cnpj_clean, 'cnpj')
                else:
                    logger.warning("Invalid CNPJ length", cnpj=cnpj)
                    
            elif cpf:
                cpf_clean = re.sub(r'[^0-9]', '', cpf)
                if len(cpf_clean) == 11:
                    normalized['cnpj'] = self.formatador.formatar_documento(cpf_clean, 'cpf')
                    normalized['cpf'] = self.formatador.formatar_documento(cpf_clean, 'cpf')
                else:
                    logger.warning("Invalid CPF length", cpf=cpf)
            
            if not normalized.get('cnpj'):
                raise ValueError("Valid CNPJ or CPF is required for emitente")
            
            # Required fields with length limits
            normalized['razao_social'] = raw_data.get('razao_social', '').strip()[:60]
            if not normalized['razao_social']:
                raise ValueError("Razão social is required for emitente")
            
            # Optional fields with length limits and validation
            normalized['nome_fantasia'] = raw_data.get('nome_fantasia', '').strip()[:60] or None
            normalized['inscricao_estadual'] = raw_data.get('inscricao_estadual', '').strip()[:14] or None
            normalized['inscricao_municipal'] = raw_data.get('inscricao_municipal', '').strip()[:15] or None
            
            # Address fields
            normalized['logradouro'] = raw_data.get('logradouro', '').strip()[:60] or None
            normalized['numero'] = raw_data.get('numero', '').strip()[:60] or None
            normalized['complemento'] = raw_data.get('complemento', '').strip()[:60] or None
            normalized['bairro'] = raw_data.get('bairro', '').strip()[:60] or None
            normalized['codigo_municipio'] = raw_data.get('codigo_municipio', '').strip()[:7] or None
            normalized['nome_municipio'] = raw_data.get('nome_municipio', '').strip()[:60] or None
            
            # UF validation
            uf = raw_data.get('uf', '').strip().upper()
            if uf and uf in self.validador.UFS_VALIDAS:
                normalized['uf'] = uf
            else:
                normalized['uf'] = None
                if uf:
                    logger.warning("Invalid UF", uf=uf)
            
            # CEP formatting
            cep = raw_data.get('cep', '').strip()
            if cep:
                cep_clean = re.sub(r'[^0-9]', '', cep)
                if len(cep_clean) == 8:
                    normalized['cep'] = self.formatador.formatar_documento(cep_clean, 'cep')
                else:
                    normalized['cep'] = None
                    logger.warning("Invalid CEP length", cep=cep)
            else:
                normalized['cep'] = None
            
            # Country data
            normalized['codigo_pais'] = raw_data.get('codigo_pais', '1058').strip()[:4]
            normalized['nome_pais'] = raw_data.get('nome_pais', 'Brasil').strip()[:60]
            
            # Contact data
            telefone = raw_data.get('telefone', '').strip()
            if telefone:
                telefone_clean = re.sub(r'[^0-9]', '', telefone)
                if len(telefone_clean) >= 10:
                    normalized['telefone'] = self.formatador.formatar_documento(telefone_clean, 'telefone')
                else:
                    normalized['telefone'] = None
                    logger.warning("Invalid telefone length", telefone=telefone)
            else:
                normalized['telefone'] = None
            
            # Email validation (basic)
            email = raw_data.get('email', '').strip()
            if email and '@' in email and '.' in email:
                normalized['email'] = email[:60]
            else:
                normalized['email'] = None
                if email:
                    logger.warning("Invalid email format", email=email)
            
            # Tax regime validation
            regime = raw_data.get('regime_tributario', '').strip()
            if regime in ['1', '2', '3']:
                normalized['regime_tributario'] = regime
            else:
                normalized['regime_tributario'] = None
                if regime:
                    logger.warning("Invalid regime tributario", regime=regime)
            
            # Validate address if present
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
                    logger.warning(
                        "Address validation issues",
                        errors=endereco_validation['erros'],
                        warnings=endereco_validation['avisos']
                    )
            
            logger.info(
                "Emitente data normalized",
                cnpj=normalized.get('cnpj'),
                razao_social=normalized.get('razao_social')
            )
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize emitente data", error=str(e))
            raise
    
    def validate_cnpj_cpf(self, documento: str) -> bool:
        """
        Validate CNPJ or CPF using Brazilian business validation
        
        Args:
            documento: CNPJ or CPF string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            doc_clean = re.sub(r'[^0-9]', '', documento)
            
            if len(doc_clean) == 14:
                # Validate CNPJ
                return self._validate_cnpj_digits(doc_clean)
            elif len(doc_clean) == 11:
                # Validate CPF
                return self._validate_cpf_digits(doc_clean)
            else:
                return False
                
        except Exception as e:
            logger.error("Failed to validate CNPJ/CPF", documento=documento, error=str(e))
            return False
    
    def _validate_cnpj_digits(self, cnpj: str) -> bool:
        """Validate CNPJ check digits"""
        try:
            # CNPJ validation algorithm
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
            # CPF validation algorithm
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