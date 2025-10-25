"""
SQL Agent for natural language to SQL query translation
"""

import asyncio
from typing import Dict, Any, List, Optional
import re
import structlog

from .base_agent import BaseAgent
from utils.database import DatabaseManager
from utils.config import settings


class SQLQuery:
    """SQL Query representation"""
    
    def __init__(self, sql: str, parameters: List[Any] = None, query_type: str = "SELECT"):
        self.sql = sql
        self.parameters = parameters or []
        self.query_type = query_type
        self.estimated_rows = 0
        self.complexity_score = 0


class QueryResult:
    """Query execution result"""
    
    def __init__(self, data: List[Dict[str, Any]], metadata: Dict[str, Any], execution_time: float, row_count: int):
        self.data = data
        self.metadata = metadata
        self.execution_time = execution_time
        self.row_count = row_count


class SQLAgent(BaseAgent):
    """Agent responsible for converting natural language to SQL queries"""
    
    def __init__(self):
        super().__init__("SQLAgent")
        self.table_schema = {}
        self.query_templates = {}
        self.business_terms = {}
        
    async def initialize(self):
        """Initialize SQL Agent resources"""
        try:
            # Load database schema information
            await self._load_table_schema()
            
            # Load query templates for common business questions
            await self._load_query_templates()
            
            # Load business term mappings
            await self._load_business_terms()
            
            self.logger.info("SQL Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize SQL Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("SQL Agent cleaned up")
    
    async def process(self, data: Dict[str, Any]) -> SQLQuery:
        """Process natural language query to generate SQL"""
        if isinstance(data, dict) and 'query' in data:
            business_question = data['query']
            entities = data.get('entities', {})
            return await self.generate_sql(business_question, entities)
        return None
    
    async def _load_table_schema(self):
        """Load database table schema information"""
        try:
            # Define the schema structure for our fiscal database
            self.table_schema = {
                'nfe_main': {
                    'columns': [
                        'chave_nfe', 'numero_nf', 'serie', 'data_emissao', 'data_saida_entrada',
                        'tipo_operacao', 'codigo_municipio', 'uf_emitente', 'natureza_operacao',
                        'valor_total_nf', 'valor_total_produtos', 'valor_icms', 'valor_ipi',
                        'valor_pis', 'valor_cofins', 'processed_at'
                    ],
                    'primary_key': 'chave_nfe',
                    'description': 'Main NF-e (electronic invoice) table'
                },
                'nfse_main': {
                    'columns': [
                        'id_nfse', 'numero_nfse', 'numero_dfse', 'data_emissao',
                        'codigo_municipio_emissao', 'valor_total_servicos', 'valor_issqn',
                        'valor_credito', 'processed_at'
                    ],
                    'primary_key': 'id_nfse',
                    'description': 'Main NFS-e (electronic service invoice) table'
                },
                'dim_emitente': {
                    'columns': [
                        'cnpj', 'razao_social', 'nome_fantasia', 'uf', 'codigo_municipio',
                        'nome_municipio', 'regime_tributario'
                    ],
                    'primary_key': 'cnpj',
                    'description': 'Supplier/issuer dimension table'
                },
                'dim_produtos': {
                    'columns': [
                        'codigo_produto', 'descricao', 'ncm', 'cfop', 'categoria', 'subcategoria'
                    ],
                    'primary_key': 'codigo_produto',
                    'description': 'Product dimension table'
                },
                'dim_servicos': {
                    'columns': [
                        'codigo_servico', 'descricao', 'codigo_cnae', 'categoria', 'subcategoria'
                    ],
                    'primary_key': 'codigo_servico',
                    'description': 'Service dimension table'
                },
                'fact_itens_nfe': {
                    'columns': [
                        'chave_nfe', 'codigo_produto', 'quantidade_comercial', 'valor_unitario_comercial',
                        'valor_total_bruto', 'valor_icms', 'valor_ipi', 'valor_pis', 'valor_cofins'
                    ],
                    'foreign_keys': ['chave_nfe', 'codigo_produto'],
                    'description': 'NF-e items fact table'
                },
                'fact_servicos_nfse': {
                    'columns': [
                        'id_nfse', 'codigo_servico', 'quantidade', 'valor_unitario',
                        'valor_total', 'valor_issqn'
                    ],
                    'foreign_keys': ['id_nfse', 'codigo_servico'],
                    'description': 'NFS-e services fact table'
                },
                'vw_documentos_fiscais': {
                    'columns': [
                        'tipo_documento', 'identificador', 'data_emissao', 'valor_total',
                        'valor_servicos', 'valor_total_produtos', 'valor_issqn', 'valor_icms'
                    ],
                    'description': 'Unified view of all fiscal documents'
                },
                'vw_fornecedores_resumo': {
                    'columns': [
                        'cnpj', 'razao_social', 'uf', 'total_notas', 'valor_total',
                        'valor_medio', 'primeira_compra', 'ultima_compra'
                    ],
                    'description': 'Supplier summary view'
                }
            }
            
            self.logger.info("Table schema loaded", tables=len(self.table_schema))
            
        except Exception as e:
            self.logger.error("Error loading table schema", error=str(e))
    
    async def _load_query_templates(self):
        """Load common query templates"""
        try:
            self.query_templates = {
                'top_suppliers': """
                    SELECT e.razao_social, SUM(n.valor_total_nf) as total_value
                    FROM nfe_main n
                    JOIN dim_emitente e ON SUBSTRING(n.chave_nfe, 7, 14) = e.cnpj
                    WHERE n.data_emissao >= '{start_date}'
                    GROUP BY e.cnpj, e.razao_social
                    ORDER BY total_value DESC
                    LIMIT {limit}
                """,
                
                'monthly_summary': """
                    SELECT 
                        DATE_FORMAT(data_emissao, '%Y-%m') as periodo,
                        COUNT(*) as total_documentos,
                        SUM(valor_total) as valor_total
                    FROM vw_documentos_fiscais
                    WHERE data_emissao >= '{start_date}'
                    GROUP BY DATE_FORMAT(data_emissao, '%Y-%m')
                    ORDER BY periodo DESC
                """,
                
                'product_analysis': """
                    SELECT 
                        p.categoria,
                        COUNT(i.id) as quantidade_compras,
                        SUM(i.valor_total_bruto) as valor_total,
                        AVG(i.valor_unitario_comercial) as preco_medio
                    FROM fact_itens_nfe i
                    JOIN dim_produtos p ON i.codigo_produto = p.codigo_produto
                    JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
                    WHERE n.data_emissao >= '{start_date}'
                    GROUP BY p.categoria
                    ORDER BY valor_total DESC
                """,
                
                'tax_analysis': """
                    SELECT 
                        tipo_documento,
                        SUM(valor_total) as valor_total,
                        SUM(COALESCE(valor_icms, 0)) as total_icms,
                        SUM(COALESCE(valor_issqn, 0)) as total_issqn,
                        (SUM(COALESCE(valor_icms, 0) + COALESCE(valor_issqn, 0)) / SUM(valor_total)) * 100 as taxa_tributaria
                    FROM vw_documentos_fiscais
                    WHERE data_emissao >= '{start_date}'
                    GROUP BY tipo_documento
                """,
                
                'supplier_by_region': """
                    SELECT 
                        e.uf,
                        COUNT(DISTINCT e.cnpj) as total_fornecedores,
                        SUM(n.valor_total_nf) as valor_total
                    FROM dim_emitente e
                    JOIN nfe_main n ON SUBSTRING(n.chave_nfe, 7, 14) = e.cnpj
                    WHERE n.data_emissao >= '{start_date}'
                    GROUP BY e.uf
                    ORDER BY valor_total DESC
                """
            }
            
            self.logger.info("Query templates loaded", templates=len(self.query_templates))
            
        except Exception as e:
            self.logger.error("Error loading query templates", error=str(e))
    
    async def _load_business_terms(self):
        """Load business term to database field mappings"""
        try:
            self.business_terms = {
                # Portuguese business terms
                'fornecedor': ['dim_emitente.razao_social', 'dim_emitente.nome_fantasia'],
                'fornecedores': ['dim_emitente.razao_social', 'dim_emitente.nome_fantasia'],
                'supplier': ['dim_emitente.razao_social', 'dim_emitente.nome_fantasia'],
                'suppliers': ['dim_emitente.razao_social', 'dim_emitente.nome_fantasia'],
                
                'produto': ['dim_produtos.descricao', 'dim_produtos.categoria'],
                'produtos': ['dim_produtos.descricao', 'dim_produtos.categoria'],
                'product': ['dim_produtos.descricao', 'dim_produtos.categoria'],
                'products': ['dim_produtos.descricao', 'dim_produtos.categoria'],
                
                'serviço': ['dim_servicos.descricao', 'dim_servicos.categoria'],
                'serviços': ['dim_servicos.descricao', 'dim_servicos.categoria'],
                'service': ['dim_servicos.descricao', 'dim_servicos.categoria'],
                'services': ['dim_servicos.descricao', 'dim_servicos.categoria'],
                
                'valor': ['valor_total_nf', 'valor_total_servicos', 'valor_total'],
                'total': ['valor_total_nf', 'valor_total_servicos', 'valor_total'],
                'value': ['valor_total_nf', 'valor_total_servicos', 'valor_total'],
                
                'imposto': ['valor_icms', 'valor_ipi', 'valor_issqn'],
                'impostos': ['valor_icms', 'valor_ipi', 'valor_issqn'],
                'tax': ['valor_icms', 'valor_ipi', 'valor_issqn'],
                'taxes': ['valor_icms', 'valor_ipi', 'valor_issqn'],
                
                'estado': ['uf', 'uf_emitente'],
                'região': ['uf', 'uf_emitente'],
                'region': ['uf', 'uf_emitente'],
                'state': ['uf', 'uf_emitente'],
                
                'mês': ['data_emissao'],
                'mensal': ['data_emissao'],
                'monthly': ['data_emissao'],
                'month': ['data_emissao'],
                
                'ano': ['data_emissao'],
                'anual': ['data_emissao'],
                'yearly': ['data_emissao'],
                'year': ['data_emissao']
            }
            
            self.logger.info("Business terms loaded", terms=len(self.business_terms))
            
        except Exception as e:
            self.logger.error("Error loading business terms", error=str(e))
    
    async def generate_sql(self, business_question: str, entities: Dict[str, Any] = None) -> SQLQuery:
        """Generate SQL query from business question"""
        try:
            self.logger.info("Generating SQL", question=business_question)
            
            entities = entities or {}
            question_lower = business_question.lower()
            
            # Determine query intent and select appropriate template
            sql_query = await self._select_query_template(question_lower, entities)
            
            if not sql_query:
                # If no template matches, try to build custom query
                sql_query = await self._build_custom_query(question_lower, entities)
            
            # Optimize the query
            optimized_query = await self.optimize_query(sql_query)
            
            self.logger.info("SQL generated", sql=optimized_query.sql[:100] + "...")
            
            return optimized_query
            
        except Exception as e:
            self.logger.error("Error generating SQL", error=str(e))
            raise
    
    async def _select_query_template(self, question: str, entities: Dict[str, Any]) -> Optional[SQLQuery]:
        """Select appropriate query template based on question"""
        
        # Default date range
        start_date = entities.get('start_date', '2024-01-01')
        limit = entities.get('limit', 10)
        
        # Top suppliers query
        if any(term in question for term in ['maior', 'top', 'principal', 'fornecedor']):
            if any(term in question for term in ['fornecedor', 'supplier']):
                sql = self.query_templates['top_suppliers'].format(
                    start_date=start_date,
                    limit=limit
                )
                return SQLQuery(sql, query_type="SELECT")
        
        # Monthly summary
        if any(term in question for term in ['mensal', 'mês', 'monthly', 'resumo']):
            sql = self.query_templates['monthly_summary'].format(start_date=start_date)
            return SQLQuery(sql, query_type="SELECT")
        
        # Product analysis
        if any(term in question for term in ['produto', 'product', 'categoria']):
            sql = self.query_templates['product_analysis'].format(start_date=start_date)
            return SQLQuery(sql, query_type="SELECT")
        
        # Tax analysis
        if any(term in question for term in ['imposto', 'tax', 'tributário', 'icms', 'issqn']):
            sql = self.query_templates['tax_analysis'].format(start_date=start_date)
            return SQLQuery(sql, query_type="SELECT")
        
        # Regional analysis
        if any(term in question for term in ['região', 'estado', 'uf', 'region', 'state']):
            sql = self.query_templates['supplier_by_region'].format(start_date=start_date)
            return SQLQuery(sql, query_type="SELECT")
        
        return None
    
    async def _build_custom_query(self, question: str, entities: Dict[str, Any]) -> SQLQuery:
        """Build custom SQL query when no template matches"""
        
        # This is a simplified custom query builder
        # In a real implementation, this would be much more sophisticated
        
        # Determine main table based on document type
        if entities.get('document_type') == 'NFSE':
            main_table = 'nfse_main'
            value_column = 'valor_total_servicos'
        else:
            main_table = 'nfe_main'
            value_column = 'valor_total_nf'
        
        # Build basic SELECT
        select_columns = [value_column, 'data_emissao']
        
        # Add columns based on question content
        if any(term in question for term in ['fornecedor', 'supplier']):
            select_columns.append('dim_emitente.razao_social')
        
        # Build FROM clause
        from_clause = main_table
        joins = []
        
        # Add joins based on needed columns
        if 'dim_emitente.razao_social' in select_columns:
            if main_table == 'nfe_main':
                joins.append("JOIN dim_emitente ON SUBSTRING(nfe_main.chave_nfe, 7, 14) = dim_emitente.cnpj")
            else:
                joins.append("JOIN dim_emitente ON SUBSTRING(nfse_main.id_nfse, 9, 14) = dim_emitente.cnpj")
        
        # Build WHERE clause
        where_conditions = ["data_emissao >= '2024-01-01'"]
        
        # Build ORDER BY
        order_by = f"{value_column} DESC"
        
        # Construct final SQL
        sql = f"""
            SELECT {', '.join(select_columns)}
            FROM {from_clause}
            {' '.join(joins)}
            WHERE {' AND '.join(where_conditions)}
            ORDER BY {order_by}
            LIMIT 100
        """
        
        return SQLQuery(sql.strip(), query_type="SELECT")
    
    async def optimize_query(self, query: SQLQuery) -> SQLQuery:
        """Optimize SQL query for better performance"""
        try:
            optimized_sql = query.sql
            
            # Basic optimizations
            
            # Add LIMIT if not present and it's a SELECT query
            if query.query_type == "SELECT" and "LIMIT" not in optimized_sql.upper():
                optimized_sql += " LIMIT 1000"
            
            # Ensure date filters use indexes
            optimized_sql = re.sub(
                r"data_emissao >= '(\d{4}-\d{2}-\d{2})'",
                r"data_emissao >= '\1' AND data_emissao < DATE_ADD('\1', INTERVAL 1 YEAR)",
                optimized_sql
            )
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(optimized_sql)
            
            optimized_query = SQLQuery(
                sql=optimized_sql,
                parameters=query.parameters,
                query_type=query.query_type
            )
            optimized_query.complexity_score = complexity_score
            
            return optimized_query
            
        except Exception as e:
            self.logger.error("Error optimizing query", error=str(e))
            return query
    
    def _calculate_complexity(self, sql: str) -> int:
        """Calculate query complexity score"""
        score = 0
        sql_upper = sql.upper()
        
        # Count JOINs
        score += sql_upper.count('JOIN') * 2
        
        # Count subqueries
        score += sql_upper.count('SELECT') - 1
        
        # Count aggregations
        score += sql_upper.count('GROUP BY') * 3
        score += sql_upper.count('ORDER BY') * 1
        
        # Count functions
        score += sql_upper.count('SUM(') * 1
        score += sql_upper.count('COUNT(') * 1
        score += sql_upper.count('AVG(') * 1
        
        return score
    
    async def validate_syntax(self, query: SQLQuery) -> Dict[str, Any]:
        """Validate SQL syntax"""
        try:
            # Basic syntax validation
            sql = query.sql.strip()
            
            if not sql:
                return {'valid': False, 'error': 'Empty query'}
            
            # Check for basic SQL structure
            if not any(keyword in sql.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                return {'valid': False, 'error': 'No valid SQL command found'}
            
            # Check for balanced parentheses
            if sql.count('(') != sql.count(')'):
                return {'valid': False, 'error': 'Unbalanced parentheses'}
            
            # Check for SQL injection patterns (basic)
            dangerous_patterns = [
                r';\s*DROP\s+TABLE',
                r';\s*DELETE\s+FROM',
                r';\s*UPDATE\s+.*\s+SET',
                r'UNION\s+SELECT.*--'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    return {'valid': False, 'error': 'Potentially dangerous SQL pattern detected'}
            
            return {'valid': True, 'warnings': []}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def execute_query(self, query: SQLQuery) -> QueryResult:
        """Execute SQL query and return results"""
        try:
            # Validate query first
            validation = await self.validate_syntax(query)
            if not validation['valid']:
                raise ValueError(f"Invalid query: {validation['error']}")
            
            self.logger.info("Executing query", sql=query.sql[:100] + "...")
            
            start_time = asyncio.get_event_loop().time()
            
            # Execute query using DatabaseManager
            results = await DatabaseManager.execute_query(query.sql, *query.parameters)
            
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # Convert results to list of dictionaries
            data = []
            if results:
                columns = list(results[0].keys()) if results else []
                data = [dict(row) for row in results]
            
            metadata = {
                'columns': columns if results else [],
                'query_type': query.query_type,
                'complexity_score': query.complexity_score,
                'execution_time': execution_time
            }
            
            query_result = QueryResult(
                data=data,
                metadata=metadata,
                execution_time=execution_time,
                row_count=len(data)
            )
            
            self.logger.info("Query executed successfully", 
                           rows=query_result.row_count, 
                           time=f"{execution_time:.3f}s")
            
            return query_result
            
        except Exception as e:
            self.logger.error("Error executing query", error=str(e))
            raise
    
    async def explain_query(self, query: SQLQuery) -> Dict[str, Any]:
        """Explain query execution plan"""
        try:
            explain_sql = f"EXPLAIN {query.sql}"
            
            # Execute EXPLAIN query
            explain_results = await DatabaseManager.execute_query(explain_sql, *query.parameters)
            
            return {
                'execution_plan': [dict(row) for row in explain_results],
                'complexity_score': query.complexity_score,
                'estimated_cost': 'medium'  # Placeholder
            }
            
        except Exception as e:
            self.logger.error("Error explaining query", error=str(e))
            return {'error': str(e)}