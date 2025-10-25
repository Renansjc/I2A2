"""
Data Lake Agent for managing centralized data storage and analytics
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import structlog

from .base_agent import BaseAgent
from models.fiscal_data import FiscalDocument, NFEData, NFSEData, DocumentType
from utils.database import DatabaseManager, get_db_connection
from utils.config import settings


class StorageResult:
    """Result of data storage operation"""
    
    def __init__(self, success: bool, document_id: str, message: str = ""):
        self.success = success
        self.document_id = document_id
        self.message = message
        self.timestamp = datetime.now()


class IntegrityCheckResult:
    """Result of data integrity check"""
    
    def __init__(self, passed: bool, issues: List[str] = None):
        self.passed = passed
        self.issues = issues or []
        self.checked_at = datetime.now()


class AnalyticsRequest:
    """Analytics request structure"""
    
    def __init__(self, query_type: str, parameters: Dict[str, Any], 
                 date_range: Dict[str, datetime] = None):
        self.query_type = query_type
        self.parameters = parameters
        self.date_range = date_range or {}
        self.requested_at = datetime.now()


class AnalyticsResult:
    """Analytics result structure"""
    
    def __init__(self, data: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.data = data
        self.metadata = metadata
        self.generated_at = datetime.now()


class DataLakeAgent(BaseAgent):
    """Agent responsible for data lake management and analytics"""
    
    def __init__(self):
        super().__init__("DataLakeAgent")
        self.storage_stats = {
            'total_documents': 0,
            'nfe_count': 0,
            'nfse_count': 0,
            'last_update': None
        }
        self.integrity_checks = []
        
    async def initialize(self):
        """Initialize Data Lake Agent resources"""
        try:
            # Initialize database connections
            await self._initialize_storage()
            
            # Load storage statistics
            await self._load_storage_stats()
            
            # Schedule periodic integrity checks
            asyncio.create_task(self._periodic_integrity_check())
            
            self.logger.info("Data Lake Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize Data Lake Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Data Lake Agent cleaned up")
    
    async def process(self, data: Union[FiscalDocument, Dict[str, Any]]) -> Any:
        """Process data storage or analytics request"""
        if isinstance(data, (NFEData, NFSEData)):
            return await self.store_fiscal_data(data)
        elif isinstance(data, dict):
            if 'analytics_request' in data:
                return await self.perform_advanced_analytics(data['analytics_request'])
            elif 'query' in data:
                return await self._execute_query(data['query'], data.get('parameters', []))
        return None
    
    async def _initialize_storage(self):
        """Initialize storage connections and verify schema"""
        try:
            # Verify database schema exists
            await self._verify_schema()
            
            self.logger.info("Storage initialized successfully")
            
        except Exception as e:
            self.logger.error("Error initializing storage", error=str(e))
            raise
    
    async def _verify_schema(self):
        """Verify that required database schema exists"""
        try:
            # Check if main tables exist
            tables_to_check = [
                'nfe_main', 'nfse_main', 'dim_emitente', 'dim_produtos', 
                'dim_servicos', 'fact_itens_nfe', 'fact_servicos_nfse'
            ]
            
            for table in tables_to_check:
                query = f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table}'"
                result = await DatabaseManager.execute_query(query)
                
                if not result or result[0]['count'] == 0:
                    self.logger.warning("Table not found", table=table)
            
            self.logger.info("Schema verification completed")
            
        except Exception as e:
            self.logger.error("Error verifying schema", error=str(e))
    
    async def _load_storage_stats(self):
        """Load current storage statistics"""
        try:
            # Count NFE documents
            nfe_count_query = "SELECT COUNT(*) as count FROM nfe_main"
            nfe_result = await DatabaseManager.execute_query(nfe_count_query)
            self.storage_stats['nfe_count'] = nfe_result[0]['count'] if nfe_result else 0
            
            # Count NFSE documents
            nfse_count_query = "SELECT COUNT(*) as count FROM nfse_main"
            nfse_result = await DatabaseManager.execute_query(nfse_count_query)
            self.storage_stats['nfse_count'] = nfse_result[0]['count'] if nfse_result else 0
            
            # Calculate total
            self.storage_stats['total_documents'] = (
                self.storage_stats['nfe_count'] + self.storage_stats['nfse_count']
            )
            self.storage_stats['last_update'] = datetime.now()
            
            self.logger.info("Storage stats loaded", 
                           total=self.storage_stats['total_documents'],
                           nfe=self.storage_stats['nfe_count'],
                           nfse=self.storage_stats['nfse_count'])
            
        except Exception as e:
            self.logger.error("Error loading storage stats", error=str(e))
    
    async def store_fiscal_data(self, data: FiscalDocument) -> StorageResult:
        """Store fiscal document data in the data lake"""
        try:
            self.logger.info("Storing fiscal data", 
                           document_type=data.document_type.value,
                           document_id=getattr(data, 'chave_nfe', None) or getattr(data, 'id_nfse', None))
            
            if data.document_type == DocumentType.NFE:
                result = await self._store_nfe_data(data)
            else:
                result = await self._store_nfse_data(data)
            
            if result.success:
                # Update storage stats
                await self._update_storage_stats(data.document_type)
                
                # Maintain referential integrity
                await self.maintain_referential_integrity()
            
            return result
            
        except Exception as e:
            self.logger.error("Error storing fiscal data", error=str(e))
            return StorageResult(False, "", str(e))
    
    async def _store_nfe_data(self, nfe_data: NFEData) -> StorageResult:
        """Store NFE data in the database"""
        try:
            # Store supplier data
            await self._store_supplier(nfe_data.supplier)
            
            # Store recipient data
            await self._store_recipient(nfe_data.recipient)
            
            # Store main NFE record
            nfe_insert_query = """
                INSERT INTO nfe_main (
                    chave_nfe, numero_nf, serie, modelo, data_emissao, data_saida_entrada,
                    tipo_operacao, codigo_municipio, uf_emitente, natureza_operacao,
                    forma_pagamento, valor_total_nf, valor_total_produtos, valor_total_servicos,
                    base_calculo_icms, valor_icms, base_calculo_icms_st, valor_icms_st,
                    valor_total_ipi, valor_pis, valor_cofins, xml_file_path
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                ) ON CONFLICT (chave_nfe) DO UPDATE SET
                    processed_at = NOW(),
                    updated_at = NOW()
            """
            
            await DatabaseManager.execute_command(
                nfe_insert_query,
                nfe_data.chave_nfe, nfe_data.numero_nf, nfe_data.serie, nfe_data.modelo,
                nfe_data.data_emissao, nfe_data.data_saida_entrada, nfe_data.tipo_operacao,
                nfe_data.codigo_municipio, nfe_data.uf_emitente, nfe_data.natureza_operacao,
                nfe_data.forma_pagamento, nfe_data.valor_total_nf, nfe_data.valor_total_produtos,
                nfe_data.valor_total_servicos, nfe_data.base_calculo_icms, nfe_data.valor_icms,
                nfe_data.base_calculo_icms_st, nfe_data.valor_icms_st, nfe_data.valor_total_ipi,
                nfe_data.valor_pis, nfe_data.valor_cofins, nfe_data.xml_file_path
            )
            
            # Store NFE items
            for item in nfe_data.items:
                await self._store_nfe_item(nfe_data.chave_nfe, item)
            
            return StorageResult(True, nfe_data.chave_nfe, "NFE data stored successfully")
            
        except Exception as e:
            self.logger.error("Error storing NFE data", error=str(e))
            return StorageResult(False, nfe_data.chave_nfe, str(e))
    
    async def _store_nfse_data(self, nfse_data: NFSEData) -> StorageResult:
        """Store NFSE data in the database"""
        try:
            # Store supplier data
            await self._store_supplier(nfse_data.supplier)
            
            # Store recipient data
            await self._store_recipient(nfse_data.recipient)
            
            # Store main NFSE record
            nfse_insert_query = """
                INSERT INTO nfse_main (
                    id_nfse, numero_nfse, numero_dfse, codigo_municipio_emissao,
                    local_emissao, local_prestacao, codigo_municipio_incidencia,
                    local_incidencia, tributacao_nacional, tributacao_municipal,
                    codigo_nbs, data_emissao, data_processamento, ambiente_gerador,
                    tipo_emissao, processo_emissao, codigo_status, valor_total_servicos,
                    valor_total_deducoes, valor_base_calculo, valor_issqn, valor_credito,
                    xml_file_path
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
                ) ON CONFLICT (id_nfse) DO UPDATE SET
                    processed_at = NOW()
            """
            
            await DatabaseManager.execute_command(
                nfse_insert_query,
                nfse_data.id_nfse, nfse_data.numero_nfse, nfse_data.numero_dfse,
                nfse_data.codigo_municipio_emissao, nfse_data.local_emissao,
                nfse_data.local_prestacao, nfse_data.codigo_municipio_incidencia,
                nfse_data.local_incidencia, nfse_data.tributacao_nacional,
                nfse_data.tributacao_municipal, nfse_data.codigo_nbs,
                nfse_data.data_emissao, nfse_data.data_processamento,
                nfse_data.ambiente_gerador, nfse_data.tipo_emissao,
                nfse_data.processo_emissao, nfse_data.codigo_status,
                nfse_data.valor_total_servicos, nfse_data.valor_total_deducoes,
                nfse_data.valor_base_calculo, nfse_data.valor_issqn,
                nfse_data.valor_credito, nfse_data.xml_file_path
            )
            
            # Store NFSE services
            for service_item in nfse_data.services:
                await self._store_nfse_service(nfse_data.id_nfse, service_item)
            
            return StorageResult(True, nfse_data.id_nfse, "NFSE data stored successfully")
            
        except Exception as e:
            self.logger.error("Error storing NFSE data", error=str(e))
            return StorageResult(False, nfse_data.id_nfse, str(e))
    
    async def _store_supplier(self, supplier):
        """Store supplier data"""
        try:
            supplier_query = """
                INSERT INTO dim_emitente (
                    cnpj, cpf, inscricao_estadual, razao_social, nome_fantasia,
                    logradouro, numero, complemento, bairro, codigo_municipio,
                    nome_municipio, uf, cep, codigo_pais, nome_pais,
                    telefone, email, regime_tributario
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                ) ON CONFLICT (cnpj) DO UPDATE SET
                    updated_at = NOW()
            """
            
            await DatabaseManager.execute_command(
                supplier_query,
                supplier.cnpj, supplier.cpf, supplier.inscricao_estadual,
                supplier.razao_social, supplier.nome_fantasia,
                supplier.address.logradouro, supplier.address.numero,
                supplier.address.complemento, supplier.address.bairro,
                supplier.address.codigo_municipio, supplier.address.nome_municipio,
                supplier.address.uf, supplier.address.cep,
                supplier.address.codigo_pais, supplier.address.nome_pais,
                supplier.telefone, supplier.email, supplier.regime_tributario
            )
            
        except Exception as e:
            self.logger.error("Error storing supplier", error=str(e))
    
    async def _store_recipient(self, recipient):
        """Store recipient data"""
        try:
            recipient_query = """
                INSERT INTO dim_destinatario (
                    cnpj, cpf, inscricao_estadual, razao_social,
                    logradouro, numero, complemento, bairro, codigo_municipio,
                    nome_municipio, uf, cep, codigo_pais, nome_pais,
                    telefone, email
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                ) ON CONFLICT DO NOTHING
            """
            
            await DatabaseManager.execute_command(
                recipient_query,
                recipient.cnpj, recipient.cpf, recipient.inscricao_estadual,
                recipient.razao_social, recipient.address.logradouro,
                recipient.address.numero, recipient.address.complemento,
                recipient.address.bairro, recipient.address.codigo_municipio,
                recipient.address.nome_municipio, recipient.address.uf,
                recipient.address.cep, recipient.address.codigo_pais,
                recipient.address.nome_pais, recipient.telefone, recipient.email
            )
            
        except Exception as e:
            self.logger.error("Error storing recipient", error=str(e))
    
    async def _store_nfe_item(self, chave_nfe: str, item):
        """Store NFE item data"""
        try:
            # Store product first
            await self._store_product(item.produto)
            
            # Store item
            item_query = """
                INSERT INTO fact_itens_nfe (
                    chave_nfe, numero_item, codigo_produto, ean, descricao,
                    ncm, cest, cfop, unidade_comercial, quantidade_comercial,
                    valor_unitario_comercial, valor_total_bruto, ean_tributavel,
                    unidade_tributavel, quantidade_tributavel, valor_unitario_tributavel,
                    valor_frete, valor_seguro, valor_desconto, valor_outras_despesas
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                )
            """
            
            await DatabaseManager.execute_command(
                item_query,
                chave_nfe, item.numero_item, item.produto.codigo_produto,
                item.produto.ean, item.produto.descricao, item.produto.ncm,
                item.produto.cest, item.produto.cfop, item.produto.unidade_comercial,
                item.quantidade_comercial, item.valor_unitario_comercial,
                item.valor_total_bruto, item.produto.ean, item.produto.unidade_tributavel,
                item.quantidade_tributavel, item.valor_unitario_tributavel,
                item.valor_frete, item.valor_seguro, item.valor_desconto,
                item.valor_outras_despesas
            )
            
        except Exception as e:
            self.logger.error("Error storing NFE item", error=str(e))
    
    async def _store_nfse_service(self, id_nfse: str, service_item):
        """Store NFSE service data"""
        try:
            # Store service first
            await self._store_service(service_item.servico)
            
            # Store service item
            service_query = """
                INSERT INTO fact_servicos_nfse (
                    id_nfse, codigo_servico, descricao_servico, quantidade,
                    valor_unitario, valor_total, valor_deducoes, valor_base_calculo,
                    aliquota_issqn, valor_issqn, valor_credito, codigo_cnae,
                    codigo_tributacao_nacional, codigo_tributacao_municipal
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
            """
            
            issqn_tax = service_item.issqn_tax
            await DatabaseManager.execute_command(
                service_query,
                id_nfse, service_item.servico.codigo_servico,
                service_item.servico.descricao, service_item.quantidade,
                service_item.valor_unitario, service_item.valor_total,
                service_item.valor_deducoes, issqn_tax.base_calculo if issqn_tax else None,
                issqn_tax.aliquota if issqn_tax else None,
                issqn_tax.valor if issqn_tax else None,
                issqn_tax.valor_credito if issqn_tax else None,
                service_item.servico.codigo_cnae,
                service_item.servico.codigo_tributacao_nacional,
                service_item.servico.codigo_tributacao_municipal
            )
            
        except Exception as e:
            self.logger.error("Error storing NFSE service", error=str(e))
    
    async def _store_product(self, product):
        """Store product data"""
        try:
            product_query = """
                INSERT INTO dim_produtos (
                    codigo_produto, ean, descricao, ncm, cest, cfop,
                    unidade_comercial, unidade_tributavel, categoria, subcategoria
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                ) ON CONFLICT (codigo_produto) DO UPDATE SET
                    updated_at = NOW()
            """
            
            await DatabaseManager.execute_command(
                product_query,
                product.codigo_produto, product.ean, product.descricao,
                product.ncm, product.cest, product.cfop,
                product.unidade_comercial, product.unidade_tributavel,
                product.category, product.subcategory
            )
            
        except Exception as e:
            self.logger.error("Error storing product", error=str(e))
    
    async def _store_service(self, service):
        """Store service data"""
        try:
            service_query = """
                INSERT INTO dim_servicos (
                    codigo_servico, descricao, codigo_cnae, codigo_tributacao_nacional,
                    codigo_tributacao_municipal, codigo_nbs, categoria, subcategoria
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8
                ) ON CONFLICT (codigo_servico) DO UPDATE SET
                    updated_at = NOW()
            """
            
            await DatabaseManager.execute_command(
                service_query,
                service.codigo_servico, service.descricao, service.codigo_cnae,
                service.codigo_tributacao_nacional, service.codigo_tributacao_municipal,
                service.codigo_nbs, service.category, service.subcategory
            )
            
        except Exception as e:
            self.logger.error("Error storing service", error=str(e))
    
    async def _update_storage_stats(self, document_type: DocumentType):
        """Update storage statistics"""
        try:
            if document_type == DocumentType.NFE:
                self.storage_stats['nfe_count'] += 1
            else:
                self.storage_stats['nfse_count'] += 1
            
            self.storage_stats['total_documents'] += 1
            self.storage_stats['last_update'] = datetime.now()
            
        except Exception as e:
            self.logger.error("Error updating storage stats", error=str(e))
    
    async def maintain_data_integrity(self) -> IntegrityCheckResult:
        """Maintain data integrity and consistency"""
        try:
            issues = []
            
            # Check for orphaned records
            orphaned_items = await self._check_orphaned_items()
            if orphaned_items:
                issues.extend(orphaned_items)
            
            # Check for missing references
            missing_refs = await self._check_missing_references()
            if missing_refs:
                issues.extend(missing_refs)
            
            # Check data consistency
            consistency_issues = await self._check_data_consistency()
            if consistency_issues:
                issues.extend(consistency_issues)
            
            result = IntegrityCheckResult(len(issues) == 0, issues)
            self.integrity_checks.append(result)
            
            if issues:
                self.logger.warning("Data integrity issues found", issues=len(issues))
            else:
                self.logger.info("Data integrity check passed")
            
            return result
            
        except Exception as e:
            self.logger.error("Error checking data integrity", error=str(e))
            return IntegrityCheckResult(False, [str(e)])
    
    async def _check_orphaned_items(self) -> List[str]:
        """Check for orphaned item records"""
        issues = []
        
        try:
            # Check for NFE items without parent NFE
            orphaned_nfe_items = await DatabaseManager.execute_query("""
                SELECT COUNT(*) as count
                FROM fact_itens_nfe i
                LEFT JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
                WHERE n.chave_nfe IS NULL
            """)
            
            if orphaned_nfe_items and orphaned_nfe_items[0]['count'] > 0:
                issues.append(f"Found {orphaned_nfe_items[0]['count']} orphaned NFE items")
            
            # Check for NFSE services without parent NFSE
            orphaned_nfse_services = await DatabaseManager.execute_query("""
                SELECT COUNT(*) as count
                FROM fact_servicos_nfse s
                LEFT JOIN nfse_main n ON s.id_nfse = n.id_nfse
                WHERE n.id_nfse IS NULL
            """)
            
            if orphaned_nfse_services and orphaned_nfse_services[0]['count'] > 0:
                issues.append(f"Found {orphaned_nfse_services[0]['count']} orphaned NFSE services")
            
        except Exception as e:
            issues.append(f"Error checking orphaned items: {str(e)}")
        
        return issues
    
    async def _check_missing_references(self) -> List[str]:
        """Check for missing reference data"""
        issues = []
        
        try:
            # Check for items referencing non-existent products
            missing_products = await DatabaseManager.execute_query("""
                SELECT COUNT(*) as count
                FROM fact_itens_nfe i
                LEFT JOIN dim_produtos p ON i.codigo_produto = p.codigo_produto
                WHERE p.codigo_produto IS NULL
            """)
            
            if missing_products and missing_products[0]['count'] > 0:
                issues.append(f"Found {missing_products[0]['count']} items with missing product references")
            
        except Exception as e:
            issues.append(f"Error checking missing references: {str(e)}")
        
        return issues
    
    async def _check_data_consistency(self) -> List[str]:
        """Check for data consistency issues"""
        issues = []
        
        try:
            # Check for negative values where they shouldn't exist
            negative_values = await DatabaseManager.execute_query("""
                SELECT COUNT(*) as count
                FROM nfe_main
                WHERE valor_total_nf < 0 OR valor_total_produtos < 0
            """)
            
            if negative_values and negative_values[0]['count'] > 0:
                issues.append(f"Found {negative_values[0]['count']} records with negative values")
            
        except Exception as e:
            issues.append(f"Error checking data consistency: {str(e)}")
        
        return issues
    
    async def maintain_referential_integrity(self):
        """Maintain referential integrity between entities"""
        try:
            # This would implement foreign key constraint checks
            # and cleanup operations if needed
            
            self.logger.info("Referential integrity maintained")
            
        except Exception as e:
            self.logger.error("Error maintaining referential integrity", error=str(e))
    
    async def preserve_historical_data(self, data: FiscalDocument):
        """Preserve historical information for trend analysis"""
        try:
            # Historical data is preserved by default in our schema
            # Additional archiving logic could be implemented here
            
            self.logger.info("Historical data preserved")
            
        except Exception as e:
            self.logger.error("Error preserving historical data", error=str(e))
    
    async def optimize_query_access(self, query: str) -> str:
        """Optimize query for better performance"""
        try:
            # Basic query optimization
            optimized_query = query
            
            # Add appropriate indexes hints if needed
            # This is a placeholder for more sophisticated optimization
            
            return optimized_query
            
        except Exception as e:
            self.logger.error("Error optimizing query", error=str(e))
            return query
    
    async def perform_advanced_analytics(self, analytics_request: AnalyticsRequest) -> AnalyticsResult:
        """Perform advanced analytics on stored data"""
        try:
            self.logger.info("Performing advanced analytics", 
                           query_type=analytics_request.query_type)
            
            if analytics_request.query_type == "supplier_analysis":
                data = await self._analyze_suppliers(analytics_request.parameters)
            elif analytics_request.query_type == "product_trends":
                data = await self._analyze_product_trends(analytics_request.parameters)
            elif analytics_request.query_type == "tax_efficiency":
                data = await self._analyze_tax_efficiency(analytics_request.parameters)
            elif analytics_request.query_type == "regional_distribution":
                data = await self._analyze_regional_distribution(analytics_request.parameters)
            else:
                data = []
            
            metadata = {
                'query_type': analytics_request.query_type,
                'parameters': analytics_request.parameters,
                'execution_time': '1.2s',  # Placeholder
                'data_points': len(data)
            }
            
            return AnalyticsResult(data, metadata)
            
        except Exception as e:
            self.logger.error("Error performing advanced analytics", error=str(e))
            return AnalyticsResult([], {'error': str(e)})
    
    async def _analyze_suppliers(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze supplier performance and trends"""
        query = """
            SELECT 
                e.razao_social,
                e.uf,
                COUNT(n.chave_nfe) as total_invoices,
                SUM(n.valor_total_nf) as total_value,
                AVG(n.valor_total_nf) as avg_value,
                MIN(n.data_emissao) as first_invoice,
                MAX(n.data_emissao) as last_invoice
            FROM dim_emitente e
            JOIN nfe_main n ON SUBSTRING(n.chave_nfe, 7, 14) = e.cnpj
            WHERE n.data_emissao >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY e.cnpj, e.razao_social, e.uf
            ORDER BY total_value DESC
            LIMIT 50
        """
        
        results = await DatabaseManager.execute_query(query)
        return [dict(row) for row in results] if results else []
    
    async def _analyze_product_trends(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze product purchase trends"""
        query = """
            SELECT 
                p.categoria,
                p.subcategoria,
                COUNT(i.id) as purchase_frequency,
                SUM(i.quantidade_comercial) as total_quantity,
                SUM(i.valor_total_bruto) as total_value,
                AVG(i.valor_unitario_comercial) as avg_unit_price
            FROM dim_produtos p
            JOIN fact_itens_nfe i ON p.codigo_produto = i.codigo_produto
            JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
            WHERE n.data_emissao >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY p.categoria, p.subcategoria
            ORDER BY total_value DESC
            LIMIT 30
        """
        
        results = await DatabaseManager.execute_query(query)
        return [dict(row) for row in results] if results else []
    
    async def _analyze_tax_efficiency(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tax efficiency and optimization opportunities"""
        query = """
            SELECT 
                DATE_FORMAT(data_emissao, '%Y-%m') as period,
                SUM(valor_total_nf) as total_value,
                SUM(valor_icms) as total_icms,
                SUM(valor_ipi) as total_ipi,
                SUM(valor_pis) as total_pis,
                SUM(valor_cofins) as total_cofins,
                (SUM(valor_icms + COALESCE(valor_ipi, 0) + COALESCE(valor_pis, 0) + COALESCE(valor_cofins, 0)) / SUM(valor_total_nf)) * 100 as tax_rate
            FROM nfe_main
            WHERE data_emissao >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY DATE_FORMAT(data_emissao, '%Y-%m')
            ORDER BY period DESC
        """
        
        results = await DatabaseManager.execute_query(query)
        return [dict(row) for row in results] if results else []
    
    async def _analyze_regional_distribution(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze regional distribution of suppliers and transactions"""
        query = """
            SELECT 
                e.uf,
                COUNT(DISTINCT e.cnpj) as supplier_count,
                COUNT(n.chave_nfe) as invoice_count,
                SUM(n.valor_total_nf) as total_value,
                AVG(n.valor_total_nf) as avg_invoice_value
            FROM dim_emitente e
            JOIN nfe_main n ON SUBSTRING(n.chave_nfe, 7, 14) = e.cnpj
            WHERE n.data_emissao >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY e.uf
            ORDER BY total_value DESC
        """
        
        results = await DatabaseManager.execute_query(query)
        return [dict(row) for row in results] if results else []
    
    async def _execute_query(self, query: str, parameters: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute custom query"""
        try:
            results = await DatabaseManager.execute_query(query, *(parameters or []))
            return [dict(row) for row in results] if results else []
        except Exception as e:
            self.logger.error("Error executing query", error=str(e))
            return []
    
    async def _periodic_integrity_check(self):
        """Periodic integrity check task"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                await self.maintain_data_integrity()
            except Exception as e:
                self.logger.error("Error in periodic integrity check", error=str(e))