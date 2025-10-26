#!/usr/bin/env python3
"""
Script to reprocess pending documents by triggering background processing
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from api.routes import _processar_xml_background
import structlog

logger = structlog.get_logger()

async def reprocess_pending_documents():
    try:
        print("=== Reprocessing Pending Documents ===")
        
        # Get all pending documents
        pending_docs = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=50,
            status_filter='pending',
            admin_mode=True
        )
        
        print(f"Found {len(pending_docs)} pending documents")
        
        for doc in pending_docs:
            document_id = doc['id']
            filename = doc['filename']
            xml_content = doc['xml_content']
            document_type = doc['document_type']
            
            print(f"\nReprocessing: {filename} (ID: {document_id})")
            
            # Update status to processing
            await FileUploadManager.update_processing_status(
                document_id, "processing", admin_mode=True
            )
            
            # Initialize agent statuses
            agent_names = [
                "xml_processing_agent",
                "ai_categorization_agent", 
                "sql_agent",
                "report_agent"
            ]
            await ProcessingStatusManager.initialize_agent_statuses(
                document_id, agent_names, admin_mode=True
            )
            
            # Start background processing
            try:
                await _processar_xml_background(
                    document_id,
                    xml_content,
                    filename,
                    document_type
                )
                print(f"✅ Successfully processed: {filename}")
            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")
                await FileUploadManager.update_processing_status(
                    document_id, "error", str(e), admin_mode=True
                )
        
        print(f"\n=== Reprocessing completed ===")
        
    except Exception as e:
        print(f"Error during reprocessing: {e}")
        import traceback
        traceback.print_exc()

async def reprocess_stuck_processing_documents():
    try:
        print("\n=== Reprocessing Stuck Processing Documents ===")
        
        # Get all processing documents with pending agents
        processing_docs = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=50,
            status_filter='processing',
            admin_mode=True
        )
        
        print(f"Found {len(processing_docs)} processing documents")
        
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
                print(f"\nReprocessing stuck document: {filename} (ID: {document_id})")
                print(f"Pending agents: {[agent['agent_name'] for agent in pending_agents]}")
                
                # Start background processing
                try:
                    await _processar_xml_background(
                        document_id,
                        xml_content,
                        filename,
                        document_type
                    )
                    print(f"✅ Successfully reprocessed: {filename}")
                except Exception as e:
                    print(f"❌ Failed to reprocess {filename}: {e}")
                    await FileUploadManager.update_processing_status(
                        document_id, "error", str(e), admin_mode=True
                    )
        
        print(f"\n=== Stuck document reprocessing completed ===")
        
    except Exception as e:
        print(f"Error during stuck document reprocessing: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("Starting document reprocessing...")
    
    # Reprocess pending documents
    await reprocess_pending_documents()
    
    # Reprocess stuck processing documents
    await reprocess_stuck_processing_documents()
    
    print("\nAll reprocessing completed!")

if __name__ == "__main__":
    asyncio.run(main())