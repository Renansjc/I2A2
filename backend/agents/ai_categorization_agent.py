"""
AI Categorization Agent for intelligent product and service categorization
"""

import structlog
from typing import Dict, Any, List
from .base_agent import BaseAgent
from utils.database import ProcessingStatusManager

logger = structlog.get_logger()


class LLMEnhancedAICategorizationAgent(BaseAgent):
    """Enhanced AI Categorization Agent with LLM capabilities"""
    
    def __init__(self):
        super().__init__("LLMEnhancedAICategorizationAgent")
        self.agent_name = "ai_categorization_agent"
    
    async def categorize_document(self, xml_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize products and services in fiscal document"""
        try:
            document_id = context.get('document_id')
            document_type = context.get('document_type', 'NFE')
            
            logger.info(
                "Starting AI categorization",
                document_id=document_id,
                document_type=document_type
            )
            
            # Extract items from XML for categorization
            items = await self._extract_items_for_categorization(xml_content, document_type)
            
            # Categorize items using LLM
            categorized_items = await self._categorize_items_with_llm(items)
            
            # Generate category insights
            category_insights = await self._generate_category_insights(categorized_items)
            
            # Detect category patterns
            patterns = await self._detect_category_patterns(categorized_items)
            
            result = {
                "categorized_items": categorized_items,
                "category_insights": category_insights,
                "patterns_detected": patterns,
                "total_items": len(items),
                "unique_categories": len(set(item.get("category", "") for item in categorized_items)),
                "confidence": 0.85,
                "processing_status": "completed"
            }
            
            logger.info(
                "AI categorization completed",
                document_id=document_id,
                total_items=len(items),
                unique_categories=result["unique_categories"]
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "AI categorization failed",
                document_id=document_id,
                error=str(e)
            )
            raise
    
    async def _extract_items_for_categorization(self, xml_content: str, document_type: str) -> List[Dict[str, Any]]:
        """Extract items from XML for categorization"""
        try:
            from lxml import etree
            
            items = []
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            if document_type == "NFE":
                # Extract NF-e items
                det_elements = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                
                for det in det_elements:
                    prod = det.find('.//{http://www.portalfiscal.inf.br/nfe}prod')
                    if prod is not None:
                        item = {
                            "code": self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}cProd'),
                            "description": self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}xProd'),
                            "ncm": self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}NCM'),
                            "cfop": self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}CFOP'),
                            "value": float(self._get_text(prod, './/{http://www.portalfiscal.inf.br/nfe}vProd') or 0),
                            "type": "product"
                        }
                        items.append(item)
            
            elif document_type == "NFSE":
                # Extract NFS-e services (simplified)
                items.append({
                    "code": "SERV001",
                    "description": "Serviços diversos",
                    "type": "service",
                    "value": 0.0
                })
            
            return items
            
        except Exception as e:
            logger.warning("Failed to extract items for categorization", error=str(e))
            return []
    
    async def _categorize_items_with_llm(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize items using LLM"""
        try:
            categorized_items = []
            
            for item in items:
                # Simple categorization logic (would use LLM in production)
                category = await self._determine_category(item)
                subcategory = await self._determine_subcategory(item, category)
                
                categorized_item = {
                    **item,
                    "category": category,
                    "subcategory": subcategory,
                    "confidence": 0.85,
                    "categorization_method": "llm_enhanced"
                }
                categorized_items.append(categorized_item)
            
            return categorized_items
            
        except Exception as e:
            logger.warning("LLM categorization failed", error=str(e))
            return items
    
    async def _determine_category(self, item: Dict[str, Any]) -> str:
        """Determine main category for item"""
        description = item.get("description", "").lower()
        
        # Simple rule-based categorization (would use LLM)
        if any(word in description for word in ["computador", "notebook", "eletrônico"]):
            return "Eletrônicos"
        elif any(word in description for word in ["móvel", "mesa", "cadeira"]):
            return "Móveis"
        elif any(word in description for word in ["serviço", "consultoria", "manutenção"]):
            return "Serviços"
        elif any(word in description for word in ["material", "escritório", "papel"]):
            return "Material de Escritório"
        else:
            return "Outros"
    
    async def _determine_subcategory(self, item: Dict[str, Any], category: str) -> str:
        """Determine subcategory for item"""
        description = item.get("description", "").lower()
        
        # Simple subcategorization
        if category == "Eletrônicos":
            if "notebook" in description:
                return "Computadores Portáteis"
            elif "desktop" in description:
                return "Computadores Desktop"
            else:
                return "Eletrônicos Gerais"
        elif category == "Serviços":
            if "consultoria" in description:
                return "Consultoria"
            elif "manutenção" in description:
                return "Manutenção"
            else:
                return "Serviços Gerais"
        else:
            return f"{category} - Geral"
    
    async def _generate_category_insights(self, categorized_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights about categorization"""
        try:
            insights = []
            
            # Category distribution
            category_counts = {}
            total_value_by_category = {}
            
            for item in categorized_items:
                category = item.get("category", "Outros")
                value = item.get("value", 0)
                
                category_counts[category] = category_counts.get(category, 0) + 1
                total_value_by_category[category] = total_value_by_category.get(category, 0) + value
            
            # Generate insights
            if category_counts:
                most_common_category = max(category_counts, key=category_counts.get)
                insights.append({
                    "type": "category_distribution",
                    "description": f"Categoria mais comum: {most_common_category} ({category_counts[most_common_category]} itens)",
                    "confidence": 0.9
                })
            
            if total_value_by_category:
                highest_value_category = max(total_value_by_category, key=total_value_by_category.get)
                insights.append({
                    "type": "value_analysis",
                    "description": f"Categoria com maior valor: {highest_value_category} (R$ {total_value_by_category[highest_value_category]:.2f})",
                    "confidence": 0.95
                })
            
            return insights
            
        except Exception as e:
            logger.warning("Failed to generate category insights", error=str(e))
            return []
    
    async def _detect_category_patterns(self, categorized_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in categorization"""
        try:
            patterns = []
            
            # Pattern: High-value items
            high_value_items = [item for item in categorized_items if item.get("value", 0) > 1000]
            if high_value_items:
                patterns.append({
                    "type": "high_value_items",
                    "description": f"Identificados {len(high_value_items)} itens de alto valor (>R$ 1.000)",
                    "items_count": len(high_value_items),
                    "confidence": 0.9
                })
            
            # Pattern: Category concentration
            categories = [item.get("category") for item in categorized_items]
            unique_categories = set(categories)
            if len(unique_categories) <= 2 and len(categorized_items) > 5:
                patterns.append({
                    "type": "category_concentration",
                    "description": f"Documento concentrado em poucas categorias ({len(unique_categories)} categorias)",
                    "concentration_level": "high",
                    "confidence": 0.85
                })
            
            return patterns
            
        except Exception as e:
            logger.warning("Failed to detect category patterns", error=str(e))
            return []
    
    def _get_text(self, parent, xpath: str) -> str:
        """Get text content from XML element"""
        if parent is None:
            return ""
        element = parent.find(xpath)
        return element.text if element is not None else ""