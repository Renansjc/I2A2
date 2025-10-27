"""
Agente de Insights Executivos
Implementa análises estratégicas, consultas em linguagem natural e geração de SQL
"""

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
import re
import sqlite3
from dataclasses import dataclass


@dataclass
class QueryContext:
    """Contexto para consultas em linguagem natural"""
    available_data: Dict[str, Any]
    user_history: List[Dict[str, Any]]
    business_context: Dict[str, Any]


class InsightsAgent:
    """
    Agente especializado em insights executivos e consultas em linguagem natural.
    Processa perguntas em português e gera análises estratégicas acionáveis.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.name = "Insights Agent"
        self.version = "1.0.0"
        self.openai_api_key = openai_api_key
        self.model = model
        
        # Inicializar LLM se API key disponível
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                model=self.model,
                temperature=0.1
            )
        else:
            self.llm = None
        
        # Templates de consultas comuns
        self.query_templates = {
            "valor_total": "SELECT SUM(valor_total) as total FROM documents WHERE status = 'completed'",
            "fornecedores": "SELECT emitente_razao_social, COUNT(*) as docs, SUM(valor_total) as total FROM documents GROUP BY emitente_razao_social",
            "categorias": "SELECT categoria, COUNT(*) as quantidade, SUM(valor_total) as valor FROM items GROUP BY categoria",
            "periodo": "SELECT DATE(data_emissao) as data, SUM(valor_total) as valor FROM documents WHERE data_emissao BETWEEN ? AND ? GROUP BY DATE(data_emissao)"
        }
        
        # Sugestões contextuais padrão
        self.default_suggestions = [
            "Qual o valor total dos documentos processados?",
            "Quais são os principais fornecedores?",
            "Como está distribuído por categoria?",
            "Qual a evolução mensal dos valores?",
            "Quais fornecedores têm maior volume?",
            "Há algum padrão nos produtos mais comprados?"
        ]
    
    def generate_executive_insights(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Gera insights executivos automáticos baseados nos documentos processados
        
        Args:
            documents_data: Lista de documentos com dados extraídos e categorizados
            
        Returns:
            Dict com insights executivos estruturados
        """
        try:
            # Análise quantitativa
            quantitative_analysis = self._analyze_quantitative_data(documents_data)
            
            # Análise de fornecedores
            supplier_analysis = self._analyze_suppliers(documents_data)
            
            # Análise de categorias
            category_analysis = self._analyze_categories(documents_data)
            
            # Análise temporal
            temporal_analysis = self._analyze_temporal_patterns(documents_data)
            
            # Gerar insights com IA se disponível
            ai_insights = None
            if self.llm:
                ai_insights = self._generate_ai_executive_insights(
                    quantitative_analysis, supplier_analysis, category_analysis, temporal_analysis
                )
            
            # Identificar alertas e oportunidades
            alerts = self._identify_alerts(documents_data, quantitative_analysis)
            opportunities = self._identify_opportunities(supplier_analysis, category_analysis)
            
            return {
                "resumo_executivo": {
                    "total_documentos": len(documents_data),
                    "valor_total": quantitative_analysis.get("valor_total", 0),
                    "periodo_analise": quantitative_analysis.get("periodo"),
                    "fornecedores_unicos": len(supplier_analysis.get("fornecedores", {})),
                    "categorias_ativas": len(category_analysis.get("distribuicao", {}))
                },
                "analise_quantitativa": quantitative_analysis,
                "analise_fornecedores": supplier_analysis,
                "analise_categorias": category_analysis,
                "analise_temporal": temporal_analysis,
                "insights_ia": ai_insights,
                "alertas": alerts,
                "oportunidades": opportunities,
                "recomendacoes": self._generate_recommendations(
                    supplier_analysis, category_analysis, alerts, opportunities
                ),
                "metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "generated_at": datetime.now().isoformat(),
                    "method": "ai_enhanced" if self.llm else "rule_based"
                }
            }
            
        except Exception as e:
            return {
                "resumo_executivo": {"erro": str(e)},
                "metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "generated_at": datetime.now().isoformat(),
                    "method": "error",
                    "error": str(e)
                }
            }
    
    def process_natural_query(self, query: str, context: QueryContext) -> Dict[str, Any]:
        """
        Processa consulta em linguagem natural e retorna resposta executiva
        
        Args:
            query: Pergunta em português
            context: Contexto com dados disponíveis
            
        Returns:
            Dict com resposta, dados e sugestões
        """
        try:
            # Analisar intenção da consulta
            intent = self._analyze_query_intent(query)
            
            # Gerar SQL se necessário
            sql_query = None
            if intent.get("requires_sql"):
                sql_query = self._generate_sql_query(query, context)
            
            # Processar consulta
            if sql_query:
                # Executar consulta SQL simulada (em produção seria no Supabase)
                query_result = self._execute_simulated_query(sql_query, context.available_data)
            else:
                # Resposta baseada em dados disponíveis
                query_result = self._process_direct_query(query, context.available_data)
            
            # Gerar resposta executiva
            if self.llm:
                response = self._generate_ai_response(query, query_result, context)
            else:
                response = self._generate_rule_based_response(query, query_result, intent)
            
            # Gerar sugestões contextuais
            suggestions = self._generate_contextual_suggestions(query, context)
            
            return {
                "query": query,
                "response": response,
                "data": query_result,
                "sql_generated": sql_query,
                "intent": intent,
                "suggestions": suggestions,
                "metadata": {
                    "agent": self.name,
                    "processed_at": datetime.now().isoformat(),
                    "method": "ai_enhanced" if self.llm else "rule_based"
                }
            }
            
        except Exception as e:
            return {
                "query": query,
                "response": f"Desculpe, não consegui processar sua consulta: {str(e)}",
                "data": None,
                "error": str(e),
                "suggestions": self.default_suggestions[:3],
                "metadata": {
                    "agent": self.name,
                    "processed_at": datetime.now().isoformat(),
                    "method": "error"
                }
            }
    
    def _analyze_quantitative_data(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise quantitativa dos documentos"""
        if not documents_data:
            return {"valor_total": 0, "media_documento": 0, "periodo": None}
        
        valores = []
        datas = []
        
        for doc in documents_data:
            extracted = doc.get('extracted_data', {})
            if extracted and extracted.get('valor_total'):
                try:
                    valor = float(extracted['valor_total'])
                    valores.append(valor)
                except (ValueError, TypeError):
                    pass
            
            if extracted and extracted.get('data_emissao'):
                datas.append(extracted['data_emissao'])
        
        total = sum(valores)
        media = total / len(valores) if valores else 0
        
        # Período de análise
        periodo = None
        if datas:
            datas_validas = [d for d in datas if d]
            if datas_validas:
                periodo = {
                    "inicio": min(datas_validas),
                    "fim": max(datas_validas),
                    "dias": len(set(datas_validas))
                }
        
        return {
            "valor_total": total,
            "media_documento": media,
            "quantidade_documentos": len(documents_data),
            "documentos_com_valor": len(valores),
            "periodo": periodo,
            "estatisticas": {
                "maior_valor": max(valores) if valores else 0,
                "menor_valor": min(valores) if valores else 0,
                "mediana": sorted(valores)[len(valores)//2] if valores else 0
            }
        }
    
    def _analyze_suppliers(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise de fornecedores"""
        fornecedores = {}
        
        for doc in documents_data:
            extracted = doc.get('extracted_data', {})
            emitente = extracted.get('emitente', {}) if extracted else {}
            
            razao_social = emitente.get('razao_social')
            cnpj = emitente.get('cnpj')
            valor = extracted.get('valor_total', 0) if extracted else 0
            
            if razao_social:
                key = razao_social
                if key not in fornecedores:
                    fornecedores[key] = {
                        "razao_social": razao_social,
                        "cnpj": cnpj,
                        "documentos": 0,
                        "valor_total": 0,
                        "categoria_fornecedor": None
                    }
                
                fornecedores[key]["documentos"] += 1
                try:
                    fornecedores[key]["valor_total"] += float(valor) if valor else 0
                except (ValueError, TypeError):
                    pass
        
        # Ordenar por valor total
        fornecedores_ordenados = sorted(
            fornecedores.values(),
            key=lambda x: x["valor_total"],
            reverse=True
        )
        
        # Top 5 fornecedores
        top_fornecedores = fornecedores_ordenados[:5]
        
        # Análise de concentração
        total_valor = sum(f["valor_total"] for f in fornecedores.values())
        concentracao = {
            "top_3_percentual": sum(f["valor_total"] for f in top_fornecedores[:3]) / total_valor * 100 if total_valor > 0 else 0,
            "diversificacao": len(fornecedores),
            "fornecedor_dominante": fornecedores_ordenados[0] if fornecedores_ordenados else None
        }
        
        return {
            "fornecedores": fornecedores,
            "top_fornecedores": top_fornecedores,
            "concentracao": concentracao,
            "total_fornecedores": len(fornecedores)
        }
    
    def _analyze_categories(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise de categorias de produtos/serviços"""
        categorias = {}
        
        for doc in documents_data:
            categorized_items = doc.get('categorized_items', [])
            
            for item in categorized_items:
                if not isinstance(item, dict):
                    continue
                
                categoria = item.get('categoria', 'Outros')
                valor = item.get('valor_total', 0)
                
                if categoria not in categorias:
                    categorias[categoria] = {
                        "quantidade": 0,
                        "valor_total": 0,
                        "itens": []
                    }
                
                categorias[categoria]["quantidade"] += 1
                try:
                    categorias[categoria]["valor_total"] += float(valor) if valor else 0
                except (ValueError, TypeError):
                    pass
                
                categorias[categoria]["itens"].append(item.get('descricao', ''))
        
        # Ordenar por valor
        categorias_ordenadas = sorted(
            categorias.items(),
            key=lambda x: x[1]["valor_total"],
            reverse=True
        )
        
        # Distribuição percentual
        total_valor = sum(cat["valor_total"] for cat in categorias.values())
        distribuicao = {}
        for nome, dados in categorias.items():
            distribuicao[nome] = {
                "valor": dados["valor_total"],
                "percentual": (dados["valor_total"] / total_valor * 100) if total_valor > 0 else 0,
                "quantidade": dados["quantidade"]
            }
        
        return {
            "distribuicao": distribuicao,
            "categorias_ordenadas": categorias_ordenadas,
            "categoria_principal": categorias_ordenadas[0] if categorias_ordenadas else None,
            "diversidade": len(categorias)
        }
    
    def _analyze_temporal_patterns(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Análise de padrões temporais"""
        dados_temporais = {}
        
        for doc in documents_data:
            extracted = doc.get('extracted_data', {})
            if not extracted:
                continue
            
            data_emissao = extracted.get('data_emissao')
            valor = extracted.get('valor_total', 0)
            
            if data_emissao and valor:
                try:
                    # Agrupar por mês
                    mes_ano = data_emissao[:7]  # YYYY-MM
                    
                    if mes_ano not in dados_temporais:
                        dados_temporais[mes_ano] = {
                            "documentos": 0,
                            "valor_total": 0
                        }
                    
                    dados_temporais[mes_ano]["documentos"] += 1
                    dados_temporais[mes_ano]["valor_total"] += float(valor)
                    
                except (ValueError, TypeError):
                    pass
        
        # Ordenar por data
        timeline = sorted(dados_temporais.items())
        
        # Calcular tendências
        tendencia = None
        if len(timeline) >= 2:
            valores = [item[1]["valor_total"] for item in timeline]
            if len(valores) >= 2:
                crescimento = ((valores[-1] - valores[0]) / valores[0] * 100) if valores[0] > 0 else 0
                tendencia = {
                    "crescimento_percentual": crescimento,
                    "direcao": "crescimento" if crescimento > 5 else "declinio" if crescimento < -5 else "estavel"
                }
        
        return {
            "dados_mensais": dados_temporais,
            "timeline": timeline,
            "tendencia": tendencia,
            "periodo_ativo": len(timeline)
        }
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analisa a intenção da consulta em linguagem natural"""
        query_lower = query.lower()
        
        # Padrões de intenção
        patterns = {
            "valor_total": ["total", "soma", "quanto", "valor", "montante"],
            "fornecedores": ["fornecedor", "empresa", "emitente", "quem", "principais"],
            "categorias": ["categoria", "tipo", "produto", "serviço", "classificação"],
            "temporal": ["quando", "período", "mês", "ano", "data", "evolução", "tendência"],
            "comparacao": ["maior", "menor", "melhor", "pior", "comparar", "diferença"],
            "ranking": ["top", "principais", "maiores", "menores", "ranking", "lista"]
        }
        
        intents = []
        for intent, keywords in patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                intents.append(intent)
        
        # Determinar se precisa de SQL
        requires_sql = any(intent in ["temporal", "comparacao", "ranking"] for intent in intents)
        
        return {
            "intents": intents,
            "primary_intent": intents[0] if intents else "geral",
            "requires_sql": requires_sql,
            "complexity": "complex" if len(intents) > 2 else "simple"
        }
    
    def _generate_sql_query(self, query: str, context: QueryContext) -> Optional[str]:
        """Gera consulta SQL baseada na pergunta em português"""
        if not self.llm:
            return None
        
        try:
            # Schema simplificado para o contexto
            schema = """
            Tabelas disponíveis:
            - documents: id, filename, valor_total, data_emissao, emitente_razao_social, status
            - items: id, document_id, descricao, categoria, quantidade, valor_total
            - suppliers: razao_social, cnpj, tipo, documentos_count, valor_total
            """
            
            prompt = ChatPromptTemplate.from_template(
                """
                Você é um especialista em SQL para análise de documentos fiscais brasileiros.
                
                Schema do banco: {schema}
                
                Pergunta do usuário: "{query}"
                
                Gere uma consulta SQL que responda à pergunta. Retorne APENAS o SQL, sem explicações.
                
                Regras:
                - Use nomes de tabelas e colunas exatos do schema
                - Para valores monetários, use SUM() e ROUND()
                - Para datas, use DATE() functions
                - Ordene resultados de forma lógica
                - Limite resultados a 10 quando apropriado
                """
            )
            
            chain = prompt | self.llm
            result = chain.invoke({"schema": schema, "query": query})
            
            sql = result.content.strip() if hasattr(result, "content") else str(result).strip()
            
            # Limpar SQL se necessário
            if sql.startswith('```sql'):
                sql = sql.replace('```sql', '').replace('```', '').strip()
            
            return sql
            
        except Exception as e:
            print(f"Erro na geração de SQL: {e}")
            return None
    
    def _execute_simulated_query(self, sql: str, available_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simula execução de consulta SQL nos dados disponíveis"""
        # Em produção, isso seria executado no Supabase
        # Aqui fazemos uma simulação baseada nos dados disponíveis
        
        try:
            # Análise simples do SQL para determinar o tipo de resposta
            sql_lower = sql.lower()
            
            if "sum(valor_total)" in sql_lower:
                # Consulta de soma de valores
                total = available_data.get("valor_total", 0)
                return {"total": total, "type": "sum"}
            
            elif "count(*)" in sql_lower and "group by" in sql_lower:
                # Consulta de contagem agrupada
                if "emitente" in sql_lower or "supplier" in sql_lower:
                    fornecedores = available_data.get("fornecedores", {})
                    return {"results": list(fornecedores.values())[:10], "type": "grouped_count"}
                
                elif "categoria" in sql_lower:
                    categorias = available_data.get("categorias", {})
                    return {"results": list(categorias.items())[:10], "type": "category_count"}
            
            else:
                # Consulta genérica
                return {"message": "Consulta processada", "type": "generic"}
                
        except Exception as e:
            return {"error": str(e), "type": "error"}
    
    def _process_direct_query(self, query: str, available_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa consulta diretamente nos dados disponíveis"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["total", "soma", "quanto"]):
            return {"valor_total": available_data.get("valor_total", 0)}
        
        elif any(word in query_lower for word in ["fornecedor", "empresa"]):
            return {"fornecedores": available_data.get("fornecedores", {})}
        
        elif any(word in query_lower for word in ["categoria", "produto"]):
            return {"categorias": available_data.get("categorias", {})}
        
        else:
            return {"resumo": available_data}
    
    def _generate_ai_response(self, query: str, query_result: Dict[str, Any], context: QueryContext) -> str:
        """Gera resposta executiva usando IA"""
        try:
            prompt = ChatPromptTemplate.from_template(
                """
                Você é um assistente executivo especializado em análise fiscal brasileira.
                
                Pergunta do usuário: "{query}"
                Dados encontrados: {data}
                
                Gere uma resposta executiva em português que:
                - Responda diretamente à pergunta
                - Use linguagem executiva e profissional
                - Inclua números específicos quando disponíveis
                - Forneça insights acionáveis
                - Seja concisa mas informativa
                
                Resposta:
                """
            )
            
            chain = prompt | self.llm
            result = chain.invoke({
                "query": query,
                "data": json.dumps(query_result, ensure_ascii=False)
            })
            
            return result.content if hasattr(result, "content") else str(result)
            
        except Exception as e:
            return f"Baseado nos dados disponíveis, posso fornecer as seguintes informações: {query_result}"
    
    def _generate_rule_based_response(self, query: str, query_result: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """Gera resposta baseada em regras quando IA não está disponível"""
        primary_intent = intent.get("primary_intent", "geral")
        
        if primary_intent == "valor_total":
            valor = query_result.get("valor_total", 0)
            return f"O valor total processado é R$ {valor:,.2f}."
        
        elif primary_intent == "fornecedores":
            fornecedores = query_result.get("fornecedores", {})
            count = len(fornecedores)
            return f"Temos {count} fornecedores únicos nos documentos processados."
        
        elif primary_intent == "categorias":
            categorias = query_result.get("categorias", {})
            count = len(categorias)
            return f"Os produtos/serviços estão distribuídos em {count} categorias diferentes."
        
        else:
            return "Dados processados com sucesso. Use consultas mais específicas para obter insights detalhados."
    
    def _generate_contextual_suggestions(self, query: str, context: QueryContext) -> List[str]:
        """Gera sugestões contextuais baseadas na consulta atual"""
        suggestions = []
        
        # Sugestões baseadas na consulta atual
        query_lower = query.lower()
        
        if "total" in query_lower:
            suggestions.extend([
                "Qual fornecedor tem o maior volume?",
                "Como está a distribuição por categoria?",
                "Qual a evolução mensal dos valores?"
            ])
        
        elif "fornecedor" in query_lower:
            suggestions.extend([
                "Quais categorias este fornecedor mais fornece?",
                "Qual a frequência de compras deste fornecedor?",
                "Há oportunidades de negociação?"
            ])
        
        elif "categoria" in query_lower:
            suggestions.extend([
                "Quais fornecedores dominam esta categoria?",
                "Qual a tendência de crescimento desta categoria?",
                "Há oportunidades de consolidação?"
            ])
        
        # Adicionar sugestões padrão se necessário
        while len(suggestions) < 3:
            for suggestion in self.default_suggestions:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    break
        
        return suggestions[:5]  # Máximo 5 sugestões
    
    def _generate_ai_executive_insights(self, quantitative: Dict, suppliers: Dict, categories: Dict, temporal: Dict) -> Optional[Dict[str, Any]]:
        """Gera insights executivos usando IA"""
        if not self.llm:
            return None
        
        try:
            context_data = {
                "quantitative": quantitative,
                "suppliers": suppliers,
                "categories": categories,
                "temporal": temporal
            }
            
            prompt = ChatPromptTemplate.from_template(
                """
                Você é um consultor executivo sênior analisando dados fiscais de uma empresa brasileira.
                
                Dados para análise: {data}
                
                Gere insights executivos estruturados em JSON:
                {{
                    "insights_principais": ["insight estratégico 1", "insight estratégico 2"],
                    "oportunidades": ["oportunidade 1", "oportunidade 2"],
                    "riscos": ["risco identificado 1"],
                    "recomendacoes_imediatas": ["ação 1", "ação 2"],
                    "kpis_sugeridos": ["KPI 1", "KPI 2"],
                    "score_geral": 8.5
                }}
                
                Foque em:
                - Concentração de fornecedores
                - Diversificação de categorias
                - Padrões temporais
                - Oportunidades de otimização
                - Riscos operacionais
                """
            )
            
            chain = prompt | self.llm
            result = chain.invoke({"data": json.dumps(context_data, ensure_ascii=False)})
            
            result_str = result.content if hasattr(result, "content") else str(result)
            
            # Parse JSON
            if result_str.startswith('```json'):
                result_str = result_str.replace('```json', '').replace('```', '').strip()
            
            return json.loads(result_str)
            
        except Exception as e:
            print(f"Erro na geração de insights IA: {e}")
            return None
    
    def _identify_alerts(self, documents_data: List[Dict[str, Any]], quantitative: Dict[str, Any]) -> List[str]:
        """Identifica alertas baseados nos dados"""
        alerts = []
        
        # Alert de concentração de fornecedores
        if len(set(doc.get('extracted_data', {}).get('emitente', {}).get('razao_social') 
                  for doc in documents_data if doc.get('extracted_data', {}).get('emitente', {}).get('razao_social'))) <= 2:
            alerts.append("Alta concentração de fornecedores - risco de dependência")
        
        # Alert de valores muito altos
        valores = [float(doc.get('extracted_data', {}).get('valor_total', 0)) 
                  for doc in documents_data 
                  if doc.get('extracted_data', {}).get('valor_total')]
        
        if valores:
            media = sum(valores) / len(valores)
            for valor in valores:
                if valor > media * 3:
                    alerts.append(f"Documento com valor atípico detectado: R$ {valor:,.2f}")
                    break
        
        return alerts
    
    def _identify_opportunities(self, suppliers: Dict[str, Any], categories: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades baseadas nos dados"""
        opportunities = []
        
        # Oportunidade de consolidação de fornecedores
        if suppliers.get("total_fornecedores", 0) > 10:
            opportunities.append("Oportunidade de consolidação de fornecedores para melhor negociação")
        
        # Oportunidade de diversificação
        concentracao = suppliers.get("concentracao", {})
        if concentracao.get("top_3_percentual", 0) > 80:
            opportunities.append("Considerar diversificação de fornecedores para reduzir riscos")
        
        # Oportunidade de padronização de categorias
        if categories.get("diversidade", 0) > 15:
            opportunities.append("Oportunidade de padronização e consolidação de categorias")
        
        return opportunities
    
    def _generate_recommendations(self, suppliers: Dict, categories: Dict, alerts: List[str], opportunities: List[str]) -> List[str]:
        """Gera recomendações executivas"""
        recommendations = []
        
        # Recomendações baseadas em alertas
        if any("concentração" in alert for alert in alerts):
            recommendations.append("Desenvolver estratégia de diversificação de fornecedores")
        
        if any("atípico" in alert for alert in alerts):
            recommendations.append("Implementar controles adicionais para valores elevados")
        
        # Recomendações baseadas em oportunidades
        if any("consolidação" in opp for opp in opportunities):
            recommendations.append("Avaliar programa de fornecedores preferenciais")
        
        if any("diversificação" in opp for opp in opportunities):
            recommendations.append("Mapear fornecedores alternativos para categorias críticas")
        
        # Recomendações gerais
        if not recommendations:
            recommendations.extend([
                "Implementar dashboard de monitoramento contínuo",
                "Estabelecer KPIs de performance de fornecedores",
                "Criar processo de revisão mensal de gastos"
            ])
        
        return recommendations[:5]  # Máximo 5 recomendações