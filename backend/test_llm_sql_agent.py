"""
Test script for LLM-Enhanced SQL Agent
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Carregar arquivo .env
load_dotenv()

from agents.sql_agent import LLMEnhancedSQLAgent, QueryResult

async def test_llm_sql_agent():
    """Test the LLM-Enhanced SQL Agent functionality"""
    
    print("🚀 Testing LLM-Enhanced SQL Agent...")
    
    # Initialize the agent
    sql_agent = LLMEnhancedSQLAgent()
    
    try:
        # Initialize the agent
        await sql_agent.initialize()
        print("✅ Agent initialized successfully")
        
        # Test business-to-SQL translation
        print("\n📝 Testing business-to-SQL translation...")
        
        business_context = {
            'user_role': 'executive',
            'business_sector': 'retail',
            'time_period': 'last_quarter'
        }
        
        test_queries = [
            "Quais são os 5 maiores fornecedores por valor no último trimestre?",
            "Qual foi o total de impostos ICMS pagos este ano?",
            "Mostre o resumo mensal de vendas dos últimos 6 meses"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            
            try:
                # Test translation
                translation = await sql_agent.translate_business_query(query, business_context)
                
                print(f"📊 SQL Generated: {translation.sql_query[:100]}...")
                print(f"🎯 Confidence: {translation.confidence_score:.2f}")
                print(f"💡 Business Logic: {translation.business_logic_explanation[:100]}...")
                
                if translation.optimization_suggestions:
                    print(f"🔧 Suggestions: {', '.join(translation.optimization_suggestions[:2])}")
                
                # Test query optimization
                print("\n⚡ Testing query optimization...")
                optimization = await sql_agent.optimize_query_for_business(
                    translation.sql_query,
                    "Análise executiva de performance de fornecedores"
                )
                
                print(f"🚀 Optimized: {optimization.optimized_query != translation.sql_query}")
                print(f"📈 Reasoning: {optimization.optimization_reasoning[:100]}...")
                
                # Create mock query result for explanation test
                mock_result = QueryResult(
                    data=[
                        {'fornecedor': 'Empresa A', 'total': 150000.00},
                        {'fornecedor': 'Empresa B', 'total': 120000.00}
                    ],
                    metadata={'columns': ['fornecedor', 'total']},
                    execution_time=2.5,
                    row_count=2
                )
                
                # Test business explanation
                print("\n📋 Testing business explanation...")
                explanation = await sql_agent.explain_query_business_logic(
                    translation.sql_query,
                    mock_result
                )
                
                print(f"🎯 Purpose: {explanation.business_purpose[:100]}...")
                print(f"📊 Impact: {explanation.business_impact[:100]}...")
                print(f"🔍 Confidence: {explanation.confidence_assessment}")
                
                print("✅ Query processed successfully\n" + "="*50)
                
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
                continue
        
        print("\n🎉 LLM-Enhanced SQL Agent test completed!")
        
    except Exception as e:
        print(f"❌ Error during agent testing: {str(e)}")
        
    finally:
        # Cleanup
        await sql_agent.cleanup()

async def test_schema_context():
    """Test schema context functionality"""
    
    print("\n🗄️ Testing Schema Context...")
    
    sql_agent = LLMEnhancedSQLAgent()
    await sql_agent.initialize()
    
    # Test schema context retrieval
    schema_context = await sql_agent.schema_context.get_relevant_schema(
        "fornecedores com maior volume"
    )
    
    print(f"📋 Schema tables: {list(schema_context['tables'].keys())}")
    print(f"🔗 Relationships: {len(schema_context['relationships'])}")
    print(f"📏 Business rules: {len(schema_context['business_rules'])}")
    
    await sql_agent.cleanup()

async def test_prompt_templates():
    """Test prompt template functionality"""
    
    print("\n📝 Testing Prompt Templates...")
    
    sql_agent = LLMEnhancedSQLAgent()
    await sql_agent.initialize()
    
    # Test prompt template retrieval
    business_to_sql_prompt = sql_agent._get_business_to_sql_prompt()
    optimization_prompt = sql_agent._get_query_optimization_prompt()
    explanation_prompt = sql_agent._get_business_explanation_prompt()
    
    print(f"✅ Business-to-SQL prompt: {len(business_to_sql_prompt)} characters")
    print(f"✅ Optimization prompt: {len(optimization_prompt)} characters")
    print(f"✅ Explanation prompt: {len(explanation_prompt)} characters")
    
    # Test similar query examples
    examples = await sql_agent._get_similar_query_examples("fornecedores maiores")
    print(f"🔍 Found {len(examples)} similar examples")
    
    for example in examples:
        print(f"  - {example['question'][:50]}... (relevance: {example['relevance_score']:.2f})")
    
    await sql_agent.cleanup()

if __name__ == "__main__":
    print("🧪 LLM-Enhanced SQL Agent Test Suite")
    print("="*50)
    
    # Run tests
    asyncio.run(test_schema_context())
    asyncio.run(test_prompt_templates())
    
    # Note: The main LLM test requires OpenAI API key
    print("\n⚠️  Note: Full LLM testing requires OPENAI_API_KEY in environment")
    print("   Set OPENAI_API_KEY and run: python test_llm_sql_agent.py")
    
    # Uncomment to run full LLM test (requires API key)
    # asyncio.run(test_llm_sql_agent())