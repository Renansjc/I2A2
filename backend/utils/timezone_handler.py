"""
Timezone handling for Brazilian business data
Manipulação de timezone para dados empresariais brasileiros
"""

import pytz
from datetime import datetime, date, time, timezone, timedelta
from typing import Union, Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class GerenciadorTimezoneBrasil:
    """Gerenciador de timezone para o Brasil"""
    
    # Timezones brasileiros
    TIMEZONE_SAO_PAULO = pytz.timezone('America/Sao_Paulo')
    TIMEZONE_MANAUS = pytz.timezone('America/Manaus')
    TIMEZONE_BELEM = pytz.timezone('America/Belem')
    TIMEZONE_FORTALEZA = pytz.timezone('America/Fortaleza')
    TIMEZONE_RECIFE = pytz.timezone('America/Recife')
    TIMEZONE_BAHIA = pytz.timezone('America/Bahia')
    TIMEZONE_CUIABA = pytz.timezone('America/Cuiaba')
    TIMEZONE_PORTO_VELHO = pytz.timezone('America/Porto_Velho')
    TIMEZONE_BOA_VISTA = pytz.timezone('America/Boa_Vista')
    TIMEZONE_RIO_BRANCO = pytz.timezone('America/Rio_Branco')
    TIMEZONE_NORONHA = pytz.timezone('America/Noronha')
    
    # Timezone padrão (Brasília)
    TIMEZONE_PADRAO = TIMEZONE_SAO_PAULO
    
    # Mapeamento de UF para timezone
    UF_TIMEZONE_MAP = {
        'AC': TIMEZONE_RIO_BRANCO,      # Acre
        'AL': TIMEZONE_FORTALEZA,       # Alagoas
        'AP': TIMEZONE_FORTALEZA,       # Amapá
        'AM': TIMEZONE_MANAUS,          # Amazonas
        'BA': TIMEZONE_BAHIA,           # Bahia
        'CE': TIMEZONE_FORTALEZA,       # Ceará
        'DF': TIMEZONE_SAO_PAULO,       # Distrito Federal
        'ES': TIMEZONE_SAO_PAULO,       # Espírito Santo
        'GO': TIMEZONE_SAO_PAULO,       # Goiás
        'MA': TIMEZONE_FORTALEZA,       # Maranhão
        'MT': TIMEZONE_CUIABA,          # Mato Grosso
        'MS': TIMEZONE_CUIABA,          # Mato Grosso do Sul
        'MG': TIMEZONE_SAO_PAULO,       # Minas Gerais
        'PA': TIMEZONE_BELEM,           # Pará
        'PB': TIMEZONE_FORTALEZA,       # Paraíba
        'PR': TIMEZONE_SAO_PAULO,       # Paraná
        'PE': TIMEZONE_RECIFE,          # Pernambuco
        'PI': TIMEZONE_FORTALEZA,       # Piauí
        'RJ': TIMEZONE_SAO_PAULO,       # Rio de Janeiro
        'RN': TIMEZONE_FORTALEZA,       # Rio Grande do Norte
        'RS': TIMEZONE_SAO_PAULO,       # Rio Grande do Sul
        'RO': TIMEZONE_PORTO_VELHO,     # Rondônia
        'RR': TIMEZONE_BOA_VISTA,       # Roraima
        'SC': TIMEZONE_SAO_PAULO,       # Santa Catarina
        'SP': TIMEZONE_SAO_PAULO,       # São Paulo
        'SE': TIMEZONE_FORTALEZA,       # Sergipe
        'TO': TIMEZONE_FORTALEZA,       # Tocantins
        'FN': TIMEZONE_NORONHA,         # Fernando de Noronha
    }
    
    @classmethod
    def obter_timezone_por_uf(cls, uf: str) -> pytz.BaseTzInfo:
        """Obter timezone baseado na UF"""
        uf_upper = uf.upper() if uf else ''
        return cls.UF_TIMEZONE_MAP.get(uf_upper, cls.TIMEZONE_PADRAO)
    
    @classmethod
    def converter_para_timezone_uf(cls, data: datetime, uf: str) -> datetime:
        """Converter datetime para timezone da UF especificada"""
        try:
            timezone_uf = cls.obter_timezone_por_uf(uf)
            
            if data.tzinfo is None:
                # Se não tem timezone, assumir UTC
                data_utc = pytz.UTC.localize(data)
            else:
                data_utc = data.astimezone(pytz.UTC)
            
            return data_utc.astimezone(timezone_uf)
            
        except Exception as e:
            logger.error("Erro ao converter para timezone da UF", data=data, uf=uf, erro=str(e))
            return data
    
    @classmethod
    def converter_para_brasilia(cls, data: datetime) -> datetime:
        """Converter datetime para horário de Brasília"""
        return cls.converter_para_timezone_uf(data, 'DF')
    
    @classmethod
    def obter_agora_por_uf(cls, uf: str) -> datetime:
        """Obter datetime atual no timezone da UF"""
        timezone_uf = cls.obter_timezone_por_uf(uf)
        return datetime.now(timezone_uf)
    
    @classmethod
    def obter_agora_brasilia(cls) -> datetime:
        """Obter datetime atual em Brasília"""
        return datetime.now(cls.TIMEZONE_PADRAO)
    
    @classmethod
    def formatar_com_timezone(cls, data: datetime, uf: Optional[str] = None, formato: str = "%d/%m/%Y %H:%M:%S %Z") -> str:
        """Formatar datetime com timezone brasileiro"""
        try:
            if uf:
                data_formatada = cls.converter_para_timezone_uf(data, uf)
            else:
                data_formatada = cls.converter_para_brasilia(data)
            
            return data_formatada.strftime(formato)
            
        except Exception as e:
            logger.error("Erro ao formatar com timezone", data=data, uf=uf, erro=str(e))
            return str(data)
    
    @classmethod
    def calcular_diferenca_horario(cls, uf1: str, uf2: str, data: Optional[datetime] = None) -> timedelta:
        """Calcular diferença de horário entre duas UFs"""
        try:
            if data is None:
                data = datetime.now(pytz.UTC)
            elif data.tzinfo is None:
                data = pytz.UTC.localize(data)
            
            timezone1 = cls.obter_timezone_por_uf(uf1)
            timezone2 = cls.obter_timezone_por_uf(uf2)
            
            data_uf1 = data.astimezone(timezone1)
            data_uf2 = data.astimezone(timezone2)
            
            # Calcular diferença em segundos e converter para timedelta
            diferenca_segundos = (data_uf1.utcoffset() - data_uf2.utcoffset()).total_seconds()
            return timedelta(seconds=diferenca_segundos)
            
        except Exception as e:
            logger.error("Erro ao calcular diferença de horário", uf1=uf1, uf2=uf2, erro=str(e))
            return timedelta(0)
    
    @classmethod
    def eh_horario_comercial(cls, data: datetime, uf: str = 'SP') -> bool:
        """Verificar se é horário comercial (8h às 18h, segunda a sexta)"""
        try:
            data_local = cls.converter_para_timezone_uf(data, uf)
            
            # Verificar se é dia útil (segunda a sexta)
            if data_local.weekday() >= 5:  # 5 = sábado, 6 = domingo
                return False
            
            # Verificar se está no horário comercial (8h às 18h)
            hora = data_local.hour
            return 8 <= hora < 18
            
        except Exception as e:
            logger.error("Erro ao verificar horário comercial", data=data, uf=uf, erro=str(e))
            return False
    
    @classmethod
    def obter_proximo_dia_util(cls, data: datetime, uf: str = 'SP') -> datetime:
        """Obter próximo dia útil"""
        try:
            data_local = cls.converter_para_timezone_uf(data, uf)
            
            # Se é fim de semana, avançar para segunda
            while data_local.weekday() >= 5:
                data_local += timedelta(days=1)
            
            # Se passou do horário comercial, avançar para próximo dia útil
            if data_local.hour >= 18:
                data_local = data_local.replace(hour=8, minute=0, second=0, microsecond=0)
                data_local += timedelta(days=1)
                
                # Verificar novamente se não caiu em fim de semana
                while data_local.weekday() >= 5:
                    data_local += timedelta(days=1)
            
            return data_local
            
        except Exception as e:
            logger.error("Erro ao obter próximo dia útil", data=data, uf=uf, erro=str(e))
            return data

class ProcessadorDatasFiscais:
    """Processador específico para datas de documentos fiscais"""
    
    @classmethod
    def processar_data_emissao_nfe(cls, data_emissao: Union[str, datetime], uf_emitente: str) -> Dict[str, Any]:
        """Processar data de emissão de NF-e com timezone correto"""
        try:
            # Converter string para datetime se necessário
            if isinstance(data_emissao, str):
                # Formatos comuns de data em XML
                formatos = [
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S.%fZ',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d'
                ]
                
                data_obj = None
                for formato in formatos:
                    try:
                        data_obj = datetime.strptime(data_emissao, formato)
                        break
                    except ValueError:
                        continue
                
                if data_obj is None:
                    raise ValueError(f"Formato de data não reconhecido: {data_emissao}")
            else:
                data_obj = data_emissao
            
            # Converter para timezone da UF emitente
            data_local = GerenciadorTimezoneBrasil.converter_para_timezone_uf(data_obj, uf_emitente)
            data_brasilia = GerenciadorTimezoneBrasil.converter_para_brasilia(data_obj)
            data_utc = data_obj.astimezone(pytz.UTC) if data_obj.tzinfo else pytz.UTC.localize(data_obj)
            
            return {
                'data_original': data_emissao,
                'data_local': data_local,
                'data_brasilia': data_brasilia,
                'data_utc': data_utc,
                'timezone_local': str(data_local.tzinfo),
                'uf_emitente': uf_emitente,
                'formatado_local': data_local.strftime('%d/%m/%Y %H:%M:%S %Z'),
                'formatado_brasilia': data_brasilia.strftime('%d/%m/%Y %H:%M:%S %Z'),
                'eh_horario_comercial': GerenciadorTimezoneBrasil.eh_horario_comercial(data_local, uf_emitente)
            }
            
        except Exception as e:
            logger.error("Erro ao processar data de emissão", data=data_emissao, uf=uf_emitente, erro=str(e))
            return {
                'data_original': data_emissao,
                'erro': str(e),
                'data_fallback': GerenciadorTimezoneBrasil.obter_agora_brasilia()
            }
    
    @classmethod
    def validar_data_fiscal(cls, data: datetime, uf: str) -> Dict[str, Any]:
        """Validar data fiscal considerando regras brasileiras"""
        try:
            data_local = GerenciadorTimezoneBrasil.converter_para_timezone_uf(data, uf)
            agora_local = GerenciadorTimezoneBrasil.obter_agora_por_uf(uf)
            
            validacoes = {
                'data_valida': True,
                'avisos': [],
                'erros': []
            }
            
            # Verificar se não é muito no futuro (máximo 30 dias)
            if data_local > agora_local + timedelta(days=30):
                validacoes['erros'].append('Data muito no futuro (mais de 30 dias)')
                validacoes['data_valida'] = False
            
            # Verificar se não é muito no passado (máximo 5 anos para NF-e)
            if data_local < agora_local - timedelta(days=5*365):
                validacoes['avisos'].append('Data muito antiga (mais de 5 anos)')
            
            # Verificar se é fim de semana
            if data_local.weekday() >= 5:
                validacoes['avisos'].append('Data em fim de semana')
            
            # Verificar se é fora do horário comercial
            if not GerenciadorTimezoneBrasil.eh_horario_comercial(data_local, uf):
                validacoes['avisos'].append('Data fora do horário comercial')
            
            return validacoes
            
        except Exception as e:
            logger.error("Erro ao validar data fiscal", data=data, uf=uf, erro=str(e))
            return {
                'data_valida': False,
                'erros': [f'Erro na validação: {str(e)}'],
                'avisos': []
            }

class UtilitarioDatasBrasil:
    """Utilitários diversos para datas brasileiras"""
    
    FERIADOS_NACIONAIS_2024 = [
        (1, 1),   # Confraternização Universal
        (2, 12),  # Carnaval (exemplo - varia por ano)
        (2, 13),  # Carnaval (exemplo - varia por ano)
        (4, 21),  # Tiradentes
        (5, 1),   # Dia do Trabalhador
        (9, 7),   # Independência do Brasil
        (10, 12), # Nossa Senhora Aparecida
        (11, 2),  # Finados
        (11, 15), # Proclamação da República
        (12, 25), # Natal
    ]
    
    @classmethod
    def eh_feriado_nacional(cls, data: datetime) -> bool:
        """Verificar se é feriado nacional"""
        return (data.month, data.day) in cls.FERIADOS_NACIONAIS_2024
    
    @classmethod
    def obter_dias_uteis_periodo(cls, data_inicio: datetime, data_fim: datetime, uf: str = 'SP') -> int:
        """Calcular número de dias úteis em um período"""
        try:
            data_atual = data_inicio.date()
            data_final = data_fim.date()
            dias_uteis = 0
            
            while data_atual <= data_final:
                data_datetime = datetime.combine(data_atual, time.min)
                data_local = GerenciadorTimezoneBrasil.converter_para_timezone_uf(data_datetime, uf)
                
                # Verificar se é dia útil (não é fim de semana nem feriado)
                if (data_local.weekday() < 5 and 
                    not cls.eh_feriado_nacional(data_local)):
                    dias_uteis += 1
                
                data_atual += timedelta(days=1)
            
            return dias_uteis
            
        except Exception as e:
            logger.error("Erro ao calcular dias úteis", inicio=data_inicio, fim=data_fim, erro=str(e))
            return 0
    
    @classmethod
    def formatar_periodo_brasileiro(cls, data_inicio: datetime, data_fim: datetime) -> str:
        """Formatar período no padrão brasileiro"""
        try:
            inicio_br = GerenciadorTimezoneBrasil.converter_para_brasilia(data_inicio)
            fim_br = GerenciadorTimezoneBrasil.converter_para_brasilia(data_fim)
            
            # Se é o mesmo dia
            if inicio_br.date() == fim_br.date():
                return f"{inicio_br.strftime('%d/%m/%Y')} das {inicio_br.strftime('%H:%M')} às {fim_br.strftime('%H:%M')}"
            
            # Se é o mesmo mês
            elif inicio_br.month == fim_br.month and inicio_br.year == fim_br.year:
                return f"{inicio_br.day} a {fim_br.strftime('%d/%m/%Y')}"
            
            # Período completo
            else:
                return f"{inicio_br.strftime('%d/%m/%Y')} a {fim_br.strftime('%d/%m/%Y')}"
                
        except Exception as e:
            logger.error("Erro ao formatar período", inicio=data_inicio, fim=data_fim, erro=str(e))
            return f"{data_inicio} a {data_fim}"

# Instâncias globais
gerenciador_timezone = GerenciadorTimezoneBrasil()
processador_datas_fiscais = ProcessadorDatasFiscais()
utilitario_datas = UtilitarioDatasBrasil()