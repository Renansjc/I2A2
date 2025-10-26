"""
Check processing_results table schema
"""

import asyncio
import sys
import os
from utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def check_processing_results_schema():
    """Check processing_results table schema"""
    print("🔍 Checking processing_results Table Schema")
    print("=" * 50)
    
    supabase_client = get_supabase_client(admin_mode=True)
    
    # Get existing records to see structure
    print("\n📊 Existing processing_results records")
    print("-" * 50)
    
    try:
        result = supabase_client.client.table('processing_results').select('*').limit(5).execute()
        
        if result.data:
            print(f"Found {len(result.data)} records")
            for i, record in enumerate(result.data):
                print(f"\nRecord {i+1}:")
                for key, value in record.items():
                    print(f"  {key}: {value}")
        else:
            print("No records found")
            
    except Exception as e:
        print(f"Could not get records: {e}")
    
    # Try to insert with correct structure based on error message
    print("\n📊 Testing insert with minimal data")
    print("-" * 50)
    
    try:
        test_data = {
            'document_id': '00000000-0000-0000-0000-000000000000',
            'agent_name': 'dimensional_processing_agent',
            'result_data': {'test': True}
        }
        
        result = supabase_client.client.table('processing_results').insert(test_data).execute()
        print("✅ Test insert successful")
        
        # Clean up test record
        supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
        
    except Exception as e:
        print(f"❌ Test insert failed: {e}")
        
        # Try with different agent name
        print("\n📊 Testing with xml_processing_agent")
        print("-" * 30)
        
        try:
            test_data = {
                'document_id': '00000000-0000-0000-0000-000000000000',
                'agent_name': 'xml_processing_agent',
                'result_data': {'test': True}
            }
            
            result = supabase_client.client.table('processing_results').insert(test_data).execute()
            print("✅ xml_processing_agent insert successful")
            
            # Clean up test record
            supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
            
        except Exception as e2:
            print(f"❌ xml_processing_agent insert also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(check_processing_results_schema())