#!/usr/bin/env python3

from utils.database import SupabaseClient
import asyncio

async def check_document_types():
    try:
        print("🔍 Checking fiscal_documents table...")
        
        # Method 1: Using anon client (RLS policies apply)
        print("\n📊 Method 1 - Using anon client (with RLS):")
        anon_client = SupabaseClient(use_service_key=False)
        result = anon_client.client.table('fiscal_documents').select('*').execute()
        print(f"   Documents found: {len(result.data)}")
        
        # Method 2: Using service client (bypasses RLS)
        print("\n📊 Method 2 - Using service client (bypasses RLS):")
        service_client = SupabaseClient(use_service_key=True)
        service_result = service_client.client.table('fiscal_documents').select('*').execute()
        print(f"   Documents found: {len(service_result.data)}")
        
        if service_result.data:
            print("\n📄 Document Types in Database (Service Client):")
            print("-" * 60)
            
            for doc in service_result.data:
                filename = doc.get('filename', 'Unknown')
                doc_type = doc.get('document_type', 'Unknown')
                created_at = doc.get('created_at', 'Unknown')
                file_size = doc.get('file_size', 0)
                print(f"   {filename}: {doc_type} ({file_size} bytes, Created: {created_at})")
                
            print(f"\n📊 Total documents: {len(service_result.data)}")
            
            # Check for the specific NFSE file
            nfse_file = "42054072257653110000170000000000000725050541353120.xml"
            nfse_doc = next((doc for doc in service_result.data if doc.get('filename') == nfse_file), None)
            if nfse_doc:
                print(f"\n🎯 NFSE File Found:")
                print(f"   Filename: {nfse_doc.get('filename')}")
                print(f"   Type: {nfse_doc.get('document_type')}")
                print(f"   Size: {nfse_doc.get('file_size')} bytes")
                
                # Check if it was correctly detected as NFSE
                if nfse_doc.get('document_type') == 'NFSE':
                    print("   ✅ Correctly detected as NFSE!")
                else:
                    print(f"   ❌ Incorrectly detected as {nfse_doc.get('document_type')} (should be NFSE)")
            else:
                print(f"\n❌ NFSE file '{nfse_file}' not found")
        else:
            print("❌ No documents found even with service client")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_document_types())