#!/usr/bin/env python3
"""
Test database connection and check available tables
"""

import asyncio
from utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def test_database_connection():
    """Test database connection and list available tables"""
    try:
        # Get admin client for testing
        supabase_client = get_supabase_client(admin_mode=True)
        client = supabase_client.client
        
        print("Testing Supabase connection...")
        
        # Test basic connection
        try:
            result = client.table('fiscal_documents').select('id').limit(1).execute()
            print(f"✅ Connection successful! Found {len(result.data)} records in fiscal_documents")
        except Exception as e:
            print(f"❌ fiscal_documents table error: {e}")
        
        # Check dimensional tables
        dimensional_tables = [
            'dim_emitente',
            'dim_destinatario', 
            'dim_produtos',
            'dim_servicos',
            'fact_itens_nfe',
            'fact_servicos_nfse',
            'nfe_main',
            'nfse_main'
        ]
        
        print("\nChecking dimensional tables:")
        for table in dimensional_tables:
            try:
                result = client.table(table).select('*').limit(1).execute()
                print(f"✅ {table}: {len(result.data)} records found")
                if result.data:
                    print(f"   Sample columns: {list(result.data[0].keys())}")
            except Exception as e:
                print(f"❌ {table}: {e}")
        
        # Check if we have any processed data
        print("\nChecking for processed data:")
        try:
            # Check for NF-e data
            nfe_result = client.table('nfe_main').select('chave_nfe, data_emissao').limit(5).execute()
            print(f"✅ NF-e records: {len(nfe_result.data)}")
            for record in nfe_result.data:
                print(f"   - {record.get('chave_nfe', 'N/A')} ({record.get('data_emissao', 'N/A')})")
        except Exception as e:
            print(f"❌ NF-e data check failed: {e}")
        
        try:
            # Check for dimensional data
            emitente_result = client.table('dim_emitente').select('cnpj, razao_social').limit(5).execute()
            print(f"✅ Emitente records: {len(emitente_result.data)}")
            for record in emitente_result.data:
                print(f"   - {record.get('cnpj', 'N/A')}: {record.get('razao_social', 'N/A')}")
        except Exception as e:
            print(f"❌ Emitente data check failed: {e}")
            
        try:
            # Check for product data
            produto_result = client.table('dim_produtos').select('codigo_produto, descricao').limit(5).execute()
            print(f"✅ Produto records: {len(produto_result.data)}")
            for record in produto_result.data:
                print(f"   - {record.get('codigo_produto', 'N/A')}: {record.get('descricao', 'N/A')}")
        except Exception as e:
            print(f"❌ Produto data check failed: {e}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_database_connection())