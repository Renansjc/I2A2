#!/usr/bin/env python3
"""
Script to fix documents with failed agents
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from api.routes import _processar_xml_background
import structlog

logger = structlog.get_logger()

async def fix_failed_agents():
    try:
        print("=== Fixing Documents with Failed Agents ===")
        
        # Get all processing documents
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
            
            failed_agents = [status for status in agent_statuses if status['status'] == 'failed']
            completed_agents = [status for status in agent_statuses if status['status'] == 'completed']
            
            if failed_agents:
                print(f"\n🔧 Fixing document: {filename} (ID: {document_id})")
                print(f"   Failed agents: {[agent['agent_name'] for agent in failed_agents]}")
                print(f"   Completed agents: {[agent['agent_name'] for agent in completed_agents]}")
                
                # Reset failed agents to pending
                for failed_agent in failed_agents:
                    await ProcessingStatusManager.update_agent_status(
                        document_id, failed_agent['agent_name'], "pending", admin_mode=True
                    )
                
                # Start background processing
                try:
                    await _processar_xml_background(
                        document_id,
                        xml_content,
                        filename,
                        document_type
                    )
                    print(f"   ✅ Successfully reprocessed: {filename}")
                except Exception as e:
                    print(f"   ❌ Failed to reprocess {filename}: {e}")
            else:
                print(f"✅ Document OK: {filename} - All agents completed")
        
        print(f"\n=== Failed agent fixing completed ===")
        
        # Final status check
        print("\n=== Final Status Check ===")
        processing_docs = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=50,
            status_filter='processing',
            admin_mode=True
        )
        
        total_completed = 0
        total_failed = 0
        
        for doc in processing_docs:
            document_id = doc['id']
            filename = doc['filename']
            
            agent_statuses = await ProcessingStatusManager.get_document_processing_status(
                document_id, admin_mode=True
            )
            
            failed_count = len([s for s in agent_statuses if s['status'] == 'failed'])
            completed_count = len([s for s in agent_statuses if s['status'] == 'completed'])
            
            if failed_count == 0 and completed_count == 4:
                total_completed += 1
                print(f"✅ {filename}: All 4 agents completed")
            else:
                total_failed += 1
                print(f"❌ {filename}: {completed_count}/4 completed, {failed_count} failed")
        
        print(f"\nSummary:")
        print(f"✅ Documents fully processed: {total_completed}")
        print(f"❌ Documents with issues: {total_failed}")
        
    except Exception as e:
        print(f"Error during fixing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_failed_agents())