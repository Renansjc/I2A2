"""
Pydantic schemas for fiscal document data validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TipoDocumento(str, Enum):
    """Tipos de documento fiscal"""
    NFE = "NFE"
    NFSE = "NFSE"

class EnderecoSchema(BaseModel):
    """Schema para endereços"""
    logradouro: str = Field(..., description="Logradouro")
    numero: str = Field(..., description="Número")
    complemento: Optional[str] = Field(None, description="Complemento")
    bairro: str = Field(..., description="Bairro")
    codigo_municipio: str = Field(..., description="Código do município")
    nome_municipio: str = Field(..., description="Nome do município")
    uf: str = Field(..., min_length=2, max_length=2, description="UF")
    cep: str = Field(..., regex=r'^\d{5}-?\d{3}$', description="CEP")
    codigo_pais: Optional[str] = Field("1058", description="Código do país")
    nome_pais: Optional[str] = Field("Brasil", description="Nome do país")

class FornecedorSchema(BaseModel):
    """Schema para fornecedores"""
    cnpj: Optional[str] = Field(None, regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', description="CNPJ")
    cpf: Optional[str] = Field(None, regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', description="CPF")
    inscricao_estadual: Optional[str] = Field(None, description="Inscrição estadual")
    razao_social: str = Field(..., min_length=1, max_length=200, description="Razão social")
    nome_fantasia: Optional[str] = Field(None, max_length=200, description="Nome fantasia")
    endereco: EnderecoSchema = Field(..., description="Endereço")
    telefone: Optional[str] = Field(None, description="Telefone")
    email: Optional[str] = Field(None, description="Email")
    regime_tributario: Optional[str] = Field(None, description="Regime tributário")
    categoria: Optional[str] = Field(None, description="Categoria (gerada por IA)")
    regiao: Optional[str] = Field(None, description="Região (gerada por IA)")
    relacionamento_comercial: Optional[str] = Field(None, description="Relacionamento comercial (gerado por IA)")
    
    @validator('cnpj', 'cpf')
    def validar_documento(cls, v, field):
        if v is None:
            return v
        # Remove formatação para validação
        doc = v.replace('.', '').replace('-', '').replace('/', '')
        if field.name == 'cnpj' and len(doc) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        elif field.name == 'cpf' and len(doc) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        return v

class DestinatarioSchema(BaseModel):
    """Schema para destinatários"""
    cnpj: Optional[str] = Field(None, regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', description="CNPJ")
    cpf: Optional[str] = Field(None, regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', description="CPF")
    inscricao_estadual: Optional[str] = Field(None, description="Inscrição estadual")
    razao_social: str = Field(..., min_length=1, max_length=200, description="Razão social")
    endereco: EnderecoSchema = Field(..., description="Endereço")
    telefone: Optional[str] = Field(None, description="Telefone")
    email: Optional[str] = Field(None, description="Email")

class ProdutoSchema(BaseModel):
    """Schema para produtos"""
    codigo_produto: str = Field(..., description="Código do produto")
    ean: Optional[str] = Field(None, description="Código EAN")
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição do produto")
    ncm: str = Field(..., regex=r'^\d{8}$', description="Código NCM")
    cest: Optional[str] = Field(None, description="Código CEST")
    cfop: str = Field(..., regex=r'^\d{4}$', description="CFOP")
    unidade_comercial: str = Field(..., description="Unidade comercial")
    unidade_tributavel: Optional[str] = Field(None, description="Unidade tributável")
    categoria: Optional[str] = Field(None, description="Categoria (gerada por IA)")
    subcategoria: Optional[str] = Field(None, description="Subcategoria (gerada por IA)")

class ServicoSchema(BaseModel):
    """Schema para serviços"""
    codigo_servico: str = Field(..., description="Código do serviço")
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição do serviço")
    codigo_cnae: Optional[str] = Field(None, description="Código CNAE")
    codigo_tributacao_nacional: Optional[str] = Field(None, description="Código de tributação nacional")
    codigo_tributacao_municipal: Optional[str] = Field(None, description="Código de tributação municipal")
    codigo_nbs: Optional[str] = Field(None, description="Código NBS")
    categoria: Optional[str] = Field(None, description="Categoria (gerada por IA)")
    subcategoria: Optional[str] = Field(None, description="Subcategoria (gerada por IA)")

class ImpostoSchema(BaseModel):
    """Schema para impostos"""
    tipo_imposto: str = Field(..., description="Tipo do imposto (ICMS, IPI, PIS, COFINS)")
    origem_produto: Optional[str] = Field(None, description="Origem do produto")
    situacao_tributaria: str = Field(..., description="Situação tributária")
    base_calculo: Decimal = Field(..., ge=0, description="Base de cálculo")
    aliquota: Decimal = Field(..., ge=0, le=100, description="Alíquota (%)")
    valor: Decimal = Field(..., ge=0, description="Valor do imposto")

class ImpostoISSQNSchema(BaseModel):
    """Schema para imposto ISSQN"""
    base_calculo: Decimal = Field(..., ge=0, description="Base de cálculo")
    aliquota: Decimal = Field(..., ge=0, le=100, description="Alíquota (%)")
    valor: Decimal = Field(..., ge=0, description="Valor do ISSQN")
    situacao_tributaria: Optional[str] = Field(None, description="Situação tributária")
    valor_credito: Optional[Decimal] = Field(None, ge=0, description="Valor do crédito")

class ItemNFESchema(BaseModel):
    """Schema para itens de NFE"""
    numero_item: int = Field(..., ge=1, description="Número do item")
    produto: ProdutoSchema = Field(..., description="Dados do produto")
    quantidade_comercial: Decimal = Field(..., gt=0, description="Quantidade comercial")
    valor_unitario_comercial: Decimal = Field(..., gt=0, description="Valor unitário comercial")
    valor_total_bruto: Decimal = Field(..., gt=0, description="Valor total bruto")
    quantidade_tributavel: Optional[Decimal] = Field(None, description="Quantidade tributável")
    valor_unitario_tributavel: Optional[Decimal] = Field(None, description="Valor unitário tributável")
    valor_frete: Optional[Decimal] = Field(None, ge=0, description="Valor do frete")
    valor_seguro: Optional[Decimal] = Field(None, ge=0, description="Valor do seguro")
    valor_desconto: Optional[Decimal] = Field(None, ge=0, description="Valor do desconto")
    valor_outras_despesas: Optional[Decimal] = Field(None, ge=0, description="Outras despesas")
    impostos: Optional[List[ImpostoSchema]] = Field(None, description="Lista de impostos")

class ItemNFSESchema(BaseModel):
    """Schema para itens de NFSE"""
    servico: ServicoSchema = Field(..., description="Dados do serviço")
    quantidade: Decimal = Field(..., gt=0, description="Quantidade")
    valor_unitario: Decimal = Field(..., gt=0, description="Valor unitário")
    valor_total: Decimal = Field(..., gt=0, description="Valor total")
    valor_deducoes: Optional[Decimal] = Field(None, ge=0, description="Valor das deduções")
    imposto_issqn: Optional[ImpostoISSQNSchema] = Field(None, description="Imposto ISSQN")

class NFESchema(BaseModel):
    """Schema para NFE"""
    chave_nfe: str = Field(..., regex=r'^\d{44}$', description="Chave da NFE")
    numero_nf: str = Field(..., description="Número da NF")
    serie: str = Field(..., description="Série")
    data_emissao: datetime = Field(..., description="Data de emissão")
    tipo_operacao: str = Field(..., regex=r'^[01]$', description="Tipo de operação (0=Entrada, 1=Saída)")
    codigo_municipio: str = Field(..., description="Código do município")
    uf_emitente: str = Field(..., min_length=2, max_length=2, description="UF do emitente")
    natureza_operacao: str = Field(..., description="Natureza da operação")
    fornecedor: FornecedorSchema = Field(..., description="Dados do fornecedor")
    destinatario: DestinatarioSchema = Field(..., description="Dados do destinatário")
    itens: List[ItemNFESchema] = Field(..., min_items=1, description="Lista de itens")
    valor_total_nf: Decimal = Field(..., gt=0, description="Valor total da NF")
    valor_total_produtos: Decimal = Field(..., ge=0, description="Valor total dos produtos")
    caminho_arquivo_xml: str = Field(..., description="Caminho do arquivo XML")
    modelo: str = Field("55", description="Modelo do documento")
    data_saida_entrada: Optional[datetime] = Field(None, description="Data de saída/entrada")
    forma_pagamento: Optional[str] = Field(None, description="Forma de pagamento")
    valor_total_servicos: Optional[Decimal] = Field(None, ge=0, description="Valor total dos serviços")
    base_calculo_icms: Optional[Decimal] = Field(None, ge=0, description="Base de cálculo ICMS")
    valor_icms: Optional[Decimal] = Field(None, ge=0, description="Valor ICMS")
    base_calculo_icms_st: Optional[Decimal] = Field(None, ge=0, description="Base de cálculo ICMS ST")
    valor_icms_st: Optional[Decimal] = Field(None, ge=0, description="Valor ICMS ST")
    valor_total_ipi: Optional[Decimal] = Field(None, ge=0, description="Valor total IPI")
    valor_pis: Optional[Decimal] = Field(None, ge=0, description="Valor PIS")
    valor_cofins: Optional[Decimal] = Field(None, ge=0, description="Valor COFINS")
    tipo_documento: TipoDocumento = Field(TipoDocumento.NFE, description="Tipo do documento")

class NFSESchema(BaseModel):
    """Schema para NFSE"""
    id_nfse: str = Field(..., description="ID da NFSE")
    numero_nfse: str = Field(..., description="Número da NFSE")
    codigo_municipio_emissao: str = Field(..., description="Código do município de emissão")
    data_emissao: datetime = Field(..., description="Data de emissão")
    fornecedor: FornecedorSchema = Field(..., description="Dados do fornecedor")
    destinatario: DestinatarioSchema = Field(..., description="Dados do destinatário")
    servicos: List[ItemNFSESchema] = Field(..., min_items=1, description="Lista de serviços")
    valor_total_servicos: Decimal = Field(..., gt=0, description="Valor total dos serviços")
    caminho_arquivo_xml: str = Field(..., description="Caminho do arquivo XML")
    numero_dfse: Optional[str] = Field(None, description="Número DFSE")
    local_emissao: Optional[str] = Field(None, description="Local de emissão")
    local_prestacao: Optional[str] = Field(None, description="Local de prestação")
    codigo_municipio_incidencia: Optional[str] = Field(None, description="Código do município de incidência")
    local_incidencia: Optional[str] = Field(None, description="Local de incidência")
    tributacao_nacional: Optional[str] = Field(None, description="Tributação nacional")
    tributacao_municipal: Optional[str] = Field(None, description="Tributação municipal")
    codigo_nbs: Optional[str] = Field(None, description="Código NBS")
    data_processamento: Optional[datetime] = Field(None, description="Data de processamento")
    ambiente_gerador: Optional[str] = Field(None, description="Ambiente gerador")
    tipo_emissao: Optional[str] = Field(None, description="Tipo de emissão")
    processo_emissao: Optional[str] = Field(None, description="Processo de emissão")
    codigo_status: Optional[str] = Field(None, description="Código de status")
    valor_total_deducoes: Optional[Decimal] = Field(None, ge=0, description="Valor total das deduções")
    valor_base_calculo: Optional[Decimal] = Field(None, ge=0, description="Valor da base de cálculo")
    valor_issqn: Optional[Decimal] = Field(None, ge=0, description="Valor ISSQN")
    valor_credito: Optional[Decimal] = Field(None, ge=0, description="Valor do crédito")
    tipo_documento: TipoDocumento = Field(TipoDocumento.NFSE, description="Tipo do documento")