#!/usr/bin/env python3
"""
Script para verificar se as tabelas dimensionais foram populadas
"""

import asyncio
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

async def check_tables():
    """Verifica o conteúdo das tabelas dimensionais"""
    try:
        from utils.database import SupabaseClient
        
        print("🔍 Verificando tabelas dimensionais...")
        print("=" * 50)
        
        from supabase import create_client
        from utils.config import settings
        
        # Create admin client
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Check dim_emitente
        print("\n📊 Tabela: dim_emitente")
        try:
            result = supabase.table("dim_emitente").select("cnpj, razao_social, nome_fantasia, uf").limit(10).execute()
            if result.data:
                print(f"   ✅ {len(result.data)} registros encontrados:")
                for row in result.data:
                    print(f"      • {row.get('razao_social', 'N/A')} (CNPJ: {row.get('cnpj', 'N/A')}) - {row.get('uf', 'N/A')}")
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        # Check dim_destinatario
        print("\n📊 Tabela: dim_destinatario")
        try:
            result = supabase.table("dim_destinatario").select("id, cnpj, cpf, razao_social, uf").limit(10).execute()
            if result.data:
                print(f"   ✅ {len(result.data)} registros encontrados:")
                for row in result.data:
                    doc_id = row.get('cnpj') or row.get('cpf', 'N/A')
                    print(f"      • {row.get('razao_social', 'N/A')} (Doc: {doc_id}) - {row.get('uf', 'N/A')}")
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        # Check dim_produtos
        print("\n📊 Tabela: dim_produtos")
        try:
            result = supabase.table("dim_produtos").select("codigo_produto, descricao, categoria, subcategoria, ncm").limit(10).execute()
            if result.data:
                print(f"   ✅ {len(result.data)} registros encontrados:")
                for row in result.data:
                    print(f"      • {row.get('descricao', 'N/A')[:50]}... ({row.get('categoria', 'N/A')})")
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        # Check nfe_main
        print("\n📊 Tabela: nfe_main")
        try:
            result = supabase.table("nfe_main").select("chave_nfe, numero_nf, natureza_operacao, valor_total_nf").limit(10).execute()
            if result.data:
                print(f"   ✅ {len(result.data)} registros encontrados:")
                for row in result.data:
                    valor = row.get('valor_total_nf', 0)
                    print(f"      • NF {row.get('numero_nf', 'N/A')} - {row.get('natureza_operacao', 'N/A')[:30]}... (R$ {valor:.2f})")
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        # Check fact_itens_nfe
        print("\n📊 Tabela: fact_itens_nfe")
        try:
            result = supabase.table("fact_itens_nfe").select("chave_nfe, numero_item, descricao, valor_total_bruto").limit(10).execute()
            if result.data:
                print(f"   ✅ {len(result.data)} registros encontrados:")
                for row in result.data:
                    valor = row.get('valor_total_bruto', 0)
                    print(f"      • Item {row.get('numero_item', 'N/A')}: {row.get('descricao', 'N/A')[:40]}... (R$ {valor:.2f})")
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ Verificação concluída!")
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_tables())