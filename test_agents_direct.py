#!/usr/bin/env python3
"""
Teste direto dos 3 agentes IA para debug
"""

import sys
import os
sys.path.append('backend')

from agents.xml_processing_agent import XMLProcessingAgent
from agents.categorization_agent import CategorizationAgent
from agents.insights_agent import InsightsAgent, QueryContext

def test_agents():
    """Testa os 3 agentes diretamente"""
    
    print("🧪 Testando os 3 agentes IA diretamente...\n")
    
    # Ler arquivo XML de exemplo
    xml_file_path = "xml_nf/exemplo.xml"
    
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        print(f"✅ Arquivo XML carregado: {len(xml_content)} caracteres")
    except Exception as e:
        print(f"❌ Erro ao carregar XML: {e}")
        return False
    
    # TESTE AGENTE 1: XML Processing
    print(f"\n🤖 AGENTE 1: XML Processing Agent")
    try:
        xml_agent = XMLProcessingAgent()
        print(f"   Agente inicializado: {xml_agent.name} v{xml_agent.version}")
        
        xml_result = xml_agent.process_xml(xml_content)
        extracted_data = xml_result.get("extracted_data", {})
        validation_result = xml_result.get("validation", {})
        
        print(f"   ✅ Processamento concluído")
        print(f"   📊 Dados extraídos:")
        print(f"      Emitente: {extracted_data.get('emitente', {}).get('razao_social', 'N/A')}")
        print(f"      Destinatário: {extracted_data.get('destinatario', {}).get('razao_social', 'N/A')}")
        print(f"      Valor Total: R$ {extracted_data.get('valor_total', 'N/A')}")
        print(f"      Itens: {len(extracted_data.get('itens', []))}")
        print(f"   🔍 Validação: {validation_result.get('valid', False)}")
        
    except Exception as e:
        print(f"   ❌ Erro no Agente 1: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # TESTE AGENTE 2: Categorização
    print(f"\n🤖 AGENTE 2: Categorization Agent")
    try:
        # Verificar se OpenAI está configurada
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"   ⚠️  OPENAI_API_KEY não encontrada no ambiente")
            return False
        
        categorization_agent = CategorizationAgent(openai_key, "gpt-4o-mini")
        print(f"   Agente inicializado: {categorization_agent.name} v{categorization_agent.version}")
        print(f"   OpenAI configurada: {categorization_agent.llm is not None}")
        
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        
        print(f"   ✅ Categorização concluída")
        print(f"   📦 Itens categorizados: {len(categorized_items)}")
        
        for i, item in enumerate(categorized_items[:3]):  # Mostrar apenas os 3 primeiros
            print(f"      Item {i+1}: {item.get('descricao', 'N/A')[:50]}...")
            print(f"               Categoria: {item.get('categoria', 'N/A')}")
            print(f"               Confiança: {item.get('categoria_confianca', 'N/A')}")
        
        print(f"   🏢 Fornecedor:")
        print(f"      Tipo: {supplier_category.get('type', 'N/A')}")
        print(f"      Confiança: {supplier_category.get('confidence', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Erro no Agente 2: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # TESTE AGENTE 3: Insights Executivos
    print(f"\n🤖 AGENTE 3: Insights Agent")
    try:
        insights_agent = InsightsAgent(openai_key, "gpt-4o-mini")
        print(f"   Agente inicializado: {insights_agent.name} v{insights_agent.version}")
        
        # Preparar dados para insights
        document_data = [{
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "patterns": categorization_result.get("patterns", {})
        }]
        
        executive_insights = insights_agent.generate_executive_insights(document_data)
        
        print(f"   ✅ Insights gerados")
        print(f"   💡 Alertas: {len(executive_insights.get('alertas', []))}")
        print(f"   🎯 Oportunidades: {len(executive_insights.get('oportunidades', []))}")
        
        # Mostrar alguns insights
        for alerta in executive_insights.get('alertas', [])[:2]:
            print(f"      ⚠️  {alerta}")
        
        for oportunidade in executive_insights.get('oportunidades', [])[:2]:
            print(f"      💰 {oportunidade}")
        
    except Exception as e:
        print(f"   ❌ Erro no Agente 3: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎉 Todos os 3 agentes funcionaram corretamente!")
    return True

if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    success = test_agents()
    
    if success:
        print(f"\n✅ VALIDAÇÃO COMPLETA: Os 3 agentes estão funcionando!")
        print(f"   🤖 Agente 1: Extração de dados XML ✅")
        print(f"   🤖 Agente 2: Categorização inteligente ✅") 
        print(f"   🤖 Agente 3: Insights executivos ✅")
        print(f"\n🚀 Sistema pronto para processamento completo!")
    else:
        print(f"\n❌ FALHA NA VALIDAÇÃO: Verifique os erros acima")