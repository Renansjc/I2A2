"""
Test script for XML Processing Agent with real Brazilian fiscal documents
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

from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent

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


class XMLProcessingTestSuite:
    """Test suite for XML Processing Agent with real data"""
    
    def __init__(self):
        self.agent = LLMEnhancedXMLProcessingAgent()
        self.xml_files_dir = Path("../xml_nf")
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all XML processing tests with real data"""
        print("🚀 Starting XML Processing Agent Real Data Tests")
        print("=" * 60)
        
        # Get all XML files
        xml_files = self._get_xml_files()
        
        if not xml_files:
            print("❌ No XML files found in xml_nf directory")
            return
        
        print(f"📁 Found {len(xml_files)} XML files to test")
        
        # Test each XML file
        for xml_file in xml_files:
            await self._test_xml_file(xml_file)
        
        # Generate summary report
        self._generate_summary_report()
        
        print("\n🎉 XML Processing Agent Real Data Tests Completed!")
    
    def _get_xml_files(self) -> List[Path]:
        """Get list of XML files to test"""
        xml_files = []
        
        if self.xml_files_dir.exists():
            xml_files = list(self.xml_files_dir.glob("*.xml")) + list(self.xml_files_dir.glob("*.XML"))
        
        return sorted(xml_files)
    
    async def _test_xml_file(self, xml_file: Path):
        """Test processing of a single XML file"""
        print(f"\n📄 Testing file: {xml_file.name}")
        print("-" * 40)
        
        test_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "processing_time": 0,
            "document_type": None,
            "extracted_data": {},
            "insights": [],
            "anomalies": [],
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {test_result['file_size']:,} bytes")
            
            # Prepare context
            context = {
                'document_id': f"test_{xml_file.stem}",
                'document_type': 'NFE',  # Will be detected by agent
                'test_mode': True
            }
            
            # Process XML document
            start_time = datetime.now()
            
            result = await self.agent.process_xml_document(xml_content, context)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update test result
            test_result.update({
                "success": True,
                "processing_time": processing_time,
                "document_type": result.get("document_type"),
                "extracted_data": result.get("document_summary", {}),
                "insights": result.get("business_insights", []),
                "anomalies": result.get("anomalies", []),
                "semantic_analysis": result.get("semantic_analysis", {}),
                "business_validation": result.get("business_validation", {})
            })
            
            # Print results
            self._print_processing_results(result, processing_time)
            
        except Exception as e:
            test_result["errors"].append(str(e))
            print(f"❌ Error processing {xml_file.name}: {str(e)}")
            logger.error("XML processing test failed", filename=xml_file.name, error=str(e))
        
        self.test_results.append(test_result)
    
    def _print_processing_results(self, result: Dict[str, Any], processing_time: float):
        """Print processing results for a file"""
        print(f"✅ Processing completed in {processing_time:.2f}s")
        
        # Document summary
        summary = result.get("document_summary", {})
        print(f"📋 Document Type: {result.get('document_type', 'Unknown')}")
        print(f"🏢 Supplier: {summary.get('supplier', 'N/A')}")
        print(f"💰 Total Value: R$ {summary.get('total_value', 0):,.2f}")
        print(f"📅 Emission Date: {summary.get('emission_date', 'N/A')}")
        
        # Semantic analysis
        semantic = result.get("semantic_analysis", {})
        if semantic:
            print(f"🧠 Semantic Analysis Confidence: {semantic.get('confidence', 0):.2f}")
            print(f"📊 Data Completeness: {semantic.get('data_completeness', 0):.2f}")
        
        # Business insights
        insights = result.get("business_insights", [])
        if insights:
            print(f"💡 Business Insights ({len(insights)}):")
            for insight in insights[:3]:  # Show first 3
                print(f"   - {insight.get('description', 'N/A')}")
        
        # Anomalies
        anomalies = result.get("anomalies", [])
        if anomalies:
            print(f"⚠️  Anomalies Detected ({len(anomalies)}):")
            for anomaly in anomalies:
                print(f"   - {anomaly}")
        
        # Business validation
        validation = result.get("business_validation", {})
        if validation:
            valid_count = sum(1 for v in validation.values() if v)
            total_count = len(validation)
            print(f"✓ Business Validation: {valid_count}/{total_count} checks passed")
    
    def _generate_summary_report(self):
        """Generate summary report of all tests"""
        print("\n" + "=" * 60)
        print("📊 SUMMARY REPORT")
        print("=" * 60)
        
        total_files = len(self.test_results)
        successful_files = sum(1 for r in self.test_results if r["success"])
        failed_files = total_files - successful_files
        
        print(f"📁 Total Files Tested: {total_files}")
        print(f"✅ Successful: {successful_files}")
        print(f"❌ Failed: {failed_files}")
        print(f"📈 Success Rate: {(successful_files/total_files*100):.1f}%")
        
        if successful_files > 0:
            # Processing time statistics
            processing_times = [r["processing_time"] for r in self.test_results if r["success"]]
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            
            print(f"\n⏱️  Processing Time Statistics:")
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Maximum: {max_time:.2f}s")
            print(f"   Minimum: {min_time:.2f}s")
            
            # Document type distribution
            doc_types = {}
            for result in self.test_results:
                if result["success"]:
                    doc_type = result.get("document_type", "Unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            print(f"\n📋 Document Types:")
            for doc_type, count in doc_types.items():
                print(f"   {doc_type}: {count} files")
            
            # Value analysis
            total_values = []
            for result in self.test_results:
                if result["success"] and result["extracted_data"]:
                    value = result["extracted_data"].get("total_value", 0)
                    if isinstance(value, (int, float)) and value > 0:
                        total_values.append(value)
            
            if total_values:
                print(f"\n💰 Value Analysis:")
                print(f"   Total Documents Value: R$ {sum(total_values):,.2f}")
                print(f"   Average Document Value: R$ {sum(total_values)/len(total_values):,.2f}")
                print(f"   Highest Value: R$ {max(total_values):,.2f}")
                print(f"   Lowest Value: R$ {min(total_values):,.2f}")
            
            # Anomalies summary
            total_anomalies = sum(len(r.get("anomalies", [])) for r in self.test_results if r["success"])
            files_with_anomalies = sum(1 for r in self.test_results if r["success"] and r.get("anomalies"))
            
            print(f"\n⚠️  Anomalies Summary:")
            print(f"   Total Anomalies: {total_anomalies}")
            print(f"   Files with Anomalies: {files_with_anomalies}")
            
            # Business insights summary
            total_insights = sum(len(r.get("insights", [])) for r in self.test_results if r["success"])
            
            print(f"\n💡 Business Insights:")
            print(f"   Total Insights Generated: {total_insights}")
            print(f"   Average per Document: {total_insights/successful_files:.1f}")
        
        # Failed files details
        if failed_files > 0:
            print(f"\n❌ Failed Files:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   {result['filename']}: {', '.join(result['errors'])}")
        
        # Save detailed results to JSON
        self._save_results_to_file()
    
    def _save_results_to_file(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"xml_processing_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Detailed results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def test_document_type_detection():
    """Test document type detection with real files"""
    print("\n🔍 Testing Document Type Detection")
    print("-" * 40)
    
    agent = LLMEnhancedXMLProcessingAgent()
    xml_files_dir = Path("../xml_nf")
    
    if not xml_files_dir.exists():
        print("❌ XML files directory not found")
        return
    
    xml_files = list(xml_files_dir.glob("*.xml")) + list(xml_files_dir.glob("*.XML"))
    
    for xml_file in xml_files[:3]:  # Test first 3 files
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            detected_type = await agent.detect_document_type(xml_content)
            print(f"📄 {xml_file.name}: {detected_type}")
            
        except Exception as e:
            print(f"❌ Error with {xml_file.name}: {str(e)}")


async def test_semantic_analysis():
    """Test semantic analysis capabilities"""
    print("\n🧠 Testing Semantic Analysis")
    print("-" * 40)
    
    agent = LLMEnhancedXMLProcessingAgent()
    
    # Test with sample fiscal data
    sample_fiscal_data = {
        "supplier_name": "GK INFOSTORE SP",
        "total_value": 5533.13,
        "emission_date": "2025-09-15T09:55:59-03:00",
        "document_key": "35250941797695000323550010000021281408322997"
    }
    
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe><infNFe><emit><xNome>GK INFOSTORE SP</xNome></emit></infNFe></NFe>
    </nfeProc>"""
    
    try:
        analysis = await agent.perform_semantic_analysis(sample_fiscal_data, sample_xml)
        
        print(f"✅ Semantic Analysis Results:")
        print(f"   Structure: {analysis.get('document_structure', 'N/A')}")
        print(f"   Completeness: {analysis.get('data_completeness', 0):.2f}")
        print(f"   Confidence: {analysis.get('confidence', 0):.2f}")
        
        insights = analysis.get('key_insights', [])
        if insights:
            print(f"   Key Insights:")
            for insight in insights:
                print(f"     - {insight}")
        
    except Exception as e:
        print(f"❌ Semantic analysis test failed: {str(e)}")


async def test_anomaly_detection():
    """Test anomaly detection with various scenarios"""
    print("\n⚠️  Testing Anomaly Detection")
    print("-" * 40)
    
    agent = LLMEnhancedXMLProcessingAgent()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "High Value Document",
            "data": {"total_value": 150000, "emission_date": "2025-01-15T10:00:00"}
        },
        {
            "name": "Old Document",
            "data": {"total_value": 1000, "emission_date": "2022-01-15T10:00:00"}
        },
        {
            "name": "Future Date Document",
            "data": {"total_value": 1000, "emission_date": "2026-12-31T10:00:00"}
        },
        {
            "name": "Normal Document",
            "data": {"total_value": 5000, "emission_date": "2025-01-15T10:00:00"}
        }
    ]
    
    for scenario in test_scenarios:
        try:
            anomalies = await agent.detect_anomalies(scenario["data"], {})
            
            print(f"📊 {scenario['name']}:")
            if anomalies:
                for anomaly in anomalies:
                    print(f"   ⚠️  {anomaly}")
            else:
                print(f"   ✅ No anomalies detected")
            
        except Exception as e:
            print(f"❌ Error in {scenario['name']}: {str(e)}")


if __name__ == "__main__":
    print("🧪 XML Processing Agent Real Data Test Suite")
    print("=" * 60)
    
    async def main():
        # Run document type detection test
        await test_document_type_detection()
        
        # Run semantic analysis test
        await test_semantic_analysis()
        
        # Run anomaly detection test
        await test_anomaly_detection()
        
        # Run comprehensive test suite
        test_suite = XMLProcessingTestSuite()
        await test_suite.run_all_tests()
    
    # Run the tests
    asyncio.run(main())