#!/usr/bin/env python3
"""
Test script to manually trigger agent processing for a pending document
"""

import asyncio
from utils.database import FileUploadManager, ProcessingStatusManager
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent
from agents.ai_categorization_agent import LLMEnhancedAICategorizationAgent
import structlog

logger = structlog.get_logger()

async def test_agent_processing():
    try:
        print("=== Testing Agent Processing ===")
        
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
        
        print(f"Testing with document: {filename} (ID: {document_id})")
        
        # Get XML content from document record
        document_details = await FileUploadManager.get_document_by_id(document_id, admin_mode=True)
        if not document_details or not document_details.get('xml_content'):
            print("Could not retrieve XML content")
            return
        
        xml_content = document_details['xml_content']
        
        print(f"XML content length: {len(xml_content)} characters")
        
        # Test XML Processing Agent
        print("\n--- Testing XML Processing Agent ---")
        try:
            await ProcessingStatusManager.update_agent_status(
                document_id, "xml_processing_agent", "in_progress", admin_mode=True
            )
            
            xml_agent = LLMEnhancedXMLProcessingAgent()
            xml_result = await xml_agent.process_xml_document(
                xml_content,
                {
                    "processar_com_ia": True,
                    "extrair_insights": True,
                    "categorizar_automaticamente": True,
                    "validar_regras_negocio": True,
                    "document_id": document_id,
                    "document_type": "NFE"
                }
            )
            
            print(f"XML processing result: {type(xml_result)}")
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "xml_processing_agent", "completed", admin_mode=True
            )
            
            print("✅ XML Processing Agent completed successfully")
            
        except Exception as e:
            print(f"❌ XML Processing Agent failed: {e}")
            await ProcessingStatusManager.update_agent_status(
                document_id, "xml_processing_agent", "failed", str(e), admin_mode=True
            )
        
        # Test AI Categorization Agent
        print("\n--- Testing AI Categorization Agent ---")
        try:
            await ProcessingStatusManager.update_agent_status(
                document_id, "ai_categorization_agent", "in_progress", admin_mode=True
            )
            
            categorization_agent = LLMEnhancedAICategorizationAgent()
            categorization_result = await categorization_agent.categorize_document(
                xml_content,
                {
                    "document_id": document_id,
                    "document_type": "NFE",
                    "context": "automated_processing"
                }
            )
            
            print(f"Categorization result: {type(categorization_result)}")
            
            await ProcessingStatusManager.update_agent_status(
                document_id, "ai_categorization_agent", "completed", admin_mode=True
            )
            
            print("✅ AI Categorization Agent completed successfully")
            
        except Exception as e:
            print(f"❌ AI Categorization Agent failed: {e}")
            await ProcessingStatusManager.update_agent_status(
                document_id, "ai_categorization_agent", "failed", str(e), admin_mode=True
            )
        
        print("\n=== Test completed ===")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_processing())