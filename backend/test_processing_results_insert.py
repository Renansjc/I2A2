"""
Test processing_results insert with correct fields
"""

import asyncio
import sys
import os
from utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def test_processing_results_insert():
    """Test processing_results insert"""
    print("🔍 Testing processing_results Insert")
    print("=" * 50)
    
    supabase_client = get_supabase_client(admin_mode=True)
    
    # Test with result_type field
    print("\n📊 Testing with result_type field")
    print("-" * 50)
    
    try:
        test_data = {
            'document_id': '00000000-0000-0000-0000-000000000000',
            'agent_name': 'dimensional_processing_agent',
            'result_type': 'dimensional_processing',
            'result_data': {'test': True}
        }
        
        result = supabase_client.client.table('processing_results').insert(test_data).execute()
        print("✅ dimensional_processing_agent insert successful!")
        
        # Clean up test record
        supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
        print("✅ Test record cleaned up")
        
    except Exception as e:
        print(f"❌ dimensional_processing_agent insert failed: {e}")
        
        # Check if it's the agent name constraint
        error_str = str(e)
        if 'processing_results_agent_name_check' in error_str:
            print("\n🔍 AGENT NAME CONSTRAINT ISSUE DETECTED!")
            print("The constraint only allows specific agent names.")
            print("Let's test with known working agent names...")
            
            # Test with xml_processing_agent
            print("\n📊 Testing with xml_processing_agent")
            print("-" * 30)
            
            try:
                test_data = {
                    'document_id': '00000000-0000-0000-0000-000000000000',
                    'agent_name': 'xml_processing_agent',
                    'result_type': 'xml_processing',
                    'result_data': {'test': True}
                }
                
                result = supabase_client.client.table('processing_results').insert(test_data).execute()
                print("✅ xml_processing_agent insert successful!")
                
                # Clean up test record
                supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
                
            except Exception as e2:
                print(f"❌ xml_processing_agent insert also failed: {e2}")
            
            # Test with ai_categorization_agent
            print("\n📊 Testing with ai_categorization_agent")
            print("-" * 30)
            
            try:
                test_data = {
                    'document_id': '00000000-0000-0000-0000-000000000000',
                    'agent_name': 'ai_categorization_agent',
                    'result_type': 'categorization',
                    'result_data': {'test': True}
                }
                
                result = supabase_client.client.table('processing_results').insert(test_data).execute()
                print("✅ ai_categorization_agent insert successful!")
                
                # Clean up test record
                supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
                
            except Exception as e3:
                print(f"❌ ai_categorization_agent insert also failed: {e3}")

if __name__ == "__main__":
    asyncio.run(test_processing_results_insert())