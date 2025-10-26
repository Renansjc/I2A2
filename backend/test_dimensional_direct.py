"""
Direct dimensional processing test - bypasses status system
"""

import asyncio
import sys
import os
from agents.dimensional_processing_agent import DimensionalProcessingAgent
import structlog

logger = structlog.get_logger()

async def test_dimensional_agent_direct():
    """Test dimensional agent directly"""
    print("🔄 Testing Dimensional Agent Directly")
    print("=" * 50)
    
    agent = DimensionalProcessingAgent()
    await agent.initialize()
    
    try:
        # Read a single XML file
        xml_file = "xml_nf/42054072257653110000170000000000000725050541353120.xml"
        
        if not os.path.exists(xml_file):
            xml_file = "../xml_nf/42054072257653110000170000000000000725050541353120.xml"
        
        if not os.path.exists(xml_file):
            print("❌ XML file not found")
            return False
        
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print(f"📄 Processing: {os.path.basename(xml_file)}")
        
        # Process document directly
        context = {
            'document_id': None,  # No document_id to avoid foreign key issues
            'document_type': 'NFSE'
        }
        
        result = await agent.process_fiscal_document(xml_content, context)
        
        print("✅ Processing completed successfully!")
        print(f"📊 Result summary:")
        
        summary = result.get('summary', {})
        print(f"   Emitente processed: {'✅' if summary.get('emitente_processed') else '❌'}")
        print(f"   Products count: {summary.get('produtos_count', 0)}")
        print(f"   Fact records: {summary.get('fact_records_count', 0)}")
        
        # Print detailed results
        if result.get('dimensional_data'):
            dim_data = result['dimensional_data']
            print(f"\n📋 Dimensional Data:")
            print(f"   Emitente ID: {dim_data.get('emitente_id', 'N/A')}")
            print(f"   Destinatário ID: {dim_data.get('destinatario_id', 'N/A')}")
            print(f"   Products: {len(dim_data.get('produtos', []))}")
            print(f"   Fact records: {len(dim_data.get('fact_records', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await agent.cleanup()

async def main():
    """Main test execution"""
    print("🧪 Direct Dimensional Agent Test")
    print("=" * 50)
    
    success = await test_dimensional_agent_direct()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("The dimensional processing agent is working correctly!")
    else:
        print("\n❌ Test failed")

if __name__ == "__main__":
    asyncio.run(main())