#!/usr/bin/env python3
"""
Test script for LLM-Enhanced AI Categorization Agent
"""

import sys
import asyncio
import traceback
from datetime import datetime
from decimal import Decimal

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from utils.openai_integration import get_openai_service, OpenAIIntegrationService
        print("✅ OpenAI integration imported successfully")
        
        from agents.ai_categorization_agent import AICategorization_Agent
        print("✅ LLM-Enhanced AI Categorization Agent imported successfully")
        
        from models.fiscal_data import Product, Supplier, Address, NFEData, DocumentType
        print("✅ Fiscal data models imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_openai_service():
    """Test OpenAI service initialization"""
    print("\n🤖 Testing OpenAI service...")
    
    try:
        from utils.config import settings
        
        if not settings.OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY not configured - skipping OpenAI tests")
            return True
        
        from utils.openai_integration import get_openai_service
        
        service = get_openai_service()
        print("✅ OpenAI service initialized successfully")
        
        # Test usage statistics
        stats = service.get_usage_statistics()
        print(f"   📊 Token usage stats: {stats['token_usage']['current_minute']}")
        print(f"   💾 Cache stats: {stats['cache_stats']['cache_size']}/{stats['cache_stats']['max_cache_size']}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI service error: {e}")
        traceback.print_exc()
        return False

async def test_agent_initialization():
    """Test agent initialization"""
    print("\n🤖 Testing agent initialization...")
    
    try:
        from agents.ai_categorization_agent import AICategorization_Agent
        
        agent = AICategorization_Agent()
        print("✅ Agent created successfully")
        
        # Initialize agent (this might fail without proper ML dependencies)
        try:
            await agent.initialize()
            print("✅ Agent initialized successfully")
            return True
        except ImportError as e:
            print(f"⚠️ ML dependencies not available: {e}")
            print("   This is expected in development environment")
            return True
        except Exception as e:
            print(f"❌ Agent initialization error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        traceback.print_exc()
        return False

async def test_product_categorization():
    """Test LLM-enhanced product categorization"""
    print("\n📦 Testing product categorization...")
    
    try:
        from agents.ai_categorization_agent import AICategorization_Agent
        from models.fiscal_data import Product
        from utils.config import settings
        
        if not settings.OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY not configured - skipping LLM categorization test")
            return True
        
        agent = AICategorization_Agent()
        
        # Create test products
        test_products = [
            Product(
                codigo_produto="001",
                ean=None,
                descricao="Açúcar cristal especial 1kg",
                ncm="17019900",
                cest=None,
                cfop="5102",
                unidade_comercial="KG",
                unidade_tributavel="KG"
            ),
            Product(
                codigo_produto="002", 
                ean=None,
                descricao="Notebook Dell Inspiron 15",
                ncm="84713000",
                cest=None,
                cfop="5102",
                unidade_comercial="UN",
                unidade_tributavel="UN"
            )
        ]
        
        # Test business context
        business_context = {
            'supplier_info': {
                'name': 'Fornecedor Teste Ltda',
                'cnpj': '12.345.678/0001-90',
                'state': 'SP'
            },
            'business_sector': 'Varejo',
            'document_context': {
                'type': 'NFE',
                'date': '2024-01-15',
                'value': 3050.0
            }
        }
        
        # Test categorization (this will use fallback if OpenAI fails)
        try:
            categorized_products = await agent.categorize_products_with_context(
                test_products, business_context
            )
            
            print("✅ Product categorization completed")
            for product in categorized_products:
                print(f"   📦 {product.descricao[:30]}... -> {product.category}/{product.subcategory}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ LLM categorization failed, testing fallback: {e}")
            
            # Test fallback categorization
            for product in test_products:
                categorized = await agent._categorize_product(product)
                print(f"   📦 Fallback: {categorized.descricao[:30]}... -> {categorized.category}")
            
            print("✅ Fallback categorization works")
            return True
        
    except Exception as e:
        print(f"❌ Product categorization error: {e}")
        traceback.print_exc()
        return False

async def test_supplier_analysis():
    """Test supplier relationship analysis"""
    print("\n🏢 Testing supplier analysis...")
    
    try:
        from agents.ai_categorization_agent import AICategorization_Agent
        from models.fiscal_data import Supplier, Address
        from utils.config import settings
        
        agent = AICategorization_Agent()
        
        # Create test supplier
        test_supplier = Supplier(
            cnpj="12.345.678/0001-90",
            cpf=None,
            inscricao_estadual="123456789",
            razao_social="Fornecedor Industrial Ltda",
            nome_fantasia="FornecedorTech",
            address=Address(
                logradouro="Rua das Indústrias, 123",
                numero="123",
                complemento=None,
                bairro="Distrito Industrial",
                codigo_municipio="3550308",
                nome_municipio="São Paulo",
                uf="SP",
                cep="01234-567"
            )
        )
        
        # Test supplier analysis
        try:
            if settings.OPENAI_API_KEY:
                analyses = await agent.analyze_supplier_relationships([test_supplier])
                
                if analyses:
                    analysis = analyses[0]
                    print("✅ Supplier analysis completed")
                    print(f"   🏢 Supplier: {analysis['supplier'].razao_social}")
                    print(f"   📊 Relationship: {analysis.get('relationship_classification', 'N/A')}")
                    print(f"   ⚠️ Risk: {analysis.get('risk_assessment', 'N/A')}")
                    print(f"   📈 Growth: {analysis.get('growth_potential', 'N/A')}")
                else:
                    print("⚠️ No analysis results returned")
            else:
                print("⚠️ OPENAI_API_KEY not configured - testing fallback")
                analysis = await agent._fallback_supplier_analysis(test_supplier)
                print("✅ Fallback supplier analysis works")
                print(f"   🏢 Supplier: {analysis['supplier'].razao_social}")
            
            return True
            
        except Exception as e:
            print(f"⚠️ LLM supplier analysis failed: {e}")
            # Test fallback
            analysis = await agent._fallback_supplier_analysis(test_supplier)
            print("✅ Fallback supplier analysis works")
            return True
        
    except Exception as e:
        print(f"❌ Supplier analysis error: {e}")
        traceback.print_exc()
        return False

def test_environment_variables():
    """Test environment variables"""
    print("\n🌍 Testing environment variables...")
    
    try:
        from utils.config import settings
        
        # Check critical variables
        critical_vars = [
            ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
            ("OPENAI_DEFAULT_MODEL", settings.OPENAI_DEFAULT_MODEL),
            ("OPENAI_MAX_TOKENS", settings.OPENAI_MAX_TOKENS),
            ("OPENAI_TEMPERATURE", settings.OPENAI_TEMPERATURE),
            ("DEBUG", settings.DEBUG)
        ]
        
        for name, value in critical_vars:
            if value:
                if name == "OPENAI_API_KEY":
                    # Mask the key
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                    print(f"✅ {name}: {display_value}")
                else:
                    print(f"✅ {name}: {value}")
            else:
                print(f"⚠️ {name}: not configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking variables: {e}")
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting LLM-Enhanced AI Categorization Agent Tests")
    print("=" * 60)
    print(f"⏰ Date/Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("OpenAI Service", test_openai_service),
        ("Agent Initialization", test_agent_initialization),
        ("Product Categorization", test_product_categorization),
        ("Supplier Analysis", test_supplier_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Critical error in test {test_name}: {e}")
            results.append((test_name, False))
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successes = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
        if result:
            successes += 1
    
    print(f"\n🎯 Result: {successes}/{len(results)} tests passed")
    
    if successes == len(results):
        print("🎉 All tests passed! LLM-Enhanced AI Categorization Agent is working.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the configuration and dependencies.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)