"""
OpenAI Integration Service for LLM-powered AI Agents
Provides centralized access to OpenAI API with intelligent prompt management
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib

try:
    import openai
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import structlog
from .config import settings

logger = structlog.get_logger(__name__)

class LLMModel(Enum):
    """Available LLM models"""
    GPT_4_mini = "gpt-4o-mini"
    GPT_4 = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

@dataclass
class LLMResponse:
    """Response from LLM with metadata"""
    content: str
    model_used: str
    tokens_used: int
    confidence_score: float
    processing_time: float
    context_id: str
    cached: bool = False

@dataclass
class DocumentAnalysis:
    """Document analysis result"""
    document_type: str
    business_context: Dict[str, Any]
    key_insights: List[str]
    anomalies_detected: List[str]
    confidence_score: float
    processing_notes: List[str]

@dataclass
class BusinessInsights:
    """Business insights from data analysis"""
    key_findings: List[str]
    trends_identified: List[str]
    business_impact: Dict[str, Any]
    strategic_implications: List[str]
    confidence_level: float
    supporting_data: Dict[str, Any]

@dataclass
class CategorizationResult:
    """Result of LLM-powered categorization"""
    categories: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    reasoning: List[str]
    suggested_improvements: List[str]

class PromptManager:
    """Manages prompt templates for different agent types"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load prompt templates for different use cases"""
        return {
            "query_interpretation": """
Você é um assistente de IA especializado em análise de documentos fiscais brasileiros para executivos C-level.

Analise a consulta do usuário e forneça uma interpretação estruturada incluindo:

1. **Intenção Principal**: Identifique o objetivo empresarial (consulta_dados, gerar_relatorio, agendar_tarefa, analisar_tendencias, etc.)
2. **Objetivo Empresarial**: Descreva o que o usuário quer alcançar em termos de negócio
3. **Entidades Extraídas**: Identifique períodos, fornecedores, produtos, valores, etc.
4. **Requisitos de Dados**: Liste que dados são necessários para atender a consulta
5. **Nível de Confiança**: Avalie sua confiança na interpretação (0.0 a 1.0)
6. **Necessidade de Esclarecimento**: Determine se precisa de mais informações
7. **Esclarecimentos Sugeridos**: Liste perguntas para esclarecer ambiguidades
8. **Consulta Normalizada**: Reformule a consulta de forma clara e estruturada
9. **Parâmetros**: Extraia parâmetros específicos (formato, período, filtros, etc.)

Contexto disponível:
- Consulta: {query}
- Cargo do usuário: {user_role}
- Histórico de conversa: {conversation_history}
- Dados disponíveis: {available_data}
- Contexto empresarial: {business_context}
- Capacidades do sistema: {system_capabilities}

Responda em formato JSON válido com as chaves:
- intent
- business_objective  
- entities (lista de objetos com type, value, confidence)
- data_requirements (lista de strings)
- confidence_level (float)
- clarification_needed (boolean)
- suggested_clarifications (lista de strings)
- normalized_query (string)
- parameters (objeto com chaves específicas)

Use linguagem empresarial clara em português brasileiro.
""",
            "business_to_sql_translation": """
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
""",
            
            "query_optimization": """
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
""",
            
            "business_explanation": """
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
""",
            
            "product_categorization": """
Você é um especialista em categorização de produtos fiscais brasileiros com profundo conhecimento de NCM, CFOP e contexto empresarial.

Produto para Análise:
- Descrição: {description}
- Código NCM: {ncm}
- CFOP: {cfop}
- Unidade: {unit}
- Fornecedor: {supplier_info}
- Contexto de Uso: {usage_context}
- Categoria de Mercado: {market_category}

Contexto Empresarial:
- Setor: {business_sector}
- Categorias Existentes: {existing_categories}
- Regras de Categorização: {categorization_rules}

Forneça uma categorização inteligente incluindo:
1. Categoria principal baseada no contexto empresarial
2. Subcategoria específica
3. Justificativa da categorização
4. Nível de confiança (0-1)
5. Sugestões de melhoria se aplicável

Responda em formato JSON estruturado em português brasileiro.
""",
            
            "supplier_relationship_analysis": """
Você é um analista de relacionamentos comerciais especializado no mercado brasileiro.

Fornecedor para Análise:
- Razão Social: {supplier_name}
- CNPJ: {cnpj}
- Histórico de Transações: {transaction_history}
- Posição de Mercado: {market_position}
- Fatores de Risco: {risk_factors}
- Importância Estratégica: {strategic_importance}

Forneça análise completa incluindo:
1. Classificação do relacionamento (Estratégico/Importante/Regular/Eventual)
2. Avaliação de risco (Alto/Médio/Baixo)
3. Potencial de crescimento
4. Recomendações de relacionamento
5. Oportunidades de otimização
6. Nível de confiança da análise

Responda em formato JSON estruturado focando em insights executivos.
""",
            
            "business_pattern_detection": """
Você é um especialista em análise de padrões empresariais e tendências de mercado brasileiro.

Dados para Análise:
- Documentos Fiscais: {documents_summary}
- Dados de Série Temporal: {time_series_data}
- Tendências de Mercado: {market_trends}
- Padrões Sazonais: {seasonal_patterns}
- Ciclos Empresariais: {business_cycles}

Detecte e analise padrões incluindo:
1. Padrões de comportamento de fornecedores
2. Tendências sazonais e cíclicas
3. Anomalias significativas
4. Oportunidades de otimização
5. Riscos identificados
6. Impacto estratégico dos padrões
7. Recomendações acionáveis

Foque em insights de alto nível para tomada de decisão executiva.
Responda em formato JSON estruturado em português brasileiro.
""",
            
            "error_analysis": """
Você é um especialista em análise de erros de sistemas e diagnóstico técnico para sistemas de análise fiscal brasileiros.

DETALHES DO ERRO:
- Tipo de Erro: {error_details[error_type]}
- Mensagem: {error_details[error_message]}
- Stack Trace: {error_details[stack_trace]}
- Agente: {error_details[agent_name]}
- Operação: {error_details[operation]}
- Timestamp: {error_details[timestamp]}

CONTEXTO DO SISTEMA:
- Dados de Entrada: {system_context[input_data]}
- Estado do Sistema: {system_context[system_state]}
- Contexto Empresarial: {system_context[business_context]}

CONTEXTO HISTÓRICO:
- Erros Similares: {historical_context[similar_errors_count]}
- Taxa de Erro Recente: {historical_context[recent_error_rate]}
- Padrões Conhecidos: {historical_context[error_patterns]}

CAPACIDADES DO SISTEMA:
- Agentes Disponíveis: {system_capabilities[available_agents]}
- Mecanismos de Recuperação: {system_capabilities[recovery_mechanisms]}
- Ferramentas de Monitoramento: {system_capabilities[monitoring_tools]}

Forneça análise completa incluindo:
1. Categoria do erro (system, database, xml_processing, agent_communication, api, authentication, validation, business_logic, external_service, llm_service)
2. Severidade (low, medium, high, critical)
3. Causa raiz identificada
4. Impacto no negócio
5. Diagnóstico técnico detalhado
6. Sugestões de recuperação (lista de ações específicas)
7. Recomendações de prevenção
8. Mensagem amigável para usuário final
9. Mensagem de alerta para administrador
10. Nível de confiança da análise (0-1)
11. Se requer escalação (true/false)

RESPOSTA EM JSON:
{{
    "category": "categoria_do_erro",
    "severity": "nivel_severidade",
    "root_cause": "causa raiz identificada em português",
    "business_impact": "impacto no negócio em português",
    "technical_diagnosis": "diagnóstico técnico detalhado",
    "recovery_suggestions": ["sugestão 1", "sugestão 2", "sugestão 3"],
    "prevention_recommendations": ["recomendação 1", "recomendação 2"],
    "user_friendly_message": "mensagem amigável para usuário final",
    "admin_alert_message": "mensagem de alerta para administrador",
    "confidence_score": 0.85,
    "escalation_required": false
}}
""",
            
            "recovery_plan_generation": """
Você é um especialista em recuperação de sistemas e automação de TI para sistemas fiscais brasileiros.

ANÁLISE DO ERRO:
- Categoria: {error_analysis[category]}
- Severidade: {error_analysis[severity]}
- Causa Raiz: {error_analysis[root_cause]}
- Diagnóstico Técnico: {error_analysis[technical_diagnosis]}
- Sugestões de Recuperação: {error_analysis[recovery_suggestions]}

CAPACIDADES DO SISTEMA:
{system_capabilities}

ESTADO ATUAL DO SISTEMA:
{current_system_state}

RESTRIÇÕES EMPRESARIAIS:
{business_constraints}

Crie um plano de recuperação detalhado incluindo:
1. Passos automatizados que o sistema pode executar
2. Passos manuais que requerem intervenção humana
3. Tempo estimado de recuperação
4. Probabilidade de sucesso
5. Critérios de validação da recuperação
6. Plano de rollback se necessário
7. Se requer escalação

RESPOSTA EM JSON:
{{
    "automated_steps": [
        "passo automatizado 1",
        "passo automatizado 2"
    ],
    "manual_steps": [
        "passo manual 1",
        "passo manual 2"
    ],
    "estimated_recovery_time": "tempo estimado",
    "success_probability": 0.85,
    "validation_criteria": [
        "critério 1",
        "critério 2"
    ],
    "rollback_plan": [
        "passo rollback 1",
        "passo rollback 2"
    ],
    "escalation_required": false
}}
""",
            
            "admin_alert_generation": """
Você é um especialista em comunicação técnica e alertas de sistema para administradores de TI.

ANÁLISE DO ERRO:
- ID do Erro: {error_analysis[error_id]}
- Categoria: {error_analysis[category]}
- Severidade: {error_analysis[severity]}
- Causa Raiz: {error_analysis[root_cause]}
- Impacto no Negócio: {error_analysis[business_impact]}
- Diagnóstico Técnico: {error_analysis[technical_diagnosis]}
- Requer Escalação: {error_analysis[escalation_required]}

CONTEXTO DO SISTEMA:
{system_context}

INFORMAÇÕES ADICIONAIS:
- Erros Similares: {similar_errors_count}
- Urgência do Alerta: {alert_urgency}

Crie um alerta contextual e acionável para administradores incluindo:
1. Título claro e informativo
2. Mensagem principal com contexto
3. Detalhes técnicos relevantes
4. Ações recomendadas específicas
5. Impacto no negócio
6. Prioridade de resposta

RESPOSTA EM JSON:
{{
    "title": "título claro do alerta",
    "message": "mensagem principal com contexto completo",
    "technical_details": "detalhes técnicos relevantes para diagnóstico",
    "recommended_actions": [
        "ação específica 1",
        "ação específica 2",
        "ação específica 3"
    ],
    "business_impact": "descrição do impacto no negócio",
    "response_priority": "immediate|high|medium|low"
}}
""",
            
            "error_pattern_analysis": """
Você é um especialista em análise de padrões de erro e monitoramento preditivo de sistemas.

GRUPO DE PADRÃO:
- Identificador: {pattern_group}
- Quantidade de Erros: {error_count}
- Período: {time_span} horas

DETALHES DOS ERROS:
{error_details}

Analise este padrão de erros e forneça:
1. Tipo de padrão identificado
2. Descrição do padrão
3. Severidade do padrão
4. Impacto previsto se não tratado
5. Recomendações de prevenção
6. Nível de confiança da análise

RESPOSTA EM JSON:
{{
    "pattern_type": "tipo do padrão (recurring_error, escalating_issue, cascade_failure, etc.)",
    "description": "descrição clara do padrão identificado",
    "severity": "low|medium|high|critical",
    "predicted_impact": "impacto previsto se o padrão continuar",
    "prevention_recommendations": [
        "recomendação 1",
        "recomendação 2",
        "recomendação 3"
    ],
    "confidence_score": 0.85
}}
""",
            
            "system_pattern_analysis": """
Você é um especialista em análise de padrões de sistema e monitoramento inteligente para sistemas fiscais brasileiros.

MÉTRICAS ATUAIS:
{current_metrics}

TENDÊNCIAS HISTÓRICAS:
{historical_trends}

HISTÓRICO DE ALERTAS:
{alert_history}

COMPONENTES DO SISTEMA:
{system_components}

CONTEXTO EMPRESARIAL:
- Horários de Pico: {business_context[peak_hours]}
- Operações Críticas: {business_context[critical_operations]}
- Padrões Sazonais: {business_context[seasonal_patterns]}

Analise os padrões do sistema e identifique:
1. Padrões de comportamento normais vs anômalos
2. Tendências preocupantes que podem indicar problemas futuros
3. Correlações entre métricas e alertas
4. Anomalias que requerem atenção imediata
5. Recomendações para otimização preventiva

RESPOSTA EM JSON:
{{
    "patterns": [
        {{
            "type": "tipo do padrão",
            "description": "descrição do padrão",
            "severity": "low|medium|high",
            "components_affected": ["componente1", "componente2"],
            "business_impact": "impacto no negócio"
        }}
    ],
    "anomalies_detected": [
        {{
            "type": "tipo da anomalia",
            "description": "descrição da anomalia",
            "confidence": 0.85,
            "predicted_impact": "impacto previsto",
            "recommended_actions": ["ação 1", "ação 2"]
        }}
    ],
    "optimization_opportunities": [
        "oportunidade 1",
        "oportunidade 2"
    ],
    "confidence_score": 0.85
}}
""",
            
            "predictive_issue_detection": """
Você é um especialista em detecção preditiva de problemas e análise de risco para sistemas empresariais.

ESTADO ATUAL DO SISTEMA:
{current_system_state}

PADRÕES DE ERRO RECENTES:
{recent_error_patterns}

TENDÊNCIAS DE PERFORMANCE:
{performance_trends}

UTILIZAÇÃO DE RECURSOS:
{resource_utilization}

CALENDÁRIO EMPRESARIAL:
{business_calendar}

INCIDENTES HISTÓRICOS:
{historical_incidents}

Com base nos dados fornecidos, prediga possíveis problemas futuros incluindo:
1. Problemas de alta probabilidade nas próximas 24-48 horas
2. Riscos de médio prazo (próxima semana)
3. Tendências preocupantes de longo prazo
4. Ações preventivas recomendadas
5. Impacto empresarial estimado

RESPOSTA EM JSON:
{{
    "predictions": [
        {{
            "issue_type": "tipo do problema",
            "description": "descrição do problema previsto",
            "probability": 0.75,
            "estimated_time_to_occurrence": "24-48 horas",
            "affected_components": ["componente1", "componente2"],
            "business_impact": "impacto no negócio",
            "preventive_actions": ["ação preventiva 1", "ação preventiva 2"]
        }}
    ],
    "high_risk_issues": [
        {{
            "issue_description": "descrição do problema de alto risco",
            "probability": 0.85,
            "eta": "próximas 12 horas",
            "business_impact": "crítico",
            "preventive_actions": ["ação urgente 1", "ação urgente 2"]
        }}
    ],
    "medium_term_risks": [
        "risco de médio prazo 1",
        "risco de médio prazo 2"
    ],
    "confidence_score": 0.80
}}
""",
            
            "performance_optimization": """
Você é um especialista em otimização de performance de sistemas empresariais e infraestrutura.

GARGALOS DE PERFORMANCE:
{performance_bottlenecks}

MÉTRICAS DO SISTEMA:
{system_metrics}

RESTRIÇÕES DE RECURSOS:
{resource_constraints}

PADRÕES DE CARGA DE TRABALHO:
{workload_patterns}

CAPACIDADE DA INFRAESTRUTURA:
{infrastructure_capacity}

REQUISITOS EMPRESARIAIS:
- Metas de SLA: {business_requirements[sla_targets]}
- Tratamento de Pico: {business_requirements[peak_load_handling]}
- Otimização de Custo: {business_requirements[cost_optimization]}

Forneça recomendações de otimização incluindo:
1. Otimizações de curto prazo (implementação imediata)
2. Melhorias de médio prazo (próximas semanas)
3. Investimentos de longo prazo (próximos meses)
4. Estimativa de impacto para cada recomendação
5. Priorização baseada em ROI e facilidade de implementação

RESPOSTA EM JSON:
{{
    "immediate_optimizations": [
        {{
            "optimization": "descrição da otimização",
            "impact": "high|medium|low",
            "effort": "low|medium|high",
            "estimated_improvement": "melhoria estimada",
            "implementation_steps": ["passo 1", "passo 2"]
        }}
    ],
    "medium_term_improvements": [
        {{
            "improvement": "descrição da melhoria",
            "impact": "high|medium|low",
            "effort": "low|medium|high",
            "timeline": "2-4 semanas",
            "resource_requirements": ["recurso 1", "recurso 2"]
        }}
    ],
    "long_term_investments": [
        {{
            "investment": "descrição do investimento",
            "impact": "high|medium|low",
            "cost_estimate": "estimativa de custo",
            "timeline": "2-6 meses",
            "business_justification": "justificativa empresarial"
        }}
    ],
    "priority_ranking": [
        "item prioritário 1",
        "item prioritário 2",
        "item prioritário 3"
    ],
    "confidence_score": 0.85
}}
""",
            
            "fiscal_data_quality_analysis": """
Você é um especialista em qualidade de dados fiscais brasileiros e análise de padrões empresariais.

MÉTRICAS DE DADOS FISCAIS:
{fiscal_data_metrics}

INDICADORES DE QUALIDADE:
- Erros de Validação XML: {data_quality_indicators[xml_validation_errors]}
- Taxa de Campos Faltantes: {data_quality_indicators[missing_fields_rate]}%
- Documentos Duplicados: {data_quality_indicators[duplicate_documents]}
- Variância no Tempo de Processamento: {data_quality_indicators[processing_time_variance]}%

CONTEXTO EMPRESARIAL:
- Tipos de Documento: {business_context[document_types]}
- Volumes Típicos: {business_context[typical_volumes]}
- Padrões Sazonais: {business_context[seasonal_patterns]}
- Padrões de Fornecedores: {business_context[supplier_patterns]}

BASELINES HISTÓRICAS:
{historical_baselines}

Analise a qualidade dos dados fiscais e determine:
1. Se os padrões indicam problemas de qualidade de dados ou mudanças empresariais legítimas
2. Problemas críticos de qualidade que requerem ação imediata
3. Tendências empresariais identificadas nos dados
4. Recomendações para melhoria da qualidade
5. Impacto no negócio dos problemas identificados

RESPOSTA EM JSON:
{{
    "data_quality_assessment": {{
        "overall_score": 85,
        "quality_trend": "improving|stable|declining",
        "critical_issues_count": 2
    }},
    "data_quality_issues": [
        {{
            "type": "validation_errors",
            "description": "descrição do problema",
            "severity": "high|medium|low",
            "affected_count": 150,
            "business_impact": "impacto no negócio",
            "recommended_actions": ["ação 1", "ação 2"]
        }}
    ],
    "business_changes": [
        {{
            "change_type": "tipo de mudança empresarial",
            "description": "descrição da mudança",
            "confidence": 0.85,
            "supporting_evidence": ["evidência 1", "evidência 2"]
        }}
    ],
    "improvement_recommendations": [
        "recomendação de melhoria 1",
        "recomendação de melhoria 2"
    ],
    "confidence_score": 0.80
}}
""",
            
            "maintenance_recommendations": """
Você é um especialista em manutenção de sistemas e planejamento de infraestrutura para ambientes empresariais.

SAÚDE DO SISTEMA:
- Status Geral: {system_health[overall_status]}
- Saúde dos Componentes: {system_health[component_health]}
- Métricas de Performance: {system_health[performance_metrics]}

HISTÓRICO DE MANUTENÇÃO:
{maintenance_history}

EVENTOS EMPRESARIAIS FUTUROS:
{upcoming_business_events}

TENDÊNCIAS DE UTILIZAÇÃO:
{resource_utilization_trends}

DÍVIDA TÉCNICA CONHECIDA:
{known_technical_debt}

RESTRIÇÕES EMPRESARIAIS:
- Janelas de Manutenção: {business_constraints[maintenance_windows]}
- Períodos Críticos: {business_constraints[critical_business_periods]}
- Requisitos de SLA: {business_constraints[sla_requirements]}

Gere recomendações de manutenção incluindo:
1. Manutenção urgente necessária
2. Manutenção preventiva recomendada
3. Atualizações e melhorias planejadas
4. Avaliação de impacto para cada item
5. Cronograma otimizado considerando restrições empresariais

RESPOSTA EM JSON:
{{
    "urgent_maintenance": [
        {{
            "item": "descrição do item urgente",
            "urgency": "critical|high|medium",
            "estimated_downtime": "2 horas",
            "business_impact": "impacto no negócio",
            "recommended_window": "próxima janela disponível"
        }}
    ],
    "preventive_maintenance": [
        {{
            "item": "descrição da manutenção preventiva",
            "frequency": "mensal|trimestral|semestral",
            "estimated_effort": "4 horas",
            "benefits": ["benefício 1", "benefício 2"],
            "next_due_date": "2024-12-15"
        }}
    ],
    "planned_improvements": [
        {{
            "improvement": "descrição da melhoria",
            "priority": "high|medium|low",
            "estimated_timeline": "2-4 semanas",
            "resource_requirements": ["recurso 1", "recurso 2"],
            "business_value": "valor empresarial"
        }}
    ],
    "recommended_schedule": [
        {{
            "date": "2024-11-30",
            "maintenance_window": "02:00-04:00 BRT",
            "items": ["item 1", "item 2"],
            "total_downtime": "1.5 horas"
        }}
    ],
    "confidence_score": 0.85
}}
"""
        }
    
    def get_template(self, template_name: str) -> str:
        """Get prompt template by name"""
        return self.templates.get(template_name, "")
    
    def format_prompt(self, template_name: str, context: Dict[str, Any]) -> str:
        """Format prompt template with context"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error("Missing context key for prompt template", 
                        template=template_name, missing_key=str(e))
            raise

class ContextManager:
    """Manages conversation context and memory"""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.max_context_age = timedelta(hours=24)
    
    def create_context(self, user_id: str, session_id: str) -> str:
        """Create new conversation context"""
        context_id = f"{user_id}_{session_id}_{int(time.time())}"
        self.contexts[context_id] = {
            'user_id': user_id,
            'session_id': session_id,
            'created_at': datetime.now(),
            'conversation_history': [],
            'business_context': {},
            'learned_patterns': {}
        }
        return context_id
    
    def add_to_context(self, context_id: str, interaction: Dict[str, Any]):
        """Add interaction to context"""
        if context_id in self.contexts:
            self.contexts[context_id]['conversation_history'].append({
                'timestamp': datetime.now(),
                'interaction': interaction
            })
            # Keep only last 20 interactions
            if len(self.contexts[context_id]['conversation_history']) > 20:
                self.contexts[context_id]['conversation_history'] = \
                    self.contexts[context_id]['conversation_history'][-20:]
    
    def get_context(self, context_id: str) -> Dict[str, Any]:
        """Get context by ID"""
        return self.contexts.get(context_id, {})
    
    def cleanup_old_contexts(self):
        """Remove old contexts"""
        cutoff = datetime.now() - self.max_context_age
        to_remove = [
            ctx_id for ctx_id, ctx in self.contexts.items()
            if ctx.get('created_at', datetime.min) < cutoff
        ]
        for ctx_id in to_remove:
            del self.contexts[ctx_id]

class TokenManager:
    """Manages token usage and rate limiting"""
    
    def __init__(self):
        self.usage_history: List[Dict[str, Any]] = []
        self.rate_limits = {
            'requests_per_minute': settings.openai_rate_limit_rpm,
            'tokens_per_minute': settings.openai_rate_limit_tpm
        }
        self.current_usage = {'requests': 0, 'tokens': 0}
        self.last_reset = time.time()
    
    def can_make_request(self, estimated_tokens: int) -> bool:
        """Check if request can be made within rate limits"""
        self._reset_if_needed()
        
        return (self.current_usage['requests'] < self.rate_limits['requests_per_minute'] and
                self.current_usage['tokens'] + estimated_tokens < self.rate_limits['tokens_per_minute'])
    
    def record_usage(self, tokens_used: int):
        """Record token usage"""
        self.current_usage['requests'] += 1
        self.current_usage['tokens'] += tokens_used
        
        self.usage_history.append({
            'timestamp': datetime.now(),
            'tokens': tokens_used,
            'requests': 1
        })
        
        # Keep only last 1000 entries
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
    
    def _reset_if_needed(self):
        """Reset counters if minute has passed"""
        if time.time() - self.last_reset >= 60:
            self.current_usage = {'requests': 0, 'tokens': 0}
            self.last_reset = time.time()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        recent_usage = [
            entry for entry in self.usage_history
            if entry['timestamp'] > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'current_minute': self.current_usage,
            'last_24h_requests': len(recent_usage),
            'last_24h_tokens': sum(entry['tokens'] for entry in recent_usage),
            'rate_limits': self.rate_limits
        }

class ResponseCache:
    """Caches LLM responses to reduce API calls"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_cache_size = 1000
        self.cache_ttl = settings.openai_cache_ttl
    
    def _generate_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate cache key"""
        content = f"{prompt}_{model}_{temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, temperature: float) -> Optional[str]:
        """Get cached response"""
        if not settings.openai_enable_caching:
            return None
        
        key = self._generate_key(prompt, model, temperature)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.cache_ttl:
                return entry['response']
            else:
                del self.cache[key]
        return None
    
    def set(self, prompt: str, model: str, temperature: float, response: str):
        """Cache response"""
        if not settings.openai_enable_caching:
            return
        
        key = self._generate_key(prompt, model, temperature)
        
        # Remove oldest entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }

class OpenAIIntegrationService:
    """Central service for OpenAI API integration"""
    
    def __init__(self):
        if not HAS_OPENAI:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.prompt_manager = PromptManager()
        self.context_manager = ContextManager()
        self.token_manager = TokenManager()
        self.cache = ResponseCache()
        
        logger.info("OpenAI Integration Service initialized")
    
    async def generate_completion(
        self,
        prompt_template: str,
        context: Dict[str, Any],
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> LLMResponse:
        """Generate LLM completion with context and error handling"""
        
        model = model or settings.openai_default_model
        max_tokens = max_tokens or settings.openai_max_tokens
        temperature = temperature if temperature is not None else settings.openai_temperature
        
        # Format prompt
        formatted_prompt = self.prompt_manager.format_prompt(prompt_template, context)
        
        # Check cache first
        cached_response = self.cache.get(formatted_prompt, model, temperature)
        if cached_response:
            return LLMResponse(
                content=cached_response,
                model_used=model,
                tokens_used=0,  # Cached responses don't use tokens
                confidence_score=0.9,  # High confidence for cached responses
                processing_time=0.0,
                context_id=context.get('context_id', ''),
                cached=True
            )
        
        # Estimate tokens for rate limiting
        estimated_tokens = len(formatted_prompt.split()) * 1.3  # Rough estimation
        
        if not self.token_manager.can_make_request(int(estimated_tokens)):
            raise Exception("Rate limit exceeded. Please try again later.")
        
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em análise fiscal brasileira."},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=settings.openai_timeout
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            
            # Record usage
            self.token_manager.record_usage(tokens_used)
            
            # Cache response
            content = response.choices[0].message.content
            self.cache.set(formatted_prompt, model, temperature, content)
            
            # Calculate confidence score based on response quality
            confidence_score = self._calculate_confidence_score(content, response)
            
            return LLMResponse(
                content=content,
                model_used=model,
                tokens_used=tokens_used,
                confidence_score=confidence_score,
                processing_time=processing_time,
                context_id=context.get('context_id', ''),
                cached=False
            )
            
        except Exception as e:
            logger.error("Error generating completion", error=str(e), model=model)
            
            # Try fallback model if primary fails
            if model != settings.openai_fallback_model:
                logger.info("Trying fallback model", fallback_model=settings.openai_fallback_model)
                return await self.generate_completion(
                    prompt_template, context, 
                    model=settings.openai_fallback_model,
                    max_tokens=max_tokens, temperature=temperature
                )
            
            raise
    
    async def analyze_document(
        self,
        document_content: str,
        analysis_type: str,
        context: Dict[str, Any] = None
    ) -> DocumentAnalysis:
        """Analyze documents using specialized prompts"""
        
        context = context or {}
        context.update({
            'document_content': document_content,
            'analysis_type': analysis_type
        })
        
        # Use appropriate template based on analysis type
        template_map = {
            'semantic_analysis': 'product_categorization',
            'fiscal_document': 'business_pattern_detection'
        }
        
        template = template_map.get(analysis_type, 'product_categorization')
        
        response = await self.generate_completion(template, context)
        
        try:
            # Parse JSON response
            analysis_data = json.loads(response.content)
            
            return DocumentAnalysis(
                document_type=analysis_data.get('document_type', 'unknown'),
                business_context=analysis_data.get('business_context', {}),
                key_insights=analysis_data.get('key_insights', []),
                anomalies_detected=analysis_data.get('anomalies_detected', []),
                confidence_score=analysis_data.get('confidence_score', response.confidence_score),
                processing_notes=analysis_data.get('processing_notes', [])
            )
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, using raw content")
            return DocumentAnalysis(
                document_type=analysis_type,
                business_context={},
                key_insights=[response.content],
                anomalies_detected=[],
                confidence_score=response.confidence_score,
                processing_notes=["Raw response due to JSON parse error"]
            )
    
    async def generate_insights(
        self,
        data: Dict[str, Any],
        insight_type: str,
        audience: str = "executive"
    ) -> BusinessInsights:
        """Generate business insights from data"""
        
        context = {
            'data': data,
            'insight_type': insight_type,
            'audience': audience
        }
        
        response = await self.generate_completion('business_pattern_detection', context)
        
        try:
            insights_data = json.loads(response.content)
            
            return BusinessInsights(
                key_findings=insights_data.get('key_findings', []),
                trends_identified=insights_data.get('trends_identified', []),
                business_impact=insights_data.get('business_impact', {}),
                strategic_implications=insights_data.get('strategic_implications', []),
                confidence_level=insights_data.get('confidence_level', response.confidence_score),
                supporting_data=insights_data.get('supporting_data', {})
            )
            
        except json.JSONDecodeError:
            return BusinessInsights(
                key_findings=[response.content],
                trends_identified=[],
                business_impact={},
                strategic_implications=[],
                confidence_level=response.confidence_score,
                supporting_data={}
            )
    
    async def categorize_with_context(
        self,
        items: List[str],
        category_type: str,
        business_context: Dict[str, Any]
    ) -> CategorizationResult:
        """Intelligent categorization with business understanding"""
        
        context = {
            'items': items,
            'category_type': category_type,
            'business_context': business_context
        }
        
        template = 'product_categorization' if category_type == 'product' else 'supplier_relationship_analysis'
        response = await self.generate_completion(template, context)
        
        try:
            categorization_data = json.loads(response.content)
            
            return CategorizationResult(
                categories=categorization_data.get('categories', []),
                confidence_scores=categorization_data.get('confidence_scores', {}),
                reasoning=categorization_data.get('reasoning', []),
                suggested_improvements=categorization_data.get('suggested_improvements', [])
            )
            
        except json.JSONDecodeError:
            return CategorizationResult(
                categories=[{'item': item, 'category': 'Não Classificado'} for item in items],
                confidence_scores={item: 0.5 for item in items},
                reasoning=[response.content],
                suggested_improvements=["Melhorar qualidade dos dados de entrada"]
            )
    
    def _calculate_confidence_score(self, content: str, response) -> float:
        """Calculate confidence score based on response quality"""
        base_score = 0.7
        
        # Adjust based on response length (longer responses often more detailed)
        if len(content) > 500:
            base_score += 0.1
        elif len(content) < 100:
            base_score -= 0.1
        
        # Adjust based on structured content (JSON responses are more reliable)
        try:
            json.loads(content)
            base_score += 0.1
        except json.JSONDecodeError:
            base_score -= 0.05
        
        # Adjust based on finish reason
        if hasattr(response, 'choices') and response.choices:
            finish_reason = response.choices[0].finish_reason
            if finish_reason == 'stop':
                base_score += 0.05
            elif finish_reason == 'length':
                base_score -= 0.1
        
        return max(0.0, min(1.0, base_score))
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        return {
            'token_usage': self.token_manager.get_usage_stats(),
            'cache_stats': {
                'cache_size': len(self.cache.cache),
                'max_cache_size': self.cache.max_cache_size,
                'cache_ttl': self.cache.cache_ttl
            },
            'context_stats': {
                'active_contexts': len(self.context_manager.contexts)
            }
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.context_manager.cleanup_old_contexts()
        logger.info("OpenAI Integration Service cleanup completed")

# Global instance
openai_service = None

def get_openai_service() -> OpenAIIntegrationService:
    """Get global OpenAI service instance"""
    global openai_service
    if openai_service is None:
        openai_service = OpenAIIntegrationService()
    return openai_service

# Compatibility aliases for existing code
async def obter_servico_openai() -> OpenAIIntegrationService:
    """Portuguese alias for get_openai_service (compatibility)"""
    return get_openai_service()

# Type aliases for compatibility
ServicoIntegracaoOpenAI = OpenAIIntegrationService
AnaliseDocumento = DocumentAnalysis
TraducaoSQL = LLMResponse  # Simplified for compatibility
InsightsEmpresariais = BusinessInsights
ResultadoCategorizacao = CategorizationResult

# Enum aliases for compatibility
class TipoPrompt:
    """Compatibility enum for prompt types"""
    INTERPRETACAO_CONSULTA = "master_agent_query_interpretation"
    ANALISE_SEMANTICA = "xml_semantic_analysis"
    CATEGORIZACAO_PRODUTO = "product_categorization"
    ANALISE_FORNECEDOR = "supplier_relationship_analysis"
    DETECCAO_PADRAO = "business_pattern_detection"

class ModeloLLM:
    """Compatibility enum for LLM models"""
    GPT_4 = LLMModel.GPT_4.value
    GPT_4_TURBO = LLMModel.GPT_4_TURBO.value
    GPT_3_5_TURBO = LLMModel.GPT_3_5_TURBO.value