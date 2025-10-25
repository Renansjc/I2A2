"""
LLM-Enhanced SQL Agent for intelligent business-to-SQL translation
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
import re
import structlog
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from utils.database import DatabaseManager
from utils.config import settings
from utils.openai_integration import get_openai_service, LLMResponse, BusinessInsights


class SQLTranslation:
    """Enhanced SQL translation with business context"""
    
    def __init__(self, sql_query: str, business_logic_explanation: str, 
                 confidence_score: float, optimization_suggestions: List[str] = None,
                 potential_issues: List[str] = None, estimated_performance: Dict[str, Any] = None):
        self.sql_query = sql_query
        self.business_logic_explanation = business_logic_explanation
        self.confidence_score = confidence_score
        self.optimization_suggestions = optimization_suggestions or []
        self.potential_issues = potential_issues or []
        self.estimated_performance = estimated_performance or {}
        self.parameters = []
        self.query_type = "SELECT"
        self.complexity_score = 0

class OptimizedQuery:
    """Optimized SQL query with business context"""
    
    def __init__(self, original_query: str, optimized_query: str, 
                 optimization_reasoning: str, performance_improvement: Dict[str, Any],
                 business_alignment: str):
        self.original_query = original_query
        self.optimized_query = optimized_query
        self.optimization_reasoning = optimization_reasoning
        self.performance_improvement = performance_improvement
        self.business_alignment = business_alignment

class QueryExplanation:
    """Business-focused query explanation"""
    
    def __init__(self, sql_query: str, business_purpose: str, 
                 data_sources: List[str], business_impact: str,
                 confidence_assessment: str, data_quality_notes: List[str]):
        self.sql_query = sql_query
        self.business_purpose = business_purpose
        self.data_sources = data_sources
        self.business_impact = business_impact
        self.confidence_assessment = confidence_assessment
        self.data_quality_notes = data_quality_notes

class SchemaContext:
    """Database schema context for LLM understanding"""
    
    def __init__(self):
        self.schema_info = {}
        self.business_rules = {}
        self.data_relationships = {}
        self.query_examples = []
    
    async def get_relevant_schema(self, natural_query: str) -> Dict[str, Any]:
        """Get schema information relevant to the natural query"""
        # This would analyze the query and return relevant schema parts
        # For now, return the full schema context
        return {
            'tables': self.schema_info,
            'relationships': self.data_relationships,
            'business_rules': self.business_rules
        }

class SQLQuery:
    """SQL Query representation (legacy compatibility)"""
    
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


class LLMEnhancedSQLAgent(BaseAgent):
    """LLM-Enhanced SQL Agent for intelligent business-to-SQL translation"""
    
    def __init__(self):
        super().__init__("LLMEnhancedSQLAgent")
        self.llm_service = get_openai_service()
        self.schema_context = SchemaContext()
        self.table_schema = {}
        self.query_templates = {}
        self.business_terms = {}
        self.business_rules = {}
        self.query_examples = []
        
    async def initialize(self):
        """Initialize LLM-Enhanced SQL Agent resources"""
        try:
            # Load database schema information
            await self._load_table_schema()
            
            # Load query templates for common business questions
            await self._load_query_templates()
            
            # Load business term mappings
            await self._load_business_terms()
            
            # Load business rules for LLM context
            await self._load_business_rules()
            
            # Load query examples for LLM learning
            await self._load_query_examples()
            
            # Initialize schema context for LLM
            await self._initialize_schema_context()
            
            self.logger.info("LLM-Enhanced SQL Agent initialized")
            
        except Exception as e:
            self.logger.error("Failed to initialize LLM-Enhanced SQL Agent", error=str(e))
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
    
    # ===== LLM-ENHANCED METHODS =====
    
    async def translate_business_query(
        self,
        natural_query: str,
        business_context: Dict[str, Any]
    ) -> SQLTranslation:
        """Convert business questions to SQL with full context understanding"""
        try:
            self.logger.info("Translating business query with LLM", query=natural_query)
            
            # Get relevant schema context
            schema_context = await self.schema_context.get_relevant_schema(natural_query)
            
            # Prepare context for LLM
            llm_context = {
                'natural_query': natural_query,
                'database_schema': schema_context,
                'business_rules': self.business_rules,
                'data_relationships': self.schema_context.data_relationships,
                'query_examples': await self._get_similar_query_examples(natural_query),
                'business_context': business_context,
                'user_role': business_context.get('user_role', 'executive'),
                'table_descriptions': self._get_table_descriptions(),
                'brazilian_context': {
                    'fiscal_document_types': ['NF-e', 'NFS-e'],
                    'tax_types': ['ICMS', 'IPI', 'PIS', 'COFINS', 'ISSQN'],
                    'date_format': 'DD/MM/YYYY',
                    'currency': 'BRL'
                }
            }
            
            # Use LLM to translate business query to SQL
            response = await self.llm_service.generate_completion(
                "business_to_sql_translation",
                llm_context,
                model="gpt-4o-mini",
                temperature=0.1
            )
            
            # Parse LLM response
            translation = await self._parse_sql_translation_response(response, natural_query)
            
            self.logger.info("Business query translated successfully", 
                           confidence=translation.confidence_score)
            
            return translation
            
        except Exception as e:
            self.logger.error("Error translating business query", error=str(e))
            # Fallback to traditional method
            fallback_query = await self.generate_sql(natural_query, business_context)
            return SQLTranslation(
                sql_query=fallback_query.sql,
                business_logic_explanation="Fallback translation due to LLM error",
                confidence_score=0.5,
                optimization_suggestions=["Review query manually"],
                potential_issues=[f"LLM translation failed: {str(e)}"]
            )
    
    async def optimize_query_for_business(
        self,
        sql_query: str,
        business_objective: str
    ) -> OptimizedQuery:
        """Optimize SQL query based on business objectives"""
        try:
            self.logger.info("Optimizing query for business objective", 
                           objective=business_objective)
            
            # Prepare context for LLM optimization
            llm_context = {
                'original_query': sql_query,
                'business_objective': business_objective,
                'performance_requirements': await self._get_performance_requirements(),
                'data_volume_estimates': await self._get_data_volume_estimates(),
                'index_information': await self._get_index_information(),
                'optimization_patterns': await self._get_optimization_patterns(),
                'database_type': 'PostgreSQL',
                'business_constraints': {
                    'max_execution_time': '30 seconds',
                    'data_freshness_requirements': 'real-time for current month, daily for historical',
                    'user_expectations': 'executive-level summary data'
                }
            }
            
            # Use LLM for intelligent optimization
            response = await self.llm_service.generate_completion(
                "query_optimization",
                llm_context,
                model="gpt-4o-mini",
                temperature=0.1
            )
            
            # Parse optimization response
            optimization = await self._parse_optimization_response(response, sql_query)
            
            self.logger.info("Query optimized successfully")
            
            return optimization
            
        except Exception as e:
            self.logger.error("Error optimizing query", error=str(e))
            # Return original query as fallback
            return OptimizedQuery(
                original_query=sql_query,
                optimized_query=sql_query,
                optimization_reasoning=f"Optimization failed: {str(e)}",
                performance_improvement={'status': 'no_improvement'},
                business_alignment="Unable to assess due to optimization error"
            )
    
    async def explain_query_business_logic(
        self,
        sql_query: str,
        results: QueryResult
    ) -> QueryExplanation:
        """Generate business-focused explanation of query and results"""
        try:
            self.logger.info("Generating business explanation for query")
            
            # Prepare context for business explanation
            llm_context = {
                'sql_query': sql_query,
                'query_results': {
                    'row_count': results.row_count,
                    'execution_time': results.execution_time,
                    'sample_data': results.data[:5] if results.data else [],
                    'columns': list(results.data[0].keys()) if results.data else []
                },
                'business_impact': await self._analyze_business_impact(results),
                'data_quality_assessment': await self._assess_data_quality(results),
                'confidence_level': await self._calculate_confidence_level(results),
                'executive_context': {
                    'focus_areas': ['financial_impact', 'operational_insights', 'strategic_implications'],
                    'communication_style': 'executive_summary',
                    'language': 'portuguese'
                }
            }
            
            # Use LLM to generate business explanation
            response = await self.llm_service.generate_completion(
                "business_explanation",
                llm_context,
                model="gpt-4o-mini",
                temperature=0.2
            )
            
            # Parse explanation response
            explanation = await self._parse_explanation_response(response, sql_query, results)
            
            self.logger.info("Business explanation generated successfully")
            
            return explanation
            
        except Exception as e:
            self.logger.error("Error generating business explanation", error=str(e))
            # Return basic explanation as fallback
            return QueryExplanation(
                sql_query=sql_query,
                business_purpose="Consulta de dados fiscais para análise executiva",
                data_sources=self._extract_table_names(sql_query),
                business_impact="Impacto não determinado devido a erro na análise",
                confidence_assessment="Baixa confiança devido a erro no processamento",
                data_quality_notes=[f"Erro na análise: {str(e)}"]
            )
    
    # ===== LLM HELPER METHODS =====
    
    async def _load_business_rules(self):
        """Load business rules for LLM context"""
        try:
            self.business_rules = {
                'fiscal_document_validation': {
                    'nfe_required_fields': ['chave_nfe', 'numero_nf', 'data_emissao', 'valor_total_nf'],
                    'nfse_required_fields': ['id_nfse', 'numero_nfse', 'data_emissao', 'valor_total_servicos'],
                    'date_range_limits': 'Maximum 2 years for detailed queries, unlimited for summaries'
                },
                'business_logic': {
                    'supplier_classification': 'Based on transaction volume and frequency',
                    'product_categorization': 'Uses NCM codes and business context',
                    'tax_calculations': 'Brazilian tax rules (ICMS, IPI, PIS, COFINS, ISSQN)',
                    'regional_analysis': 'Based on UF (state) codes'
                },
                'performance_guidelines': {
                    'large_datasets': 'Use aggregation and date filters',
                    'real_time_queries': 'Limit to current month data',
                    'historical_analysis': 'Use monthly/yearly aggregations'
                }
            }
            
            self.logger.info("Business rules loaded for LLM context")
            
        except Exception as e:
            self.logger.error("Error loading business rules", error=str(e))
    
    async def _load_query_examples(self):
        """Load query examples for LLM learning"""
        try:
            self.query_examples = [
                {
                    'business_question': 'Quais são os 5 maiores fornecedores por valor no último trimestre?',
                    'sql_query': """
                        SELECT e.razao_social, SUM(n.valor_total_nf) as total_value
                        FROM nfe_main n
                        JOIN dim_emitente e ON SUBSTRING(n.chave_nfe, 7, 14) = e.cnpj
                        WHERE n.data_emissao >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                        GROUP BY e.cnpj, e.razao_social
                        ORDER BY total_value DESC
                        LIMIT 5
                    """,
                    'explanation': 'Identifica fornecedores com maior volume de transações'
                },
                {
                    'business_question': 'Qual foi o total de impostos pagos por tipo no ano passado?',
                    'sql_query': """
                        SELECT 
                            'ICMS' as tipo_imposto, SUM(valor_icms) as total
                        FROM vw_documentos_fiscais
                        WHERE YEAR(data_emissao) = YEAR(CURDATE()) - 1
                        UNION ALL
                        SELECT 
                            'ISSQN' as tipo_imposto, SUM(valor_issqn) as total
                        FROM vw_documentos_fiscais
                        WHERE YEAR(data_emissao) = YEAR(CURDATE()) - 1
                    """,
                    'explanation': 'Sumariza impostos por tipo para análise fiscal'
                },
                {
                    'business_question': 'Quais produtos tiveram maior crescimento de preço este ano?',
                    'sql_query': """
                        WITH preco_atual AS (
                            SELECT p.codigo_produto, p.descricao,
                                   AVG(i.valor_unitario_comercial) as preco_medio_atual
                            FROM fact_itens_nfe i
                            JOIN dim_produtos p ON i.codigo_produto = p.codigo_produto
                            JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
                            WHERE n.data_emissao >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                            GROUP BY p.codigo_produto, p.descricao
                        ),
                        preco_anterior AS (
                            SELECT p.codigo_produto,
                                   AVG(i.valor_unitario_comercial) as preco_medio_anterior
                            FROM fact_itens_nfe i
                            JOIN dim_produtos p ON i.codigo_produto = p.codigo_produto
                            JOIN nfe_main n ON i.chave_nfe = n.chave_nfe
                            WHERE n.data_emissao BETWEEN DATE_SUB(CURDATE(), INTERVAL 15 MONTH) 
                                  AND DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                            GROUP BY p.codigo_produto
                        )
                        SELECT pa.codigo_produto, pa.descricao,
                               pa.preco_medio_atual, pr.preco_medio_anterior,
                               ((pa.preco_medio_atual - pr.preco_medio_anterior) / pr.preco_medio_anterior) * 100 as crescimento_percentual
                        FROM preco_atual pa
                        JOIN preco_anterior pr ON pa.codigo_produto = pr.codigo_produto
                        ORDER BY crescimento_percentual DESC
                        LIMIT 10
                    """,
                    'explanation': 'Analisa variação de preços para identificar tendências de mercado'
                }
            ]
            
            self.logger.info("Query examples loaded for LLM learning", examples=len(self.query_examples))
            
        except Exception as e:
            self.logger.error("Error loading query examples", error=str(e))
    
    async def _initialize_schema_context(self):
        """Initialize schema context for LLM"""
        try:
            self.schema_context.schema_info = self.table_schema
            self.schema_context.business_rules = self.business_rules
            self.schema_context.query_examples = self.query_examples
            
            # Set up data relationships
            self.schema_context.data_relationships = {
                'nfe_to_emitente': 'SUBSTRING(nfe_main.chave_nfe, 7, 14) = dim_emitente.cnpj',
                'nfe_to_items': 'nfe_main.chave_nfe = fact_itens_nfe.chave_nfe',
                'items_to_products': 'fact_itens_nfe.codigo_produto = dim_produtos.codigo_produto',
                'nfse_to_emitente': 'SUBSTRING(nfse_main.id_nfse, 9, 14) = dim_emitente.cnpj',
                'nfse_to_services': 'nfse_main.id_nfse = fact_servicos_nfse.id_nfse',
                'services_to_service_dim': 'fact_servicos_nfse.codigo_servico = dim_servicos.codigo_servico'
            }
            
            self.logger.info("Schema context initialized for LLM")
            
        except Exception as e:
            self.logger.error("Error initializing schema context", error=str(e))
    
    def _get_business_to_sql_prompt(self) -> str:
        """Get prompt template for business-to-SQL translation"""
        return """
Você é um especialista em SQL e análise de dados fiscais brasileiros. Sua tarefa é converter perguntas empresariais em consultas SQL otimizadas.

CONTEXTO DA CONSULTA:
Pergunta Empresarial: {natural_query}
Cargo do Usuário: {user_role}
Contexto Empresarial: {business_context}

ESQUEMA DO BANCO DE DADOS:
{database_schema}

REGRAS DE NEGÓCIO:
{business_rules}

RELACIONAMENTOS DE DADOS:
{data_relationships}

EXEMPLOS DE CONSULTAS SIMILARES:
{query_examples}

CONTEXTO BRASILEIRO:
- Tipos de documentos fiscais: {brazilian_context[fiscal_document_types]}
- Tipos de impostos: {brazilian_context[tax_types]}
- Formato de data: {brazilian_context[date_format]}
- Moeda: {brazilian_context[currency]}

INSTRUÇÕES:
1. Analise a pergunta empresarial e identifique:
   - Objetivo principal da consulta
   - Dados necessários
   - Filtros e agregações requeridas
   - Período temporal (se aplicável)

2. Gere uma consulta SQL que:
   - Reflita com precisão a intenção empresarial
   - Use JOINs apropriados baseados nos relacionamentos
   - Inclua filtros de performance (datas, limites)
   - Otimize para execução eficiente
   - Trate casos extremos adequadamente

3. Forneça explicação da lógica empresarial em português

4. Avalie a confiança da tradução (0-1)

5. Identifique possíveis problemas ou sugestões de otimização

RESPOSTA EM JSON:
{{
    "sql_query": "consulta SQL completa",
    "business_logic_explanation": "explicação da lógica empresarial em português",
    "confidence_score": 0.95,
    "optimization_suggestions": ["sugestão 1", "sugestão 2"],
    "potential_issues": ["problema potencial 1"],
    "estimated_performance": {{
        "complexity": "medium",
        "estimated_rows": 1000,
        "execution_time_estimate": "< 5 segundos"
    }}
}}
"""
    
    def _get_query_optimization_prompt(self) -> str:
        """Get prompt template for query optimization"""
        return """
Você é um especialista em otimização de consultas SQL para bancos de dados PostgreSQL com foco em dados fiscais brasileiros.

CONSULTA ORIGINAL:
{original_query}

OBJETIVO EMPRESARIAL:
{business_objective}

CONTEXTO DE PERFORMANCE:
- Requisitos de Performance: {performance_requirements}
- Estimativas de Volume de Dados: {data_volume_estimates}
- Informações de Índices: {index_information}
- Padrões de Otimização: {optimization_patterns}
- Tipo de Banco: {database_type}

RESTRIÇÕES EMPRESARIAIS:
{business_constraints}

INSTRUÇÕES:
1. Analise a consulta original identificando:
   - Gargalos de performance
   - Oportunidades de otimização
   - Uso inadequado de índices
   - JOINs desnecessários ou ineficientes

2. Otimize a consulta considerando:
   - Alinhamento com o objetivo empresarial
   - Melhoria de performance
   - Manutenção da precisão dos resultados
   - Legibilidade e manutenibilidade

3. Explique as otimizações realizadas

4. Estime a melhoria de performance

RESPOSTA EM JSON:
{{
    "optimized_query": "consulta SQL otimizada",
    "optimization_reasoning": "explicação das otimizações em português",
    "performance_improvement": {{
        "estimated_speedup": "2x mais rápida",
        "resource_usage": "50% menos CPU",
        "scalability": "melhor para grandes volumes"
    }},
    "business_alignment": "como a otimização atende ao objetivo empresarial"
}}
"""
    
    def _get_business_explanation_prompt(self) -> str:
        """Get prompt template for business explanation"""
        return """
Você é um consultor de business intelligence especializado em comunicação executiva para o mercado brasileiro.

CONSULTA SQL:
{sql_query}

RESULTADOS DA CONSULTA:
- Número de registros: {query_results[row_count]}
- Tempo de execução: {query_results[execution_time]} segundos
- Colunas: {query_results[columns]}
- Amostra de dados: {query_results[sample_data]}

ANÁLISE DE IMPACTO EMPRESARIAL:
{business_impact}

AVALIAÇÃO DE QUALIDADE DOS DADOS:
{data_quality_assessment}

NÍVEL DE CONFIANÇA:
{confidence_level}

CONTEXTO EXECUTIVO:
- Áreas de foco: {executive_context[focus_areas]}
- Estilo de comunicação: {executive_context[communication_style]}
- Idioma: {executive_context[language]}

INSTRUÇÕES:
1. Explique o propósito empresarial da consulta em linguagem executiva
2. Identifique as fontes de dados utilizadas
3. Analise o impacto empresarial dos resultados
4. Avalie a confiança nos dados e resultados
5. Forneça notas sobre qualidade dos dados

RESPOSTA EM JSON:
{{
    "business_purpose": "propósito empresarial da consulta em português executivo",
    "data_sources": ["fonte 1", "fonte 2"],
    "business_impact": "análise do impacto empresarial dos resultados",
    "confidence_assessment": "avaliação da confiança nos resultados",
    "data_quality_notes": ["nota 1 sobre qualidade", "nota 2 sobre qualidade"]
}}
"""
    
    async def _get_similar_query_examples(self, natural_query: str) -> List[Dict[str, Any]]:
        """Get similar query examples for LLM context"""
        # Simple keyword matching for now
        query_lower = natural_query.lower()
        similar_examples = []
        
        for example in self.query_examples:
            example_lower = example['business_question'].lower()
            
            # Check for common keywords
            common_keywords = ['fornecedor', 'produto', 'imposto', 'valor', 'total', 'maior', 'menor']
            matches = sum(1 for keyword in common_keywords if keyword in query_lower and keyword in example_lower)
            
            if matches > 0:
                similar_examples.append({
                    'question': example['business_question'],
                    'sql': example['sql_query'],
                    'explanation': example['explanation'],
                    'relevance_score': matches / len(common_keywords)
                })
        
        # Sort by relevance and return top 3
        similar_examples.sort(key=lambda x: x['relevance_score'], reverse=True)
        return similar_examples[:3]
    
    def _get_table_descriptions(self) -> Dict[str, str]:
        """Get table descriptions for LLM context"""
        return {
            table: info.get('description', f'Tabela {table}')
            for table, info in self.table_schema.items()
        }
    
    async def _parse_sql_translation_response(self, response: LLMResponse, original_query: str) -> SQLTranslation:
        """Parse LLM response for SQL translation"""
        try:
            # Try to parse JSON response
            response_data = json.loads(response.content)
            
            return SQLTranslation(
                sql_query=response_data.get('sql_query', ''),
                business_logic_explanation=response_data.get('business_logic_explanation', ''),
                confidence_score=response_data.get('confidence_score', response.confidence_score),
                optimization_suggestions=response_data.get('optimization_suggestions', []),
                potential_issues=response_data.get('potential_issues', []),
                estimated_performance=response_data.get('estimated_performance', {})
            )
            
        except json.JSONDecodeError:
            # Fallback to parsing raw response
            self.logger.warning("Failed to parse JSON response, using raw content")
            return SQLTranslation(
                sql_query=self._extract_sql_from_text(response.content),
                business_logic_explanation=response.content,
                confidence_score=response.confidence_score * 0.7,  # Lower confidence for unparsed response
                optimization_suggestions=["Revisar consulta manualmente"],
                potential_issues=["Resposta não estruturada do LLM"]
            )
    
    async def _parse_optimization_response(self, response: LLMResponse, original_query: str) -> OptimizedQuery:
        """Parse LLM response for query optimization"""
        try:
            response_data = json.loads(response.content)
            
            return OptimizedQuery(
                original_query=original_query,
                optimized_query=response_data.get('optimized_query', original_query),
                optimization_reasoning=response_data.get('optimization_reasoning', ''),
                performance_improvement=response_data.get('performance_improvement', {}),
                business_alignment=response_data.get('business_alignment', '')
            )
            
        except json.JSONDecodeError:
            return OptimizedQuery(
                original_query=original_query,
                optimized_query=original_query,
                optimization_reasoning="Falha ao processar otimização do LLM",
                performance_improvement={'status': 'no_improvement'},
                business_alignment="Não foi possível avaliar alinhamento empresarial"
            )
    
    async def _parse_explanation_response(self, response: LLMResponse, sql_query: str, results: QueryResult) -> QueryExplanation:
        """Parse LLM response for business explanation"""
        try:
            response_data = json.loads(response.content)
            
            return QueryExplanation(
                sql_query=sql_query,
                business_purpose=response_data.get('business_purpose', ''),
                data_sources=response_data.get('data_sources', []),
                business_impact=response_data.get('business_impact', ''),
                confidence_assessment=response_data.get('confidence_assessment', ''),
                data_quality_notes=response_data.get('data_quality_notes', [])
            )
            
        except json.JSONDecodeError:
            return QueryExplanation(
                sql_query=sql_query,
                business_purpose="Análise de dados fiscais para tomada de decisão executiva",
                data_sources=self._extract_table_names(sql_query),
                business_impact="Impacto não determinado devido a erro na análise",
                confidence_assessment="Confiança limitada devido a erro no processamento",
                data_quality_notes=["Erro ao processar explicação do LLM"]
            )
    
    def _extract_sql_from_text(self, text: str) -> str:
        """Extract SQL query from text response"""
        # Look for SQL patterns in the text
        sql_patterns = [
            r'```sql\s*(.*?)\s*```',
            r'```\s*(SELECT.*?)\s*```',
            r'(SELECT.*?;)',
            r'(SELECT.*?)(?=\n\n|\Z)'
        ]
        
        for pattern in sql_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, return the whole text (might be just SQL)
        return text.strip()
    
    def _extract_table_names(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        # Simple regex to find table names after FROM and JOIN
        table_pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(table_pattern, sql_query, re.IGNORECASE)
        return list(set(matches))
    
    async def _get_performance_requirements(self) -> Dict[str, Any]:
        """Get performance requirements for optimization"""
        return {
            'max_execution_time': '30 seconds',
            'target_response_time': '< 5 seconds',
            'concurrent_users': 10,
            'data_freshness': 'real-time for current month'
        }
    
    async def _get_data_volume_estimates(self) -> Dict[str, Any]:
        """Get data volume estimates"""
        return {
            'nfe_main': '~1M records per year',
            'nfse_main': '~500K records per year',
            'fact_itens_nfe': '~10M records per year',
            'fact_servicos_nfse': '~2M records per year'
        }
    
    async def _get_index_information(self) -> Dict[str, Any]:
        """Get database index information"""
        return {
            'nfe_main': ['data_emissao', 'chave_nfe', 'valor_total_nf'],
            'nfse_main': ['data_emissao', 'id_nfse', 'valor_total_servicos'],
            'dim_emitente': ['cnpj', 'razao_social'],
            'dim_produtos': ['codigo_produto', 'categoria'],
            'dim_servicos': ['codigo_servico', 'categoria']
        }
    
    async def _get_optimization_patterns(self) -> List[str]:
        """Get common optimization patterns"""
        return [
            'Use date range filters to limit data scan',
            'Prefer aggregated views for summary queries',
            'Use LIMIT for top-N queries',
            'Consider partitioning for large date ranges',
            'Use appropriate JOINs based on cardinality'
        ]
    
    async def _analyze_business_impact(self, results: QueryResult) -> str:
        """Analyze business impact of query results"""
        if results.row_count == 0:
            return "Nenhum dado encontrado - pode indicar filtros muito restritivos ou ausência de dados no período"
        elif results.row_count > 10000:
            return "Grande volume de dados - considere agregação para análise executiva"
        else:
            return f"Volume adequado de dados ({results.row_count} registros) para análise detalhada"
    
    async def _assess_data_quality(self, results: QueryResult) -> List[str]:
        """Assess data quality from results"""
        quality_notes = []
        
        if results.execution_time > 10:
            quality_notes.append("Consulta demorada - pode indicar necessidade de otimização")
        
        if results.row_count == 0:
            quality_notes.append("Nenhum resultado - verificar filtros e disponibilidade de dados")
        
        # Check for null values in sample data
        if results.data:
            sample = results.data[0]
            null_columns = [col for col, val in sample.items() if val is None]
            if null_columns:
                quality_notes.append(f"Valores nulos encontrados em: {', '.join(null_columns)}")
        
        if not quality_notes:
            quality_notes.append("Qualidade dos dados aparenta estar adequada")
        
        return quality_notes
    
    async def _calculate_confidence_level(self, results: QueryResult) -> str:
        """Calculate confidence level in results"""
        if results.row_count == 0:
            return "Baixa confiança - nenhum dado encontrado"
        elif results.execution_time > 30:
            return "Confiança moderada - consulta muito lenta pode indicar problemas"
        elif results.row_count > 0 and results.execution_time < 5:
            return "Alta confiança - dados encontrados com boa performance"
        else:
            return "Confiança moderada - resultados adequados"

# Compatibility alias for existing code
SQLAgent = LLMEnhancedSQLAgent