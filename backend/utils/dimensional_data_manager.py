"""
Dimensional Data Manager for Brazilian fiscal documents processing
Handles CRUD operations for dimensional tables with optimized upsert strategies
"""

import structlog
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from supabase import Client
from postgrest.exceptions import APIError

from .database import get_supabase_client, SupabaseClient
from .validation import ValidadorDocumentosBrasileiros
from .brazilian_formatting import FormatadorBrasileiro

logger = structlog.get_logger()


class ValidationResult:
    """Result of data validation"""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False


class DimensionalDataValidator:
    """Validator for dimensional data with Brazilian business rules"""
    
    @staticmethod
    def validate_emitente_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate emitente data completeness and format"""
        result = ValidationResult(True)
        
        # Required fields validation
        required_fields = ['razao_social']
        for field in required_fields:
            if not data.get(field):
                result.add_error(f"Campo obrigatório ausente: {field}")
        
        # CNPJ or CPF validation
        cnpj = data.get('cnpj')
        cpf = data.get('cpf')
        
        if not cnpj and not cpf:
            result.add_error("CNPJ ou CPF é obrigatório")
        
        if cnpj and not ValidadorDocumentosBrasileiros.validar_cnpj(cnpj):
            result.add_error(f"CNPJ inválido: {cnpj}")
        
        if cpf and not ValidadorDocumentosBrasileiros.validar_cpf(cpf):
            result.add_error(f"CPF inválido: {cpf}")
        
        # Address validation
        address_fields = ['logradouro', 'numero', 'bairro', 'codigo_municipio', 'nome_municipio', 'uf', 'cep']
        for field in address_fields:
            if not data.get(field):
                result.add_error(f"Campo de endereço obrigatório ausente: {field}")
        
        return result
    
    @staticmethod
    def validate_destinatario_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate destinatario data completeness and format"""
        result = ValidationResult(True)
        
        # CNPJ or CPF validation (at least one required)
        cnpj = data.get('cnpj')
        cpf = data.get('cpf')
        
        if not cnpj and not cpf:
            result.add_error("CNPJ ou CPF é obrigatório")
        
        if cnpj and not ValidadorDocumentosBrasileiros.validar_cnpj(cnpj):
            result.add_error(f"CNPJ inválido: {cnpj}")
        
        if cpf and not ValidadorDocumentosBrasileiros.validar_cpf(cpf):
            result.add_error(f"CPF inválido: {cpf}")
        
        return result
    
    @staticmethod
    def validate_produto_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate product data completeness"""
        result = ValidationResult(True)
        
        # Required fields validation
        required_fields = ['codigo_produto', 'descricao']
        for field in required_fields:
            if not data.get(field):
                result.add_error(f"Campo obrigatório ausente: {field}")
        
        # NCM validation (8 digits)
        ncm = data.get('ncm')
        if ncm and (not ncm.isdigit() or len(ncm) != 8):
            result.add_error(f"NCM deve ter 8 dígitos: {ncm}")
        
        # CFOP validation (4 digits)
        cfop = data.get('cfop')
        if cfop and (not cfop.isdigit() or len(cfop) != 4):
            result.add_error(f"CFOP deve ter 4 dígitos: {cfop}")
        
        return result
    
    @staticmethod
    def validate_servico_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate service data completeness"""
        result = ValidationResult(True)
        
        # Required fields validation
        required_fields = ['codigo_servico', 'descricao']
        for field in required_fields:
            if not data.get(field):
                result.add_error(f"Campo obrigatório ausente: {field}")
        
        return result


class DimensionalDataManager:
    """Manager for dimensional data operations with Brazilian fiscal compliance"""
    
    def __init__(self, admin_mode: bool = False):
        self.client = get_supabase_client(admin_mode)
        self.admin_mode = admin_mode
        self.validator = DimensionalDataValidator()
    
    async def upsert_emitente(self, emitente_data: Dict[str, Any]) -> str:
        """Insert or update emitente record with duplicate detection"""
        try:
            # Validate data
            validation = self.validator.validate_emitente_data(emitente_data)
            if not validation.is_valid:
                raise ValueError(f"Dados de emitente inválidos: {', '.join(validation.errors)}")
            
            # Format and prepare data
            cnpj = emitente_data.get('cnpj')
            if cnpj:
                cnpj = FormatadorBrasileiro.formatar_documento(cnpj, 'cnpj')
            
            cpf = emitente_data.get('cpf')
            if cpf:
                cpf = FormatadorBrasileiro.formatar_documento(cpf, 'cpf')
            
            # Use CNPJ as primary key, generate if CPF only
            primary_key = cnpj if cnpj else f"CPF_{cpf}"
            
            upsert_data = {
                'cnpj': primary_key,
                'cpf': cpf,
                'inscricao_estadual': emitente_data.get('inscricao_estadual'),
                'razao_social': emitente_data.get('razao_social'),
                'nome_fantasia': emitente_data.get('nome_fantasia'),
                'logradouro': emitente_data.get('logradouro'),
                'numero': emitente_data.get('numero'),
                'complemento': emitente_data.get('complemento'),
                'bairro': emitente_data.get('bairro'),
                'codigo_municipio': emitente_data.get('codigo_municipio'),
                'nome_municipio': emitente_data.get('nome_municipio'),
                'uf': emitente_data.get('uf'),
                'cep': emitente_data.get('cep'),
                'codigo_pais': emitente_data.get('codigo_pais', '1058'),
                'nome_pais': emitente_data.get('nome_pais', 'Brasil'),
                'telefone': emitente_data.get('telefone'),
                'email': emitente_data.get('email'),
                'regime_tributario': emitente_data.get('regime_tributario'),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values
            upsert_data = {k: v for k, v in upsert_data.items() if v is not None}
            
            # Perform upsert operation
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_emitente')
                .upsert(upsert_data, on_conflict='cnpj')
                .execute()
            )
            
            logger.info(
                "Emitente upserted successfully",
                cnpj=primary_key,
                razao_social=emitente_data.get('razao_social'),
                admin_mode=self.admin_mode
            )
            
            return primary_key
            
        except Exception as e:
            logger.error("Failed to upsert emitente", error=str(e), data=emitente_data)
            raise
    
    async def upsert_destinatario(self, destinatario_data: Dict[str, Any]) -> Optional[int]:
        """Insert or update destinatario record with duplicate detection"""
        try:
            # Validate data
            validation = self.validator.validate_destinatario_data(destinatario_data)
            if not validation.is_valid:
                raise ValueError(f"Dados de destinatário inválidos: {', '.join(validation.errors)}")
            
            # Format identifiers
            cnpj = destinatario_data.get('cnpj')
            if cnpj:
                cnpj = FormatadorBrasileiro.formatar_documento(cnpj, 'cnpj')
            
            cpf = destinatario_data.get('cpf')
            if cpf:
                cpf = FormatadorBrasileiro.formatar_documento(cpf, 'cpf')
            
            # Check for existing record by CNPJ or CPF
            existing_record = None
            if cnpj:
                result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_destinatario')
                    .select('id')
                    .eq('cnpj', cnpj)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    existing_record = result.data[0]
            
            if not existing_record and cpf:
                result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_destinatario')
                    .select('id')
                    .eq('cpf', cpf)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    existing_record = result.data[0]
            
            upsert_data = {
                'cnpj': cnpj,
                'cpf': cpf,
                'inscricao_estadual': destinatario_data.get('inscricao_estadual'),
                'razao_social': destinatario_data.get('razao_social'),
                'logradouro': destinatario_data.get('logradouro'),
                'numero': destinatario_data.get('numero'),
                'complemento': destinatario_data.get('complemento'),
                'bairro': destinatario_data.get('bairro'),
                'codigo_municipio': destinatario_data.get('codigo_municipio'),
                'nome_municipio': destinatario_data.get('nome_municipio'),
                'uf': destinatario_data.get('uf'),
                'cep': destinatario_data.get('cep'),
                'codigo_pais': destinatario_data.get('codigo_pais', '1058'),
                'nome_pais': destinatario_data.get('nome_pais', 'Brasil'),
                'telefone': destinatario_data.get('telefone'),
                'email': destinatario_data.get('email'),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values
            upsert_data = {k: v for k, v in upsert_data.items() if v is not None}
            
            if existing_record:
                # Update existing record
                upsert_data['id'] = existing_record['id']
                result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_destinatario')
                    .update(upsert_data)
                    .eq('id', existing_record['id'])
                    .execute()
                )
                record_id = existing_record['id']
            else:
                # Insert new record
                result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_destinatario')
                    .insert(upsert_data)
                    .execute()
                )
                record_id = result.data[0]['id']
            
            logger.info(
                "Destinatario upserted successfully",
                id=record_id,
                cnpj=cnpj,
                cpf=cpf,
                razao_social=destinatario_data.get('razao_social'),
                admin_mode=self.admin_mode
            )
            
            return record_id
            
        except Exception as e:
            logger.error("Failed to upsert destinatario", error=str(e), data=destinatario_data)
            raise
    
    async def upsert_produto(self, produto_data: Dict[str, Any]) -> str:
        """Insert or update produto record with duplicate detection"""
        try:
            # Validate data
            validation = self.validator.validate_produto_data(produto_data)
            if not validation.is_valid:
                raise ValueError(f"Dados de produto inválidos: {', '.join(validation.errors)}")
            
            codigo_produto = produto_data['codigo_produto']
            
            upsert_data = {
                'codigo_produto': codigo_produto,
                'ean': produto_data.get('ean'),
                'descricao': produto_data.get('descricao'),
                'ncm': produto_data.get('ncm'),
                'cest': produto_data.get('cest'),
                'cfop': produto_data.get('cfop'),
                'unidade_comercial': produto_data.get('unidade_comercial'),
                'unidade_tributavel': produto_data.get('unidade_tributavel'),
                'categoria': produto_data.get('categoria'),
                'subcategoria': produto_data.get('subcategoria'),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values
            upsert_data = {k: v for k, v in upsert_data.items() if v is not None}
            
            # Perform upsert operation
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_produtos')
                .upsert(upsert_data, on_conflict='codigo_produto')
                .execute()
            )
            
            logger.info(
                "Produto upserted successfully",
                codigo_produto=codigo_produto,
                descricao=produto_data.get('descricao'),
                categoria=produto_data.get('categoria'),
                admin_mode=self.admin_mode
            )
            
            return codigo_produto
            
        except Exception as e:
            logger.error("Failed to upsert produto", error=str(e), data=produto_data)
            raise
    
    async def upsert_servico(self, servico_data: Dict[str, Any]) -> str:
        """Insert or update servico record with duplicate detection"""
        try:
            # Validate data
            validation = self.validator.validate_servico_data(servico_data)
            if not validation.is_valid:
                raise ValueError(f"Dados de serviço inválidos: {', '.join(validation.errors)}")
            
            codigo_servico = servico_data['codigo_servico']
            
            upsert_data = {
                'codigo_servico': codigo_servico,
                'descricao': servico_data.get('descricao'),
                'codigo_cnae': servico_data.get('codigo_cnae'),
                'codigo_tributacao_nacional': servico_data.get('codigo_tributacao_nacional'),
                'codigo_tributacao_municipal': servico_data.get('codigo_tributacao_municipal'),
                'codigo_nbs': servico_data.get('codigo_nbs'),
                'categoria': servico_data.get('categoria'),
                'subcategoria': servico_data.get('subcategoria'),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Remove None values
            upsert_data = {k: v for k, v in upsert_data.items() if v is not None}
            
            # Perform upsert operation
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_servicos')
                .upsert(upsert_data, on_conflict='codigo_servico')
                .execute()
            )
            
            logger.info(
                "Servico upserted successfully",
                codigo_servico=codigo_servico,
                descricao=servico_data.get('descricao'),
                categoria=servico_data.get('categoria'),
                admin_mode=self.admin_mode
            )
            
            return codigo_servico
            
        except Exception as e:
            logger.error("Failed to upsert servico", error=str(e), data=servico_data)
            raise
    
    async def insert_fact_item_nfe(self, item_data: Dict[str, Any]) -> str:
        """Insert NF-e item into fact table with foreign key validation"""
        try:
            # Validate required fields
            required_fields = ['chave_nfe', 'numero_item', 'codigo_produto', 'descricao']
            for field in required_fields:
                if not item_data.get(field):
                    raise ValueError(f"Campo obrigatório ausente: {field}")
            
            # Validate foreign key references
            await self._validate_nfe_exists(item_data['chave_nfe'])
            await self._validate_produto_exists(item_data['codigo_produto'])
            
            # Check for duplicate item
            existing_item = await self._check_duplicate_nfe_item(
                item_data['chave_nfe'], 
                item_data['numero_item']
            )
            
            if existing_item:
                logger.warning(
                    "Item NFe já existe, ignorando inserção",
                    chave_nfe=item_data['chave_nfe'],
                    numero_item=item_data['numero_item']
                )
                return existing_item['id']
            
            # Prepare fact data with automatic calculations
            fact_data = {
                'chave_nfe': item_data['chave_nfe'],
                'numero_item': item_data['numero_item'],
                'codigo_produto': item_data['codigo_produto'],
                'ean': item_data.get('ean'),
                'descricao': item_data['descricao'],
                'ncm': item_data.get('ncm'),
                'cest': item_data.get('cest'),
                'cfop': item_data.get('cfop'),
                'unidade_comercial': item_data.get('unidade_comercial'),
                'quantidade_comercial': self._to_decimal(item_data.get('quantidade_comercial')),
                'valor_unitario_comercial': self._to_decimal(item_data.get('valor_unitario_comercial')),
                'valor_total_bruto': self._to_decimal(item_data.get('valor_total_bruto')),
                'ean_tributavel': item_data.get('ean_tributavel'),
                'unidade_tributavel': item_data.get('unidade_tributavel'),
                'quantidade_tributavel': self._to_decimal(item_data.get('quantidade_tributavel')),
                'valor_unitario_tributavel': self._to_decimal(item_data.get('valor_unitario_tributavel')),
                'valor_frete': self._to_decimal(item_data.get('valor_frete')),
                'valor_seguro': self._to_decimal(item_data.get('valor_seguro')),
                'valor_desconto': self._to_decimal(item_data.get('valor_desconto')),
                'valor_outras_despesas': self._to_decimal(item_data.get('valor_outras_despesas')),
                # Tax information
                'origem_produto': item_data.get('origem_produto'),
                'situacao_tributaria_icms': item_data.get('situacao_tributaria_icms'),
                'base_calculo_icms': self._to_decimal(item_data.get('base_calculo_icms')),
                'aliquota_icms': self._to_decimal(item_data.get('aliquota_icms')),
                'valor_icms': self._to_decimal(item_data.get('valor_icms')),
                'situacao_tributaria_ipi': item_data.get('situacao_tributaria_ipi'),
                'base_calculo_ipi': self._to_decimal(item_data.get('base_calculo_ipi')),
                'aliquota_ipi': self._to_decimal(item_data.get('aliquota_ipi')),
                'valor_ipi': self._to_decimal(item_data.get('valor_ipi')),
                'situacao_tributaria_pis': item_data.get('situacao_tributaria_pis'),
                'base_calculo_pis': self._to_decimal(item_data.get('base_calculo_pis')),
                'aliquota_pis': self._to_decimal(item_data.get('aliquota_pis')),
                'valor_pis': self._to_decimal(item_data.get('valor_pis')),
                'situacao_tributaria_cofins': item_data.get('situacao_tributaria_cofins'),
                'base_calculo_cofins': self._to_decimal(item_data.get('base_calculo_cofins')),
                'aliquota_cofins': self._to_decimal(item_data.get('aliquota_cofins')),
                'valor_cofins': self._to_decimal(item_data.get('valor_cofins')),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate derived values if not provided
            if not fact_data['valor_total_bruto'] and fact_data['quantidade_comercial'] and fact_data['valor_unitario_comercial']:
                fact_data['valor_total_bruto'] = fact_data['quantidade_comercial'] * fact_data['valor_unitario_comercial']
            
            # Remove None values
            fact_data = {k: v for k, v in fact_data.items() if v is not None}
            
            # Insert fact record
            result = await asyncio.to_thread(
                lambda: self.client.client.table('fact_itens_nfe')
                .insert(fact_data)
                .execute()
            )
            
            fact_id = result.data[0]['id']
            
            logger.info(
                "Item NFe inserted successfully",
                fact_id=fact_id,
                chave_nfe=item_data['chave_nfe'],
                numero_item=item_data['numero_item'],
                codigo_produto=item_data['codigo_produto'],
                valor_total=fact_data.get('valor_total_bruto'),
                admin_mode=self.admin_mode
            )
            
            return str(fact_id)
            
        except Exception as e:
            logger.error("Failed to insert fact item NFe", error=str(e), data=item_data)
            raise
    
    async def insert_fact_servico_nfse(self, servico_data: Dict[str, Any]) -> str:
        """Insert NFS-e service into fact table with foreign key validation"""
        try:
            # Validate required fields
            required_fields = ['id_nfse', 'codigo_servico', 'descricao_servico']
            for field in required_fields:
                if not servico_data.get(field):
                    raise ValueError(f"Campo obrigatório ausente: {field}")
            
            # Validate foreign key references
            await self._validate_nfse_exists(servico_data['id_nfse'])
            await self._validate_servico_exists(servico_data['codigo_servico'])
            
            # Check for duplicate service
            existing_service = await self._check_duplicate_nfse_service(
                servico_data['id_nfse'], 
                servico_data['codigo_servico']
            )
            
            if existing_service:
                logger.warning(
                    "Serviço NFSe já existe, ignorando inserção",
                    id_nfse=servico_data['id_nfse'],
                    codigo_servico=servico_data['codigo_servico']
                )
                return existing_service['id']
            
            # Prepare fact data with automatic calculations
            fact_data = {
                'id_nfse': servico_data['id_nfse'],
                'codigo_servico': servico_data['codigo_servico'],
                'descricao_servico': servico_data['descricao_servico'],
                'quantidade': self._to_decimal(servico_data.get('quantidade', 1)),
                'valor_unitario': self._to_decimal(servico_data.get('valor_unitario')),
                'valor_total': self._to_decimal(servico_data.get('valor_total')),
                'valor_deducoes': self._to_decimal(servico_data.get('valor_deducoes')),
                'valor_base_calculo': self._to_decimal(servico_data.get('valor_base_calculo')),
                'aliquota_issqn': self._to_decimal(servico_data.get('aliquota_issqn')),
                'valor_issqn': self._to_decimal(servico_data.get('valor_issqn')),
                'valor_credito': self._to_decimal(servico_data.get('valor_credito')),
                'codigo_cnae': servico_data.get('codigo_cnae'),
                'codigo_tributacao_nacional': servico_data.get('codigo_tributacao_nacional'),
                'codigo_tributacao_municipal': servico_data.get('codigo_tributacao_municipal'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Calculate derived values if not provided
            if not fact_data['valor_total'] and fact_data['quantidade'] and fact_data['valor_unitario']:
                fact_data['valor_total'] = fact_data['quantidade'] * fact_data['valor_unitario']
            
            if not fact_data['valor_base_calculo'] and fact_data['valor_total'] and fact_data['valor_deducoes']:
                fact_data['valor_base_calculo'] = fact_data['valor_total'] - fact_data['valor_deducoes']
            elif not fact_data['valor_base_calculo'] and fact_data['valor_total']:
                fact_data['valor_base_calculo'] = fact_data['valor_total']
            
            if not fact_data['valor_issqn'] and fact_data['valor_base_calculo'] and fact_data['aliquota_issqn']:
                fact_data['valor_issqn'] = fact_data['valor_base_calculo'] * (fact_data['aliquota_issqn'] / 100)
            
            # Remove None values
            fact_data = {k: v for k, v in fact_data.items() if v is not None}
            
            # Insert fact record
            result = await asyncio.to_thread(
                lambda: self.client.client.table('fact_servicos_nfse')
                .insert(fact_data)
                .execute()
            )
            
            fact_id = result.data[0]['id']
            
            logger.info(
                "Serviço NFSe inserted successfully",
                fact_id=fact_id,
                id_nfse=servico_data['id_nfse'],
                codigo_servico=servico_data['codigo_servico'],
                valor_total=fact_data.get('valor_total'),
                admin_mode=self.admin_mode
            )
            
            return str(fact_id)
            
        except Exception as e:
            logger.error("Failed to insert fact servico NFSe", error=str(e), data=servico_data)
            raise
    
    # Helper methods for validation and calculations
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal safely"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            elif isinstance(value, str):
                # Remove common formatting
                clean_value = value.replace(',', '.').replace(' ', '')
                return Decimal(clean_value)
            elif isinstance(value, Decimal):
                return value
            else:
                return None
        except (ValueError, TypeError):
            return None
    
    async def _validate_nfe_exists(self, chave_nfe: str):
        """Validate that NFe main record exists"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('nfe_main')
                .select('chave_nfe')
                .eq('chave_nfe', chave_nfe)
                .limit(1)
                .execute()
            )
            
            if not result.data:
                raise ValueError(f"NFe não encontrada: {chave_nfe}")
                
        except Exception as e:
            logger.error("Failed to validate NFe existence", error=str(e), chave_nfe=chave_nfe)
            raise
    
    async def _validate_nfse_exists(self, id_nfse: str):
        """Validate that NFSe main record exists"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('nfse_main')
                .select('id_nfse')
                .eq('id_nfse', id_nfse)
                .limit(1)
                .execute()
            )
            
            if not result.data:
                raise ValueError(f"NFSe não encontrada: {id_nfse}")
                
        except Exception as e:
            logger.error("Failed to validate NFSe existence", error=str(e), id_nfse=id_nfse)
            raise
    
    async def _validate_produto_exists(self, codigo_produto: str):
        """Validate that produto record exists"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_produtos')
                .select('codigo_produto')
                .eq('codigo_produto', codigo_produto)
                .limit(1)
                .execute()
            )
            
            if not result.data:
                raise ValueError(f"Produto não encontrado: {codigo_produto}")
                
        except Exception as e:
            logger.error("Failed to validate produto existence", error=str(e), codigo_produto=codigo_produto)
            raise
    
    async def _validate_servico_exists(self, codigo_servico: str):
        """Validate that servico record exists"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_servicos')
                .select('codigo_servico')
                .eq('codigo_servico', codigo_servico)
                .limit(1)
                .execute()
            )
            
            if not result.data:
                raise ValueError(f"Serviço não encontrado: {codigo_servico}")
                
        except Exception as e:
            logger.error("Failed to validate servico existence", error=str(e), codigo_servico=codigo_servico)
            raise
    
    async def _check_duplicate_nfe_item(self, chave_nfe: str, numero_item: int) -> Optional[Dict[str, Any]]:
        """Check for duplicate NFe item"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('fact_itens_nfe')
                .select('id')
                .eq('chave_nfe', chave_nfe)
                .eq('numero_item', numero_item)
                .limit(1)
                .execute()
            )
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error("Failed to check duplicate NFe item", error=str(e))
            return None
    
    async def _check_duplicate_nfse_service(self, id_nfse: str, codigo_servico: str) -> Optional[Dict[str, Any]]:
        """Check for duplicate NFSe service"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.client.table('fact_servicos_nfse')
                .select('id')
                .eq('id_nfse', id_nfse)
                .eq('codigo_servico', codigo_servico)
                .limit(1)
                .execute()
            )
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error("Failed to check duplicate NFSe service", error=str(e))
            return None


class IntegrityReport:
    """Report of referential integrity validation"""
    
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.orphaned_records = []
        self.missing_references = []
        self.statistics = {}
    
    def add_error(self, error: str):
        """Add integrity error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add integrity warning"""
        self.warnings.append(warning)
    
    def add_orphaned_record(self, table: str, record_id: str, reference_field: str, reference_value: str):
        """Add orphaned record information"""
        self.orphaned_records.append({
            'table': table,
            'record_id': record_id,
            'reference_field': reference_field,
            'reference_value': reference_value
        })
        self.is_valid = False
    
    def add_missing_reference(self, table: str, field: str, value: str):
        """Add missing reference information"""
        self.missing_references.append({
            'table': table,
            'field': field,
            'value': value
        })
        self.is_valid = False
    
    def set_statistics(self, stats: Dict[str, Any]):
        """Set validation statistics"""
        self.statistics = stats


class ReferentialIntegrityValidator:
    """Validator for referential integrity across dimensional and fact tables"""
    
    def __init__(self, client: SupabaseClient):
        self.client = client
    
    async def validate_referential_integrity(self, document_id: Optional[str] = None) -> IntegrityReport:
        """Validate referential integrity for processed document or entire database"""
        report = IntegrityReport()
        
        try:
            # Collect statistics
            stats = await self._collect_statistics()
            report.set_statistics(stats)
            
            # Validate dimension table integrity
            await self._validate_dimension_integrity(report)
            
            # Validate fact table foreign keys
            await self._validate_fact_table_integrity(report, document_id)
            
            # Check for orphaned records
            await self._check_orphaned_records(report, document_id)
            
            # Validate business rules
            await self._validate_business_rules(report, document_id)
            
            logger.info(
                "Referential integrity validation completed",
                document_id=document_id,
                is_valid=report.is_valid,
                errors_count=len(report.errors),
                warnings_count=len(report.warnings),
                orphaned_count=len(report.orphaned_records)
            )
            
            return report
            
        except Exception as e:
            logger.error("Failed to validate referential integrity", error=str(e), document_id=document_id)
            report.add_error(f"Falha na validação de integridade: {str(e)}")
            return report
    
    async def _collect_statistics(self) -> Dict[str, Any]:
        """Collect database statistics"""
        try:
            stats = {}
            
            # Count records in each table
            tables = ['dim_emitente', 'dim_destinatario', 'dim_produtos', 'dim_servicos', 
                     'fact_itens_nfe', 'fact_servicos_nfse', 'nfe_main', 'nfse_main']
            
            for table in tables:
                result = await asyncio.to_thread(
                    lambda t=table: self.client.client.table(t).select('*', count='exact').limit(0).execute()
                )
                stats[f'{table}_count'] = result.count
            
            return stats
            
        except Exception as e:
            logger.error("Failed to collect statistics", error=str(e))
            return {}
    
    async def _validate_dimension_integrity(self, report: IntegrityReport):
        """Validate dimension table data integrity"""
        try:
            # Validate emitente data
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_emitente')
                .select('cnpj, razao_social')
                .execute()
            )
            
            for emitente in result.data:
                if not emitente.get('razao_social'):
                    report.add_error(f"Emitente sem razão social: {emitente.get('cnpj')}")
                
                cnpj = emitente.get('cnpj')
                if cnpj and not cnpj.startswith('CPF_') and not ValidadorDocumentosBrasileiros.validar_cnpj(cnpj):
                    report.add_warning(f"CNPJ inválido para emitente: {cnpj}")
            
            # Validate destinatario data
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_destinatario')
                .select('id, cnpj, cpf')
                .execute()
            )
            
            for destinatario in result.data:
                cnpj = destinatario.get('cnpj')
                cpf = destinatario.get('cpf')
                
                if not cnpj and not cpf:
                    report.add_error(f"Destinatário sem CNPJ ou CPF: ID {destinatario.get('id')}")
                
                if cnpj and not ValidadorDocumentosBrasileiros.validar_cnpj(cnpj):
                    report.add_warning(f"CNPJ inválido para destinatário: {cnpj}")
                
                if cpf and not ValidadorDocumentosBrasileiros.validar_cpf(cpf):
                    report.add_warning(f"CPF inválido para destinatário: {cpf}")
            
            # Validate produto data
            result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_produtos')
                .select('codigo_produto, descricao, ncm')
                .execute()
            )
            
            for produto in result.data:
                if not produto.get('descricao'):
                    report.add_error(f"Produto sem descrição: {produto.get('codigo_produto')}")
                
                ncm = produto.get('ncm')
                if ncm and (not ncm.isdigit() or len(ncm) != 8):
                    report.add_warning(f"NCM inválido para produto {produto.get('codigo_produto')}: {ncm}")
            
        except Exception as e:
            logger.error("Failed to validate dimension integrity", error=str(e))
            report.add_error(f"Erro na validação de dimensões: {str(e)}")
    
    async def _validate_fact_table_integrity(self, report: IntegrityReport, document_id: Optional[str] = None):
        """Validate fact table foreign key integrity"""
        try:
            # Validate NFe items foreign keys
            query = self.client.client.table('fact_itens_nfe').select('id, chave_nfe, codigo_produto')
            
            if document_id:
                # Filter by document if specified (assuming we can link through chave_nfe)
                query = query.like('chave_nfe', f'%{document_id}%')
            
            result = await asyncio.to_thread(lambda: query.execute())
            
            for item in result.data:
                # Check NFe main reference
                nfe_result = await asyncio.to_thread(
                    lambda: self.client.client.table('nfe_main')
                    .select('chave_nfe')
                    .eq('chave_nfe', item['chave_nfe'])
                    .limit(1)
                    .execute()
                )
                
                if not nfe_result.data:
                    report.add_orphaned_record(
                        'fact_itens_nfe', 
                        str(item['id']), 
                        'chave_nfe', 
                        item['chave_nfe']
                    )
                
                # Check produto reference
                produto_result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_produtos')
                    .select('codigo_produto')
                    .eq('codigo_produto', item['codigo_produto'])
                    .limit(1)
                    .execute()
                )
                
                if not produto_result.data:
                    report.add_orphaned_record(
                        'fact_itens_nfe', 
                        str(item['id']), 
                        'codigo_produto', 
                        item['codigo_produto']
                    )
            
            # Validate NFSe services foreign keys
            query = self.client.client.table('fact_servicos_nfse').select('id, id_nfse, codigo_servico')
            
            if document_id:
                query = query.like('id_nfse', f'%{document_id}%')
            
            result = await asyncio.to_thread(lambda: query.execute())
            
            for servico in result.data:
                # Check NFSe main reference
                nfse_result = await asyncio.to_thread(
                    lambda: self.client.client.table('nfse_main')
                    .select('id_nfse')
                    .eq('id_nfse', servico['id_nfse'])
                    .limit(1)
                    .execute()
                )
                
                if not nfse_result.data:
                    report.add_orphaned_record(
                        'fact_servicos_nfse', 
                        str(servico['id']), 
                        'id_nfse', 
                        servico['id_nfse']
                    )
                
                # Check servico reference
                servico_result = await asyncio.to_thread(
                    lambda: self.client.client.table('dim_servicos')
                    .select('codigo_servico')
                    .eq('codigo_servico', servico['codigo_servico'])
                    .limit(1)
                    .execute()
                )
                
                if not servico_result.data:
                    report.add_orphaned_record(
                        'fact_servicos_nfse', 
                        str(servico['id']), 
                        'codigo_servico', 
                        servico['codigo_servico']
                    )
            
        except Exception as e:
            logger.error("Failed to validate fact table integrity", error=str(e))
            report.add_error(f"Erro na validação de tabelas de fato: {str(e)}")
    
    async def _check_orphaned_records(self, report: IntegrityReport, document_id: Optional[str] = None):
        """Check for orphaned records in dimension tables"""
        try:
            # Check for unused produtos
            result = await asyncio.to_thread(
                lambda: self.client.client.rpc('check_unused_produtos').execute()
            )
            
            # Since RPC might not be available, use manual check
            produtos_result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_produtos')
                .select('codigo_produto')
                .execute()
            )
            
            for produto in produtos_result.data:
                usage_result = await asyncio.to_thread(
                    lambda: self.client.client.table('fact_itens_nfe')
                    .select('id')
                    .eq('codigo_produto', produto['codigo_produto'])
                    .limit(1)
                    .execute()
                )
                
                if not usage_result.data:
                    report.add_warning(f"Produto não utilizado: {produto['codigo_produto']}")
            
            # Check for unused servicos
            servicos_result = await asyncio.to_thread(
                lambda: self.client.client.table('dim_servicos')
                .select('codigo_servico')
                .execute()
            )
            
            for servico in servicos_result.data:
                usage_result = await asyncio.to_thread(
                    lambda: self.client.client.table('fact_servicos_nfse')
                    .select('id')
                    .eq('codigo_servico', servico['codigo_servico'])
                    .limit(1)
                    .execute()
                )
                
                if not usage_result.data:
                    report.add_warning(f"Serviço não utilizado: {servico['codigo_servico']}")
            
        except Exception as e:
            logger.error("Failed to check orphaned records", error=str(e))
            report.add_warning(f"Não foi possível verificar registros órfãos: {str(e)}")
    
    async def _validate_business_rules(self, report: IntegrityReport, document_id: Optional[str] = None):
        """Validate Brazilian business rules"""
        try:
            # Validate NFe totals consistency
            nfe_query = self.client.client.table('nfe_main').select('chave_nfe, valor_total_nf')
            
            if document_id:
                nfe_query = nfe_query.like('chave_nfe', f'%{document_id}%')
            
            nfe_result = await asyncio.to_thread(lambda: nfe_query.execute())
            
            for nfe in nfe_result.data:
                # Calculate sum of items
                items_result = await asyncio.to_thread(
                    lambda: self.client.client.table('fact_itens_nfe')
                    .select('valor_total_bruto')
                    .eq('chave_nfe', nfe['chave_nfe'])
                    .execute()
                )
                
                items_total = sum(
                    Decimal(str(item['valor_total_bruto'])) 
                    for item in items_result.data 
                    if item.get('valor_total_bruto')
                )
                
                nfe_total = Decimal(str(nfe['valor_total_nf'])) if nfe.get('valor_total_nf') else Decimal('0')
                
                # Allow small differences due to rounding
                if abs(items_total - nfe_total) > Decimal('0.01'):
                    report.add_error(
                        f"Inconsistência de valores NFe {nfe['chave_nfe']}: "
                        f"Total NFe: {nfe_total}, Soma itens: {items_total}"
                    )
            
            # Validate NFSe totals consistency
            nfse_query = self.client.client.table('nfse_main').select('id_nfse, valor_total_servicos')
            
            if document_id:
                nfse_query = nfse_query.like('id_nfse', f'%{document_id}%')
            
            nfse_result = await asyncio.to_thread(lambda: nfse_query.execute())
            
            for nfse in nfse_result.data:
                # Calculate sum of services
                services_result = await asyncio.to_thread(
                    lambda: self.client.client.table('fact_servicos_nfse')
                    .select('valor_total')
                    .eq('id_nfse', nfse['id_nfse'])
                    .execute()
                )
                
                services_total = sum(
                    Decimal(str(service['valor_total'])) 
                    for service in services_result.data 
                    if service.get('valor_total')
                )
                
                nfse_total = Decimal(str(nfse['valor_total_servicos'])) if nfse.get('valor_total_servicos') else Decimal('0')
                
                # Allow small differences due to rounding
                if abs(services_total - nfse_total) > Decimal('0.01'):
                    report.add_error(
                        f"Inconsistência de valores NFSe {nfse['id_nfse']}: "
                        f"Total NFSe: {nfse_total}, Soma serviços: {services_total}"
                    )
            
        except Exception as e:
            logger.error("Failed to validate business rules", error=str(e))
            report.add_error(f"Erro na validação de regras de negócio: {str(e)}")


# Add referential integrity methods to DimensionalDataManager
class DimensionalDataManager(DimensionalDataManager):
    """Extended DimensionalDataManager with referential integrity validation"""
    
    def __init__(self, admin_mode: bool = False):
        super().__init__(admin_mode)
        self.integrity_validator = ReferentialIntegrityValidator(self.client)
    
    async def validate_referential_integrity(self, document_id: Optional[str] = None) -> IntegrityReport:
        """Validate referential integrity for processed document or entire database"""
        return await self.integrity_validator.validate_referential_integrity(document_id)
    
    async def fix_integrity_issues(self, report: IntegrityReport, auto_fix: bool = False) -> Dict[str, Any]:
        """Attempt to fix referential integrity issues"""
        try:
            fixes_applied = []
            fixes_failed = []
            
            if auto_fix:
                # Auto-fix orphaned records by creating missing references
                for orphaned in report.orphaned_records:
                    try:
                        if orphaned['table'] == 'fact_itens_nfe' and orphaned['reference_field'] == 'codigo_produto':
                            # Create missing produto record
                            await self.upsert_produto({
                                'codigo_produto': orphaned['reference_value'],
                                'descricao': f"Produto criado automaticamente: {orphaned['reference_value']}",
                                'categoria': 'Não categorizado'
                            })
                            fixes_applied.append(f"Produto criado: {orphaned['reference_value']}")
                        
                        elif orphaned['table'] == 'fact_servicos_nfse' and orphaned['reference_field'] == 'codigo_servico':
                            # Create missing servico record
                            await self.upsert_servico({
                                'codigo_servico': orphaned['reference_value'],
                                'descricao': f"Serviço criado automaticamente: {orphaned['reference_value']}",
                                'categoria': 'Não categorizado'
                            })
                            fixes_applied.append(f"Serviço criado: {orphaned['reference_value']}")
                        
                    except Exception as e:
                        fixes_failed.append(f"Falha ao corrigir {orphaned['reference_value']}: {str(e)}")
            
            logger.info(
                "Integrity fixes completed",
                fixes_applied_count=len(fixes_applied),
                fixes_failed_count=len(fixes_failed),
                auto_fix=auto_fix
            )
            
            return {
                'fixes_applied': fixes_applied,
                'fixes_failed': fixes_failed,
                'auto_fix_enabled': auto_fix
            }
            
        except Exception as e:
            logger.error("Failed to fix integrity issues", error=str(e))
            raise
    
    async def generate_integrity_report(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive integrity report"""
        try:
            report = await self.validate_referential_integrity(document_id)
            
            return {
                'validation_timestamp': datetime.now(timezone.utc).isoformat(),
                'document_id': document_id,
                'is_valid': report.is_valid,
                'summary': {
                    'errors_count': len(report.errors),
                    'warnings_count': len(report.warnings),
                    'orphaned_records_count': len(report.orphaned_records),
                    'missing_references_count': len(report.missing_references)
                },
                'errors': report.errors,
                'warnings': report.warnings,
                'orphaned_records': report.orphaned_records,
                'missing_references': report.missing_references,
                'statistics': report.statistics
            }
            
        except Exception as e:
            logger.error("Failed to generate integrity report", error=str(e))
            raise