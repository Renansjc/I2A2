"""
Test for Dimensional Processing Agent
"""

import asyncio
import pytest
from agents.dimensional_processing_agent import DimensionalProcessingAgent
from agents.dimensional_coordinator import DimensionalCoordinator


async def test_dimensional_processing_agent_initialization():
    """Test that the dimensional processing agent initializes correctly"""
    agent = DimensionalProcessingAgent()
    
    # Test initialization
    await agent.initialize()
    assert agent.agent_name == "dimensional_processing_agent"
    assert agent.supabase_client is not None
    
    # Test cleanup
    await agent.cleanup()


async def test_dimensional_coordinator_initialization():
    """Test that the dimensional coordinator initializes correctly"""
    coordinator = DimensionalCoordinator()
    
    # Test initialization
    await coordinator.initialize()
    assert coordinator.xml_agent is not None
    assert coordinator.categorization_agent is not None
    assert coordinator.dimensional_agent is not None
    
    # Test cleanup
    await coordinator.cleanup()


def test_data_normalization():
    """Test data normalization methods"""
    agent = DimensionalProcessingAgent()
    
    # Test emitente data normalization
    raw_emitente = {
        'cnpj': '12.345.678/0001-90',
        'razao_social': 'Empresa Teste Ltda',
        'nome_fantasia': 'Teste',
        'uf': 'SP',
        'cep': '01234-567'
    }
    
    normalized = agent._normalize_emitente_data(raw_emitente)
    assert 'cnpj' in normalized
    assert normalized['razao_social'] == 'Empresa Teste Ltda'
    assert normalized['uf'] == 'SP'
    
    # Test product data normalization
    raw_produto = {
        'codigo_produto': 'PROD001',
        'descricao': 'Produto de Teste',
        'ncm': '12345678',
        'cfop': '5102'
    }
    
    normalized_produto = agent._normalize_produto_data(raw_produto)
    assert normalized_produto['codigo_produto'] == 'PROD001'
    assert normalized_produto['descricao'] == 'Produto de Teste'


async def test_basic_categorization():
    """Test basic categorization methods"""
    agent = DimensionalProcessingAgent()
    
    # Test product categorization
    produto = {
        'codigo_produto': 'COMP001',
        'descricao': 'Notebook Dell Inspiron'
    }
    
    categorized = await agent._apply_basic_categorization(produto)
    assert categorized['categoria'] == 'Eletrônicos'
    assert categorized['subcategoria'] == 'Informática'
    
    # Test service categorization
    servico = {
        'codigo_servico': 'CONS001',
        'descricao': 'Consultoria em TI'
    }
    
    categorized_service = await agent._apply_basic_service_categorization(servico)
    assert categorized_service['categoria'] == 'Consultoria'
    assert categorized_service['subcategoria'] == 'Consultoria Empresarial'


def test_xml_utility_methods():
    """Test XML utility methods"""
    agent = DimensionalProcessingAgent()
    
    # Test XML text extraction
    from lxml import etree
    
    xml_content = '''<?xml version="1.0"?>
    <root>
        <item>
            <name>Test Item</name>
            <value>123.45</value>
        </item>
    </root>'''
    
    root = etree.fromstring(xml_content.encode('utf-8'))
    
    # Test text extraction
    name = agent._get_text(root, './/name')
    assert name == 'Test Item'
    
    # Test decimal extraction
    value = agent._get_decimal(root, './/value')
    assert value is not None
    assert float(value) == 123.45


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(test_dimensional_processing_agent_initialization())
    asyncio.run(test_dimensional_coordinator_initialization())
    test_data_normalization()
    asyncio.run(test_basic_categorization())
    test_xml_utility_methods()
    
    print("All tests passed!")