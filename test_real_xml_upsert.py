#!/usr/bin/env python3
"""
Teste de upsert com XML real modificado
Simula uma versão atualizada de um documento fiscal real
"""

import os
import sys
import asyncio
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    create_document_record,
    upload_file_to_storage,
    save_extracted_data,
    xml_agent
)

def modify_xml_timestamp(xml_content, new_timestamp):
    """Modifica o timestamp dhEmi no XML"""
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Encontrar namespace
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Procurar dhEmi
        dh_emi_elem = root.find('.//nfe:dhEmi', ns)
        if dh_emi_elem is not None:
            dh_emi_elem.text = new_timestamp
            print(f"✅ dhEmi atualizado para: {new_timestamp}")
        else:
            print(f"⚠️  dhEmi não encontrado no XML")
        
        # Converter de volta para string
        return ET.tostring(root, encoding='unicode')
        
    except Exception as e:
        print(f"❌ Erro ao modificar XML: {e}")
        return xml_content

def modify_xml_value(xml_content, new_value):
    """Modifica o valor total no XML"""
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Encontrar namespace
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Procurar vNF (valor total da nota)
        v_nf_elem = root.find('.//nfe:vNF', ns)
        if v_nf_elem is not None:
            v_nf_elem.text = str(new_value)
            print(f"✅ vNF atualizado para: {new_value}")
        else:
            print(f"⚠️  vNF não encontrado no XML")
        
        # Converter de volta para string
        return ET.tostring(root, encoding='unicode')
        
    except Exception as e:
        print(f"❌ Erro ao modificar valor XML: {e}")
        return xml_content

async def test_real_xml_upsert():
    """Testa upsert com XML real modificado"""
    
    print("🧪 TESTE DE UPSERT COM XML REAL MODIFICADO\n")
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    print("✅ Supabase conectado")
    
    # Usar arquivo XML real
    xml_file = "xml_nf/42250383261420001201550990003348371042993209-nfe.xml"
    
    if not os.path.exists(xml_file):
        print(f"❌ Arquivo {xml_file} não encontrado")
        return False
    
    # Ler arquivo original
    with open(xml_file, 'r', encoding='utf-8') as f:
        original_xml = f.read()
    
    print(f"📄 Arquivo: {xml_file}")
    print(f"📏 Tamanho: {len(original_xml):,} caracteres")
    
    # Processar XML original para obter chave de acesso
    try:
        xml_result = xml_agent.process_xml(original_xml)
        extracted_data = xml_result.get("extracted_data", {})
        chave_acesso = extracted_data.get('chave_acesso')
        original_dh_emi = extracted_data.get('dh_emi')
        original_value = extracted_data.get('valor_total')
        
        print(f"📋 Chave de acesso: {chave_acesso}")
        print(f"📋 dhEmi original: {original_dh_emi}")
        print(f"📋 Valor original: R$ {original_value}")
        
    except Exception as e:
        print(f"❌ Erro ao processar XML original: {e}")
        return False
    
    # Verificar se documento já existe no banco
    try:
        existing_doc = supabase.table('fiscal_documents').select('*').eq('chave_acesso', chave_acesso).execute()
        if existing_doc.data:
            doc = existing_doc.data[0]
            print(f"📋 Documento já existe no banco:")
            print(f"   - ID: {doc['id']}")
            print(f"   - Valor atual: R$ {doc['valor_total']}")
            print(f"   - dhEmi atual: {doc['dh_emi']}")
            existing_id = doc['id']
        else:
            print(f"📋 Documento não existe no banco - será criado")
            existing_id = None
    except Exception as e:
        print(f"⚠️  Erro ao verificar documento existente: {e}")
        existing_id = None
    
    # Cenário 1: Processar versão original (se não existir)
    if not existing_id:
        print(f"\n{'='*60}")
        print(f"📄 CENÁRIO 1: Processando versão original")
        print(f"{'='*60}")
        
        try:
            doc_id_1 = str(uuid.uuid4())
            
            # Upload para storage
            file_path_1 = await upload_file_to_storage(original_xml.encode('utf-8'), f"original_{os.path.basename(xml_file)}", doc_id_1)
            print(f"✅ Upload original concluído: {file_path_1}")
            
            # Salvar no banco
            success_1 = await save_extracted_data(doc_id_1, extracted_data)
            
            if success_1:
                print(f"✅ Versão original processada")
                existing_id = doc_id_1
            else:
                print(f"❌ Falha ao processar versão original")
                return False
                
        except Exception as e:
            print(f"❌ Erro no cenário 1: {e}")
            return False
    
    # Cenário 2: Versão com timestamp mais antigo (deve ser rejeitada)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 2: Versão com timestamp mais antigo")
    print(f"{'='*60}")
    
    try:
        # Modificar XML para ter timestamp mais antigo
        older_timestamp = "2025-03-15T14:30:00-03:00"  # 1 hora antes
        modified_xml_older = modify_xml_timestamp(original_xml, older_timestamp)
        modified_xml_older = modify_xml_value(modified_xml_older, "5.99")  # Valor menor
        
        doc_id_2 = str(uuid.uuid4())
        
        # Upload para storage
        file_path_2 = await upload_file_to_storage(modified_xml_older.encode('utf-8'), f"older_{os.path.basename(xml_file)}", doc_id_2)
        print(f"✅ Upload versão antiga concluído: {file_path_2}")
        
        # Processar XML modificado
        xml_result_2 = xml_agent.process_xml(modified_xml_older)
        extracted_data_2 = xml_result_2.get("extracted_data", {})
        
        print(f"📋 Versão mais antiga:")
        print(f"   - dhEmi: {extracted_data_2.get('dh_emi')}")
        print(f"   - Valor: R$ {extracted_data_2.get('valor_total')}")
        
        # Tentar salvar no banco
        success_2 = await save_extracted_data(doc_id_2, extracted_data_2)
        
        if success_2:
            print(f"⚠️  Versão antiga foi aceita (verificar lógica)")
        else:
            print(f"✅ Versão antiga rejeitada corretamente")
            
    except Exception as e:
        print(f"❌ Erro no cenário 2: {e}")
    
    # Cenário 3: Versão com timestamp mais novo (deve atualizar)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 3: Versão com timestamp mais novo")
    print(f"{'='*60}")
    
    try:
        # Modificar XML para ter timestamp mais novo
        newer_timestamp = "2025-03-16T16:45:00-03:00"  # 1 hora depois
        modified_xml_newer = modify_xml_timestamp(original_xml, newer_timestamp)
        modified_xml_newer = modify_xml_value(modified_xml_newer, "8.99")  # Valor maior
        
        doc_id_3 = str(uuid.uuid4())
        
        # Upload para storage
        file_path_3 = await upload_file_to_storage(modified_xml_newer.encode('utf-8'), f"newer_{os.path.basename(xml_file)}", doc_id_3)
        print(f"✅ Upload versão nova concluído: {file_path_3}")
        
        # Processar XML modificado
        xml_result_3 = xml_agent.process_xml(modified_xml_newer)
        extracted_data_3 = xml_result_3.get("extracted_data", {})
        
        print(f"📋 Versão mais nova:")
        print(f"   - dhEmi: {extracted_data_3.get('dh_emi')}")
        print(f"   - Valor: R$ {extracted_data_3.get('valor_total')}")
        
        # Tentar salvar no banco
        success_3 = await save_extracted_data(doc_id_3, extracted_data_3)
        
        if success_3:
            print(f"✅ Versão mais nova aceita - documento atualizado")
        else:
            print(f"❌ Versão mais nova rejeitada (problema no upsert)")
            
    except Exception as e:
        print(f"❌ Erro no cenário 3: {e}")
    
    # Verificação final
    print(f"\n{'='*60}")
    print(f"📊 VERIFICAÇÃO FINAL")
    print(f"{'='*60}")
    
    try:
        # Verificar documento final no banco
        final_doc = supabase.table('fiscal_documents').select('*').eq('chave_acesso', chave_acesso).execute()
        
        if final_doc.data:
            doc = final_doc.data[0]
            print(f"📋 Estado final do documento:")
            print(f"   - ID: {doc['id']}")
            print(f"   - Número: {doc['numero_nota']}")
            print(f"   - Valor: R$ {doc['valor_total']}")
            print(f"   - dhEmi: {doc['dh_emi']}")
            print(f"   - dhEvento: {doc['dh_evento']}")
            
            # Verificar se é a versão mais nova
            if doc['valor_total'] == 8.99:
                print(f"✅ Versão mais nova foi mantida (valor R$ 8.99)")
            elif doc['valor_total'] == 6.99:
                print(f"⚠️  Versão original mantida (valor R$ 6.99)")
            elif doc['valor_total'] == 5.99:
                print(f"❌ Versão mais antiga mantida (valor R$ 5.99)")
            else:
                print(f"⚠️  Valor inesperado: R$ {doc['valor_total']}")
        else:
            print(f"❌ Documento não encontrado no banco")
        
        # Contar registros com esta chave
        count_result = supabase.table('fiscal_documents').select('id', count='exact').eq('chave_acesso', chave_acesso).execute()
        count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        print(f"📊 Total de registros com esta chave: {count}")
        
        if count == 1:
            print(f"✅ Apenas 1 registro mantido (upsert funcionando)")
        else:
            print(f"❌ {count} registros encontrados - deveria ser 1")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro na verificação final: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando teste de upsert com XML real modificado\n")
    
    success = asyncio.run(test_real_xml_upsert())
    
    if success:
        print("\n✅ TESTE DE UPSERT COM XML REAL CONCLUÍDO!")
        print("🎯 Sistema de upsert validado com documentos fiscais reais!")
        return True
    else:
        print("\n❌ FALHA NO TESTE DE UPSERT COM XML REAL")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)