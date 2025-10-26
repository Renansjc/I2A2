"""
Pydantic schemas for dimensional data API responses
Schemas para APIs de dados dimensionais reais
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum

# ===== DASHBOARD EXECUTIVE SCHEMAS =====

class SupplierSummary(BaseModel):
    """Schema para resumo de fornecedor"""
    cnpj: str = Field(..., description="CNPJ do fornecedor")
    razao_social: str = Field(..., description="Razão social")
    nome_fantasia: Optional[str] = Field(None, description="Nome fantasia")
    uf: str = Field(..., description="Estado (UF)")
    total_documentos: int = Field(..., description="Total de documentos fiscais")
    valor_total: Decimal = Field(..., description="Valor total de compras")
    valor_medio_item: Decimal = Field(..., description="Valor médio por item")
    primeira_compra: Optional[date] = Field(None, description="Data da primeira compra")
    ultima_compra: Optional[date] = Field(None, description="Data da última compra")
    produtos_distintos: int = Field(..., description="Número de produtos distintos")

class MonthlySupplierData(BaseModel):
    """Schema para dados mensais de fornecedores"""
    mes: date = Field(..., description="Mês de referência")
    fornecedores_ativos: int = Field(..., description="Fornecedores ativos no mês")
    valor_total_mes: Decimal = Field(..., description="Valor total do mês")

class SuppliersResponse(BaseModel):
    """Schema para resposta de análise de fornecedores"""
    total_suppliers: int = Field(..., description="Total de fornecedores")
    top_suppliers: List[SupplierSummary] = Field(..., description="Top fornecedores por volume")
    monthly_trend: List[MonthlySupplierData] = Field(..., description="Tendência mensal")
    periodo_analise: str = Field(..., description="Período analisado")

class CategoryDistribution(BaseModel):
    """Schema para distribuição por categoria"""
    total_produtos: int = Field(..., description="Total de produtos na categoria")
    valor_total: Decimal = Field(..., description="Valor total da categoria")

class ProductSummary(BaseModel):
    """Schema para resumo de produto"""
    codigo_produto: str = Field(..., description="Código do produto")
    descricao: str = Field(..., description="Descrição do produto")
    categoria: Optional[str] = Field(None, description="Categoria do produto")
    subcategoria: Optional[str] = Field(None, description="Subcategoria do produto")
    ncm: Optional[str] = Field(None, description="Código NCM")
    total_documentos: int = Field(..., description="Total de documentos")
    quantidade_total: Decimal = Field(..., description="Quantidade total")
    valor_total: Decimal = Field(..., description="Valor total")
    preco_medio: Decimal = Field(..., description="Preço médio")
    fornecedores_distintos: int = Field(..., description="Número de fornecedores distintos")

class ProductsResponse(BaseModel):
    """Schema para resposta de análise de produtos"""
    total_products: int = Field(..., description="Total de produtos")
    categories_distribution: Dict[str, CategoryDistribution] = Field(..., description="Distribuição por categoria")
    top_products_by_value: List[ProductSummary] = Field(..., description="Top produtos por valor")
    periodo_analise: str = Field(..., description="Período analisado")

class MonthlyTotal(BaseModel):
    """Schema para totais mensais"""
    mes: date = Field(..., description="Mês de referência")
    total_invoices: int = Field(..., description="Total de notas fiscais")
    total_value: Decimal = Field(..., description="Valor total")
    total_taxes: Decimal = Field(..., description="Total de impostos")

class TaxSummary(BaseModel):
    """Schema para resumo de impostos"""
    total_icms: Decimal = Field(..., description="Total ICMS")
    total_ipi: Decimal = Field(..., description="Total IPI")
    total_pis: Decimal = Field(..., description="Total PIS")
    total_cofins: Decimal = Field(..., description="Total COFINS")

class FinancialSummaryResponse(BaseModel):
    """Schema para resposta de resumo financeiro"""
    total_invoices: int = Field(..., description="Total de notas fiscais")
    total_value: Decimal = Field(..., description="Valor total")
    average_invoice_value: Decimal = Field(..., description="Valor médio por nota")
    monthly_totals: List[MonthlyTotal] = Field(..., description="Totais mensais")
    tax_summary: TaxSummary = Field(..., description="Resumo de impostos")
    periodo_analise: str = Field(..., description="Período analisado")

class TrendData(BaseModel):
    """Schema para dados de tendência"""
    periodo: date = Field(..., description="Período da medição")
    valor: Decimal = Field(..., description="Valor da métrica")
    metrica: str = Field(..., description="Nome da métrica")

class TrendsResponse(BaseModel):
    """Schema para resposta de análise de tendências"""
    trend_data: List[TrendData] = Field(..., description="Dados da tendência")
    growth_rate: float = Field(..., description="Taxa de crescimento (%)")
    trend_type: str = Field(..., description="Tipo de tendência analisada")
    periodo_analise: str = Field(..., description="Período analisado")
    insights: List[str] = Field(..., description="Insights sobre a tendência")

# ===== DIMENSIONAL QUERY SCHEMAS =====

class EmitenteResponse(BaseModel):
    """Schema para resposta de emitente"""
    cnpj: str = Field(..., description="CNPJ do emitente")
    cpf: Optional[str] = Field(None, description="CPF (pessoa física)")
    inscricao_estadual: Optional[str] = Field(None, description="Inscrição estadual")
    razao_social: str = Field(..., description="Razão social")
    nome_fantasia: Optional[str] = Field(None, description="Nome fantasia")
    # Endereço
    logradouro: str = Field(..., description="Logradouro")
    numero: str = Field(..., description="Número")
    complemento: Optional[str] = Field(None, description="Complemento")
    bairro: str = Field(..., description="Bairro")
    codigo_municipio: str = Field(..., description="Código do município")
    nome_municipio: str = Field(..., description="Nome do município")
    uf: str = Field(..., description="Estado (UF)")
    cep: str = Field(..., description="CEP")
    # Contato
    telefone: Optional[str] = Field(None, description="Telefone")
    email: Optional[str] = Field(None, description="Email")
    # Métricas
    total_documentos: Optional[int] = Field(None, description="Total de documentos")
    valor_total_compras: Optional[Decimal] = Field(None, description="Valor total de compras")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")

class ProdutoResponse(BaseModel):
    """Schema para resposta de produto"""
    codigo_produto: str = Field(..., description="Código do produto")
    ean: Optional[str] = Field(None, description="Código EAN")
    descricao: str = Field(..., description="Descrição do produto")
    ncm: Optional[str] = Field(None, description="Código NCM")
    cest: Optional[str] = Field(None, description="Código CEST")
    cfop: Optional[str] = Field(None, description="CFOP mais comum")
    unidade_comercial: Optional[str] = Field(None, description="Unidade comercial")
    unidade_tributavel: Optional[str] = Field(None, description="Unidade tributável")
    categoria: Optional[str] = Field(None, description="Categoria")
    subcategoria: Optional[str] = Field(None, description="Subcategoria")
    # Métricas
    total_vendas: Optional[Decimal] = Field(None, description="Total de vendas")
    quantidade_total: Optional[Decimal] = Field(None, description="Quantidade total vendida")
    preco_medio: Optional[Decimal] = Field(None, description="Preço médio")
    fornecedores_count: Optional[int] = Field(None, description="Número de fornecedores")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")

class ServicoResponse(BaseModel):
    """Schema para resposta de serviço"""
    codigo_servico: str = Field(..., description="Código do serviço")
    descricao: str = Field(..., description="Descrição do serviço")
    codigo_cnae: Optional[str] = Field(None, description="Código CNAE")
    codigo_tributacao_nacional: Optional[str] = Field(None, description="Código de tributação nacional")
    codigo_tributacao_municipal: Optional[str] = Field(None, description="Código de tributação municipal")
    codigo_nbs: Optional[str] = Field(None, description="Código NBS")
    categoria: Optional[str] = Field(None, description="Categoria")
    subcategoria: Optional[str] = Field(None, description="Subcategoria")
    # Métricas
    total_prestacoes: Optional[Decimal] = Field(None, description="Total de prestações")
    valor_total: Optional[Decimal] = Field(None, description="Valor total")
    valor_medio: Optional[Decimal] = Field(None, description="Valor médio")
    prestadores_count: Optional[int] = Field(None, description="Número de prestadores")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")

# ===== AGGREGATIONS AND METRICS SCHEMAS =====

class KPIMetrics(BaseModel):
    """Schema para métricas KPI executivas"""
    concentracao_fornecedores: float = Field(..., description="Índice de concentração de fornecedores (0-1)")
    diversificacao_produtos: float = Field(..., description="Índice de diversificação de produtos (0-1)")
    crescimento_mensal: float = Field(..., description="Taxa de crescimento mensal (%)")
    ticket_medio: Decimal = Field(..., description="Ticket médio de compras")
    fornecedores_ativos: int = Field(..., description="Fornecedores ativos no período")
    produtos_ativos: int = Field(..., description="Produtos ativos no período")
    sazonalidade_score: float = Field(..., description="Score de sazonalidade (0-1)")

class DashboardMetricsResponse(BaseModel):
    """Schema para métricas consolidadas do dashboard"""
    kpis: KPIMetrics = Field(..., description="KPIs executivos")
    periodo_analise: str = Field(..., description="Período analisado")
    ultima_atualizacao: datetime = Field(..., description="Última atualização dos dados")
    confiabilidade_dados: float = Field(..., description="Score de confiabilidade dos dados (0-1)")

# ===== PAGINATION AND FILTERING SCHEMAS =====

class PaginatedResponse(BaseModel):
    """Schema base para respostas paginadas"""
    items: List[Any] = Field(..., description="Itens da página atual")
    total_count: int = Field(..., description="Total de itens")
    page: int = Field(..., description="Página atual")
    page_size: int = Field(..., description="Tamanho da página")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Indica se há próxima página")
    has_previous: bool = Field(..., description="Indica se há página anterior")

class EmitentesPaginatedResponse(PaginatedResponse):
    """Schema para resposta paginada de emitentes"""
    items: List[EmitenteResponse] = Field(..., description="Lista de emitentes")

class ProdutosPaginatedResponse(PaginatedResponse):
    """Schema para resposta paginada de produtos"""
    items: List[ProdutoResponse] = Field(..., description="Lista de produtos")

class ServicosPaginatedResponse(PaginatedResponse):
    """Schema para resposta paginada de serviços"""
    items: List[ServicoResponse] = Field(..., description="Lista de serviços")

# ===== EXPORT AND REPORTING SCHEMAS =====

class ExportRequest(BaseModel):
    """Schema para solicitação de exportação"""
    format: str = Field(..., description="Formato de exportação (xlsx, csv, pdf)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filtros aplicados")
    columns: Optional[List[str]] = Field(None, description="Colunas específicas para exportar")
    include_summary: bool = Field(True, description="Incluir resumo executivo")

class ExportResponse(BaseModel):
    """Schema para resposta de exportação"""
    export_id: str = Field(..., description="ID da exportação")
    status: str = Field(..., description="Status da exportação")
    download_url: Optional[str] = Field(None, description="URL para download")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração do link")
    created_at: datetime = Field(..., description="Data de criação")

# ===== SEARCH AND FILTERING SCHEMAS =====

class SearchFilters(BaseModel):
    """Schema para filtros de busca"""
    search_term: Optional[str] = Field(None, description="Termo de busca")
    category: Optional[str] = Field(None, description="Filtro por categoria")
    uf: Optional[str] = Field(None, description="Filtro por estado")
    date_start: Optional[date] = Field(None, description="Data de início")
    date_end: Optional[date] = Field(None, description="Data de fim")
    min_value: Optional[Decimal] = Field(None, description="Valor mínimo")
    max_value: Optional[Decimal] = Field(None, description="Valor máximo")

class SortOptions(BaseModel):
    """Schema para opções de ordenação"""
    field: str = Field(..., description="Campo para ordenação")
    direction: str = Field("asc", description="Direção da ordenação (asc/desc)")