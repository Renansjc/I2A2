"""
Check database constraints that are failing
"""

import asyncio
import sys
import os
from utils.database import get_supabase_client
import structlog

logger = structlog.get_logger()

async def check_constraints():
    """Check database constraints"""
    print("🔍 Checking Database Constraints")
    print("=" * 50)
    
    supabase_client = get_supabase_client(admin_mode=True)
    
    # Check processing_results constraint
    print("\n📊 Checking processing_results_agent_name_check constraint")
    print("-" * 50)
    
    try:
        # Try to get constraint information
        result = supabase_client.client.rpc('get_table_constraints', {
            'table_name': 'processing_results'
        }).execute()
        
        print(f"Constraint info: {result.data}")
        
    except Exception as e:
        print(f"Could not get constraint info: {e}")
    
    # Check what agent names are currently in processing_results
    print("\n📊 Current agent names in processing_results")
    print("-" * 50)
    
    try:
        result = supabase_client.client.table('processing_results').select('agent_name').execute()
        agent_names = set(row['agent_name'] for row in result.data)
        print(f"Current agent names: {agent_names}")
        
    except Exception as e:
        print(f"Could not get agent names: {e}")
    
    # Check document_processing_status constraint
    print("\n📊 Checking check_agent_processing_times constraint")
    print("-" * 50)
    
    try:
        result = supabase_client.client.table('document_processing_status').select('agent_name').execute()
        agent_names = set(row['agent_name'] for row in result.data)
        print(f"Current agent names in document_processing_status: {agent_names}")
        
    except Exception as e:
        print(f"Could not get agent names from document_processing_status: {e}")
    
    # Try to insert a test record to see the exact constraint
    print("\n📊 Testing constraint with dimensional_processing_agent")
    print("-" * 50)
    
    try:
        test_data = {
            'document_id': '00000000-0000-0000-0000-000000000000',
            'agent_name': 'dimensional_processing_agent',
            'operation_type': 'test',
            'result_data': {'test': True},
            'confidence_score': 0.5,
            'processing_time_ms': 1000
        }
        
        result = supabase_client.client.table('processing_results').insert(test_data).execute()
        print("✅ Test insert successful")
        
        # Clean up test record
        supabase_client.client.table('processing_results').delete().eq('document_id', '00000000-0000-0000-0000-000000000000').execute()
        
    except Exception as e:
        print(f"❌ Test insert failed: {e}")
        
        # Extract constraint details
        error_str = str(e)
        if 'processing_results_agent_name_check' in error_str:
            print("🔍 This is the agent name constraint issue")
            print("The constraint likely only allows specific agent names")

if __name__ == "__main__":
    asyncio.run(check_constraints())