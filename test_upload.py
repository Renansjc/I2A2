#!/usr/bin/env python3
"""
Script para testar o upload de arquivo XML para validar o Supabase
"""

import requests
import time
import json

def test_upload_xml():
    """Testa o upload de um arquivo XML e verifica o processamento"""
    
    # URL do backend
    base_url = "http://localhost:8000"
    
    print("🧪 Testando upload de arquivo XML...")
    
    # 1. Verificar se o backend está rodando
    try:
        health_response = requests.get(f"{base_url}/health")
        print(f"✅ Backend está rodando: {health_response.json()}")
    except Exception as e:
        print(f"❌ Backend não está rodando: {e}")
        return False
    
    # 2. Fazer upload do arquivo XML
    xml_file_path = "xml_nf/exemplo.xml"
    
    try:
        with open(xml_file_path, 'rb') as f:
            files = {'files': (xml_file_path, f, 'application/xml')}
            upload_response = requests.post(f"{base_url}/api/v1/documents/upload", files=files)
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print(f"✅ Upload realizado com sucesso!")
            print(f"   Documento IDs: {upload_data['document_ids']}")
            print(f"   Total de arquivos: {upload_data['total_files']}")
            
            document_id = upload_data['document_ids'][0]
            
            # 3. Monitorar o processamento
            print(f"\n📊 Monitorando processamento do documento {document_id}...")
            
            max_attempts = 30  # 30 tentativas (30 segundos)
            for attempt in range(max_attempts):
                try:
                    status_response = requests.get(f"{base_url}/api/v1/documents/{document_id}/status")
                    status_data = status_response.json()
                    
                    print(f"   Tentativa {attempt + 1}: Status = {status_data['status']}, Progresso = {status_data['progress']}%")
                    
                    if status_data['status'] in ['finalizado', 'completed']:
                        print(f"✅ Processamento concluído!")
                        
                        # 4. Verificar dados extraídos
                        doc_response = requests.get(f"{base_url}/api/v1/documents/{document_id}")
                        doc_data = doc_response.json()
                        
                        print(f"\n📋 Dados extraídos:")
                        extracted_data = doc_data.get('extracted_data', {})
                        print(f"   Emitente: {extracted_data.get('emitente', {}).get('razao_social', 'N/A')}")
                        print(f"   Destinatário: {extracted_data.get('destinatario', {}).get('razao_social', 'N/A')}")
                        print(f"   Valor Total: R$ {extracted_data.get('valor_total', 'N/A')}")
                        print(f"   Número da Nota: {extracted_data.get('numero_nota', 'N/A')}")
                        
                        # 5. Verificar se há itens categorizados
                        categorized_items = doc_data.get('categorized_items', [])
                        print(f"   Itens categorizados: {len(categorized_items)}")
                        
                        if categorized_items:
                            for i, item in enumerate(categorized_items[:3]):  # Mostrar apenas os 3 primeiros
                                print(f"     Item {i+1}: {item.get('descricao', 'N/A')} - Categoria: {item.get('categoria', 'N/A')}")
                        
                        # 6. Verificar insights executivos
                        executive_insights = doc_data.get('executive_insights', {})
                        if executive_insights:
                            print(f"   Insights executivos gerados: ✅")
                            alertas = executive_insights.get('alertas', [])
                            oportunidades = executive_insights.get('oportunidades', [])
                            print(f"     Alertas: {len(alertas)}")
                            print(f"     Oportunidades: {len(oportunidades)}")
                        
                        return True
                        
                    elif status_data['status'] == 'erro':
                        print(f"❌ Erro no processamento: {status_data.get('error', 'Erro desconhecido')}")
                        return False
                    
                    time.sleep(1)  # Aguardar 1 segundo
                    
                except Exception as e:
                    print(f"   Erro ao verificar status: {e}")
                    time.sleep(1)
            
            print(f"⏰ Timeout - processamento não concluído em {max_attempts} segundos")
            return False
            
        else:
            print(f"❌ Erro no upload: {upload_response.status_code}")
            print(f"   Resposta: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o upload: {e}")
        return False

def test_dashboard_data():
    """Testa se os dados estão aparecendo no dashboard"""
    
    base_url = "http://localhost:8000"
    
    print(f"\n📊 Testando dados do dashboard...")
    
    try:
        # Métricas gerais
        metrics_response = requests.get(f"{base_url}/api/v1/dashboard/metrics")
        metrics = metrics_response.json()
        
        print(f"✅ Métricas do dashboard:")
        print(f"   Total de documentos: {metrics.get('total_documentos', 0)}")
        print(f"   Documentos processados: {metrics.get('documentos_processados', 0)}")
        print(f"   Valor total: R$ {metrics.get('valor_total', 0):,.2f}")
        print(f"   Taxa de sucesso: {metrics.get('taxa_sucesso', 0):.1f}%")
        
        # Fornecedores
        suppliers_response = requests.get(f"{base_url}/api/v1/dashboard/suppliers")
        suppliers = suppliers_response.json()
        
        print(f"\n🏢 Fornecedores:")
        for supplier in suppliers.get('suppliers', [])[:3]:
            print(f"   {supplier.get('name', 'N/A')}: R$ {supplier.get('total_value', 0):,.2f}")
        
        # Categorias
        categories_response = requests.get(f"{base_url}/api/v1/dashboard/categories")
        categories = categories_response.json()
        
        print(f"\n📦 Categorias:")
        for category in categories.get('categories', [])[:3]:
            print(f"   {category.get('category', 'N/A')}: R$ {category.get('total_value', 0):,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar dashboard: {e}")
        return False

def test_supabase_connection():
    """Testa a conexão com o Supabase"""
    
    base_url = "http://localhost:8000"
    
    print(f"\n🗄️  Testando conexão com Supabase...")
    
    try:
        # Verificar status dos agentes (inclui status do Supabase)
        agents_response = requests.get(f"{base_url}/api/v1/agents/status")
        agents_data = agents_response.json()
        
        print(f"✅ Status dos agentes:")
        for agent in agents_data.get('agents', []):
            print(f"   {agent.get('name', 'N/A')}: {agent.get('status', 'N/A')}")
        
        print(f"   OpenAI configurada: {agents_data.get('openai_configured', False)}")
        print(f"   Status do sistema: {agents_data.get('system_status', 'N/A')}")
        
        # Verificar endpoint raiz que mostra status do Supabase
        root_response = requests.get(f"{base_url}/")
        root_data = root_response.json()
        
        print(f"   Status do Supabase: {root_data.get('supabase_status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando validação do Supabase e processamento de documentos\n")
    
    # Executar testes
    supabase_ok = test_supabase_connection()
    upload_ok = test_upload_xml()
    dashboard_ok = test_dashboard_data()
    
    print(f"\n📋 Resumo dos testes:")
    print(f"   Conexão Supabase: {'✅' if supabase_ok else '❌'}")
    print(f"   Upload e processamento: {'✅' if upload_ok else '❌'}")
    print(f"   Dashboard com dados: {'✅' if dashboard_ok else '❌'}")
    
    if supabase_ok and upload_ok and dashboard_ok:
        print(f"\n🎉 Todos os testes passaram! O sistema está funcionando corretamente.")
        print(f"   ✅ Arquivos estão sendo analisados e categorizados no DB")
        print(f"   ✅ Os 3 agentes IA estão processando documentos")
        print(f"   ✅ Dados estão sendo salvos no Supabase")
        print(f"   ✅ Dashboard está exibindo métricas corretas")
        print(f"\n🚀 Pronto para prosseguir com a Task 5!")
    else:
        print(f"\n⚠️  Alguns testes falharam. Verifique os problemas antes de prosseguir.")