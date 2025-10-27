#!/usr/bin/env python3
"""
Aplicar schema de upsert e limpar duplicatas
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

def apply_upsert_schema():
    """Aplicar schema de upsert no banco"""
    
    print("🔧 Aplicando schema de upsert no banco de dados\n")
    
    if not supabase:
        print("❌ Supabase não configurado")
        return False
    
    try:
        # 1. Adicionar colunas se não existirem
        print("1. Adicionando colunas dh_evento e dh_emi...")
        
        # Verificar se as colunas já existem
        columns_result = supabase.rpc('execute_sql', {
            'query': """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'fiscal_documents' 
            AND column_name IN ('dh_evento', 'dh_emi')
            """
        }).execute()
        
        existing_columns = [col['column_name'] for col in columns_result.data] if columns_result.data else []
        
        if 'dh_evento' not in existing_columns:
            supabase.rpc('execute_sql', {
                'query': 'ALTER TABLE fiscal_documents ADD COLUMN dh_evento TIMESTAMP'
            }).execute()
            print("✅ Coluna dh_evento adicionada")
        else:
            print("✅ Coluna dh_evento já existe")
        
        if 'dh_emi' not in existing_columns:
            supabase.rpc('execute_sql', {
                'query': 'ALTER TABLE fiscal_documents ADD COLUMN dh_emi TIMESTAMP'
            }).execute()
            print("✅ Coluna dh_emi adicionada")
        else:
            print("✅ Coluna dh_emi já existe")
        
        # 2. Verificar duplicatas antes de aplicar constraint
        print("\n2. Verificando duplicatas...")
        
        duplicates_result = supabase.rpc('execute_sql', {
            'query': """
            SELECT chave_acesso, COUNT(*) as count 
            FROM fiscal_documents 
            WHERE chave_acesso IS NOT NULL 
            GROUP BY chave_acesso 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            """
        }).execute()
        
        if duplicates_result.data:
            print(f"⚠️  Encontradas {len(duplicates_result.data)} chaves duplicadas:")
            for dup in duplicates_result.data:
                print(f"   - {dup['chave_acesso']}: {dup['count']} registros")
            
            # 3. Remover duplicatas (manter o mais recente)
            print("\n3. Removendo duplicatas...")
            
            cleanup_result = supabase.rpc('execute_sql', {
                'query': """
                DELETE FROM fiscal_documents 
                WHERE id NOT IN (
                    SELECT DISTINCT ON (chave_acesso) id 
                    FROM fiscal_documents 
                    WHERE chave_acesso IS NOT NULL
                    ORDER BY chave_acesso, created_at DESC
                )
                """
            }).execute()
            
            print("✅ Duplicatas removidas")
        else:
            print("✅ Nenhuma duplicata encontrada")
        
        # 4. Aplicar constraint de chave única
        print("\n4. Aplicando constraint de chave única...")
        
        try:
            supabase.rpc('execute_sql', {
                'query': """
                ALTER TABLE fiscal_documents 
                ADD CONSTRAINT fiscal_documents_chave_acesso_key UNIQUE (chave_acesso)
                """
            }).execute()
            print("✅ Constraint de chave única aplicada")
        except Exception as e:
            if "already exists" in str(e):
                print("✅ Constraint de chave única já existe")
            else:
                print(f"⚠️  Erro ao aplicar constraint: {e}")
        
        # 5. Criar índices
        print("\n5. Criando índices...")
        
        indices = [
            ('idx_fiscal_documents_chave_acesso', 'chave_acesso'),
            ('idx_fiscal_documents_dh_evento', 'dh_evento'),
            ('idx_fiscal_documents_dh_emi', 'dh_emi')
        ]
        
        for index_name, column_name in indices:
            try:
                supabase.rpc('execute_sql', {
                    'query': f'CREATE INDEX IF NOT EXISTS {index_name} ON fiscal_documents({column_name})'
                }).execute()
                print(f"✅ Índice {index_name} criado")
            except Exception as e:
                print(f"⚠️  Erro ao criar índice {index_name}: {e}")
        
        # 6. Verificar estado final
        print("\n6. Verificando estado final...")
        
        final_count_result = supabase.table('fiscal_documents').select('id', count='exact').execute()
        final_count = final_count_result.count if hasattr(final_count_result, 'count') else len(final_count_result.data)
        
        unique_keys_result = supabase.table('fiscal_documents').select('chave_acesso').execute()
        unique_keys = set()
        for doc in unique_keys_result.data:
            if doc.get('chave_acesso'):
                unique_keys.add(doc['chave_acesso'])
        
        print(f"📊 Estado final:")
        print(f"   - Total de registros: {final_count}")
        print(f"   - Chaves únicas: {len(unique_keys)}")
        print(f"   - Duplicatas: {max(0, final_count - len(unique_keys))}")
        
        if final_count == len(unique_keys):
            print(f"\n✅ Schema de upsert aplicado com sucesso!")
            print(f"🎯 Sistema pronto para evitar duplicatas")
            return True
        else:
            print(f"\n⚠️  Ainda há duplicatas - pode ser necessário limpeza manual")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao aplicar schema: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = apply_upsert_schema()
    
    if success:
        print(f"\n✅ SCHEMA DE UPSERT APLICADO COM SUCESSO!")
        print(f"🎯 Agora o sistema evitará duplicatas automaticamente")
    else:
        print(f"\n❌ FALHA AO APLICAR SCHEMA DE UPSERT")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)