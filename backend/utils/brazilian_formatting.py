"""
Brazilian data formatting utilities
Utilitários de formatação de dados brasileiros
"""

import re
from typing import Union, Optional, Dict, Any
from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP
import locale
import pytz
import structlog

logger = structlog.get_logger()

class FormatadorBrasileiro:
    """Formatador para dados brasileiros"""
    
    # Timezone brasileiro
    TIMEZONE_BRASIL = pytz.timezone('America/Sao_Paulo')
    
    # Configurações de locale brasileiro
    LOCALE_BRASIL = 'pt_BR.UTF-8'
    
    def __init__(self):
        """Inicializar formatador brasileiro"""
        try:
            # Tentar configurar locale brasileiro
            locale.setlocale(locale.LC_ALL, self.LOCALE_BRASIL)
        except locale.Error:
            try:
                # Fallback para configurações alternativas
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
            except locale.Error:
                logger.warning("Não foi possível configurar locale brasileiro")
    
    @classmethod
    def formatar_moeda(cls, valor: Union[str, float, Decimal], incluir_simbolo: bool = True) -> str:
        """Formatar valor monetário no padrão brasileiro"""
        try:
            # Converter para Decimal para precisão
            if isinstance(valor, str):
                # Limpar formatação existente
                valor_limpo = valor.replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_decimal = Decimal(valor_limpo)
            else:
                valor_decimal = Decimal(str(valor))
            
            # Arredondar para 2 casas decimais
            valor_arredondado = valor_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Formatar com separadores brasileiros
            valor_str = f"{valor_arredondado:.2f}"
            partes = valor_str.split('.')
            
            # Adicionar separadores de milhares
            parte_inteira = partes[0]
            parte_decimal = partes[1]
            
            # Inverter para adicionar pontos a cada 3 dígitos
            parte_inteira_invertida = parte_inteira[::-1]
            grupos = [parte_inteira_invertida[i:i+3] for i in range(0, len(parte_inteira_invertida), 3)]
            parte_inteira_formatada = '.'.join(grupos)[::-1]
            
            # Montar valor final
            valor_formatado = f"{parte_inteira_formatada},{parte_decimal}"
            
            if incluir_simbolo:
                return f"R$ {valor_formatado}"
            else:
                return valor_formatado
                
        except (ValueError, TypeError, ArithmeticError) as e:
            logger.error("Erro ao formatar moeda", valor=valor, erro=str(e))
            return "R$ 0,00" if incluir_simbolo else "0,00"
    
    @classmethod
    def formatar_numero(cls, numero: Union[str, int, float, Decimal], casas_decimais: int = 2) -> str:
        """Formatar número no padrão brasileiro"""
        try:
            if isinstance(numero, str):
                numero_limpo = numero.replace('.', '').replace(',', '.').strip()
                numero_decimal = Decimal(numero_limpo)
            else:
                numero_decimal = Decimal(str(numero))
            
            # Arredondar para o número de casas decimais especificado
            if casas_decimais > 0:
                fator_arredondamento = Decimal('0.' + '0' * (casas_decimais - 1) + '1')
                numero_arredondado = numero_decimal.quantize(fator_arredondamento, rounding=ROUND_HALF_UP)
                numero_str = f"{numero_arredondado:.{casas_decimais}f}"
            else:
                numero_arredondado = numero_decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                numero_str = str(int(numero_arredondado))
                return cls._adicionar_separadores_milhares(numero_str)
            
            # Separar parte inteira e decimal
            partes = numero_str.split('.')
            parte_inteira = partes[0]
            parte_decimal = partes[1] if len(partes) > 1 else '0' * casas_decimais
            
            # Formatar parte inteira com separadores
            parte_inteira_formatada = cls._adicionar_separadores_milhares(parte_inteira)
            
            return f"{parte_inteira_formatada},{parte_decimal}"
            
        except (ValueError, TypeError, ArithmeticError) as e:
            logger.error("Erro ao formatar número", numero=numero, erro=str(e))
            return "0" + (",00" if casas_decimais > 0 else "")
    
    @classmethod
    def _adicionar_separadores_milhares(cls, numero_str: str) -> str:
        """Adicionar separadores de milhares (pontos)"""
        numero_invertido = numero_str[::-1]
        grupos = [numero_invertido[i:i+3] for i in range(0, len(numero_invertido), 3)]
        return '.'.join(grupos)[::-1]
    
    @classmethod
    def formatar_data(cls, data: Union[str, datetime, date], formato: str = "dd/mm/aaaa") -> str:
        """Formatar data no padrão brasileiro"""
        try:
            # Converter para datetime se necessário
            if isinstance(data, str):
                # Tentar diferentes formatos de entrada
                formatos_entrada = [
                    '%Y-%m-%d',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%d/%m/%Y',
                    '%d/%m/%Y %H:%M:%S'
                ]
                
                data_obj = None
                for fmt in formatos_entrada:
                    try:
                        data_obj = datetime.strptime(data, fmt)
                        break
                    except ValueError:
                        continue
                
                if data_obj is None:
                    raise ValueError(f"Formato de data não reconhecido: {data}")
                    
            elif isinstance(data, date) and not isinstance(data, datetime):
                data_obj = datetime.combine(data, datetime.min.time())
            else:
                data_obj = data
            
            # Converter para timezone brasileiro se necessário
            if data_obj.tzinfo is None:
                data_obj = cls.TIMEZONE_BRASIL.localize(data_obj)
            else:
                data_obj = data_obj.astimezone(cls.TIMEZONE_BRASIL)
            
            # Aplicar formato solicitado
            if formato == "dd/mm/aaaa":
                return data_obj.strftime("%d/%m/%Y")
            elif formato == "dd/mm/aaaa hh:mm":
                return data_obj.strftime("%d/%m/%Y %H:%M")
            elif formato == "dd/mm/aaaa hh:mm:ss":
                return data_obj.strftime("%d/%m/%Y %H:%M:%S")
            elif formato == "dd de mmmm de aaaa":
                meses = [
                    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
                ]
                mes_nome = meses[data_obj.month - 1]
                return f"{data_obj.day} de {mes_nome} de {data_obj.year}"
            elif formato == "extenso":
                dias_semana = [
                    'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira',
                    'sexta-feira', 'sábado', 'domingo'
                ]
                meses = [
                    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
                ]
                dia_semana = dias_semana[data_obj.weekday()]
                mes_nome = meses[data_obj.month - 1]
                return f"{dia_semana}, {data_obj.day} de {mes_nome} de {data_obj.year}"
            else:
                # Formato personalizado
                return data_obj.strftime(formato)
                
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Erro ao formatar data", data=data, formato=formato, erro=str(e))
            return "Data inválida"
    
    @classmethod
    def formatar_documento(cls, documento: str, tipo: str = "auto") -> str:
        """Formatar documento brasileiro (CPF, CNPJ, etc.)"""
        try:
            # Limpar documento
            doc_limpo = re.sub(r'[^0-9]', '', str(documento))
            
            if not doc_limpo:
                return documento
            
            # Detectar tipo automaticamente se não especificado
            if tipo == "auto":
                if len(doc_limpo) == 11:
                    tipo = "cpf"
                elif len(doc_limpo) == 14:
                    tipo = "cnpj"
                else:
                    return documento
            
            # Formatar baseado no tipo
            if tipo == "cpf" and len(doc_limpo) == 11:
                return f"{doc_limpo[:3]}.{doc_limpo[3:6]}.{doc_limpo[6:9]}-{doc_limpo[9:]}"
            elif tipo == "cnpj" and len(doc_limpo) == 14:
                return f"{doc_limpo[:2]}.{doc_limpo[2:5]}.{doc_limpo[5:8]}/{doc_limpo[8:12]}-{doc_limpo[12:]}"
            elif tipo == "cep" and len(doc_limpo) == 8:
                return f"{doc_limpo[:5]}-{doc_limpo[5:]}"
            elif tipo == "telefone":
                if len(doc_limpo) == 10:
                    return f"({doc_limpo[:2]}) {doc_limpo[2:6]}-{doc_limpo[6:]}"
                elif len(doc_limpo) == 11:
                    return f"({doc_limpo[:2]}) {doc_limpo[2:7]}-{doc_limpo[7:]}"
            
            return documento
            
        except Exception as e:
            logger.error("Erro ao formatar documento", documento=documento, tipo=tipo, erro=str(e))
            return documento
    
    @classmethod
    def formatar_endereco(cls, endereco: Dict[str, Any]) -> str:
        """Formatar endereço brasileiro"""
        try:
            partes = []
            
            # Logradouro e número
            logradouro = endereco.get('logradouro', '').strip()
            numero = endereco.get('numero', '').strip()
            if logradouro:
                if numero:
                    partes.append(f"{logradouro}, {numero}")
                else:
                    partes.append(logradouro)
            
            # Complemento
            complemento = endereco.get('complemento', '').strip()
            if complemento:
                partes.append(complemento)
            
            # Bairro
            bairro = endereco.get('bairro', '').strip()
            if bairro:
                partes.append(bairro)
            
            # Cidade e UF
            cidade = endereco.get('nome_municipio', '').strip()
            uf = endereco.get('uf', '').strip()
            if cidade and uf:
                partes.append(f"{cidade}/{uf}")
            elif cidade:
                partes.append(cidade)
            
            # CEP
            cep = endereco.get('cep', '').strip()
            if cep:
                cep_formatado = cls.formatar_documento(cep, 'cep')
                partes.append(f"CEP: {cep_formatado}")
            
            return ' - '.join(partes) if partes else 'Endereço não informado'
            
        except Exception as e:
            logger.error("Erro ao formatar endereço", endereco=endereco, erro=str(e))
            return 'Endereço inválido'
    
    @classmethod
    def formatar_porcentagem(cls, valor: Union[str, float, Decimal], casas_decimais: int = 2) -> str:
        """Formatar porcentagem no padrão brasileiro"""
        try:
            if isinstance(valor, str):
                valor_limpo = valor.replace('%', '').replace(',', '.').strip()
                valor_decimal = Decimal(valor_limpo)
            else:
                valor_decimal = Decimal(str(valor))
            
            # Arredondar
            if casas_decimais > 0:
                fator_arredondamento = Decimal('0.' + '0' * (casas_decimais - 1) + '1')
                valor_arredondado = valor_decimal.quantize(fator_arredondamento, rounding=ROUND_HALF_UP)
                valor_formatado = f"{valor_arredondado:.{casas_decimais}f}".replace('.', ',')
            else:
                valor_arredondado = valor_decimal.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                valor_formatado = str(int(valor_arredondado))
            
            return f"{valor_formatado}%"
            
        except (ValueError, TypeError, ArithmeticError) as e:
            logger.error("Erro ao formatar porcentagem", valor=valor, erro=str(e))
            return "0,00%"

class ConversorTimezoneBrasil:
    """Conversor de timezone para horário brasileiro"""
    
    TIMEZONE_BRASIL = pytz.timezone('America/Sao_Paulo')
    
    @classmethod
    def converter_para_brasil(cls, data: datetime) -> datetime:
        """Converter datetime para timezone brasileiro"""
        try:
            if data.tzinfo is None:
                # Se não tem timezone, assumir UTC
                data_utc = pytz.UTC.localize(data)
            else:
                data_utc = data.astimezone(pytz.UTC)
            
            return data_utc.astimezone(cls.TIMEZONE_BRASIL)
            
        except Exception as e:
            logger.error("Erro ao converter timezone", data=data, erro=str(e))
            return data
    
    @classmethod
    def obter_agora_brasil(cls) -> datetime:
        """Obter datetime atual no timezone brasileiro"""
        return datetime.now(cls.TIMEZONE_BRASIL)
    
    @classmethod
    def formatar_timezone_brasil(cls, data: datetime) -> str:
        """Formatar datetime com timezone brasileiro"""
        data_brasil = cls.converter_para_brasil(data)
        return data_brasil.strftime("%d/%m/%Y %H:%M:%S %Z")

class ValidadorDadosBrasileiros:
    """Validador específico para dados brasileiros"""
    
    @staticmethod
    def validar_formato_brasileiro(dados: Dict[str, Any]) -> Dict[str, Any]:
        """Validar e formatar dados no padrão brasileiro"""
        dados_formatados = {}
        
        for chave, valor in dados.items():
            try:
                # Formatar valores monetários
                if any(palavra in chave.lower() for palavra in ['valor', 'preco', 'custo', 'total']):
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_moeda(valor)
                    else:
                        dados_formatados[chave] = valor
                
                # Formatar datas
                elif any(palavra in chave.lower() for palavra in ['data', 'timestamp']):
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_data(valor)
                    else:
                        dados_formatados[chave] = valor
                
                # Formatar documentos
                elif 'cnpj' in chave.lower():
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_documento(valor, 'cnpj')
                    else:
                        dados_formatados[chave] = valor
                
                elif 'cpf' in chave.lower():
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_documento(valor, 'cpf')
                    else:
                        dados_formatados[chave] = valor
                
                elif 'cep' in chave.lower():
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_documento(valor, 'cep')
                    else:
                        dados_formatados[chave] = valor
                
                elif 'telefone' in chave.lower():
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_documento(valor, 'telefone')
                    else:
                        dados_formatados[chave] = valor
                
                # Formatar porcentagens
                elif any(palavra in chave.lower() for palavra in ['aliquota', 'percentual', 'taxa']):
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_porcentagem(valor)
                    else:
                        dados_formatados[chave] = valor
                
                # Formatar números
                elif any(palavra in chave.lower() for palavra in ['quantidade', 'numero']):
                    if valor is not None:
                        dados_formatados[chave] = FormatadorBrasileiro.formatar_numero(valor, 2)
                    else:
                        dados_formatados[chave] = valor
                
                else:
                    dados_formatados[chave] = valor
                    
            except Exception as e:
                logger.warning("Erro ao formatar campo", chave=chave, valor=valor, erro=str(e))
                dados_formatados[chave] = valor
        
        return dados_formatados

# Instâncias globais
formatador_brasileiro = FormatadorBrasileiro()
conversor_timezone = ConversorTimezoneBrasil()
validador_dados_br = ValidadorDadosBrasileiros()