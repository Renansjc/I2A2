#!/usr/bin/env python3
"""
Teste avançado de upsert - cenários específicos
Testa diferentes cenários de upsert com versões e timestamps
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    save_extracted_data,
    xml_agent
)

async def test_advanced_upsert_scenarios():
    """Testa cenários avançados de upsert"""
    
    print("🧪 TESTE AVANÇADO DE UPSERT - CENÁRIOS ESPECÍFICOS\n")
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    print("✅ Supabase conectado")
    
    # Chave de acesso fictícia para teste
    test_chave = "99999999999999999999999999999999999999999999"
    
    # Cenário 1: Documento novo
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 1: Documento completamente novo")
    print(f"{'='*60}")
    
    try:
        doc_id_1 = str(uuid.uuid4())
        
        # Dados do primeiro documento
        extracted_data_1 = {
            'chave_acesso': test_chave,
            'numero_nota': '12345',
            'serie': '1',
            'data_emissao': '2025-01-15',
            'natureza_operacao': 'Venda de Mercadoria',
            'valor_total': 100.50,
            'dh_emi': '2025-01-15T10:00:00-03:00',
            'dh_evento': None,
            'emitente_razao_social': 'Empresa Teste LTDA',
            'emitente_cnpj': '12345678000199',
            'destinatario_nome': 'Cliente Teste',
            'destinatario_cpf': '12345678901',
            'items': [{
                'codigo_produto': 'PROD001',
                'descricao': 'Produto Teste',
                'valor_produto': 100.50,
                'quantidade_comercial': 1.0
            }]
        }
        
        print(f"📋 Inserindo documento novo:")
        print(f"   - Chave: {test_chave}")
        print(f"   - dhEmi: {extracted_data_1['dh_emi']}")
        print(f"   - Valor: R$ {extracted_data_1['valor_total']}")
        
        success_1 = await save_extracted_data(doc_id_1, extracted_data_1)
        
        if success_1:
            print(f"✅ Documento novo inserido com sucesso")
        else:
            print(f"❌ Falha ao inserir documento novo")
            return False
            
    except Exception as e:
        print(f"❌ Erro no cenário 1: {e}")
        return False
    
    # Verificar inserção
    try:
        doc_check = supabase.table('fiscal_documents').select('*').eq('chave_acesso', test_chave).execute()
        if doc_check.data:
            doc = doc_check.data[0]
            print(f"📋 Documento verificado no banco:")
            print(f"   - ID: {doc['id']}")
            print(f"   - Número: {doc['numero_nota']}")
            print(f"   - Valor: R$ {doc['valor_total']}")
            print(f"   - dhEmi: {doc['dh_emi']}")
    except Exception as e:
        print(f"⚠️  Erro ao verificar documento: {e}")
    
    # Cenário 2: Mesmo documento (deve ser rejeitado)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 2: Mesmo documento exato (deve ser rejeitado)")
    print(f"{'='*60}")
    
    try:
        doc_id_2 = str(uuid.uuid4())
        
        # Mesmos dados exatos
        extracted_data_2 = extracted_data_1.copy()
        
        print(f"📋 Tentando inserir documento idêntico:")
        print(f"   - Chave: {test_chave}")
        print(f"   - dhEmi: {extracted_data_2['dh_emi']}")
        print(f"   - Valor: R$ {extracted_data_2['valor_total']}")
        
        success_2 = await save_extracted_data(doc_id_2, extracted_data_2)
        
        if success_2:
            print(f"⚠️  Documento foi aceito (pode indicar problema)")
        else:
            print(f"✅ Documento rejeitado corretamente (versão não é mais nova)")
            
    except Exception as e:
        print(f"❌ Erro no cenário 2: {e}")
    
    # Cenário 3: Versão mais antiga (deve ser rejeitada)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 3: Versão mais antiga (deve ser rejeitada)")
    print(f"{'='*60}")
    
    try:
        doc_id_3 = str(uuid.uuid4())
        
        # Dados com dhEmi mais antigo
        extracted_data_3 = extracted_data_1.copy()
        extracted_data_3['dh_emi'] = '2025-01-14T09:00:00-03:00'  # 1 dia antes
        extracted_data_3['valor_total'] = 200.00  # Valor diferente
        
        print(f"📋 Tentando inserir versão mais antiga:")
        print(f"   - Chave: {test_chave}")
        print(f"   - dhEmi: {extracted_data_3['dh_emi']} (mais antigo)")
        print(f"   - Valor: R$ {extracted_data_3['valor_total']} (diferente)")
        
        success_3 = await save_extracted_data(doc_id_3, extracted_data_3)
        
        if success_3:
            print(f"⚠️  Versão antiga foi aceita (pode indicar problema)")
        else:
            print(f"✅ Versão antiga rejeitada corretamente")
            
    except Exception as e:
        print(f"❌ Erro no cenário 3: {e}")
    
    # Cenário 4: Versão mais nova (deve atualizar)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 4: Versão mais nova (deve atualizar)")
    print(f"{'='*60}")
    
    try:
        doc_id_4 = str(uuid.uuid4())
        
        # Dados com dhEmi mais novo
        extracted_data_4 = extracted_data_1.copy()
        extracted_data_4['dh_emi'] = '2025-01-16T11:00:00-03:00'  # 1 dia depois
        extracted_data_4['valor_total'] = 150.75  # Valor atualizado
        extracted_data_4['numero_nota'] = '12346'  # Número atualizado
        
        print(f"📋 Tentando inserir versão mais nova:")
        print(f"   - Chave: {test_chave}")
        print(f"   - dhEmi: {extracted_data_4['dh_emi']} (mais novo)")
        print(f"   - Valor: R$ {extracted_data_4['valor_total']} (atualizado)")
        print(f"   - Número: {extracted_data_4['numero_nota']} (atualizado)")
        
        success_4 = await save_extracted_data(doc_id_4, extracted_data_4)
        
        if success_4:
            print(f"✅ Versão mais nova aceita - documento atualizado")
        else:
            print(f"❌ Versão mais nova rejeitada (problema no upsert)")
            
    except Exception as e:
        print(f"❌ Erro no cenário 4: {e}")
    
    # Verificar estado final
    print(f"\n{'='*60}")
    print(f"📊 VERIFICAÇÃO FINAL")
    print(f"{'='*60}")
    
    try:
        # Contar documentos com esta chave
        doc_count = supabase.table('fiscal_documents').select('id', count='exact').eq('chave_acesso', test_chave).execute()
        count = doc_count.count if hasattr(doc_count, 'count') else len(doc_count.data)
        
        print(f"📊 Documentos com chave {test_chave}: {count}")
        
        if count == 1:
            print(f"✅ Apenas 1 documento mantido (upsert funcionando)")
            
            # Verificar qual versão foi mantida
            final_doc = supabase.table('fiscal_documents').select('*').eq('chave_acesso', test_chave).execute()
            if final_doc.data:
                doc = final_doc.data[0]
                print(f"📋 Versão final mantida:")
                print(f"   - Número: {doc['numero_nota']}")
                print(f"   - Valor: R$ {doc['valor_total']}")
                print(f"   - dhEmi: {doc['dh_emi']}")
                
                # Verificar se é a versão mais nova
                if doc['numero_nota'] == '12346' and doc['valor_total'] == 150.75:
                    print(f"✅ Versão mais nova foi mantida corretamente")
                else:
                    print(f"⚠️  Versão mantida pode não ser a mais nova")
        else:
            print(f"❌ {count} documentos encontrados - deveria ser apenas 1")
            
        # Verificar dados relacionados
        extracted_count = supabase.table('extracted_data').select('id', count='exact').eq('document_id', doc['id'] if 'doc' in locals() else '').execute()
        items_count = supabase.table('document_items').select('id', count='exact').eq('document_id', doc['id'] if 'doc' in locals() else '').execute()
        
        print(f"📊 Dados relacionados:")
        print(f"   - extracted_data: {extracted_count.count if hasattr(extracted_count, 'count') else len(extracted_count.data)}")
        print(f"   - document_items: {items_count.count if hasattr(items_count, 'count') else len(items_count.data)}")
        
    except Exception as e:
        print(f"⚠️  Erro na verificação final: {e}")
    
    # Cenário 5: Documento com dhEvento (prioridade máxima)
    print(f"\n{'='*60}")
    print(f"📄 CENÁRIO 5: Documento com dhEvento (deve ter prioridade)")
    print(f"{'='*60}")
    
    try:
        doc_id_5 = str(uuid.uuid4())
        
        # Dados com dhEvento (prioridade sobre dhEmi)
        extracted_data_5 = extracted_data_1.copy()
        extracted_data_5['dh_emi'] = '2025-01-15T10:00:00-03:00'  # dhEmi mais antigo
        extracted_data_5['dh_evento'] = '2025-01-17T12:00:00-03:00'  # dhEvento mais novo
        extracted_data_5['valor_total'] = 300.00  # Valor final
        extracted_data_5['numero_nota'] = '12347'  # Número final
        
        print(f"📋 Tentando inserir documento com dhEvento:")
        print(f"   - Chave: {test_chave}")
        print(f"   - dhEmi: {extracted_data_5['dh_emi']}")
        print(f"   - dhEvento: {extracted_data_5['dh_evento']} (prioridade)")
        print(f"   - Valor: R$ {extracted_data_5['valor_total']}")
        print(f"   - Número: {extracted_data_5['numero_nota']}")
        
        success_5 = await save_extracted_data(doc_id_5, extracted_data_5)
        
        if success_5:
            print(f"✅ Documento com dhEvento aceito")
        else:
            print(f"❌ Documento com dhEvento rejeitado")
            
    except Exception as e:
        print(f"❌ Erro no cenário 5: {e}")
    
    # Verificação final após dhEvento
    try:
        final_doc_2 = supabase.table('fiscal_documents').select('*').eq('chave_acesso', test_chave).execute()
        if final_doc_2.data:
            doc = final_doc_2.data[0]
            print(f"📋 Versão final após dhEvento:")
            print(f"   - Número: {doc['numero_nota']}")
            print(f"   - Valor: R$ {doc['valor_total']}")
            print(f"   - dhEmi: {doc['dh_emi']}")
            print(f"   - dhEvento: {doc['dh_evento']}")
            
            # Verificar se dhEvento teve prioridade
            if doc['numero_nota'] == '12347' and doc['valor_total'] == 300.00:
                print(f"✅ dhEvento teve prioridade corretamente")
            else:
                print(f"⚠️  dhEvento pode não ter tido prioridade")
    except Exception as e:
        print(f"⚠️  Erro na verificação final: {e}")
    
    # Limpeza - remover documento de teste
    print(f"\n{'='*60}")
    print(f"🧹 LIMPEZA - Removendo documento de teste")
    print(f"{'='*60}")
    
    try:
        # Remover documento de teste
        delete_result = supabase.table('fiscal_documents').delete().eq('chave_acesso', test_chave).execute()
        print(f"✅ Documento de teste removido")
    except Exception as e:
        print(f"⚠️  Erro na limpeza: {e}")
    
    return True

def main():
    """Função principal"""
    print("🚀 Iniciando teste avançado de upsert\n")
    
    success = asyncio.run(test_advanced_upsert_scenarios())
    
    if success:
        print("\n✅ TESTE AVANÇADO DE UPSERT CONCLUÍDO!")
        print("🎯 Todos os cenários de upsert testados!")
        return True
    else:
        print("\n❌ FALHA NO TESTE AVANÇADO DE UPSERT")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)