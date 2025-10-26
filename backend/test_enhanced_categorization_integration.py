"""
Test Enhanced Categorization Integration
Tests the complete categorization pipeline with caching, fallback, and optimization
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from agents.dimensional_processing_agent import DimensionalProcessingAgent
from utils.enhanced_categorization import EnhancedCategorizationService
from utils.categorization_cache import CategorizationCacheManager
from utils.categorization_optimization import CategorizationOptimizationService


class TestEnhancedCategorizationIntegration:
    """Test suite for enhanced categorization integration"""
    
    @pytest.fixture
    def sample_product_data(self):
        """Sample product data for testing"""
        return {
            'codigo_produto': 'PROD001',
            'descricao': 'Notebook Dell Inspiron 15 3000',
            'ncm': '84713012',
            'cfop': '5102',
            'unidade_comercial': 'UN'
        }
    
    @pytest.fixture
    def sample_service_data(self):
        """Sample service data for testing"""
        return {
            'codigo_servico': 'SERV001',
            'descricao': 'Consultoria em Tecnologia da Informação',
            'codigo_cnae': '6201500'
        }
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client for testing"""
        mock_client = Mock()
        mock_client.client.table.return_value.upsert.return_value.execute.return_value.data = [{'id': 1}]
        mock_client.client.table.return_value.select.return_value.execute.return_value.data = []
        mock_client.client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 1}]
        return mock_client
    
    @pytest.mark.asyncio
    async def test_enhanced_categorization_service_initialization(self):
        """Test that the enhanced categorization service initializes correctly"""
        service = EnhancedCategorizationService()
        
        assert service.cache_manager is not None
        assert service.confidence_threshold == 0.7
        assert service.fallback_confidence == 0.6
        assert service.max_retries == 2
    
    @pytest.mark.asyncio
    async def test_categorization_cache_manager_initialization(self):
        """Test that the categorization cache manager initializes correctly"""
        cache_manager = CategorizationCacheManager()
        
        assert cache_manager.cache_duration_hours == 24 * 7  # 1 week
        assert cache_manager.similarity_threshold == 0.85
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, sample_product_data):
        """Test cache key generation for consistent caching"""
        cache_manager = CategorizationCacheManager()
        
        # Generate cache key
        cache_key = cache_manager._generate_cache_key(sample_product_data)
        
        assert cache_key is not None
        assert len(cache_key) == 32  # MD5 hash length
        
        # Same data should generate same key
        cache_key2 = cache_manager._generate_cache_key(sample_product_data)
        assert cache_key == cache_key2
    
    @pytest.mark.asyncio
    async def test_item_similarity_calculation(self):
        """Test similarity calculation between items"""
        cache_manager = CategorizationCacheManager()
        
        item1 = {
            'descricao': 'Notebook Dell Inspiron',
            'ncm': '84713012',
            'type': 'product'
        }
        
        item2 = {
            'descricao': 'Notebook Dell Vostro',
            'ncm': '84713012',
            'type': 'product'
        }
        
        cache_entry = {
            'item_description': 'Notebook Dell Inspiron',
            'item_ncm': '84713012'
        }
        
        similarity = cache_manager._calculate_similarity(item1, cache_entry)
        
        assert similarity > 0.8  # Should be high similarity
        assert similarity <= 1.0
    
    @pytest.mark.asyncio
    @patch('utils.enhanced_categorization.EnhancedCategorizationService._categorize_with_ai')
    async def test_categorize_items_with_ai_success(self, mock_ai_categorize, sample_product_data):
        """Test successful AI categorization"""
        # Mock AI categorization success
        mock_ai_categorize.return_value = {
            'category': 'Eletrônicos',
            'subcategory': 'Computadores',
            'confidence': 0.85,
            'method': 'ai_enhanced'
        }
        
        service = EnhancedCategorizationService()
        
        # Mock cache miss
        with patch.object(service.cache_manager, 'get_cached_categorization', return_value=None):
            with patch.object(service.cache_manager, 'cache_categorization', return_value=True):
                result = await service.categorize_items([sample_product_data], 'product')
        
        assert len(result) == 1
        assert result[0]['categoria'] == 'Eletrônicos'
        assert result[0]['subcategoria'] == 'Computadores'
        assert result[0]['categorization_confidence'] == 0.85
        assert result[0]['categorization_method'] == 'ai_enhanced'
        assert result[0]['cache_hit'] == False
    
    @pytest.mark.asyncio
    async def test_categorize_items_with_cache_hit(self, sample_product_data):
        """Test categorization with cache hit"""
        service = EnhancedCategorizationService()
        
        # Mock cache hit
        cached_result = {
            'category': 'Eletrônicos',
            'subcategory': 'Computadores',
            'confidence': 0.9,
            'cache_hit': True,
            'cache_type': 'exact_match'
        }
        
        with patch.object(service.cache_manager, 'get_cached_categorization', return_value=cached_result):
            result = await service.categorize_items([sample_product_data], 'product')
        
        assert len(result) == 1
        assert result[0]['categoria'] == 'Eletrônicos'
        assert result[0]['subcategoria'] == 'Computadores'
        assert result[0]['categorization_confidence'] == 0.9
        assert result[0]['categorization_method'] == 'cached_exact_match'
        assert result[0]['cache_hit'] == True
    
    @pytest.mark.asyncio
    @patch('utils.enhanced_categorization.EnhancedCategorizationService._categorize_with_ai')
    async def test_categorize_items_with_fallback(self, mock_ai_categorize, sample_product_data):
        """Test categorization fallback when AI fails"""
        # Mock AI categorization failure
        mock_ai_categorize.return_value = None
        
        service = EnhancedCategorizationService()
        
        # Mock cache miss
        with patch.object(service.cache_manager, 'get_cached_categorization', return_value=None):
            with patch.object(service.cache_manager, 'cache_categorization', return_value=True):
                result = await service.categorize_items([sample_product_data], 'product')
        
        assert len(result) == 1
        assert result[0]['categoria'] is not None  # Should have fallback category
        assert result[0]['categorization_method'] == 'rule_based_fallback'
        assert result[0]['categorization_confidence'] == 0.6  # Fallback confidence
        assert result[0]['cache_hit'] == False
    
    @pytest.mark.asyncio
    async def test_product_fallback_categorization(self, sample_product_data):
        """Test rule-based fallback categorization for products"""
        service = EnhancedCategorizationService()
        
        # Test notebook categorization
        result = await service._categorize_product_fallback(sample_product_data)
        
        assert result['category'] == 'Eletrônicos'
        assert 'Informática' in result['subcategory'] or 'Computadores' in result['subcategory']
    
    @pytest.mark.asyncio
    async def test_service_fallback_categorization(self, sample_service_data):
        """Test rule-based fallback categorization for services"""
        service = EnhancedCategorizationService()
        
        # Test IT consulting categorization
        result = await service._categorize_service_fallback(sample_service_data)
        
        assert result['category'] == 'Tecnologia da Informação'
        assert 'Software' in result['subcategory']
    
    @pytest.mark.asyncio
    async def test_dimensional_processing_agent_integration(self, mock_supabase_client):
        """Test integration with dimensional processing agent"""
        with patch('agents.dimensional_processing_agent.get_supabase_client', return_value=mock_supabase_client):
            agent = DimensionalProcessingAgent()
            
            # Mock XML root with product data
            mock_xml_root = Mock()
            
            # Mock the extraction methods
            with patch.object(agent, '_extract_produtos_data', return_value=[{
                'codigo_produto': 'PROD001',
                'descricao': 'Notebook Dell',
                'ncm': '84713012'
            }]):
                with patch('utils.enhanced_categorization.EnhancedCategorizationService.categorize_items') as mock_categorize:
                    mock_categorize.return_value = [{
                        'codigo_produto': 'PROD001',
                        'descricao': 'Notebook Dell',
                        'ncm': '84713012',
                        'categoria': 'Eletrônicos',
                        'subcategoria': 'Computadores',
                        'categorization_confidence': 0.85,
                        'categorization_method': 'ai_enhanced',
                        'cache_hit': False
                    }]
                    
                    result = await agent.process_produtos_data_enhanced(mock_xml_root)
                    
                    assert len(result) == 1
                    assert result[0] == 'PROD001'
    
    @pytest.mark.asyncio
    async def test_categorization_optimization_service(self):
        """Test categorization optimization service"""
        optimization_service = CategorizationOptimizationService()
        
        assert optimization_service.cache_manager is not None
        assert optimization_service.batch_size == 50
        assert optimization_service.similarity_threshold == 0.9
    
    @pytest.mark.asyncio
    @patch('utils.categorization_optimization.get_supabase_client')
    async def test_categorization_pattern_analysis(self, mock_get_client):
        """Test categorization pattern analysis"""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.client.rpc.return_value.execute.return_value.data = []
        mock_client.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []
        mock_get_client.return_value = mock_client
        
        optimization_service = CategorizationOptimizationService()
        
        # Mock cache manager
        with patch.object(optimization_service.cache_manager, 'get_cache_statistics', return_value={}):
            result = await optimization_service.analyze_categorization_patterns()
        
        assert 'method_statistics' in result
        assert 'cache_statistics' in result
        assert 'recommendations' in result
        assert 'analysis_timestamp' in result
    
    @pytest.mark.asyncio
    async def test_manual_categorization_override(self, mock_supabase_client):
        """Test manual categorization override functionality"""
        with patch('agents.dimensional_processing_agent.get_supabase_client', return_value=mock_supabase_client):
            agent = DimensionalProcessingAgent()
            
            # Mock successful update
            mock_supabase_client.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
                'codigo_produto': 'PROD001',
                'descricao': 'Test Product'
            }]
            
            with patch('utils.enhanced_categorization.EnhancedCategorizationService') as mock_service:
                mock_service.return_value.cache_manager.invalidate_cache_for_item = AsyncMock(return_value=True)
                result = await agent.apply_manual_categorization_override(
                    'PROD001', 'product', 'Nova Categoria', 'Nova Subcategoria', 'reviewer123'
                )
            
            assert result['success'] == True
            assert result['item_code'] == 'PROD001'
            assert result['new_category'] == 'Nova Categoria'
            assert result['new_subcategory'] == 'Nova Subcategoria'
    
    @pytest.mark.asyncio
    async def test_bulk_recategorization_by_pattern(self, mock_supabase_client):
        """Test bulk recategorization by pattern"""
        with patch('agents.dimensional_processing_agent.get_supabase_client', return_value=mock_supabase_client):
            agent = DimensionalProcessingAgent()
            
            # Mock search results
            mock_supabase_client.client.table.return_value.select.return_value.ilike.return_value.execute.return_value.data = [
                {'codigo_produto': 'PROD001', 'descricao': 'Notebook Dell'},
                {'codigo_produto': 'PROD002', 'descricao': 'Notebook HP'}
            ]
            
            # Mock successful updates
            with patch.object(agent, 'apply_manual_categorization_override') as mock_override:
                mock_override.return_value = {'success': True}
                
                result = await agent.bulk_recategorize_by_pattern(
                    'Notebook', 'Eletrônicos', 'Computadores Portáteis', 'product', 'reviewer123'
                )
            
            assert result['success'] == True
            assert result['pattern'] == 'Notebook'
            assert result['new_category'] == 'Eletrônicos'
            assert result['updated_count'] == 2
    
    @pytest.mark.asyncio
    async def test_categorization_performance_metrics(self, mock_supabase_client):
        """Test categorization performance metrics collection"""
        with patch('agents.dimensional_processing_agent.get_supabase_client', return_value=mock_supabase_client):
            agent = DimensionalProcessingAgent()
            
            # Mock metrics data
            mock_supabase_client.client.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 5
            mock_supabase_client.client.table.return_value.select.return_value.execute.return_value.data = []
            
            with patch('utils.enhanced_categorization.EnhancedCategorizationService.get_categorization_statistics') as mock_stats:
                mock_stats.return_value = {
                    'cache_statistics': {'active_entries': 100},
                    'recent_metrics': []
                }
                
                result = await agent.get_categorization_performance_metrics()
            
            assert 'cache_statistics' in result
            assert 'dimensional_processing_metrics' in result
    
    @pytest.mark.asyncio
    async def test_error_handling_in_categorization(self, sample_product_data):
        """Test error handling in categorization process"""
        service = EnhancedCategorizationService()
        
        # Mock cache manager to raise exception
        with patch.object(service.cache_manager, 'get_cached_categorization', side_effect=Exception("Cache error")):
            result = await service.categorize_items([sample_product_data], 'product')
        
        # Should still return results with fallback categorization
        assert len(result) == 1
        assert result[0]['categorization_method'] == 'error_fallback'
        assert 'error' in result[0]
    
    @pytest.mark.asyncio
    async def test_confidence_validation_and_low_confidence_handling(self, mock_supabase_client):
        """Test handling of low confidence categorizations"""
        with patch('agents.dimensional_processing_agent.get_supabase_client', return_value=mock_supabase_client):
            agent = DimensionalProcessingAgent()
            
            # Mock low confidence items
            low_confidence_items = [
                {
                    'codigo_produto': 'PROD001',
                    'descricao': 'Unknown Product',
                    'categoria': 'Outros',
                    'confidence': 0.4,
                    'method': 'fallback'
                }
            ]
            
            # Test storing low confidence items
            await agent._store_low_confidence_items(low_confidence_items, 'product')
            
            # Verify insert was called
            mock_supabase_client.client.table.assert_called()
    
    def test_categorization_method_constants(self):
        """Test that categorization method constants are properly defined"""
        service = EnhancedCategorizationService()
        
        # Test confidence thresholds
        assert service.confidence_threshold > 0
        assert service.confidence_threshold <= 1.0
        assert service.fallback_confidence > 0
        assert service.fallback_confidence <= 1.0
        assert service.fallback_confidence <= service.confidence_threshold
        
        # Test retry configuration
        assert service.max_retries > 0
        assert service.max_retries <= 5  # Reasonable upper limit


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])