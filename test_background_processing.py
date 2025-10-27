#!/usr/bin/env python3
"""
Teste do processamento em background para debug
"""

import sys
import os
sys.path.append('backend')

import asyncio
from datetime import datetime
from agents.xml_processing_agent import XMLProcessingAgent
from agents.categorization_agent import CategorizationAgent
from agents.insights_agent import InsightsAgent, QueryContext

# Simular a função process_document_with_agents
def test_background_processing():
    """Simula exatamente o que acontece no processamento em background"""
    
    print("🧪 Testando processamento em background...\n")
    
    # Simular dados
    doc_id = "test-doc-123"
    
    # Ler arquivo XML
    xml_file_path = "xml_nf/exemplo.xml"
    
    try:
        with open(xml_file_path, 'rb') as f:
            file_content = f.read()
        print(f"✅ Arquivo carregado: {len(file_content)} bytes")
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return False
    
    # Simular documents_db
    documents_db = {}
    documents_db[doc_id] = {
        "id": doc_id,
        "filename": "exemplo.xml",
        "uploaded_at": datetime.now().isoformat(),
        "status": "ingestao",
        "progress": 5,
        "file_path": None,
        "extracted_data": None,
        "insights": None,
        "current_step": "ingestao"
    }
    
    # Inicializar agentes
    openai_key = os.getenv("OPENAI_API_KEY")
    xml_agent = XMLProcessingAgent()
    categorization_agent = CategorizationAgent(openai_key, "gpt-4o-mini")
    insights_agent = InsightsAgent(openai_key, "gpt-4o-mini")
    
    start_time = datetime.now()
    
    try:
        # ETAPA 1: Ingestão → Preprocessamento
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando preprocessamento")
        documents_db[doc_id]["status"] = "preprocessamento"
        documents_db[doc_id]["progress"] = 15
        
        # ETAPA 2: Preprocessamento → OCR/Extração
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando extração de dados")
        documents_db[doc_id]["status"] = "ocr"
        documents_db[doc_id]["progress"] = 25
        
        # AGENTE 1: Processamento XML
        print(f"[AGENTE 1] {doc_id} - Processamento XML iniciado")
        xml_content = file_content.decode('utf-8', errors='ignore')
        xml_result = xml_agent.process_xml(xml_content)
        
        extracted_data = xml_result.get("extracted_data", {})
        validation_result = xml_result.get("validation", {})
        
        # Armazenar resultados localmente
        documents_db[doc_id]["extracted_data"] = extracted_data
        documents_db[doc_id]["xml_validation"] = validation_result
        documents_db[doc_id]["xml_metadata"] = xml_result.get("processing_metadata", {})
        
        print(f"   ✅ Agente 1 concluído - Valor: {extracted_data.get('valor_total')}")
        
        # ETAPA 3: OCR → NLP
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando NLP")
        documents_db[doc_id]["status"] = "nlp"
        documents_db[doc_id]["progress"] = 40
        
        # AGENTE 2: Categorização
        print(f"[AGENTE 2] {doc_id} - Categorização IA iniciada")
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        patterns = categorization_result.get("patterns", {})
        ai_insights = categorization_result.get("ai_insights", {})
        
        documents_db[doc_id]["categorized_items"] = categorized_items
        documents_db[doc_id]["supplier_category"] = supplier_category
        documents_db[doc_id]["categorization_patterns"] = patterns
        documents_db[doc_id]["categorization_ai_insights"] = ai_insights
        documents_db[doc_id]["categorization_metadata"] = categorization_result.get("categorization_metadata", {})
        
        print(f"   ✅ Agente 2 concluído - Itens categorizados: {len(categorized_items)}")
        
        # ETAPA 4: NLP → Validação
        print(f"[PROCESSAMENTO] {doc_id} - Iniciando validação")
        documents_db[doc_id]["status"] = "validacao"
        documents_db[doc_id]["progress"] = 70
        
        # AGENTE 3: Insights Executivos
        print(f"[AGENTE 3] {doc_id} - Geração de insights executivos")
        document_data = [{
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "patterns": patterns
        }]
        
        executive_insights = insights_agent.generate_executive_insights(document_data)
        
        documents_db[doc_id]["executive_insights"] = executive_insights
        documents_db[doc_id]["insights_metadata"] = executive_insights.get("metadata", {})
        
        print(f"   ✅ Agente 3 concluído - Alertas: {len(executive_insights.get('alertas', []))}")
        
        # ETAPA 5: Validação → Finalizado
        print(f"[SUCESSO] {doc_id} - Processamento concluído com 3 agentes")
        documents_db[doc_id]["status"] = "finalizado"
        documents_db[doc_id]["progress"] = 100
        documents_db[doc_id]["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # Resumo final
        documents_db[doc_id]["insights"] = {
            "resumo_financeiro": {
                "valor_total": extracted_data.get('valor_total'),
                "quantidade_itens": len(categorized_items),
                "fornecedor": extracted_data.get('emitente', {}).get('razao_social'),
                "categoria_fornecedor": supplier_category.get('type'),
                "confianca_geral": categorization_result.get("categorization_metadata", {}).get("confidence", 0.0)
            },
            "categorias_principais": [item.get('categoria') for item in categorized_items[:3]],
            "alertas": executive_insights.get("alertas", []),
            "oportunidades": executive_insights.get("oportunidades", []),
            "status_processamento": "completo_3_agentes"
        }
        
        print(f"\n🎉 PROCESSAMENTO COMPLETO!")
        print(f"   ⏱️  Tempo total: {documents_db[doc_id]['processing_time']:.2f}s")
        print(f"   📊 Status final: {documents_db[doc_id]['status']}")
        print(f"   📈 Progresso: {documents_db[doc_id]['progress']}%")
        
        # Mostrar resumo dos resultados
        insights = documents_db[doc_id]["insights"]
        print(f"\n📋 RESUMO DOS RESULTADOS:")
        print(f"   💰 Valor total: R$ {insights['resumo_financeiro']['valor_total']}")
        print(f"   📦 Itens: {insights['resumo_financeiro']['quantidade_itens']}")
        print(f"   🏢 Fornecedor: {insights['resumo_financeiro']['fornecedor']}")
        print(f"   🏷️  Categorias: {', '.join(insights['categorias_principais'])}")
        print(f"   ⚠️  Alertas: {len(insights['alertas'])}")
        print(f"   💡 Oportunidades: {len(insights['oportunidades'])}")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] {doc_id} - {str(e)}")
        import traceback
        traceback.print_exc()
        
        documents_db[doc_id]["status"] = "erro"
        documents_db[doc_id]["error"] = str(e)
        documents_db[doc_id]["progress"] = 100
        
        return False

if __name__ == "__main__":
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    success = test_background_processing()
    
    if success:
        print(f"\n✅ TESTE DE PROCESSAMENTO EM BACKGROUND: SUCESSO!")
        print(f"   🔧 O problema não está nos agentes")
        print(f"   🔧 O problema pode estar na execução assíncrona do FastAPI")
    else:
        print(f"\n❌ TESTE FALHOU: Verifique os erros acima")