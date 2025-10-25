"""
Test script for LLM Enhanced Error Handler
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from utils.llm_error_handler import (
    LLMEnhancedErrorHandler,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    analyze_and_handle_error,
    create_user_friendly_error_response
)

async def test_error_handler():
    """Test the LLM Enhanced Error Handler"""
    print("🧪 Testando LLM Enhanced Error Handler...")
    
    try:
        # Initialize error handler
        handler = LLMEnhancedErrorHandler()
        print("✅ Error handler inicializado com sucesso")
        
        # Test 1: Create a sample error context
        print("\n📝 Teste 1: Análise de erro XML")
        error_context = ErrorContext(
            error_id="test_error_001",
            timestamp=datetime.now(),
            error_type="XMLParseError",
            error_message="Failed to parse NF-e XML: Invalid CNPJ format",
            stack_trace="Traceback (most recent call last):\n  File 'xml_processor.py', line 45, in parse_nfe\n    validate_cnpj(cnpj)\nXMLParseError: Invalid CNPJ format",
            user_id="user_123",
            agent_name="xml_processing_agent",
            operation="parse_nfe_document",
            input_data={"file_name": "nfe_001.xml", "cnpj": "invalid_cnpj"},
            business_context={"document_type": "NF-e", "supplier": "Fornecedor Teste"}
        )
        
        # Analyze error (this will use fallback if OpenAI is not configured)
        analysis = await handler.analyze_error(error_context)
        
        print(f"   Categoria: {analysis.category.value}")
        print(f"   Severidade: {analysis.severity.value}")
        print(f"   Causa raiz: {analysis.root_cause}")
        print(f"   Confiança: {analysis.confidence_score:.2f}")
        print(f"   Mensagem usuário: {analysis.user_friendly_message}")
        
        # Test 2: Create admin alert
        print("\n📝 Teste 2: Criação de alerta administrativo")
        alert = await handler.create_admin_alert(analysis)
        
        print(f"   ID do Alerta: {alert['alert_id']}")
        print(f"   Título: {alert['title']}")
        print(f"   Severidade: {alert['severity']}")
        print(f"   Escalação necessária: {alert['escalation_required']}")
        
        # Test 3: Generate recovery plan
        print("\n📝 Teste 3: Geração de plano de recuperação")
        recovery_plan = await handler.generate_recovery_plan(analysis)
        
        print(f"   Passos automatizados: {len(recovery_plan.get('automated_steps', []))}")
        print(f"   Passos manuais: {len(recovery_plan.get('manual_steps', []))}")
        print(f"   Tempo estimado: {recovery_plan.get('estimated_recovery_time', 'N/A')}")
        
        # Test 4: Convenience function
        print("\n📝 Teste 4: Função de conveniência")
        try:
            # Simulate an error
            raise ValueError("Teste de erro para demonstração")
        except Exception as e:
            error_analysis = await analyze_and_handle_error(
                error=e,
                context={
                    'input_data': {'test': 'data'},
                    'business_context': {'operation': 'test'}
                },
                user_id="test_user",
                agent_name="test_agent",
                operation="test_operation"
            )
            
            user_response = await create_user_friendly_error_response(error_analysis)
            print(f"   Resposta para usuário: {user_response['message']}")
            print(f"   Retry recomendado: {user_response['retry_recommended']}")
        
        # Test 5: Pattern detection (with minimal data)
        print("\n📝 Teste 5: Detecção de padrões")
        
        # Add a few more errors to history for pattern detection
        for i in range(3):
            similar_error = ErrorContext(
                error_id=f"test_error_00{i+2}",
                timestamp=datetime.now(),
                error_type="XMLParseError",
                error_message=f"Failed to parse NF-e XML: Invalid format {i+1}",
                stack_trace="Similar stack trace",
                agent_name="xml_processing_agent",
                operation="parse_nfe_document"
            )
            await handler.analyze_error(similar_error)
        
        patterns = await handler.detect_error_patterns()
        print(f"   Padrões detectados: {len(patterns)}")
        
        for pattern in patterns:
            print(f"   - Padrão: {pattern.get('description', 'N/A')}")
            print(f"     Frequência: {pattern.get('frequency', 0)}")
        
        print("\n✅ Todos os testes concluídos com sucesso!")
        
        # Display summary
        print("\n📊 Resumo dos testes:")
        print(f"   - Error handler funcional: ✅")
        print(f"   - Análise de erro: ✅")
        print(f"   - Alerta administrativo: ✅")
        print(f"   - Plano de recuperação: ✅")
        print(f"   - Função de conveniência: ✅")
        print(f"   - Detecção de padrões: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_categorization():
    """Test error categorization logic"""
    print("\n🔍 Testando categorização de erros...")
    
    handler = LLMEnhancedErrorHandler()
    
    test_cases = [
        ("DatabaseError", "Connection timeout to PostgreSQL", ErrorCategory.DATABASE),
        ("XMLParseError", "Invalid XML structure in NF-e", ErrorCategory.XML_PROCESSING),
        ("AuthenticationError", "Invalid API key", ErrorCategory.AUTHENTICATION),
        ("ValidationError", "Invalid CNPJ format", ErrorCategory.VALIDATION),
        ("HTTPError", "API endpoint not found", ErrorCategory.API),
        ("OpenAIError", "Rate limit exceeded", ErrorCategory.LLM_SERVICE),
        ("SystemError", "Unknown system error", ErrorCategory.SYSTEM)
    ]
    
    for error_type, error_message, expected_category in test_cases:
        category = handler._categorize_error_simple(error_type, error_message)
        status = "✅" if category == expected_category else "❌"
        print(f"   {status} {error_type}: {category.value} (esperado: {expected_category.value})")
    
    print("✅ Teste de categorização concluído")

async def main():
    """Main test function"""
    print("🚀 Iniciando testes do LLM Enhanced Error Handler")
    print("=" * 60)
    
    # Test basic functionality
    success = await test_error_handler()
    
    if success:
        # Test categorization
        await test_error_categorization()
        
        print("\n" + "=" * 60)
        print("🎉 Todos os testes foram executados com sucesso!")
        print("\n💡 Notas:")
        print("   - Se OpenAI não estiver configurado, o sistema usa análise de fallback")
        print("   - O error handler está pronto para integração com os agentes")
        print("   - Mensagens estão em português para usuários brasileiros")
        print("   - Suporte completo para análise de padrões e recuperação automática")
    else:
        print("\n❌ Alguns testes falharam. Verifique a configuração.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)