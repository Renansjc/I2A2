"""
Simplified test script for XML Processing Agent with real Brazilian fiscal documents
Task 4.1: Test XML Processing Agent with real data
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import structlog

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Import the agent directly
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent


async def test_xml_processing_with_real_data():
    """Test XML Processing Agent with real Brazilian fiscal documents"""
    print("🚀 Testing XML Processing Agent with Real Data")
    print("=" * 60)
    
    # Initialize agent
    agent = LLMEnhancedXMLProcessingAgent()
    
    # Get XML files
    xml_files_dir = Path("../xml_nf")
    if not xml_files_dir.exists():
        print("❌ XML files directory not found")
        return
    
    xml_files = list(xml_files_dir.glob("*.xml")) + list(xml_files_dir.glob("*.XML"))
    
    if not xml_files:
        print("❌ No XML files found")
        return
    
    print(f"📁 Found {len(xml_files)} XML files to test")
    
    test_results = []
    
    # Test each XML file
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n📄 Testing file {i}/{len(xml_files)}: {xml_file.name}")
        print("-" * 50)
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {xml_file.stat().st_size:,} bytes")
            
            # Test document type detection
            print("🔍 Detecting document type...")
            doc_type = await agent.detect_document_type(xml_content)
            print(f"   Document type: {doc_type}")
            
            # Test schema validation
            print("✅ Validating schema...")
            is_valid = await agent.validate_schema(xml_content, doc_type)
            print(f"   Schema valid: {is_valid}")
            
            # Test fiscal data extraction
            print("📋 Extracting fiscal data...")
            fiscal_data = await agent.extract_basic_fiscal_data(xml_content, doc_type)
            
            if fiscal_data:
                print(f"   Supplier: {fiscal_data.get('supplier_name', 'N/A')}")
                print(f"   Total Value: R$ {fiscal_data.get('total_value', 0):,.2f}")
                print(f"   Emission Date: {fiscal_data.get('emission_date', 'N/A')}")
                print(f"   Document Key: {fiscal_data.get('document_key', 'N/A')[:20]}...")
            
            # Test semantic analysis
            print("🧠 Performing semantic analysis...")
            semantic_analysis = await agent.perform_semantic_analysis(fiscal_data, xml_content)
            
            if semantic_analysis:
                print(f"   Confidence: {semantic_analysis.get('confidence', 0):.2f}")
                print(f"   Data Completeness: {semantic_analysis.get('data_completeness', 0):.2f}")
                
                insights = semantic_analysis.get('key_insights', [])
                if insights:
                    print(f"   Key Insights:")
                    for insight in insights[:2]:  # Show first 2
                        print(f"     - {insight}")
            
            # Test business insights extraction
            print("💡 Extracting business insights...")
            business_insights = await agent.extract_business_insights(fiscal_data, semantic_analysis)
            
            if business_insights:
                print(f"   Generated {len(business_insights)} insights:")
                for insight in business_insights[:2]:  # Show first 2
                    print(f"     - {insight.get('description', 'N/A')}")
            
            # Test anomaly detection
            print("⚠️  Detecting anomalies...")
            anomalies = await agent.detect_anomalies(fiscal_data, semantic_analysis)
            
            if anomalies:
                print(f"   Found {len(anomalies)} anomalies:")
                for anomaly in anomalies:
                    print(f"     - {anomaly}")
            else:
                print("   No anomalies detected")
            
            # Test business rules validation
            print("✓ Validating business rules...")
            business_validation = await agent.validate_business_rules(fiscal_data)
            
            if business_validation:
                valid_count = sum(1 for v in business_validation.values() if v)
                total_count = len(business_validation)
                print(f"   Validation: {valid_count}/{total_count} checks passed")
                
                for rule, result in business_validation.items():
                    status = "✅" if result else "❌"
                    print(f"     {status} {rule}")
            
            # Store test result
            test_result = {
                "filename": xml_file.name,
                "file_size": xml_file.stat().st_size,
                "document_type": doc_type,
                "schema_valid": is_valid,
                "fiscal_data": fiscal_data,
                "semantic_analysis": semantic_analysis,
                "business_insights_count": len(business_insights) if business_insights else 0,
                "anomalies_count": len(anomalies) if anomalies else 0,
                "business_validation": business_validation,
                "success": True
            }
            
            test_results.append(test_result)
            print("✅ Processing completed successfully")
            
        except Exception as e:
            print(f"❌ Error processing {xml_file.name}: {str(e)}")
            test_results.append({
                "filename": xml_file.name,
                "error": str(e),
                "success": False
            })
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY REPORT")
    print("=" * 60)
    
    total_files = len(test_results)
    successful_files = sum(1 for r in test_results if r.get("success", False))
    failed_files = total_files - successful_files
    
    print(f"📁 Total Files Tested: {total_files}")
    print(f"✅ Successful: {successful_files}")
    print(f"❌ Failed: {failed_files}")
    print(f"📈 Success Rate: {(successful_files/total_files*100):.1f}%")
    
    if successful_files > 0:
        # Document type distribution
        doc_types = {}
        for result in test_results:
            if result.get("success"):
                doc_type = result.get("document_type", "Unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"\n📋 Document Types:")
        for doc_type, count in doc_types.items():
            print(f"   {doc_type}: {count} files")
        
        # Value analysis
        total_values = []
        for result in test_results:
            if result.get("success") and result.get("fiscal_data"):
                value = result["fiscal_data"].get("total_value", 0)
                if isinstance(value, (int, float)) and value > 0:
                    total_values.append(value)
        
        if total_values:
            print(f"\n💰 Value Analysis:")
            print(f"   Total Documents Value: R$ {sum(total_values):,.2f}")
            print(f"   Average Document Value: R$ {sum(total_values)/len(total_values):,.2f}")
            print(f"   Highest Value: R$ {max(total_values):,.2f}")
            print(f"   Lowest Value: R$ {min(total_values):,.2f}")
        
        # Anomalies summary
        total_anomalies = sum(result.get("anomalies_count", 0) for result in test_results if result.get("success"))
        files_with_anomalies = sum(1 for result in test_results if result.get("success") and result.get("anomalies_count", 0) > 0)
        
        print(f"\n⚠️  Anomalies Summary:")
        print(f"   Total Anomalies: {total_anomalies}")
        print(f"   Files with Anomalies: {files_with_anomalies}")
        
        # Business insights summary
        total_insights = sum(result.get("business_insights_count", 0) for result in test_results if result.get("success"))
        
        print(f"\n💡 Business Insights:")
        print(f"   Total Insights Generated: {total_insights}")
        if successful_files > 0:
            print(f"   Average per Document: {total_insights/successful_files:.1f}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"xml_processing_test_results_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Detailed results saved to: {filename}")
        
    except Exception as e:
        print(f"⚠️  Could not save results to file: {str(e)}")
    
    print("\n🎉 XML Processing Agent Real Data Test Completed!")


if __name__ == "__main__":
    asyncio.run(test_xml_processing_with_real_data())