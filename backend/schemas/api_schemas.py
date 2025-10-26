"""
Pydantic schemas for API request/response validation in Portuguese
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TipoConsulta(str, Enum):
    """Tipos de consulta disponíveis"""
    FORNECEDORES = "fornecedores"
    PRODUTOS = "produtos"
    IMPOSTOS = "impostos"
    VENDAS = "vendas"
    COMPRAS = "compras"
    GERAL = "geral"

class FormatoRelatorio(str, Enum):
    """Formatos de relatório disponíveis"""
    PDF = "pdf"
    XLSX = "xlsx"
    DOCX = "docx"
    JSON = "json"

class NivelExecutivo(str, Enum):
    """Níveis executivos para personalização de relatórios"""
    CEO = "ceo"
    CFO = "cfo"
    COO = "coo"
    DIRETOR = "diretor"
    GERENTE = "gerente"

class StatusProcessamento(str, Enum):
    """Status de processamento"""
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    ERRO = "erro"

# Request Schemas
class ConsultaNaturalRequest(BaseModel):
    """Schema para consultas em linguagem natural"""
    consulta: str = Field(..., min_length=5, max_length=1000, description="Consulta em linguagem natural")
    tipo_consulta: Optional[TipoConsulta] = Field(None, description="Tipo específico de consulta")
    periodo_inicio: Optional[datetime] = Field(None, description="Data de início do período")
    periodo_fim: Optional[datetime] = Field(None, description="Data de fim do período")
    contexto_usuario: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto adicional do usuário")
    nivel_executivo: Optional[NivelExecutivo] = Field(NivelExecutivo.GERENTE, description="Nível executivo para personalização")
    incluir_insights: bool = Field(True, description="Incluir insights de IA na resposta")
    
    @validator('consulta')
    def validar_consulta(cls, v):
        if not v.strip():
            raise ValueError('Consulta não pode estar vazia')
        return v.strip()
    
    @validator('periodo_fim')
    def validar_periodo(cls, v, values):
        if v and 'periodo_inicio' in values and values['periodo_inicio']:
            if v <= values['periodo_inicio']:
                raise ValueError('Data de fim deve ser posterior à data de início')
        return v

class RelatorioExecutivoRequest(BaseModel):
    """Schema para geração de relatórios executivos"""
    titulo: str = Field(..., min_length=5, max_length=200, description="Título do relatório")
    tipo_relatorio: TipoConsulta = Field(..., description="Tipo de relatório a ser gerado")
    formato: FormatoRelatorio = Field(FormatoRelatorio.PDF, description="Formato de saída do relatório")
    periodo_inicio: datetime = Field(..., description="Data de início do período")
    periodo_fim: datetime = Field(..., description="Data de fim do período")
    nivel_executivo: NivelExecutivo = Field(NivelExecutivo.CEO, description="Nível executivo para personalização")
    incluir_resumo_executivo: bool = Field(True, description="Incluir resumo executivo")
    incluir_recomendacoes: bool = Field(True, description="Incluir recomendações de ação")
    incluir_graficos: bool = Field(True, description="Incluir visualizações gráficas")
    filtros_adicionais: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Filtros específicos")
    contexto_empresarial: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto empresarial")
    
    @validator('titulo')
    def validar_titulo(cls, v):
        if not v.strip():
            raise ValueError('Título não pode estar vazio')
        return v.strip()
    
    @validator('periodo_fim')
    def validar_periodo_relatorio(cls, v, values):
        if 'periodo_inicio' in values and v <= values['periodo_inicio']:
            raise ValueError('Data de fim deve ser posterior à data de início')
        return v

class ProcessarXMLRequest(BaseModel):
    """Schema para processamento de documentos XML"""
    nome_arquivo: str = Field(..., description="Nome do arquivo XML")
    conteudo_base64: Optional[str] = Field(None, description="Conteúdo do arquivo em base64")
    url_arquivo: Optional[str] = Field(None, description="URL do arquivo para download")
    processar_com_ia: bool = Field(True, description="Usar IA para análise semântica")
    extrair_insights: bool = Field(True, description="Extrair insights empresariais")
    categorizar_automaticamente: bool = Field(True, description="Categorizar produtos/serviços automaticamente")
    validar_regras_negocio: bool = Field(True, description="Validar regras de negócio")
    contexto_processamento: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contexto adicional")
    
    @validator('nome_arquivo')
    def validar_nome_arquivo(cls, v):
        if not v.strip():
            raise ValueError('Nome do arquivo não pode estar vazio')
        if not v.lower().endswith('.xml'):
            raise ValueError('Arquivo deve ter extensão .xml')
        return v.strip()
    
    @validator('conteudo_base64', 'url_arquivo')
    def validar_fonte_arquivo(cls, v, values, field):
        # Pelo menos uma fonte deve ser fornecida
        if field.name == 'url_arquivo' and not v and not values.get('conteudo_base64'):
            raise ValueError('Deve fornecer conteúdo_base64 ou url_arquivo')
        return v

# Response Schemas
class InsightIA(BaseModel):
    """Schema para insights gerados por IA"""
    tipo: str = Field(..., description="Tipo do insight")
    descricao: str = Field(..., description="Descrição do insight")
    confianca: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança (0-1)")
    impacto_empresarial: str = Field(..., description="Impacto empresarial do insight")
    recomendacao: Optional[str] = Field(None, description="Recomendação de ação")

class ResultadoConsulta(BaseModel):
    """Schema para resultados de consulta SQL"""
    colunas: List[str] = Field(..., description="Nomes das colunas")
    dados: List[List[Any]] = Field(..., description="Dados da consulta")
    total_registros: int = Field(..., ge=0, description="Total de registros")
    tempo_execucao: float = Field(..., ge=0, description="Tempo de execução em segundos")

class ConsultaNaturalResponse(BaseModel):
    """Schema para resposta de consultas em linguagem natural"""
    id_consulta: str = Field(..., description="ID único da consulta")
    consulta_original: str = Field(..., description="Consulta original do usuário")
    interpretacao_ia: str = Field(..., description="Interpretação da IA sobre a consulta")
    sql_gerado: str = Field(..., description="SQL gerado pela IA")
    resultado: ResultadoConsulta = Field(..., description="Resultado da consulta")
    insights: List[InsightIA] = Field(default_factory=list, description="Insights gerados pela IA")
    explicacao_executiva: str = Field(..., description="Explicação em linguagem executiva")
    recomendacoes: List[str] = Field(default_factory=list, description="Recomendações de ação")
    confianca_geral: float = Field(..., ge=0.0, le=1.0, description="Confiança geral da resposta")
    tempo_processamento: float = Field(..., ge=0, description="Tempo total de processamento")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")

class RelatorioExecutivoResponse(BaseModel):
    """Schema para resposta de geração de relatórios"""
    id_relatorio: str = Field(..., description="ID único do relatório")
    titulo: str = Field(..., description="Título do relatório")
    status: StatusProcessamento = Field(..., description="Status do processamento")
    formato: FormatoRelatorio = Field(..., description="Formato do relatório")
    url_download: Optional[str] = Field(None, description="URL para download do relatório")
    resumo_executivo: Optional[str] = Field(None, description="Resumo executivo gerado")
    principais_insights: List[InsightIA] = Field(default_factory=list, description="Principais insights")
    recomendacoes_estrategicas: List[str] = Field(default_factory=list, description="Recomendações estratégicas")
    metricas_chave: Dict[str, Any] = Field(default_factory=dict, description="Métricas chave do período")
    tempo_processamento: Optional[float] = Field(None, description="Tempo de processamento")
    data_geracao: datetime = Field(default_factory=datetime.now, description="Data de geração")
    valido_ate: Optional[datetime] = Field(None, description="Data de validade do relatório")

class DocumentoProcessado(BaseModel):
    """Schema para documento processado"""
    tipo_documento: str = Field(..., description="Tipo do documento (NFE/NFSE)")
    chave_documento: str = Field(..., description="Chave do documento")
    fornecedor: str = Field(..., description="Nome do fornecedor")
    valor_total: Decimal = Field(..., description="Valor total do documento")
    data_emissao: datetime = Field(..., description="Data de emissão")
    produtos_servicos: List[str] = Field(default_factory=list, description="Lista de produtos/serviços")
    categorias_identificadas: List[str] = Field(default_factory=list, description="Categorias identificadas pela IA")

class ProcessarXMLResponse(BaseModel):
    """Schema para resposta de processamento XML"""
    id_processamento: str = Field(..., description="ID único do processamento")
    nome_arquivo: str = Field(..., description="Nome do arquivo processado")
    status: StatusProcessamento = Field(..., description="Status do processamento")
    documento: Optional[DocumentoProcessado] = Field(None, description="Dados do documento processado")
    insights_semanticos: List[InsightIA] = Field(default_factory=list, description="Insights semânticos extraídos")
    anomalias_detectadas: List[str] = Field(default_factory=list, description="Anomalias detectadas")
    validacoes_negocio: Dict[str, bool] = Field(default_factory=dict, description="Resultado das validações")
    confianca_processamento: float = Field(..., ge=0.0, le=1.0, description="Confiança do processamento")
    tempo_processamento: float = Field(..., ge=0, description="Tempo de processamento")
    data_processamento: datetime = Field(default_factory=datetime.now, description="Data do processamento")
    proximos_passos: List[str] = Field(default_factory=list, description="Próximos passos sugeridos")

# Error Response Schema
class ErrorResponse(BaseModel):
    """Schema para respostas de erro"""
    codigo_erro: str = Field(..., description="Código do erro")
    mensagem: str = Field(..., description="Mensagem de erro em português")
    detalhes: Optional[str] = Field(None, description="Detalhes adicionais do erro")
    sugestao_solucao: Optional[str] = Field(None, description="Sugestão para resolver o erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")
    id_rastreamento: Optional[str] = Field(None, description="ID para rastreamento do erro")

# Status Response Schema
class StatusSistemaResponse(BaseModel):
    """Schema para status do sistema"""
    status_geral: str = Field(..., description="Status geral do sistema")
    agentes_ativos: Dict[str, str] = Field(..., description="Status dos agentes")
    versao_sistema: str = Field(..., description="Versão do sistema")
    tempo_atividade: str = Field(..., description="Tempo de atividade")
    estatisticas_uso: Dict[str, Any] = Field(default_factory=dict, description="Estatísticas de uso")
    ultima_atualizacao: datetime = Field(default_factory=datetime.now, description="Última atualização")