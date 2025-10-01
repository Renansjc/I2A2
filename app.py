"""
Agente Autônomo para Análise Exploratória de Dados (EDA)
Autor: [Seu Nome]
Framework: OpenAI + Streamlit
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv('config.env')
except:
    pass

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================
PAGE_CONFIG = {
    "page_title": "EDA Agent Pro",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

ANALYSIS_MEMORY_DIR = Path(".eda_sessions")
ANALYSIS_MEMORY_DIR.mkdir(exist_ok=True)

# ============================================================================
# CLASSE PRINCIPAL: DataAnalyzer
# ============================================================================
class DataAnalyzer:
    """Analisador de dados com capacidades de EDA e geração de insights"""
    
    def __init__(self, dataframe: pd.DataFrame, session_id: str):
        self.df = dataframe
        self.session_id = session_id
        self.metadata = self._extract_metadata()
        self.insights_history = []
        
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extrai metadados do dataset sem enviar dados completos"""
        numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        metadata = {
            "shape": self.df.shape,
            "columns": self.df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "numeric_cols": numeric_columns,
            "categorical_cols": categorical_columns,
            "missing_values": self.df.isnull().sum().to_dict(),
            "sample_stats": {}
        }
        
        # Estatísticas básicas para colunas numéricas (limita a 10)
        for col in numeric_columns[:10]:
            try:
                metadata["sample_stats"][col] = {
                    "mean": float(self.df[col].mean()),
                    "std": float(self.df[col].std()),
                    "min": float(self.df[col].min()),
                    "max": float(self.df[col].max()),
                    "median": float(self.df[col].median()),
                    "q25": float(self.df[col].quantile(0.25)),
                    "q75": float(self.df[col].quantile(0.75))
                }
            except:
                pass
        
        return metadata
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo geral do dataset"""
        return {
            "shape": self.metadata['shape'],
            "columns": len(self.metadata['columns']),
            "numeric_cols": len(self.metadata['numeric_cols']),
            "categorical_cols": len(self.metadata['categorical_cols']),
            "missing_values": sum(self.metadata['missing_values'].values()),
            "sample_stats": self.metadata['sample_stats']
        }
    
    def compute_correlation_analysis(self) -> Dict[str, Any]:
        """Análise de correlação entre variáveis numéricas"""
        numeric_df = self.df[self.metadata['numeric_cols']]
        
        if len(self.metadata['numeric_cols']) < 2:
            return {"error": "Necessário pelo menos 2 colunas numéricas"}
        
        corr_matrix = numeric_df.corr()
        
        # Encontrar correlações mais fortes
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.5:
                    strong_correlations.append({
                        "var1": corr_matrix.columns[i],
                        "var2": corr_matrix.columns[j],
                        "correlation": float(corr_val)
                    })
        
        return {
            "correlation_matrix": corr_matrix,
            "strong_correlations": sorted(strong_correlations, 
                                         key=lambda x: abs(x['correlation']), 
                                         reverse=True)[:10]
        }
    
    def detect_anomalies(self, column: str, method: str = "iqr") -> Dict[str, Any]:
        """Detecta anomalias em uma coluna específica"""
        if column not in self.metadata['numeric_cols']:
            return {"error": f"Coluna {column} não é numérica"}
        
        data = self.df[column].dropna()
        
        if len(data) == 0:
            return {"error": "Coluna não possui dados válidos"}
        
        if method == "zscore":
            z_scores = np.abs((data - data.mean()) / data.std())
            anomalies = data[z_scores > 3]
            threshold = "Z-score > 3"
        elif method == "iqr":
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            anomalies = data[(data < lower_bound) | (data > upper_bound)]
            threshold = f"IQR: [{lower_bound:.2f}, {upper_bound:.2f}]"
        
        return {
            "column": column,
            "total_values": len(data),
            "anomalies_count": len(anomalies),
            "anomalies_percentage": (len(anomalies) / len(data)) * 100,
            "method": method,
            "threshold": threshold,
            "anomalies_sample": anomalies.head(10).tolist()
        }
    
    def temporal_analysis(self, time_col: str, value_col: str) -> Dict[str, Any]:
        """Análise temporal de uma série"""
        if time_col not in self.df.columns or value_col not in self.metadata['numeric_cols']:
            return {"error": "Colunas inválidas"}
        
        df_temp = self.df[[time_col, value_col]].copy()
        df_temp[time_col] = pd.to_datetime(df_temp[time_col], errors='coerce')
        df_temp = df_temp.dropna()
        df_temp = df_temp.sort_values(time_col)
        
        if len(df_temp) < 10:
            return {"error": "Dados insuficientes para análise temporal"}
        
        # Tendência (média móvel)
        window_size = min(30, len(df_temp)//10)
        df_temp['moving_avg'] = df_temp[value_col].rolling(window=window_size).mean()
        
        return {
            "has_trend": True,
            "data": df_temp,
            "start_date": str(df_temp[time_col].min()),
            "end_date": str(df_temp[time_col].max()),
            "mean_value": float(df_temp[value_col].mean())
        }


# ============================================================================
# CLASSE: MemoryManager
# ============================================================================
class MemoryManager:
    """Gerencia memória persistente das análises"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory_file = ANALYSIS_MEMORY_DIR / f"session_{session_id}.json"
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict:
        """Carrega memória existente"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "queries": [],
            "insights": [],
            "conclusions": [],
            "created_at": datetime.now().isoformat()
        }
    
    def save_query(self, question: str, answer: str, chart_type: Optional[str] = None):
        """Salva uma query e resposta"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "chart_type": chart_type
        }
        self.memory["queries"].append(entry)
        self._persist()
    
    def save_insight(self, insight: str, category: str):
        """Salva um insight descoberto"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "insight": insight,
            "category": category
        }
        self.memory["insights"].append(entry)
        self._persist()
    
    def save_conclusion(self, conclusion: str):
        """Salva conclusão geral da análise"""
        self.memory["conclusions"].append({
            "timestamp": datetime.now().isoformat(),
            "text": conclusion
        })
        self._persist()
    
    def get_context_summary(self) -> str:
        """Retorna resumo do contexto para a LLM"""
        num_queries = len(self.memory['queries'])
        summary = f"Análises anteriores realizadas: {num_queries}\n"
        
        if self.memory['insights']:
            summary += "\nÚltimos insights descobertos:\n"
            for insight in self.memory['insights'][-3:]:
                cat = insight['category']
                text = insight['insight']
                summary += f"- [{cat}] {text}\n"
        
        return summary
    
    def _persist(self):
        """Persiste memória em disco"""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.warning(f"Erro ao salvar memória: {e}")


# ============================================================================
# CLASSE: LLMQueryProcessor
# ============================================================================
class LLMQueryProcessor:
    """Processa queries usando LLM"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def interpret_query(self, question: str, metadata: Dict, context: str) -> Dict[str, Any]:
        """Interpreta a pergunta e determina qual análise executar"""
        
        system_prompt = """Você é um assistente especialista em análise de dados.
Analise a pergunta do usuário e determine qual tipo de análise deve ser executada.

Retorne APENAS um JSON válido com a seguinte estrutura:
{
    "analysis_type": "correlation" | "anomaly" | "distribution" | "temporal" | "summary" | "conclusion",
    "parameters": {
        "column": "nome_da_coluna" (se aplicável),
        "method": "iqr" ou "zscore" (para anomalias)
    },
    "reasoning": "breve explicação"
}
"""
        
        cols_sample = metadata['columns'][:20]
        num_cols_sample = metadata['numeric_cols'][:15]
        shape = metadata['shape']
        
        user_prompt = f"""Pergunta do usuário: {question}

Metadados do dataset:
- Colunas disponíveis: {cols_sample}
- Colunas numéricas: {num_cols_sample}
- Shape: {shape}

Contexto:
{context}

Determine qual análise executar."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Erro ao interpretar query: {e}")
            return {
                "analysis_type": "summary",
                "parameters": {},
                "reasoning": f"Fallback devido a erro: {str(e)}"
            }
    
    def generate_insight(self, analysis_result: Dict, question: str) -> str:
        """Gera insight em linguagem natural"""
        
        system_prompt = """Você é um analista de dados experiente.
Gere um insight claro em português baseado nos resultados.
Seja conciso e objetivo (máximo 200 palavras)."""
        
        result_str = json.dumps(analysis_result, indent=2, default=str)[:2000]
        
        user_prompt = f"""Pergunta: {question}

Resultados:
{result_str}

Gere um insight em português."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Análise concluída. Resultados: {str(analysis_result)[:300]}"
    
    def generate_conclusions(self, memory: Dict, metadata: Dict) -> str:
        """Gera conclusões gerais"""
        
        system_prompt = """Você é um cientista de dados sênior.
Analise o histórico de análises e gere conclusões gerais sobre o dataset.
Seja específico, técnico e objetivo."""
        
        insights_list = memory['insights'][-10:]
        insights_text = "\n".join([f"- {ins['insight']}" for ins in insights_list])
        
        num_rows = metadata['shape'][0]
        num_cols = metadata['shape'][1]
        num_numeric = len(metadata['numeric_cols'])
        
        user_prompt = f"""Dataset: {num_rows:,} linhas × {num_cols} colunas
Variáveis numéricas: {num_numeric}

Insights das análises:
{insights_text}

Gere conclusões gerais em português (máximo 400 palavras)."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=600
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Erro ao gerar conclusões: {str(e)}"


# ============================================================================
# CLASSE: ChartGenerator
# ============================================================================
class ChartGenerator:
    """Gera visualizações"""
    
    @staticmethod
    def plot_correlation_heatmap(corr_matrix: pd.DataFrame):
        """Gera heatmap de correlação"""
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={"size": 9}
        ))
        
        height = min(600, 50 * len(corr_matrix.columns))
        fig.update_layout(title='Matriz de Correlação', height=height)
        
        return fig
    
    @staticmethod
    def plot_distribution(data: pd.Series, column_name: str):
        """Gera gráfico de distribuição"""
        fig = make_subplots(rows=1, cols=2, subplot_titles=('Histograma', 'Box Plot'))
        
        fig.add_trace(go.Histogram(x=data, name='Freq', nbinsx=30), row=1, col=1)
        fig.add_trace(go.Box(y=data, name=column_name), row=1, col=2)
        
        fig.update_layout(
            title=f'Distribuição: {column_name}',
            height=400,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_temporal(df_temp: pd.DataFrame, time_col: str, value_col: str):
        """Gera gráfico temporal"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_temp[time_col],
            y=df_temp[value_col],
            mode='lines',
            name='Valores',
            line=dict(color='blue', width=1)
        ))
        
        if 'moving_avg' in df_temp.columns:
            fig.add_trace(go.Scatter(
                x=df_temp[time_col],
                y=df_temp['moving_avg'],
                mode='lines',
                name='Média Móvel',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title=f'Análise Temporal: {value_col}',
            xaxis_title=time_col,
            yaxis_title=value_col,
            hovermode='x unified',
            height=500
        )
        
        return fig


# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================
def generate_session_id(file_content: bytes) -> str:
    """Gera ID único para sessão"""
    return hashlib.md5(file_content).hexdigest()[:12]


def main():
    st.set_page_config(**PAGE_CONFIG)
    
    st.title("🤖 Agente Autônomo de Análise Exploratória de Dados")
    st.markdown("*Framework: OpenAI GPT-4o-mini + Streamlit*")
    
    # Sidebar - apenas configuração
    with st.sidebar:
        st.header("⚙️ Configuração")
        
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", "")
        )
        
        if not api_key:
            st.warning("⚠️ Configure a API Key")
            st.stop()
    
    # Upload na área principal
    st.divider()
    uploaded_file = st.file_uploader(
        "📁 Faça upload de um arquivo CSV para começar",
        type=['csv'],
        help="Carregue um dataset em formato CSV"
    )
    
    if not uploaded_file:
        st.info("👆 Faça upload de um arquivo CSV para começar")
        st.stop()
    
    # Carregar dados
    file_content = uploaded_file.getvalue()
    session_id = generate_session_id(file_content)
    
    @st.cache_data
    def load_data(content):
        return pd.read_csv(content)
    
    try:
        df = load_data(uploaded_file)
        st.success(f"📊 Dataset: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        st.stop()
    
    # Inicializar componentes
    analyzer = DataAnalyzer(df, session_id)
    memory_mgr = MemoryManager(session_id)
    llm_processor = LLMQueryProcessor(api_key)
    chart_gen = ChartGenerator()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🔍 Análise",
        "💡 Memória",
        "📝 Conclusões"
    ])
    
    with tab1:
        st.subheader("Resumo Estatístico")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Linhas", f"{df.shape[0]:,}")
        col2.metric("Colunas", df.shape[1])
        col3.metric("Numéricas", len(analyzer.metadata['numeric_cols']))
        
        st.dataframe(df.head(20), use_container_width=True)
        
        st.subheader("Estatísticas Descritivas")
        st.dataframe(df.describe(), use_container_width=True)
    
    with tab2:
        st.subheader("💬 Pergunte ao Agente")
        
        question = st.text_area(
            "Sua pergunta:",
            placeholder="Ex: Existe correlação? Quais outliers em Amount?",
            height=100
        )
        
        if st.button("🚀 Analisar", type="primary"):
            if not question:
                st.warning("Digite uma pergunta")
            else:
                with st.spinner("Processando..."):
                    try:
                        context = memory_mgr.get_context_summary()
                        interpretation = llm_processor.interpret_query(
                            question, analyzer.metadata, context
                        )
                        
                        analysis_type = interpretation['analysis_type']
                        st.info(f"🎯 Análise: **{analysis_type}**")
                        
                        result = None
                        chart = None
                        
                        # TRATAMENTO POR TIPO DE ANÁLISE
                        if analysis_type == 'summary':
                            result = analyzer.get_summary()
                        
                        elif analysis_type == 'correlation':
                            result = analyzer.compute_correlation_analysis()
                            if 'correlation_matrix' in result:
                                chart = chart_gen.plot_correlation_heatmap(
                                    result['correlation_matrix']
                                )
                        
                        elif analysis_type == 'anomaly':
                            col = interpretation['parameters'].get('column')
                            if col and col in analyzer.metadata['numeric_cols']:
                                method = interpretation['parameters'].get('method', 'iqr')
                                result = analyzer.detect_anomalies(col, method=method)
                        
                        elif analysis_type == 'distribution':
                            col = interpretation['parameters'].get('column')
                            if col and col in analyzer.metadata['numeric_cols']:
                                chart = chart_gen.plot_distribution(df[col], col)
                                result = {"column": col, "status": "Gráfico gerado"}
                        
                        elif analysis_type == 'temporal':
                            params = interpretation['parameters']
                            time_col = params.get('time_column')
                            value_col = params.get('value_column')
                            if time_col and value_col:
                                result = analyzer.temporal_analysis(time_col, value_col)
                                if 'data' in result:
                                    chart = chart_gen.plot_temporal(
                                        result['data'], time_col, value_col
                                    )
                        
                        elif analysis_type == 'conclusion':
                            conclusion = llm_processor.generate_conclusions(
                                memory_mgr.memory, analyzer.metadata
                            )
                            st.success("📋 Conclusões Gerais")
                            st.write(conclusion)
                            memory_mgr.save_conclusion(conclusion)
                            result = {"done": True}
                        
                        # Gerar insight se houver resultado
                        if result and analysis_type != 'conclusion':
                            if 'error' in result:
                                st.error(result['error'])
                            else:
                                insight = llm_processor.generate_insight(result, question)
                                st.success("✨ Resposta")
                                st.write(insight)
                                memory_mgr.save_query(question, insight, analysis_type)
                                memory_mgr.save_insight(insight, analysis_type)
                        
                        # Mostrar gráfico
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Erro durante análise: {e}")
                        import traceback
                        with st.expander("Ver detalhes do erro"):
                            st.code(traceback.format_exc())
    
    with tab3:
        st.subheader("🧠 Memória do Agente")
        
        num_queries = len(memory_mgr.memory['queries'])
        
        if num_queries > 0:
            st.write(f"**Total de análises:** {num_queries}")
            
            for i, q in enumerate(reversed(memory_mgr.memory['queries'][-5:]), 1):
                preview = q['question'][:50]
                with st.expander(f"Query {num_queries - i + 1}: {preview}..."):
                    st.write(f"**Pergunta:** {q['question']}")
                    st.write(f"**Resposta:** {q['answer']}")
                    st.caption(f"📅 {q['timestamp']}")
        else:
            st.info("Nenhuma análise realizada")
        
        st.divider()
        
        st.subheader("💡 Insights Acumulados")
        if memory_mgr.memory['insights']:
            for ins in memory_mgr.memory['insights'][-5:]:
                st.info(f"**[{ins['category']}]** {ins['insight']}")
        else:
            st.info("Nenhum insight gerado")
    
    with tab4:
        st.subheader("📝 Conclusões Finais")
        
        if st.button("🎯 Gerar Conclusões Gerais"):
            with st.spinner("Analisando histórico..."):
                try:
                    conclusion = llm_processor.generate_conclusions(
                        memory_mgr.memory, analyzer.metadata
                    )
                    st.success("✅ Conclusões Geradas")
                    st.write(conclusion)
                    memory_mgr.save_conclusion(conclusion)
                except Exception as e:
                    st.error(f"Erro: {e}")
        
        if memory_mgr.memory['conclusions']:
            st.divider()
            st.subheader("Histórico")
            for conc in memory_mgr.memory['conclusions']:
                st.write(conc['text'])
                st.caption(f"📅 {conc['timestamp']}")
        else:
            st.info("Nenhuma conclusão gerada ainda")


if __name__ == "__main__":
    main()