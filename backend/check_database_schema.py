#!/usr/bin/env python3

from utils.database import SupabaseClient
import asyncio

async def check_database_schema():
    """Check the actual schema of nfe_main and nfse_main tables"""
    try:
        print("🔍 Checking Database Schema")
        print("=" * 50)
        
        # Use service client to bypass RLS
        service_client = SupabaseClient(use_service_key=True)
        
        # Check if tables exist and get their structure
        tables_to_check = ['nfe_main', 'nfse_main', 'fact_itens_nfe', 'fact_servicos_nfse']
        
        for table_name in tables_to_check:
            print(f"\n📊 Checking table: {table_name}")
            print("-" * 30)
            
            try:
                # Try to get table info by attempting a select with limit 0
                result = service_client.client.table(table_name).select('*').limit(0).execute()
                print(f"   ✅ Table '{table_name}' exists")
                
                # Try to insert a test record to see what columns are expected
                # This will fail but give us column information
                try:
                    test_data = {'test_column': 'test_value'}
                    service_client.client.table(table_name).insert(test_data).execute()
                except Exception as insert_error:
                    error_msg = str(insert_error)
                    if 'Could not find' in error_msg and 'column' in error_msg:
                        print(f"   📋 Column info from error: {error_msg}")
                    elif 'violates not-null constraint' in error_msg:
                        print(f"   📋 Required columns info: {error_msg}")
                    else:
                        print(f"   📋 Schema info: {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                if 'does not exist' in error_msg or 'relation' in error_msg:
                    print(f"   ❌ Table '{table_name}' does not exist")
                else:
                    print(f"   ⚠️  Error checking table: {error_msg}")
        
        # Check existing data in tables that exist
        print(f"\n📊 Checking existing data:")
        print("-" * 30)
        
        # Check dimensional tables (corrected names)
        for table_name in ['dim_emitente', 'dim_produtos', 'dim_destinatario']:
            try:
                result = service_client.client.table(table_name).select('*').limit(1).execute()
                if result.data:
                    print(f"   📄 {table_name}: {len(result.data)} sample records")
                    sample = result.data[0]
                    columns = list(sample.keys())
                    print(f"      Columns: {', '.join(columns)}")
                else:
                    print(f"   📄 {table_name}: No data, but table exists")
            except Exception as e:
                print(f"   ❌ {table_name}: {str(e)}")
        
        # Check main tables with sample data
        for table_name in ['nfe_main', 'nfse_main']:
            try:
                result = service_client.client.table(table_name).select('*').limit(1).execute()
                if result.data:
                    print(f"   📄 {table_name}: {len(result.data)} sample records")
                    sample = result.data[0]
                    columns = list(sample.keys())
                    print(f"      Columns: {', '.join(columns)}")
                else:
                    print(f"   📄 {table_name}: No data, checking with minimal insert...")
                    # Try minimal insert to discover required columns
                    try:
                        minimal_data = {'id': 'test123'}
                        service_client.client.table(table_name).insert(minimal_data).execute()
                    except Exception as insert_error:
                        error_msg = str(insert_error)
                        print(f"      Schema hints: {error_msg}")
            except Exception as e:
                print(f"   ❌ {table_name}: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_database_schema())