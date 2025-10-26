#!/usr/bin/env python3
"""
Test complete agent processing pipeline
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from api.routes import _processar_xml_background
import structlog

logger = structlog.get_logger()

async def test_complete_processing():
    try:
        print("=== Testing Complete Agent Processing Pipeline ===")
        
        # Get a processing document
        documents = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=1,
            status_filter='processing',
            admin_mode=True
        )
        
        if not documents:
            print("No processing documents found")
            return
        
        document = documents[0]
        document_id = document['id']
        filename = document['filename']
        xml_content = document['xml_content']
        document_type = document['document_type']
        
        print(f"Testing complete processing with: {filename} (ID: {document_id})")
        
        # Reset agent statuses to pending
        agent_names = [
            "xml_processing_agent",
            "ai_categorization_agent",
            "sql_agent",
            "report_agent"
        ]
        
        for agent_name in agent_names:
            await ProcessingStatusManager.update_agent_status(
                document_id, agent_name, "pending", admin_mode=True
            )
        
        print("Reset all agent statuses to pending")
        
        # Run complete background processing
        print("Starting complete background processing...")
        await _processar_xml_background(
            document_id,
            xml_content,
            filename,
            document_type
        )
        
        print("Background processing completed!")
        
        # Check final status
        agent_statuses = await ProcessingStatusManager.get_document_processing_status(
            document_id, admin_mode=True
        )
        
        print("\nFinal Agent Statuses:")
        for status in agent_statuses:
            status_icon = "✅" if status['status'] == 'completed' else "❌" if status['status'] == 'failed' else "⏳"
            print(f"{status_icon} {status['agent_name']}: {status['status']}")
            if status['status'] == 'failed' and status.get('error_message'):
                print(f"   Error: {status['error_message'][:100]}...")
        
        # Get processing results
        results = await ProcessingStatusManager.get_processing_results(document_id, admin_mode=True)
        print(f"\nProcessing Results: {len(results)} results stored")
        
        for result in results:
            print(f"- {result['agent_name']}: {result['result_type']} (confidence: {result.get('confidence_score', 'N/A')})")
        
        print("\n=== Complete Processing Test Finished ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_processing())