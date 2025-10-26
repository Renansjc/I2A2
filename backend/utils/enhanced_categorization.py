"""
Enhanced Categorization Integration Module
Provides integrated AI categorization with caching, fallback, and confidence validation
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import asyncio

from .categorization_cache import CategorizationCacheManager

logger = structlog.get_logger()


class EnhancedCategorizationService:
    """Service for enhanced AI categorization with caching and fallback mechanisms"""
    
    def __init__(self):
        self.cache_manager = CategorizationCacheManager()
        self.confidence_threshold = 0.7  # Minimum confidence for AI categorization
        self.fallback_confidence = 0.6  # Confidence assigned to fallback categorization
        self.max_retries = 2  # Maximum retries for AI categorization
    
    async def categorize_items(
        self, 
        items: List[Dict[str, Any]], 
        item_type: str = 'product'
    ) -> List[Dict[str, Any]]:
        """
        Categorize a list of items with caching and fallback
        
        Args:
            items: List of items to categorize
            item_type: Type of items ('product' or 'service')
            
        Returns:
            List of items with enhanced categorization data
        """
        try:
            categorized_items = []
            cache_hits = 0
            cache_misses = 0
            ai_categorizations = 0
            fallback_categorizations = 0
            
            start_time = datetime.now()
            
            for item in items:
                try:
                    # Add item type to item data
                    item['type'] = item_type
                    
                    # Try to get cached categorization first
                    cached_result = await self.cache_manager.get_cached_categorization(item)
                    
                    if cached_result:
                        # Use cached categorization
                        item.update({
                            'categoria': cached_result['category'],
                            'subcategoria': cached_result['subcategory'],
                            'categorization_confidence': cached_result['confidence'],
                            'categorization_method': f"cached_{cached_result['cache_type']}",
                            'cache_hit': True
                        })
                        cache_hits += 1
                        
                    else:
                        # No cache hit, try AI categorization
                        ai_result = await self._categorize_with_ai(item, item_type)
                        
                        if ai_result and ai_result['confidence'] >= self.confidence_threshold:
                            # AI categorization successful
                            item.update({
                                'categoria': ai_result['category'],
                                'subcategoria': ai_result['subcategory'],
                                'categorization_confidence': ai_result['confidence'],
                                'categorization_method': 'ai_enhanced',
                                'cache_hit': False
                            })
                            
                            # Cache the result for future use
                            await self.cache_manager.cache_categorization(
                                item, 
                                ai_result['category'], 
                                ai_result['subcategory'], 
                                ai_result['confidence'],
                                'ai_enhanced'
                            )
                            
                            ai_categorizations += 1
                            
                        else:
                            # AI categorization failed or low confidence, use fallback
                            fallback_result = await self._categorize_with_fallback(item, item_type)
                            
                            item.update({
                                'categoria': fallback_result['category'],
                                'subcategoria': fallback_result['subcategory'],
                                'categorization_confidence': self.fallback_confidence,
                                'categorization_method': 'rule_based_fallback',
                                'cache_hit': False,
                                'ai_failed': True
                            })
                            
                            # Cache fallback result with lower confidence
                            await self.cache_manager.cache_categorization(
                                item, 
                                fallback_result['category'], 
                                fallback_result['subcategory'], 
                                self.fallback_confidence,
                                'rule_based_fallback'
                            )
                            
                            fallback_categorizations += 1
                        
                        cache_misses += 1
                    
                    categorized_items.append(item)
                    
                except Exception as e:
                    logger.warning(
                        "Failed to categorize individual item",
                        item_code=item.get('codigo_produto', item.get('codigo_servico', 'unknown')),
                        error=str(e)
                    )
                    
                    # Use basic fallback for failed items
                    fallback_result = await self._categorize_with_fallback(item, item_type)
                    item.update({
                        'categoria': fallback_result['category'],
                        'subcategoria': fallback_result['subcategory'],
                        'categorization_confidence': 0.5,
                        'categorization_method': 'error_fallback',
                        'cache_hit': False,
                        'error': str(e)
                    })
                    
                    categorized_items.append(item)
                    fallback_categorizations += 1
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update metrics
            await self._update_metrics(
                cache_hits, cache_misses, ai_categorizations, 
                fallback_categorizations, processing_time
            )
            
            logger.info(
                "Batch categorization completed",
                total_items=len(items),
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                ai_categorizations=ai_categorizations,
                fallback_categorizations=fallback_categorizations,
                processing_time_ms=processing_time
            )
            
            return categorized_items
            
        except Exception as e:
            logger.error("Failed to categorize items batch", error=str(e))
            # Return items with basic fallback categorization
            return await self._batch_fallback_categorization(items, item_type)
    
    async def _categorize_with_ai(
        self, 
        item: Dict[str, Any], 
        item_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Categorize item using AI Categorization Agent
        
        Args:
            item: Item to categorize
            item_type: Type of item ('product' or 'service')
            
        Returns:
            AI categorization result or None if failed
        """
        try:
            from agents.ai_categorization_agent import LLMEnhancedAICategorizationAgent
            
            # Create mock XML for the categorization agent
            mock_xml = self._create_mock_xml_for_categorization([item], item_type)
            
            # Initialize categorization agent
            categorization_agent = LLMEnhancedAICategorizationAgent()
            await categorization_agent.initialize()
            
            try:
                # Perform categorization with retries
                for attempt in range(self.max_retries):
                    try:
                        categorization_result = await categorization_agent.categorize_document(
                            mock_xml, 
                            {'document_type': 'NFE' if item_type == 'product' else 'NFSE'}
                        )
                        
                        if categorization_result.get('categorized_items'):
                            categorized_item = categorization_result['categorized_items'][0]
                            
                            return {
                                'category': categorized_item.get('category', 'Outros'),
                                'subcategory': categorized_item.get('subcategory', 'Diversos'),
                                'confidence': categorized_item.get('confidence', 0.8),
                                'method': 'ai_enhanced'
                            }
                        
                        break  # Exit retry loop if no items returned
                        
                    except Exception as retry_error:
                        logger.warning(
                            f"AI categorization attempt {attempt + 1} failed",
                            error=str(retry_error)
                        )
                        
                        if attempt == self.max_retries - 1:
                            raise retry_error
                        
                        # Wait before retry
                        await asyncio.sleep(1 * (attempt + 1))
                
            finally:
                await categorization_agent.cleanup()
            
            return None
            
        except Exception as e:
            logger.warning("AI categorization failed", error=str(e))
            return None
    
    async def _categorize_with_fallback(
        self, 
        item: Dict[str, Any], 
        item_type: str
    ) -> Dict[str, Any]:
        """
        Categorize item using rule-based fallback
        
        Args:
            item: Item to categorize
            item_type: Type of item ('product' or 'service')
            
        Returns:
            Fallback categorization result
        """
        try:
            if item_type == 'product':
                return await self._categorize_product_fallback(item)
            else:
                return await self._categorize_service_fallback(item)
                
        except Exception as e:
            logger.warning("Fallback categorization failed", error=str(e))
            return {
                'category': 'Outros',
                'subcategory': 'Não Classificado'
            }
    
    async def _categorize_product_fallback(self, produto: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced rule-based categorization for products"""
        try:
            descricao = produto.get('descricao', '').lower()
            ncm = produto.get('ncm', '').strip()
            
            # NCM-based categorization (more accurate)
            if ncm:
                if ncm.startswith('8471'):  # Computer equipment
                    return {'category': 'Eletrônicos', 'subcategory': 'Equipamentos de Informática'}
                elif ncm.startswith('8517'):  # Telecommunications equipment
                    return {'category': 'Eletrônicos', 'subcategory': 'Equipamentos de Telecomunicações'}
                elif ncm.startswith('9401'):  # Seats and furniture
                    return {'category': 'Móveis', 'subcategoria': 'Móveis de Escritório'}
                elif ncm.startswith('4820'):  # Paper products
                    return {'category': 'Material de Escritório', 'subcategory': 'Papelaria'}
                elif ncm.startswith('3004'):  # Medicines
                    return {'category': 'Medicamentos', 'subcategory': 'Medicamentos Gerais'}
                elif ncm.startswith('2711'):  # Gas
                    return {'category': 'Combustíveis e Energia', 'subcategory': 'Gás GLP'}
            
            # Description-based categorization (enhanced)
            if any(word in descricao for word in ['computador', 'notebook', 'desktop', 'pc', 'laptop']):
                return {'category': 'Eletrônicos', 'subcategory': 'Computadores'}
            elif any(word in descricao for word in ['placa', 'video', 'geforce', 'rtx', 'gpu', 'graphics']):
                return {'category': 'Eletrônicos', 'subcategory': 'Placas de Vídeo'}
            elif any(word in descricao for word in ['móvel', 'mesa', 'cadeira', 'estante', 'armário']):
                return {'category': 'Móveis', 'subcategory': 'Móveis de Escritório'}
            elif any(word in descricao for word in ['papel', 'caneta', 'lápis', 'caderno', 'escritório']):
                return {'category': 'Material de Escritório', 'subcategory': 'Papelaria'}
            elif any(word in descricao for word in ['tesoura', 'churrasco', 'utensílio', 'cozinha', 'doméstico']):
                return {'category': 'Utensílios Domésticos', 'subcategory': 'Utensílios de Cozinha'}
            elif any(word in descricao for word in ['overgrip', 'esporte', 'tênis', 'absorb', 'atlético']):
                return {'category': 'Artigos Esportivos', 'subcategory': 'Equipamentos Esportivos'}
            elif any(word in descricao for word in ['medicamento', 'remédio', 'farmácia', 'lacday', 'cpr', 'comprimido']):
                return {'category': 'Medicamentos', 'subcategory': 'Medicamentos Orais'}
            elif any(word in descricao for word in ['glp', 'gás', 'combustível', 'energia', 'botijão']):
                return {'category': 'Combustíveis e Energia', 'subcategory': 'Gás GLP'}
            elif any(word in descricao for word in ['eletrônico', 'digital', 'tecnologia', 'tech']):
                return {'category': 'Eletrônicos', 'subcategory': 'Eletrônicos Gerais'}
            elif any(word in descricao for word in ['ferramenta', 'tool', 'equipamento', 'instrumento']):
                return {'category': 'Ferramentas e Equipamentos', 'subcategory': 'Ferramentas Gerais'}
            elif any(word in descricao for word in ['roupa', 'vestuário', 'clothing', 'apparel']):
                return {'category': 'Vestuário', 'subcategory': 'Roupas'}
            elif any(word in descricao for word in ['livro', 'book', 'revista', 'publicação']):
                return {'category': 'Livros e Publicações', 'subcategory': 'Literatura'}
            else:
                return {'category': 'Outros', 'subcategory': 'Produtos Diversos'}
                
        except Exception as e:
            logger.warning("Product fallback categorization failed", error=str(e))
            return {'category': 'Outros', 'subcategory': 'Não Classificado'}
    
    async def _categorize_service_fallback(self, servico: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced rule-based categorization for services"""
        try:
            descricao = servico.get('descricao', '').lower()
            cnae = servico.get('codigo_cnae', '').strip()
            
            # CNAE-based categorization (more accurate)
            if cnae:
                if cnae.startswith('62'):  # IT services
                    return {'category': 'Tecnologia da Informação', 'subcategory': 'Desenvolvimento de Software'}
                elif cnae.startswith('69'):  # Legal and accounting services
                    return {'category': 'Serviços Profissionais', 'subcategory': 'Consultoria Jurídica e Contábil'}
                elif cnae.startswith('70'):  # Management consulting
                    return {'category': 'Consultoria', 'subcategory': 'Consultoria Empresarial'}
                elif cnae.startswith('81'):  # Facility services
                    return {'category': 'Serviços de Apoio', 'subcategory': 'Serviços de Limpeza e Manutenção'}
                elif cnae.startswith('85'):  # Education
                    return {'category': 'Educação', 'subcategory': 'Serviços Educacionais'}
            
            # Description-based categorization (enhanced)
            if any(word in descricao for word in ['consultoria', 'assessoria', 'consulting', 'advisory']):
                return {'category': 'Consultoria', 'subcategory': 'Consultoria Empresarial'}
            elif any(word in descricao for word in ['desenvolvimento', 'software', 'sistema', 'programação', 'ti']):
                return {'category': 'Tecnologia da Informação', 'subcategory': 'Desenvolvimento de Software'}
            elif any(word in descricao for word in ['manutenção', 'reparo', 'maintenance', 'repair']):
                return {'category': 'Manutenção', 'subcategory': 'Serviços Técnicos'}
            elif any(word in descricao for word in ['limpeza', 'cleaning', 'higienização', 'sanitização']):
                return {'category': 'Serviços de Apoio', 'subcategory': 'Serviços de Limpeza'}
            elif any(word in descricao for word in ['segurança', 'security', 'vigilância', 'monitoramento']):
                return {'category': 'Segurança', 'subcategory': 'Serviços de Segurança'}
            elif any(word in descricao for word in ['transporte', 'transport', 'logística', 'entrega']):
                return {'category': 'Logística e Transporte', 'subcategory': 'Serviços de Transporte'}
            elif any(word in descricao for word in ['marketing', 'publicidade', 'advertising', 'propaganda']):
                return {'category': 'Marketing e Publicidade', 'subcategory': 'Serviços de Marketing'}
            elif any(word in descricao for word in ['treinamento', 'training', 'capacitação', 'educação']):
                return {'category': 'Educação', 'subcategory': 'Treinamento e Capacitação'}
            elif any(word in descricao for word in ['contábil', 'accounting', 'fiscal', 'tributário']):
                return {'category': 'Serviços Profissionais', 'subcategory': 'Serviços Contábeis'}
            elif any(word in descricao for word in ['jurídico', 'legal', 'advocacia', 'direito']):
                return {'category': 'Serviços Profissionais', 'subcategory': 'Serviços Jurídicos'}
            else:
                return {'category': 'Serviços Gerais', 'subcategory': 'Serviços Diversos'}
                
        except Exception as e:
            logger.warning("Service fallback categorization failed", error=str(e))
            return {'category': 'Serviços Gerais', 'subcategory': 'Não Classificado'}
    
    async def _batch_fallback_categorization(
        self, 
        items: List[Dict[str, Any]], 
        item_type: str
    ) -> List[Dict[str, Any]]:
        """Apply fallback categorization to all items in batch"""
        try:
            categorized_items = []
            
            for item in items:
                item['type'] = item_type
                fallback_result = await self._categorize_with_fallback(item, item_type)
                
                item.update({
                    'categoria': fallback_result['category'],
                    'subcategoria': fallback_result['subcategory'],
                    'categorization_confidence': 0.5,
                    'categorization_method': 'batch_fallback',
                    'cache_hit': False
                })
                
                categorized_items.append(item)
            
            return categorized_items
            
        except Exception as e:
            logger.error("Batch fallback categorization failed", error=str(e))
            return items
    
    def _create_mock_xml_for_categorization(
        self, 
        items: List[Dict[str, Any]], 
        item_type: str
    ) -> str:
        """Create mock XML content for categorization agent"""
        try:
            if item_type == "product":
                # Create minimal NF-e XML structure for products
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <det nItem="1">
                <prod>
                    <cProd>{}</cProd>
                    <xProd>{}</xProd>
                    <NCM>{}</NCM>
                    <CFOP>{}</CFOP>
                    <uCom>{}</uCom>
                    <vProd>100.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>
</nfeProc>'''.format(
                    items[0].get('codigo_produto', 'PROD001'),
                    items[0].get('descricao', 'Produto para categorização'),
                    items[0].get('ncm', '12345678'),
                    items[0].get('cfop', '5102'),
                    items[0].get('unidade_comercial', 'UN')
                )
            
            else:  # service
                # Create minimal NFS-e XML structure for services
                xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<nfse>
    <servico>
        <codigo>{}</codigo>
        <descricao>{}</descricao>
        <cnae>{}</cnae>
    </servico>
</nfse>'''.format(
                    items[0].get('codigo_servico', 'SERV001'),
                    items[0].get('descricao', 'Serviço para categorização'),
                    items[0].get('codigo_cnae', '6201500')
                )
            
            return xml_content
            
        except Exception as e:
            logger.error("Failed to create mock XML for categorization", error=str(e))
            return "<root></root>"
    
    async def _update_metrics(
        self, 
        cache_hits: int, 
        cache_misses: int, 
        ai_categorizations: int, 
        fallback_categorizations: int, 
        processing_time: float
    ) -> None:
        """Update categorization performance metrics"""
        try:
            import asyncio
            from utils.database import get_supabase_client
            
            supabase_client = get_supabase_client(admin_mode=True)
            
            # Calculate average confidence (simplified)
            total_categorizations = cache_hits + cache_misses + ai_categorizations + fallback_categorizations
            avg_confidence = 0.8 if total_categorizations > 0 else None
            
            await asyncio.to_thread(
                lambda: supabase_client.client.rpc(
                    'update_categorization_metrics',
                    {
                        'cache_hits_param': cache_hits,
                        'cache_misses_param': cache_misses,
                        'ai_categorizations_param': ai_categorizations,
                        'fallback_categorizations_param': fallback_categorizations,
                        'confidence_param': avg_confidence,
                        'processing_time_param': int(processing_time)
                    }
                ).execute()
            )
            
        except Exception as e:
            logger.warning("Failed to update categorization metrics", error=str(e))
    
    async def get_categorization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive categorization statistics"""
        try:
            cache_stats = await self.cache_manager.get_cache_statistics()
            
            # Get recent metrics
            from utils.database import get_supabase_client
            import asyncio
            
            supabase_client = get_supabase_client(admin_mode=True)
            
            metrics_result = await asyncio.to_thread(
                lambda: supabase_client.client.table('categorization_metrics')
                .select('*')
                .order('date', desc=True)
                .limit(7)  # Last 7 days
                .execute()
            )
            
            return {
                'cache_statistics': cache_stats,
                'recent_metrics': metrics_result.data,
                'configuration': {
                    'confidence_threshold': self.confidence_threshold,
                    'fallback_confidence': self.fallback_confidence,
                    'max_retries': self.max_retries
                }
            }
            
        except Exception as e:
            logger.error("Failed to get categorization statistics", error=str(e))
            return {
                'error': str(e),
                'cache_statistics': {},
                'recent_metrics': []
            }
    
    async def recategorize_items_by_pattern(
        self, 
        pattern: str, 
        new_category: str, 
        new_subcategory: str
    ) -> Dict[str, Any]:
        """
        Recategorize items matching a specific pattern
        
        Args:
            pattern: Pattern to match in item descriptions
            new_category: New category to assign
            new_subcategory: New subcategory to assign
            
        Returns:
            Results of recategorization operation
        """
        try:
            # This would involve updating both cache and dimensional tables
            # Implementation would depend on specific business requirements
            
            logger.info(
                "Pattern-based recategorization requested",
                pattern=pattern,
                new_category=new_category,
                new_subcategory=new_subcategory
            )
            
            # Placeholder implementation
            return {
                'success': True,
                'pattern': pattern,
                'new_category': new_category,
                'new_subcategory': new_subcategory,
                'items_updated': 0,
                'message': 'Pattern-based recategorization feature to be implemented'
            }
            
        except Exception as e:
            logger.error("Failed to recategorize items by pattern", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }