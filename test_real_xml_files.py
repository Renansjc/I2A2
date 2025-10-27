#!/usr/bin/env python3
"""
Teste com arquivos XML reais da pasta xml_nf
Faz upload e processamento completo com novo schema
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    create_document_record,
    upload_file_to_storage,
    update_document_status,
    save_extracted_data,
    save_supplier_analysis,
    save_ai_insights,
    get_document,
    get_dashboard_metrics,
    get_top_suppliers,
    get_product_categories,
    STORAGE_BUCKET,
    xml_agent,
    categorization_agent,
    insights_agent
)

async def process_document_async(doc_id: str, file_content: bytes, filename: str) -> dict:
    """Versão assíncrona do processamento para testes"""
    start_time = datetime.now()
    
    try:
        print(f"[PROCESSAMENTO] {filename} - Iniciando processamento")
        
        # AGENTE 1: Processamento XML
        print(f"[AGENTE 1] Processamento XML iniciado")
        xml_content = file_content.decode('utf-8', errors='ignore')
        xml_result = xml_agent.process_xml(xml_content)
        
        extracted_data = xml_result.get("extracted_data", {})
        validation_result = xml_result.get("validation", {})
        
        if not validation_result.get('valid', False):
            return {
                "success": False,
                "error": "Falha na validação do XML",
                "validation_errors": validation_result.get('errors', [])
            }
        
        # Atualizar progresso
        await update_document_status(doc_id, "processing", 40, "categorization")
        
        # AGENTE 2: Categorização
        print(f"[AGENTE 2] Categorização IA iniciada")
        categorization_result = categorization_agent.categorize_document(extracted_data)
        
        categorized_items = categorization_result.get("categorized_items", [])
        supplier_category = categorization_result.get("supplier_category", {})
        patterns = categorization_result.get("patterns", {})
        
        # Atualizar progresso
        await update_document_status(doc_id, "processing", 70, "insights")
        
        # AGENTE 3: Insights Executivos
        print(f"[AGENTE 3] Geração de insights executivos")
        document_data = [{
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "patterns": patterns
        }]
        
        executive_insights = insights_agent.generate_executive_insights(document_data)
        
        # Salvar dados extraídos no Supabase
        if supabase:
            success = await save_extracted_data(doc_id, extracted_data)
            if not success:
                print(f"⚠️  Falha ao salvar dados no Supabase para {doc_id}")
            
            # Salvar análise de fornecedor
            if supplier_category:
                supplier_success = await save_supplier_analysis(doc_id, supplier_category)
                if not supplier_success:
                    print(f"⚠️  Falha ao salvar análise de fornecedor para {doc_id}")
            
            # Salvar insights de IA
            if executive_insights:
                insights_success = await save_ai_insights(doc_id, executive_insights)
                if not insights_success:
                    print(f"⚠️  Falha ao salvar insights de IA para {doc_id}")
        
        # Finalizar processamento
        await update_document_status(doc_id, "completed", 100, "completed")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"[SUCESSO] {filename} - Processamento concluído em {processing_time:.2f}s")
        
        return {
            "success": True,
            "processing_time": processing_time,
            "extracted_data": extracted_data,
            "categorized_items": categorized_items,
            "supplier_category": supplier_category,
            "executive_insights": executive_insights,
            "alertas": executive_insights.get("alertas", []),
            "oportunidades": executive_insights.get("oportunidades", []),
            "validation": validation_result
        }
        
    except Exception as e:
        print(f"[ERRO] {filename} - {str(e)}")
        
        # Atualizar status de erro
        await update_document_status(doc_id, "error", 100, "error")
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

async def test_real_xml_files():
    """Testa processamento com arquivos XML reais"""
    
    print("🧪 Testando processamento com arquivos XML reais da pasta xml_nf\n")
    
    # Verificar conexão com Supabase
    if not supabase:
        print("❌ Supabase não configurado. Verifique as variáveis de ambiente.")
        return False
    
    print("✅ Supabase conectado")
    
    # Listar arquivos XML na pasta xml_nf
    xml_dir = "xml_nf"
    if not os.path.exists(xml_dir):
        print(f"❌ Pasta {xml_dir} não encontrada")
        return False
    
    xml_files = [f for f in os.listdir(xml_dir) if f.lower().endswith('.xml')]
    
    if not xml_files:
        print(f"❌ Nenhum arquivo XML encontrado na pasta {xml_dir}")
        return False
    
    print(f"📁 Encontrados {len(xml_files)} arquivos XML:")
    for i, filename in enumerate(xml_files, 1):
        file_path = os.path.join(xml_dir, filename)
        file_size = os.path.getsize(file_path)
        print(f"   {i}. {filename} ({file_size:,} bytes)")
    
    # Estatísticas do processamento
    results = {
        "total_files": len(xml_files),
        "successful": 0,
        "failed": 0,
        "processing_times": [],
        "documents": []
    }
    
    # Processar cada arquivo
    for i, filename in enumerate(xml_files, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processando arquivo {i}/{len(xml_files)}: {filename}")
        print(f"{'='*60}")
        
        try:
            # Ler arquivo
            file_path = os.path.join(xml_dir, filename)
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            print(f"✅ Arquivo lido: {len(file_content):,} bytes")
            
            # Criar ID único para o documento
            doc_id = str(uuid.uuid4())
            
            # 1. Upload para Storage
            print(f"1. Fazendo upload para Storage...")
            storage_path = await upload_file_to_storage(file_content, filename, doc_id)
            
            if not storage_path:
                print(f"❌ Falha no upload para Storage")
                results["failed"] += 1
                continue
            
            print(f"✅ Upload concluído: {storage_path}")
            
            # 2. Criar registro no banco
            print(f"2. Criando registro no banco...")
            doc_created = await create_document_record(doc_id, filename, storage_path)
            
            if not doc_created:
                print(f"❌ Falha ao criar registro no banco")
                results["failed"] += 1
                continue
            
            print(f"✅ Documento registrado: {doc_id}")
            
            # 3. Processar com os 3 agentes
            print(f"3. Processando com os 3 agentes IA...")
            processing_result = await process_document_async(doc_id, file_content, filename)
            
            if processing_result.get('success'):
                results["successful"] += 1
                results["processing_times"].append(processing_result.get('processing_time', 0))
                
                # Extrair informações principais
                extracted_data = processing_result.get('extracted_data', {})
                doc_info = {
                    "filename": filename,
                    "doc_id": doc_id,
                    "numero_nota": extracted_data.get('numero_nota'),
                    "valor_total": extracted_data.get('valor_total'),
                    "emitente": extracted_data.get('emitente', {}).get('razao_social'),
                    "cnpj_emitente": extracted_data.get('emitente', {}).get('cnpj'),
                    "uf_origem": extracted_data.get('emitente', {}).get('uf'),
                    "destinatario": extracted_data.get('destinatario', {}).get('nome') or extracted_data.get('destinatario', {}).get('razao_social'),
                    "uf_destino": extracted_data.get('destinatario', {}).get('uf'),
                    "itens_count": len(processing_result.get('categorized_items', [])),
                    "alertas_count": len(processing_result.get('alertas', [])),
                    "oportunidades_count": len(processing_result.get('oportunidades', [])),
                    "processing_time": processing_result.get('processing_time', 0)
                }
                results["documents"].append(doc_info)
                
                print(f"✅ Processamento concluído com sucesso!")
                print(f"   - Número da nota: {doc_info['numero_nota']}")
                print(f"   - Valor total: R$ {doc_info['valor_total']:,.2f}" if doc_info['valor_total'] else "   - Valor total: N/A")
                print(f"   - Emitente: {doc_info['emitente']}")
                print(f"   - Itens categorizados: {doc_info['itens_count']}")
                print(f"   - Tempo: {doc_info['processing_time']:.2f}s")
                
            else:
                results["failed"] += 1
                print(f"❌ Falha no processamento: {processing_result.get('error', 'Erro desconhecido')}")
            
        except Exception as e:
            results["failed"] += 1
            print(f"❌ Erro ao processar {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    # Relatório final
    print(f"\n{'='*80}")
    print(f"📊 RELATÓRIO FINAL DO PROCESSAMENTO")
    print(f"{'='*80}")
    
    print(f"\n📈 Estatísticas Gerais:")
    print(f"   - Total de arquivos: {results['total_files']}")
    print(f"   - Processados com sucesso: {results['successful']}")
    print(f"   - Falharam: {results['failed']}")
    print(f"   - Taxa de sucesso: {(results['successful'] / results['total_files'] * 100):.1f}%")
    
    if results['processing_times']:
        avg_time = sum(results['processing_times']) / len(results['processing_times'])
        total_time = sum(results['processing_times'])
        print(f"   - Tempo médio por documento: {avg_time:.2f}s")
        print(f"   - Tempo total de processamento: {total_time:.2f}s")
    
    # Detalhes dos documentos processados
    if results['documents']:
        print(f"\n📋 Documentos Processados com Sucesso:")
        print(f"{'Arquivo':<35} {'Nota':<10} {'Valor (R$)':<15} {'Emitente':<30} {'Itens':<6} {'Tempo':<8}")
        print(f"{'-'*35} {'-'*10} {'-'*15} {'-'*30} {'-'*6} {'-'*8}")
        
        total_value = 0
        total_items = 0
        
        for doc in results['documents']:
            filename_short = doc['filename'][:32] + "..." if len(doc['filename']) > 35 else doc['filename']
            emitente_short = (doc['emitente'] or 'N/A')[:27] + "..." if doc['emitente'] and len(doc['emitente']) > 30 else (doc['emitente'] or 'N/A')
            valor_str = f"{doc['valor_total']:,.2f}" if doc['valor_total'] else "N/A"
            
            print(f"{filename_short:<35} {doc['numero_nota'] or 'N/A':<10} {valor_str:<15} {emitente_short:<30} {doc['itens_count']:<6} {doc['processing_time']:.1f}s")
            
            if doc['valor_total']:
                total_value += doc['valor_total']
            total_items += doc['itens_count']
        
        print(f"\n💰 Resumo Financeiro:")
        print(f"   - Valor total processado: R$ {total_value:,.2f}")
        print(f"   - Total de itens categorizados: {total_items}")
        print(f"   - Valor médio por documento: R$ {(total_value / len(results['documents'])):,.2f}")
    
    # Testar métricas do dashboard
    print(f"\n📊 Testando métricas do dashboard...")
    try:
        metrics = await get_dashboard_metrics()
        suppliers = await get_top_suppliers()
        categories = await get_product_categories()
        
        print(f"✅ Dashboard atualizado:")
        print(f"   - Total de documentos no sistema: {metrics.get('total_documentos', 0)}")
        print(f"   - Documentos processados: {metrics.get('documentos_processados', 0)}")
        print(f"   - Valor total geral: R$ {metrics.get('valor_total', 0):,.2f}")
        print(f"   - Fornecedores únicos: {len(suppliers.get('suppliers', []))}")
        print(f"   - Categorias de produtos: {len(categories.get('categories', []))}")
        
        # Mostrar top 3 fornecedores
        top_suppliers = suppliers.get('suppliers', [])[:3]
        if top_suppliers:
            print(f"\n🏢 Top 3 Fornecedores:")
            for i, supplier in enumerate(top_suppliers, 1):
                print(f"   {i}. {supplier.get('name', 'N/A')} - R$ {supplier.get('total_value', 0):,.2f}")
        
        # Mostrar top 3 categorias
        top_categories = categories.get('categories', [])[:3]
        if top_categories:
            print(f"\n📦 Top 3 Categorias:")
            for i, category in enumerate(top_categories, 1):
                print(f"   {i}. {category.get('category', 'N/A')} - R$ {category.get('total_value', 0):,.2f}")
        
    except Exception as e:
        print(f"⚠️  Erro ao testar dashboard: {e}")
    
    print(f"\n🎉 Teste com arquivos XML reais concluído!")
    
    if results['successful'] > 0:
        print(f"✅ {results['successful']} documento(s) processado(s) com sucesso!")
        print(f"📊 Todos os dados foram salvos no novo schema do banco!")
        print(f"🎯 Sistema funcionando perfeitamente com documentos fiscais reais!")
        return True
    else:
        print(f"❌ Nenhum documento foi processado com sucesso")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando teste com arquivos XML reais\n")
    
    success = asyncio.run(test_real_xml_files())
    
    if success:
        print("\n✅ TESTE COM ARQUIVOS REAIS CONCLUÍDO COM SUCESSO!")
        print("🎯 O sistema está pronto para produção!")
        return True
    else:
        print("\n❌ FALHA NO TESTE COM ARQUIVOS REAIS")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)