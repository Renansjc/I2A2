"""
Script para testar se há dados reais no banco de dados
"""

import asyncio
from utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def test_real_data():
    """Testar se há dados reais nas tabelas"""
    try:
        supabase_client = get_supabase_client(admin_mode=True)
        
        print("🔍 Testando dados reais no banco...")
        
        # Test fiscal_documents table
        print("\n📄 Testando tabela fiscal_documents:")
        try:
            docs_result = supabase_client.table('fiscal_documents').select('id').execute()
            docs_count = len(docs_result.data) if docs_result.data else 0
            print(f"   Total de documentos fiscais: {docs_count}")
        except Exception as e:
            print(f"   ❌ Erro ao consultar fiscal_documents: {e}")
        
        # Test nfe_main table
        print("\n📋 Testando tabela nfe_main:")
        try:
            nfe_result = supabase_client.table('nfe_main').select('chave_nfe').execute()
            nfe_count = len(nfe_result.data) if nfe_result.data else 0
            print(f"   Total de NFe processadas: {nfe_count}")
        except Exception as e:
            print(f"   ❌ Erro ao consultar nfe_main: {e}")
        
        # Test fact_itens_nfe table
        print("\n🛍️ Testando tabela fact_itens_nfe:")
        try:
            items_result = supabase_client.table('fact_itens_nfe').select('id, valor_total_bruto').execute()
            items_count = len(items_result.data) if items_result.data else 0
            total_value = sum(float(item.get('valor_total_bruto', 0)) for item in items_result.data) if items_result.data else 0
            print(f"   Total de itens: {items_count}")
            print(f"   Valor total: R$ {total_value:,.2f}")
        except Exception as e:
            print(f"   ❌ Erro ao consultar fact_itens_nfe: {e}")
        
        # Test dim_emitente table
        print("\n🏢 Testando tabela dim_emitente:")
        try:
            emitente_result = supabase_client.table('dim_emitente').select('cnpj').execute()
            emitente_count = len(emitente_result.data) if emitente_result.data else 0
            print(f"   Total de emitentes: {emitente_count}")
        except Exception as e:
            print(f"   ❌ Erro ao consultar dim_emitente: {e}")
        
        # Test dim_produtos table
        print("\n📦 Testando tabela dim_produtos:")
        try:
            produtos_result = supabase_client.table('dim_produtos').select('codigo_produto').execute()
            produtos_count = len(produtos_result.data) if produtos_result.data else 0
            print(f"   Total de produtos: {produtos_count}")
        except Exception as e:
            print(f"   ❌ Erro ao consultar dim_produtos: {e}")
        
        # Summary
        print("\n📊 RESUMO:")
        print("   ⚠️  VERIFICAÇÃO CONCLUÍDA")
        print("   📝 Se não há dados reais, é necessário processar alguns documentos XML primeiro")
        print("   💡 Use o endpoint /upload para enviar arquivos XML")
        print("   🔄 Ou use dados de exemplo para testar as APIs")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar dados reais: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_real_data())