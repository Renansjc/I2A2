"""
Clean dimensional processing test - clears database first
"""

import asyncio
import sys
import os
from utils.database import get_supabase_client
import structlog
from agents.dimensional_coordinator import DimensionalCoordinator

logger = structlog.get_logger()

async def clean_database():
    """Clean database tables for fresh test"""
    print("🧹 Cleaning Database for Fresh Test")
    print("=" * 50)
    
    supabase_client = get_supabase_client(admin_mode=True)
    
    # Tables to clean (in order to respect foreign keys)
    tables_to_clean = [
        'fact_itens_nfe',
        'fact_servicos_nfse', 
        'nfe_main',
        'nfse_main',
        'processing_results',
        'document_processing_status',
        'fiscal_documents',
        'dim_produtos',
        'dim_destinatario',
        'dim_emitente'
    ]
    
    for table in tables_to_clean:
        try:
            result = supabase_client.client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Cleaned {table}")
        except Exception as e:
            print(f"   ⚠️  Could not clean {table}: {e}")

async def test_single_document():
    """Test processing a single document"""
    print("\n🔄 Testing Single Document Processing")
    print("=" * 50)
    
    coordinator = DimensionalCoordinator()
    await coordinator.initialize()
    
    try:
        # Read a single XML file
        xml_file = "xml_nf/42054072257653110000170000000000000725050541353120.xml"
        
        if not os.path.exists(xml_file):
            xml_file = "../xml_nf/42054072257653110000170000000000000725050541353120.xml"
        
        if not os.path.exists(xml_file):
            print("❌ XML file not found")
            return
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print(f"📄 Processing: {os.path.basename(xml_file)}")
        
        # Process document
        import uuid
        test_document_id = str(uuid.uuid4())
        
        result = await coordinator.process_document_pipeline(
            xml_content,
            test_document_id,
            "NFSE"  # This file is NFSE
        )
        
        print("✅ Processing completed successfully!")
        print(f"📊 Result summary:")
        
        summary = result.get('summary', {})
        print(f"   Emitente processed: {'✅' if summary.get('emitente_processed') else '❌'}")
        print(f"   Products count: {summary.get('produtos_count', 0)}")
        print(f"   Fact records: {summary.get('fact_records_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False
        
    finally:
        await coordinator.cleanup()

async def main():
    """Main test execution"""
    print("🧪 Clean Dimensional Processing Test")
    print("=" * 50)
    
    # Clean database first
    await clean_database()
    
    # Test single document
    success = await test_single_document()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("The dimensional processing agent is working correctly!")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())