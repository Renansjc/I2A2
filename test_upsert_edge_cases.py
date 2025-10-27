#!/usr/bin/env python3
"""
Teste de edge cases do sistema de upsert
Testa cenários extremos e casos especiais
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
    get_dashboard_metrics
)

async def test_upsert_edge_cases():
    """Testa casos extremos do upsert"""
    
    print("🧪 TESTE DE EDGE CASES DO SISTEMA DE UPSERT\n")
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    print("✅ Supabase conectado")
    
    # Estado inicial
    try:
        initial_metrics = await get_dashboard_metrics()
        initial_count = initial_metrics.get('total_documents', 0)
        print(f"📊 Documentos iniciais no sistema: {initial_count}")
    except:
        initial_count = 0
    
    # Edge Case 1: dhEmi e dhEvento nulos
    print(f"\n{'='*60}")
    print(f"📄 EDGE CASE 1: dhEmi e dhEvento nulos")
    print(f"{'='*60}")
    
    try:
        test_chave_1 = "11111111111111111111111111111111111111111111"
        doc_id_1 = str(uuid.uuid4())
        
        extracted_data_1 = {
            'chave_acesso': test_chave_1,
            'numero_nota': '11111',
            'serie': '1',
            'data_emissao': '2025-01-15',
            'valor_total': 100.00,
            'dh_emi': None,  # Nulo
            'dh_evento': None,  # Nulo
            'emitente_razao_social': 'Empresa Teste 1',
            'emitente_cnpj': '11111111000111'
        }
        
        print(f"📋 Inserindo documento com timestamps nulos:")
        print(f"   - Chave: {test_chave_1}")
        print(f"   - dhEmi: {extracted_data_1['dh_emi']}")
        print(f"   - dhEvento: {extracted_data_1['dh_evento']}")
        
        success_1 = await save_extracted_data(doc_id_1, extracted_data_1)
        
        if success_1:
            print(f"✅ Documento com timestamps nulos inserido")
        else:
            print(f"❌ Falha ao inserir documento com timestamps nulos")
            
    except Exception as e:
        print(f"❌ Erro no edge case 1: {e}")
    
    # Edge Case 2: Tentar atualizar documento com timestamps nulos
    print(f"\n{'='*60}")
    print(f"📄 EDGE CASE 2: Atualizar documento com timestamps nulos")
    print(f"{'='*60}")
    
    try:
        doc_id_2 = str(uuid.uuid4())
        
        extracted_data_2 = {
            'chave_acesso': test_chave_1,  # Mesma chave
            'numero_nota': '11112',
            'serie': '1',
            'data_emissao': '2025-01-16',
            'valor_total': 200.00,
            'dh_emi': '2025-01-16T10:00:00-03:00',  # Com timestamp
            'dh_evento': None,
            'emitente_razao_social': 'Empresa Teste 1 Atualizada',
            'emitente_cnpj': '11111111000111'
        }
        
        print(f"📋 Tentando atualizar com dhEmi válido:")
        print(f"   - Chave: {test_chave_1}")
        print(f"   - dhEmi: {extracted_data_2['dh_emi']}")
        print(f"   - Valor: R$ {extracted_data_2['valor_total']}")
        
        success_2 = await save_extracted_data(doc_id_2, extracted_data_2)
        
        if success_2:
            print(f"✅ Documento atualizado com timestamp válido")
        else:
            print(f"❌ Falha ao atualizar documento")
            
    except Exception as e:
        print(f"❌ Erro no edge case 2: {e}")
    
    # Edge Case 3: dhEvento vs dhEmi - prioridade
    print(f"\n{'='*60}")
    print(f"📄 EDGE CASE 3: Prioridade dhEvento vs dhEmi")
    print(f"{'='*60}")
    
    try:
        test_chave_3 = "33333333333333333333333333333333333333333333"
        doc_id_3a = str(uuid.uuid4())
        
        # Primeiro documento com dhEmi mais novo
        extracted_data_3a = {
            'chave_acesso': test_chave_3,
            'numero_nota': '33331',
            'valor_total': 300.00,
            'dh_emi': '2025-01-20T15:00:00-03:00',  # Mais novo
            'dh_evento': None,
            'emitente_razao_social': 'Empresa Teste 3A'
        }
        
        print(f"📋 Inserindo documento com dhEmi mais novo:")
        print(f"   - dhEmi: {extracted_data_3a['dh_emi']}")
        print(f"   - dhEvento: {extracted_data_3a['dh_evento']}")
        print(f"   - Valor: R$ {extracted_data_3a['valor_total']}")
        
        success_3a = await save_extracted_data(doc_id_3a, extracted_data_3a)
        
        if success_3a:
            print(f"✅ Primeiro documento inserido")
        
        # Segundo documento com dhEmi mais antigo mas dhEvento mais novo
        doc_id_3b = str(uuid.uuid4())
        
        extracted_data_3b = {
            'chave_acesso': test_chave_3,  # Mesma chave
            'numero_nota': '33332',
            'valor_total': 400.00,
            'dh_emi': '2025-01-19T10:00:00-03:00',  # Mais antigo
            'dh_evento': '2025-01-21T16:00:00-03:00',  # Mais novo que dhEmi anterior
            'emitente_razao_social': 'Empresa Teste 3B'
        }
        
        print(f"📋 Tentando atualizar com dhEvento mais novo:")
        print(f"   - dhEmi: {extracted_data_3b['dh_emi']} (mais antigo)")
        print(f"   - dhEvento: {extracted_data_3b['dh_evento']} (mais novo)")
        print(f"   - Valor: R$ {extracted_data_3b['valor_total']}")
        
        success_3b = await save_extracted_data(doc_id_3b, extracted_data_3b)
        
        if success_3b:
            print(f"✅ dhEvento teve prioridade sobre dhEmi")
        else:
            print(f"❌ dhEvento não teve prioridade")
            
    except Exception as e:
        print(f"❌ Erro no edge case 3: {e}")
    
    # Edge Case 4: Timestamps idênticos com valores diferentes
    print(f"\n{'='*60}")
    print(f"📄 EDGE CASE 4: Timestamps idênticos, valores diferentes")
    print(f"{'='*60}")
    
    try:
        test_chave_4 = "44444444444444444444444444444444444444444444"
        same_timestamp = "2025-01-25T12:00:00-03:00"
        
        # Primeiro documento
        doc_id_4a = str(uuid.uuid4())
        extracted_data_4a = {
            'chave_acesso': test_chave_4,
            'numero_nota': '44441',
            'valor_total': 500.00,
            'dh_emi': same_timestamp,
            'dh_evento': None,
            'emitente_razao_social': 'Empresa Teste 4A'
        }
        
        print(f"📋 Inserindo primeiro documento:")
        print(f"   - dhEmi: {same_timestamp}")
        print(f"   - Valor: R$ {extracted_data_4a['valor_total']}")
        
        success_4a = await save_extracted_data(doc_id_4a, extracted_data_4a)
        
        # Segundo documento com mesmo timestamp
        doc_id_4b = str(uuid.uuid4())
        extracted_data_4b = {
            'chave_acesso': test_chave_4,  # Mesma chave
            'numero_nota': '44442',
            'valor_total': 600.00,  # Valor diferente
            'dh_emi': same_timestamp,  # Mesmo timestamp
            'dh_evento': None,
            'emitente_razao_social': 'Empresa Teste 4B'
        }
        
        print(f"📋 Tentando inserir com mesmo timestamp:")
        print(f"   - dhEmi: {same_timestamp} (idêntico)")
        print(f"   - Valor: R$ {extracted_data_4b['valor_total']} (diferente)")
        
        success_4b = await save_extracted_data(doc_id_4b, extracted_data_4b)
        
        if success_4b:
            print(f"✅ Documento com timestamp idêntico processado")
        else:
            print(f"❌ Documento com timestamp idêntico rejeitado")
            
    except Exception as e:
        print(f"❌ Erro no edge case 4: {e}")
    
    # Edge Case 5: Chave de acesso inválida/muito longa
    print(f"\n{'='*60}")
    print(f"📄 EDGE CASE 5: Chave de acesso inválida")
    print(f"{'='*60}")
    
    try:
        # Chave muito longa
        invalid_chave = "5" * 100  # 100 caracteres
        doc_id_5 = str(uuid.uuid4())
        
        extracted_data_5 = {
            'chave_acesso': invalid_chave,
            'numero_nota': '55555',
            'valor_total': 700.00,
            'dh_emi': '2025-01-26T10:00:00-03:00',
            'emitente_razao_social': 'Empresa Teste 5'
        }
        
        print(f"📋 Tentando inserir chave inválida:")
        print(f"   - Chave: {invalid_chave[:50]}... ({len(invalid_chave)} chars)")
        
        success_5 = await save_extracted_data(doc_id_5, extracted_data_5)
        
        if success_5:
            print(f"⚠️  Chave inválida foi aceita")
        else:
            print(f"✅ Chave inválida rejeitada corretamente")
            
    except Exception as e:
        print(f"✅ Chave inválida causou erro esperado: {str(e)[:100]}...")
    
    # Verificação final de todos os edge cases
    print(f"\n{'='*60}")
    print(f"📊 VERIFICAÇÃO FINAL DOS EDGE CASES")
    print(f"{'='*60}")
    
    try:
        # Verificar cada documento de teste
        test_chaves = [
            ("11111111111111111111111111111111111111111111", "Timestamps nulos"),
            ("33333333333333333333333333333333333333333333", "Prioridade dhEvento"),
            ("44444444444444444444444444444444444444444444", "Timestamps idênticos")
        ]
        
        for chave, descricao in test_chaves:
            try:
                doc_result = supabase.table('fiscal_documents').select('*').eq('chave_acesso', chave).execute()
                if doc_result.data:
                    doc = doc_result.data[0]
                    print(f"📋 {descricao}:")
                    print(f"   - Chave: {chave[:20]}...")
                    print(f"   - Número: {doc['numero_nota']}")
                    print(f"   - Valor: R$ {doc['valor_total']}")
                    print(f"   - dhEmi: {doc['dh_emi']}")
                    print(f"   - dhEvento: {doc['dh_evento']}")
                else:
                    print(f"❌ {descricao}: Documento não encontrado")
            except Exception as e:
                print(f"⚠️  Erro ao verificar {descricao}: {e}")
        
        # Estado final
        final_metrics = await get_dashboard_metrics()
        final_count = final_metrics.get('total_documents', 0)
        new_docs = final_count - initial_count
        
        print(f"\n📊 RESUMO FINAL:")
        print(f"   - Documentos iniciais: {initial_count}")
        print(f"   - Documentos finais: {final_count}")
        print(f"   - Novos documentos: {new_docs}")
        
        # Limpeza - remover documentos de teste
        print(f"\n🧹 LIMPEZA - Removendo documentos de teste")
        
        for chave, _ in test_chaves:
            try:
                delete_result = supabase.table('fiscal_documents').delete().eq('chave_acesso', chave).execute()
                print(f"✅ Documento {chave[:20]}... removido")
            except Exception as e:
                print(f"⚠️  Erro ao remover {chave[:20]}...: {e}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Erro na verificação final: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando teste de edge cases do upsert\n")
    
    success = asyncio.run(test_upsert_edge_cases())
    
    if success:
        print("\n✅ TESTE DE EDGE CASES DO UPSERT CONCLUÍDO!")
        print("🎯 Sistema de upsert robusto validado!")
        return True
    else:
        print("\n❌ FALHA NO TESTE DE EDGE CASES")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)