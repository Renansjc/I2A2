"""
Comprehensive data validation utilities for Brazilian business data
Validação abrangente de dados empresariais brasileiros
"""

import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, validator
import structlog

logger = structlog.get_logger()

class ValidationError(Exception):
    """Erro de validação customizado"""
    def __init__(self, campo: str, valor: Any, mensagem: str, sugestao: Optional[str] = None):
        self.campo = campo
        self.valor = valor
        self.mensagem = mensagem
        self.sugestao = sugestao
        super().__init__(f"{campo}: {mensagem}")

class ValidationResult(BaseModel):
    """Resultado de validação"""
    valido: bool
    erros: List[Dict[str, Any]]
    avisos: List[Dict[str, Any]]
    dados_limpos: Optional[Dict[str, Any]] = None

class ValidadorDocumentosBrasileiros:
    """Validador para documentos brasileiros (CPF, CNPJ, etc.)"""
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        """Validar CPF brasileiro"""
        if not cpf:
            return False
            
        # Remove formatação
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
            
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
            
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cpf[9:11] == f"{digito1}{digito2}"
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:
        """Validar CNPJ brasileiro"""
        if not cnpj:
            return False
            
        # Remove formatação
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
            
        # Verifica se todos os dígitos são iguais
        if cnpj == cnpj[0] * 14:
            return False
            
        # Calcula primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return cnpj[12:14] == f"{digito1}{digito2}"
    
    @staticmethod
    def validar_cep(cep: str) -> bool:
        """Validar CEP brasileiro"""
        if not cep:
            return False
        
        # Remove formatação
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        # Verifica se tem 8 dígitos
        if len(cep_limpo) != 8:
            return False
            
        # Verifica se não é um CEP inválido conhecido
        ceps_invalidos = ['00000000', '11111111', '22222222', '33333333', 
                         '44444444', '55555555', '66666666', '77777777', 
                         '88888888', '99999999']
        
        return cep_limpo not in ceps_invalidos
    
    @staticmethod
    def validar_inscricao_estadual(ie: str, uf: str) -> bool:
        """Validar Inscrição Estadual por UF"""
        if not ie or not uf:
            return False
            
        # Remove formatação
        ie = re.sub(r'[^0-9]', '', ie)
        uf = uf.upper()
        
        # Implementação básica - pode ser expandida por UF
        if uf == 'SP':
            return len(ie) == 12
        elif uf == 'RJ':
            return len(ie) == 8
        elif uf == 'MG':
            return len(ie) == 13
        else:
            # Validação genérica para outros estados
            return 8 <= len(ie) <= 15

class ValidadorDadosFiscais:
    """Validador para dados fiscais brasileiros"""
    
    @staticmethod
    def validar_chave_nfe(chave: str) -> bool:
        """Validar chave de acesso da NF-e"""
        if not chave:
            return False
            
        # Remove formatação
        chave = re.sub(r'[^0-9]', '', chave)
        
        # Verifica se tem 44 dígitos
        if len(chave) != 44:
            return False
            
        # Validação do dígito verificador (algoritmo módulo 11)
        try:
            chave_sem_dv = chave[:43]
            dv_informado = int(chave[43])
            
            # Calcula dígito verificador
            soma = 0
            multiplicador = 2
            
            for i in range(42, -1, -1):
                soma += int(chave_sem_dv[i]) * multiplicador
                multiplicador += 1
                if multiplicador > 9:
                    multiplicador = 2
            
            resto = soma % 11
            dv_calculado = 0 if resto in [0, 1] else 11 - resto
            
            return dv_calculado == dv_informado
            
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def validar_ncm(ncm: str) -> bool:
        """Validar código NCM"""
        if not ncm:
            return False
            
        # Remove formatação
        ncm = re.sub(r'[^0-9]', '', ncm)
        
        # Verifica se tem 8 dígitos
        return len(ncm) == 8 and ncm.isdigit()
    
    @staticmethod
    def validar_cfop(cfop: str) -> bool:
        """Validar código CFOP"""
        if not cfop:
            return False
            
        # Remove formatação
        cfop = re.sub(r'[^0-9]', '', cfop)
        
        # Verifica se tem 4 dígitos
        if len(cfop) != 4 or not cfop.isdigit():
            return False
            
        # Verifica se o primeiro dígito é válido (1-7)
        primeiro_digito = int(cfop[0])
        return 1 <= primeiro_digito <= 7

class ValidadorDadosEmpresariais:
    """Validador para dados empresariais e financeiros"""
    
    @staticmethod
    def validar_valor_monetario(valor: Union[str, float, Decimal], minimo: float = 0) -> bool:
        """Validar valor monetário"""
        try:
            if isinstance(valor, str):
                # Remove formatação brasileira
                valor_limpo = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_decimal = Decimal(valor_limpo)
            else:
                valor_decimal = Decimal(str(valor))
                
            return valor_decimal >= Decimal(str(minimo))
            
        except (InvalidOperation, ValueError):
            return False
    
    @staticmethod
    def validar_data_brasileira(data: Union[str, datetime, date]) -> bool:
        """Validar data no formato brasileiro"""
        if isinstance(data, (datetime, date)):
            return True
            
        if not isinstance(data, str):
            return False
            
        # Formatos aceitos: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']
        
        for formato in formatos:
            try:
                datetime.strptime(data, formato)
                return True
            except ValueError:
                continue
                
        return False
    
    @staticmethod
    def validar_email(email: str) -> bool:
        """Validar endereço de email"""
        if not email:
            return False
            
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(padrao, email))
    
    @staticmethod
    def validar_telefone_brasileiro(telefone: str) -> bool:
        """Validar telefone brasileiro"""
        if not telefone:
            return False
            
        # Remove formatação
        telefone_limpo = re.sub(r'[^0-9]', '', telefone)
        
        # Verifica formatos válidos: 10 ou 11 dígitos (com ou sem DDD)
        return len(telefone_limpo) in [10, 11] and telefone_limpo.isdigit()

class ValidadorRegrasNegocio:
    """Validador para regras de negócio específicas"""
    
    @staticmethod
    def validar_periodo_fiscal(data_inicio: datetime, data_fim: datetime) -> ValidationResult:
        """Validar período fiscal"""
        erros = []
        avisos = []
        
        # Verifica se data fim é posterior à data início
        if data_fim <= data_inicio:
            erros.append({
                "campo": "periodo",
                "mensagem": "Data de fim deve ser posterior à data de início",
                "sugestao": "Verifique as datas informadas"
            })
        
        # Verifica se o período não é muito longo (mais de 5 anos)
        diferenca_anos = (data_fim - data_inicio).days / 365
        if diferenca_anos > 5:
            avisos.append({
                "campo": "periodo",
                "mensagem": "Período muito longo pode impactar performance",
                "sugestao": "Considere dividir a consulta em períodos menores"
            })
        
        # Verifica se as datas não são futuras
        agora = datetime.now()
        if data_inicio > agora or data_fim > agora:
            avisos.append({
                "campo": "periodo",
                "mensagem": "Período inclui datas futuras",
                "sugestao": "Verifique se as datas estão corretas"
            })
        
        return ValidationResult(
            valido=len(erros) == 0,
            erros=erros,
            avisos=avisos
        )
    
    @staticmethod
    def validar_consistencia_nfe(dados_nfe: Dict[str, Any]) -> ValidationResult:
        """Validar consistência de dados de NFE"""
        erros = []
        avisos = []
        
        try:
            # Verifica se valor total bate com soma dos itens
            valor_total = Decimal(str(dados_nfe.get('valor_total_nf', 0)))
            valor_produtos = Decimal(str(dados_nfe.get('valor_total_produtos', 0)))
            
            if abs(valor_total - valor_produtos) > Decimal('0.01'):
                avisos.append({
                    "campo": "valores",
                    "mensagem": "Divergência entre valor total e valor dos produtos",
                    "sugestao": "Verifique se há serviços ou outros valores incluídos"
                })
            
            # Verifica se CNPJ do fornecedor é válido
            cnpj_fornecedor = dados_nfe.get('fornecedor', {}).get('cnpj')
            if cnpj_fornecedor and not ValidadorDocumentosBrasileiros.validar_cnpj(cnpj_fornecedor):
                erros.append({
                    "campo": "fornecedor.cnpj",
                    "mensagem": "CNPJ do fornecedor inválido",
                    "sugestao": "Verifique se o CNPJ está correto"
                })
            
            # Verifica se chave NFE é válida
            chave_nfe = dados_nfe.get('chave_nfe')
            if chave_nfe and not ValidadorDadosFiscais.validar_chave_nfe(chave_nfe):
                erros.append({
                    "campo": "chave_nfe",
                    "mensagem": "Chave de acesso da NFE inválida",
                    "sugestao": "Verifique se a chave está completa e correta"
                })
            
        except Exception as e:
            erros.append({
                "campo": "geral",
                "mensagem": f"Erro na validação de consistência: {str(e)}",
                "sugestao": "Verifique a estrutura dos dados"
            })
        
        return ValidationResult(
            valido=len(erros) == 0,
            erros=erros,
            avisos=avisos
        )

class ValidadorCompleto:
    """Validador completo que combina todas as validações"""
    
    def __init__(self):
        self.doc_validator = ValidadorDocumentosBrasileiros()
        self.fiscal_validator = ValidadorDadosFiscais()
        self.business_validator = ValidadorDadosEmpresariais()
        self.rules_validator = ValidadorRegrasNegocio()
    
    def validar_dados_completos(self, dados: Dict[str, Any], tipo_validacao: str = "geral") -> ValidationResult:
        """Validação completa de dados"""
        erros = []
        avisos = []
        dados_limpos = {}
        
        try:
            if tipo_validacao == "nfe":
                resultado = self.rules_validator.validar_consistencia_nfe(dados)
                erros.extend(resultado.erros)
                avisos.extend(resultado.avisos)
            
            elif tipo_validacao == "consulta":
                if 'periodo_inicio' in dados and 'periodo_fim' in dados:
                    resultado = self.rules_validator.validar_periodo_fiscal(
                        dados['periodo_inicio'], 
                        dados['periodo_fim']
                    )
                    erros.extend(resultado.erros)
                    avisos.extend(resultado.avisos)
            
            # Validações gerais
            for campo, valor in dados.items():
                if 'cnpj' in campo.lower() and valor:
                    if not self.doc_validator.validar_cnpj(str(valor)):
                        erros.append({
                            "campo": campo,
                            "mensagem": "CNPJ inválido",
                            "sugestao": "Verifique se o CNPJ está no formato correto"
                        })
                
                elif 'cpf' in campo.lower() and valor:
                    if not self.doc_validator.validar_cpf(str(valor)):
                        erros.append({
                            "campo": campo,
                            "mensagem": "CPF inválido",
                            "sugestao": "Verifique se o CPF está no formato correto"
                        })
                
                elif 'email' in campo.lower() and valor:
                    if not self.business_validator.validar_email(str(valor)):
                        erros.append({
                            "campo": campo,
                            "mensagem": "Email inválido",
                            "sugestao": "Verifique se o email está no formato correto"
                        })
                
                elif 'valor' in campo.lower() and valor is not None:
                    if not self.business_validator.validar_valor_monetario(valor):
                        erros.append({
                            "campo": campo,
                            "mensagem": "Valor monetário inválido",
                            "sugestao": "Verifique se o valor está no formato correto"
                        })
                
                # Limpar e formatar dados
                dados_limpos[campo] = self._limpar_campo(campo, valor)
        
        except Exception as e:
            logger.error("Erro na validação completa", error=str(e))
            erros.append({
                "campo": "geral",
                "mensagem": f"Erro interno na validação: {str(e)}",
                "sugestao": "Contate o suporte técnico"
            })
        
        return ValidationResult(
            valido=len(erros) == 0,
            erros=erros,
            avisos=avisos,
            dados_limpos=dados_limpos if dados_limpos else None
        )
    
    def _limpar_campo(self, campo: str, valor: Any) -> Any:
        """Limpar e formatar campo específico"""
        if valor is None:
            return valor
            
        try:
            # Limpar documentos
            if any(doc in campo.lower() for doc in ['cnpj', 'cpf']):
                return re.sub(r'[^0-9]', '', str(valor))
            
            # Limpar CEP
            elif 'cep' in campo.lower():
                return re.sub(r'[^0-9]', '', str(valor))
            
            # Limpar telefone
            elif 'telefone' in campo.lower():
                return re.sub(r'[^0-9]', '', str(valor))
            
            # Limpar valores monetários
            elif 'valor' in campo.lower() and isinstance(valor, str):
                return valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
            
            return valor
            
        except Exception:
            return valor

# Instância global do validador
validador = ValidadorCompleto()