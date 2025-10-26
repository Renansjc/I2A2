"""
Simplified Dimensional Processing Test
Tests the dimensional processing pipeline without complex status tracking

This is a simplified version that focuses on core functionality:
- XML processing and data extraction
- Dimensional table population
- Basic validation
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import structlog
import uuid

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

# Import dimensional processing components
from agents.dimensional_processing_agent import DimensionalProcessingAgent
from utils.database import get_supabase_client


class SimplifiedDimensionalTester:
    """Simplified dimensional processing tester"""
    
    def __init__(self):
        self.dimensional_agent = DimensionalProcessingAgent()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.test_results = []
    
    async def run_simplified_tests(self):
        """Run simplified dimensional processing tests"""
        print("🧪 SIMPLIFIED DIMENSIONAL PROCESSING TESTS")
        print("=" * 60)
        
        # Initialize agent
        await self.dimensional_agent.initialize()
        
        try:
            # Get XML files
            xml_files_dir = Path("../xml_nf")
            if not xml_files_dir.exists():
                xml_files_dir = Path("xml_nf")
            
            if not xml_files_dir.exists():
                print("❌ XML files directory not found")
                return
            
            # Get all XML files (both .xml and .XML extensions)
            xml_files = []
            xml_files.extend(xml_files_dir.glob("*.xml"))
            xml_files.extend(xml_files_dir.glob("*.XML"))
            
            # Remove duplicates by converting to set and back to list
            xml_files = list(set(xml_files))
            
            print(f"📁 Found {len(xml_files)} XML files for testing")
            
            # Test each file
            for i, xml_file in enumerate(xml_files, 1):
                await self._test_single_file(xml_file, i, len(xml_files))
            
            # Generate report
            self._generate_report()
            
            print("\n🎉 Simplified Tests Completed!")
            
        finally:
            # Cleanup agent
            await self.dimensional_agent.cleanup()
    
    async def _test_single_file(self, xml_file: Path, file_num: int, total_files: int):
        """Test processing of a single XML file"""
        print(f"\n📄 Testing File {file_num}/{total_files}: {xml_file.name}")
        print("-" * 50)
        
        test_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "processing_time": 0,
            "extracted_data": {},
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {test_result['file_size']:,} bytes")
            
            # Test direct dimensional processing
            start_time = datetime.now()
            
            # Create context for processing
            context = {
                'document_id': str(uuid.uuid4()),
                'document_type': 'NFE',
                'test_mode': True
            }
            
            # Process through dimensional agent directly
            result = await self.dimensional_agent.process_fiscal_document(
                xml_content, context
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            test_result.update({
                "success": True,
                "processing_time": processing_time,
                "extracted_data": result
            })
            
            print(f"✅ Processing completed in {processing_time:.2f}s")
            print(f"📋 Emitente ID: {result.get('emitente_id', 'N/A')}")
            print(f"📦 Produtos processed: {result.get('produtos_processed', 0)}")
            print(f"🧾 Fact records created: {result.get('fact_records_created', 0)}")
            
            # Validate data in database
            await self._validate_database_data(result, test_result)
            
        except Exception as e:
            test_result["errors"].append(str(e))
            print(f"❌ Processing failed: {str(e)}")
            logger.error("Simplified test failed", filename=xml_file.name, error=str(e))
        
        self.test_results.append(test_result)
    
    async def _validate_database_data(self, processing_result: Dict[str, Any], test_result: Dict[str, Any]):
        """Validate that data was correctly stored in database"""
        try:
            validation_results = {}
            
            # Check emitente data
            emitente_id = processing_result.get('emitente_id')
            if emitente_id:
                emitente_check = self.supabase_client.table('dim_emitente').select('cnpj').eq('cnpj', emitente_id).execute()
                validation_results['emitente_exists'] = len(emitente_check.data) > 0
                print(f"   🏢 Emitente in DB: {'✅' if validation_results['emitente_exists'] else '❌'}")
            
            # Check produtos data
            produtos_processed = processing_result.get('produtos_processed', 0)
            if produtos_processed > 0:
                produtos_check = self.supabase_client.table('dim_produtos').select('codigo_produto', count='exact').execute()
                validation_results['produtos_count'] = produtos_check.count
                print(f"   📦 Products in DB: {produtos_check.count}")
            
            # Check fact records
            fact_records = processing_result.get('fact_records_created', 0)
            if fact_records > 0:
                fact_check = self.supabase_client.table('fact_itens_nfe').select('id', count='exact').execute()
                validation_results['fact_records_count'] = fact_check.count
                print(f"   🧾 Fact records in DB: {fact_check.count}")
            
            test_result['validation_results'] = validation_results
            
        except Exception as e:
            print(f"   ⚠️  Validation error: {str(e)}")
            test_result['validation_errors'] = [str(e)]
    
    def _generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 SIMPLIFIED DIMENSIONAL PROCESSING REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success", False))
        failed_tests = total_tests - successful_tests
        
        print(f"📁 Total Files Tested: {total_tests}")
        print(f"✅ Successful Tests: {successful_tests}")
        print(f"❌ Failed Tests: {failed_tests}")
        print(f"📈 Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        if successful_tests > 0:
            # Processing time analysis
            processing_times = [r.get("processing_time", 0) for r in self.test_results if r.get("success")]
            avg_time = sum(processing_times) / len(processing_times)
            
            print(f"\n⏱️  Performance:")
            print(f"   Average Processing Time: {avg_time:.2f}s")
            print(f"   Fastest: {min(processing_times):.2f}s")
            print(f"   Slowest: {max(processing_times):.2f}s")
            
            # Data extraction analysis
            total_emitentes = sum(1 for r in self.test_results if r.get("success") and r.get("extracted_data", {}).get("emitente_id"))
            total_produtos = sum(r.get("extracted_data", {}).get("produtos_processed", 0) for r in self.test_results if r.get("success"))
            total_facts = sum(r.get("extracted_data", {}).get("fact_records_created", 0) for r in self.test_results if r.get("success"))
            
            print(f"\n📊 Data Extraction:")
            print(f"   Emitentes Processed: {total_emitentes}")
            print(f"   Products Processed: {total_produtos}")
            print(f"   Fact Records Created: {total_facts}")
        
        # Failed tests analysis
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.get("success"):
                    print(f"   {result['filename']}: {', '.join(result.get('errors', ['Unknown error']))}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"simplified_dimensional_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_results": self.test_results,
                    "summary": {
                        "total_tests": total_tests,
                        "successful_tests": successful_tests,
                        "failed_tests": failed_tests,
                        "success_rate": (successful_tests/total_tests*100) if total_tests > 0 else 0
                    }
                }, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results: {str(e)}")


async def main():
    """Main test execution"""
    print("🧪 Simplified Dimensional Processing Test Suite")
    print("Testing core dimensional processing without complex dependencies")
    print()
    
    tester = SimplifiedDimensionalTester()
    await tester.run_simplified_tests()


if __name__ == "__main__":
    asyncio.run(main())