"""
Configurações específicas para LLM (Large Language Models) com foco no mercado brasileiro
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum
import json
from datetime import datetime


class ModeloLLM(str, Enum):
    """Modelos LLM disponíveis"""
    GPT_4 = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class TipoPrompt(str, Enum):
    """Tipos de prompts especializados"""
    INTERPRETACAO_CONSULTA = "interpretacao_consulta"
    ANALISE_SEMANTICA_XML = "analise_semantica_xml"
    CATEGORIZACAO_PRODUTOS = "categorizacao_produtos"
    TRADUCAO_SQL = "traducao_sql"
    GERACAO_RELATORIO = "geracao_relatorio"
    ANALISE_FORNECEDOR = "analise_fornecedor"
    DETECCAO_PADROES = "deteccao_padroes"
    RESUMO_EXECUTIVO = "resumo_executivo"


class ConfiguracaoModelo(BaseModel):
    """Configuração específica para cada modelo"""
    modelo: ModeloLLM
    max_tokens: int = Field(default=4000, ge=1, le=8000)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    timeout: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=3, ge=1, le=5)


class ConfiguracaoContextoBrasileiro(BaseModel):
    """Configurações específicas para o contexto empresarial brasileiro"""
    timezone: str = "America/Sao_Paulo"
    moeda: str = "BRL"
    formato_data: str = "%d/%m/%Y"
    formato_numero: str = "pt_BR"
    idioma_principal: str = "pt-BR"
    idioma_fallback: str = "en-US"
    
    # Configurações fiscais brasileiras
    tipos_documento_fiscal: List[str] = [
        "NF-e", "NFS-e", "CT-e", "MDF-e", "NFC-e"
    ]
    
    # Configurações de categorização
    categorias_produto_padrao: List[str] = [
        "Matéria Prima", "Produto Acabado", "Mercadoria para Revenda",
        "Imobilizado", "Uso e Consumo", "Ativo Imobilizado", "Serviços"
    ]
    
    # Configurações de fornecedores
    tipos_fornecedor: List[str] = [
        "Fornecedor Nacional", "Fornecedor Internacional", 
        "Prestador de Serviços", "Distribuidor", "Fabricante"
    ]
    
    # Configurações de relatórios executivos
    cargos_executivos: List[str] = [
        "CEO", "CFO", "COO", "CTO", "Diretor Financeiro",
        "Diretor Comercial", "Gerente Geral", "Controller"
    ]


class ConfiguracaoRateLimiting(BaseModel):
    """Configuração de rate limiting para APIs"""
    requests_per_minute: int = Field(default=3500, ge=1, le=10000)
    tokens_per_minute: int = Field(default=90000, ge=1000, le=200000)
    concurrent_requests: int = Field(default=10, ge=1, le=50)
    backoff_factor: float = Field(default=2.0, ge=1.0, le=5.0)
    max_wait_time: int = Field(default=300, ge=30, le=600)


class ConfiguracaoCache(BaseModel):
    """Configuração de cache para respostas LLM"""
    habilitado: bool = True
    ttl_segundos: int = Field(default=3600, ge=300, le=86400)  # 1 hora padrão
    max_size: int = Field(default=1000, ge=100, le=10000)
    chave_versao: str = "v1.0"
    
    # TTL específico por tipo de prompt
    ttl_por_tipo: Dict[TipoPrompt, int] = {
        TipoPrompt.INTERPRETACAO_CONSULTA: 1800,  # 30 minutos
        TipoPrompt.ANALISE_SEMANTICA_XML: 7200,   # 2 horas
        TipoPrompt.CATEGORIZACAO_PRODUTOS: 3600,  # 1 hora
        TipoPrompt.TRADUCAO_SQL: 1800,            # 30 minutos
        TipoPrompt.GERACAO_RELATORIO: 900,        # 15 minutos
        TipoPrompt.ANALISE_FORNECEDOR: 3600,      # 1 hora
        TipoPrompt.DETECCAO_PADROES: 7200,        # 2 horas
        TipoPrompt.RESUMO_EXECUTIVO: 1800         # 30 minutos
    }


class ConfiguracaoMonitoramento(BaseModel):
    """Configuração de monitoramento e métricas"""
    rastrear_uso_tokens: bool = True
    rastrear_tempo_resposta: bool = True
    rastrear_taxa_erro: bool = True
    rastrear_custo: bool = True
    
    # Alertas
    alerta_custo_diario: float = 100.0  # USD
    alerta_taxa_erro: float = 0.05      # 5%
    alerta_tempo_resposta: float = 30.0  # segundos
    
    # Métricas de qualidade
    score_confianca_minimo: float = 0.7
    validar_respostas: bool = True


class ConfiguracoesLLM(BaseModel):
    """Configurações principais para integração LLM com foco brasileiro"""
    
    # Configurações de modelo
    modelo_padrao: ModeloLLM = ModeloLLM.GPT_4
    modelo_fallback: ModeloLLM = ModeloLLM.GPT_3_5_TURBO
    
    # Configurações por modelo
    configuracoes_modelo: Dict[ModeloLLM, ConfiguracaoModelo] = {
        ModeloLLM.GPT_4: ConfiguracaoModelo(
            modelo=ModeloLLM.GPT_4,
            max_tokens=4000,
            temperature=0.1,
            timeout=90
        ),
        ModeloLLM.GPT_4_TURBO: ConfiguracaoModelo(
            modelo=ModeloLLM.GPT_4_TURBO,
            max_tokens=4000,
            temperature=0.1,
            timeout=60
        ),
        ModeloLLM.GPT_3_5_TURBO: ConfiguracaoModelo(
            modelo=ModeloLLM.GPT_3_5_TURBO,
            max_tokens=2000,
            temperature=0.2,
            timeout=30
        )
    }
    
    # Configurações específicas do Brasil
    contexto_brasileiro: ConfiguracaoContextoBrasileiro = ConfiguracaoContextoBrasileiro()
    
    # Rate limiting
    rate_limiting: ConfiguracaoRateLimiting = ConfiguracaoRateLimiting()
    
    # Cache
    cache: ConfiguracaoCache = ConfiguracaoCache()
    
    # Monitoramento
    monitoramento: ConfiguracaoMonitoramento = ConfiguracaoMonitoramento()
    
    # Configurações de fallback
    usar_fallback_automatico: bool = True
    max_tentativas_fallback: int = 2
    
    # Configurações de desenvolvimento
    modo_debug: bool = False
    log_prompts: bool = False
    log_respostas: bool = False
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def obter_configuracao_modelo(self, modelo: ModeloLLM) -> ConfiguracaoModelo:
        """Obtém configuração específica para um modelo"""
        return self.configuracoes_modelo.get(modelo, self.configuracoes_modelo[self.modelo_padrao])
    
    def obter_ttl_cache(self, tipo_prompt: TipoPrompt) -> int:
        """Obtém TTL específico para tipo de prompt"""
        return self.cache.ttl_por_tipo.get(tipo_prompt, self.cache.ttl_segundos)
    
    def validar_configuracao(self) -> List[str]:
        """Valida configurações e retorna lista de problemas encontrados"""
        problemas = []
        
        # Validar rate limiting
        if self.rate_limiting.requests_per_minute > 10000:
            problemas.append("Rate limit de requests muito alto")
        
        if self.rate_limiting.tokens_per_minute > 200000:
            problemas.append("Rate limit de tokens muito alto")
        
        # Validar configurações de modelo
        for modelo, config in self.configuracoes_modelo.items():
            if config.max_tokens > 8000:
                problemas.append(f"Max tokens muito alto para {modelo}")
            
            if config.timeout > 300:
                problemas.append(f"Timeout muito alto para {modelo}")
        
        return problemas
    
    def exportar_para_json(self) -> str:
        """Exporta configurações para JSON"""
        return self.model_dump_json(indent=2)
    
    @classmethod
    def carregar_de_json(cls, json_str: str) -> 'ConfiguracoesLLM':
        """Carrega configurações de JSON"""
        return cls.model_validate_json(json_str)


# Instância padrão das configurações
configuracoes_llm_padrao = ConfiguracoesLLM()