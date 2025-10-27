#!/usr/bin/env python3
"""
Teste de processamento completo com novo schema
Utiliza arquivo já existente no bucket do Supabase
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    create_document_record,
    process_document_with_agents_sync,
    get_document,
    get_dashboard_metrics,
    get_top_suppliers,
    get_product_categories,
    STORAGE_BUCKET
)

async def list_bucket_files():
    """Lista arquivos disponíveis no bucket"""
    if not supabase:
        print("❌ Supabase não configurado")
        return []
    
    try:
        result = supabase.storage.from_(STORAGE_BUCKET).list()
        print(f"📁 Arquivos encontrados no bucket '{STORAGE_BUCKET}':")
        
        files = []
        for item in result:
            if isinstance(item, dict):
                name = item.get('name', 'unknown')
                size = item.get('metadata', {}).get('size', 0)
                print(f"   - {name} ({size} bytes)")
                files.append(name)
        
        return files
    except Exception as e:
        print(f"❌ Erro ao listar arquivos do bucket: {e}")
        return []

async def test_existing_file_processing():
    """Testa processamento usando arquivo existente no bucket"""
    
    print("🧪 Testando processamento completo com novo schema\n")
    
    # Verificar conexão com Supabase
    if not supabase:
        print("❌ Supabase não configurado. Verifique as variáveis de ambiente.")
        return False
    
    print("✅ Supabase conectado")
    
    # Listar arquivos disponíveis
    print("\n1. Verificando arquivos no bucket...")
    files = await list_bucket_files()
    
    if not files:
        print("❌ Nenhum arquivo encontrado no bucket")
        return False
    
    # Selecionar primeiro arquivo XML ou qualquer arquivo disponível
    selected_file = None
    for file in files:
        if file.lower().endswith('.xml'):
            selected_file = file
            break
    
    if not selected_file and files:
        selected_file = files[0]  # Usar primeiro arquivo disponível
    
    if not selected_file:
        print("❌ Nenhum arquivo adequado encontrado")
        return False
    
    print(f"📄 Arquivo selecionado: {selected_file}")
    
    # Criar ID único para o teste
    test_doc_id = f"test_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 2. Criar registro do documento
        print(f"\n2. Criando registro do documento...")
        file_path = selected_file  # Caminho no bucket
        
        doc_created = await create_document_record(test_doc_id, selected_file, file_path)
        if not doc_created:
            print("❌ Falha ao criar registro do documento")
            return False
        
        print("✅ Documento registrado com sucesso")
        
        # 3. Baixar arquivo do bucket
        print(f"\n3. Baixando arquivo do bucket...")
        try:
            file_content = supabase.storage.from_(STORAGE_BUCKET).download(file_path)
            print(f"✅ Arquivo baixado: {len(file_content)} bytes")
        except Exception as e:
            print(f"❌ Erro ao baixar arquivo: {e}")
            return False
        
        # 4. Processar documento com os 3 agentes
        print(f"\n4. Processando documento com os 3 agentes IA...")
        
        processing_result = process_document_with_agents_sync(test_doc_id, file_content, selected_file)
        
        if processing_result.get('success'):
            print("✅ Processamento concluído com sucesso!")
            
            # Mostrar resultados
            print(f"\n📊 Resultados do processamento:")
            print(f"   - Tempo de processamento: {processing_result.get('processing_time', 0):.2f}s")
            
            extracted_data = processing_result.get('extracted_data', {})
            if extracted_data:
                print(f"   - Valor total: R$ {extracted_data.get('valor_total', 0):,.2f}")
                print(f"   - Emitente: {extracted_data.get('emitente', {}).get('razao_social', 'N/A')}")
                print(f"   - Número da nota: {extracted_data.get('numero_nota', 'N/A')}")
            
            categorized_items = processing_result.get('categorized_items', [])
            print(f"   - Itens categorizados: {len(categorized_items)}")
            
            supplier_category = processing_result.get('supplier_category', {})
            if supplier_category:
                print(f"   - Tipo de fornecedor: {supplier_category.get('type', 'N/A')}")
                print(f"   - Categoria de negócio: {supplier_category.get('business_category', 'N/A')}")
            
            executive_insights = processing_result.get('executive_insights', {})
            alertas = executive_insights.get('alertas', [])
            oportunidades = executive_insights.get('oportunidades', [])
            print(f"   - Alertas gerados: {len(alertas)}")
            print(f"   - Oportunidades identificadas: {len(oportunidades)}")
            
        else:
            print(f"❌ Falha no processamento: {processing_result.get('error', 'Erro desconhecido')}")
            return False
        
        # 5. Verificar dados salvos no banco
        print(f"\n5. Verificando dados salvos no banco...")
        
        try:
            document_details = await get_document(test_doc_id)
            print("✅ Documento recuperado do banco:")
            print(f"   - Status: {document_details.get('status')}")
            print(f"   - Progresso: {document_details.get('progress')}%")
            print(f"   - Número da nota: {document_details.get('numero_nota')}")
            print(f"   - Valor total: R$ {document_details.get('valor_total', 0):,.2f}")
            
            # Verificar dados extraídos detalhados
            extracted_data_db = document_details.get('extracted_data', {})
            if extracted_data_db:
                print(f"   - Emitente (DB): {extracted_data_db.get('emitente_razao_social')}")
                print(f"   - CNPJ Emitente: {extracted_data_db.get('emitente_cnpj')}")
                print(f"   - UF Origem: {extracted_data_db.get('emitente_uf')}")
            
            # Verificar itens
            items = document_details.get('items', [])
            print(f"   - Itens salvos: {len(items)}")
            for i, item in enumerate(items[:3]):  # Mostrar apenas os 3 primeiros
                print(f"     {i+1}. {item.get('descricao', 'N/A')} - Categoria: {item.get('categoria', 'N/A')}")
            
            # Verificar análise de fornecedor
            supplier_analysis = document_details.get('supplier_analysis', {})
            if supplier_analysis:
                print(f"   - Análise de fornecedor salva:")
                print(f"     - Tipo: {supplier_analysis.get('tipo_fornecedor')}")
                print(f"     - Score de risco: {supplier_analysis.get('score_risco')}")
            
            # Verificar insights de IA
            ai_insights = document_details.get('ai_insights', [])
            print(f"   - Insights de IA salvos: {len(ai_insights)}")
            for insight in ai_insights[:3]:  # Mostrar apenas os 3 primeiros
                print(f"     - {insight.get('tipo_insight')}: {insight.get('titulo')}")
            
        except Exception as e:
            print(f"❌ Erro ao verificar dados salvos: {e}")
            return False
        
        # 6. Testar endpoints do dashboard
        print(f"\n6. Testando endpoints do dashboard...")
        
        try:
            # Métricas do dashboard
            metrics = await get_dashboard_metrics()
            print(f"✅ Métricas do dashboard:")
            print(f"   - Total de documentos: {metrics.get('total_documentos', 0)}")
            print(f"   - Documentos processados: {metrics.get('documentos_processados', 0)}")
            print(f"   - Valor total geral: R$ {metrics.get('valor_total', 0):,.2f}")
            
            # Top fornecedores
            suppliers = await get_top_suppliers()
            suppliers_list = suppliers.get('suppliers', [])
            print(f"✅ Top fornecedores ({len(suppliers_list)} encontrados):")
            for supplier in suppliers_list[:3]:
                print(f"   - {supplier.get('name', 'N/A')}: R$ {supplier.get('total_value', 0):,.2f}")
            
            # Categorias de produtos
            categories = await get_product_categories()
            categories_list = categories.get('categories', [])
            print(f"✅ Categorias de produtos ({len(categories_list)} encontradas):")
            for category in categories_list[:3]:
                print(f"   - {category.get('category', 'N/A')}: R$ {category.get('total_value', 0):,.2f}")
            
        except Exception as e:
            print(f"⚠️  Aviso: Erro ao testar dashboard: {e}")
        
        print(f"\n🎉 Teste completo realizado com sucesso!")
        print(f"📋 Resumo:")
        print(f"   - Arquivo processado: {selected_file}")
        print(f"   - Documento ID: {test_doc_id}")
        print(f"   - Status: Processamento completo")
        print(f"   - Novo schema: ✅ Funcionando")
        
        # Limpeza opcional
        print(f"\n🧹 Limpando dados de teste...")
        try:
            supabase.table('fiscal_documents').delete().eq('id', test_doc_id).execute()
            print("✅ Dados de teste removidos")
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível remover dados de teste: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando teste de processamento com novo schema\n")
    
    success = asyncio.run(test_existing_file_processing())
    
    if success:
        print("\n✅ Teste de processamento concluído com sucesso!")
        print("🎯 O novo schema está funcionando perfeitamente!")
        return True
    else:
        print("\n❌ Falha no teste de processamento")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)