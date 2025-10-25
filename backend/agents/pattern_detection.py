"""
Advanced pattern detection and adaptive learning module
for the AI Categorization Agent
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

# Core imports
from models.fiscal_data import FiscalDocument, NFEData, NFSEData, DocumentType
from utils.logging import get_agent_logger

# ML imports
try:
    import pandas as pd
    import numpy as np
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score
    from scipy import stats
    HAS_ML_DEPENDENCIES = True
except ImportError:
    HAS_ML_DEPENDENCIES = False

@dataclass
class Pattern:
    """Represents a detected pattern in fiscal data"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    first_detected: datetime
    last_detected: datetime
    context: Dict[str, Any]
    impact_score: float = 0.0
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"

@dataclass
class TrendAnalysis:
    """Represents trend analysis results"""
    metric: str
    trend_direction: str
    slope: float
    r_squared: float
    significance: float
    forecast_next_period: Optional[float] = None

class PatternDetectionEngine:
    """
    Advanced pattern detection engine for fiscal data analysis
    
    Capabilities:
    - Time series pattern detection
    - Supplier behavior analysis
    - Product/service trend identification
    - Tax optimization pattern recognition
    - Anomaly detection
    - Adaptive learning from new patterns
    """
    
    def __init__(self, agent_name: str = "PatternDetectionEngine"):
        self.logger = get_agent_logger(agent_name)
        
        if not HAS_ML_DEPENDENCIES:
            self.logger.warning("ML dependencies not available, using simplified pattern detection")
        
        # Pattern storage
        self.detected_patterns: List[Pattern] = []
        self.pattern_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Adaptive learning components
        self.learning_rate = 0.1
        self.pattern_threshold = 0.7
        self.min_pattern_frequency = 3
        
        # Data storage for analysis
        self.historical_data: List[Dict[str, Any]] = []
        self.supplier_profiles: Dict[str, Dict[str, Any]] = {}
        self.product_trends: Dict[str, List[float]] = defaultdict(list)
        self.service_trends: Dict[str, List[float]] = defaultdict(list)
        
        # Pattern types
        self.pattern_types = {
            "supplier_behavior": "Padrão de Comportamento do Fornecedor",
            "seasonal_trend": "Tendência Sazonal",
            "price_volatility": "Volatilidade de Preços",
            "volume_pattern": "Padrão de Volume",
            "tax_optimization": "Otimização Tributária",
            "geographic_pattern": "Padrão Geográfico",
            "product_lifecycle": "Ciclo de Vida do Produto",
            "payment_pattern": "Padrão de Pagamento",
            "anomaly": "Anomalia Detectada"
        }
    
    async def detect_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """
        Main pattern detection method
        
        Args:
            fiscal_documents: List of fiscal documents to analyze
            
        Returns:
            List of detected patterns
        """
        self.logger.info("Starting pattern detection", document_count=len(fiscal_documents))
        
        try:
            # Update historical data
            await self._update_historical_data(fiscal_documents)
            
            # Detect different types of patterns
            patterns = []
            
            # Supplier behavior patterns
            supplier_patterns = await self._detect_supplier_patterns(fiscal_documents)
            patterns.extend(supplier_patterns)
            
            # Time-based patterns
            temporal_patterns = await self._detect_temporal_patterns(fiscal_documents)
            patterns.extend(temporal_patterns)
            
            # Price and volume patterns
            economic_patterns = await self._detect_economic_patterns(fiscal_documents)
            patterns.extend(economic_patterns)
            
            # Tax optimization patterns
            tax_patterns = await self._detect_tax_patterns(fiscal_documents)
            patterns.extend(tax_patterns)
            
            # Geographic patterns
            geographic_patterns = await self._detect_geographic_patterns(fiscal_documents)
            patterns.extend(geographic_patterns)
            
            # Anomaly detection
            anomalies = await self._detect_anomalies(fiscal_documents)
            patterns.extend(anomalies)
            
            # Update pattern storage
            self.detected_patterns.extend(patterns)
            
            # Adaptive learning
            await self._adaptive_learning_update(patterns)
            
            self.logger.info("Pattern detection completed", patterns_found=len(patterns))
            return patterns
            
        except Exception as e:
            self.logger.error("Error in pattern detection", error=str(e))
            return []
    
    async def _update_historical_data(self, fiscal_documents: List[FiscalDocument]):
        """Update historical data for pattern analysis"""
        for doc in fiscal_documents:
            doc_data = {
                'document_id': getattr(doc, 'chave_nfe', getattr(doc, 'id_nfse', 'unknown')),
                'document_type': doc.document_type.value,
                'date': doc.data_emissao,
                'supplier_cnpj': doc.supplier.cnpj,
                'supplier_name': doc.supplier.razao_social,
                'supplier_uf': doc.supplier.address.uf,
                'total_value': getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0)),
                'timestamp': datetime.now()
            }
            
            # Add document-specific data
            if doc.document_type == DocumentType.NFE:
                doc_data.update({
                    'product_count': len(doc.items) if doc.items else 0,
                    'icms_value': getattr(doc, 'valor_icms', 0),
                    'ipi_value': getattr(doc, 'valor_total_ipi', 0)
                })
            elif doc.document_type == DocumentType.NFSE:
                doc_data.update({
                    'service_count': len(doc.services) if doc.services else 0,
                    'issqn_value': getattr(doc, 'valor_issqn', 0)
                })
            
            self.historical_data.append(doc_data)
    
    async def _detect_supplier_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect supplier behavior patterns"""
        patterns = []
        
        try:
            # Group documents by supplier
            supplier_data = defaultdict(list)
            for doc in fiscal_documents:
                if doc.supplier.cnpj:
                    supplier_data[doc.supplier.cnpj].append(doc)
            
            for supplier_cnpj, docs in supplier_data.items():
                if len(docs) < self.min_pattern_frequency:
                    continue
                
                # Analyze supplier patterns
                supplier_patterns = await self._analyze_supplier_behavior(supplier_cnpj, docs)
                patterns.extend(supplier_patterns)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting supplier patterns", error=str(e))
            return []
    
    async def _analyze_supplier_behavior(self, supplier_cnpj: str, documents: List[FiscalDocument]) -> List[Pattern]:
        """Analyze behavior patterns for a specific supplier"""
        patterns = []
        
        try:
            # Calculate supplier metrics
            values = [getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0)) for doc in documents]
            dates = [doc.data_emissao for doc in documents]
            
            # Frequency pattern
            if len(documents) >= 10:  # Frequent supplier
                avg_interval = self._calculate_average_interval(dates)
                if avg_interval and avg_interval.days <= 30:  # Monthly or more frequent
                    pattern = Pattern(
                        pattern_id=f"supplier_frequent_{supplier_cnpj}",
                        pattern_type="supplier_behavior",
                        description=f"Fornecedor frequente - transações a cada {avg_interval.days} dias em média",
                        confidence=0.9,
                        frequency=len(documents),
                        first_detected=min(dates),
                        last_detected=max(dates),
                        context={
                            "supplier_cnpj": supplier_cnpj,
                            "transaction_count": len(documents),
                            "avg_interval_days": avg_interval.days,
                            "total_value": sum(values)
                        },
                        impact_score=0.8
                    )
                    patterns.append(pattern)
            
            # Value consistency pattern
            if len(values) >= 5:
                cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
                if cv < 0.2:  # Low coefficient of variation
                    pattern = Pattern(
                        pattern_id=f"supplier_consistent_{supplier_cnpj}",
                        pattern_type="supplier_behavior",
                        description=f"Fornecedor com valores consistentes (CV: {cv:.2f})",
                        confidence=0.8,
                        frequency=len(documents),
                        first_detected=min(dates),
                        last_detected=max(dates),
                        context={
                            "supplier_cnpj": supplier_cnpj,
                            "coefficient_variation": cv,
                            "avg_value": np.mean(values),
                            "std_value": np.std(values)
                        },
                        impact_score=0.6
                    )
                    patterns.append(pattern)
            
            # Growth pattern
            if len(documents) >= 6:
                trend_analysis = await self._analyze_trend(dates, values)
                if trend_analysis and abs(trend_analysis.slope) > 0.1 and trend_analysis.r_squared > 0.5:
                    direction = "crescimento" if trend_analysis.slope > 0 else "declínio"
                    pattern = Pattern(
                        pattern_id=f"supplier_trend_{supplier_cnpj}",
                        pattern_type="supplier_behavior",
                        description=f"Fornecedor em {direction} - tendência {trend_analysis.trend_direction}",
                        confidence=trend_analysis.r_squared,
                        frequency=len(documents),
                        first_detected=min(dates),
                        last_detected=max(dates),
                        context={
                            "supplier_cnpj": supplier_cnpj,
                            "trend_slope": trend_analysis.slope,
                            "r_squared": trend_analysis.r_squared,
                            "trend_direction": trend_analysis.trend_direction
                        },
                        impact_score=0.7,
                        trend_direction=trend_analysis.trend_direction
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error analyzing supplier behavior", error=str(e), supplier_cnpj=supplier_cnpj)
            return []
    
    async def _detect_temporal_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect time-based patterns (seasonal, cyclical, etc.)"""
        patterns = []
        
        try:
            if not fiscal_documents:
                return patterns
            
            # Group by month for seasonal analysis
            monthly_data = defaultdict(list)
            for doc in fiscal_documents:
                month_key = doc.data_emissao.strftime("%m")
                value = getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0))
                monthly_data[month_key].append(float(value))
            
            # Detect seasonal patterns
            if len(monthly_data) >= 6:  # At least 6 months of data
                monthly_averages = {month: np.mean(values) for month, values in monthly_data.items()}
                
                # Calculate coefficient of variation across months
                avg_values = list(monthly_averages.values())
                if len(avg_values) >= 3:
                    cv = np.std(avg_values) / np.mean(avg_values) if np.mean(avg_values) > 0 else 0
                    
                    if cv > 0.3:  # Significant seasonal variation
                        peak_month = max(monthly_averages, key=monthly_averages.get)
                        low_month = min(monthly_averages, key=monthly_averages.get)
                        
                        pattern = Pattern(
                            pattern_id="seasonal_variation",
                            pattern_type="seasonal_trend",
                            description=f"Variação sazonal detectada - pico em {peak_month}, baixa em {low_month}",
                            confidence=min(cv, 1.0),
                            frequency=len(fiscal_documents),
                            first_detected=min(doc.data_emissao for doc in fiscal_documents),
                            last_detected=max(doc.data_emissao for doc in fiscal_documents),
                            context={
                                "coefficient_variation": cv,
                                "peak_month": peak_month,
                                "low_month": low_month,
                                "monthly_averages": monthly_averages
                            },
                            impact_score=0.7
                        )
                        patterns.append(pattern)
            
            # Detect weekly patterns
            weekly_data = defaultdict(list)
            for doc in fiscal_documents:
                weekday = doc.data_emissao.strftime("%A")
                value = getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0))
                weekly_data[weekday].append(float(value))
            
            if len(weekly_data) >= 5:  # At least 5 different weekdays
                weekday_counts = {day: len(values) for day, values in weekly_data.items()}
                total_docs = sum(weekday_counts.values())
                
                # Check for concentration on specific weekdays
                max_day_count = max(weekday_counts.values())
                if max_day_count / total_docs > 0.4:  # More than 40% on one day
                    peak_day = max(weekday_counts, key=weekday_counts.get)
                    
                    pattern = Pattern(
                        pattern_id="weekly_concentration",
                        pattern_type="temporal_pattern",
                        description=f"Concentração de transações em {peak_day} ({max_day_count/total_docs:.1%})",
                        confidence=0.8,
                        frequency=len(fiscal_documents),
                        first_detected=min(doc.data_emissao for doc in fiscal_documents),
                        last_detected=max(doc.data_emissao for doc in fiscal_documents),
                        context={
                            "peak_weekday": peak_day,
                            "concentration_percentage": max_day_count / total_docs,
                            "weekday_distribution": weekday_counts
                        },
                        impact_score=0.5
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting temporal patterns", error=str(e))
            return []
    
    async def _detect_economic_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect price and volume patterns"""
        patterns = []
        
        try:
            # Analyze price volatility
            values = []
            dates = []
            
            for doc in fiscal_documents:
                value = getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0))
                if value > 0:
                    values.append(float(value))
                    dates.append(doc.data_emissao)
            
            if len(values) >= 10:
                # Calculate price volatility
                returns = np.diff(np.log(values))
                volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
                
                if volatility > 0.5:  # High volatility threshold
                    pattern = Pattern(
                        pattern_id="high_price_volatility",
                        pattern_type="price_volatility",
                        description=f"Alta volatilidade de preços detectada (σ: {volatility:.2f})",
                        confidence=0.8,
                        frequency=len(values),
                        first_detected=min(dates),
                        last_detected=max(dates),
                        context={
                            "volatility": volatility,
                            "avg_value": np.mean(values),
                            "max_value": max(values),
                            "min_value": min(values)
                        },
                        impact_score=0.9
                    )
                    patterns.append(pattern)
            
            # Analyze volume patterns for NFE documents
            nfe_docs = [doc for doc in fiscal_documents if doc.document_type == DocumentType.NFE]
            if nfe_docs:
                item_counts = []
                for doc in nfe_docs:
                    if hasattr(doc, 'items') and doc.items:
                        item_counts.append(len(doc.items))
                
                if len(item_counts) >= 5:
                    avg_items = np.mean(item_counts)
                    if avg_items > 10:  # High volume threshold
                        pattern = Pattern(
                            pattern_id="high_volume_transactions",
                            pattern_type="volume_pattern",
                            description=f"Transações de alto volume - média de {avg_items:.1f} itens por NF-e",
                            confidence=0.7,
                            frequency=len(item_counts),
                            first_detected=min(doc.data_emissao for doc in nfe_docs),
                            last_detected=max(doc.data_emissao for doc in nfe_docs),
                            context={
                                "avg_items_per_invoice": avg_items,
                                "max_items": max(item_counts),
                                "total_nfe_count": len(nfe_docs)
                            },
                            impact_score=0.6
                        )
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting economic patterns", error=str(e))
            return []
    
    async def _detect_tax_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect tax optimization patterns"""
        patterns = []
        
        try:
            # Analyze CFOP patterns for NFE documents
            nfe_docs = [doc for doc in fiscal_documents if doc.document_type == DocumentType.NFE]
            if nfe_docs:
                cfop_usage = defaultdict(int)
                interstate_count = 0
                total_nfe = len(nfe_docs)
                
                for doc in nfe_docs:
                    if hasattr(doc, 'items') and doc.items:
                        for item in doc.items:
                            if item.produto.cfop:
                                cfop_usage[item.produto.cfop] += 1
                    
                    # Check for interstate transactions
                    if (hasattr(doc, 'uf_emitente') and 
                        doc.uf_emitente != doc.recipient.address.uf):
                        interstate_count += 1
                
                # Detect interstate transaction pattern
                if interstate_count / total_nfe > 0.3:  # More than 30% interstate
                    pattern = Pattern(
                        pattern_id="interstate_transactions",
                        pattern_type="tax_optimization",
                        description=f"Alto percentual de transações interestaduais ({interstate_count/total_nfe:.1%})",
                        confidence=0.8,
                        frequency=interstate_count,
                        first_detected=min(doc.data_emissao for doc in nfe_docs),
                        last_detected=max(doc.data_emissao for doc in nfe_docs),
                        context={
                            "interstate_percentage": interstate_count / total_nfe,
                            "interstate_count": interstate_count,
                            "total_nfe": total_nfe
                        },
                        impact_score=0.8
                    )
                    patterns.append(pattern)
                
                # Detect CFOP concentration patterns
                if cfop_usage:
                    most_used_cfop = max(cfop_usage, key=cfop_usage.get)
                    cfop_concentration = cfop_usage[most_used_cfop] / sum(cfop_usage.values())
                    
                    if cfop_concentration > 0.6:  # More than 60% using same CFOP
                        pattern = Pattern(
                            pattern_id=f"cfop_concentration_{most_used_cfop}",
                            pattern_type="tax_optimization",
                            description=f"Concentração no CFOP {most_used_cfop} ({cfop_concentration:.1%})",
                            confidence=0.7,
                            frequency=cfop_usage[most_used_cfop],
                            first_detected=min(doc.data_emissao for doc in nfe_docs),
                            last_detected=max(doc.data_emissao for doc in nfe_docs),
                            context={
                                "dominant_cfop": most_used_cfop,
                                "concentration_percentage": cfop_concentration,
                                "cfop_distribution": dict(cfop_usage)
                            },
                            impact_score=0.6
                        )
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting tax patterns", error=str(e))
            return []
    
    async def _detect_geographic_patterns(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect geographic patterns in transactions"""
        patterns = []
        
        try:
            # Analyze supplier geographic distribution
            uf_distribution = defaultdict(int)
            region_distribution = defaultdict(int)
            
            for doc in fiscal_documents:
                supplier_uf = doc.supplier.address.uf
                if supplier_uf:
                    uf_distribution[supplier_uf] += 1
                    region = self._get_region_from_uf(supplier_uf)
                    region_distribution[region] += 1
            
            total_docs = len(fiscal_documents)
            
            # Detect regional concentration
            if region_distribution:
                dominant_region = max(region_distribution, key=region_distribution.get)
                region_concentration = region_distribution[dominant_region] / total_docs
                
                if region_concentration > 0.7:  # More than 70% from one region
                    pattern = Pattern(
                        pattern_id=f"regional_concentration_{dominant_region}",
                        pattern_type="geographic_pattern",
                        description=f"Concentração regional em {dominant_region} ({region_concentration:.1%})",
                        confidence=0.8,
                        frequency=region_distribution[dominant_region],
                        first_detected=min(doc.data_emissao for doc in fiscal_documents),
                        last_detected=max(doc.data_emissao for doc in fiscal_documents),
                        context={
                            "dominant_region": dominant_region,
                            "concentration_percentage": region_concentration,
                            "region_distribution": dict(region_distribution)
                        },
                        impact_score=0.6
                    )
                    patterns.append(pattern)
            
            # Detect state concentration
            if uf_distribution:
                dominant_uf = max(uf_distribution, key=uf_distribution.get)
                uf_concentration = uf_distribution[dominant_uf] / total_docs
                
                if uf_concentration > 0.5:  # More than 50% from one state
                    pattern = Pattern(
                        pattern_id=f"state_concentration_{dominant_uf}",
                        pattern_type="geographic_pattern",
                        description=f"Concentração estadual em {dominant_uf} ({uf_concentration:.1%})",
                        confidence=0.8,
                        frequency=uf_distribution[dominant_uf],
                        first_detected=min(doc.data_emissao for doc in fiscal_documents),
                        last_detected=max(doc.data_emissao for doc in fiscal_documents),
                        context={
                            "dominant_uf": dominant_uf,
                            "concentration_percentage": uf_concentration,
                            "uf_distribution": dict(uf_distribution)
                        },
                        impact_score=0.5
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting geographic patterns", error=str(e))
            return []
    
    async def _detect_anomalies(self, fiscal_documents: List[FiscalDocument]) -> List[Pattern]:
        """Detect anomalies in fiscal data"""
        patterns = []
        
        try:
            if not fiscal_documents:
                return patterns
            
            # Value-based anomaly detection
            values = []
            for doc in fiscal_documents:
                value = getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0))
                if value > 0:
                    values.append(float(value))
            
            if len(values) >= 10:
                # Use IQR method for outlier detection
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                outliers = [v for v in values if v < lower_bound or v > upper_bound]
                
                if len(outliers) > 0:
                    outlier_percentage = len(outliers) / len(values)
                    
                    if outlier_percentage > 0.05:  # More than 5% outliers
                        pattern = Pattern(
                            pattern_id="value_anomalies",
                            pattern_type="anomaly",
                            description=f"Anomalias de valor detectadas ({outlier_percentage:.1%} dos documentos)",
                            confidence=0.9,
                            frequency=len(outliers),
                            first_detected=min(doc.data_emissao for doc in fiscal_documents),
                            last_detected=max(doc.data_emissao for doc in fiscal_documents),
                            context={
                                "outlier_count": len(outliers),
                                "outlier_percentage": outlier_percentage,
                                "q1": q1,
                                "q3": q3,
                                "iqr": iqr,
                                "max_outlier": max(outliers),
                                "min_outlier": min(outliers)
                            },
                            impact_score=0.8
                        )
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting anomalies", error=str(e))
            return []
    
    async def _adaptive_learning_update(self, new_patterns: List[Pattern]):
        """Update learning models based on newly detected patterns"""
        try:
            for pattern in new_patterns:
                # Update pattern history
                pattern_key = f"{pattern.pattern_type}_{pattern.pattern_id}"
                
                pattern_data = {
                    'pattern': asdict(pattern),
                    'timestamp': datetime.now(),
                    'confidence': pattern.confidence,
                    'frequency': pattern.frequency
                }
                
                self.pattern_history[pattern_key].append(pattern_data)
                
                # Adaptive learning: adjust thresholds based on pattern frequency
                if len(self.pattern_history[pattern_key]) >= 5:
                    # Calculate average confidence for this pattern type
                    confidences = [p['confidence'] for p in self.pattern_history[pattern_key]]
                    avg_confidence = np.mean(confidences)
                    
                    # Adjust threshold based on learning
                    if avg_confidence > 0.8:
                        # Lower threshold for well-established patterns
                        self.pattern_threshold = max(0.5, self.pattern_threshold - self.learning_rate * 0.1)
                    elif avg_confidence < 0.6:
                        # Raise threshold for uncertain patterns
                        self.pattern_threshold = min(0.9, self.pattern_threshold + self.learning_rate * 0.1)
            
            self.logger.info("Adaptive learning update completed", 
                           new_patterns=len(new_patterns),
                           current_threshold=self.pattern_threshold)
            
        except Exception as e:
            self.logger.error("Error in adaptive learning update", error=str(e))
    
    # Helper methods
    def _calculate_average_interval(self, dates: List[datetime]) -> Optional[timedelta]:
        """Calculate average interval between dates"""
        if len(dates) < 2:
            return None
        
        sorted_dates = sorted(dates)
        intervals = []
        
        for i in range(1, len(sorted_dates)):
            interval = sorted_dates[i] - sorted_dates[i-1]
            intervals.append(interval)
        
        if intervals:
            total_seconds = sum(interval.total_seconds() for interval in intervals)
            avg_seconds = total_seconds / len(intervals)
            return timedelta(seconds=avg_seconds)
        
        return None
    
    async def _analyze_trend(self, dates: List[datetime], values: List[float]) -> Optional[TrendAnalysis]:
        """Analyze trend in time series data"""
        try:
            if len(dates) != len(values) or len(dates) < 3:
                return None
            
            # Convert dates to numeric values (days since first date)
            first_date = min(dates)
            x = [(date - first_date).days for date in dates]
            y = values
            
            # Perform linear regression
            if HAS_ML_DEPENDENCIES:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # Determine trend direction
                if abs(slope) < 0.01:
                    trend_direction = "stable"
                elif slope > 0:
                    trend_direction = "increasing"
                else:
                    trend_direction = "decreasing"
                
                return TrendAnalysis(
                    metric="value_trend",
                    trend_direction=trend_direction,
                    slope=slope,
                    r_squared=r_value**2,
                    significance=p_value
                )
            else:
                # Simple trend calculation without scipy
                if len(x) >= 2:
                    slope = (y[-1] - y[0]) / (x[-1] - x[0]) if x[-1] != x[0] else 0
                    
                    if abs(slope) < 0.01:
                        trend_direction = "stable"
                    elif slope > 0:
                        trend_direction = "increasing"
                    else:
                        trend_direction = "decreasing"
                    
                    return TrendAnalysis(
                        metric="value_trend",
                        trend_direction=trend_direction,
                        slope=slope,
                        r_squared=0.5,  # Default value
                        significance=0.05  # Default value
                    )
            
            return None
            
        except Exception as e:
            self.logger.error("Error analyzing trend", error=str(e))
            return None
    
    def _get_region_from_uf(self, uf: str) -> str:
        """Get Brazilian region from UF"""
        regions = {
            # Norte
            "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", 
            "RO": "Norte", "RR": "Norte", "TO": "Norte",
            # Nordeste
            "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
            "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
            # Centro-Oeste
            "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste", "DF": "Centro-Oeste",
            # Sudeste
            "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
            # Sul
            "PR": "Sul", "RS": "Sul", "SC": "Sul"
        }
        
        return regions.get(uf.upper(), "Não Identificado")
    
    # Public methods for external access
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of detected patterns"""
        if not self.detected_patterns:
            return {"total_patterns": 0, "pattern_types": {}}
        
        pattern_type_counts = Counter(p.pattern_type for p in self.detected_patterns)
        
        return {
            "total_patterns": len(self.detected_patterns),
            "pattern_types": dict(pattern_type_counts),
            "avg_confidence": np.mean([p.confidence for p in self.detected_patterns]),
            "high_impact_patterns": len([p for p in self.detected_patterns if p.impact_score > 0.7]),
            "recent_patterns": len([p for p in self.detected_patterns 
                                 if (datetime.now() - p.last_detected).days <= 30])
        }
    
    def get_patterns_by_type(self, pattern_type: str) -> List[Pattern]:
        """Get patterns filtered by type"""
        return [p for p in self.detected_patterns if p.pattern_type == pattern_type]
    
    def get_high_impact_patterns(self, min_impact: float = 0.7) -> List[Pattern]:
        """Get patterns with high impact scores"""
        return [p for p in self.detected_patterns if p.impact_score >= min_impact]
    
    async def save_patterns(self, file_path: str):
        """Save detected patterns to file"""
        try:
            patterns_data = [asdict(p) for p in self.detected_patterns]
            
            # Convert datetime objects to strings for JSON serialization
            for pattern_data in patterns_data:
                pattern_data['first_detected'] = pattern_data['first_detected'].isoformat()
                pattern_data['last_detected'] = pattern_data['last_detected'].isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info("Patterns saved successfully", file_path=file_path, count=len(patterns_data))
            
        except Exception as e:
            self.logger.error("Error saving patterns", error=str(e), file_path=file_path)
    
    async def load_patterns(self, file_path: str):
        """Load patterns from file"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning("Pattern file not found", file_path=file_path)
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            
            self.detected_patterns = []
            for pattern_data in patterns_data:
                # Convert string dates back to datetime objects
                pattern_data['first_detected'] = datetime.fromisoformat(pattern_data['first_detected'])
                pattern_data['last_detected'] = datetime.fromisoformat(pattern_data['last_detected'])
                
                pattern = Pattern(**pattern_data)
                self.detected_patterns.append(pattern)
            
            self.logger.info("Patterns loaded successfully", file_path=file_path, count=len(self.detected_patterns))
            
        except Exception as e:
            self.logger.error("Error loading patterns", error=str(e), file_path=file_path)