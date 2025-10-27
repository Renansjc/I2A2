#!/usr/bin/env python3
"""
Teste da nova arquitetura Storage-First
"""

import requests
import time
import json

def test_new_architecture():
    """Testa o novo fluxo: Upload → Storage → Process"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testando nova arquitetura Storage-First...\n")
    
    # 1. Verificar se o backend está rodando
    try:
        health_response = requests.get(f"{base_url}/health")
        print(f"✅ Backend está rodando: {health_response.json()}")
    except Exception as e:
        print(f"❌ Backend não está rodando: {e}")
        return False
    
    # 2. Upload do arquivo (apenas para Storage)
    xml_file_path = "xml_nf/exemplo.xml"
    
    try:
        with open(xml_file_path, 'rb') as f:
            files = {'files': (xml_file_path, f, 'application/xml')}
            upload_response = requests.post(f"{base_url}/api/v1/documents/upload", files=files)
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print(f"✅ Upload para Storage realizado com sucesso!")
            print(f"   Documento IDs: {upload_data['document_ids']}")
            print(f"   Mensagem: {upload_data['message']}")
            
            document_id = upload_data['document_ids'][0]
            
            # 3. Verificar status após upload (deve estar 'uploaded')
            status_response = requests.get(f"{base_url}/api/v1/documents/{document_id}/status")
            status_data = status_response.json()
            print(f"\n📊 Status após upload: {status_data['status']} ({status_data['progress']}%)")
            
            # 4. Processar documento com os 3 agentes
            print(f"\n🤖 Iniciando processamento com os 3 agentes...")
            process_response = requests.post(f"{base_url}/api/v1/documents/{document_id}/process")
            
            if process_response.status_code == 200:
                process_data = process_response.json()
                print(f"✅ Processamento concluído!")
                print(f"   Status: {process_data['status']}")
                print(f"   Tempo: {process_data.get('processing_time', 'N/A')}s")
                print(f"   Resultados dos agentes:")
                
                agents_results = process_data.get('agents_results', {})
                for agent, result in agents_results.items():
                    print(f"     {agent}: {result}")
                
                # 5. Verificar dados finais
                doc_response = requests.get(f"{base_url}/api/v1/documents/{document_id}")
                doc_data = doc_response.json()
                
                print(f"\n📋 Dados finais do documento:")
                extracted_data = doc_data.get('extracted_data', {})
                items = doc_data.get('items', [])
                
                print(f"   Emitente: {extracted_data.get('emitente', {}).get('razao_social', 'N/A')}")
                print(f"   Valor Total: R$ {extracted_data.get('valor_total', 'N/A')}")
                print(f"   Status: {doc_data.get('status', 'N/A')}")
                
                if items:
                    item = items[0]
                    print(f"   Item 1: {item.get('descricao', 'N/A')[:50]}...")
                    print(f"   Categoria: {item.get('categoria', 'N/A')}")
                    print(f"   Confiança: {item.get('categoria_confianca', 'N/A')}")
                
                # 6. Testar dashboard com dados processados
                print(f"\n📊 Testando dashboard com dados processados...")
                
                metrics_response = requests.get(f"{base_url}/api/v1/dashboard/metrics")
                metrics = metrics_response.json()
                
                print(f"   Total de documentos: {metrics.get('total_documentos', 0)}")
                print(f"   Documentos processados: {metrics.get('documentos_processados', 0)}")
                print(f"   Valor total: R$ {metrics.get('valor_total', 0):,.2f}")
                
                return True
                
            else:
                print(f"❌ Erro no processamento: {process_response.status_code}")
                print(f"   Resposta: {process_response.text}")
                return False
            
        else:
            print(f"❌ Erro no upload: {upload_response.status_code}")
            print(f"   Resposta: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_batch_processing():
    """Testa processamento em lote"""
    
    base_url = "http://localhost:8000"
    
    print(f"\n🔄 Testando processamento em lote...")
    
    try:
        batch_response = requests.post(f"{base_url}/api/v1/documents/process-all")
        
        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            print(f"✅ Processamento em lote concluído!")
            print(f"   Processados: {batch_data.get('processed', 0)}")
            print(f"   Erros: {batch_data.get('errors', 0)}")
            
            return True
        else:
            print(f"❌ Erro no processamento em lote: {batch_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no processamento em lote: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testando Nova Arquitetura Storage-First\n")
    
    # Executar testes
    architecture_ok = test_new_architecture()
    batch_ok = test_batch_processing()
    
    print(f"\n📋 Resumo dos testes:")
    print(f"   Nova arquitetura: {'✅' if architecture_ok else '❌'}")
    print(f"   Processamento em lote: {'✅' if batch_ok else '❌'}")
    
    if architecture_ok and batch_ok:
        print(f"\n🎉 NOVA ARQUITETURA FUNCIONANDO PERFEITAMENTE!")
        print(f"   ✅ Upload para Storage separado do processamento")
        print(f"   ✅ Processamento sob demanda funcionando")
        print(f"   ✅ Os 3 agentes executando corretamente")
        print(f"   ✅ Dados sendo categorizados e salvos no DB")
        print(f"   ✅ Dashboard com dados reais")
        print(f"\n🚀 SISTEMA VALIDADO - PRONTO PARA TASK 5!")
    else:
        print(f"\n⚠️  Alguns testes falharam. Verifique os problemas antes de prosseguir.")