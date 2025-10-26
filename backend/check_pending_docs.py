#!/usr/bin/env python3
"""
Script to check pending documents and their agent statuses
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from utils.config import settings

async def check_pending_documents():
    try:
        print("Checking pending documents...")
        
        # List documents with pending status
        documents = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=10,
            status_filter='pending',
            admin_mode=True
        )
        
        print(f'Found {len(documents)} pending documents:')
        for doc in documents:
            print(f'- ID: {doc["id"]}, File: {doc["filename"]}, Status: {doc["processing_status"]}')
            
            # Check agent statuses
            agent_statuses = await ProcessingStatusManager.get_document_processing_status(
                doc['id'], admin_mode=True
            )
            print(f'  Agent statuses:')
            for status in agent_statuses:
                print(f'    - {status["agent_name"]}: {status["status"]}')
        
        return documents
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return []

async def check_processing_documents():
    try:
        print("\nChecking processing documents...")
        
        # List documents with processing status
        documents = await FileUploadManager.list_user_documents(
            user_id=None,
            skip=0,
            limit=10,
            status_filter='processing',
            admin_mode=True
        )
        
        print(f'Found {len(documents)} processing documents:')
        for doc in documents:
            print(f'- ID: {doc["id"]}, File: {doc["filename"]}, Status: {doc["processing_status"]}')
            
            # Check agent statuses
            agent_statuses = await ProcessingStatusManager.get_document_processing_status(
                doc['id'], admin_mode=True
            )
            print(f'  Agent statuses:')
            for status in agent_statuses:
                print(f'    - {status["agent_name"]}: {status["status"]}')
        
        return documents
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return []

async def main():
    print("=== Document Status Check ===")
    
    # Check pending documents
    pending_docs = await check_pending_documents()
    
    # Check processing documents
    processing_docs = await check_processing_documents()
    
    print(f"\nSummary:")
    print(f"- Pending documents: {len(pending_docs)}")
    print(f"- Processing documents: {len(processing_docs)}")

if __name__ == "__main__":
    asyncio.run(main())