"""
Agente Autônomo para Análise Exploratória de Dados (EDA)
Autor: [Seu Nome] - VERSÃO AJUSTADA
Framework: OpenAI + Streamlit
Alterações menores: prompt do LLM melhorado; suporte à análise de distribuição em múltiplas colunas; tratamento da coluna Time quando é numérica; correções de UI/slider e proteções contra respostas vazias do LLM.
"""

import os
import json
import hashlib
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
import warnings

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from openai import OpenAI

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suprimir warnings desnecessários
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

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

# Configurações do sistema
MAX_FILE_SIZE_MB = 200
MAX_ROWS_PREVIEW = 100
MAX_COLUMNS_FOR_ANALYSIS = 50
ANALYSIS_MEMORY_DIR = Path(".eda_sessions")
ANALYSIS_MEMORY_DIR.mkdir(exist_ok=True)

# Configurações de análise
CORRELATION_THRESHOLD = 0.5
ANOMALY_ZSCORE_THRESHOLD = 3
ANOMALY_IQR_MULTIPLIER = 1.5
PCA_COMPONENTS = 0.95  # Variância explicada mínima

# Mensagens de erro padronizadas
ERROR_MESSAGES = {
    "file_too_large": f"Arquivo muito grande. Máximo permitido: {MAX_FILE_SIZE_MB}MB",
    "invalid_csv": "Arquivo CSV inválido ou corrompido",
    "empty_dataset": "Dataset está vazio ou não possui dados válidos",
    "insufficient_data": "Dados insuficientes para análise",
    "api_error": "Erro na comunicação com a API OpenAI",
    "analysis_error": "Erro durante análise dos dados"
}

# ============================================================================
# CLASSE PRINCIPAL: DataAnalyzer
# ============================================================================
class DataAnalyzer:
    """Analisador de dados com capacidades de EDA e geração de insights"""
    
    def __init__(self, dataframe: pd.DataFrame, session_id: str):
        self.df = dataframe
        self.session_id = session_id
        self.insights_history = []
        self._validate_dataframe()
        self.metadata = self._extract_metadata()
        
    def _validate_dataframe(self):
        """Valida se o dataframe é adequado para análise"""
        if self.df.empty:
            raise ValueError(ERROR_MESSAGES["empty_dataset"])
        
        if len(self.df.columns) > MAX_COLUMNS_FOR_ANALYSIS:
            logger.warning(f"Dataset tem {len(self.df.columns)} colunas. Limitando análise às primeiras {MAX_COLUMNS_FOR_ANALYSIS}")
            self.df = self.df.iloc[:, :MAX_COLUMNS_FOR_ANALYSIS]
        
        if len(self.df) < 5:
            raise ValueError(ERROR_MESSAGES["insufficient_data"])
        
        # Verificar se há pelo menos uma coluna numérica
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            logger.warning("Nenhuma coluna numérica encontrada. Análises quantitativas serão limitadas.")
        
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extrai metadados do dataset sem enviar dados completos"""
        try:
            numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
            datetime_columns = self.df.select_dtypes(include=['datetime64']).columns.tolist()
            
            metadata = {
                "shape": self.df.shape,
                "columns": self.df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
                "numeric_cols": numeric_columns,
                "categorical_cols": categorical_columns,
                "datetime_cols": datetime_columns,
                "missing_values": self.df.isnull().sum().to_dict(),
                "missing_percentage": (self.df.isnull().sum() / len(self.df) * 100).to_dict(),
                "sample_stats": {},
                "data_quality": self._assess_data_quality()
            }
            
            # Estatísticas básicas para colunas numéricas
            for col in numeric_columns[:15]:  # Aumentado para 15
                try:
                    col_data = self.df[col].dropna()
                    if len(col_data) > 0:
                        metadata["sample_stats"][col] = {
                            "mean": float(col_data.mean()),
                            "std": float(col_data.std()),
                            "min": float(col_data.min()),
                            "max": float(col_data.max()),
                            "median": float(col_data.median()),
                            "q25": float(col_data.quantile(0.25)),
                            "q75": float(col_data.quantile(0.75)),
                            "skewness": float(stats.skew(col_data)),
                            "kurtosis": float(stats.kurtosis(col_data))
                        }
                except Exception as e:
                    logger.warning(f"Erro ao calcular estatísticas para {col}: {e}")
            
            return metadata
        except Exception as e:
            logger.error(f"Erro ao extrair metadados: {e}")
            raise ValueError(f"Erro ao processar metadados: {str(e)}")
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Avalia a qualidade dos dados"""
        total_cells = self.df.size
        missing_cells = self.df.isnull().sum().sum()
        duplicate_rows = self.df.duplicated().sum()
        
        return {
            "completeness": (total_cells - missing_cells) / total_cells * 100,
            "missing_cells": int(missing_cells),
            "duplicate_rows": int(duplicate_rows),
            "duplicate_percentage": duplicate_rows / len(self.df) * 100,
            "total_cells": int(total_cells)
        }
    
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
        try:
            numeric_cols = self.metadata['numeric_cols']
            
            if len(numeric_cols) < 2:
                return {"error": "Necessário pelo menos 2 colunas numéricas"}
            
            numeric_df = self.df[numeric_cols].dropna()
            
            if len(numeric_df) < 10:
                return {"error": "Dados insuficientes após remoção de valores faltantes"}
            
            corr_matrix = numeric_df.corr()
            
            # Encontrar correlações mais fortes
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > CORRELATION_THRESHOLD:
                        strong_correlations.append({
                            "var1": corr_matrix.columns[i],
                            "var2": corr_matrix.columns[j],
                            "correlation": float(corr_val),
                            "strength": "forte" if abs(corr_val) > 0.7 else "moderada"
                        })
            
            # Detectar multicolinearidade
            multicollinearity = self._detect_multicollinearity(corr_matrix)
            
            return {
                "correlation_matrix": corr_matrix,
                "strong_correlations": sorted(strong_correlations, 
                                             key=lambda x: abs(x['correlation']), 
                                             reverse=True)[:15],
                "multicollinearity": multicollinearity,
                "correlation_summary": {
                    "total_pairs": len(numeric_cols) * (len(numeric_cols) - 1) // 2,
                    "strong_pairs": len(strong_correlations),
                    "avg_correlation": float(corr_matrix.abs().mean().mean())
                }
            }
        except Exception as e:
            logger.error(f"Erro na análise de correlação: {e}")
            return {"error": f"Erro na análise de correlação: {str(e)}"}
    
    def _detect_multicollinearity(self, corr_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Detecta problemas de multicolinearidade"""
        try:
            # Calcular VIF aproximado usando correlação
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = abs(corr_matrix.iloc[i, j])
                    if corr_val > 0.8:
                        high_corr_pairs.append({
                            "var1": corr_matrix.columns[i],
                            "var2": corr_matrix.columns[j],
                            "correlation": float(corr_val)
                        })
            
            return {
                "high_correlation_pairs": high_corr_pairs,
                "has_multicollinearity": len(high_corr_pairs) > 0,
                "severity": "alta" if len(high_corr_pairs) > 3 else "moderada" if len(high_corr_pairs) > 0 else "baixa"
            }
        except Exception as e:
            logger.warning(f"Erro ao detectar multicolinearidade: {e}")
            return {"error": str(e)}
    
    def detect_anomalies(self, column: str, method: str = "iqr") -> Dict[str, Any]:
        """Detecta anomalias em uma coluna específica"""
        try:
            if column not in self.metadata['numeric_cols']:
                return {"error": f"Coluna {column} não é numérica"}
            
            data = self.df[column].dropna()
            
            if len(data) < 10:
                return {"error": "Dados insuficientes para detecção de anomalias"}
            
            anomalies = None
            threshold = ""
            anomaly_indices = []
            
            if method == "zscore":
                z_scores = np.abs((data - data.mean()) / data.std())
                anomaly_mask = z_scores > ANOMALY_ZSCORE_THRESHOLD
                anomalies = data[anomaly_mask]
                anomaly_indices = data[anomaly_mask].index.tolist()
                threshold = f"Z-score > {ANOMALY_ZSCORE_THRESHOLD}"
                
            elif method == "iqr":
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - ANOMALY_IQR_MULTIPLIER * IQR
                upper_bound = Q3 + ANOMALY_IQR_MULTIPLIER * IQR
                anomaly_mask = (data < lower_bound) | (data > upper_bound)
                anomalies = data[anomaly_mask]
                anomaly_indices = data[anomaly_mask].index.tolist()
                threshold = f"IQR: [{lower_bound:.2f}, {upper_bound:.2f}]"
                
            elif method == "isolation_forest":
                # Implementação simples de Isolation Forest
                from sklearn.ensemble import IsolationForest
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_labels = iso_forest.fit_predict(data.values.reshape(-1, 1))
                anomaly_mask = anomaly_labels == -1
                anomalies = data[anomaly_mask]
                anomaly_indices = data[anomaly_mask].index.tolist()
                threshold = "Isolation Forest (contamination=0.1)"
            
            if anomalies is None:
                return {"error": f"Método {method} não implementado"}
            
            return {
                "column": column,
                "total_values": len(data),
                "anomalies_count": len(anomalies),
                "anomalies_percentage": (len(anomalies) / len(data)) * 100,
                "method": method,
                "threshold": threshold,
                "anomalies_sample": anomalies.head(10).tolist(),
                "anomaly_indices": anomaly_indices[:20],  # Limitar para performance
                "statistics": {
                    "mean": float(data.mean()),
                    "std": float(data.std()),
                    "min": float(data.min()),
                    "max": float(data.max())
                }
            }
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {e}")
            return {"error": f"Erro na detecção de anomalias: {str(e)}"}
    
    def temporal_analysis(self, time_col: str, value_col: str) -> Dict[str, Any]:
        """Análise temporal de uma série
        Nota: trata automaticamente quando a coluna de tempo é numérica (por exemplo: segundos desde o início).
        **Importante:** quando a coluna for numérica, INTERPRETAR COMO SEGUNDOS desde a primeira transação e **NÃO** converter para Unix epoch (1970-01-01). O eixo deverá mostrar segundos (ou tempo decorrido) em vez de datas de 1970.
        """
        try:
            if time_col not in self.df.columns or value_col not in self.metadata['numeric_cols']:
                return {"error": "Colunas inválidas"}

            df_temp = self.df[[time_col, value_col]].copy()
            # Se a coluna de tempo for numérica, interpretar como segundos desde o início (não usar epoch unix)
            if pd.api.types.is_numeric_dtype(df_temp[time_col]):
                df_temp['__time_seconds'] = df_temp[time_col].astype(float)
                # calcular tempo decorrido a partir do primeiro evento (em segundos)
                df_temp['__time_elapsed'] = df_temp['__time_seconds'] - df_temp['__time_seconds'].min()
                df_temp = df_temp.dropna(subset=['__time_elapsed'])
                df_temp = df_temp.sort_values('__time_elapsed')
                time_use = '__time_elapsed'
                time_label = 'Seconds since first transaction'
                is_numeric_time = True
            else:
                df_temp[time_col] = pd.to_datetime(df_temp[time_col], errors='coerce')
                df_temp = df_temp.dropna(subset=[time_col])
                df_temp = df_temp.sort_values(time_col)
                time_use = time_col
                time_label = time_col
                is_numeric_time = False

            if len(df_temp) < 10:
                return {"error": "Dados insuficientes para análise temporal"}

            # Tendência (média móvel)
            window_size = min(30, max(3, len(df_temp)//10))
            df_temp['moving_avg'] = df_temp[value_col].rolling(window=window_size, min_periods=1).mean()

            # Regressão simples sobre o índice (mantendo a unidade de tempo consistente quando for numérico)
            if is_numeric_time:
                x = df_temp[time_use].values.astype(float)
            else:
                x = np.arange(len(df_temp))
            y = df_temp[value_col].values
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

            # Sazonalidade simples (apenas faz sentido quando time não é apenas segundos decorrido ou quando há datetime real)
            seasonal_pattern = None
            if (not is_numeric_time) and len(df_temp) > 50:
                try:
                    df_temp['month'] = df_temp[time_use].dt.month
                    monthly_avg = df_temp.groupby('month')[value_col].mean()
                    seasonal_pattern = monthly_avg.to_dict()
                except Exception:
                    seasonal_pattern = None

            return {
                "has_trend": True,
                "data": df_temp,
                "start": float(df_temp[time_use].min()) if is_numeric_time else str(df_temp[time_use].min()),
                "end": float(df_temp[time_use].max()) if is_numeric_time else str(df_temp[time_use].max()),
                "time_label": time_label,
                "mean_value": float(df_temp[value_col].mean()),
                "trend_analysis": {
                    "slope": float(slope),
                    "r_squared": float(r_value**2),
                    "p_value": float(p_value),
                    "trend_direction": "crescente" if slope > 0 else "decrescente" if slope < 0 else "estável"
                },
                "seasonal_pattern": seasonal_pattern,
                "data_points": len(df_temp)
            }
        except Exception as e:
            logger.error(f"Erro na análise temporal: {e}")
            return {"error": f"Erro na análise temporal: {str(e)}"}

    def analyze_distribution(self, column: str) -> Dict[str, Any]:
        """Análise detalhada de distribuição de uma variável"""
        try:
            if column not in self.metadata['numeric_cols']:
                return {"error": f"Coluna {column} não é numérica"}
            
            data = self.df[column].dropna()
            if len(data) < 10:
                return {"error": "Dados insuficientes para análise de distribuição"}
            
            # Teste de normalidade
            shapiro_stat, shapiro_p = stats.shapiro(data) if len(data) <= 5000 else (None, None)
            ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
            
            # Análise de assimetria e curtose
            skewness = stats.skew(data)
            kurtosis = stats.kurtosis(data)
            
            # Classificação da distribuição
            distribution_type = self._classify_distribution(skewness, kurtosis)
            
            return {
                "column": column,
                "distribution_type": distribution_type,
                "statistics": {
                    "mean": float(data.mean()),
                    "median": float(data.median()),
                    "mode": float(data.mode().iloc[0]) if len(data.mode()) > 0 else None,
                    "std": float(data.std()),
                    "variance": float(data.var()),
                    "skewness": float(skewness),
                    "kurtosis": float(kurtosis),
                    "range": float(data.max() - data.min()),
                    "iqr": float(data.quantile(0.75) - data.quantile(0.25))
                },
                "normality_tests": {
                    "shapiro_wilk": {"statistic": float(shapiro_stat) if shapiro_stat else None, 
                                       "p_value": float(shapiro_p) if shapiro_p else None},
                    "kolmogorov_smirnov": {"statistic": float(ks_stat), "p_value": float(ks_p)}
                },
                "percentiles": {
                    "p5": float(data.quantile(0.05)),
                    "p25": float(data.quantile(0.25)),
                    "p50": float(data.quantile(0.50)),
                    "p75": float(data.quantile(0.75)),
                    "p95": float(data.quantile(0.95))
                }
            }
        except Exception as e:
            logger.error(f"Erro na análise de distribuição: {e}")
            return {"error": f"Erro na análise de distribuição: {str(e)}"}
    
    def _classify_distribution(self, skewness: float, kurtosis: float) -> str:
        """Classifica o tipo de distribuição baseado em assimetria e curtose"""
        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return "normal"
        elif skewness > 0.5:
            return "positivamente assimétrica"
        elif skewness < -0.5:
            return "negativamente assimétrica"
        elif kurtosis > 0.5:
            return "leptocúrtica (picos altos)"
        elif kurtosis < -0.5:
            return "platicúrtica (picos baixos)"
        else:
            return "distribuição mista"
    
    def perform_pca_analysis(self) -> Dict[str, Any]:
        """Análise de Componentes Principais"""
        try:
            numeric_cols = self.metadata['numeric_cols']
            if len(numeric_cols) < 3:
                return {"error": "PCA requer pelo menos 3 variáveis numéricas"}
            
            # Preparar dados
            data = self.df[numeric_cols].dropna()
            if len(data) < 10:
                return {"error": "Dados insuficientes para PCA"}
            
            # Normalizar dados
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)
            
            # PCA
            pca = PCA(n_components=PCA_COMPONENTS)
            pca_result = pca.fit_transform(data_scaled)
            
            # Componentes principais
            components = pd.DataFrame(
                pca.components_.T,
                columns=[f'PC{i+1}' for i in range(pca.components_.shape[0])],
                index=numeric_cols
            )
            
            return {
                "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                "cumulative_variance": np.cumsum(pca.explained_variance_ratio_).tolist(),
                "n_components": pca.n_components_,
                "components": components.to_dict(),
                "total_variance_explained": float(np.sum(pca.explained_variance_ratio_)),
                "recommendation": self._pca_recommendation(pca.explained_variance_ratio_)
            }
        except Exception as e:
            logger.error(f"Erro na análise PCA: {e}")
            return {"error": f"Erro na análise PCA: {str(e)}"}
    
    def _pca_recommendation(self, explained_variance: np.ndarray) -> str:
        """Gera recomendação baseada na análise PCA"""
        if len(explained_variance) <= 2:
            return "Dataset tem poucas dimensões para redução significativa"
        elif explained_variance[0] > 0.8:
            return "Primeira componente explica mais de 80% da variância - possível redundância nos dados"
        elif np.sum(explained_variance[:2]) > 0.7:
            return "Duas componentes principais explicam mais de 70% da variância"
        else:
            return "Dataset tem estrutura multidimensional complexa"
    
    def analyze_missing_data_patterns(self) -> Dict[str, Any]:
        """Analisa padrões de dados faltantes"""
        try:
            missing_data = self.df.isnull()
            
            # Padrões de missing data
            missing_patterns = {}
            for col in self.df.columns:
                if missing_data[col].sum() > 0:
                    missing_patterns[col] = {
                        "count": int(missing_data[col].sum()),
                        "percentage": float(missing_data[col].sum() / len(self.df) * 100),
                        "type": "MCAR" if missing_data[col].sum() < len(self.df) * 0.05 else "MAR"
                    }
            
            # Correlação entre missing values
            missing_corr = missing_data.corr()
            
            return {
                "missing_by_column": missing_patterns,
                "total_missing": int(missing_data.sum().sum()),
                "missing_percentage": float(missing_data.sum().sum() / self.df.size * 100),
                "columns_with_missing": [col for col in self.df.columns if missing_data[col].sum() > 0],
                "complete_cases": int(len(self.df.dropna())),
                "complete_cases_percentage": float(len(self.df.dropna()) / len(self.df) * 100),
                "missing_correlation_matrix": missing_corr.to_dict() if len(missing_corr) > 0 else {}
            }
        except Exception as e:
            logger.error(f"Erro na análise de missing data: {e}")
            return {"error": f"Erro na análise de missing data: {str(e)}"}
    
    def suggest_analyses(self) -> List[Dict[str,str]]:
        """Sugere análises baseadas nas características do dataset"""
        suggestions = []
        
        # Sugestões baseadas no tipo de dados
        if len(self.metadata['numeric_cols']) >= 2:
            suggestions.append({
                "analysis": "correlation",
                "title": "Análise de Correlação",
                "description": "Identificar relações entre variáveis numéricas",
                "priority": "alta"
            })
        
        if len(self.metadata['numeric_cols']) >= 1:
            suggestions.append({
                "analysis": "distribution",
                "title": "Análise de Distribuições",
                "description": "Verificar normalidade e características das distribuições",
                "priority": "média"
            })
        
        if len(self.metadata['numeric_cols']) >= 3:
            suggestions.append({
                "analysis": "pca",
                "title": "Análise de Componentes Principais",
                "description": "Reduzir dimensionalidade e identificar padrões",
                "priority": "média"
            })
        
        # Sugestões baseadas na qualidade dos dados
        if self.metadata['data_quality']['missing_cells'] > 0:
            suggestions.append({
                "analysis": "missing_patterns",
                "title": "Análise de Dados Faltantes",
                "description": "Identificar padrões nos valores faltantes",
                "priority": "alta"
            })
        
        if self.metadata['data_quality']['duplicate_rows'] > 0:
            suggestions.append({
                "analysis": "duplicates",
                "title": "Análise de Duplicatas",
                "description": "Investigar registros duplicados",
                "priority": "média"
            })
        
        return suggestions


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
            "created_at": datetime.now().isoformat(),
            "selected_model": None
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

    def save_selected_model(self, model_name: str):
        """Persiste o modelo selecionado na memória da sessão"""
        self.memory['selected_model'] = model_name
        self._persist()

    def get_context_summary(self) -> str:
        """Retorna resumo do contexto para a LLM"""
        num_queries = len(self.memory['queries'])
        # linha segura: a string é fechada corretamente e contém \n para nova linha
        summary = f"Análises anteriores realizadas: {num_queries}\n"

        if self.memory.get('insights'):
            summary += "\nÚltimos insights descobertos:\n"
            for insight in self.memory['insights'][-3:]:
                cat = insight.get('category', 'geral')
                text = insight.get('insight', '')
                # cada linha adicionada é formatada e terminada com \\n
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
    
    def list_models(self) -> List[str]:
        """Lista modelos disponíveis via API OpenAI. Retorna lista de nomes (strings)."""
        try:
            resp = self.client.models.list()
            models = []
            # A resposta pode variar de acordo com a versão do SDK
            if hasattr(resp, 'data'):
                for m in resp.data:
                    # cada item geralmente tem um 'id' ou 'model'
                    if isinstance(m, dict):
                        name = m.get('id') or m.get('model')
                    else:
                        name = getattr(m, 'id', None) or getattr(m, 'model', None)
                    if name:
                        models.append(name)
            elif isinstance(resp, list):
                for m in resp:
                    if isinstance(m, dict):
                        name = m.get('id') or m.get('model')
                    else:
                        name = getattr(m, 'id', None) or getattr(m, 'model', None)
                    if name:
                        models.append(name)
            return sorted(list(set(models)))
        except Exception as e:
            logger.warning(f"Não foi possível listar modelos: {e}")
            # fallback para lista padrão
            return [self.model]

    def set_model(self, model_name: str):
        """Define o modelo a ser usado nas chamadas subsequentes"""
        self.model = model_name

    def interpret_query(self, question: str, metadata: Dict, context: str) -> Dict[str, Any]:
        """Interpreta a pergunta e determina qual análise executar"""
        
        # PROMPT MELHORADO: explicita o layout do dataset com ênfase em datasets tipo 'creditcardfraud'
        system_prompt = """Você é um assistente especialista em análise de dados.
Analise a pergunta do usuário e determine qual tipo de análise deve ser executada.

Descrição importante (quando presente):
- Time: número de segundos desde a primeira transação (variável temporal contínua; **NUMÉRICA**). **NUNCA** interprete essa coluna como um timestamp Unix (1970-01-01). Quando "Time" for numérica, trate-a como segundos decorrido desde a primeira transação e indique que o eixo X deve estar em segundos (ou em formato decorrido legível, ex: HH:MM:SS). 
- V1 a V28: componentes gerados por PCA (dimensões reduzidas)
- Amount: valor da transação (numérico)
- Class: indicador (0 = normal, 1 = fraudulenta)

Retorne APENAS um JSON válido com a seguinte estrutura:
{
    "analysis_type": "correlation" | "anomaly" | "distribution" | "temporal" | "summary" | "conclusion" | "pca" | "missing_patterns" | "suggestions",
    "parameters": {
        "column": "nome_da_coluna" (se aplicável),
        "columns": ["col1","col2"] (opcional — quando pedir distribuições de várias colunas),
        "method": "iqr" | "zscore" | "isolation_forest" (para anomalias),
        "time_column": "coluna_temporal" (para análise temporal),
        "value_column": "coluna_valor" (para análise temporal)
    },
    "reasoning": "breve explicação"
}

Instruções adicionais:
- Se o usuário perguntar sobre todas as distribuições ou sobre 'variáveis numéricas', retorne parameters.columns com a lista de colunas numéricas ou a string "ALL_NUMERIC".
- Seja objetivo no campo 'reasoning'.
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

Determine qual análise executar e preencha o JSON conforme instruções do sistema."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            # A API pode retornar diretamente o objeto JSON se configurada; tentar parse seguro
            raw = response.choices[0].message.content
            if isinstance(raw, dict):
                return raw
            try:
                return json.loads(raw)
            except Exception:
                return {"analysis_type": "summary", "parameters": {}, "reasoning": "Fallback: resposta não-JSON"}
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
        """Gera gráfico temporal
        Observação: se a coluna temporal for numérica (tempo em segundos desde a primeira transação),
        o eixo X será exibido em segundos (tempo decorrido) e NÃO será convertido para Unix epoch (1970).
        """
        fig = go.Figure()

        # Detectar se eixo temporal é numérico (segundos) ou datetime
        try:
            if pd.api.types.is_numeric_dtype(df_temp[time_col]):
                x_vals = df_temp[time_col]
                x_title = 'Seconds since first transaction'
            else:
                x_vals = df_temp[time_col]
                x_title = time_col
        except Exception:
            x_vals = df_temp[time_col]
            x_title = time_col

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=df_temp[value_col],
            mode='lines',
            name='Valores'
        ))

        if 'moving_avg' in df_temp.columns:
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=df_temp['moving_avg'],
                mode='lines',
                name='Média Móvel',
                line=dict(dash='dash')
            ))

        fig.update_layout(
            title=f'Análise Temporal: {value_col}',
            xaxis_title=x_title,
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


def validate_file_size(file_size_bytes: int) -> bool:
    """Valida se o arquivo está dentro do limite de tamanho"""
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return file_size_bytes <= max_size_bytes

def validate_csv_file(uploaded_file) -> Tuple[bool, str]:
    """Valida se o arquivo CSV é válido"""
    try:
        # Verificar tamanho
        file_size = len(uploaded_file.getvalue())
        if not validate_file_size(file_size):
            return False, ERROR_MESSAGES["file_too_large"]
        
        # Tentar ler o CSV
        uploaded_file.seek(0)  # Reset file pointer
        test_df = pd.read_csv(uploaded_file, nrows=5)
        uploaded_file.seek(0)  # Reset again
        
        if test_df.empty:
            return False, ERROR_MESSAGES["empty_dataset"]
        
        return True, "Arquivo válido"
    except Exception as e:
        logger.error(f"Erro na validação do CSV: {e}")
        return False, ERROR_MESSAGES["invalid_csv"]

def main():
    st.set_page_config(**PAGE_CONFIG)
    
    st.title("🤖 Agente Autônomo de Análise Exploratória de Dados")
    st.markdown("*Framework: OpenAI GPT-4o-mini + Streamlit*")
    
    # Sidebar - configuração e informações
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
        
        st.divider()
        
        # Informações do sistema
        st.header("📊 Informações do Sistema")
        st.info(f"""
        **Limites do Sistema:**
        - Tamanho máximo: {MAX_FILE_SIZE_MB}MB
        - Colunas máximas: {MAX_COLUMNS_FOR_ANALYSIS}
        - Preview máximo: {MAX_ROWS_PREVIEW} linhas
        """)
        
        # Estatísticas de sessão
        if 'session_stats' in st.session_state:
            st.header("📈 Estatísticas da Sessão")
            stats = st.session_state.session_stats
            st.metric("Análises Realizadas", stats.get('analyses_count', 0))
            st.metric("Insights Gerados", stats.get('insights_count', 0))
            st.metric("Tempo de Sessão", f"{stats.get('session_time', 0):.1f} min")
    
    # Upload na área principal
    st.divider()
    
    # Seção de upload com validação
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📁 Faça upload de um arquivo CSV para começar",
            type=['csv'],
            help=f"Carregue um dataset em formato CSV (máximo {MAX_FILE_SIZE_MB}MB)"
        )
    
    with col2:
        if uploaded_file:
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.metric("Tamanho", f"{file_size_mb:.1f} MB")
    
    if not uploaded_file:
        st.info("👆 Faça upload de um arquivo CSV para começar")
        
        # Mostrar exemplos de perguntas
        st.subheader("💡 Exemplos de Perguntas")
        example_questions = [
            "Existe correlação entre as variáveis numéricas?",
            "Quais são os outliers na coluna Amount?",
            "Como está distribuída a variável Amount?",
            "Há padrões nos dados faltantes?",
            "Quais são as principais componentes dos dados?",
            "Gere sugestões de análises para este dataset"
        ]
        
        for i, question in enumerate(example_questions, 1):
            st.write(f"{i}. {question}")
        
        st.stop()
    
    # Validar arquivo
    is_valid, validation_message = validate_csv_file(uploaded_file)
    
    if not is_valid:
        st.error(f"❌ {validation_message}")
        st.stop()
    
    # Carregar dados com progress bar
    file_content = uploaded_file.getvalue()
    session_id = generate_session_id(file_content)
    
    @st.cache_data
    def load_data(content):
        return pd.read_csv(content)
    
    with st.spinner("Carregando dados..."):
        try:
            df = load_data(uploaded_file)
            
            # Inicializar estatísticas de sessão
            if 'session_stats' not in st.session_state:
                st.session_state.session_stats = {
                    'analyses_count': 0,
                    'insights_count': 0,
                    'session_start': datetime.now(),
                    'session_time': 0
                }
            
            st.success(f"✅ Dataset carregado: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
            
            # Mostrar informações do dataset
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Linhas", f"{df.shape[0]:,}")
            with col2:
                st.metric("Colunas", df.shape[1])
            with col3:
                numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                st.metric("Numéricas", numeric_cols)
            with col4:
                missing_pct = (df.isnull().sum().sum() / df.size) * 100
                st.metric("Missing %", f"{missing_pct:.1f}%")
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            st.error(f"❌ Erro ao carregar: {str(e)}")
            with st.expander("Detalhes do erro"):
                st.code(traceback.format_exc())
            st.stop()
    
    # Inicializar componentes
    analyzer = DataAnalyzer(df, session_id)
    memory_mgr = MemoryManager(session_id)
    llm_processor = LLMQueryProcessor(api_key)
    chart_gen = ChartGenerator()

    # -------------------------------
    # Seletor de Modelo LLM (sidebar)
    # -------------------------------
    with st.sidebar:
        st.header("🤖 Modelo da LLM")
        # Carregar seleção prévia (memória)
        saved_model = memory_mgr.memory.get('selected_model', llm_processor.model)
        if 'selected_model' not in st.session_state:
            st.session_state['selected_model'] = saved_model

        # Função para carregar modelos (faz GET via OpenAI client)
        def _fetch_models():
            try:
                models = llm_processor.list_models()
                st.session_state['available_models'] = models
                return models
            except Exception as e:
                st.error(f"Erro ao listar modelos: {e}")
                return [st.session_state['selected_model']]

        if st.button("🔄 Carregar modelos disponíveis"):
            with st.spinner("Buscando modelos..."):
                _fetch_models()

        available = st.session_state.get('available_models', [st.session_state['selected_model']])
        try:
            default_index = available.index(st.session_state['selected_model']) if st.session_state['selected_model'] in available else 0
        except Exception:
            default_index = 0
        selected_model = st.selectbox("Escolha um modelo para usar nas análises:", options=available, index=default_index)

        if st.button("💾 Salvar modelo selecionado"):
            st.session_state['selected_model'] = selected_model
            try:
                llm_processor.set_model(selected_model)
                memory_mgr.save_selected_model(selected_model)
                st.success(f"Modelo salvo: {selected_model}")
            except Exception as e:
                st.error(f"Erro ao salvar modelo: {e}")

        st.caption("Clique em 'Carregar modelos' para obter a lista de modelos disponíveis via API OpenAI.")
    
    # Tabs melhoradas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🔍 Análise Interativa", 
        "🎯 Análises Sugeridas",
        "💡 Memória",
        "📝 Conclusões"
    ])
    
    with tab1:
        st.subheader("📊 Resumo Estatístico")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Linhas", f"{df.shape[0]:,}")
        with col2:
            st.metric("Colunas", df.shape[1])
        with col3:
            st.metric("Numéricas", len(analyzer.metadata['numeric_cols']))
        with col4:
            st.metric("Categóricas", len(analyzer.metadata['categorical_cols']))
        
        # Qualidade dos dados
        st.subheader("🔍 Qualidade dos Dados")
        quality = analyzer.metadata['data_quality']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Completude", f"{quality['completeness']:.1f}%")
        with col2:
            st.metric("Valores Faltantes", f"{quality['missing_cells']:,}")
        with col3:
            st.metric("Duplicatas", f"{quality['duplicate_rows']:,}")
        
        # Preview dos dados
        st.subheader("👀 Preview dos Dados")
        
        # Controles para preview (corrigido para não ocorrer erro quando df tem poucas linhas)
        col1, col2 = st.columns([1, 3])
        with col1:
            max_rows = min(MAX_ROWS_PREVIEW, len(df))
            preview_rows = st.slider("Linhas para mostrar", 5, max_rows, min(20, max_rows))
            show_all_cols = st.checkbox("Mostrar todas as colunas", value=False)
        
        with col2:
            if show_all_cols:
                preview_df = df.head(preview_rows)
            else:
                preview_df = df.head(preview_rows).iloc[:, :10]  # Primeiras 10 colunas
            
            st.dataframe(preview_df, use_container_width=True)
        
        # Estatísticas descritivas
        st.subheader("📈 Estatísticas Descritivas")
        
        numeric_cols = analyzer.metadata['numeric_cols']
        if numeric_cols:
            st.dataframe(df[numeric_cols].describe(), use_container_width=True)
        else:
            st.info("Nenhuma coluna numérica encontrada para estatísticas descritivas")
        
        # Informações sobre tipos de dados
        st.subheader("📋 Informações dos Tipos de Dados")
        
        dtype_info = pd.DataFrame({
            'Coluna': df.columns,
            'Tipo': df.dtypes.astype(str),
            'Valores Únicos': df.nunique(),
            'Valores Faltantes': df.isnull().sum(),
            '% Faltantes': (df.isnull().sum() / len(df) * 100).round(2)
        })
        
        st.dataframe(dtype_info, use_container_width=True)
    
    with tab2:
        st.subheader("💬 Análise Interativa")
        
        # Sugestões rápidas
        st.subheader("🚀 Sugestões Rápidas")
        quick_actions = st.columns(3)
        
        with quick_actions[0]:
            if st.button("🔗 Análise de Correlação", use_container_width=True):
                st.session_state.quick_question = "Existe correlação entre as variáveis numéricas?"
        
        with quick_actions[1]:
            if st.button("📊 Distribuições", use_container_width=True):
                st.session_state.quick_question = "Como estão distribuídas as variáveis numéricas?"
        
        with quick_actions[2]:
            if st.button("🔍 Outliers", use_container_width=True):
                st.session_state.quick_question = "Quais são os outliers nas variáveis numéricas?"
        
        # Área de pergunta
        st.subheader("💭 Sua Pergunta")
        
        # Usar pergunta rápida se disponível
        default_question = st.session_state.get('quick_question', '')
        if default_question:
            st.session_state.quick_question = ''  # Limpar após usar
        
        question = st.text_area(
            "Descreva o que você gostaria de analisar:",
            placeholder="Ex: Existe correlação? Quais outliers em Amount? Há padrões nos dados faltantes?",
            height=100,
            value=default_question
        )
        
        # Seleção de colunas para análises específicas
        if analyzer.metadata['numeric_cols']:
            st.subheader("🎯 Análise Específica")
            
            col1, col2 = st.columns(2)
            with col1:
                selected_column = st.selectbox(
                    "Selecione uma coluna numérica:",
                    options=[''] + analyzer.metadata['numeric_cols'],
                    help="Escolha uma coluna para análises específicas"
                )
            
            with col2:
                if selected_column:
                    analysis_type = st.selectbox(
                        "Tipo de análise:",
                        options=['Distribuição', 'Outliers', 'Estatísticas'],
                        help="Tipo de análise para a coluna selecionada"
                    )
                    
                    if st.button("🔍 Analisar Coluna", use_container_width=True):
                        if analysis_type == 'Distribuição':
                            question = f"Analise a distribuição da coluna {selected_column}"
                        elif analysis_type == 'Outliers':
                            question = f"Identifique outliers na coluna {selected_column}"
                        else:
                            question = f"Mostre estatísticas detalhadas da coluna {selected_column}"
        
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
                        
                        analysis_type = interpretation.get('analysis_type', 'summary')
                        params = interpretation.get('parameters', {}) or {}
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
                            col = params.get('column')
                            if col and col in analyzer.metadata['numeric_cols']:
                                method = params.get('method', 'iqr')
                                result = analyzer.detect_anomalies(col, method=method)
                            else:
                                result = {"error": "Especifique o parâmetro 'column' para detecção de anomalias."}
                        
                        elif analysis_type == 'distribution':
                            # Suporte a análise de uma coluna, múltiplas colunas ou todas as numéricas
                            cols_param = params.get('column') or params.get('columns') or []
                            if isinstance(cols_param, str) and cols_param == 'ALL_NUMERIC':
                                cols = analyzer.metadata['numeric_cols']
                            elif isinstance(cols_param, str) and cols_param:
                                cols = [cols_param]
                            elif isinstance(cols_param, list) and len(cols_param) > 0:
                                cols = cols_param
                            else:
                                # fallback: todas as numéricas (limitado a 6 para performance)
                                cols = analyzer.metadata['numeric_cols'][:6]
                            
                            charts = []
                            distributions_summary = []
                            for c in cols:
                                if c in analyzer.metadata['numeric_cols']:
                                    distributions_summary.append(analyzer.analyze_distribution(c))
                                    charts.append(chart_gen.plot_distribution(df[c], c))
                            
                            if charts:
                                for fig in charts:
                                    st.plotly_chart(fig, use_container_width=True)
                                result = {"columns": cols, "status": "Gráficos gerados", "count": len(charts)}
                            else:
                                result = {"error": "Nenhuma coluna válida encontrada para distribuição."}
                        
                        elif analysis_type == 'temporal':
                            params = interpretation.get('parameters', {})
                            time_col = params.get('time_column')
                            value_col = params.get('value_column')
                            if time_col and value_col:
                                result = analyzer.temporal_analysis(time_col, value_col)
                                if 'data' in result:
                                    # identificar qual coluna temporal foi usada (pode ter sido convertida internamente)
                                    time_used = '__time_dt' if '__time_dt' in result['data'].columns else time_col
                                    chart = chart_gen.plot_temporal(
                                        result['data'], time_used, value_col
                                    )
                            else:
                                result = {"error": "Especifique time_column e value_column para análise temporal."}
                        
                        elif analysis_type == 'pca':
                            result = analyzer.perform_pca_analysis()
                            if 'components' in result:
                                # Criar gráfico de variância explicada
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=[f'PC{i+1}' for i in range(len(result['explained_variance_ratio']))],
                                    y=result['explained_variance_ratio'],
                                    name='Variância Explicada'
                                ))
                                fig.add_trace(go.Scatter(
                                    x=[f'PC{i+1}' for i in range(len(result['cumulative_variance']))],
                                    y=result['cumulative_variance'],
                                    mode='lines+markers',
                                    name='Variância Acumulada',
                                    yaxis='y2'
                                ))
                                fig.update_layout(
                                    title='Análise de Componentes Principais',
                                    xaxis_title='Componentes',
                                    yaxis_title='Variância Explicada',
                                    yaxis2=dict(title='Variância Acumulada', overlaying='y', side='right'),
                                    height=500
                                )
                                chart = fig
                        
                        elif analysis_type == 'missing_patterns':
                            result = analyzer.analyze_missing_data_patterns()
                            if 'missing_by_column' in result:
                                # Criar gráfico de missing data
                                missing_df = pd.DataFrame([
                                    {'Coluna': col, 'Valores Faltantes': info['count'], 'Percentual': info['percentage']}
                                    for col, info in result['missing_by_column'].items()
                                ])
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=missing_df['Coluna'],
                                    y=missing_df['Percentual'],
                                    text=missing_df['Valores Faltantes'],
                                    texttemplate='%{text}<br>%{y:.1f}%',
                                    textposition='outside'
                                ))
                                fig.update_layout(
                                    title='Padrões de Dados Faltantes',
                                    xaxis_title='Colunas',
                                    yaxis_title='Percentual de Valores Faltantes',
                                    height=400
                                )
                                chart = fig
                        
                        elif analysis_type == 'suggestions':
                            suggestions = analyzer.suggest_analyses()
                            result = {"suggestions": suggestions}
                            st.success("💡 Sugestões de Análises")
                            
                            for i, suggestion in enumerate(suggestions, 1):
                                priority_color = "🔴" if suggestion['priority'] == 'alta' else "🟡" if suggestion['priority'] == 'média' else "🟢"
                                st.write(f"{i}. {priority_color} **{suggestion['title']}**")
                                st.write(f"   {suggestion['description']}")
                                st.write("---")
                        
                        elif analysis_type == 'conclusion':
                            conclusion = llm_processor.generate_conclusions(
                                memory_mgr.memory, analyzer.metadata
                            )
                            st.success("📋 Conclusões Gerais")
                            st.write(conclusion)
                            memory_mgr.save_conclusion(conclusion)
                            result = {"done": True}
                        
                        # Gerar insight se houver resultado
                        if result and analysis_type not in ['conclusion', 'suggestions']:
                            if 'error' in result:
                                st.error(result['error'])
                            else:
                                insight = llm_processor.generate_insight(result, question)
                                st.success("✨ Resposta")
                                st.write(insight)
                                memory_mgr.save_query(question, insight, analysis_type)
                                memory_mgr.save_insight(insight, analysis_type)
                                
                                # Atualizar estatísticas
                                if 'session_stats' in st.session_state:
                                    st.session_state.session_stats['analyses_count'] += 1
                                    st.session_state.session_stats['insights_count'] += 1
                        
                        # Mostrar gráfico (quando retornado como chart)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        
                    except Exception as e:
                        logger.error(f"Erro durante análise: {e}")
                        st.error(f"❌ Erro durante análise: {str(e)}")
                        with st.expander("Ver detalhes do erro"):
                            st.code(traceback.format_exc())
    
    with tab3:
        st.subheader("🎯 Análises Sugeridas")
        
        # Obter sugestões
        suggestions = analyzer.suggest_analyses()
        
        if suggestions:
            st.info(f"💡 Encontramos {len(suggestions)} análises recomendadas para seu dataset")
            
            # Agrupar por prioridade
            high_priority = [s for s in suggestions if s['priority'] == 'alta']
            medium_priority = [s for s in suggestions if s['priority'] == 'média']
            low_priority = [s for s in suggestions if s['priority'] == 'baixa']
            
            # Mostrar análises de alta prioridade
            if high_priority:
                st.subheader("🔴 Alta Prioridade")
                for i, suggestion in enumerate(high_priority, 1):
                    with st.expander(f"{i}. {suggestion['title']}"):
                        st.write(f"**Descrição:** {suggestion['description']}")
                        st.write(f"**Tipo:** {suggestion['analysis']}")
                        
                        if st.button(f"Executar {suggestion['title']}", key=f"exec_{suggestion['analysis']}"):
                            # Simular execução da análise
                            st.info(f"Executando {suggestion['title']}...")
                            # Aqui você pode chamar a análise diretamente
            
            # Mostrar análises de média prioridade
            if medium_priority:
                st.subheader("🟡 Média Prioridade")
                for i, suggestion in enumerate(medium_priority, 1):
                    with st.expander(f"{i}. {suggestion['title']}"):
                        st.write(f"**Descrição:** {suggestion['description']}")
                        st.write(f"**Tipo:** {suggestion['analysis']}")
            
            # Mostrar análises de baixa prioridade
            if low_priority:
                st.subheader("🟢 Baixa Prioridade")
                for i, suggestion in enumerate(low_priority, 1):
                    with st.expander(f"{i}. {suggestion['title']}"):
                        st.write(f"**Descrição:** {suggestion['description']}")
                        st.write(f"**Tipo:** {suggestion['analysis']}")
        else:
            st.info("Nenhuma análise específica sugerida para este dataset")
        
        # Análises automáticas disponíveis
        st.subheader("🔧 Análises Automáticas Disponíveis")
        
        auto_analyses = [
            {"name": "Análise de Correlação", "description": "Identifica relações entre variáveis numéricas", "icon": "🔗"},
            {"name": "Análise de Distribuições", "description": "Verifica normalidade e características das distribuições", "icon": "📊"},
            {"name": "Detecção de Outliers", "description": "Identifica valores atípicos usando múltiplos métodos", "icon": "🔍"},
            {"name": "Análise PCA", "description": "Reduz dimensionalidade e identifica componentes principais", "icon": "📈"},
            {"name": "Padrões de Missing Data", "description": "Analisa padrões nos dados faltantes", "icon": "❓"},
            {"name": "Análise Temporal", "description": "Identifica tendências e sazonalidade", "icon": "⏰"}
        ]
        
        cols = st.columns(2)
        for i, analysis in enumerate(auto_analyses):
            with cols[i % 2]:
                st.write(f"{analysis['icon']} **{analysis['name']}**")
                st.caption(analysis['description'])
    
    with tab4:
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
    
    with tab5:
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
