#!/usr/bin/env python3
"""
Verificar se o sistema de upsert está funcionando corretamente
Contar registros únicos por chave de acesso
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import supabase

def verify_upsert_results():
    """Verificar resultados do upsert"""
    
    print("🔍 Verificando resultados do sistema de upsert\n")
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    try:
        # 1. Contar total de documentos
        total_result = supabase.table('fiscal_documents').select('id', count='exact').execute()
        total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
        
        print(f"📊 Total de registros na tabela fiscal_documents: {total_count}")
        
        # 2. Contar chaves de acesso únicas
        unique_keys_result = supabase.table('fiscal_documents').select('chave_acesso').execute()
        unique_keys = set()
        for doc in unique_keys_result.data:
            if doc.get('chave_acesso'):
                unique_keys.add(doc['chave_acesso'])
        
        print(f"📊 Chaves de acesso únicas: {len(unique_keys)}")
        
        # 3. Verificar se há duplicatas
        if total_count > len(unique_keys):
            print(f"⚠️  ATENÇÃO: Há {total_count - len(unique_keys)} registros duplicados!")
            
            # Mostrar duplicatas manualmente
            chave_counts = {}
            for doc in unique_keys_result.data:
                chave = doc.get('chave_acesso')
                if chave:
                    chave_counts[chave] = chave_counts.get(chave, 0) + 1
            
            print(f"🔍 Chaves duplicadas:")
            for chave, count in chave_counts.items():
                if count > 1:
                    print(f"   - {chave}: {count} registros")
        else:
            print(f"✅ Não há duplicatas - upsert funcionando corretamente!")
        
        # 4. Mostrar detalhes dos documentos processados
        docs_result = supabase.table('fiscal_documents').select('chave_acesso, numero_nota, valor_total, dh_emi, dh_evento, created_at').order('created_at', desc=True).execute()
        
        print(f"\n📋 Documentos no banco:")
        print(f"{'Chave (últimos 8)':<15} {'Nota':<10} {'Valor':<12} {'dhEmi':<20} {'dhEvento':<20}")
        print(f"{'-'*15} {'-'*10} {'-'*12} {'-'*20} {'-'*20}")
        
        for doc in docs_result.data:
            chave_short = doc.get('chave_acesso', 'N/A')[-8:] if doc.get('chave_acesso') else 'N/A'
            nota = doc.get('numero_nota', 'N/A')
            valor_raw = doc.get('valor_total')
            valor = f"R$ {valor_raw:,.2f}" if valor_raw is not None else 'N/A'
            dh_emi = doc.get('dh_emi', 'N/A')[:19] if doc.get('dh_emi') else 'N/A'
            dh_evento = doc.get('dh_evento', 'N/A')[:19] if doc.get('dh_evento') else 'N/A'
            
            print(f"{chave_short:<15} {nota:<10} {valor:<12} {dh_emi:<20} {dh_evento:<20}")
        
        # 5. Verificar dados nas tabelas relacionadas
        extracted_count_result = supabase.table('extracted_data').select('id', count='exact').execute()
        extracted_count = extracted_count_result.count if hasattr(extracted_count_result, 'count') else len(extracted_count_result.data)
        
        items_count_result = supabase.table('document_items').select('id', count='exact').execute()
        items_count = items_count_result.count if hasattr(items_count_result, 'count') else len(items_count_result.data)
        
        print(f"\n📊 Dados relacionados:")
        print(f"   - extracted_data: {extracted_count} registros")
        print(f"   - document_items: {items_count} registros")
        
        # 6. Verificar integridade dos dados
        docs_with_data = supabase.table('fiscal_documents').select('id').not_.is_('valor_total', 'null').execute()
        docs_with_data_count = len(docs_with_data.data)
        
        print(f"   - Documentos com valor_total: {docs_with_data_count}")
        
        if docs_with_data_count > 0:
            print(f"✅ Dados estão sendo salvos corretamente")
        else:
            print(f"⚠️  Nenhum documento tem valor_total - pode haver problema no salvamento")
        
        # 7. Resumo final
        print(f"\n🎯 RESUMO:")
        print(f"   - Total de registros: {total_count}")
        print(f"   - Chaves únicas: {len(unique_keys)}")
        print(f"   - Duplicatas: {max(0, total_count - len(unique_keys))}")
        print(f"   - Upsert funcionando: {'✅ SIM' if total_count == len(unique_keys) else '❌ NÃO'}")
        
        return total_count == len(unique_keys)
        
    except Exception as e:
        print(f"❌ Erro ao verificar upsert: {e}")
        return False

def main():
    """Função principal"""
    success = verify_upsert_results()
    
    if success:
        print(f"\n✅ SISTEMA DE UPSERT FUNCIONANDO CORRETAMENTE!")
    else:
        print(f"\n❌ PROBLEMAS DETECTADOS NO SISTEMA DE UPSERT")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)