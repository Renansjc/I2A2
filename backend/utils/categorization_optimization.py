"""
Categorization Optimization Service
Provides bulk recategorization, performance optimization, and consistency management
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import asyncio
from collections import defaultdict

from .categorization_cache import CategorizationCacheManager
from .database import get_supabase_client

logger = structlog.get_logger()


class CategorizationOptimizationService:
    """Service for optimizing categorization performance and consistency"""
    
    def __init__(self):
        self.cache_manager = CategorizationCacheManager()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.batch_size = 50  # Process items in batches
        self.similarity_threshold = 0.9  # Threshold for considering items similar for bulk operations
    
    async def analyze_categorization_patterns(self) -> Dict[str, Any]:
        """
        Analyze categorization patterns to identify optimization opportunities
        
        Returns:
            Analysis results with optimization recommendations
        """
        try:
            # Get categorization method statistics
            method_stats = await asyncio.to_thread(
                lambda: self.supabase_client.client.rpc('get_categorization_method_stats').execute()
            )
            
            # Get low confidence items
            low_confidence_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('low_confidence_items')
                .select('*')
                .limit(100)
                .execute()
            )
            
            # Get cache statistics
            cache_stats = await self.cache_manager.get_cache_statistics()
            
            # Analyze category distribution
            category_analysis = await self._analyze_category_distribution()
            
            # Identify duplicate/similar items
            duplicate_analysis = await self._identify_similar_items()
            
            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                method_stats.data, low_confidence_result.data, cache_stats, category_analysis
            )
            
            return {
                'method_statistics': method_stats.data,
                'low_confidence_items': low_confidence_result.data,
                'cache_statistics': cache_stats,
                'category_analysis': category_analysis,
                'duplicate_analysis': duplicate_analysis,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to analyze categorization patterns", error=str(e))
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _analyze_category_distribution(self) -> Dict[str, Any]:
        """Analyze the distribution of categories across products and services"""
        try:
            # Get category distribution for products
            produtos_dist = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_produtos')
                .select('categoria, subcategoria, categorization_confidence, categorization_method')
                .execute()
            )
            
            # Get category distribution for services
            servicos_dist = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_servicos')
                .select('categoria, subcategoria, categorization_confidence, categorization_method')
                .execute()
            )
            
            # Analyze product categories
            product_categories = defaultdict(lambda: {'count': 0, 'avg_confidence': 0, 'methods': defaultdict(int)})
            for item in produtos_dist.data:
                category = item.get('categoria', 'Unknown')
                confidence = float(item.get('categorization_confidence', 0))
                method = item.get('categorization_method', 'unknown')
                
                product_categories[category]['count'] += 1
                product_categories[category]['avg_confidence'] += confidence
                product_categories[category]['methods'][method] += 1
            
            # Calculate averages for products
            for category in product_categories:
                count = product_categories[category]['count']
                product_categories[category]['avg_confidence'] /= count
            
            # Analyze service categories
            service_categories = defaultdict(lambda: {'count': 0, 'avg_confidence': 0, 'methods': defaultdict(int)})
            for item in servicos_dist.data:
                category = item.get('categoria', 'Unknown')
                confidence = float(item.get('categorization_confidence', 0))
                method = item.get('categorization_method', 'unknown')
                
                service_categories[category]['count'] += 1
                service_categories[category]['avg_confidence'] += confidence
                service_categories[category]['methods'][method] += 1
            
            # Calculate averages for services
            for category in service_categories:
                count = service_categories[category]['count']
                service_categories[category]['avg_confidence'] /= count
            
            return {
                'product_categories': dict(product_categories),
                'service_categories': dict(service_categories),
                'total_products': len(produtos_dist.data),
                'total_services': len(servicos_dist.data),
                'unique_product_categories': len(product_categories),
                'unique_service_categories': len(service_categories)
            }
            
        except Exception as e:
            logger.warning("Failed to analyze category distribution", error=str(e))
            return {}
    
    async def _identify_similar_items(self) -> Dict[str, Any]:
        """Identify items that might be duplicates or very similar"""
        try:
            # Get all products for similarity analysis
            produtos_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_produtos')
                .select('codigo_produto, descricao, categoria, subcategoria, ncm')
                .execute()
            )
            
            # Get all services for similarity analysis
            servicos_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_servicos')
                .select('codigo_servico, descricao, categoria, subcategoria, codigo_cnae')
                .execute()
            )
            
            # Find similar products
            similar_products = await self._find_similar_items_in_list(
                produtos_result.data, 'codigo_produto', 'product'
            )
            
            # Find similar services
            similar_services = await self._find_similar_items_in_list(
                servicos_result.data, 'codigo_servico', 'service'
            )
            
            return {
                'similar_products': similar_products,
                'similar_services': similar_services,
                'total_product_groups': len(similar_products),
                'total_service_groups': len(similar_services)
            }
            
        except Exception as e:
            logger.warning("Failed to identify similar items", error=str(e))
            return {}
    
    async def _find_similar_items_in_list(
        self, 
        items: List[Dict[str, Any]], 
        code_field: str, 
        item_type: str
    ) -> List[Dict[str, Any]]:
        """Find groups of similar items in a list"""
        try:
            similar_groups = []
            processed_items = set()
            
            for i, item1 in enumerate(items):
                if item1[code_field] in processed_items:
                    continue
                
                similar_items = [item1]
                processed_items.add(item1[code_field])
                
                # Compare with remaining items
                for j, item2 in enumerate(items[i+1:], i+1):
                    if item2[code_field] in processed_items:
                        continue
                    
                    similarity = self._calculate_item_similarity(item1, item2)
                    
                    if similarity >= self.similarity_threshold:
                        similar_items.append(item2)
                        processed_items.add(item2[code_field])
                
                # Only include groups with more than one item
                if len(similar_items) > 1:
                    similar_groups.append({
                        'group_id': f"{item_type}_group_{len(similar_groups) + 1}",
                        'items': similar_items,
                        'item_count': len(similar_items),
                        'similarity_score': self._calculate_group_similarity(similar_items)
                    })
            
            return similar_groups
            
        except Exception as e:
            logger.warning("Failed to find similar items in list", error=str(e))
            return []
    
    def _calculate_item_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """Calculate similarity between two items"""
        try:
            # Description similarity
            desc1 = item1.get('descricao', '').lower().strip()
            desc2 = item2.get('descricao', '').lower().strip()
            
            if not desc1 or not desc2:
                return 0.0
            
            # Simple word-based similarity
            words1 = set(desc1.split())
            words2 = set(desc2.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            text_similarity = len(intersection) / len(union) if union else 0.0
            
            # NCM/CNAE similarity bonus
            code1 = item1.get('ncm') or item1.get('codigo_cnae', '')
            code2 = item2.get('ncm') or item2.get('codigo_cnae', '')
            
            code_bonus = 0.2 if code1 and code2 and code1 == code2 else 0.0
            
            # Category similarity bonus
            cat1 = item1.get('categoria', '')
            cat2 = item2.get('categoria', '')
            
            category_bonus = 0.1 if cat1 and cat2 and cat1 == cat2 else 0.0
            
            return min(1.0, text_similarity + code_bonus + category_bonus)
            
        except Exception as e:
            logger.warning("Failed to calculate item similarity", error=str(e))
            return 0.0
    
    def _calculate_group_similarity(self, items: List[Dict[str, Any]]) -> float:
        """Calculate average similarity within a group of items"""
        try:
            if len(items) < 2:
                return 1.0
            
            total_similarity = 0.0
            comparisons = 0
            
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    similarity = self._calculate_item_similarity(items[i], items[j])
                    total_similarity += similarity
                    comparisons += 1
            
            return total_similarity / comparisons if comparisons > 0 else 0.0
            
        except Exception as e:
            logger.warning("Failed to calculate group similarity", error=str(e))
            return 0.0
    
    async def _generate_optimization_recommendations(
        self, 
        method_stats: List[Dict], 
        low_confidence_items: List[Dict], 
        cache_stats: Dict, 
        category_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis"""
        try:
            recommendations = []
            
            # Cache optimization recommendations
            if cache_stats.get('cache_hit_potential', 0) < 0.5:
                recommendations.append({
                    'type': 'cache_optimization',
                    'priority': 'high',
                    'title': 'Improve Cache Hit Rate',
                    'description': f"Current cache hit potential is {cache_stats.get('cache_hit_potential', 0):.1%}. Consider increasing cache duration or improving similarity matching.",
                    'action': 'optimize_cache_settings'
                })
            
            # Low confidence items recommendations
            if len(low_confidence_items) > 10:
                recommendations.append({
                    'type': 'manual_review',
                    'priority': 'medium',
                    'title': 'Review Low Confidence Items',
                    'description': f"There are {len(low_confidence_items)} items with low categorization confidence that may need manual review.",
                    'action': 'schedule_manual_review',
                    'item_count': len(low_confidence_items)
                })
            
            # Method distribution recommendations
            ai_percentage = 0
            fallback_percentage = 0
            
            for stat in method_stats:
                if 'ai_enhanced' in stat.get('categorization_method', ''):
                    ai_percentage += stat.get('percentage', 0)
                elif 'fallback' in stat.get('categorization_method', ''):
                    fallback_percentage += stat.get('percentage', 0)
            
            if fallback_percentage > 30:
                recommendations.append({
                    'type': 'ai_improvement',
                    'priority': 'high',
                    'title': 'Reduce Fallback Categorization',
                    'description': f"Currently {fallback_percentage:.1f}% of items use fallback categorization. Consider improving AI model or training data.",
                    'action': 'improve_ai_categorization'
                })
            
            # Category distribution recommendations
            product_categories = category_analysis.get('product_categories', {})
            if len(product_categories) > 20:
                recommendations.append({
                    'type': 'category_consolidation',
                    'priority': 'low',
                    'title': 'Consider Category Consolidation',
                    'description': f"There are {len(product_categories)} product categories. Consider consolidating similar categories for better organization.",
                    'action': 'review_category_structure'
                })
            
            # Performance recommendations
            total_items = category_analysis.get('total_products', 0) + category_analysis.get('total_services', 0)
            if total_items > 1000 and cache_stats.get('active_entries', 0) < total_items * 0.1:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'title': 'Increase Cache Coverage',
                    'description': f"With {total_items} total items, cache coverage could be improved to reduce processing time.",
                    'action': 'expand_cache_coverage'
                })
            
            return recommendations
            
        except Exception as e:
            logger.warning("Failed to generate optimization recommendations", error=str(e))
            return []
    
    async def bulk_recategorize_similar_items(
        self, 
        group_id: str, 
        target_category: str, 
        target_subcategory: str,
        reviewer_id: str = None
    ) -> Dict[str, Any]:
        """
        Bulk recategorize a group of similar items
        
        Args:
            group_id: ID of the similar items group
            target_category: Category to assign to all items
            target_subcategory: Subcategory to assign to all items
            reviewer_id: ID of the person making the change
            
        Returns:
            Results of bulk recategorization
        """
        try:
            # This would need to be implemented with proper group tracking
            # For now, return a placeholder response
            
            logger.info(
                "Bulk recategorization requested for similar items",
                group_id=group_id,
                target_category=target_category,
                target_subcategory=target_subcategory,
                reviewer_id=reviewer_id
            )
            
            return {
                'success': True,
                'group_id': group_id,
                'target_category': target_category,
                'target_subcategory': target_subcategory,
                'items_updated': 0,
                'message': 'Bulk recategorization for similar items feature to be fully implemented'
            }
            
        except Exception as e:
            logger.error("Failed to bulk recategorize similar items", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def optimize_cache_performance(self) -> Dict[str, Any]:
        """
        Optimize cache performance by cleaning up and reorganizing
        
        Returns:
            Results of cache optimization
        """
        try:
            # Clean up expired entries
            cleaned_count = await self.cache_manager.cleanup_expired_entries()
            
            # Get current cache statistics
            cache_stats_before = await self.cache_manager.get_cache_statistics()
            
            # Identify and cache frequently accessed items that aren't cached
            await self._cache_frequent_items()
            
            # Get updated cache statistics
            cache_stats_after = await self.cache_manager.get_cache_statistics()
            
            logger.info(
                "Cache optimization completed",
                cleaned_entries=cleaned_count,
                active_entries_before=cache_stats_before.get('active_entries', 0),
                active_entries_after=cache_stats_after.get('active_entries', 0)
            )
            
            return {
                'success': True,
                'cleaned_entries': cleaned_count,
                'cache_stats_before': cache_stats_before,
                'cache_stats_after': cache_stats_after,
                'optimization_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to optimize cache performance", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _cache_frequent_items(self) -> None:
        """Cache items that are frequently accessed but not yet cached"""
        try:
            # Get items that might benefit from caching
            # This is a simplified implementation - in practice, you'd track access patterns
            
            # Get recently categorized items with high confidence
            recent_produtos = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_produtos')
                .select('*')
                .gte('categorization_confidence', 0.8)
                .gte('categorization_timestamp', (datetime.now(timezone.utc) - timedelta(days=7)).isoformat())
                .limit(50)
                .execute()
            )
            
            recent_servicos = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('dim_servicos')
                .select('*')
                .gte('categorization_confidence', 0.8)
                .gte('categorization_timestamp', (datetime.now(timezone.utc) - timedelta(days=7)).isoformat())
                .limit(50)
                .execute()
            )
            
            # Cache these items
            cached_count = 0
            
            for produto in recent_produtos.data:
                success = await self.cache_manager.cache_categorization(
                    {
                        'codigo_produto': produto['codigo_produto'],
                        'descricao': produto['descricao'],
                        'ncm': produto.get('ncm'),
                        'type': 'product'
                    },
                    produto['categoria'],
                    produto['subcategoria'],
                    produto['categorization_confidence'],
                    produto['categorization_method']
                )
                if success:
                    cached_count += 1
            
            for servico in recent_servicos.data:
                success = await self.cache_manager.cache_categorization(
                    {
                        'codigo_servico': servico['codigo_servico'],
                        'descricao': servico['descricao'],
                        'codigo_cnae': servico.get('codigo_cnae'),
                        'type': 'service'
                    },
                    servico['categoria'],
                    servico['subcategoria'],
                    servico['categorization_confidence'],
                    servico['categorization_method']
                )
                if success:
                    cached_count += 1
            
            logger.info("Frequent items cached", cached_count=cached_count)
            
        except Exception as e:
            logger.warning("Failed to cache frequent items", error=str(e))
    
    async def generate_categorization_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive categorization performance report
        
        Returns:
            Detailed categorization report
        """
        try:
            # Get analysis data
            analysis = await self.analyze_categorization_patterns()
            
            # Get manual review statistics
            manual_stats = await asyncio.to_thread(
                lambda: self.supabase_client.client.rpc('get_manual_review_stats').execute()
            )
            
            # Get recent categorization metrics
            recent_metrics = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_metrics')
                .select('*')
                .order('date', desc=True)
                .limit(30)
                .execute()
            )
            
            # Calculate performance trends
            performance_trends = self._calculate_performance_trends(recent_metrics.data)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                analysis, manual_stats.data, performance_trends
            )
            
            report = {
                'report_id': f"cat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'executive_summary': executive_summary,
                'detailed_analysis': analysis,
                'manual_review_stats': manual_stats.data,
                'performance_trends': performance_trends,
                'recent_metrics': recent_metrics.data[:7]  # Last 7 days
            }
            
            logger.info("Categorization report generated", report_id=report['report_id'])
            
            return report
            
        except Exception as e:
            logger.error("Failed to generate categorization report", error=str(e))
            return {
                'error': str(e),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_performance_trends(self, metrics_data: List[Dict]) -> Dict[str, Any]:
        """Calculate performance trends from metrics data"""
        try:
            if not metrics_data:
                return {}
            
            # Calculate cache hit rate trend
            cache_hit_rates = []
            ai_usage_rates = []
            avg_confidence_scores = []
            
            for metric in metrics_data:
                total_cat = metric.get('total_categorizations', 0)
                cache_hits = metric.get('cache_hits', 0)
                ai_cat = metric.get('ai_categorizations', 0)
                avg_conf = metric.get('average_confidence', 0)
                
                if total_cat > 0:
                    cache_hit_rates.append(cache_hits / total_cat)
                    ai_usage_rates.append(ai_cat / total_cat)
                
                if avg_conf:
                    avg_confidence_scores.append(float(avg_conf))
            
            return {
                'cache_hit_rate_trend': {
                    'current': cache_hit_rates[0] if cache_hit_rates else 0,
                    'average': sum(cache_hit_rates) / len(cache_hit_rates) if cache_hit_rates else 0,
                    'trend': 'improving' if len(cache_hit_rates) > 1 and cache_hit_rates[0] > cache_hit_rates[-1] else 'stable'
                },
                'ai_usage_trend': {
                    'current': ai_usage_rates[0] if ai_usage_rates else 0,
                    'average': sum(ai_usage_rates) / len(ai_usage_rates) if ai_usage_rates else 0,
                    'trend': 'improving' if len(ai_usage_rates) > 1 and ai_usage_rates[0] > ai_usage_rates[-1] else 'stable'
                },
                'confidence_trend': {
                    'current': avg_confidence_scores[0] if avg_confidence_scores else 0,
                    'average': sum(avg_confidence_scores) / len(avg_confidence_scores) if avg_confidence_scores else 0,
                    'trend': 'improving' if len(avg_confidence_scores) > 1 and avg_confidence_scores[0] > avg_confidence_scores[-1] else 'stable'
                }
            }
            
        except Exception as e:
            logger.warning("Failed to calculate performance trends", error=str(e))
            return {}
    
    def _generate_executive_summary(
        self, 
        analysis: Dict, 
        manual_stats: List[Dict], 
        trends: Dict
    ) -> Dict[str, Any]:
        """Generate executive summary of categorization performance"""
        try:
            # Extract key metrics
            cache_stats = analysis.get('cache_statistics', {})
            category_analysis = analysis.get('category_analysis', {})
            recommendations = analysis.get('recommendations', [])
            
            # Manual review stats
            manual_review_data = manual_stats[0] if manual_stats else {}
            
            # Performance indicators
            cache_hit_rate = cache_stats.get('cache_hit_potential', 0)
            total_items = category_analysis.get('total_products', 0) + category_analysis.get('total_services', 0)
            pending_reviews = manual_review_data.get('total_pending', 0)
            
            # Determine overall health
            health_score = 0
            if cache_hit_rate > 0.7:
                health_score += 30
            elif cache_hit_rate > 0.5:
                health_score += 20
            elif cache_hit_rate > 0.3:
                health_score += 10
            
            if pending_reviews < total_items * 0.05:  # Less than 5% pending
                health_score += 25
            elif pending_reviews < total_items * 0.1:  # Less than 10% pending
                health_score += 15
            
            if len(recommendations) < 3:
                health_score += 25
            elif len(recommendations) < 5:
                health_score += 15
            
            # AI usage effectiveness
            ai_trend = trends.get('ai_usage_trend', {})
            if ai_trend.get('current', 0) > 0.6:
                health_score += 20
            elif ai_trend.get('current', 0) > 0.4:
                health_score += 10
            
            # Determine health status
            if health_score >= 80:
                health_status = 'excellent'
            elif health_score >= 60:
                health_status = 'good'
            elif health_score >= 40:
                health_status = 'fair'
            else:
                health_status = 'needs_attention'
            
            return {
                'overall_health': health_status,
                'health_score': health_score,
                'key_metrics': {
                    'total_items_categorized': total_items,
                    'cache_hit_rate': f"{cache_hit_rate:.1%}",
                    'pending_manual_reviews': pending_reviews,
                    'ai_usage_rate': f"{ai_trend.get('current', 0):.1%}",
                    'active_cache_entries': cache_stats.get('active_entries', 0)
                },
                'top_recommendations': recommendations[:3],  # Top 3 recommendations
                'performance_summary': {
                    'cache_performance': 'good' if cache_hit_rate > 0.5 else 'needs_improvement',
                    'ai_effectiveness': 'good' if ai_trend.get('current', 0) > 0.5 else 'needs_improvement',
                    'manual_review_load': 'manageable' if pending_reviews < total_items * 0.1 else 'high'
                }
            }
            
        except Exception as e:
            logger.warning("Failed to generate executive summary", error=str(e))
            return {
                'overall_health': 'unknown',
                'error': str(e)
            }