"""
Data Lake Agent - Gerencia armazenamento centralizado e integridade dos dados fiscais
Responsável por armazenar dados estruturados com verificações de integridade,
preservar dados históricos e manter integridade referencial entre entidades.
"""

import asyncio
import asyncpg
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
from dataclasses import asdict

from .base_agent import BaseAgent
from models.fiscal_data import (
    NFEData, NFSEData, FiscalDocument, Supplier, Recipient, 
    Product, Service, NFEItem, NFSEItem, Address, DocumentType
)
from utils.database import DatabaseManager, get_db_connection
from utils.config import settings

logger = structlog.get_logger()

class DataIntegrityError(Exception):
    """Exceção para erros de integridade de dados"""
    pass

class DataLakeAgent(BaseAgent):
    """
    Agente responsável pelo gerenciamento do Data Lake fiscal.
    
    Funcionalidades principais:
    - Armazenamento estruturado de dados fiscais com verificações de integridade
    - Preservação de dados históricos com arquivamento automatizado
    - Manutenção de integridade referencial entre entidades
    - Otimização de acesso para consultas complexas
    """
    
    def __init__(self):
        super().__init__("DataLakeAgent")
        self.db_manager = DatabaseManager()
        self.integrity_check_interval = 3600  # 1 hora em segundos
        self.archival_retention_days = 2555  # 7 anos (requisito fiscal brasileiro)
        self._integrity_task = None
        
    async def initialize(self):
        """Inicializa o agente e verifica conectividade do banco"""
        try:
            # Verifica conectividade do banco de dados
            await self._verify_database_connectivity()
            
            # Inicia tarefa de verificação de integridade periódica
            self._integrity_task = asyncio.create_task(self._periodic_integrity_check())
            
            self.logger.info("Data Lake Agent inicializado com sucesso")
            
        except Exception as e:
            self.logger.error("Falha na inicialização do Data Lake Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Limpa recursos do agente"""
        if self._integrity_task:
            self._integrity_task.cancel()
            try:
                await self._integrity_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Data Lake Agent finalizado")
    
    async def process(self, data: FiscalDocument) -> Dict[str, Any]:
        """
        Processa e armazena documento fiscal no Data Lake
        
        Args:
            data: Documento fiscal (NFEData ou NFSEData)
            
        Returns:
            Dict com resultado do armazenamento
        """
        try:
            self.logger.info("Iniciando armazenamento de documento fiscal", 
                           document_type=data.document_type.value,
                           document_id=getattr(data, 'chave_nfe', None) or getattr(data, 'id_nfse', None))
            
            # Valida dados antes do armazenamento
            await self._validate_fiscal_data(data)
            
            # Armazena documento baseado no tipo
            if data.document_type == DocumentType.NFE:
                result = await self._store_nfe_data(data)
            elif data.document_type == DocumentType.NFSE:
                result = await self._store_nfse_data(data)
            else:
                raise ValueError(f"Tipo de documento não suportado: {data.document_type}")
            
            # Verifica integridade após armazenamento
            await self._verify_data_integrity(data)
            
            self.logger.info("Documento fiscal armazenado com sucesso", 
                           document_type=data.document_type.value,
                           storage_result=result)
            
            return {
                "status": "success",
                "document_type": data.document_type.value,
                "document_id": result.get("document_id"),
                "records_inserted": result.get("records_inserted", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Erro no armazenamento de documento fiscal", 
                            document_type=data.document_type.value if hasattr(data, 'document_type') else 'unknown',
                            error=str(e))
            raise DataIntegrityError(f"Falha no armazenamento: {str(e)}")
    
    async def _verify_database_connectivity(self):
        """Verifica conectividade com o banco de dados"""
        try:
            async with get_db_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise ConnectionError("Falha na verificação de conectividade")
                    
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao banco de dados: {str(e)}")
    
    async def _validate_fiscal_data(self, data: FiscalDocument):
        """
        Valida dados fiscais antes do armazenamento
        
        Args:
            data: Documento fiscal a ser validado
        """
        if data.document_type == DocumentType.NFE:
            await self._validate_nfe_data(data)
        elif data.document_type == DocumentType.NFSE:
            await self._validate_nfse_data(data)
    
    async def _validate_nfe_data(self, nfe_data: NFEData):
        """Valida dados específicos de NF-e"""
        # Validações obrigatórias para NF-e
        if not nfe_data.chave_nfe or len(nfe_data.chave_nfe) != 44:
            raise DataIntegrityError("Chave NF-e inválida ou ausente")
        
        if not nfe_data.numero_nf:
            raise DataIntegrityError("Número da NF-e é obrigatório")
        
        if not nfe_data.supplier or not nfe_data.supplier.cnpj:
            raise DataIntegrityError("CNPJ do emitente é obrigatório")
        
        if not nfe_data.items:
            raise DataIntegrityError("NF-e deve conter pelo menos um item")
        
        # Valida consistência de valores
        total_items = sum(item.valor_total_bruto for item in nfe_data.items)
        if abs(total_items - nfe_data.valor_total_produtos) > Decimal('0.01'):
            raise DataIntegrityError("Inconsistência entre total de itens e valor total de produtos")
    
    async def _validate_nfse_data(self, nfse_data: NFSEData):
        """Valida dados específicos de NFS-e"""
        # Validações obrigatórias para NFS-e
        if not nfse_data.id_nfse:
            raise DataIntegrityError("ID da NFS-e é obrigatório")
        
        if not nfse_data.numero_nfse:
            raise DataIntegrityError("Número da NFS-e é obrigatório")
        
        if not nfse_data.supplier or not nfse_data.supplier.cnpj:
            raise DataIntegrityError("CNPJ do prestador é obrigatório")
        
        if not nfse_data.services:
            raise DataIntegrityError("NFS-e deve conter pelo menos um serviço")
        
        # Valida consistência de valores
        total_services = sum(service.valor_total for service in nfse_data.services)
        if abs(total_services - nfse_data.valor_total_servicos) > Decimal('0.01'):
            raise DataIntegrityError("Inconsistência entre total de serviços e valor total")
    
    async def _store_nfe_data(self, nfe_data: NFEData) -> Dict[str, Any]:
        """
        Armazena dados de NF-e no Data Lake
        
        Args:
            nfe_data: Dados da NF-e
            
        Returns:
            Dict com resultado do armazenamento
        """
        records_inserted = 0
        
        async with get_db_connection() as conn:
            async with conn.transaction():
                # 1. Armazena/atualiza emitente
                await self._upsert_supplier(conn, nfe_data.supplier)
                records_inserted += 1
                
                # 2. Armazena/atualiza destinatário
                recipient_id = await self._upsert_recipient(conn, nfe_data.recipient)
                records_inserted += 1
                
                # 3. Armazena/atualiza produtos
                for item in nfe_data.items:
                    await self._upsert_product(conn, item.produto)
                    records_inserted += 1
                
                # 4. Armazena NF-e principal
                await self._insert_nfe_main(conn, nfe_data, recipient_id)
                records_inserted += 1
                
                # 5. Armazena itens da NF-e
                for item in nfe_data.items:
                    await self._insert_nfe_item(conn, nfe_data.chave_nfe, item)
                    records_inserted += 1
        
        return {
            "document_id": nfe_data.chave_nfe,
            "records_inserted": records_inserted,
            "document_type": "NFE"
        }
    
    async def _store_nfse_data(self, nfse_data: NFSEData) -> Dict[str, Any]:
        """
        Armazena dados de NFS-e no Data Lake
        
        Args:
            nfse_data: Dados da NFS-e
            
        Returns:
            Dict com resultado do armazenamento
        """
        records_inserted = 0
        
        async with get_db_connection() as conn:
            async with conn.transaction():
                # 1. Armazena/atualiza prestador
                await self._upsert_supplier(conn, nfse_data.supplier)
                records_inserted += 1
                
                # 2. Armazena/atualiza tomador
                recipient_id = await self._upsert_recipient(conn, nfse_data.recipient)
                records_inserted += 1
                
                # 3. Armazena/atualiza serviços
                for service_item in nfse_data.services:
                    await self._upsert_service(conn, service_item.servico)
                    records_inserted += 1
                
                # 4. Armazena NFS-e principal
                await self._insert_nfse_main(conn, nfse_data, recipient_id)
                records_inserted += 1
                
                # 5. Armazena serviços da NFS-e
                for service_item in nfse_data.services:
                    await self._insert_nfse_service(conn, nfse_data.id_nfse, service_item)
                    records_inserted += 1
        
        return {
            "document_id": nfse_data.id_nfse,
            "records_inserted": records_inserted,
            "document_type": "NFSE"
        }
    
    async def _upsert_supplier(self, conn: asyncpg.Connection, supplier: Supplier):
        """Insere ou atualiza dados do fornecedor/prestador"""
        query = """
        INSERT INTO dim_emitente (
            cnpj, cpf, inscricao_estadual, razao_social, nome_fantasia,
            logradouro, numero, complemento, bairro, codigo_municipio,
            nome_municipio, uf, cep, codigo_pais, nome_pais,
            telefone, email, regime_tributario, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, NOW()
        )
        ON CONFLICT (cnpj) DO UPDATE SET
            cpf = EXCLUDED.cpf,
            inscricao_estadual = EXCLUDED.inscricao_estadual,
            razao_social = EXCLUDED.razao_social,
            nome_fantasia = EXCLUDED.nome_fantasia,
            logradouro = EXCLUDED.logradouro,
            numero = EXCLUDED.numero,
            complemento = EXCLUDED.complemento,
            bairro = EXCLUDED.bairro,
            codigo_municipio = EXCLUDED.codigo_municipio,
            nome_municipio = EXCLUDED.nome_municipio,
            uf = EXCLUDED.uf,
            cep = EXCLUDED.cep,
            codigo_pais = EXCLUDED.codigo_pais,
            nome_pais = EXCLUDED.nome_pais,
            telefone = EXCLUDED.telefone,
            email = EXCLUDED.email,
            regime_tributario = EXCLUDED.regime_tributario,
            updated_at = NOW()
        """
        
        await conn.execute(
            query,
            supplier.cnpj, supplier.cpf, supplier.inscricao_estadual,
            supplier.razao_social, supplier.nome_fantasia,
            supplier.address.logradouro, supplier.address.numero,
            supplier.address.complemento, supplier.address.bairro,
            supplier.address.codigo_municipio, supplier.address.nome_municipio,
            supplier.address.uf, supplier.address.cep,
            supplier.address.codigo_pais, supplier.address.nome_pais,
            supplier.telefone, supplier.email, supplier.regime_tributario
        )
    
    async def _upsert_recipient(self, conn: asyncpg.Connection, recipient: Recipient) -> int:
        """Insere ou atualiza dados do destinatário/tomador"""
        query = """
        INSERT INTO dim_destinatario (
            cnpj, cpf, inscricao_estadual, razao_social,
            logradouro, numero, complemento, bairro, codigo_municipio,
            nome_municipio, uf, cep, codigo_pais, nome_pais,
            telefone, email, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9,
            $10, $11, $12, $13, $14, $15, $16, NOW()
        )
        ON CONFLICT (cnpj, cpf) DO UPDATE SET
            inscricao_estadual = EXCLUDED.inscricao_estadual,
            razao_social = EXCLUDED.razao_social,
            logradouro = EXCLUDED.logradouro,
            numero = EXCLUDED.numero,
            complemento = EXCLUDED.complemento,
            bairro = EXCLUDED.bairro,
            codigo_municipio = EXCLUDED.codigo_municipio,
            nome_municipio = EXCLUDED.nome_municipio,
            uf = EXCLUDED.uf,
            cep = EXCLUDED.cep,
            codigo_pais = EXCLUDED.codigo_pais,
            nome_pais = EXCLUDED.nome_pais,
            telefone = EXCLUDED.telefone,
            email = EXCLUDED.email,
            updated_at = NOW()
        RETURNING id
        """
        
        result = await conn.fetchval(
            query,
            recipient.cnpj, recipient.cpf, recipient.inscricao_estadual,
            recipient.razao_social,
            recipient.address.logradouro, recipient.address.numero,
            recipient.address.complemento, recipient.address.bairro,
            recipient.address.codigo_municipio, recipient.address.nome_municipio,
            recipient.address.uf, recipient.address.cep,
            recipient.address.codigo_pais, recipient.address.nome_pais,
            recipient.telefone, recipient.email
        )
        
        # Se não retornou ID (caso de UPDATE), busca o ID existente
        if result is None:
            result = await conn.fetchval(
                "SELECT id FROM dim_destinatario WHERE cnpj = $1 OR cpf = $2",
                recipient.cnpj, recipient.cpf
            )
        
        return result
    
    async def _upsert_product(self, conn: asyncpg.Connection, product: Product):
        """Insere ou atualiza dados do produto"""
        query = """
        INSERT INTO dim_produtos (
            codigo_produto, ean, descricao, ncm, cest, cfop,
            unidade_comercial, unidade_tributavel, categoria, subcategoria, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW()
        )
        ON CONFLICT (codigo_produto) DO UPDATE SET
            ean = EXCLUDED.ean,
            descricao = EXCLUDED.descricao,
            ncm = EXCLUDED.ncm,
            cest = EXCLUDED.cest,
            cfop = EXCLUDED.cfop,
            unidade_comercial = EXCLUDED.unidade_comercial,
            unidade_tributavel = EXCLUDED.unidade_tributavel,
            categoria = EXCLUDED.categoria,
            subcategoria = EXCLUDED.subcategoria,
            updated_at = NOW()
        """
        
        await conn.execute(
            query,
            product.codigo_produto, product.ean, product.descricao,
            product.ncm, product.cest, product.cfop,
            product.unidade_comercial, product.unidade_tributavel,
            product.category, product.subcategory
        )
    
    async def _upsert_service(self, conn: asyncpg.Connection, service: Service):
        """Insere ou atualiza dados do serviço"""
        query = """
        INSERT INTO dim_servicos (
            codigo_servico, descricao, codigo_cnae, codigo_tributacao_nacional,
            codigo_tributacao_municipal, codigo_nbs, categoria, subcategoria, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, NOW()
        )
        ON CONFLICT (codigo_servico) DO UPDATE SET
            descricao = EXCLUDED.descricao,
            codigo_cnae = EXCLUDED.codigo_cnae,
            codigo_tributacao_nacional = EXCLUDED.codigo_tributacao_nacional,
            codigo_tributacao_municipal = EXCLUDED.codigo_tributacao_municipal,
            codigo_nbs = EXCLUDED.codigo_nbs,
            categoria = EXCLUDED.categoria,
            subcategoria = EXCLUDED.subcategoria,
            updated_at = NOW()
        """
        
        await conn.execute(
            query,
            service.codigo_servico, service.descricao, service.codigo_cnae,
            service.codigo_tributacao_nacional, service.codigo_tributacao_municipal,
            service.codigo_nbs, service.category, service.subcategory
        )
    
    async def _insert_nfe_main(self, conn: asyncpg.Connection, nfe_data: NFEData, recipient_id: int):
        """Insere dados principais da NF-e"""
        query = """
        INSERT INTO nfe_main (
            chave_nfe, numero_nf, serie, modelo, data_emissao, data_saida_entrada,
            tipo_operacao, codigo_municipio, uf_emitente, natureza_operacao,
            forma_pagamento, valor_total_nf, valor_total_produtos, valor_total_servicos,
            base_calculo_icms, valor_icms, base_calculo_icms_st, valor_icms_st,
            valor_total_ipi, valor_pis, valor_cofins, xml_file_path
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
        )
        ON CONFLICT (chave_nfe) DO UPDATE SET
            numero_nf = EXCLUDED.numero_nf,
            serie = EXCLUDED.serie,
            data_emissao = EXCLUDED.data_emissao,
            updated_at = NOW()
        """
        
        await conn.execute(
            query,
            nfe_data.chave_nfe, nfe_data.numero_nf, nfe_data.serie, nfe_data.modelo,
            nfe_data.data_emissao, nfe_data.data_saida_entrada, nfe_data.tipo_operacao,
            nfe_data.codigo_municipio, nfe_data.uf_emitente, nfe_data.natureza_operacao,
            nfe_data.forma_pagamento, nfe_data.valor_total_nf, nfe_data.valor_total_produtos,
            nfe_data.valor_total_servicos, nfe_data.base_calculo_icms, nfe_data.valor_icms,
            nfe_data.base_calculo_icms_st, nfe_data.valor_icms_st, nfe_data.valor_total_ipi,
            nfe_data.valor_pis, nfe_data.valor_cofins, nfe_data.xml_file_path
        )
    
    async def _insert_nfe_item(self, conn: asyncpg.Connection, chave_nfe: str, item: NFEItem):
        """Insere item da NF-e"""
        query = """
        INSERT INTO fact_itens_nfe (
            chave_nfe, numero_item, codigo_produto, ean, descricao, ncm, cest, cfop,
            unidade_comercial, quantidade_comercial, valor_unitario_comercial, valor_total_bruto,
            ean_tributavel, unidade_tributavel, quantidade_tributavel, valor_unitario_tributavel,
            valor_frete, valor_seguro, valor_desconto, valor_outras_despesas
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
        )
        ON CONFLICT (chave_nfe, numero_item) DO UPDATE SET
            codigo_produto = EXCLUDED.codigo_produto,
            valor_total_bruto = EXCLUDED.valor_total_bruto
        """
        
        await conn.execute(
            query,
            chave_nfe, item.numero_item, item.produto.codigo_produto, item.produto.ean,
            item.produto.descricao, item.produto.ncm, item.produto.cest, item.produto.cfop,
            item.produto.unidade_comercial, item.quantidade_comercial, item.valor_unitario_comercial,
            item.valor_total_bruto, None, item.produto.unidade_tributavel, item.quantidade_tributavel,
            item.valor_unitario_tributavel, item.valor_frete, item.valor_seguro, item.valor_desconto,
            item.valor_outras_despesas
        )
    
    async def _insert_nfse_main(self, conn: asyncpg.Connection, nfse_data: NFSEData, recipient_id: int):
        """Insere dados principais da NFS-e"""
        query = """
        INSERT INTO nfse_main (
            id_nfse, numero_nfse, numero_dfse, codigo_municipio_emissao, local_emissao,
            local_prestacao, codigo_municipio_incidencia, local_incidencia,
            tributacao_nacional, tributacao_municipal, codigo_nbs, data_emissao,
            data_processamento, ambiente_gerador, tipo_emissao, processo_emissao,
            codigo_status, valor_total_servicos, valor_total_deducoes, valor_base_calculo,
            valor_issqn, valor_credito, xml_file_path
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
        )
        ON CONFLICT (id_nfse) DO UPDATE SET
            numero_nfse = EXCLUDED.numero_nfse,
            valor_total_servicos = EXCLUDED.valor_total_servicos,
            updated_at = NOW()
        """
        
        await conn.execute(
            query,
            nfse_data.id_nfse, nfse_data.numero_nfse, nfse_data.numero_dfse,
            nfse_data.codigo_municipio_emissao, nfse_data.local_emissao, nfse_data.local_prestacao,
            nfse_data.codigo_municipio_incidencia, nfse_data.local_incidencia,
            nfse_data.tributacao_nacional, nfse_data.tributacao_municipal, nfse_data.codigo_nbs,
            nfse_data.data_emissao, nfse_data.data_processamento, nfse_data.ambiente_gerador,
            nfse_data.tipo_emissao, nfse_data.processo_emissao, nfse_data.codigo_status,
            nfse_data.valor_total_servicos, nfse_data.valor_total_deducoes, nfse_data.valor_base_calculo,
            nfse_data.valor_issqn, nfse_data.valor_credito, nfse_data.xml_file_path
        )
    
    async def _insert_nfse_service(self, conn: asyncpg.Connection, id_nfse: str, service_item: NFSEItem):
        """Insere serviço da NFS-e"""
        query = """
        INSERT INTO fact_servicos_nfse (
            id_nfse, codigo_servico, descricao_servico, quantidade, valor_unitario,
            valor_total, valor_deducoes, valor_base_calculo, aliquota_issqn, valor_issqn,
            valor_credito, codigo_cnae, codigo_tributacao_nacional, codigo_tributacao_municipal
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        )
        ON CONFLICT (id_nfse, codigo_servico) DO UPDATE SET
            valor_total = EXCLUDED.valor_total,
            valor_issqn = EXCLUDED.valor_issqn
        """
        
        issqn_tax = service_item.issqn_tax
        
        await conn.execute(
            query,
            id_nfse, service_item.servico.codigo_servico, service_item.servico.descricao,
            service_item.quantidade, service_item.valor_unitario, service_item.valor_total,
            service_item.valor_deducoes,
            issqn_tax.base_calculo if issqn_tax else None,
            issqn_tax.aliquota if issqn_tax else None,
            issqn_tax.valor if issqn_tax else None,
            issqn_tax.valor_credito if issqn_tax else None,
            service_item.servico.codigo_cnae, service_item.servico.codigo_tributacao_nacional,
            service_item.servico.codigo_tributacao_municipal
        )
    
    async def _verify_data_integrity(self, data: FiscalDocument):
        """
        Verifica integridade dos dados após armazenamento
        
        Args:
            data: Documento fiscal armazenado
        """
        try:
            if data.document_type == DocumentType.NFE:
                await self._verify_nfe_integrity(data)
            elif data.document_type == DocumentType.NFSE:
                await self._verify_nfse_integrity(data)
                
        except Exception as e:
            self.logger.error("Falha na verificação de integridade", 
                            document_type=data.document_type.value,
                            error=str(e))
            raise DataIntegrityError(f"Integridade comprometida: {str(e)}")
    
    async def _verify_nfe_integrity(self, nfe_data: NFEData):
        """Verifica integridade específica de NF-e"""
        async with get_db_connection() as conn:
            # Verifica se a NF-e foi armazenada
            nfe_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM nfe_main WHERE chave_nfe = $1)",
                nfe_data.chave_nfe
            )
            if not nfe_exists:
                raise DataIntegrityError("NF-e não encontrada após armazenamento")
            
            # Verifica se todos os itens foram armazenados
            items_count = await conn.fetchval(
                "SELECT COUNT(*) FROM fact_itens_nfe WHERE chave_nfe = $1",
                nfe_data.chave_nfe
            )
            if items_count != len(nfe_data.items):
                raise DataIntegrityError(f"Inconsistência no número de itens: esperado {len(nfe_data.items)}, encontrado {items_count}")
    
    async def _verify_nfse_integrity(self, nfse_data: NFSEData):
        """Verifica integridade específica de NFS-e"""
        async with get_db_connection() as conn:
            # Verifica se a NFS-e foi armazenada
            nfse_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM nfse_main WHERE id_nfse = $1)",
                nfse_data.id_nfse
            )
            if not nfse_exists:
                raise DataIntegrityError("NFS-e não encontrada após armazenamento")
            
            # Verifica se todos os serviços foram armazenados
            services_count = await conn.fetchval(
                "SELECT COUNT(*) FROM fact_servicos_nfse WHERE id_nfse = $1",
                nfse_data.id_nfse
            )
            if services_count != len(nfse_data.services):
                raise DataIntegrityError(f"Inconsistência no número de serviços: esperado {len(nfse_data.services)}, encontrado {services_count}")
    
    async def _periodic_integrity_check(self):
        """Executa verificações periódicas de integridade"""
        while self.is_active:
            try:
                await asyncio.sleep(self.integrity_check_interval)
                
                if not self.is_active:
                    break
                
                self.logger.info("Iniciando verificação periódica de integridade")
                
                # Verifica integridade referencial geral
                await self._check_referential_integrity()
                
                # Verifica consistência de valores
                await self._check_value_consistency()
                
                self.logger.info("Verificação periódica de integridade concluída")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Erro na verificação periódica de integridade", error=str(e))
    
    async def _check_referential_integrity(self):
        """Verifica integridade referencial entre tabelas"""
        async with get_db_connection() as conn:
            # Verifica produtos órfãos em itens NF-e
            orphaned_products = await conn.fetchval(
                """
                SELECT COUNT(*) FROM fact_itens_nfe i
                LEFT JOIN dim_produtos p ON i.codigo_produto = p.codigo_produto
                WHERE p.codigo_produto IS NULL
                """
            )
            
            if orphaned_products > 0:
                self.logger.warning("Produtos órfãos encontrados em itens NF-e", count=orphaned_products)
    
    async def _check_value_consistency(self):
        """Verifica consistência de valores calculados"""
        async with get_db_connection() as conn:
            # Verifica consistência de totais NF-e
            inconsistent_nfe = await conn.fetch(
                """
                SELECT n.chave_nfe, n.valor_total_produtos, SUM(i.valor_total_bruto) as soma_itens
                FROM nfe_main n
                JOIN fact_itens_nfe i ON n.chave_nfe = i.chave_nfe
                GROUP BY n.chave_nfe, n.valor_total_produtos
                HAVING ABS(n.valor_total_produtos - SUM(i.valor_total_bruto)) > 0.01
                """
            )
            
            if inconsistent_nfe:
                self.logger.warning("Inconsistências de valores encontradas em NF-e", count=len(inconsistent_nfe))
    
    async def preserve_historical_data(self, cutoff_date: datetime = None) -> Dict[str, Any]:
        """
        Preserva dados históricos movendo registros antigos para tabelas de arquivo
        
        Args:
            cutoff_date: Data limite para arquivamento (padrão: 7 anos atrás)
            
        Returns:
            Dict com estatísticas do arquivamento
        """
        if cutoff_date is None:
            cutoff_date = datetime.now() - timedelta(days=self.archival_retention_days)
        
        self.logger.info("Iniciando preservação de dados históricos", cutoff_date=cutoff_date.isoformat())
        
        archived_records = {
            "nfe_main": 0,
            "nfse_main": 0,
            "fact_itens_nfe": 0,
            "fact_servicos_nfse": 0
        }
        
        try:
            async with get_db_connection() as conn:
                async with conn.transaction():
                    # Cria tabelas de arquivo se não existirem
                    await self._create_archive_tables(conn)
                    
                    # Arquiva NF-e antigas
                    archived_records["nfe_main"] = await self._archive_old_nfe(conn, cutoff_date)
                    archived_records["fact_itens_nfe"] = await self._archive_old_nfe_items(conn, cutoff_date)
                    
                    # Arquiva NFS-e antigas
                    archived_records["nfse_main"] = await self._archive_old_nfse(conn, cutoff_date)
                    archived_records["fact_servicos_nfse"] = await self._archive_old_nfse_services(conn, cutoff_date)
            
            self.logger.info("Preservação de dados históricos concluída", archived_records=archived_records)
            
            return {
                "status": "success",
                "cutoff_date": cutoff_date.isoformat(),
                "archived_records": archived_records,
                "total_archived": sum(archived_records.values())
            }
            
        except Exception as e:
            self.logger.error("Erro na preservação de dados históricos", error=str(e))
            raise DataIntegrityError(f"Falha no arquivamento: {str(e)}")
    
    async def _create_archive_tables(self, conn: asyncpg.Connection):
        """Cria tabelas de arquivo se não existirem"""
        # Tabela de arquivo para NF-e
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_nfe_main (
                LIKE nfe_main INCLUDING ALL,
                archived_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de arquivo para itens NF-e
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_fact_itens_nfe (
                LIKE fact_itens_nfe INCLUDING ALL,
                archived_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de arquivo para NFS-e
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_nfse_main (
                LIKE nfse_main INCLUDING ALL,
                archived_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de arquivo para serviços NFS-e
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_fact_servicos_nfse (
                LIKE fact_servicos_nfse INCLUDING ALL,
                archived_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    
    async def _archive_old_nfe(self, conn: asyncpg.Connection, cutoff_date: datetime) -> int:
        """Arquiva NF-e antigas"""
        # Move registros para arquivo
        result = await conn.execute("""
            INSERT INTO archive_nfe_main 
            SELECT *, NOW() as archived_at FROM nfe_main 
            WHERE data_emissao < $1
        """, cutoff_date.date())
        
        # Remove registros da tabela principal
        await conn.execute("""
            DELETE FROM nfe_main WHERE data_emissao < $1
        """, cutoff_date.date())
        
        return int(result.split()[-1]) if result else 0
    
    async def _archive_old_nfe_items(self, conn: asyncpg.Connection, cutoff_date: datetime) -> int:
        """Arquiva itens de NF-e antigas"""
        # Move registros para arquivo
        result = await conn.execute("""
            INSERT INTO archive_fact_itens_nfe 
            SELECT i.*, NOW() as archived_at 
            FROM fact_itens_nfe i
            JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
            WHERE n.data_emissao < $1
        """, cutoff_date.date())
        
        return int(result.split()[-1]) if result else 0
    
    async def _archive_old_nfse(self, conn: asyncpg.Connection, cutoff_date: datetime) -> int:
        """Arquiva NFS-e antigas"""
        # Move registros para arquivo
        result = await conn.execute("""
            INSERT INTO archive_nfse_main 
            SELECT *, NOW() as archived_at FROM nfse_main 
            WHERE data_emissao < $1
        """, cutoff_date.date())
        
        return int(result.split()[-1]) if result else 0
    
    async def _archive_old_nfse_services(self, conn: asyncpg.Connection, cutoff_date: datetime) -> int:
        """Arquiva serviços de NFS-e antigas"""
        # Move registros para arquivo
        result = await conn.execute("""
            INSERT INTO archive_fact_servicos_nfse 
            SELECT s.*, NOW() as archived_at 
            FROM fact_servicos_nfse s
            JOIN nfse_main n ON s.id_nfse = n.id_nfse
            WHERE n.data_emissao < $1
        """, cutoff_date.date())
        
        return int(result.split()[-1]) if result else 0
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de armazenamento do Data Lake
        
        Returns:
            Dict com estatísticas detalhadas
        """
        try:
            async with get_db_connection() as conn:
                # Estatísticas de NF-e
                nfe_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_nfe,
                        SUM(valor_total_nf) as valor_total_nfe,
                        MIN(data_emissao) as primeira_nfe,
                        MAX(data_emissao) as ultima_nfe
                    FROM nfe_main
                """)
                
                # Estatísticas de NFS-e
                nfse_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_nfse,
                        SUM(valor_total_servicos) as valor_total_nfse,
                        MIN(data_emissao) as primeira_nfse,
                        MAX(data_emissao) as ultima_nfse
                    FROM nfse_main
                """)
                
                stats = {
                    "nfe": {
                        "total_documentos": nfe_stats['total_nfe'],
                        "valor_total": float(nfe_stats['valor_total_nfe'] or 0),
                        "primeira_data": nfe_stats['primeira_nfe'].isoformat() if nfe_stats['primeira_nfe'] else None,
                        "ultima_data": nfe_stats['ultima_nfe'].isoformat() if nfe_stats['ultima_nfe'] else None
                    },
                    "nfse": {
                        "total_documentos": nfse_stats['total_nfse'],
                        "valor_total": float(nfse_stats['valor_total_nfse'] or 0),
                        "primeira_data": nfse_stats['primeira_nfse'].isoformat() if nfse_stats['primeira_nfse'] else None,
                        "ultima_data": nfse_stats['ultima_nfse'].isoformat() if nfse_stats['ultima_nfse'] else None
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                return stats
                
        except Exception as e:
            self.logger.error("Erro ao obter estatísticas de armazenamento", error=str(e))
            raise DataIntegrityError(f"Falha ao obter estatísticas: {str(e)}")
    
    async def optimize_query(self, sql_query: str, parameters: List[Any] = None) -> Dict[str, Any]:
        """
        Otimiza consulta SQL para melhor performance
        
        Args:
            sql_query: Consulta SQL a ser otimizada
            parameters: Parâmetros da consulta
            
        Returns:
            Dict com consulta otimizada e estatísticas
        """
        try:
            self.logger.info("Iniciando otimização de consulta")
            
            # Aplica otimizações básicas
            optimized_query = self._apply_basic_optimizations(sql_query)
            
            return {
                "original_query": sql_query,
                "optimized_query": optimized_query,
                "optimization_applied": optimized_query != sql_query
            }
            
        except Exception as e:
            self.logger.error("Erro na otimização de consulta", error=str(e))
            return {
                "original_query": sql_query,
                "optimized_query": sql_query,
                "error": str(e)
            }
    
    def _apply_basic_optimizations(self, sql_query: str) -> str:
        """Aplica otimizações básicas na consulta"""
        optimized_query = sql_query.strip()
        
        # Remove comentários desnecessários
        lines = optimized_query.split('\n')
        optimized_lines = [line for line in lines if not line.strip().startswith('--')]
        optimized_query = '\n'.join(optimized_lines)
        
        # Adiciona LIMIT se não existir e a consulta for potencialmente custosa
        if "LIMIT" not in optimized_query.upper() and any(keyword in optimized_query.upper() for keyword in ["JOIN", "GROUP BY", "ORDER BY"]):
            optimized_query += " LIMIT 1000"
        
        # Otimizações específicas para consultas fiscais
        optimized_query = self._apply_fiscal_optimizations(optimized_query)
        
        return optimized_query
    
    def _apply_fiscal_optimizations(self, sql_query: str) -> str:
        """Aplica otimizações específicas para consultas fiscais"""
        query_upper = sql_query.upper()
        
        # Otimização para consultas de período fiscal
        if "DATA_EMISSAO" in query_upper and "BETWEEN" not in query_upper:
            # Sugere uso de índices de data
            if "WHERE" in query_upper:
                # Adiciona hint para usar índice de data
                sql_query = sql_query.replace("WHERE", "WHERE /*+ INDEX(data_emissao) */")
        
        # Otimização para consultas de fornecedores
        if "DIM_EMITENTE" in query_upper and "CNPJ" in query_upper:
            # Força uso do índice de CNPJ
            sql_query = sql_query.replace("dim_emitente", "dim_emitente /*+ INDEX(cnpj) */")
        
        # Otimização para consultas de produtos/serviços
        if any(table in query_upper for table in ["FACT_ITENS_NFE", "FACT_SERVICOS_NFSE"]):
            if "GROUP BY" in query_upper and "SUM" in query_upper:
                # Adiciona hint para agregações
                sql_query = sql_query.replace("GROUP BY", "/*+ USE_HASH_AGGREGATION */ GROUP BY")
        
        return sql_query
    
    async def execute_optimized_query(self, sql_query: str, parameters: List[Any] = None, 
                                    optimize: bool = True) -> Dict[str, Any]:
        """
        Executa consulta com otimizações aplicadas
        
        Args:
            sql_query: Consulta SQL
            parameters: Parâmetros da consulta
            optimize: Se deve aplicar otimizações
            
        Returns:
            Resultado da consulta com metadados
        """
        start_time = datetime.now()
        
        try:
            # Aplica otimizações se solicitado
            if optimize:
                optimization_result = await self.optimize_query(sql_query, parameters)
                final_query = optimization_result["optimized_query"]
            else:
                final_query = sql_query
                optimization_result = None
            
            # Executa consulta
            async with get_db_connection() as conn:
                if parameters:
                    result = await conn.fetch(final_query, *parameters)
                else:
                    result = await conn.fetch(final_query)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Converte resultado para formato serializável
            data = []
            for row in result:
                row_dict = {}
                for key, value in row.items():
                    if isinstance(value, Decimal):
                        row_dict[key] = float(value)
                    elif isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                data.append(row_dict)
            
            return {
                "status": "success",
                "data": data,
                "row_count": len(data),
                "execution_time": execution_time,
                "optimized": optimize,
                "optimization_result": optimization_result,
                "query_executed": final_query
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error("Erro na execução de consulta otimizada", 
                            query=sql_query[:100], error=str(e))
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": execution_time,
                "query_executed": sql_query
            }
    
    async def build_query_optimization_engine(self) -> Dict[str, Any]:
        """
        Constrói motor de otimização de consultas para análises complexas
        
        Returns:
            Dict com configurações do motor de otimização
        """
        try:
            self.logger.info("Construindo motor de otimização de consultas")
            
            # Configurações do motor de otimização
            optimization_config = {
                "max_execution_time": 30,  # segundos
                "max_rows_without_limit": 10000,
                "enable_query_cache": True,
                "cache_ttl": 300,  # 5 minutos
                "enable_parallel_execution": True,
                "max_parallel_queries": 5,
                "optimization_rules": [
                    "add_missing_indexes",
                    "rewrite_subqueries",
                    "optimize_joins",
                    "partition_pruning",
                    "predicate_pushdown"
                ]
            }
            
            # Cria índices otimizados se não existirem
            await self._create_optimization_indexes()
            
            # Cria views materializadas para consultas frequentes
            await self._create_materialized_views()
            
            self.logger.info("Motor de otimização de consultas construído com sucesso")
            
            return {
                "status": "success",
                "optimization_config": optimization_config,
                "indexes_created": True,
                "materialized_views_created": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Erro na construção do motor de otimização", error=str(e))
            raise DataIntegrityError(f"Falha na construção do motor de otimização: {str(e)}")
    
    async def _create_optimization_indexes(self):
        """Cria índices otimizados para consultas analíticas"""
        async with get_db_connection() as conn:
            # Índices compostos para análises temporais
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nfe_data_valor 
                ON nfe_main(data_emissao, valor_total_nf)
            """)
            
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_nfse_data_valor 
                ON nfse_main(data_emissao, valor_total_servicos)
            """)
            
            # Índices para análises por fornecedor
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_emitente_uf_categoria 
                ON dim_emitente(uf, regime_tributario)
            """)
            
            # Índices para análises de produtos/serviços
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_produtos_ncm_categoria 
                ON dim_produtos(ncm, categoria)
            """)
            
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_servicos_cnae_categoria 
                ON dim_servicos(codigo_cnae, categoria)
            """)
            
            # Índices para análises tributárias
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_itens_nfe_tributos 
                ON fact_itens_nfe(origem_produto, situacao_tributaria_icms, valor_icms)
            """)
            
            await conn.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_servicos_nfse_issqn 
                ON fact_servicos_nfse(aliquota_issqn, valor_issqn)
            """)
    
    async def _create_materialized_views(self):
        """Cria views materializadas para consultas analíticas frequentes"""
        async with get_db_connection() as conn:
            # View materializada para análise mensal de receitas
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_receitas_mensais AS
                SELECT 
                    DATE_TRUNC('month', data_emissao) as mes,
                    'NFE' as tipo_documento,
                    COUNT(*) as quantidade_documentos,
                    SUM(valor_total_nf) as valor_total,
                    SUM(valor_icms) as total_icms,
                    SUM(valor_ipi) as total_ipi,
                    SUM(valor_pis) as total_pis,
                    SUM(valor_cofins) as total_cofins,
                    AVG(valor_total_nf) as valor_medio
                FROM nfe_main
                WHERE data_emissao >= CURRENT_DATE - INTERVAL '24 months'
                GROUP BY DATE_TRUNC('month', data_emissao)
                
                UNION ALL
                
                SELECT 
                    DATE_TRUNC('month', data_emissao) as mes,
                    'NFSE' as tipo_documento,
                    COUNT(*) as quantidade_documentos,
                    SUM(valor_total_servicos) as valor_total,
                    0 as total_icms,
                    0 as total_ipi,
                    0 as total_pis,
                    0 as total_cofins,
                    AVG(valor_total_servicos) as valor_medio
                FROM nfse_main
                WHERE data_emissao >= CURRENT_DATE - INTERVAL '24 months'
                GROUP BY DATE_TRUNC('month', data_emissao)
            """)
            
            # View materializada para ranking de fornecedores
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ranking_fornecedores AS
                SELECT 
                    e.cnpj,
                    e.razao_social,
                    e.uf,
                    e.regime_tributario,
                    COUNT(DISTINCT n.chave_nfe) as total_nfe,
                    COUNT(DISTINCT ns.id_nfse) as total_nfse,
                    COALESCE(SUM(n.valor_total_nf), 0) as valor_total_produtos,
                    COALESCE(SUM(ns.valor_total_servicos), 0) as valor_total_servicos,
                    COALESCE(SUM(n.valor_total_nf), 0) + COALESCE(SUM(ns.valor_total_servicos), 0) as valor_total_geral,
                    MIN(COALESCE(n.data_emissao, ns.data_emissao)) as primeira_transacao,
                    MAX(COALESCE(n.data_emissao, ns.data_emissao)) as ultima_transacao
                FROM dim_emitente e
                LEFT JOIN nfe_main n ON e.cnpj = SUBSTRING(n.chave_nfe, 7, 14)
                LEFT JOIN nfse_main ns ON e.cnpj = SUBSTRING(ns.id_nfse, 9, 14)
                WHERE (n.data_emissao >= CURRENT_DATE - INTERVAL '12 months' 
                       OR ns.data_emissao >= CURRENT_DATE - INTERVAL '12 months')
                GROUP BY e.cnpj, e.razao_social, e.uf, e.regime_tributario
                HAVING COUNT(DISTINCT n.chave_nfe) > 0 OR COUNT(DISTINCT ns.id_nfse) > 0
                ORDER BY valor_total_geral DESC
            """)
            
            # View materializada para análise de produtos mais vendidos
            await conn.execute("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS mv_produtos_top AS
                SELECT 
                    p.codigo_produto,
                    p.descricao,
                    p.categoria,
                    p.ncm,
                    COUNT(i.id) as frequencia_compra,
                    SUM(i.quantidade_comercial) as quantidade_total,
                    SUM(i.valor_total_bruto) as valor_total,
                    AVG(i.valor_unitario_comercial) as preco_medio,
                    COUNT(DISTINCT SUBSTRING(i.chave_nfe, 7, 14)) as fornecedores_distintos
                FROM dim_produtos p
                JOIN fact_itens_nfe i ON p.codigo_produto = i.codigo_produto
                JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
                WHERE n.data_emissao >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY p.codigo_produto, p.descricao, p.categoria, p.ncm
                ORDER BY valor_total DESC
                LIMIT 1000
            """)
            
            # Cria índices nas views materializadas
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mv_receitas_mes_tipo 
                ON mv_receitas_mensais(mes, tipo_documento)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mv_fornecedores_valor 
                ON mv_ranking_fornecedores(valor_total_geral DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mv_produtos_categoria 
                ON mv_produtos_top(categoria, valor_total DESC)
            """)
    
    async def create_advanced_analytics_capabilities(self) -> Dict[str, Any]:
        """
        Cria capacidades avançadas de processamento analítico
        
        Returns:
            Dict com configurações das capacidades analíticas
        """
        try:
            self.logger.info("Criando capacidades avançadas de processamento analítico")
            
            # Configurações de análises avançadas
            analytics_config = {
                "trend_analysis": {
                    "enabled": True,
                    "lookback_months": 24,
                    "forecast_months": 6,
                    "confidence_interval": 0.95
                },
                "anomaly_detection": {
                    "enabled": True,
                    "sensitivity": 0.05,
                    "methods": ["statistical", "isolation_forest", "local_outlier_factor"]
                },
                "pattern_recognition": {
                    "enabled": True,
                    "seasonal_patterns": True,
                    "cyclical_patterns": True,
                    "correlation_analysis": True
                },
                "predictive_analytics": {
                    "enabled": True,
                    "models": ["linear_regression", "arima", "prophet"],
                    "update_frequency": "monthly"
                }
            }
            
            # Cria funções analíticas no banco
            await self._create_analytics_functions()
            
            # Cria tabelas para armazenar resultados analíticos
            await self._create_analytics_tables()
            
            self.logger.info("Capacidades avançadas de processamento analítico criadas com sucesso")
            
            return {
                "status": "success",
                "analytics_config": analytics_config,
                "functions_created": True,
                "tables_created": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Erro na criação de capacidades analíticas", error=str(e))
            raise DataIntegrityError(f"Falha na criação de capacidades analíticas: {str(e)}")
    
    async def _create_analytics_functions(self):
        """Cria funções SQL para análises avançadas"""
        async with get_db_connection() as conn:
            # Função para calcular tendências
            await conn.execute("""
                CREATE OR REPLACE FUNCTION calcular_tendencia_receita(
                    p_meses_historico INTEGER DEFAULT 12,
                    p_tipo_documento VARCHAR DEFAULT 'ALL'
                )
                RETURNS TABLE(
                    mes DATE,
                    valor_real NUMERIC,
                    tendencia NUMERIC,
                    crescimento_percentual NUMERIC
                )
                LANGUAGE SQL
                AS $$
                    WITH dados_mensais AS (
                        SELECT 
                            DATE_TRUNC('month', data_emissao)::DATE as mes,
                            SUM(CASE 
                                WHEN p_tipo_documento = 'NFE' OR p_tipo_documento = 'ALL' 
                                THEN valor_total_nf ELSE 0 
                            END) as valor_nfe,
                            SUM(CASE 
                                WHEN p_tipo_documento = 'NFSE' OR p_tipo_documento = 'ALL' 
                                THEN 0 ELSE 0 
                            END) as valor_nfse
                        FROM nfe_main
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '1 month' * p_meses_historico
                        GROUP BY DATE_TRUNC('month', data_emissao)
                        
                        UNION ALL
                        
                        SELECT 
                            DATE_TRUNC('month', data_emissao)::DATE as mes,
                            0 as valor_nfe,
                            SUM(CASE 
                                WHEN p_tipo_documento = 'NFSE' OR p_tipo_documento = 'ALL' 
                                THEN valor_total_servicos ELSE 0 
                            END) as valor_nfse
                        FROM nfse_main
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '1 month' * p_meses_historico
                        GROUP BY DATE_TRUNC('month', data_emissao)
                    ),
                    agregado AS (
                        SELECT 
                            mes,
                            SUM(valor_nfe + valor_nfse) as valor_total
                        FROM dados_mensais
                        GROUP BY mes
                        ORDER BY mes
                    ),
                    com_tendencia AS (
                        SELECT 
                            mes,
                            valor_total,
                            AVG(valor_total) OVER (
                                ORDER BY mes 
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                            ) as tendencia
                        FROM agregado
                    )
                    SELECT 
                        mes,
                        valor_total as valor_real,
                        tendencia,
                        CASE 
                            WHEN LAG(valor_total) OVER (ORDER BY mes) > 0 
                            THEN ((valor_total - LAG(valor_total) OVER (ORDER BY mes)) / 
                                  LAG(valor_total) OVER (ORDER BY mes)) * 100
                            ELSE 0
                        END as crescimento_percentual
                    FROM com_tendencia
                    ORDER BY mes;
                $$;
            """)
            
            # Função para detectar anomalias
            await conn.execute("""
                CREATE OR REPLACE FUNCTION detectar_anomalias_valor(
                    p_limite_desvios NUMERIC DEFAULT 2.0
                )
                RETURNS TABLE(
                    documento_id VARCHAR,
                    tipo_documento VARCHAR,
                    data_emissao DATE,
                    valor NUMERIC,
                    valor_medio NUMERIC,
                    desvio_padrao NUMERIC,
                    z_score NUMERIC,
                    is_anomalia BOOLEAN
                )
                LANGUAGE SQL
                AS $$
                    WITH estatisticas AS (
                        SELECT 
                            AVG(valor_total_nf) as media_nfe,
                            STDDEV(valor_total_nf) as desvio_nfe
                        FROM nfe_main
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '6 months'
                        
                        UNION ALL
                        
                        SELECT 
                            AVG(valor_total_servicos) as media_nfse,
                            STDDEV(valor_total_servicos) as desvio_nfse
                        FROM nfse_main
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '6 months'
                    ),
                    nfe_com_zscore AS (
                        SELECT 
                            chave_nfe as documento_id,
                            'NFE' as tipo_documento,
                            data_emissao,
                            valor_total_nf as valor,
                            e.media_nfe as valor_medio,
                            e.desvio_nfe as desvio_padrao,
                            (valor_total_nf - e.media_nfe) / NULLIF(e.desvio_nfe, 0) as z_score
                        FROM nfe_main n
                        CROSS JOIN (SELECT media_nfe, desvio_nfe FROM estatisticas LIMIT 1) e
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '1 month'
                    ),
                    nfse_com_zscore AS (
                        SELECT 
                            id_nfse as documento_id,
                            'NFSE' as tipo_documento,
                            data_emissao,
                            valor_total_servicos as valor,
                            e.media_nfse as valor_medio,
                            e.desvio_nfse as desvio_padrao,
                            (valor_total_servicos - e.media_nfse) / NULLIF(e.desvio_nfse, 0) as z_score
                        FROM nfse_main n
                        CROSS JOIN (SELECT media_nfe as media_nfse, desvio_nfe as desvio_nfse FROM estatisticas OFFSET 1 LIMIT 1) e
                        WHERE data_emissao >= CURRENT_DATE - INTERVAL '1 month'
                    )
                    SELECT 
                        documento_id,
                        tipo_documento,
                        data_emissao,
                        valor,
                        valor_medio,
                        desvio_padrao,
                        z_score,
                        ABS(z_score) > p_limite_desvios as is_anomalia
                    FROM (
                        SELECT * FROM nfe_com_zscore
                        UNION ALL
                        SELECT * FROM nfse_com_zscore
                    ) todos
                    WHERE ABS(z_score) > p_limite_desvios
                    ORDER BY ABS(z_score) DESC;
                $$;
            """)
    
    async def _create_analytics_tables(self):
        """Cria tabelas para armazenar resultados analíticos"""
        async with get_db_connection() as conn:
            # Tabela para armazenar tendências calculadas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_tendencias (
                    id BIGSERIAL PRIMARY KEY,
                    periodo DATE NOT NULL,
                    tipo_analise VARCHAR(50) NOT NULL,
                    tipo_documento VARCHAR(10),
                    valor_real NUMERIC(15,2),
                    valor_tendencia NUMERIC(15,2),
                    crescimento_percentual NUMERIC(8,4),
                    confianca NUMERIC(5,4),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(periodo, tipo_analise, tipo_documento)
                )
            """)
            
            # Tabela para armazenar anomalias detectadas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_anomalias (
                    id BIGSERIAL PRIMARY KEY,
                    documento_id VARCHAR(100) NOT NULL,
                    tipo_documento VARCHAR(10) NOT NULL,
                    data_documento DATE NOT NULL,
                    valor_documento NUMERIC(15,2),
                    valor_esperado NUMERIC(15,2),
                    desvio_score NUMERIC(8,4),
                    severidade VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'PENDENTE',
                    observacoes TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Tabela para armazenar padrões identificados
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analytics_padroes (
                    id BIGSERIAL PRIMARY KEY,
                    tipo_padrao VARCHAR(50) NOT NULL,
                    descricao TEXT,
                    parametros JSONB,
                    confianca NUMERIC(5,4),
                    periodo_inicio DATE,
                    periodo_fim DATE,
                    status VARCHAR(20) DEFAULT 'ATIVO',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Índices para performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tendencias_periodo_tipo 
                ON analytics_tendencias(periodo, tipo_analise)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_anomalias_documento_data 
                ON analytics_anomalias(documento_id, data_documento)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_padroes_tipo_status 
                ON analytics_padroes(tipo_padrao, status)
            """)
    
    async def implement_data_lifecycle_policies(self) -> Dict[str, Any]:
        """
        Implementa políticas de ciclo de vida e arquivamento de dados
        
        Returns:
            Dict com configurações das políticas implementadas
        """
        try:
            self.logger.info("Implementando políticas de ciclo de vida de dados")
            
            # Configurações de políticas de ciclo de vida
            lifecycle_policies = {
                "retention_periods": {
                    "active_data": "24_months",  # Dados ativos por 24 meses
                    "archived_data": "7_years",  # Dados arquivados por 7 anos (requisito fiscal)
                    "analytics_results": "12_months",  # Resultados analíticos por 12 meses
                    "logs": "6_months"  # Logs por 6 meses
                },
                "archival_rules": {
                    "auto_archive_enabled": True,
                    "archive_frequency": "monthly",
                    "compression_enabled": True,
                    "encryption_enabled": True
                },
                "cleanup_rules": {
                    "auto_cleanup_enabled": True,
                    "cleanup_frequency": "weekly",
                    "temp_data_retention": "7_days",
                    "failed_jobs_retention": "30_days"
                },
                "backup_policies": {
                    "daily_backup": True,
                    "weekly_full_backup": True,
                    "monthly_archive_backup": True,
                    "retention_period": "3_years"
                }
            }
            
            # Cria tabelas de controle de ciclo de vida
            await self._create_lifecycle_control_tables()
            
            # Cria jobs de manutenção automática
            await self._create_maintenance_jobs()
            
            # Configura políticas de particionamento
            await self._setup_table_partitioning()
            
            self.logger.info("Políticas de ciclo de vida de dados implementadas com sucesso")
            
            return {
                "status": "success",
                "lifecycle_policies": lifecycle_policies,
                "control_tables_created": True,
                "maintenance_jobs_created": True,
                "partitioning_configured": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Erro na implementação de políticas de ciclo de vida", error=str(e))
            raise DataIntegrityError(f"Falha na implementação de políticas: {str(e)}")
    
    async def _create_lifecycle_control_tables(self):
        """Cria tabelas de controle para ciclo de vida dos dados"""
        async with get_db_connection() as conn:
            # Tabela de controle de arquivamento
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_lifecycle_control (
                    id BIGSERIAL PRIMARY KEY,
                    table_name VARCHAR(100) NOT NULL,
                    partition_name VARCHAR(100),
                    data_type VARCHAR(50) NOT NULL,
                    creation_date DATE NOT NULL,
                    last_access_date DATE,
                    archive_date DATE,
                    deletion_date DATE,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    size_mb NUMERIC(12,2),
                    record_count BIGINT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Tabela de log de operações de ciclo de vida
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS data_lifecycle_log (
                    id BIGSERIAL PRIMARY KEY,
                    operation_type VARCHAR(50) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    records_affected BIGINT,
                    operation_start TIMESTAMPTZ NOT NULL,
                    operation_end TIMESTAMPTZ,
                    status VARCHAR(20) NOT NULL,
                    error_message TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Índices para controle de ciclo de vida
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lifecycle_table_status 
                ON data_lifecycle_control(table_name, status)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_lifecycle_log_operation_date 
                ON data_lifecycle_log(operation_type, operation_start)
            """)
    
    async def _create_maintenance_jobs(self):
        """Cria jobs de manutenção automática"""
        async with get_db_connection() as conn:
            # Função para arquivamento automático
            await conn.execute("""
                CREATE OR REPLACE FUNCTION executar_arquivamento_automatico()
                RETURNS INTEGER
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    registros_arquivados INTEGER := 0;
                    cutoff_date DATE := CURRENT_DATE - INTERVAL '24 months';
                BEGIN
                    -- Log início da operação
                    INSERT INTO data_lifecycle_log (operation_type, table_name, operation_start, status)
                    VALUES ('AUTO_ARCHIVE', 'ALL_TABLES', NOW(), 'RUNNING');
                    
                    -- Arquiva NF-e antigas
                    INSERT INTO archive_nfe_main 
                    SELECT *, NOW() as archived_at 
                    FROM nfe_main 
                    WHERE data_emissao < cutoff_date;
                    
                    GET DIAGNOSTICS registros_arquivados = ROW_COUNT;
                    
                    -- Remove registros arquivados da tabela principal
                    DELETE FROM nfe_main WHERE data_emissao < cutoff_date;
                    
                    -- Atualiza controle de ciclo de vida
                    UPDATE data_lifecycle_control 
                    SET status = 'ARCHIVED', archive_date = CURRENT_DATE
                    WHERE table_name = 'nfe_main' AND creation_date < cutoff_date;
                    
                    -- Log fim da operação
                    UPDATE data_lifecycle_log 
                    SET operation_end = NOW(), status = 'COMPLETED', records_affected = registros_arquivados
                    WHERE operation_type = 'AUTO_ARCHIVE' AND operation_end IS NULL;
                    
                    RETURN registros_arquivados;
                EXCEPTION
                    WHEN OTHERS THEN
                        -- Log erro
                        UPDATE data_lifecycle_log 
                        SET operation_end = NOW(), status = 'FAILED', error_message = SQLERRM
                        WHERE operation_type = 'AUTO_ARCHIVE' AND operation_end IS NULL;
                        
                        RAISE;
                END;
                $$;
            """)
            
            # Função para limpeza de dados temporários
            await conn.execute("""
                CREATE OR REPLACE FUNCTION limpar_dados_temporarios()
                RETURNS INTEGER
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    registros_removidos INTEGER := 0;
                BEGIN
                    -- Remove resultados analíticos antigos
                    DELETE FROM analytics_tendencias 
                    WHERE created_at < CURRENT_DATE - INTERVAL '12 months';
                    
                    GET DIAGNOSTICS registros_removidos = ROW_COUNT;
                    
                    -- Remove logs antigos
                    DELETE FROM data_lifecycle_log 
                    WHERE created_at < CURRENT_DATE - INTERVAL '6 months';
                    
                    -- Atualiza estatísticas das tabelas
                    ANALYZE analytics_tendencias;
                    ANALYZE analytics_anomalias;
                    ANALYZE analytics_padroes;
                    
                    RETURN registros_removidos;
                END;
                $$;
            """)
    
    async def _setup_table_partitioning(self):
        """Configura particionamento de tabelas para melhor performance"""
        async with get_db_connection() as conn:
            # Cria tabela particionada para NF-e por mês (para dados futuros)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nfe_main_partitioned (
                    LIKE nfe_main INCLUDING ALL
                ) PARTITION BY RANGE (data_emissao)
            """)
            
            # Cria partições para os próximos 12 meses
            for i in range(12):
                start_date = datetime.now().replace(day=1) + timedelta(days=32*i)
                end_date = start_date + timedelta(days=32)
                start_date = start_date.replace(day=1)
                end_date = end_date.replace(day=1)
                
                partition_name = f"nfe_main_y{start_date.year}m{start_date.month:02d}"
                
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {partition_name}
                    PARTITION OF nfe_main_partitioned
                    FOR VALUES FROM ('{start_date.date()}') TO ('{end_date.date()}')
                """)
    
    async def refresh_materialized_views(self) -> Dict[str, Any]:
        """
        Atualiza views materializadas para análises
        
        Returns:
            Dict com resultado da atualização
        """
        try:
            self.logger.info("Atualizando views materializadas")
            
            start_time = datetime.now()
            views_updated = []
            
            async with get_db_connection() as conn:
                # Lista de views materializadas para atualizar
                materialized_views = [
                    "mv_receitas_mensais",
                    "mv_ranking_fornecedores", 
                    "mv_produtos_top"
                ]
                
                for view_name in materialized_views:
                    try:
                        await conn.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
                        views_updated.append(view_name)
                        self.logger.info(f"View materializada atualizada: {view_name}")
                    except Exception as e:
                        self.logger.error(f"Erro ao atualizar view {view_name}", error=str(e))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "success",
                "views_updated": views_updated,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Erro na atualização de views materializadas", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def implement_optimized_query_access_system(self) -> Dict[str, Any]:
        """
        Implementa sistema completo de acesso otimizado a consultas
        Combina motor de otimização, capacidades analíticas e políticas de ciclo de vida
        
        Returns:
            Dict com resultado da implementação completa
        """
        try:
            self.logger.info("Implementando sistema completo de acesso otimizado a consultas")
            
            results = {
                "query_optimization_engine": None,
                "advanced_analytics": None,
                "data_lifecycle_policies": None,
                "materialized_views_refresh": None
            }
            
            # 1. Constrói motor de otimização de consultas
            self.logger.info("Construindo motor de otimização de consultas...")
            results["query_optimization_engine"] = await self.build_query_optimization_engine()
            
            # 2. Cria capacidades avançadas de processamento analítico
            self.logger.info("Criando capacidades avançadas de processamento analítico...")
            results["advanced_analytics"] = await self.create_advanced_analytics_capabilities()
            
            # 3. Implementa políticas de ciclo de vida e arquivamento
            self.logger.info("Implementando políticas de ciclo de vida de dados...")
            results["data_lifecycle_policies"] = await self.implement_data_lifecycle_policies()
            
            # 4. Atualiza views materializadas
            self.logger.info("Atualizando views materializadas...")
            results["materialized_views_refresh"] = await self.refresh_materialized_views()
            
            # Verifica se todas as implementações foram bem-sucedidas
            all_successful = all(
                result.get("status") == "success" 
                for result in results.values() 
                if isinstance(result, dict)
            )
            
            if all_successful:
                self.logger.info("Sistema de acesso otimizado implementado com sucesso")
                
                return {
                    "status": "success",
                    "message": "Sistema de acesso otimizado a consultas implementado com sucesso",
                    "components": results,
                    "capabilities": [
                        "Motor de otimização de consultas para análises complexas",
                        "Capacidades avançadas de processamento analítico",
                        "Políticas de ciclo de vida e arquivamento de dados",
                        "Views materializadas para consultas frequentes",
                        "Índices otimizados para performance",
                        "Funções analíticas avançadas",
                        "Detecção de anomalias automatizada",
                        "Análise de tendências e padrões",
                        "Particionamento de tabelas",
                        "Jobs de manutenção automática"
                    ],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                failed_components = [
                    name for name, result in results.items() 
                    if isinstance(result, dict) and result.get("status") != "success"
                ]
                
                self.logger.error("Falha na implementação de alguns componentes", 
                                failed_components=failed_components)
                
                return {
                    "status": "partial_success",
                    "message": "Sistema implementado com algumas falhas",
                    "components": results,
                    "failed_components": failed_components,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error("Erro na implementação do sistema de acesso otimizado", error=str(e))
            raise DataIntegrityError(f"Falha na implementação do sistema: {str(e)}")
    
    async def get_system_performance_metrics(self) -> Dict[str, Any]:
        """
        Obtém métricas de performance do sistema otimizado
        
        Returns:
            Dict com métricas de performance
        """
        try:
            async with get_db_connection() as conn:
                # Métricas de consultas
                query_metrics = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_queries_today,
                        AVG(EXTRACT(EPOCH FROM (NOW() - query_start))) as avg_query_time,
                        MAX(EXTRACT(EPOCH FROM (NOW() - query_start))) as max_query_time
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND query_start >= CURRENT_DATE
                """)
                
                # Métricas de armazenamento
                storage_metrics = await conn.fetchrow("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as database_size,
                        (SELECT COUNT(*) FROM nfe_main) as total_nfe,
                        (SELECT COUNT(*) FROM nfse_main) as total_nfse,
                        (SELECT COUNT(*) FROM archive_nfe_main) as archived_nfe,
                        (SELECT COUNT(*) FROM archive_nfse_main) as archived_nfse
                """)
                
                # Métricas de índices
                index_metrics = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """)
                
                return {
                    "status": "success",
                    "query_performance": {
                        "total_queries_today": query_metrics["total_queries_today"],
                        "avg_query_time_seconds": float(query_metrics["avg_query_time"] or 0),
                        "max_query_time_seconds": float(query_metrics["max_query_time"] or 0)
                    },
                    "storage_metrics": {
                        "database_size": storage_metrics["database_size"],
                        "total_nfe": storage_metrics["total_nfe"],
                        "total_nfse": storage_metrics["total_nfse"],
                        "archived_nfe": storage_metrics["archived_nfe"],
                        "archived_nfse": storage_metrics["archived_nfse"]
                    },
                    "top_indexes": [
                        {
                            "table": row["tablename"],
                            "index": row["indexname"],
                            "scans": row["idx_scan"],
                            "tuples_read": row["idx_tup_read"]
                        }
                        for row in index_metrics
                    ],
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error("Erro ao obter métricas de performance", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }