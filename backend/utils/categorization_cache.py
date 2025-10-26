"""
Categorization Cache Manager for optimizing AI categorization performance
"""

import structlog
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from utils.database import get_supabase_client

logger = structlog.get_logger()


class CategorizationCacheManager:
    """Manages caching of AI categorization results for improved performance"""
    
    def __init__(self):
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.cache_duration_hours = 24 * 7  # Cache for 1 week
        self.similarity_threshold = 0.85  # Threshold for considering items similar
    
    def _generate_cache_key(self, item_data: Dict[str, Any]) -> str:
        """Generate a unique cache key for an item"""
        try:
            # Create a normalized representation of the item for caching
            cache_data = {
                'description': item_data.get('descricao', '').lower().strip(),
                'ncm': item_data.get('ncm', '').strip(),
                'cfop': item_data.get('cfop', '').strip(),
                'type': item_data.get('type', 'product')
            }
            
            # Create hash of the normalized data
            cache_string = json.dumps(cache_data, sort_keys=True)
            return hashlib.md5(cache_string.encode()).hexdigest()
            
        except Exception as e:
            logger.warning("Failed to generate cache key", error=str(e))
            return hashlib.md5(str(item_data).encode()).hexdigest()
    
    async def get_cached_categorization(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached categorization for an item
        
        Args:
            item_data: Item data to check for cached categorization
            
        Returns:
            Cached categorization data or None if not found
        """
        try:
            import asyncio
            
            cache_key = self._generate_cache_key(item_data)
            
            # Check for exact match first
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .select('*')
                .eq('cache_key', cache_key)
                .gte('expires_at', datetime.now(timezone.utc).isoformat())
                .limit(1)
                .execute()
            )
            
            if result.data:
                cache_entry = result.data[0]
                logger.info(
                    "Cache hit for exact match",
                    cache_key=cache_key,
                    category=cache_entry.get('category')
                )
                return {
                    'category': cache_entry['category'],
                    'subcategory': cache_entry['subcategory'],
                    'confidence': cache_entry['confidence'],
                    'cache_hit': True,
                    'cache_type': 'exact_match'
                }
            
            # If no exact match, try to find similar items
            similar_categorization = await self._find_similar_categorization(item_data)
            if similar_categorization:
                return similar_categorization
            
            return None
            
        except Exception as e:
            logger.warning("Failed to get cached categorization", error=str(e))
            return None
    
    async def cache_categorization(
        self, 
        item_data: Dict[str, Any], 
        category: str, 
        subcategory: str, 
        confidence: float,
        categorization_method: str = 'ai_enhanced'
    ) -> bool:
        """
        Cache categorization result for an item
        
        Args:
            item_data: Item data that was categorized
            category: Assigned category
            subcategory: Assigned subcategory
            confidence: Confidence score of the categorization
            categorization_method: Method used for categorization
            
        Returns:
            True if caching was successful, False otherwise
        """
        try:
            import asyncio
            
            cache_key = self._generate_cache_key(item_data)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.cache_duration_hours)
            
            cache_entry = {
                'cache_key': cache_key,
                'item_description': item_data.get('descricao', '')[:200],  # Truncate for storage
                'item_ncm': item_data.get('ncm', ''),
                'item_cfop': item_data.get('cfop', ''),
                'item_type': item_data.get('type', 'product'),
                'category': category,
                'subcategory': subcategory,
                'confidence': confidence,
                'categorization_method': categorization_method,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'expires_at': expires_at.isoformat(),
                'usage_count': 1
            }
            
            # Upsert cache entry
            await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .upsert(cache_entry, on_conflict='cache_key')
                .execute()
            )
            
            logger.info(
                "Categorization cached",
                cache_key=cache_key,
                category=category,
                subcategory=subcategory
            )
            
            return True
            
        except Exception as e:
            logger.warning("Failed to cache categorization", error=str(e))
            return False
    
    async def _find_similar_categorization(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find categorization for similar items using text similarity
        
        Args:
            item_data: Item data to find similar categorization for
            
        Returns:
            Similar categorization data or None if not found
        """
        try:
            import asyncio
            
            description = item_data.get('descricao', '').lower().strip()
            ncm = item_data.get('ncm', '').strip()
            
            if not description:
                return None
            
            # Get recent cache entries for similar analysis
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .select('*')
                .gte('expires_at', datetime.now(timezone.utc).isoformat())
                .order('created_at', desc=True)
                .limit(100)
                .execute()
            )
            
            if not result.data:
                return None
            
            # Find most similar item
            best_match = None
            best_similarity = 0.0
            
            for cache_entry in result.data:
                similarity = self._calculate_similarity(item_data, cache_entry)
                
                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = cache_entry
            
            if best_match:
                # Update usage count for the matched entry
                await self._increment_usage_count(best_match['cache_key'])
                
                logger.info(
                    "Cache hit for similar item",
                    similarity=best_similarity,
                    category=best_match['category']
                )
                
                return {
                    'category': best_match['category'],
                    'subcategory': best_match['subcategory'],
                    'confidence': best_match['confidence'] * best_similarity,  # Adjust confidence based on similarity
                    'cache_hit': True,
                    'cache_type': 'similar_match',
                    'similarity_score': best_similarity
                }
            
            return None
            
        except Exception as e:
            logger.warning("Failed to find similar categorization", error=str(e))
            return None
    
    def _calculate_similarity(self, item_data: Dict[str, Any], cache_entry: Dict[str, Any]) -> float:
        """
        Calculate similarity between two items
        
        Args:
            item_data: Current item data
            cache_entry: Cached item data
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Text similarity based on description
            desc1 = item_data.get('descricao', '').lower().strip()
            desc2 = cache_entry.get('item_description', '').lower().strip()
            
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
            
            # NCM code similarity (exact match gives bonus)
            ncm1 = item_data.get('ncm', '').strip()
            ncm2 = cache_entry.get('item_ncm', '').strip()
            
            ncm_bonus = 0.2 if ncm1 and ncm2 and ncm1 == ncm2 else 0.0
            
            # CFOP similarity (exact match gives small bonus)
            cfop1 = item_data.get('cfop', '').strip()
            cfop2 = cache_entry.get('item_cfop', '').strip()
            
            cfop_bonus = 0.1 if cfop1 and cfop2 and cfop1 == cfop2 else 0.0
            
            # Combined similarity score
            total_similarity = min(1.0, text_similarity + ncm_bonus + cfop_bonus)
            
            return total_similarity
            
        except Exception as e:
            logger.warning("Failed to calculate similarity", error=str(e))
            return 0.0
    
    async def _increment_usage_count(self, cache_key: str) -> None:
        """Increment usage count for a cache entry"""
        try:
            import asyncio
            
            await asyncio.to_thread(
                lambda: self.supabase_client.client.rpc(
                    'increment_cache_usage',
                    {'cache_key_param': cache_key}
                ).execute()
            )
            
        except Exception as e:
            logger.warning("Failed to increment usage count", error=str(e))
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            import asyncio
            
            # Get total cache entries
            total_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .select('id', count='exact')
                .execute()
            )
            
            # Get active cache entries (not expired)
            active_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .select('id', count='exact')
                .gte('expires_at', datetime.now(timezone.utc).isoformat())
                .execute()
            )
            
            # Get most used categories
            categories_result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .select('category, subcategory')
                .gte('expires_at', datetime.now(timezone.utc).isoformat())
                .execute()
            )
            
            # Calculate category distribution
            category_counts = {}
            for entry in categories_result.data:
                category = entry['category']
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                'total_entries': total_result.count,
                'active_entries': active_result.count,
                'expired_entries': total_result.count - active_result.count,
                'cache_hit_potential': active_result.count / max(1, total_result.count),
                'top_categories': sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                'cache_duration_hours': self.cache_duration_hours,
                'similarity_threshold': self.similarity_threshold
            }
            
        except Exception as e:
            logger.error("Failed to get cache statistics", error=str(e))
            return {
                'error': str(e),
                'total_entries': 0,
                'active_entries': 0
            }
    
    async def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            import asyncio
            
            # Delete expired entries
            result = await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .delete()
                .lt('expires_at', datetime.now(timezone.utc).isoformat())
                .execute()
            )
            
            cleaned_count = len(result.data) if result.data else 0
            
            logger.info(
                "Cache cleanup completed",
                entries_cleaned=cleaned_count
            )
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired entries", error=str(e))
            return 0
    
    async def invalidate_cache_for_item(self, item_data: Dict[str, Any]) -> bool:
        """
        Invalidate cache entry for a specific item
        
        Args:
            item_data: Item data to invalidate cache for
            
        Returns:
            True if invalidation was successful
        """
        try:
            import asyncio
            
            cache_key = self._generate_cache_key(item_data)
            
            await asyncio.to_thread(
                lambda: self.supabase_client.client.table('categorization_cache')
                .delete()
                .eq('cache_key', cache_key)
                .execute()
            )
            
            logger.info("Cache invalidated for item", cache_key=cache_key)
            return True
            
        except Exception as e:
            logger.warning("Failed to invalidate cache", error=str(e))
            return False
    
    async def bulk_recategorize(self, category_mapping: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Bulk recategorize items based on category mapping
        
        Args:
            category_mapping: Dictionary mapping old categories to new categories
                             Format: {'old_category': {'category': 'new_category', 'subcategory': 'new_subcategory'}}
            
        Returns:
            Results of bulk recategorization
        """
        try:
            import asyncio
            
            updated_count = 0
            errors = []
            
            for old_category, new_mapping in category_mapping.items():
                try:
                    # Update cache entries with old category
                    result = await asyncio.to_thread(
                        lambda: self.supabase_client.client.table('categorization_cache')
                        .update({
                            'category': new_mapping['category'],
                            'subcategory': new_mapping['subcategory'],
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        })
                        .eq('category', old_category)
                        .execute()
                    )
                    
                    updated_count += len(result.data) if result.data else 0
                    
                except Exception as e:
                    errors.append({
                        'old_category': old_category,
                        'error': str(e)
                    })
            
            logger.info(
                "Bulk recategorization completed",
                updated_count=updated_count,
                errors_count=len(errors)
            )
            
            return {
                'updated_count': updated_count,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            logger.error("Failed to perform bulk recategorization", error=str(e))
            return {
                'updated_count': 0,
                'errors': [{'error': str(e)}],
                'success': False
            }