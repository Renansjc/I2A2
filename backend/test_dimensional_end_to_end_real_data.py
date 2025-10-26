"""
End-to-End Dimensional Processing Tests with Real XML Data
Task 7.1: Implementar testes de processamento end-to-end

This test suite validates the complete dimensional processing pipeline using real XML files
from the xml_nf directory, ensuring data integrity and proper categorization.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from decimal import Decimal

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
from agents.dimensional_coordinator import DimensionalCoordinator
from agents.dimensional_processing_agent import DimensionalProcessingAgent
from utils.database import get_supabase_client


class DimensionalEndToEndTester:
    """Comprehensive end-to-end tester for dimensional processing pipeline"""
    
    def __init__(self):
        self.coordinator = DimensionalCoordinator()
        self.dimensional_agent = DimensionalProcessingAgent()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.test_results = []
        self.processing_metrics = {
            'total_processing_time': 0,
            'documents_processed': 0,
            'emitentes_created': 0,
            'destinatarios_created': 0,
            'produtos_processed': 0,
            'servicos_processed': 0,
            'fact_records_created': 0,
            'categorization_successes': 0,
            'integrity_validations': 0
        }
    
    async def run_dimensional_end_to_end_tests(self):
        """Run complete end-to-end dimensional processing tests"""
        print("🚀 Starting Dimensional End-to-End Processing Tests")
        print("=" * 80)
        
        # Initialize coordinator
        await self.coordinator.initialize()
        
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
            
            if not xml_files:
                print("❌ No XML files found")
                return
            
            print(f"📁 Found {len(xml_files)} XML files for dimensional processing tests")
            
            # Test each file through complete dimensional pipeline
            for i, xml_file in enumerate(xml_files, 1):
                await self._test_dimensional_pipeline(xml_file, i, len(xml_files))
            
            # Generate comprehensive report
            await self._generate_dimensional_report()
            
            print("\n🎉 Dimensional End-to-End Tests Completed!")
            
        finally:
            # Cleanup coordinator
            await self.coordinator.cleanup()
    
    async def _test_dimensional_pipeline(self, xml_file: Path, file_num: int, total_files: int):
        """Test complete dimensional pipeline for a single XML file"""
        print(f"\n📄 Testing Dimensional Pipeline {file_num}/{total_files}: {xml_file.name}")
        print("-" * 70)
        
        pipeline_start_time = datetime.now()
        
        test_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": pipeline_start_time.isoformat(),
            "success": False,
            "pipeline_stages": {},
            "total_processing_time": 0,
            "dimensional_data": {},
            "data_quality": {},
            "integrity_validation": {},
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {test_result['file_size']:,} bytes")
            
            # Generate unique document ID for this test (use UUID format)
            import uuid
            document_id = str(uuid.uuid4())
            document_type = 'NFE'  # Assume NFE for now
            
            print(f"🆔 Document ID: {document_id}")
            
            # Execute complete dimensional processing pipeline
            print("🔄 Executing Dimensional Processing Pipeline...")
            pipeline_start = datetime.now()
            
            pipeline_result = await self.coordinator.process_document_pipeline(
                xml_content, document_id, document_type
            )
            
            pipeline_end = datetime.now()
            pipeline_time = (pipeline_end - pipeline_start).total_seconds()
            
            print(f"   ✅ Pipeline completed in {pipeline_time:.2f}s")
            
            # Validate dimensional data extraction
            print("\n📋 Validating Dimensional Data Extraction...")
            extraction_validation = await self._validate_data_extraction(
                document_id, pipeline_result
            )
            
            # Validate categorization results
            print("🏷️  Validating Categorization Results...")
            categorization_validation = await self._validate_categorization_results(
                document_id, pipeline_result
            )
            
            # Validate referential integrity
            print("🔗 Validating Referential Integrity...")
            integrity_validation = await self._validate_referential_integrity(
                document_id, pipeline_result
            )
            
            # Validate data quality
            print("📊 Validating Data Quality...")
            quality_validation = await self._validate_data_quality(
                xml_content, document_id, pipeline_result
            )
            
            # Calculate total processing time
            total_time = (datetime.now() - pipeline_start_time).total_seconds()
            
            # Update test result
            test_result.update({
                "success": True,
                "total_processing_time": total_time,
                "pipeline_stages": pipeline_result.get("stages", {}),
                "dimensional_data": {
                    "emitente_id": pipeline_result.get("summary", {}).get("emitente_processed"),
                    "destinatario_id": pipeline_result.get("summary", {}).get("destinatario_processed"),
                    "produtos_count": pipeline_result.get("summary", {}).get("produtos_count", 0),
                    "servicos_count": pipeline_result.get("summary", {}).get("servicos_count", 0),
                    "fact_records_count": pipeline_result.get("summary", {}).get("fact_records_count", 0)
                },
                "data_quality": {
                    "extraction_validation": extraction_validation,
                    "categorization_validation": categorization_validation,
                    "quality_validation": quality_validation
                },
                "integrity_validation": integrity_validation
            })
            
            # Update metrics
            self._update_processing_metrics(pipeline_result, total_time)
            
            print(f"\n✅ Dimensional Pipeline Test completed in {total_time:.2f}s")
            self._print_test_summary(test_result)
            
        except Exception as e:
            test_result["errors"].append(str(e))
            print(f"❌ Dimensional Pipeline Test failed: {str(e)}")
            logger.error("Dimensional pipeline test failed", filename=xml_file.name, error=str(e))
        
        self.test_results.append(test_result)
    
    async def _validate_data_extraction(self, document_id: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that data was correctly extracted and stored in dimensional tables"""
        try:
            validation_result = {
                "emitente_extracted": False,
                "destinatario_extracted": False,
                "produtos_extracted": False,
                "servicos_extracted": False,
                "extraction_errors": []
            }
            
            summary = pipeline_result.get("summary", {})
            
            # Check emitente extraction
            if summary.get("emitente_processed"):
                # Verify emitente exists in database
                dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
                emitente_id = dimensional_result.get("emitente_id")
                
                if emitente_id:
                    emitente_check = self.supabase_client.table('dim_emitente').select('cnpj').eq('cnpj', emitente_id).execute()
                    validation_result["emitente_extracted"] = len(emitente_check.data) > 0
                    
                    if not validation_result["emitente_extracted"]:
                        validation_result["extraction_errors"].append(f"Emitente {emitente_id} not found in dim_emitente")
            
            # Check destinatario extraction
            if summary.get("destinatario_processed"):
                validation_result["destinatario_extracted"] = True
            
            # Check produtos extraction
            produtos_count = summary.get("produtos_count", 0)
            if produtos_count > 0:
                produtos_check = self.supabase_client.table('dim_produtos').select('codigo_produto', count='exact').execute()
                validation_result["produtos_extracted"] = produtos_check.count >= produtos_count
                
                if not validation_result["produtos_extracted"]:
                    validation_result["extraction_errors"].append(f"Expected {produtos_count} products, found {produtos_check.count}")
            
            # Check servicos extraction
            servicos_count = summary.get("servicos_count", 0)
            if servicos_count > 0:
                servicos_check = self.supabase_client.table('dim_servicos').select('codigo_servico', count='exact').execute()
                validation_result["servicos_extracted"] = servicos_check.count >= servicos_count
                
                if not validation_result["servicos_extracted"]:
                    validation_result["extraction_errors"].append(f"Expected {servicos_count} services, found {servicos_check.count}")
            
            validation_result["overall_success"] = (
                validation_result["emitente_extracted"] and
                len(validation_result["extraction_errors"]) == 0
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Data extraction validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_categorization_results(self, document_id: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that categorization was applied correctly"""
        try:
            validation_result = {
                "categorization_applied": False,
                "categories_assigned": 0,
                "confidence_scores": [],
                "categorization_methods": [],
                "categorization_errors": []
            }
            
            categorization_stage = pipeline_result.get("stages", {}).get("ai_categorization", {})
            
            if categorization_stage:
                categorized_items = categorization_stage.get("categorized_items", [])
                validation_result["categorization_applied"] = len(categorized_items) > 0
                validation_result["categories_assigned"] = len(set(item.get("category", "") for item in categorized_items))
                
                # Collect confidence scores and methods
                for item in categorized_items:
                    confidence = item.get("confidence", 0.0)
                    method = item.get("categorization_method", "unknown")
                    
                    validation_result["confidence_scores"].append(confidence)
                    validation_result["categorization_methods"].append(method)
                
                # Calculate average confidence
                if validation_result["confidence_scores"]:
                    validation_result["average_confidence"] = sum(validation_result["confidence_scores"]) / len(validation_result["confidence_scores"])
                else:
                    validation_result["average_confidence"] = 0.0
                
                # Check if categories were stored in dimensional tables
                dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
                produtos_count = dimensional_result.get("produtos_processed", 0)
                
                if produtos_count > 0:
                    # Check if products have categories assigned
                    produtos_with_categories = self.supabase_client.table('dim_produtos').select('categoria').not_.is_('categoria', 'null').execute()
                    validation_result["categories_stored"] = len(produtos_with_categories.data) > 0
                else:
                    validation_result["categories_stored"] = True  # No products to categorize
            
            validation_result["overall_success"] = (
                validation_result["categorization_applied"] and
                validation_result["average_confidence"] > 0.3
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Categorization validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_referential_integrity(self, document_id: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate referential integrity between dimensional and fact tables"""
        try:
            validation_result = {
                "emitente_integrity": False,
                "destinatario_integrity": False,
                "produtos_integrity": False,
                "servicos_integrity": False,
                "fact_records_integrity": False,
                "integrity_errors": []
            }
            
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            integrity_check = dimensional_result.get("integrity_check", {})
            
            # Use the integrity check from dimensional processing
            if integrity_check:
                validation_result["emitente_integrity"] = integrity_check.get("emitente_exists", False)
                validation_result["destinatario_integrity"] = integrity_check.get("destinatario_exists", True)  # Optional
                validation_result["produtos_integrity"] = integrity_check.get("produtos_exist", False)
                validation_result["servicos_integrity"] = integrity_check.get("servicos_exist", True)  # May not exist
                validation_result["fact_records_integrity"] = integrity_check.get("fact_records_exist", False)
                
                # Check overall integrity
                validation_result["overall_integrity"] = integrity_check.get("overall_integrity", False)
            
            # Additional validation: Check fact table foreign keys
            fact_records_count = dimensional_result.get("fact_records_created", 0)
            if fact_records_count > 0:
                # Check if fact records reference valid dimensional records
                try:
                    # Check NFE fact records
                    nfe_facts = self.supabase_client.table('fact_itens_nfe').select('chave_nfe, codigo_produto').limit(10).execute()
                    
                    for fact in nfe_facts.data:
                        produto_code = fact.get('codigo_produto')
                        if produto_code:
                            produto_exists = self.supabase_client.table('dim_produtos').select('codigo_produto').eq('codigo_produto', produto_code).execute()
                            if not produto_exists.data:
                                validation_result["integrity_errors"].append(f"Fact record references non-existent product: {produto_code}")
                
                except Exception as e:
                    validation_result["integrity_errors"].append(f"Fact table validation error: {str(e)}")
            
            validation_result["overall_success"] = (
                validation_result["overall_integrity"] and
                len(validation_result["integrity_errors"]) == 0
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Referential integrity validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    async def _validate_data_quality(self, xml_content: str, document_id: str, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality by comparing extracted data with original XML"""
        try:
            validation_result = {
                "cnpj_format_valid": False,
                "financial_totals_match": False,
                "required_fields_present": False,
                "data_normalization_correct": False,
                "quality_errors": []
            }
            
            # Parse original XML for comparison
            from lxml import etree
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Validate CNPJ format
            dimensional_result = pipeline_result.get("stages", {}).get("dimensional_processing", {})
            emitente_id = dimensional_result.get("emitente_id")
            
            if emitente_id:
                # Check if CNPJ is properly formatted
                import re
                cnpj_pattern = r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$'
                validation_result["cnpj_format_valid"] = bool(re.match(cnpj_pattern, emitente_id))
                
                if not validation_result["cnpj_format_valid"]:
                    validation_result["quality_errors"].append(f"Invalid CNPJ format: {emitente_id}")
            
            # Validate financial totals (basic check)
            try:
                # Extract total from XML
                xml_total_elements = root.findall('.//{http://www.portalfiscal.inf.br/nfe}vNF')
                if xml_total_elements:
                    xml_total = float(xml_total_elements[0].text or 0)
                    
                    # Get total from fact table
                    fact_records = self.supabase_client.table('fact_itens_nfe').select('valor_total_bruto').execute()
                    if fact_records.data:
                        db_total = sum(float(record.get('valor_total_bruto', 0)) for record in fact_records.data)
                        
                        # Allow small differences due to decimal precision
                        validation_result["financial_totals_match"] = abs(xml_total - db_total) < 0.01
                        
                        if not validation_result["financial_totals_match"]:
                            validation_result["quality_errors"].append(f"Financial totals mismatch: XML={xml_total}, DB={db_total}")
                    else:
                        validation_result["financial_totals_match"] = True  # No data to compare
                else:
                    validation_result["financial_totals_match"] = True  # No total in XML
                    
            except Exception as e:
                validation_result["quality_errors"].append(f"Financial validation error: {str(e)}")
            
            # Check required fields presence
            if emitente_id:
                emitente_data = self.supabase_client.table('dim_emitente').select('*').eq('cnpj', emitente_id).execute()
                if emitente_data.data:
                    emitente = emitente_data.data[0]
                    required_fields = ['cnpj', 'razao_social']
                    missing_fields = [field for field in required_fields if not emitente.get(field)]
                    
                    validation_result["required_fields_present"] = len(missing_fields) == 0
                    
                    if missing_fields:
                        validation_result["quality_errors"].append(f"Missing required fields: {missing_fields}")
            
            # Data normalization check (basic)
            validation_result["data_normalization_correct"] = len(validation_result["quality_errors"]) == 0
            
            validation_result["overall_success"] = (
                validation_result["cnpj_format_valid"] and
                validation_result["financial_totals_match"] and
                validation_result["required_fields_present"] and
                len(validation_result["quality_errors"]) == 0
            )
            
            return validation_result
            
        except Exception as e:
            logger.error("Data quality validation failed", error=str(e))
            return {
                "overall_success": False,
                "validation_error": str(e)
            }
    
    def _update_processing_metrics(self, pipeline_result: Dict[str, Any], processing_time: float):
        """Update processing metrics with results from pipeline"""
        summary = pipeline_result.get("summary", {})
        
        self.processing_metrics['total_processing_time'] += processing_time
        self.processing_metrics['documents_processed'] += 1
        
        if summary.get("emitente_processed"):
            self.processing_metrics['emitentes_created'] += 1
        
        if summary.get("destinatario_processed"):
            self.processing_metrics['destinatarios_created'] += 1
        
        self.processing_metrics['produtos_processed'] += summary.get("produtos_count", 0)
        self.processing_metrics['servicos_processed'] += summary.get("servicos_count", 0)
        self.processing_metrics['fact_records_created'] += summary.get("fact_records_count", 0)
        
        categorization_stage = pipeline_result.get("stages", {}).get("ai_categorization", {})
        if categorization_stage and categorization_stage.get("total_items", 0) > 0:
            self.processing_metrics['categorization_successes'] += 1
        
        integrity_check = pipeline_result.get("summary", {}).get("integrity_check", {})
        if integrity_check.get("overall_integrity"):
            self.processing_metrics['integrity_validations'] += 1
    
    def _print_test_summary(self, test_result: Dict[str, Any]):
        """Print summary of individual test result"""
        dimensional_data = test_result.get("dimensional_data", {})
        data_quality = test_result.get("data_quality", {})
        
        print(f"   📊 Dimensional Data:")
        print(f"     Emitente: {'✅' if dimensional_data.get('emitente_id') else '❌'}")
        print(f"     Destinatário: {'✅' if dimensional_data.get('destinatario_id') else '❌'}")
        print(f"     Produtos: {dimensional_data.get('produtos_count', 0)}")
        print(f"     Serviços: {dimensional_data.get('servicos_count', 0)}")
        print(f"     Registros Fato: {dimensional_data.get('fact_records_count', 0)}")
        
        print(f"   🔍 Data Quality:")
        extraction = data_quality.get("extraction_validation", {})
        categorization = data_quality.get("categorization_validation", {})
        quality = data_quality.get("quality_validation", {})
        
        print(f"     Extração: {'✅' if extraction.get('overall_success') else '❌'}")
        print(f"     Categorização: {'✅' if categorization.get('overall_success') else '❌'}")
        print(f"     Qualidade: {'✅' if quality.get('overall_success') else '❌'}")
        
        integrity = test_result.get("integrity_validation", {})
        print(f"     Integridade: {'✅' if integrity.get('overall_success') else '❌'}")
    
    async def _generate_dimensional_report(self):
        """Generate comprehensive dimensional processing test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DIMENSIONAL PROCESSING TEST REPORT")
        print("=" * 80)
        
        total_files = len(self.test_results)
        successful_files = sum(1 for r in self.test_results if r.get("success", False))
        failed_files = total_files - successful_files
        
        print(f"📁 Total Files Tested: {total_files}")
        print(f"✅ Successful Pipelines: {successful_files}")
        print(f"❌ Failed Pipelines: {failed_files}")
        print(f"📈 Success Rate: {(successful_files/total_files*100):.1f}%")
        
        if successful_files > 0:
            # Processing metrics
            avg_processing_time = self.processing_metrics['total_processing_time'] / successful_files
            
            print(f"\n⏱️  Processing Metrics:")
            print(f"   Total Processing Time: {self.processing_metrics['total_processing_time']:.2f}s")
            print(f"   Average per Document: {avg_processing_time:.2f}s")
            print(f"   Documents Processed: {self.processing_metrics['documents_processed']}")
            print(f"   Emitentes Created: {self.processing_metrics['emitentes_created']}")
            print(f"   Destinatários Created: {self.processing_metrics['destinatarios_created']}")
            print(f"   Produtos Processed: {self.processing_metrics['produtos_processed']}")
            print(f"   Serviços Processed: {self.processing_metrics['servicos_processed']}")
            print(f"   Fact Records Created: {self.processing_metrics['fact_records_created']}")
            print(f"   Categorization Successes: {self.processing_metrics['categorization_successes']}")
            print(f"   Integrity Validations: {self.processing_metrics['integrity_validations']}")
            
            # Data quality analysis
            extraction_successes = sum(1 for r in self.test_results 
                                     if r.get("success") and 
                                     r.get("data_quality", {}).get("extraction_validation", {}).get("overall_success"))
            
            categorization_successes = sum(1 for r in self.test_results 
                                         if r.get("success") and 
                                         r.get("data_quality", {}).get("categorization_validation", {}).get("overall_success"))
            
            quality_successes = sum(1 for r in self.test_results 
                                  if r.get("success") and 
                                  r.get("data_quality", {}).get("quality_validation", {}).get("overall_success"))
            
            integrity_successes = sum(1 for r in self.test_results 
                                    if r.get("success") and 
                                    r.get("integrity_validation", {}).get("overall_success"))
            
            print(f"\n📊 Data Quality Analysis:")
            print(f"   Extraction Success Rate: {(extraction_successes/successful_files*100):.1f}%")
            print(f"   Categorization Success Rate: {(categorization_successes/successful_files*100):.1f}%")
            print(f"   Data Quality Success Rate: {(quality_successes/successful_files*100):.1f}%")
            print(f"   Integrity Validation Rate: {(integrity_successes/successful_files*100):.1f}%")
            
            # Performance analysis
            processing_times = [r.get("total_processing_time", 0) for r in self.test_results if r.get("success")]
            if processing_times:
                min_time = min(processing_times)
                max_time = max(processing_times)
                
                print(f"\n⚡ Performance Analysis:")
                print(f"   Fastest Processing: {min_time:.2f}s")
                print(f"   Slowest Processing: {max_time:.2f}s")
                print(f"   Performance Variance: {max_time - min_time:.2f}s")
        
        # Failed tests analysis
        if failed_files > 0:
            print(f"\n❌ Failed Tests Analysis:")
            for result in self.test_results:
                if not result.get("success"):
                    print(f"   {result['filename']}: {', '.join(result.get('errors', ['Unknown error']))}")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dimensional_end_to_end_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "test_results": self.test_results,
                "processing_metrics": self.processing_metrics,
                "summary": {
                    "total_files": total_files,
                    "successful_files": successful_files,
                    "failed_files": failed_files,
                    "success_rate": (successful_files/total_files*100) if total_files > 0 else 0,
                    "extraction_success_rate": (extraction_successes/successful_files*100) if successful_files > 0 else 0,
                    "categorization_success_rate": (categorization_successes/successful_files*100) if successful_files > 0 else 0,
                    "quality_success_rate": (quality_successes/successful_files*100) if successful_files > 0 else 0,
                    "integrity_success_rate": (integrity_successes/successful_files*100) if successful_files > 0 else 0
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("🧪 Dimensional End-to-End Processing Test Suite")
    print("=" * 80)
    
    tester = DimensionalEndToEndTester()
    await tester.run_dimensional_end_to_end_tests()


if __name__ == "__main__":
    asyncio.run(main())