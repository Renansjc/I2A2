#!/usr/bin/env python3

from utils.database import SupabaseClient
import asyncio

async def discover_main_tables_schema():
    """Discover the schema of nfe_main and nfse_main tables by testing common columns"""
    try:
        print("🔍 Discovering Main Tables Schema")
        print("=" * 50)
        
        service_client = SupabaseClient(use_service_key=True)
        
        # Common columns that might exist in main tables
        common_columns = [
            'chave_nfe', 'chave_nfse', 'id_nfse', 'numero_nfe', 'numero_nfse',
            'serie_nfe', 'data_emissao', 'valor_total', 'natureza_operacao',
            'emitente_cnpj', 'cnpj_emitente', 'prestador_cnpj', 'cnpj_prestador',
            'local_prestacao', 'created_at', 'updated_at'
        ]
        
        for table_name in ['nfe_main', 'nfse_main']:
            print(f"\n📊 Testing columns for: {table_name}")
            print("-" * 30)
            
            valid_columns = []
            
            for column in common_columns:
                try:
                    # Try to select just this column
                    result = service_client.client.table(table_name).select(column).limit(0).execute()
                    valid_columns.append(column)
                    print(f"   ✅ {column}")
                except Exception as e:
                    if 'Could not find' in str(e) and 'column' in str(e):
                        print(f"   ❌ {column}")
                    else:
                        print(f"   ⚠️  {column}: {str(e)}")
            
            print(f"\n   📋 Valid columns for {table_name}: {valid_columns}")
            
            # Try to get the actual schema by attempting an insert with all valid columns
            if valid_columns:
                print(f"\n   🧪 Testing insert with valid columns...")
                test_data = {}
                for col in valid_columns:
                    if col in ['chave_nfe', 'chave_nfse', 'id_nfse', 'numero_nfe', 'numero_nfse']:
                        test_data[col] = 'TEST123'
                    elif col in ['serie_nfe']:
                        test_data[col] = '1'
                    elif col in ['data_emissao']:
                        test_data[col] = '2025-10-26T12:00:00Z'
                    elif col in ['valor_total']:
                        test_data[col] = 100.0
                    elif col in ['natureza_operacao', 'local_prestacao']:
                        test_data[col] = 'TESTE'
                    elif col in ['emitente_cnpj', 'cnpj_emitente', 'prestador_cnpj', 'cnpj_prestador']:
                        test_data[col] = '12345678901234'
                    elif col in ['created_at', 'updated_at']:
                        test_data[col] = '2025-10-26T12:00:00Z'
                
                try:
                    service_client.client.table(table_name).insert(test_data).execute()
                    print(f"   ✅ Insert successful with: {list(test_data.keys())}")
                    
                    # Clean up the test record
                    try:
                        if 'chave_nfe' in test_data:
                            service_client.client.table(table_name).delete().eq('chave_nfe', 'TEST123').execute()
                        elif 'id_nfse' in test_data:
                            service_client.client.table(table_name).delete().eq('id_nfse', 'TEST123').execute()
                        elif 'chave_nfse' in test_data:
                            service_client.client.table(table_name).delete().eq('chave_nfse', 'TEST123').execute()
                    except:
                        pass  # Ignore cleanup errors
                        
                except Exception as insert_error:
                    error_msg = str(insert_error)
                    print(f"   📋 Insert error (reveals required columns): {error_msg}")
        
    except Exception as e:
        print(f"❌ Error discovering schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(discover_main_tables_schema())