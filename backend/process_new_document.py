#!/usr/bin/env python3
"""
Process the new document that was uploaded
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from api.routes import _processar_xml_background
import structlog

logger = structlog.get_logger()

async def process_new_document():
    try:
        print("=== Processing New Document ===")
        
        # Get the specific new document
        document_id = "2269d78d-7a35-44d8-a77c-e04cde4ceea1"
        
        # Get document details
        document = await FileUploadManager.get_document_by_id(document_id, admin_mode=True)
        
        if not document:
            print(f"Document {document_id} not found")
            return
        
        filename = document['filename']
        xml_content = document['xml_content']
        document_type = document['document_type']
        
        print(f"Processing document: {filename}")
        print(f"Document type: {document_type}")
        print(f"XML content length: {len(xml_content)} characters")
        
        # Check current agent statuses
        agent_statuses = await ProcessingStatusManager.get_document_processing_status(
            document_id, admin_mode=True
        )
        
        print("Current agent statuses:")
        for status in agent_statuses:
            print(f"  - {status['agent_name']}: {status['status']}")
        
        # Start background processing
        print("\nStarting background processing...")
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
        
        print("\nFinal agent statuses:")
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
        
        print("\n=== New Document Processing Completed ===")
        
    except Exception as e:
        print(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(process_new_document())