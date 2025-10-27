#!/usr/bin/env python3
"""
Debug da extração de dados - verificar quais campos estão sendo extraídos vs salvos
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import supabase, xml_agent

def debug_xml_extraction():
    """Debug da extração de dados XML"""
    
    print("🔍 Debug da extração de dados XML\n")
    
    # Testar com um arquivo XML real
    xml_file = "xml_nf/42250383261420001201550990003348371042993209-nfe.xml"
    
    if not os.path.exists(xml_file):
        print(f"❌ Arquivo {xml_file} não encontrado")
        return False
    
    # Ler arquivo XML
    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print(f"📄 Processando arquivo: {xml_file}")
    print(f"📏 Tamanho do arquivo: {len(xml_content):,} caracteres\n")
    
    # Processar com agente XML
    xml_result = xml_agent.process_xml(xml_content)
    
    extracted_data = xml_result.get("extracted_data", {})
    validation_result = xml_result.get("validation", {})
    
    print("🔍 DADOS EXTRAÍDOS PELO AGENTE XML:")
    print("="*60)
    
    # Verificar dados básicos
    print("\n📋 DADOS BÁSICOS DA NOTA:")
    basic_fields = [
        'numero_nota', 'serie', 'chave_acesso', 'data_emissao', 
        'data_saida', 'natureza_operacao', 'valor_total', 
        'consumidor_final', 'presenca_comprador'
    ]
    
    for field in basic_fields:
        value = extracted_data.get(field)
        status = "✅" if value is not None else "❌"
        print(f"   {status} {field}: {value}")
    
    # Verificar emitente
    print("\n🏢 DADOS DO EMITENTE:")
    emitente = extracted_data.get('emitente', {})
    emitente_fields = [
        'razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 
        'crt', 'logradouro', 'numero', 'complemento', 'bairro', 
        'municipio', 'uf', 'cep', 'telefone'
    ]
    
    for field in emitente_fields:
        value = emitente.get(field)
        status = "✅" if value is not None else "❌"
        print(f"   {status} {field}: {value}")
    
    # Verificar destinatário
    print("\n👤 DADOS DO DESTINATÁRIO:")
    destinatario = extracted_data.get('destinatario', {})
    destinatario_fields = [
        'nome', 'razao_social', 'cnpj', 'cpf', 'inscricao_estadual',
        'logradouro', 'numero', 'complemento', 'bairro', 
        'municipio', 'uf', 'cep', 'telefone', 'email'
    ]
    
    for field in destinatario_fields:
        value = destinatario.get(field)
        status = "✅" if value is not None else "❌"
        print(f"   {status} {field}: {value}")
    
    # Verificar itens
    print("\n📦 ITENS DO DOCUMENTO:")
    itens = extracted_data.get('itens', [])
    print(f"   Total de itens: {len(itens)}")
    
    if itens:
        item = itens[0]  # Primeiro item
        print(f"\n   📋 Detalhes do primeiro item:")
        item_fields = [
            'codigo_produto', 'codigo_ean', 'descricao', 'ncm', 'cfop',
            'unidade_comercial', 'quantidade_comercial', 'valor_unitario_comercial',
            'unidade_tributavel', 'quantidade_tributavel', 'valor_unitario_tributavel',
            'valor_produto', 'valor_frete', 'valor_seguro', 'valor_desconto', 'valor_outros',
            'icms_origem', 'icms_cst', 'icms_base_calculo', 'icms_aliquota', 'icms_valor',
            'ipi_cst', 'ipi_valor', 'pis_cst', 'pis_base_calculo', 'pis_aliquota', 'pis_valor',
            'cofins_cst', 'cofins_base_calculo', 'cofins_aliquota', 'cofins_valor',
            'total_tributos_item'
        ]
        
        for field in item_fields:
            value = item.get(field)
            status = "✅" if value is not None else "❌"
            print(f"      {status} {field}: {value}")
    
    # Verificar impostos totais
    print("\n💰 IMPOSTOS TOTAIS:")
    impostos = extracted_data.get('impostos', {})
    
    icms = impostos.get('icms', {})
    print(f"   ICMS:")
    print(f"      ✅ valor: {icms.get('valor')}")
    print(f"      ✅ base_calculo: {icms.get('base_calculo')}")
    print(f"      ✅ aliquota: {icms.get('aliquota')}")
    
    ipi = impostos.get('ipi', {})
    print(f"   IPI:")
    print(f"      ✅ valor: {ipi.get('valor')}")
    
    pis = impostos.get('pis', {})
    print(f"   PIS:")
    print(f"      ✅ valor: {pis.get('valor')}")
    
    cofins = impostos.get('cofins', {})
    print(f"   COFINS:")
    print(f"      ✅ valor: {cofins.get('valor')}")
    
    # Verificar validação
    print(f"\n✅ VALIDAÇÃO:")
    print(f"   Válido: {validation_result.get('valid', False)}")
    print(f"   Confiança: {validation_result.get('confidence', 0):.2f}")
    if validation_result.get('errors'):
        print(f"   Erros: {validation_result.get('errors')}")
    if validation_result.get('warnings'):
        print(f"   Avisos: {validation_result.get('warnings')}")
    
    # Salvar dados extraídos para análise
    debug_file = f"debug_extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(debug_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_data': extracted_data,
            'validation': validation_result,
            'processing_metadata': xml_result.get('processing_metadata', {})
        }, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Dados salvos em: {debug_file}")
    
    return True

def check_database_fields():
    """Verificar quais campos estão sendo salvos no banco"""
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    print("\n🔍 VERIFICANDO DADOS NO BANCO DE DADOS:")
    print("="*60)
    
    try:
        # Buscar último documento processado
        docs_result = supabase.table('fiscal_documents').select('*').order('created_at', desc=True).limit(1).execute()
        
        if not docs_result.data:
            print("❌ Nenhum documento encontrado no banco")
            return False
        
        doc = docs_result.data[0]
        doc_id = doc['id']
        
        print(f"\n📄 Último documento processado: {doc['filename']}")
        print(f"🆔 ID: {doc_id}")
        
        # Verificar tabela fiscal_documents
        print(f"\n📋 TABELA fiscal_documents:")
        fiscal_fields = [
            'numero_nota', 'serie', 'chave_acesso', 'data_emissao', 'data_saida',
            'natureza_operacao', 'valor_produtos', 'valor_frete', 'valor_seguro',
            'valor_desconto', 'valor_outros', 'valor_total', 'icms_base_calculo',
            'icms_valor', 'icms_st_base_calculo', 'icms_st_valor', 'ipi_valor',
            'pis_valor', 'cofins_valor', 'total_tributos', 'modalidade_frete',
            'transportadora', 'peso_liquido', 'peso_bruto', 'quantidade_volumes',
            'forma_pagamento', 'valor_pagamento', 'data_vencimento', 'uf_origem',
            'uf_destino', 'tipo_operacao', 'consumidor_final', 'presenca_comprador'
        ]
        
        for field in fiscal_fields:
            value = doc.get(field)
            status = "✅" if value is not None else "❌"
            print(f"   {status} {field}: {value}")
        
        # Verificar tabela extracted_data
        extracted_result = supabase.table('extracted_data').select('*').eq('document_id', doc_id).execute()
        
        if extracted_result.data:
            extracted = extracted_result.data[0]
            print(f"\n🏢 TABELA extracted_data:")
            
            extracted_fields = [
                'emitente_razao_social', 'emitente_nome_fantasia', 'emitente_cnpj',
                'emitente_ie', 'emitente_crt', 'emitente_logradouro', 'emitente_numero',
                'emitente_complemento', 'emitente_bairro', 'emitente_municipio',
                'emitente_uf', 'emitente_cep', 'emitente_telefone', 'destinatario_nome',
                'destinatario_cnpj', 'destinatario_cpf', 'destinatario_ie',
                'destinatario_logradouro', 'destinatario_numero', 'destinatario_complemento',
                'destinatario_bairro', 'destinatario_municipio', 'destinatario_uf',
                'destinatario_cep', 'destinatario_telefone', 'destinatario_email'
            ]
            
            for field in extracted_fields:
                value = extracted.get(field)
                status = "✅" if value is not None else "❌"
                print(f"   {status} {field}: {value}")
        else:
            print(f"\n❌ Nenhum dado encontrado na tabela extracted_data")
        
        # Verificar tabela document_items
        items_result = supabase.table('document_items').select('*').eq('document_id', doc_id).execute()
        
        print(f"\n📦 TABELA document_items:")
        print(f"   Total de itens: {len(items_result.data)}")
        
        if items_result.data:
            item = items_result.data[0]
            item_fields = [
                'codigo_produto', 'codigo_ean', 'descricao', 'ncm', 'cfop',
                'unidade_comercial', 'quantidade_comercial', 'valor_unitario_comercial',
                'unidade_tributavel', 'quantidade_tributavel', 'valor_unitario_tributavel',
                'valor_produto', 'valor_frete', 'valor_seguro', 'valor_desconto',
                'valor_outros', 'icms_origem', 'icms_cst', 'icms_base_calculo',
                'icms_aliquota', 'icms_valor', 'ipi_cst', 'ipi_valor', 'pis_cst',
                'pis_base_calculo', 'pis_aliquota', 'pis_valor', 'cofins_cst',
                'cofins_base_calculo', 'cofins_aliquota', 'cofins_valor',
                'total_tributos_item', 'categoria', 'categoria_confianca',
                'subcategoria', 'marca', 'modelo'
            ]
            
            print(f"\n   📋 Detalhes do primeiro item:")
            for field in item_fields:
                value = item.get(field)
                status = "✅" if value is not None else "❌"
                print(f"      {status} {field}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 DEBUG DA EXTRAÇÃO E SALVAMENTO DE DADOS\n")
    
    # 1. Debug da extração XML
    extraction_ok = debug_xml_extraction()
    
    if extraction_ok:
        # 2. Verificar dados no banco
        check_database_fields()
    
    print(f"\n🎯 Debug concluído!")
    print(f"📋 Verifique os resultados acima para identificar campos não preenchidos")

if __name__ == "__main__":
    main()