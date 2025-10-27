#!/usr/bin/env python3
"""
Teste básico do MVP Sistema Simplificado de Análise Fiscal
"""

import requests
import json
import time
import os

API_BASE = "http://localhost:8000"

def test_health():
    """Testa se a API está funcionando"""
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ API está funcionando")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com API: {e}")
        return False

def test_upload():
    """Testa upload de documento XML"""
    try:
        # XML de teste simples
        test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe35200714200166000187550010000000046550000000">
            <ide>
                <cUF>35</cUF>
                <natOp>Venda de Mercadoria</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>46</nNF>
                <dhEmi>2020-07-01T10:00:00-03:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>14200166000187</CNPJ>
                <xNome>Empresa Teste LTDA</xNome>
                <xFant>Teste</xFant>
            </emit>
            <dest>
                <CNPJ>11222333000181</CNPJ>
                <xNome>Cliente Teste</xNome>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>001</cProd>
                    <xProd>Produto de Teste</xProd>
                    <NCM>12345678</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>1.0000</qCom>
                    <vUnCom>100.00</vUnCom>
                    <vProd>100.00</vProd>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vProd>100.00</vProd>
                    <vNF>100.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>"""
        
        # Criar arquivo temporário
        with open("test_nfe.xml", "w", encoding="utf-8") as f:
            f.write(test_xml)
        
        # Upload
        with open("test_nfe.xml", "rb") as f:
            files = {"files": ("test_nfe.xml", f, "application/xml")}
            response = requests.post(f"{API_BASE}/api/v1/documents/upload", files=files)
        
        # Limpar arquivo temporário
        os.remove("test_nfe.xml")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload realizado com sucesso")
            print(f"   Document IDs: {result.get('document_ids')}")
            return result.get('document_ids', [])
        else:
            print(f"❌ Upload falhou: {response.status_code}")
            print(f"   Erro: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        return []

def test_document_status(doc_id):
    """Testa status do documento"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/documents/{doc_id}")
        if response.status_code == 200:
            doc = response.json()
            print(f"✅ Documento {doc_id[:8]}...")
            print(f"   Status: {doc.get('status')}")
            print(f"   Progresso: {doc.get('progress')}%")
            if doc.get('extracted_data'):
                print(f"   Dados extraídos: ✅")
            return doc
        else:
            print(f"❌ Erro ao obter documento: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

def test_dashboard():
    """Testa dashboard executivo"""
    try:
        response = requests.get(f"{API_BASE}/api/v1/dashboard/summary")
        if response.status_code == 200:
            summary = response.json()
            print("✅ Dashboard funcionando")
            print(f"   Total documentos: {summary.get('total_documentos')}")
            print(f"   Processados: {summary.get('documentos_processados')}")
            print(f"   Valor total: R$ {summary.get('valor_total', 0):.2f}")
            return True
        else:
            print(f"❌ Dashboard falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        return False

def test_natural_query():
    """Testa consulta em linguagem natural"""
    try:
        query = {"query": "Qual o valor total dos documentos?"}
        response = requests.post(f"{API_BASE}/api/v1/query/natural", json=query)
        if response.status_code == 200:
            result = response.json()
            print("✅ Consulta natural funcionando")
            print(f"   Resposta: {result.get('response')}")
            return True
        else:
            print(f"❌ Consulta natural falhou: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro na consulta: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 Testando MVP Sistema Simplificado de Análise Fiscal")
    print("=" * 60)
    
    # Teste 1: Health check
    if not test_health():
        print("\n❌ API não está funcionando. Inicie com: python main.py")
        return
    
    print()
    
    # Teste 2: Upload
    doc_ids = test_upload()
    if not doc_ids:
        print("\n❌ Upload falhou")
        return
    
    print()
    
    # Aguardar processamento completo
    print("⏳ Aguardando processamento...")
    doc_id = doc_ids[0]
    
    # Aguardar até completar (máximo 30 segundos)
    for i in range(30):
        time.sleep(1)
        doc = test_document_status(doc_id)
        if doc and doc.get('status') == 'completed':
            print(f"✅ Processamento concluído em {i+1} segundos")
            break
        elif doc and doc.get('status') == 'error':
            print(f"❌ Erro no processamento: {doc.get('error')}")
            break
        elif i % 5 == 0:  # Log a cada 5 segundos
            progress = doc.get('progress', 0) if doc else 0
            print(f"   Progresso: {progress}%")
    else:
        print("⚠️  Timeout - processamento não completou em 30s")
    
    print()
    
    # Teste 4: Dashboard
    test_dashboard()
    
    print()
    
    # Teste 5: Consulta natural
    test_natural_query()
    
    print()
    print("🎉 Testes concluídos!")
    
    # Verificar se OpenAI está configurada
    from dotenv import load_dotenv
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "your-openai-api-key-here":
        print("\n⚠️  DICA: Configure OPENAI_API_KEY no .env para usar IA completa")
    else:
        print("\n✅ OpenAI configurada - IA completa disponível")

if __name__ == "__main__":
    main()