#!/usr/bin/env python3
"""
Auto-process any documents with pending agents
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from api.routes import _processar_xml_background
import structlog

logger = structlog.get_logger()

async def auto_process_pending():
    try:
        print("=== Auto Processing Documents with Pending Agents ===")
        
        # Get all processing documents
        processing_docs = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=50,
            status_filter='processing',
            admin_mode=True
        )
        
        print(f"Found {len(processing_docs)} processing documents")
        
        processed_count = 0
        
        for doc in processing_docs:
            document_id = doc['id']
            filename = doc['filename']
            xml_content = doc['xml_content']
            document_type = doc['document_type']
            
            # Check agent statuses
            agent_statuses = await ProcessingStatusManager.get_document_processing_status(
                document_id, admin_mode=True
            )
            
            pending_agents = [status for status in agent_statuses if status['status'] == 'pending']
            
            if pending_agents:
                print(f"\n🔄 Processing: {filename}")
                print(f"   Pending agents: {[agent['agent_name'] for agent in pending_agents]}")
                
                try:
                    await _processar_xml_background(
                        document_id,
                        xml_content,
                        filename,
                        document_type
                    )
                    print(f"   ✅ Successfully processed: {filename}")
                    processed_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to process {filename}: {e}")
            else:
                print(f"✅ Already processed: {filename}")
        
        print(f"\n=== Auto Processing Completed ===")
        print(f"Documents processed: {processed_count}")
        
    except Exception as e:
        print(f"Auto processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(auto_process_pending())