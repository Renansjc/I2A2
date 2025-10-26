#!/usr/bin/env python3

from utils.database import SupabaseClient
import asyncio

async def test_suggested_columns():
    """Test the columns suggested by error messages"""
    try:
        print("🔍 Testing Suggested Columns")
        print("=" * 40)
        
        service_client = SupabaseClient(use_service_key=True)
        
        # Test suggested columns for nfe_main
        nfe_suggested = ['numero_nf', 'valor_total_nf', 'serie_nf']
        
        print(f"\n📊 Testing NFE suggested columns:")
        nfe_valid = []
        for column in nfe_suggested:
            try:
                service_client.client.table('nfe_main').select(column).limit(0).execute()
                nfe_valid.append(column)
                print(f"   ✅ {column}")
            except Exception as e:
                print(f"   ❌ {column}: {str(e)}")
        
        # Test complete NFE schema
        print(f"\n🧪 Testing complete NFE schema:")
        nfe_complete = ['chave_nfe', 'numero_nf', 'serie_nf', 'data_emissao', 'valor_total_nf', 'natureza_operacao', 'created_at', 'updated_at']
        
        nfe_test_data = {
            'chave_nfe': 'TEST_NFE_123',
            'numero_nf': '123',
            'serie': '1',  # Corrected column name
            'data_emissao': '2025-10-26T12:00:00Z',
            'valor_total_nf': 100.50,
            'natureza_operacao': 'VENDA',
            'created_at': '2025-10-26T12:00:00Z',
            'updated_at': '2025-10-26T12:00:00Z'
        }
        
        try:
            service_client.client.table('nfe_main').insert(nfe_test_data).execute()
            print(f"   ✅ NFE insert successful!")
            # Cleanup
            service_client.client.table('nfe_main').delete().eq('chave_nfe', 'TEST_NFE_123').execute()
        except Exception as e:
            print(f"   📋 NFE insert error: {str(e)}")
        
        # Test complete NFSE schema with additional columns
        print(f"\n🧪 Testing complete NFSE schema:")
        nfse_additional = ['valor_servicos', 'valor_total_nfse', 'prestador_cnpj']
        
        print(f"\n📊 Testing NFSE additional columns:")
        nfse_valid = []
        for column in nfse_additional:
            try:
                service_client.client.table('nfse_main').select(column).limit(0).execute()
                nfse_valid.append(column)
                print(f"   ✅ {column}")
            except Exception as e:
                print(f"   ❌ {column}: {str(e)}")
        
        nfse_test_data = {
            'id_nfse': 'TEST_NFSE_123',
            'numero_nfse': '7',
            'data_emissao': '2025-10-26T12:00:00Z',
            'local_prestacao': 'Florianópolis',
            'created_at': '2025-10-26T12:00:00Z',
            'updated_at': '2025-10-26T12:00:00Z'
        }
        
        # Add valid additional columns
        for col in nfse_valid:
            if col == 'valor_servicos' or col == 'valor_total_nfse':
                nfse_test_data[col] = 7000.00
            elif col == 'prestador_cnpj':
                nfse_test_data[col] = '57653110000170'
        
        try:
            service_client.client.table('nfse_main').insert(nfse_test_data).execute()
            print(f"   ✅ NFSE insert successful!")
            # Cleanup
            service_client.client.table('nfse_main').delete().eq('id_nfse', 'TEST_NFSE_123').execute()
        except Exception as e:
            print(f"   📋 NFSE insert error: {str(e)}")
        
        print(f"\n📋 Final Schema Summary:")
        print(f"   NFE Main: {nfe_complete}")
        print(f"   NFSE Main: {list(nfse_test_data.keys())}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_suggested_columns())