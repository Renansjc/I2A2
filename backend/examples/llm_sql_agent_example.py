"""
Example usage of LLM-Enhanced SQL Agent
Demonstrates business-to-SQL translation with intelligent optimization
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Carregar arquivo .env
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.sql_agent import LLMEnhancedSQLAgent

async def demonstrate_llm_sql_agent():
    """Demonstrate LLM-Enhanced SQL Agent capabilities"""
    
    print("🚀 LLM-Enhanced SQL Agent Demonstration")
    print("="*50)
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found in environment")
        print("   This demo will show the structure without making actual LLM calls")
        print()
    
    # Initialize the agent
    sql_agent = LLMEnhancedSQLAgent()
    await sql_agent.initialize()
    
    print("✅ LLM-Enhanced SQL Agent initialized")
    print()
    
    # Business context for executive user
    business_context = {
        'user_role': 'CFO',
        'business_sector': 'manufacturing',
        'company_size': 'large',
        'analysis_focus': 'cost_optimization',
        'time_period': 'current_year',
        'reporting_frequency': 'monthly'
    }
    
    # Example business questions in Portuguese
    business_questions = [
        {
            'question': 'Quais são os 10 maiores fornecedores por valor total no último trimestre?',
            'objective': 'Identificar fornecedores estratégicos para negociação de contratos'
        },
        {
            'question': 'Qual foi a evolução mensal dos impostos ICMS nos últimos 12 meses?',
            'objective': 'Análise de carga tributária para planejamento fiscal'
        },
        {
            'question': 'Quais categorias de produtos tiveram maior variação de preço este ano?',
            'objective': 'Identificar oportunidades de otimização de custos'
        },
        {
            'question': 'Mostre o resumo de compras por estado nos últimos 6 meses',
            'objective': 'Análise regional para otimização logística'
        }
    ]
    
    for i, item in enumerate(business_questions, 1):
        print(f"📋 Exemplo {i}: {item['question']}")
        print(f"🎯 Objetivo: {item['objective']}")
        print()
        
        try:
            # Step 1: Business-to-SQL Translation
            print("🔄 Etapa 1: Tradução Empresarial para SQL")
            
            if os.getenv('OPENAI_API_KEY'):
                translation = await sql_agent.translate_business_query(
                    item['question'], 
                    business_context
                )
                
                print(f"📊 SQL Gerado:")
                print(f"```sql")
                print(translation.sql_query)
                print(f"```")
                print(f"🎯 Confiança: {translation.confidence_score:.2f}")
                print(f"💡 Lógica Empresarial: {translation.business_logic_explanation}")
                
                if translation.optimization_suggestions:
                    print(f"🔧 Sugestões de Otimização:")
                    for suggestion in translation.optimization_suggestions:
                        print(f"   • {suggestion}")
                
                # Step 2: Query Optimization
                print("\n⚡ Etapa 2: Otimização Inteligente")
                
                optimization = await sql_agent.optimize_query_for_business(
                    translation.sql_query,
                    item['objective']
                )
                
                if optimization.optimized_query != translation.sql_query:
                    print("🚀 Consulta otimizada:")
                    print(f"```sql")
                    print(optimization.optimized_query)
                    print(f"```")
                    print(f"📈 Justificativa: {optimization.optimization_reasoning}")
                    
                    if optimization.performance_improvement:
                        print("📊 Melhorias de Performance:")
                        for key, value in optimization.performance_improvement.items():
                            print(f"   • {key}: {value}")
                else:
                    print("✅ Consulta já está otimizada")
                
                print(f"🎯 Alinhamento Empresarial: {optimization.business_alignment}")
                
            else:
                # Show structure without LLM calls
                print("📋 Estrutura da Tradução (sem chamada LLM):")
                print("   • SQL Query: [Consulta SQL gerada pelo LLM]")
                print("   • Business Logic: [Explicação da lógica empresarial]")
                print("   • Confidence Score: [0.0 - 1.0]")
                print("   • Optimization Suggestions: [Lista de sugestões]")
                print("   • Potential Issues: [Problemas identificados]")
                
                print("\n📋 Estrutura da Otimização (sem chamada LLM):")
                print("   • Optimized Query: [Consulta otimizada]")
                print("   • Optimization Reasoning: [Justificativa das otimizações]")
                print("   • Performance Improvement: [Métricas de melhoria]")
                print("   • Business Alignment: [Alinhamento com objetivos]")
            
        except Exception as e:
            print(f"❌ Erro ao processar consulta: {str(e)}")
        
        print("\n" + "="*50 + "\n")
    
    # Demonstrate additional capabilities
    print("🔧 Capacidades Adicionais do Agente:")
    print("   • Análise de contexto de esquema de banco de dados")
    print("   • Gerenciamento de templates de prompts em português")
    print("   • Aprendizado de padrões de consultas similares")
    print("   • Avaliação de qualidade de dados")
    print("   • Explicações empresariais de resultados")
    print("   • Integração com regras de negócio brasileiras")
    print("   • Suporte a documentos fiscais (NF-e, NFS-e)")
    print("   • Otimização baseada em objetivos empresariais")
    
    print("\n📊 Estatísticas do Agente:")
    print(f"   • Tabelas no esquema: {len(sql_agent.table_schema)}")
    print(f"   • Templates de consulta: {len(sql_agent.query_templates)}")
    print(f"   • Termos empresariais: {len(sql_agent.business_terms)}")
    print(f"   • Exemplos de consulta: {len(sql_agent.query_examples)}")
    print(f"   • Relacionamentos de dados: {len(sql_agent.schema_context.data_relationships)}")
    
    # Cleanup
    await sql_agent.cleanup()
    print("\n✅ Demonstração concluída!")

async def show_prompt_templates():
    """Show the prompt templates used by the agent"""
    
    print("\n📝 Templates de Prompts do LLM-Enhanced SQL Agent")
    print("="*50)
    
    sql_agent = LLMEnhancedSQLAgent()
    await sql_agent.initialize()
    
    templates = {
        'Business-to-SQL Translation': sql_agent._get_business_to_sql_prompt(),
        'Query Optimization': sql_agent._get_query_optimization_prompt(),
        'Business Explanation': sql_agent._get_business_explanation_prompt()
    }
    
    for name, template in templates.items():
        print(f"\n🔧 {name}:")
        print(f"   Tamanho: {len(template)} caracteres")
        print(f"   Variáveis: {template.count('{')//2} parâmetros")
        
        # Show first few lines
        lines = template.strip().split('\n')[:5]
        print("   Preview:")
        for line in lines:
            print(f"     {line}")
        print("     ...")
    
    await sql_agent.cleanup()

if __name__ == "__main__":
    print("🧪 LLM-Enhanced SQL Agent - Exemplo de Uso")
    print("="*50)
    
    # Run the demonstration
    asyncio.run(demonstrate_llm_sql_agent())
    
    # Show prompt templates
    asyncio.run(show_prompt_templates())
    
    print("\n💡 Para testar com LLM real:")
    print("   1. Configure OPENAI_API_KEY no ambiente")
    print("   2. Execute: python examples/llm_sql_agent_example.py")
    print("   3. O agente fará chamadas reais para OpenAI API")