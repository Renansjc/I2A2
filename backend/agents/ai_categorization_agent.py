"""
LLM-Enhanced AI Categorization Agent for intelligent fiscal data classification
Implements LLM-powered categorization with business context understanding for products, services and suppliers
"""

import asyncio
import pickle
import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal
from collections import defaultdict, Counter

# Core imports
from .base_agent import BaseAgent
from .pattern_detection import PatternDetectionEngine, Pattern
from models.fiscal_data import (
    FiscalDocument, NFEData, NFSEData, Product, Service, Supplier,
    CategorizedFiscalData, DocumentType
)
from utils.openai_integration import get_openai_service, BusinessInsights, CategorizationResult

# ML and NLP imports
try:
    import pandas as pd
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    from sklearn.preprocessing import LabelEncoder
    import spacy
    from spacy.lang.pt import Portuguese
    HAS_ML_DEPENDENCIES = True
except ImportError as e:
    HAS_ML_DEPENDENCIES = False
    ML_IMPORT_ERROR = str(e)

class AICategorization_Agent(BaseAgent):
    """
    Agente de categorização alimentado por IA para documentos fiscais
    
    Capacidades:
    - Categorização de produtos usando classificadores NLP e ML
    - Categorização de serviços usando códigos CNAE e NBS
    - Classificação de fornecedores por tipo, região e relacionamento comercial
    - Detecção de padrões e aprendizado adaptativo
    """
    
    def __init__(self):
        super().__init__("AI_Categorization_Agent")
        
        # Verificar dependências de ML
        if not HAS_ML_DEPENDENCIES:
            self.logger.error(
                "ML dependencies not available", 
                error=ML_IMPORT_ERROR,
                required_packages=["pandas", "scikit-learn", "spacy"]
            )
            raise ImportError(f"Required ML packages not installed: {ML_IMPORT_ERROR}")
        
        # Inicializar modelos e componentes de ML
        self.product_classifier = None
        self.service_classifier = None
        self.supplier_classifier = None
        self.text_vectorizer = None
        self.label_encoders = {}
        
        # Componentes de NLP
        self.nlp = None
        
        # Caminhos de armazenamento dos modelos
        self.models_dir = "models/ml_models"
        self.product_model_path = os.path.join(self.models_dir, "product_classifier.pkl")
        self.service_model_path = os.path.join(self.models_dir, "service_classifier.pkl")
        self.supplier_model_path = os.path.join(self.models_dir, "supplier_classifier.pkl")
        self.vectorizer_path = os.path.join(self.models_dir, "text_vectorizer.pkl")
        
        # Categorias predefinidas e mapeamentos
        self.product_categories = self._load_product_categories()
        self.service_categories = self._load_service_categories()
        self.supplier_categories = self._load_supplier_categories()
        
        # Motor de detecção de padrões
        self.pattern_engine = PatternDetectionEngine("AI_Categorization_Pattern_Engine")
        
        # Armazenamento de detecção de padrões
        self.detected_patterns = []
        self.pattern_history = []
        
        # LLM Integration Service
        self.llm_service = None
        
    async def initialize(self):
        """Inicializar o agente de categorização IA com capacidades LLM"""
        self.logger.info("Initializing LLM-Enhanced AI Categorization Agent")
        
        try:
            # Create models directory if it doesn't exist
            os.makedirs(self.models_dir, exist_ok=True)
            
            # Initialize LLM service
            self.llm_service = get_openai_service()
            
            # Initialize spaCy NLP pipeline
            await self._initialize_nlp()
            
            # Load or create ML models
            await self._load_or_create_models()
            
            self.logger.info("LLM-Enhanced AI Categorization Agent initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize LLM-Enhanced AI Categorization Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup agent resources"""
        self.logger.info("Cleaning up AI Categorization Agent")
        
        # Save models if they exist
        if self.product_classifier:
            await self._save_models()
        
        # Clear memory
        self.nlp = None
        self.product_classifier = None
        self.service_classifier = None
        self.supplier_classifier = None
    
    async def process(self, fiscal_data: FiscalDocument) -> CategorizedFiscalData:
        """
        Main processing method for categorizing fiscal data with LLM enhancement
        
        Args:
            fiscal_data: NFEData or NFSEData to be categorized
            
        Returns:
            CategorizedFiscalData with LLM-enhanced AI-generated classifications
        """
        self.logger.info(
            "Processing fiscal data for LLM-enhanced categorization",
            document_type=fiscal_data.document_type.value,
            document_id=getattr(fiscal_data, 'chave_nfe', getattr(fiscal_data, 'id_nfse', 'unknown'))
        )
        
        try:
            # Initialize result object
            result = CategorizedFiscalData(original_data=fiscal_data)
            
            # Prepare business context for LLM analysis
            business_context = {
                'supplier_info': {
                    'name': fiscal_data.supplier.razao_social if fiscal_data.supplier else '',
                    'cnpj': fiscal_data.supplier.cnpj if fiscal_data.supplier else '',
                    'state': fiscal_data.supplier.address.uf if fiscal_data.supplier and fiscal_data.supplier.address else ''
                },
                'business_sector': await self._determine_business_sector(fiscal_data),
                'document_context': {
                    'type': fiscal_data.document_type.value,
                    'date': fiscal_data.data_emissao.isoformat() if fiscal_data.data_emissao else '',
                    'value': float(getattr(fiscal_data, 'valor_total_nf', getattr(fiscal_data, 'valor_total_servicos', 0)))
                }
            }
            
            # Categorize based on document type using LLM-enhanced methods
            if fiscal_data.document_type == DocumentType.NFE:
                result = await self._process_nfe_data_with_llm(fiscal_data, result, business_context)
            elif fiscal_data.document_type == DocumentType.NFSE:
                result = await self._process_nfse_data_with_llm(fiscal_data, result, business_context)
            
            # Classify supplier using LLM analysis
            if fiscal_data.supplier:
                supplier_analysis = await self.analyze_supplier_relationships([fiscal_data.supplier])
                if supplier_analysis:
                    result.classified_supplier = supplier_analysis[0]['supplier']
                    result.supplier_analysis = supplier_analysis[0]
            
            # Detect patterns using LLM-enhanced analysis
            pattern_analysis = await self.detect_business_patterns([fiscal_data])
            result.detected_patterns = pattern_analysis.get('llm_insights', {}).get('key_findings', [])
            result.pattern_analysis = pattern_analysis
            
            # Calculate confidence scores
            result.confidence_scores = await self._calculate_confidence_scores(result)
            
            self.logger.info("LLM-enhanced fiscal data categorization completed successfully")
            return result
            
        except Exception as e:
            self.logger.error("Error processing fiscal data with LLM enhancement", error=str(e))
            # Fallback to traditional processing
            return await self._process_traditional(fiscal_data)
    
    async def _process_nfe_data_with_llm(
        self, 
        nfe_data: NFEData, 
        result: CategorizedFiscalData,
        business_context: Dict[str, Any]
    ) -> CategorizedFiscalData:
        """Process NFE data with LLM-enhanced product categorization"""
        if nfe_data.items:
            products = [item.produto for item in nfe_data.items]
            categorized_products = await self.categorize_products_with_context(
                products, business_context
            )
            result.categorized_products = categorized_products
        
        return result
    
    async def _process_nfse_data_with_llm(
        self, 
        nfse_data: NFSEData, 
        result: CategorizedFiscalData,
        business_context: Dict[str, Any]
    ) -> CategorizedFiscalData:
        """Process NFSE data with LLM-enhanced service categorization"""
        if nfse_data.services:
            # For services, we still use traditional categorization but could enhance with LLM
            categorized_services = []
            for service_item in nfse_data.services:
                categorized_service = await self._categorize_service(service_item.servico)
                categorized_services.append(categorized_service)
            result.categorized_services = categorized_services
        
        return result
    
    async def _determine_business_sector(self, fiscal_data: FiscalDocument) -> str:
        """Determine business sector from fiscal data"""
        # Simple heuristic based on document content
        if fiscal_data.document_type == DocumentType.NFE and hasattr(fiscal_data, 'items'):
            # Analyze product types to determine sector
            for item in fiscal_data.items:
                if item.produto.ncm:
                    ncm_prefix = item.produto.ncm[:2]
                    if ncm_prefix in ['01', '02', '03', '04']:
                        return 'Agronegócio'
                    elif ncm_prefix in ['84', '85']:
                        return 'Industrial'
                    elif ncm_prefix in ['87']:
                        return 'Automotivo'
        
        return 'Geral'
    
    async def _process_traditional(self, fiscal_data: FiscalDocument) -> CategorizedFiscalData:
        """Fallback to traditional processing without LLM"""
        self.logger.info("Using traditional processing as fallback")
        
        result = CategorizedFiscalData(original_data=fiscal_data)
        
        # Traditional categorization
        if fiscal_data.document_type == DocumentType.NFE:
            result = await self._process_nfe_data(fiscal_data, result)
        elif fiscal_data.document_type == DocumentType.NFSE:
            result = await self._process_nfse_data(fiscal_data, result)
        
        # Traditional supplier classification
        result.classified_supplier = await self._classify_supplier(fiscal_data.supplier)
        
        # Traditional pattern detection
        result.detected_patterns = await self._detect_patterns(fiscal_data)
        
        # Calculate confidence scores
        result.confidence_scores = await self._calculate_confidence_scores(result)
        
        return result
    
    async def _process_nfe_data(self, nfe_data: NFEData, result: CategorizedFiscalData) -> CategorizedFiscalData:
        """Process NFE data for product categorization"""
        if nfe_data.items:
            categorized_products = []
            for item in nfe_data.items:
                categorized_product = await self._categorize_product(item.produto)
                categorized_products.append(categorized_product)
            result.categorized_products = categorized_products
        
        return result
    
    async def _process_nfse_data(self, nfse_data: NFSEData, result: CategorizedFiscalData) -> CategorizedFiscalData:
        """Process NFSE data for service categorization"""
        if nfse_data.services:
            categorized_services = []
            for service_item in nfse_data.services:
                categorized_service = await self._categorize_service(service_item.servico)
                categorized_services.append(categorized_service)
            result.categorized_services = categorized_services
        
        return result
    
    async def _categorize_product(self, product: Product) -> Product:
        """
        Categorize a product using NLP and ML classifiers
        
        Args:
            product: Product to categorize
            
        Returns:
            Product with AI-generated category and subcategory
        """
        try:
            # Extract features for classification
            features = self._extract_product_features(product)
            
            # Use ML classifier if available
            if self.product_classifier and self.text_vectorizer:
                # Vectorize product description
                text_features = self.text_vectorizer.transform([features['description']])
                
                # Predict category
                predicted_category = self.product_classifier.predict(text_features)[0]
                product.category = predicted_category
                
                # Generate subcategory based on NCM and description
                product.subcategory = self._generate_product_subcategory(product)
            else:
                # Fallback to rule-based categorization
                product.category, product.subcategory = self._rule_based_product_categorization(product)
            
            self.logger.debug(
                "Product categorized",
                product_code=product.codigo_produto,
                category=product.category,
                subcategory=product.subcategory
            )
            
            return product
            
        except Exception as e:
            self.logger.error("Error categorizing product", error=str(e), product_code=product.codigo_produto)
            # Return product with default categories
            product.category = "Não Classificado"
            product.subcategory = "Geral"
            return product
    
    async def _categorize_service(self, service: Service) -> Service:
        """
        Categorize a service using CNAE and NBS codes
        
        Args:
            service: Service to categorize
            
        Returns:
            Service with AI-generated category and subcategory
        """
        try:
            # Use CNAE code for primary categorization
            if service.codigo_cnae:
                service.category = self._categorize_by_cnae(service.codigo_cnae)
            
            # Use NBS code for subcategorization
            if service.codigo_nbs:
                service.subcategory = self._categorize_by_nbs(service.codigo_nbs)
            
            # Fallback to description-based categorization
            if not service.category:
                service.category, service.subcategory = self._rule_based_service_categorization(service)
            
            self.logger.debug(
                "Service categorized",
                service_code=service.codigo_servico,
                category=service.category,
                subcategory=service.subcategory
            )
            
            return service
            
        except Exception as e:
            self.logger.error("Error categorizing service", error=str(e), service_code=service.codigo_servico)
            # Return service with default categories
            service.category = "Serviços Gerais"
            service.subcategory = "Não Especificado"
            return service
    
    async def _classify_supplier(self, supplier: Supplier) -> Supplier:
        """
        Classify supplier by type, region, and business relationship
        
        Args:
            supplier: Supplier to classify
            
        Returns:
            Supplier with AI-generated classifications
        """
        try:
            # Classify by region (based on UF from address)
            supplier.region = self._classify_supplier_region(supplier.address.uf)
            
            # Classify by business type (based on company name and CNAE patterns)
            supplier.category = self._classify_supplier_type(supplier)
            
            # Determine business relationship (frequency-based)
            supplier.business_relationship = await self._determine_business_relationship(supplier)
            
            self.logger.debug(
                "Supplier classified",
                supplier_cnpj=supplier.cnpj,
                category=supplier.category,
                region=supplier.region,
                relationship=supplier.business_relationship
            )
            
            return supplier
            
        except Exception as e:
            self.logger.error("Error classifying supplier", error=str(e), supplier_cnpj=supplier.cnpj)
            # Return supplier with default classifications
            supplier.category = "Fornecedor Geral"
            supplier.region = "Não Identificado"
            supplier.business_relationship = "Eventual"
            return supplier
    
    async def _detect_patterns(self, fiscal_data: FiscalDocument) -> List[str]:
        """
        Detect patterns and trends in fiscal data using advanced pattern detection engine
        
        Args:
            fiscal_data: Fiscal document to analyze
            
        Returns:
            List of detected pattern descriptions
        """
        try:
            # Use advanced pattern detection engine
            detected_patterns = await self.pattern_engine.detect_patterns([fiscal_data])
            
            # Convert Pattern objects to string descriptions
            pattern_descriptions = []
            for pattern in detected_patterns:
                pattern_descriptions.append(pattern.description)
                
                # Store pattern for adaptive learning
                await self.add_pattern(pattern.pattern_id, {
                    'type': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'impact_score': pattern.impact_score,
                    'context': pattern.context
                })
            
            # Add simple rule-based patterns for immediate detection
            simple_patterns = await self._detect_simple_patterns(fiscal_data)
            pattern_descriptions.extend(simple_patterns)
            
            return pattern_descriptions
            
        except Exception as e:
            self.logger.error("Error detecting patterns", error=str(e))
            return []
    
    async def _detect_simple_patterns(self, fiscal_data: FiscalDocument) -> List[str]:
        """
        Detect simple rule-based patterns for immediate feedback
        
        Args:
            fiscal_data: Fiscal document to analyze
            
        Returns:
            List of simple pattern descriptions
        """
        patterns = []
        
        try:
            # Pattern 1: High-value transactions
            total_value = getattr(fiscal_data, 'valor_total_nf', getattr(fiscal_data, 'valor_total_servicos', 0))
            if total_value > Decimal('10000'):
                patterns.append("high_value_transaction")
            
            # Pattern 2: Cross-state transaction
            if hasattr(fiscal_data, 'uf_emitente') and fiscal_data.uf_emitente != fiscal_data.recipient.address.uf:
                patterns.append("cross_state_transaction")
            
            # Pattern 3: Multiple product categories (for NFE)
            if fiscal_data.document_type == DocumentType.NFE and hasattr(fiscal_data, 'items'):
                categories = set()
                for item in fiscal_data.items:
                    if item.produto.category:
                        categories.add(item.produto.category)
                if len(categories) > 3:
                    patterns.append("diverse_product_mix")
            
            # Pattern 4: Weekend transaction
            if fiscal_data.data_emissao.weekday() >= 5:  # Saturday or Sunday
                patterns.append("weekend_transaction")
            
            # Pattern 5: Large quantity items (for NFE)
            if fiscal_data.document_type == DocumentType.NFE and hasattr(fiscal_data, 'items'):
                for item in fiscal_data.items:
                    if item.quantidade_comercial > 100:
                        patterns.append("large_quantity_item")
                        break
            
            return patterns
            
        except Exception as e:
            self.logger.error("Error detecting simple patterns", error=str(e))
            return []
    
    async def _calculate_confidence_scores(self, result: CategorizedFiscalData) -> Dict[str, float]:
        """Calculate confidence scores for categorizations"""
        scores = {}
        
        try:
            # Product categorization confidence
            if result.categorized_products:
                product_scores = []
                for product in result.categorized_products:
                    score = self._calculate_product_confidence(product)
                    product_scores.append(score)
                scores['products'] = np.mean(product_scores) if product_scores else 0.0
            
            # Service categorization confidence
            if result.categorized_services:
                service_scores = []
                for service in result.categorized_services:
                    score = self._calculate_service_confidence(service)
                    service_scores.append(score)
                scores['services'] = np.mean(service_scores) if service_scores else 0.0
            
            # Supplier classification confidence
            if result.classified_supplier:
                scores['supplier'] = self._calculate_supplier_confidence(result.classified_supplier)
            
            # Overall confidence
            all_scores = [score for score in scores.values() if score > 0]
            scores['overall'] = np.mean(all_scores) if all_scores else 0.0
            
            return scores
            
        except Exception as e:
            self.logger.error("Error calculating confidence scores", error=str(e))
            return {'overall': 0.0}
    
    # LLM-Enhanced Categorization Methods
    
    async def categorize_products_with_context(
        self, 
        products: List[Product],
        business_context: Dict[str, Any]
    ) -> List[Product]:
        """
        Intelligent product categorization using LLM business understanding
        
        Args:
            products: List of products to categorize
            business_context: Business context including supplier info, sector, etc.
            
        Returns:
            List of products with LLM-enhanced categorization
        """
        self.logger.info("Starting LLM-powered product categorization", 
                        product_count=len(products))
        
        try:
            categorized_products = []
            
            for product in products:
                # Prepare context for LLM
                llm_context = {
                    'description': product.descricao or '',
                    'ncm': product.ncm or '',
                    'cfop': product.cfop or '',
                    'unit': product.unidade_comercial or '',
                    'supplier_info': business_context.get('supplier_info', {}),
                    'usage_context': await self._get_product_usage_context(product.codigo_produto),
                    'market_category': await self._get_market_category(product.ncm),
                    'business_sector': business_context.get('business_sector', ''),
                    'existing_categories': await self._get_existing_categories(),
                    'categorization_rules': await self._get_business_rules()
                }
                
                # Use LLM for intelligent categorization
                if self.llm_service:
                    try:
                        categorization_result = await self.llm_service.categorize_with_context(
                            [product.descricao or ''], 
                            'product', 
                            llm_context
                        )
                        
                        # Extract categorization from LLM response
                        if categorization_result.categories:
                            category_info = categorization_result.categories[0]
                            product.category = category_info.get('category', 'Não Classificado')
                            product.subcategory = category_info.get('subcategory', 'Geral')
                            
                            # Store LLM reasoning for audit
                            if hasattr(product, 'categorization_reasoning'):
                                product.categorization_reasoning = categorization_result.reasoning
                        else:
                            # Fallback to traditional categorization
                            product.category, product.subcategory = self._rule_based_product_categorization(product)
                            
                    except Exception as e:
                        self.logger.warning("LLM categorization failed, using fallback", 
                                          error=str(e), product_code=product.codigo_produto)
                        product.category, product.subcategory = self._rule_based_product_categorization(product)
                else:
                    # Fallback to traditional categorization
                    product.category, product.subcategory = self._rule_based_product_categorization(product)
                
                categorized_products.append(product)
                
                self.logger.debug("Product categorized with LLM", 
                                product_code=product.codigo_produto,
                                category=product.category,
                                subcategory=product.subcategory)
            
            self.logger.info("LLM-powered product categorization completed", 
                           categorized_count=len(categorized_products))
            
            return categorized_products
            
        except Exception as e:
            self.logger.error("Error in LLM product categorization", error=str(e))
            # Fallback to traditional categorization
            return [await self._categorize_product(product) for product in products]
    
    async def analyze_supplier_relationships(
        self, 
        suppliers: List[Supplier]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to analyze supplier relationships and strategic importance
        
        Args:
            suppliers: List of suppliers to analyze
            
        Returns:
            List of supplier analysis results with LLM insights
        """
        self.logger.info("Starting LLM-powered supplier relationship analysis", 
                        supplier_count=len(suppliers))
        
        try:
            analyses = []
            
            for supplier in suppliers:
                # Prepare context for LLM analysis
                llm_context = {
                    'supplier_name': supplier.razao_social or '',
                    'cnpj': supplier.cnpj or '',
                    'transaction_history': await self._get_supplier_history(supplier.cnpj),
                    'market_position': await self._get_market_position(supplier),
                    'risk_factors': await self._get_risk_factors(supplier),
                    'strategic_importance': await self._calculate_strategic_importance(supplier)
                }
                
                if self.llm_service:
                    try:
                        # Generate insights using LLM
                        insights = await self.llm_service.generate_insights(
                            llm_context, 'supplier_relationship', 'executive'
                        )
                        
                        analysis = {
                            'supplier': supplier,
                            'relationship_classification': self._extract_relationship_classification(insights),
                            'risk_assessment': self._extract_risk_assessment(insights),
                            'growth_potential': self._extract_growth_potential(insights),
                            'strategic_recommendations': insights.strategic_implications,
                            'optimization_opportunities': self._extract_optimization_opportunities(insights),
                            'confidence_level': insights.confidence_level,
                            'key_insights': insights.key_findings
                        }
                        
                    except Exception as e:
                        self.logger.warning("LLM supplier analysis failed, using fallback", 
                                          error=str(e), supplier_cnpj=supplier.cnpj)
                        analysis = await self._fallback_supplier_analysis(supplier)
                else:
                    analysis = await self._fallback_supplier_analysis(supplier)
                
                analyses.append(analysis)
                
                self.logger.debug("Supplier analyzed with LLM", 
                                supplier_cnpj=supplier.cnpj,
                                relationship=analysis.get('relationship_classification'))
            
            self.logger.info("LLM-powered supplier relationship analysis completed", 
                           analyzed_count=len(analyses))
            
            return analyses
            
        except Exception as e:
            self.logger.error("Error in LLM supplier relationship analysis", error=str(e))
            return [await self._fallback_supplier_analysis(supplier) for supplier in suppliers]
    
    async def detect_business_patterns(
        self, 
        fiscal_data: List[FiscalDocument]
    ) -> Dict[str, Any]:
        """
        Use LLM to detect business patterns and trends with strategic impact analysis
        
        Args:
            fiscal_data: List of fiscal documents to analyze
            
        Returns:
            Dictionary with comprehensive pattern analysis and strategic insights
        """
        self.logger.info("Starting LLM-powered business pattern detection", 
                        document_count=len(fiscal_data))
        
        try:
            # Prepare comprehensive context for LLM analysis
            llm_context = {
                'documents_summary': await self._prepare_documents_summary(fiscal_data),
                'time_series_data': await self._prepare_time_series(fiscal_data),
                'market_trends': await self._get_market_trends(),
                'seasonal_patterns': await self._get_seasonal_patterns(),
                'business_cycles': await self._get_business_cycles()
            }
            
            if self.llm_service:
                try:
                    # Generate comprehensive business insights
                    insights = await self.llm_service.generate_insights(
                        llm_context, 'pattern_detection', 'executive'
                    )
                    
                    # Combine LLM insights with traditional pattern detection
                    traditional_patterns = await self._detect_traditional_patterns(fiscal_data)
                    
                    pattern_analysis = {
                        'llm_insights': {
                            'key_findings': insights.key_findings,
                            'trends_identified': insights.trends_identified,
                            'business_impact': insights.business_impact,
                            'strategic_implications': insights.strategic_implications,
                            'confidence_level': insights.confidence_level
                        },
                        'traditional_patterns': traditional_patterns,
                        'combined_recommendations': await self._combine_pattern_recommendations(
                            insights, traditional_patterns
                        ),
                        'risk_assessment': await self._assess_pattern_risks(insights, traditional_patterns),
                        'opportunity_identification': await self._identify_opportunities(insights),
                        'executive_summary': await self._generate_executive_pattern_summary(insights)
                    }
                    
                except Exception as e:
                    self.logger.warning("LLM pattern detection failed, using traditional methods", 
                                      error=str(e))
                    pattern_analysis = await self._fallback_pattern_detection(fiscal_data)
            else:
                pattern_analysis = await self._fallback_pattern_detection(fiscal_data)
            
            self.logger.info("LLM-powered business pattern detection completed", 
                           patterns_found=len(pattern_analysis.get('llm_insights', {}).get('key_findings', [])))
            
            return pattern_analysis
            
        except Exception as e:
            self.logger.error("Error in LLM business pattern detection", error=str(e))
            return await self._fallback_pattern_detection(fiscal_data)
    
    # Helper methods for LLM-enhanced functionality
    
    async def _get_product_usage_context(self, product_code: str) -> Dict[str, Any]:
        """Get product usage context from historical data"""
        # This would typically query database for historical usage patterns
        # For now, return placeholder data
        return {
            'frequency': 'regular',
            'seasonal_usage': 'stable',
            'business_purpose': 'operational'
        }
    
    async def _get_market_category(self, ncm: str) -> Dict[str, Any]:
        """Get market category information based on NCM"""
        if not ncm:
            return {'category': 'unknown', 'market_segment': 'general'}
        
        # Simplified NCM to market category mapping
        ncm_prefix = ncm[:2] if len(ncm) >= 2 else ""
        
        market_categories = {
            "01": {"category": "agribusiness", "market_segment": "primary"},
            "02": {"category": "food_industry", "market_segment": "consumer_goods"},
            "84": {"category": "machinery", "market_segment": "industrial"},
            "85": {"category": "electronics", "market_segment": "technology"},
            "87": {"category": "automotive", "market_segment": "transportation"}
        }
        
        return market_categories.get(ncm_prefix, {'category': 'general', 'market_segment': 'diverse'})
    
    async def _get_existing_categories(self) -> List[str]:
        """Get list of existing product categories"""
        return list(self.product_categories.keys())
    
    async def _get_business_rules(self) -> Dict[str, Any]:
        """Get business rules for categorization"""
        return {
            'prioritize_ncm': True,
            'consider_supplier_type': True,
            'use_business_context': True,
            'adaptive_learning': True
        }
    
    async def _get_supplier_history(self, cnpj: str) -> Dict[str, Any]:
        """Get supplier transaction history"""
        # This would typically query database for supplier history
        # For now, return placeholder data
        return {
            'total_transactions': 0,
            'avg_transaction_value': 0.0,
            'transaction_frequency': 'unknown',
            'payment_behavior': 'unknown',
            'relationship_duration': 'unknown'
        }
    
    async def _get_market_position(self, supplier: Supplier) -> Dict[str, Any]:
        """Get supplier market position information"""
        return {
            'market_share': 'unknown',
            'competitive_position': 'unknown',
            'growth_trend': 'stable',
            'market_reputation': 'unknown'
        }
    
    async def _get_risk_factors(self, supplier: Supplier) -> Dict[str, Any]:
        """Get supplier risk factors"""
        return {
            'financial_risk': 'low',
            'operational_risk': 'low',
            'compliance_risk': 'low',
            'geographic_risk': 'low'
        }
    
    async def _calculate_strategic_importance(self, supplier: Supplier) -> Dict[str, Any]:
        """Calculate supplier strategic importance"""
        return {
            'business_criticality': 'medium',
            'replacement_difficulty': 'medium',
            'cost_impact': 'medium',
            'innovation_potential': 'medium'
        }
    
    def _extract_relationship_classification(self, insights: BusinessInsights) -> str:
        """Extract relationship classification from LLM insights"""
        # Look for relationship keywords in insights
        key_findings = ' '.join(insights.key_findings).lower()
        
        if 'estratégico' in key_findings or 'crítico' in key_findings:
            return 'Estratégico'
        elif 'importante' in key_findings or 'relevante' in key_findings:
            return 'Importante'
        elif 'regular' in key_findings or 'padrão' in key_findings:
            return 'Regular'
        else:
            return 'Eventual'
    
    def _extract_risk_assessment(self, insights: BusinessInsights) -> str:
        """Extract risk assessment from LLM insights"""
        key_findings = ' '.join(insights.key_findings).lower()
        
        if 'alto risco' in key_findings or 'risco elevado' in key_findings:
            return 'Alto'
        elif 'médio risco' in key_findings or 'risco moderado' in key_findings:
            return 'Médio'
        else:
            return 'Baixo'
    
    def _extract_growth_potential(self, insights: BusinessInsights) -> str:
        """Extract growth potential from LLM insights"""
        trends = ' '.join(insights.trends_identified).lower()
        
        if 'crescimento' in trends or 'expansão' in trends:
            return 'Alto'
        elif 'estável' in trends or 'manutenção' in trends:
            return 'Médio'
        else:
            return 'Baixo'
    
    def _extract_optimization_opportunities(self, insights: BusinessInsights) -> List[str]:
        """Extract optimization opportunities from LLM insights"""
        return insights.strategic_implications[:3]  # Top 3 strategic implications
    
    async def _fallback_supplier_analysis(self, supplier: Supplier) -> Dict[str, Any]:
        """Fallback supplier analysis using traditional methods"""
        return {
            'supplier': supplier,
            'relationship_classification': 'A Definir',
            'risk_assessment': 'Médio',
            'growth_potential': 'Médio',
            'strategic_recommendations': ['Análise mais detalhada necessária'],
            'optimization_opportunities': ['Revisar histórico de transações'],
            'confidence_level': 0.5,
            'key_insights': ['Análise baseada em métodos tradicionais']
        }
    
    async def _prepare_documents_summary(self, fiscal_data: List[FiscalDocument]) -> Dict[str, Any]:
        """Prepare summary of fiscal documents for LLM analysis"""
        summary = {
            'total_documents': len(fiscal_data),
            'document_types': {},
            'total_value': 0.0,
            'date_range': {},
            'supplier_count': 0,
            'top_suppliers': [],
            'product_categories': {},
            'geographic_distribution': {}
        }
        
        suppliers = set()
        categories = defaultdict(int)
        states = defaultdict(int)
        
        for doc in fiscal_data:
            # Document type count
            doc_type = doc.document_type.value
            summary['document_types'][doc_type] = summary['document_types'].get(doc_type, 0) + 1
            
            # Total value
            total_value = getattr(doc, 'valor_total_nf', getattr(doc, 'valor_total_servicos', 0))
            summary['total_value'] += float(total_value) if total_value else 0.0
            
            # Suppliers
            if hasattr(doc, 'supplier') and doc.supplier:
                suppliers.add(doc.supplier.cnpj)
                states[doc.supplier.address.uf] += 1
            
            # Categories (for NFE)
            if doc.document_type == DocumentType.NFE and hasattr(doc, 'items'):
                for item in doc.items:
                    if hasattr(item.produto, 'category') and item.produto.category:
                        categories[item.produto.category] += 1
        
        summary['supplier_count'] = len(suppliers)
        summary['product_categories'] = dict(categories)
        summary['geographic_distribution'] = dict(states)
        
        # Date range
        if fiscal_data:
            dates = [doc.data_emissao for doc in fiscal_data if doc.data_emissao]
            if dates:
                summary['date_range'] = {
                    'start': min(dates).isoformat(),
                    'end': max(dates).isoformat()
                }
        
        return summary
    
    async def _detect_traditional_patterns(self, fiscal_data: List[FiscalDocument]) -> List[str]:
        """Detect patterns using traditional rule-based methods"""
        patterns = []
        
        # Use existing pattern detection logic
        for doc in fiscal_data:
            simple_patterns = await self._detect_simple_patterns(doc)
            patterns.extend(simple_patterns)
        
        # Remove duplicates and return unique patterns
        return list(set(patterns))
    
    async def _combine_pattern_recommendations(
        self, 
        llm_insights: BusinessInsights, 
        traditional_patterns: List[str]
    ) -> List[str]:
        """Combine LLM insights with traditional pattern recommendations"""
        recommendations = []
        
        # Add LLM strategic implications
        recommendations.extend(llm_insights.strategic_implications)
        
        # Add traditional pattern-based recommendations
        for pattern in traditional_patterns:
            if pattern == "high_value_transaction":
                recommendations.append("Revisar processos de aprovação para transações de alto valor")
            elif pattern == "cross_state_transaction":
                recommendations.append("Otimizar estratégia tributária para transações interestaduais")
            elif pattern == "diverse_product_mix":
                recommendations.append("Considerar especialização ou diversificação estratégica")
        
        # Remove duplicates and limit to top 10
        return list(set(recommendations))[:10]
    
    async def _assess_pattern_risks(
        self, 
        llm_insights: BusinessInsights, 
        traditional_patterns: List[str]
    ) -> Dict[str, Any]:
        """Assess risks based on detected patterns"""
        risks = {
            'financial_risks': [],
            'operational_risks': [],
            'compliance_risks': [],
            'strategic_risks': []
        }
        
        # Extract risks from LLM insights
        business_impact = llm_insights.business_impact
        if 'risks' in business_impact:
            risks['strategic_risks'].extend(business_impact['risks'])
        
        # Add risks based on traditional patterns
        for pattern in traditional_patterns:
            if pattern == "high_value_transaction":
                risks['financial_risks'].append("Exposição a transações de alto valor")
            elif pattern == "cross_state_transaction":
                risks['compliance_risks'].append("Complexidade tributária interestadual")
            elif pattern == "weekend_transaction":
                risks['operational_risks'].append("Operações fora do horário comercial")
        
        return risks
    
    async def _identify_opportunities(self, llm_insights: BusinessInsights) -> List[str]:
        """Identify business opportunities from LLM insights"""
        opportunities = []
        
        # Extract opportunities from trends and business impact
        for trend in llm_insights.trends_identified:
            if 'crescimento' in trend.lower():
                opportunities.append(f"Oportunidade de crescimento: {trend}")
            elif 'otimização' in trend.lower():
                opportunities.append(f"Oportunidade de otimização: {trend}")
        
        # Extract from business impact
        business_impact = llm_insights.business_impact
        if 'opportunities' in business_impact:
            opportunities.extend(business_impact['opportunities'])
        
        return opportunities[:5]  # Top 5 opportunities
    
    async def _generate_executive_pattern_summary(self, llm_insights: BusinessInsights) -> str:
        """Generate executive summary of pattern analysis"""
        key_points = []
        
        if llm_insights.key_findings:
            key_points.append(f"Principais descobertas: {', '.join(llm_insights.key_findings[:2])}")
        
        if llm_insights.trends_identified:
            key_points.append(f"Tendências identificadas: {', '.join(llm_insights.trends_identified[:2])}")
        
        if llm_insights.strategic_implications:
            key_points.append(f"Implicações estratégicas: {', '.join(llm_insights.strategic_implications[:2])}")
        
        return ". ".join(key_points) + "."
    
    async def _fallback_pattern_detection(self, fiscal_data: List[FiscalDocument]) -> Dict[str, Any]:
        """Fallback pattern detection using traditional methods"""
        traditional_patterns = await self._detect_traditional_patterns(fiscal_data)
        
        return {
            'llm_insights': {
                'key_findings': ['Análise baseada em métodos tradicionais'],
                'trends_identified': traditional_patterns,
                'business_impact': {'note': 'Análise limitada sem LLM'},
                'strategic_implications': ['Considerar implementar análise LLM para insights mais profundos'],
                'confidence_level': 0.6
            },
            'traditional_patterns': traditional_patterns,
            'combined_recommendations': ['Implementar análise LLM para melhor categorização'],
            'risk_assessment': {'note': 'Avaliação de risco limitada'},
            'opportunity_identification': ['Melhorar capacidades de análise'],
            'executive_summary': 'Análise realizada com métodos tradicionais. Recomenda-se implementar LLM para insights mais profundos.'
        }

    # Helper methods for ML model management
    async def _initialize_nlp(self):
        """Initialize spaCy NLP pipeline"""
        try:
            # Try to load Portuguese model
            try:
                self.nlp = spacy.load("pt_core_news_sm")
                self.logger.info("Loaded Portuguese spaCy model")
            except OSError:
                # Fallback to blank Portuguese model
                self.nlp = Portuguese()
                self.logger.warning("Portuguese spaCy model not found, using blank model")
                
        except Exception as e:
            self.logger.error("Failed to initialize NLP pipeline", error=str(e))
            raise
    
    async def _load_or_create_models(self):
        """Load existing ML models or create new ones"""
        try:
            # Try to load existing models
            if os.path.exists(self.product_model_path):
                with open(self.product_model_path, 'rb') as f:
                    self.product_classifier = pickle.load(f)
                self.logger.info("Loaded existing product classifier")
            
            if os.path.exists(self.vectorizer_path):
                with open(self.vectorizer_path, 'rb') as f:
                    self.text_vectorizer = pickle.load(f)
                self.logger.info("Loaded existing text vectorizer")
            
            # Create new models if they don't exist
            if not self.product_classifier or not self.text_vectorizer:
                await self._create_initial_models()
                
        except Exception as e:
            self.logger.error("Error loading/creating ML models", error=str(e))
            # Create basic models as fallback
            await self._create_basic_models()
    
    async def _create_initial_models(self):
        """Create initial ML models with sample data"""
        self.logger.info("Creating initial ML models")
        
        # Create text vectorizer
        self.text_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # Portuguese stop words would need custom list
            ngram_range=(1, 2),
            lowercase=True
        )
        
        # Create basic classifiers
        self.product_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.service_classifier = MultinomialNB()
        self.supplier_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Initialize with sample data
        await self._train_with_sample_data()
    
    async def _create_basic_models(self):
        """Create basic fallback models"""
        self.text_vectorizer = TfidfVectorizer(max_features=100)
        self.product_classifier = RandomForestClassifier(n_estimators=10, random_state=42)
        
        # Train with minimal sample data
        sample_texts = ["produto alimenticio", "equipamento eletronico", "servico consultoria"]
        sample_labels = ["Alimentos", "Eletrônicos", "Serviços"]
        
        X = self.text_vectorizer.fit_transform(sample_texts)
        self.product_classifier.fit(X, sample_labels)
    
    async def _save_models(self):
        """Save ML models to disk"""
        try:
            if self.product_classifier:
                with open(self.product_model_path, 'wb') as f:
                    pickle.dump(self.product_classifier, f)
            
            if self.text_vectorizer:
                with open(self.vectorizer_path, 'wb') as f:
                    pickle.dump(self.text_vectorizer, f)
                    
            self.logger.info("ML models saved successfully")
            
        except Exception as e:
            self.logger.error("Error saving ML models", error=str(e))   
 
    # Feature extraction and categorization helper methods
    def _extract_product_features(self, product: Product) -> Dict[str, Any]:
        """Extract features from product for ML classification"""
        return {
            'description': product.descricao.lower() if product.descricao else '',
            'ncm': product.ncm if product.ncm else '',
            'cfop': product.cfop if product.cfop else '',
            'unit': product.unidade_comercial.lower() if product.unidade_comercial else ''
        }
    
    def _generate_product_subcategory(self, product: Product) -> str:
        """Generate subcategory based on NCM and description analysis"""
        if not product.ncm:
            return "Geral"
        
        # NCM-based subcategorization (simplified)
        ncm_prefix = product.ncm[:2] if len(product.ncm) >= 2 else ""
        
        ncm_subcategories = {
            "01": "Animais Vivos",
            "02": "Carnes",
            "03": "Peixes e Crustáceos",
            "04": "Laticínios",
            "05": "Produtos de Origem Animal",
            "06": "Plantas Vivas",
            "07": "Produtos Hortícolas",
            "08": "Frutas",
            "09": "Café, Chá, Especiarias",
            "10": "Cereais",
            "84": "Máquinas e Equipamentos",
            "85": "Equipamentos Elétricos",
            "87": "Veículos",
            "90": "Instrumentos de Precisão"
        }
        
        return ncm_subcategories.get(ncm_prefix, "Outros")
    
    def _rule_based_product_categorization(self, product: Product) -> Tuple[str, str]:
        """Fallback rule-based product categorization"""
        description = product.descricao.lower() if product.descricao else ""
        
        # Simple keyword-based categorization
        if any(word in description for word in ["alimento", "comida", "bebida", "leite", "carne"]):
            return "Alimentos e Bebidas", "Consumo"
        elif any(word in description for word in ["equipamento", "maquina", "ferramenta"]):
            return "Equipamentos", "Industrial"
        elif any(word in description for word in ["eletronico", "computador", "celular", "tv"]):
            return "Eletrônicos", "Tecnologia"
        elif any(word in description for word in ["roupa", "vestuario", "calca", "camisa"]):
            return "Vestuário", "Têxtil"
        elif any(word in description for word in ["medicamento", "remedio", "farmacia"]):
            return "Farmacêutico", "Saúde"
        else:
            return "Diversos", "Geral"
    
    def _categorize_by_cnae(self, cnae_code: str) -> str:
        """Categorize service by CNAE code"""
        if not cnae_code:
            return "Serviços Gerais"
        
        # CNAE major groups (simplified)
        cnae_categories = {
            "01": "Agricultura, Pecuária, Produção Florestal",
            "02": "Agricultura, Pecuária, Produção Florestal", 
            "03": "Agricultura, Pecuária, Produção Florestal",
            "05": "Extração de Carvão Mineral",
            "06": "Extração de Petróleo e Gás Natural",
            "07": "Extração de Minerais Metálicos",
            "08": "Extração de Minerais Não-Metálicos",
            "09": "Atividades de Apoio à Extração",
            "10": "Fabricação de Produtos Alimentícios",
            "11": "Fabricação de Bebidas",
            "12": "Fabricação de Produtos do Fumo",
            "35": "Eletricidade, Gás e Outras Utilidades",
            "36": "Captação, Tratamento e Distribuição de Água",
            "37": "Esgoto e Atividades Relacionadas",
            "38": "Coleta, Tratamento e Disposição de Resíduos",
            "39": "Descontaminação e Outros Serviços",
            "41": "Construção de Edifícios",
            "42": "Obras de Infraestrutura",
            "43": "Serviços Especializados para Construção",
            "45": "Comércio e Reparação de Veículos",
            "46": "Comércio Atacadista",
            "47": "Comércio Varejista",
            "49": "Transporte Terrestre",
            "50": "Transporte Aquaviário",
            "51": "Transporte Aéreo",
            "52": "Armazenamento e Atividades Auxiliares",
            "53": "Correio e Outras Atividades",
            "55": "Alojamento",
            "56": "Alimentação",
            "58": "Atividades de Edição",
            "59": "Atividades Cinematográficas",
            "60": "Atividades de Rádio e Televisão",
            "61": "Telecomunicações",
            "62": "Atividades dos Serviços de Tecnologia",
            "63": "Atividades de Prestação de Serviços",
            "64": "Atividades de Serviços Financeiros",
            "65": "Seguros, Resseguros, Previdência",
            "66": "Atividades Auxiliares dos Serviços Financeiros",
            "68": "Atividades Imobiliárias",
            "69": "Atividades Jurídicas, Contábeis",
            "70": "Atividades de Sedes de Empresas",
            "71": "Serviços de Arquitetura e Engenharia",
            "72": "Pesquisa e Desenvolvimento Científico",
            "73": "Publicidade e Pesquisa de Mercado",
            "74": "Outras Atividades Profissionais",
            "75": "Atividades Veterinárias",
            "77": "Aluguéis Não-Imobiliários",
            "78": "Seleção, Agenciamento de Mão-de-Obra",
            "79": "Agências de Viagens",
            "80": "Atividades de Vigilância e Segurança",
            "81": "Serviços para Edifícios",
            "82": "Serviços de Escritório",
            "84": "Administração Pública",
            "85": "Educação",
            "86": "Atividades de Atenção à Saúde Humana",
            "87": "Atividades de Atenção à Saúde Residencial",
            "88": "Serviços de Assistência Social",
            "90": "Atividades Artísticas, Criativas",
            "91": "Atividades de Organizações Associativas",
            "92": "Atividades de Exploração de Jogos",
            "93": "Atividades Esportivas e Recreativas",
            "94": "Atividades de Organizações Associativas",
            "95": "Reparação e Manutenção",
            "96": "Outras Atividades de Serviços Pessoais",
            "97": "Serviços Domésticos",
            "99": "Organismos Internacionais"
        }
        
        cnae_prefix = cnae_code[:2] if len(cnae_code) >= 2 else cnae_code
        return cnae_categories.get(cnae_prefix, "Serviços Diversos")
    
    def _categorize_by_nbs(self, nbs_code: str) -> str:
        """Categorize service by NBS code"""
        if not nbs_code:
            return "Não Especificado"
        
        # NBS subcategorization (simplified)
        nbs_subcategories = {
            "101": "Serviços de Tecnologia da Informação",
            "102": "Serviços de Desenvolvimento de Software",
            "103": "Serviços de Processamento de Dados",
            "104": "Serviços de Hospedagem de Sites",
            "105": "Serviços de Consultoria em TI",
            "201": "Serviços de Engenharia",
            "202": "Serviços de Arquitetura",
            "203": "Serviços de Consultoria Técnica",
            "301": "Serviços Jurídicos",
            "302": "Serviços Contábeis",
            "303": "Serviços de Auditoria",
            "401": "Serviços de Publicidade",
            "402": "Serviços de Marketing",
            "403": "Serviços de Pesquisa de Mercado",
            "501": "Serviços de Limpeza",
            "502": "Serviços de Segurança",
            "503": "Serviços de Manutenção"
        }
        
        nbs_prefix = nbs_code[:3] if len(nbs_code) >= 3 else nbs_code
        return nbs_subcategories.get(nbs_prefix, "Serviços Especializados")
    
    def _rule_based_service_categorization(self, service: Service) -> Tuple[str, str]:
        """Fallback rule-based service categorization"""
        description = service.descricao.lower() if service.descricao else ""
        
        # Simple keyword-based categorization
        if any(word in description for word in ["consultoria", "assessoria", "orientacao"]):
            return "Consultoria", "Profissional"
        elif any(word in description for word in ["desenvolvimento", "software", "sistema", "ti"]):
            return "Tecnologia da Informação", "Desenvolvimento"
        elif any(word in description for word in ["manutencao", "reparo", "conserto"]):
            return "Manutenção", "Técnico"
        elif any(word in description for word in ["limpeza", "higienizacao"]):
            return "Limpeza", "Operacional"
        elif any(word in description for word in ["transporte", "frete", "entrega"]):
            return "Transporte", "Logística"
        elif any(word in description for word in ["juridico", "advocacia", "legal"]):
            return "Jurídico", "Profissional"
        elif any(word in description for word in ["contabil", "contabilidade", "fiscal"]):
            return "Contábil", "Profissional"
        else:
            return "Serviços Gerais", "Diversos"
    
    def _classify_supplier_region(self, uf: str) -> str:
        """Classify supplier by Brazilian region based on UF"""
        if not uf:
            return "Não Identificado"
        
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
    
    def _classify_supplier_type(self, supplier: Supplier) -> str:
        """Classify supplier by business type"""
        company_name = supplier.razao_social.lower() if supplier.razao_social else ""
        trade_name = supplier.nome_fantasia.lower() if supplier.nome_fantasia else ""
        
        full_name = f"{company_name} {trade_name}"
        
        # Business type classification based on company name patterns
        if any(word in full_name for word in ["industria", "industrial", "fabrica", "manufatura"]):
            return "Industrial"
        elif any(word in full_name for word in ["comercio", "comercial", "distribuidora", "atacado"]):
            return "Comercial"
        elif any(word in full_name for word in ["servicos", "consultoria", "assessoria", "prestadora"]):
            return "Prestador de Serviços"
        elif any(word in full_name for word in ["tecnologia", "software", "sistemas", "informatica"]):
            return "Tecnologia"
        elif any(word in full_name for word in ["construcao", "construtora", "engenharia", "obras"]):
            return "Construção Civil"
        elif any(word in full_name for word in ["transporte", "transportadora", "logistica", "frete"]):
            return "Transporte e Logística"
        elif any(word in full_name for word in ["alimenticia", "alimentos", "bebidas", "restaurante"]):
            return "Alimentício"
        elif any(word in full_name for word in ["farmacia", "farmaceutica", "medicamentos", "laboratorio"]):
            return "Farmacêutico"
        else:
            return "Fornecedor Geral"
    
    async def _determine_business_relationship(self, supplier: Supplier) -> str:
        """Determine business relationship based on transaction frequency"""
        # This would typically query historical data
        # For now, return a default classification
        # In a real implementation, this would analyze:
        # - Transaction frequency
        # - Transaction volume
        # - Contract duration
        # - Payment terms
        
        return "A Definir"  # Would be updated with actual data analysis
    
    async def _is_frequent_supplier(self, supplier_cnpj: str) -> bool:
        """Check if supplier is frequent (placeholder for database query)"""
        # This would query the database for supplier transaction history
        # For now, return False as placeholder
        return False
    
    async def _detect_tax_optimization_patterns(self, fiscal_data: FiscalDocument) -> bool:
        """Detect potential tax optimization patterns"""
        # Placeholder for tax optimization detection logic
        # Would analyze:
        # - CFOP codes for tax-efficient operations
        # - Interstate vs intrastate transactions
        # - Tax substitution usage
        # - Credit utilization patterns
        
        return False
    
    def _calculate_product_confidence(self, product: Product) -> float:
        """Calculate confidence score for product categorization"""
        score = 0.0
        
        # Base score for having a category
        if product.category and product.category != "Não Classificado":
            score += 0.5
        
        # Additional score for having NCM code
        if product.ncm:
            score += 0.3
        
        # Additional score for detailed description
        if product.descricao and len(product.descricao) > 10:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_service_confidence(self, service: Service) -> float:
        """Calculate confidence score for service categorization"""
        score = 0.0
        
        # Base score for having a category
        if service.category and service.category != "Serviços Gerais":
            score += 0.4
        
        # Additional score for having CNAE code
        if service.codigo_cnae:
            score += 0.3
        
        # Additional score for having NBS code
        if service.codigo_nbs:
            score += 0.2
        
        # Additional score for detailed description
        if service.descricao and len(service.descricao) > 10:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_supplier_confidence(self, supplier: Supplier) -> float:
        """Calculate confidence score for supplier classification"""
        score = 0.0
        
        # Base score for having classifications
        if supplier.category and supplier.category != "Fornecedor Geral":
            score += 0.4
        
        if supplier.region and supplier.region != "Não Identificado":
            score += 0.3
        
        if supplier.business_relationship and supplier.business_relationship != "A Definir":
            score += 0.3
        
        return min(score, 1.0)
    
    # Predefined categories and mappings
    def _load_product_categories(self) -> Dict[str, List[str]]:
        """Load predefined product categories"""
        return {
            "Alimentos e Bebidas": [
                "Carnes e Derivados", "Laticínios", "Cereais", "Frutas e Vegetais",
                "Bebidas Alcoólicas", "Bebidas Não Alcoólicas", "Produtos de Padaria"
            ],
            "Eletrônicos": [
                "Computadores", "Celulares", "Televisores", "Eletrodomésticos",
                "Componentes Eletrônicos", "Equipamentos de Som"
            ],
            "Equipamentos": [
                "Máquinas Industriais", "Ferramentas", "Equipamentos de Construção",
                "Veículos", "Equipamentos Médicos"
            ],
            "Vestuário": [
                "Roupas Masculinas", "Roupas Femininas", "Calçados", "Acessórios",
                "Roupas Infantis", "Uniformes"
            ],
            "Farmacêutico": [
                "Medicamentos", "Cosméticos", "Produtos de Higiene",
                "Equipamentos Médicos", "Suplementos"
            ]
        }
    
    def _load_service_categories(self) -> Dict[str, List[str]]:
        """Load predefined service categories"""
        return {
            "Consultoria": [
                "Consultoria Empresarial", "Consultoria Técnica", "Consultoria Jurídica",
                "Consultoria Financeira", "Consultoria em TI"
            ],
            "Tecnologia da Informação": [
                "Desenvolvimento de Software", "Suporte Técnico", "Hospedagem",
                "Consultoria em TI", "Manutenção de Sistemas"
            ],
            "Manutenção": [
                "Manutenção Predial", "Manutenção de Equipamentos", "Manutenção Automotiva",
                "Manutenção Industrial", "Manutenção de TI"
            ],
            "Transporte": [
                "Transporte Rodoviário", "Transporte Aéreo", "Logística",
                "Armazenagem", "Distribuição"
            ]
        }
    
    def _load_supplier_categories(self) -> Dict[str, List[str]]:
        """Load predefined supplier categories"""
        return {
            "Industrial": [
                "Fabricante", "Montadora", "Processadora", "Transformadora"
            ],
            "Comercial": [
                "Atacadista", "Varejista", "Distribuidora", "Representante"
            ],
            "Prestador de Serviços": [
                "Consultoria", "Manutenção", "Limpeza", "Segurança", "Transporte"
            ],
            "Tecnologia": [
                "Software", "Hardware", "Telecomunicações", "Internet"
            ]
        }
    
    async def _train_with_sample_data(self):
        """Train models with sample data for initial setup"""
        # Sample product data for training
        sample_products = [
            ("arroz integral organico", "Alimentos e Bebidas"),
            ("notebook dell inspiron", "Eletrônicos"),
            ("furadeira bosch profissional", "Equipamentos"),
            ("camisa polo masculina", "Vestuário"),
            ("paracetamol 500mg", "Farmacêutico"),
            ("leite desnatado", "Alimentos e Bebidas"),
            ("smartphone samsung", "Eletrônicos"),
            ("martelo carpinteiro", "Equipamentos"),
            ("sapato social couro", "Vestuário"),
            ("shampoo anticaspa", "Farmacêutico")
        ]
        
        # Prepare training data
        descriptions = [item[0] for item in sample_products]
        categories = [item[1] for item in sample_products]
        
        # Train text vectorizer and product classifier
        X = self.text_vectorizer.fit_transform(descriptions)
        self.product_classifier.fit(X, categories)
        
        self.logger.info("Models trained with sample data")
    
    # Public methods for adaptive learning
    async def retrain_models(self, training_data: List[Dict[str, Any]]):
        """
        Retrain models with new data for adaptive learning
        
        Args:
            training_data: List of training examples with features and labels
        """
        try:
            self.logger.info("Retraining models with new data", data_count=len(training_data))
            
            # Extract features and labels
            descriptions = []
            categories = []
            
            for item in training_data:
                if 'description' in item and 'category' in item:
                    descriptions.append(item['description'])
                    categories.append(item['category'])
            
            if descriptions and categories:
                # Retrain vectorizer and classifier
                X = self.text_vectorizer.fit_transform(descriptions)
                self.product_classifier.fit(X, categories)
                
                # Save updated models
                await self._save_models()
                
                self.logger.info("Models retrained successfully")
            else:
                self.logger.warning("No valid training data provided")
                
        except Exception as e:
            self.logger.error("Error retraining models", error=str(e))
            raise
    
    async def add_pattern(self, pattern: str, context: Dict[str, Any]):
        """
        Add a new detected pattern for adaptive learning
        
        Args:
            pattern: Pattern identifier
            context: Context information about the pattern
        """
        pattern_entry = {
            'pattern': pattern,
            'context': context,
            'timestamp': datetime.now(),
            'frequency': 1
        }
        
        # Check if pattern already exists
        existing_pattern = None
        for p in self.pattern_history:
            if p['pattern'] == pattern:
                existing_pattern = p
                break
        
        if existing_pattern:
            existing_pattern['frequency'] += 1
            existing_pattern['timestamp'] = datetime.now()
        else:
            self.pattern_history.append(pattern_entry)
        
        self.logger.info("Pattern added", pattern=pattern, frequency=existing_pattern['frequency'] if existing_pattern else 1)
    
    async def analyze_batch_patterns(self, fiscal_documents: List[FiscalDocument]) -> Dict[str, Any]:
        """
        Analyze patterns across a batch of fiscal documents with LLM-enhanced comprehensive insights
        
        Args:
            fiscal_documents: List of fiscal documents to analyze
            
        Returns:
            Dictionary with LLM-enhanced comprehensive pattern analysis results
        """
        try:
            self.logger.info("Starting LLM-enhanced batch pattern analysis", document_count=len(fiscal_documents))
            
            # Use LLM-enhanced pattern detection for comprehensive analysis
            llm_pattern_analysis = await self.detect_business_patterns(fiscal_documents)
            
            # Use traditional pattern detection engine as well
            detected_patterns = await self.pattern_engine.detect_patterns(fiscal_documents)
            
            # Categorize all documents using LLM-enhanced processing
            categorized_data = []
            for doc in fiscal_documents:
                categorized = await self.process(doc)
                categorized_data.append(categorized)
            
            # Analyze categorization patterns with LLM insights
            categorization_insights = await self._analyze_categorization_patterns_with_llm(categorized_data)
            
            # Get pattern summary from engine
            pattern_summary = self.pattern_engine.get_pattern_summary()
            
            # Combine LLM and traditional results
            analysis_result = {
                'total_documents': len(fiscal_documents),
                'llm_enhanced_analysis': llm_pattern_analysis,
                'traditional_patterns': [
                    {
                        'id': p.pattern_id,
                        'type': p.pattern_type,
                        'description': p.description,
                        'confidence': p.confidence,
                        'frequency': p.frequency,
                        'impact_score': p.impact_score,
                        'trend_direction': p.trend_direction
                    }
                    for p in detected_patterns
                ],
                'pattern_summary': pattern_summary,
                'categorization_insights': categorization_insights,
                'high_impact_patterns': [
                    p.description for p in self.pattern_engine.get_high_impact_patterns()
                ],
                'executive_recommendations': await self._generate_executive_recommendations(
                    llm_pattern_analysis, detected_patterns, categorized_data
                ),
                'strategic_insights': await self._extract_strategic_insights(llm_pattern_analysis),
                'risk_opportunities_matrix': await self._create_risk_opportunities_matrix(
                    llm_pattern_analysis, categorized_data
                )
            }
            
            self.logger.info("LLM-enhanced batch pattern analysis completed", 
                           llm_patterns_found=len(llm_pattern_analysis.get('llm_insights', {}).get('key_findings', [])),
                           traditional_patterns_found=len(detected_patterns))
            
            return analysis_result
            
        except Exception as e:
            self.logger.error("Error in LLM-enhanced batch pattern analysis", error=str(e))
            return {'error': str(e), 'total_documents': len(fiscal_documents)}
    
    async def _analyze_categorization_patterns_with_llm(
        self, 
        categorized_data: List[CategorizedFiscalData]
    ) -> Dict[str, Any]:
        """Analyze categorization patterns with LLM insights"""
        
        # Get traditional categorization insights
        traditional_insights = await self._analyze_categorization_patterns(categorized_data)
        
        # Prepare data for LLM analysis
        categorization_summary = {
            'total_documents': len(categorized_data),
            'categorization_distribution': traditional_insights,
            'confidence_metrics': traditional_insights.get('categorization_quality', {}),
            'supplier_diversity': len(set(
                data.classified_supplier.cnpj 
                for data in categorized_data 
                if data.classified_supplier and data.classified_supplier.cnpj
            ))
        }
        
        # Use LLM to generate insights about categorization patterns
        if self.llm_service:
            try:
                llm_insights = await self.llm_service.generate_insights(
                    categorization_summary, 'categorization_analysis', 'executive'
                )
                
                return {
                    'traditional_analysis': traditional_insights,
                    'llm_insights': {
                        'key_findings': llm_insights.key_findings,
                        'trends_identified': llm_insights.trends_identified,
                        'strategic_implications': llm_insights.strategic_implications,
                        'confidence_level': llm_insights.confidence_level
                    },
                    'combined_recommendations': await self._combine_categorization_recommendations(
                        traditional_insights, llm_insights
                    )
                }
                
            except Exception as e:
                self.logger.warning("LLM categorization analysis failed", error=str(e))
                return {'traditional_analysis': traditional_insights, 'llm_analysis': 'failed'}
        
        return {'traditional_analysis': traditional_insights}
    
    async def _generate_executive_recommendations(
        self,
        llm_analysis: Dict[str, Any],
        traditional_patterns: List[Pattern],
        categorized_data: List[CategorizedFiscalData]
    ) -> List[Dict[str, Any]]:
        """Generate executive-level recommendations combining LLM and traditional analysis"""
        
        recommendations = []
        
        # Extract LLM recommendations
        llm_insights = llm_analysis.get('llm_insights', {})
        if llm_insights.get('strategic_implications'):
            for implication in llm_insights['strategic_implications'][:3]:
                recommendations.append({
                    'type': 'strategic',
                    'priority': 'high',
                    'recommendation': implication,
                    'source': 'llm_analysis',
                    'confidence': llm_insights.get('confidence_level', 0.7)
                })
        
        # Add traditional pattern-based recommendations
        high_impact_patterns = [p for p in traditional_patterns if p.impact_score > 0.7]
        for pattern in high_impact_patterns[:2]:
            recommendations.append({
                'type': 'operational',
                'priority': 'medium',
                'recommendation': f"Ação recomendada para padrão: {pattern.description}",
                'source': 'pattern_analysis',
                'confidence': pattern.confidence
            })
        
        # Add categorization quality recommendations
        avg_confidence = self._calculate_average_confidence(categorized_data)
        if avg_confidence < 0.7:
            recommendations.append({
                'type': 'process_improvement',
                'priority': 'medium',
                'recommendation': 'Melhorar qualidade dos dados para aumentar precisão da categorização',
                'source': 'quality_analysis',
                'confidence': 0.9
            })
        
        return recommendations[:10]  # Top 10 recommendations
    
    async def _extract_strategic_insights(self, llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strategic insights from LLM analysis"""
        
        llm_insights = llm_analysis.get('llm_insights', {})
        
        return {
            'market_opportunities': self._extract_opportunities_from_insights(llm_insights),
            'competitive_advantages': self._extract_advantages_from_insights(llm_insights),
            'risk_mitigation': self._extract_risks_from_insights(llm_insights),
            'operational_efficiency': self._extract_efficiency_insights(llm_insights),
            'strategic_priorities': llm_insights.get('strategic_implications', [])[:5]
        }
    
    async def _create_risk_opportunities_matrix(
        self,
        llm_analysis: Dict[str, Any],
        categorized_data: List[CategorizedFiscalData]
    ) -> Dict[str, Any]:
        """Create risk-opportunities matrix from analysis"""
        
        matrix = {
            'high_risk_high_opportunity': [],
            'high_risk_low_opportunity': [],
            'low_risk_high_opportunity': [],
            'low_risk_low_opportunity': []
        }
        
        # Extract risks and opportunities from LLM analysis
        risks = llm_analysis.get('risk_assessment', {})
        opportunities = llm_analysis.get('opportunity_identification', [])
        
        # Categorize based on risk and opportunity levels
        for opportunity in opportunities:
            risk_level = self._assess_opportunity_risk(opportunity, risks)
            opportunity_level = self._assess_opportunity_potential(opportunity)
            
            if risk_level == 'high' and opportunity_level == 'high':
                matrix['high_risk_high_opportunity'].append(opportunity)
            elif risk_level == 'high' and opportunity_level == 'low':
                matrix['high_risk_low_opportunity'].append(opportunity)
            elif risk_level == 'low' and opportunity_level == 'high':
                matrix['low_risk_high_opportunity'].append(opportunity)
            else:
                matrix['low_risk_low_opportunity'].append(opportunity)
        
        return matrix
    
    def _calculate_average_confidence(self, categorized_data: List[CategorizedFiscalData]) -> float:
        """Calculate average confidence across categorized data"""
        confidences = []
        for data in categorized_data:
            if data.confidence_scores and 'overall' in data.confidence_scores:
                confidences.append(data.confidence_scores['overall'])
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _extract_opportunities_from_insights(self, llm_insights: Dict[str, Any]) -> List[str]:
        """Extract market opportunities from LLM insights"""
        opportunities = []
        
        for finding in llm_insights.get('key_findings', []):
            if 'oportunidade' in finding.lower() or 'crescimento' in finding.lower():
                opportunities.append(finding)
        
        return opportunities[:3]
    
    def _extract_advantages_from_insights(self, llm_insights: Dict[str, Any]) -> List[str]:
        """Extract competitive advantages from LLM insights"""
        advantages = []
        
        for trend in llm_insights.get('trends_identified', []):
            if 'vantagem' in trend.lower() or 'competitiv' in trend.lower():
                advantages.append(trend)
        
        return advantages[:3]
    
    def _extract_risks_from_insights(self, llm_insights: Dict[str, Any]) -> List[str]:
        """Extract risks from LLM insights"""
        risks = []
        
        for finding in llm_insights.get('key_findings', []):
            if 'risco' in finding.lower() or 'ameaça' in finding.lower():
                risks.append(finding)
        
        return risks[:3]
    
    def _extract_efficiency_insights(self, llm_insights: Dict[str, Any]) -> List[str]:
        """Extract operational efficiency insights"""
        efficiency = []
        
        for implication in llm_insights.get('strategic_implications', []):
            if 'eficiência' in implication.lower() or 'otimização' in implication.lower():
                efficiency.append(implication)
        
        return efficiency[:3]
    
    def _assess_opportunity_risk(self, opportunity: str, risks: Dict[str, Any]) -> str:
        """Assess risk level of an opportunity"""
        # Simple heuristic based on keywords
        if 'alto risco' in opportunity.lower() or 'complexo' in opportunity.lower():
            return 'high'
        return 'low'
    
    def _assess_opportunity_potential(self, opportunity: str) -> str:
        """Assess potential level of an opportunity"""
        # Simple heuristic based on keywords
        if 'grande' in opportunity.lower() or 'significativ' in opportunity.lower():
            return 'high'
        return 'low'
    
    async def _combine_categorization_recommendations(
        self,
        traditional_insights: Dict[str, Any],
        llm_insights: BusinessInsights
    ) -> List[str]:
        """Combine traditional and LLM categorization recommendations"""
        
        recommendations = []
        
        # Add LLM strategic implications
        recommendations.extend(llm_insights.strategic_implications[:3])
        
        # Add traditional quality-based recommendations
        quality_metrics = traditional_insights.get('categorization_quality', {})
        if quality_metrics.get('avg_confidence', 0) < 0.7:
            recommendations.append("Implementar treinamento adicional dos modelos de categorização")
        
        if quality_metrics.get('high_confidence_percentage', 0) < 0.8:
            recommendations.append("Enriquecer dados de entrada para melhorar precisão")
        
        return recommendations[:5]
    
    async def _analyze_categorization_patterns(self, categorized_data: List[CategorizedFiscalData]) -> Dict[str, Any]:
        """Analyze patterns in categorization results"""
        insights = {
            'product_categories': defaultdict(int),
            'service_categories': defaultdict(int),
            'supplier_types': defaultdict(int),
            'confidence_distribution': [],
            'categorization_quality': {}
        }
        
        try:
            for data in categorized_data:
                # Analyze product categories
                if data.categorized_products:
                    for product in data.categorized_products:
                        if product.category:
                            insights['product_categories'][product.category] += 1
                
                # Analyze service categories
                if data.categorized_services:
                    for service in data.categorized_services:
                        if service.category:
                            insights['service_categories'][service.category] += 1
                
                # Analyze supplier types
                if data.classified_supplier and data.classified_supplier.category:
                    insights['supplier_types'][data.classified_supplier.category] += 1
                
                # Collect confidence scores
                if data.confidence_scores:
                    insights['confidence_distribution'].append(data.confidence_scores.get('overall', 0.0))
            
            # Calculate categorization quality metrics
            if insights['confidence_distribution']:
                insights['categorization_quality'] = {
                    'avg_confidence': np.mean(insights['confidence_distribution']),
                    'min_confidence': min(insights['confidence_distribution']),
                    'max_confidence': max(insights['confidence_distribution']),
                    'high_confidence_percentage': len([c for c in insights['confidence_distribution'] if c > 0.8]) / len(insights['confidence_distribution'])
                }
            
            # Convert defaultdicts to regular dicts
            insights['product_categories'] = dict(insights['product_categories'])
            insights['service_categories'] = dict(insights['service_categories'])
            insights['supplier_types'] = dict(insights['supplier_types'])
            
            return insights
            
        except Exception as e:
            self.logger.error("Error analyzing categorization patterns", error=str(e))
            return insights
    
    async def _generate_recommendations(self, patterns: List[Pattern], categorized_data: List[CategorizedFiscalData]) -> List[str]:
        """Generate actionable recommendations based on detected patterns"""
        recommendations = []
        
        try:
            # Analyze high-impact patterns for recommendations
            high_impact_patterns = [p for p in patterns if p.impact_score > 0.7]
            
            for pattern in high_impact_patterns:
                if pattern.pattern_type == "supplier_behavior":
                    if "frequent" in pattern.description.lower():
                        recommendations.append(
                            f"Considere negociar contratos de longo prazo com fornecedores frequentes para obter melhores condições"
                        )
                    elif "crescimento" in pattern.description.lower():
                        recommendations.append(
                            f"Monitore fornecedores em crescimento para oportunidades de parcerias estratégicas"
                        )
                
                elif pattern.pattern_type == "tax_optimization":
                    if "interstate" in pattern.description.lower():
                        recommendations.append(
                            f"Revise a estratégia tributária para transações interestaduais - {pattern.description}"
                        )
                    elif "cfop" in pattern.description.lower():
                        recommendations.append(
                            f"Diversifique o uso de CFOPs para otimização tributária - {pattern.description}"
                        )
                
                elif pattern.pattern_type == "seasonal_trend":
                    recommendations.append(
                        f"Planeje estoque e fluxo de caixa considerando sazonalidade detectada - {pattern.description}"
                    )
                
                elif pattern.pattern_type == "price_volatility":
                    recommendations.append(
                        f"Implemente estratégias de hedge para mitigar volatilidade de preços - {pattern.description}"
                    )
                
                elif pattern.pattern_type == "geographic_pattern":
                    recommendations.append(
                        f"Considere diversificação geográfica de fornecedores - {pattern.description}"
                    )
            
            # Add categorization-based recommendations
            if categorized_data:
                avg_confidence = np.mean([
                    data.confidence_scores.get('overall', 0.0) 
                    for data in categorized_data 
                    if data.confidence_scores
                ])
                
                if avg_confidence < 0.6:
                    recommendations.append(
                        "Considere revisar e enriquecer dados de produtos/serviços para melhorar a precisão da categorização"
                    )
                
                # Check for uncategorized items
                uncategorized_count = 0
                total_items = 0
                
                for data in categorized_data:
                    if data.categorized_products:
                        for product in data.categorized_products:
                            total_items += 1
                            if not product.category or product.category == "Não Classificado":
                                uncategorized_count += 1
                    
                    if data.categorized_services:
                        for service in data.categorized_services:
                            total_items += 1
                            if not service.category or service.category == "Serviços Gerais":
                                uncategorized_count += 1
                
                if total_items > 0 and uncategorized_count / total_items > 0.2:
                    recommendations.append(
                        f"Alto percentual de itens não classificados ({uncategorized_count/total_items:.1%}) - considere treinar o modelo com mais dados"
                    )
            
            # Limit recommendations to top 10
            return recommendations[:10]
            
        except Exception as e:
            self.logger.error("Error generating recommendations", error=str(e))
            return ["Erro ao gerar recomendações - verifique os logs do sistema"]
    
    async def update_adaptive_learning(self, feedback_data: List[Dict[str, Any]]):
        """
        Update adaptive learning models based on user feedback
        
        Args:
            feedback_data: List of feedback entries with corrections and validations
        """
        try:
            self.logger.info("Updating adaptive learning models", feedback_count=len(feedback_data))
            
            # Prepare training data from feedback
            training_data = []
            pattern_feedback = []
            
            for feedback in feedback_data:
                if 'categorization_correction' in feedback:
                    # Product/service categorization corrections
                    correction = feedback['categorization_correction']
                    training_data.append({
                        'description': correction.get('description', ''),
                        'category': correction.get('correct_category', ''),
                        'confidence': 1.0  # High confidence for user corrections
                    })
                
                if 'pattern_validation' in feedback:
                    # Pattern detection feedback
                    validation = feedback['pattern_validation']
                    pattern_feedback.append({
                        'pattern_id': validation.get('pattern_id', ''),
                        'is_valid': validation.get('is_valid', False),
                        'user_confidence': validation.get('confidence', 0.5)
                    })
            
            # Retrain categorization models if we have training data
            if training_data:
                await self.retrain_models(training_data)
            
            # Update pattern detection thresholds based on feedback
            if pattern_feedback:
                await self._update_pattern_thresholds(pattern_feedback)
            
            self.logger.info("Adaptive learning update completed successfully")
            
        except Exception as e:
            self.logger.error("Error updating adaptive learning", error=str(e))
            raise
    
    async def _update_pattern_thresholds(self, pattern_feedback: List[Dict[str, Any]]):
        """Update pattern detection thresholds based on user feedback"""
        try:
            valid_patterns = [f for f in pattern_feedback if f.get('is_valid', False)]
            invalid_patterns = [f for f in pattern_feedback if not f.get('is_valid', False)]
            
            # Adjust thresholds based on feedback
            if len(valid_patterns) > len(invalid_patterns):
                # More valid patterns - can lower threshold slightly
                self.pattern_engine.pattern_threshold = max(0.5, self.pattern_engine.pattern_threshold - 0.05)
            elif len(invalid_patterns) > len(valid_patterns):
                # More invalid patterns - raise threshold
                self.pattern_engine.pattern_threshold = min(0.9, self.pattern_engine.pattern_threshold + 0.05)
            
            # Update learning rate based on feedback quality
            avg_user_confidence = np.mean([f.get('user_confidence', 0.5) for f in pattern_feedback])
            if avg_user_confidence > 0.8:
                self.pattern_engine.learning_rate = min(0.2, self.pattern_engine.learning_rate + 0.02)
            elif avg_user_confidence < 0.4:
                self.pattern_engine.learning_rate = max(0.05, self.pattern_engine.learning_rate - 0.02)
            
            self.logger.info("Pattern thresholds updated", 
                           new_threshold=self.pattern_engine.pattern_threshold,
                           new_learning_rate=self.pattern_engine.learning_rate)
            
        except Exception as e:
            self.logger.error("Error updating pattern thresholds", error=str(e))
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the adaptive learning system"""
        try:
            pattern_stats = self.pattern_engine.get_pattern_summary()
            
            return {
                'categorization_models': {
                    'product_classifier_trained': self.product_classifier is not None,
                    'service_classifier_trained': self.service_classifier is not None,
                    'supplier_classifier_trained': self.supplier_classifier is not None,
                    'text_vectorizer_vocabulary_size': len(self.text_vectorizer.vocabulary_) if self.text_vectorizer else 0
                },
                'pattern_detection': pattern_stats,
                'learning_parameters': {
                    'pattern_threshold': self.pattern_engine.pattern_threshold,
                    'learning_rate': self.pattern_engine.learning_rate,
                    'min_pattern_frequency': self.pattern_engine.min_pattern_frequency
                },
                'training_history': {
                    'total_patterns_learned': len(self.pattern_history),
                    'pattern_types_learned': len(set(p['pattern'] for p in self.pattern_history))
                }
            }
            
        except Exception as e:
            self.logger.error("Error getting learning statistics", error=str(e))
            return {'error': str(e)}
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns"""
        if not self.pattern_history:
            return {'total_patterns': 0, 'patterns': []}
        
        # Sort patterns by frequency
        sorted_patterns = sorted(self.pattern_history, key=lambda x: x['frequency'], reverse=True)
        
        return {
            'total_patterns': len(self.pattern_history),
            'most_frequent': sorted_patterns[0]['pattern'] if sorted_patterns else None,
            'patterns': [
                {
                    'pattern': p['pattern'],
                    'frequency': p['frequency'],
                    'last_seen': p['timestamp'].isoformat()
                }
                for p in sorted_patterns[:10]  # Top 10 patterns
            ]
        }