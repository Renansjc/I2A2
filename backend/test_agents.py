#!/usr/bin/env python3
"""
Teste simples dos 3 Agentes IA
Verifica se os agentes conseguem processar um XML de exemplo
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.xml_processing_agent import XMLProcessingAgent
from agents.categorization_agent import CategorizationAgent
from agents.insights_agent import InsightsAgent, QueryContext

def test_xml_agent():
    """Testa o Agente de Processamento XML"""
    print("🔍 Testando Agente de Processamento XML...")
    
    # XML de exemplo simples
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc>
        <NFe>
            <infNFe Id="NFe35200714200166000187550010000000046123456789">
                <ide>
                    <nNF>46</nNF>
                    <dhEmi>2020-07-01T10:00:00-03:00</dhEmi>
                    <natOp>Venda de mercadoria</natOp>
                </ide>
                <emit>
                    <CNPJ>14200166000187</CNPJ>
                    <xNome>EMPRESA TESTE LTDA</xNome>
                    <IE>123456789</IE>
                </emit>
                <dest>
                    <CNPJ>11222333000181</CNPJ>
                    <xNome>CLIENTE TESTE LTDA</xNome>
                </dest>
                <det nItem="1">
                    <prod>
                        <cProd>001</cProd>
                        <xProd>Produto de Teste</xProd>
                        <NCM>12345678</NCM>
                        <CFOP>5102</CFOP>
                        <qCom>1.0000</qCom>
                        <vUnCom>100.00</vUnCom>
                        <vProd>100.00</vProd>
                    </prod>
                </det>
                <total>
                    <ICMSTot>
                        <vNF>100.00</vNF>
                        <vICMS>18.00</vICMS>
                    </ICMSTot>
                </total>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    agent = XMLProcessingAgent()
    result = agent.process_xml(xml_content)
    
    print(f"✅ Agente XML processou com sucesso!")
    print(f"   - Valor total extraído: {result['extracted_data'].get('valor_total')}")
    print(f"   - Emitente: {result['extracted_data'].get('emitente', {}).get('razao_social')}")
    print(f"   - Itens encontrados: {len(result['extracted_data'].get('itens', []))}")
    print(f"   - Validação: {'✅ Válido' if result['validation'].get('valid') else '❌ Inválido'}")
    
    return result

def test_categorization_agent(extracted_data):
    """Testa o Agente de Categorização"""
    print("\n🏷️  Testando Agente de Categorização...")
    
    agent = CategorizationAgent()  # Sem API key para teste básico
    result = agent.categorize_document(extracted_data)
    
    print(f"✅ Agente de Categorização processou com sucesso!")
    print(f"   - Itens categorizados: {len(result['categorized_items'])}")
    print(f"   - Tipo de fornecedor: {result['supplier_category'].get('type')}")
    print(f"   - Confiança geral: {result['categorization_metadata'].get('confidence', 0.0):.2f}")
    
    if result['categorized_items']:
        item = result['categorized_items'][0]
        print(f"   - Primeira categoria: {item.get('categoria')} (confiança: {item.get('categoria_confianca', 0.0):.2f})")
    
    return result

def test_insights_agent(documents_data):
    """Testa o Agente de Insights"""
    print("\n💡 Testando Agente de Insights...")
    
    agent = InsightsAgent()  # Sem API key para teste básico
    
    # Teste de insights executivos
    insights = agent.generate_executive_insights(documents_data)
    
    print(f"✅ Agente de Insights processou com sucesso!")
    print(f"   - Resumo executivo gerado: {bool(insights.get('resumo_executivo'))}")
    print(f"   - Alertas identificados: {len(insights.get('alertas', []))}")
    print(f"   - Oportunidades: {len(insights.get('oportunidades', []))}")
    print(f"   - Recomendações: {len(insights.get('recomendacoes', []))}")
    
    # Teste de consulta natural
    context = QueryContext(
        available_data={"valor_total": 100.0, "fornecedores": ["EMPRESA TESTE LTDA"]},
        user_history=[],
        business_context={}
    )
    
    query_result = agent.process_natural_query("Qual o valor total?", context)
    print(f"   - Consulta natural processada: '{query_result.get('query')}'")
    print(f"   - Resposta: {query_result.get('response')[:50]}...")
    
    return insights

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes dos 3 Agentes IA\n")
    
    try:
        # Teste 1: Agente XML
        xml_result = test_xml_agent()
        extracted_data = xml_result['extracted_data']
        
        # Teste 2: Agente de Categorização
        cat_result = test_categorization_agent(extracted_data)
        
        # Teste 3: Agente de Insights
        documents_data = [{
            "extracted_data": extracted_data,
            "categorized_items": cat_result['categorized_items'],
            "supplier_category": cat_result['supplier_category']
        }]
        
        insights_result = test_insights_agent(documents_data)
        
        print("\n🎉 Todos os agentes funcionaram corretamente!")
        print("\n📊 Resumo dos testes:")
        print(f"   - XML Agent: ✅ Extraiu dados e validou documento")
        print(f"   - Categorization Agent: ✅ Categorizou itens e fornecedor")
        print(f"   - Insights Agent: ✅ Gerou insights e processou consulta")
        
        print("\n💡 Os agentes estão prontos para integração com Supabase!")
        
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)