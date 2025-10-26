"""
Basic Dimensional Processing Test
Tests core XML processing and data extraction without database dependencies

This test focuses on:
- XML parsing and data extraction
- Data normalization and validation
- Basic categorization logic
- No database operations
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import structlog
from lxml import etree

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


class BasicDimensionalTester:
    """Basic dimensional processing tester without database dependencies"""
    
    def __init__(self):
        self.dimensional_agent = DimensionalProcessingAgent()
        self.test_results = []
    
    async def run_basic_tests(self):
        """Run basic dimensional processing tests"""
        print("🧪 BASIC DIMENSIONAL PROCESSING TESTS")
        print("=" * 60)
        print("Testing XML parsing and data extraction without database operations")
        print()
        
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
                await self._test_xml_processing(xml_file, i, len(xml_files))
            
            # Generate report
            self._generate_report()
            
            print("\n🎉 Basic Tests Completed!")
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            logger.error("Basic test suite failed", error=str(e))
    
    async def _test_xml_processing(self, xml_file: Path, file_num: int, total_files: int):
        """Test XML processing for a single file"""
        print(f"\n📄 Testing File {file_num}/{total_files}: {xml_file.name}")
        print("-" * 50)
        
        test_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "processing_time": 0,
            "extracted_data": {},
            "validation_results": {},
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {test_result['file_size']:,} bytes")
            
            # Test XML parsing
            start_time = datetime.now()
            
            # Parse XML
            root = etree.fromstring(xml_content.encode('utf-8'))
            print("✅ XML parsing successful")
            
            # Test data extraction methods directly
            extracted_data = await self._test_data_extraction(root)
            
            # Test data normalization
            normalized_data = await self._test_data_normalization(extracted_data)
            
            # Test basic categorization
            categorized_data = await self._test_basic_categorization(normalized_data)
            
            # Test data validation
            validation_results = await self._test_data_validation(categorized_data)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            test_result.update({
                "success": True,
                "processing_time": processing_time,
                "extracted_data": extracted_data,
                "normalized_data": normalized_data,
                "categorized_data": categorized_data,
                "validation_results": validation_results
            })
            
            print(f"✅ Processing completed in {processing_time:.2f}s")
            self._print_extraction_summary(extracted_data, normalized_data, categorized_data)
            
        except Exception as e:
            test_result["errors"].append(str(e))
            print(f"❌ Processing failed: {str(e)}")
            logger.error("Basic XML processing failed", filename=xml_file.name, error=str(e))
        
        self.test_results.append(test_result)
    
    async def _test_data_extraction(self, xml_root) -> Dict[str, Any]:
        """Test data extraction methods"""
        try:
            extracted_data = {}
            
            # Test emitente extraction
            emitente_data = self.dimensional_agent._extract_emitente_data(xml_root, 'NFE')
            extracted_data['emitente'] = emitente_data
            print(f"   🏢 Emitente extracted: {emitente_data.get('razao_social', 'N/A')}")
            
            # Test destinatario extraction
            destinatario_data = self.dimensional_agent._extract_destinatario_data(xml_root, 'NFE')
            extracted_data['destinatario'] = destinatario_data
            if destinatario_data:
                print(f"   👤 Destinatário extracted: {destinatario_data.get('razao_social', 'N/A')}")
            else:
                print("   👤 No destinatário data found")
            
            # Test produtos extraction
            produtos_data = self.dimensional_agent._extract_produtos_data(xml_root)
            extracted_data['produtos'] = produtos_data
            print(f"   📦 Products extracted: {len(produtos_data)}")
            
            # Test NFE items extraction
            nfe_items = self.dimensional_agent._extract_nfe_items_data(xml_root)
            extracted_data['nfe_items'] = nfe_items
            print(f"   🧾 NFE items extracted: {len(nfe_items)}")
            
            return extracted_data
            
        except Exception as e:
            print(f"   ❌ Data extraction failed: {str(e)}")
            raise
    
    async def _test_data_normalization(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test data normalization methods"""
        try:
            normalized_data = {}
            
            # Test emitente normalization
            if extracted_data.get('emitente'):
                normalized_emitente = self.dimensional_agent._normalize_emitente_data(extracted_data['emitente'])
                normalized_data['emitente'] = normalized_emitente
                print(f"   ✅ Emitente normalized: CNPJ {normalized_emitente.get('cnpj', 'N/A')}")
            
            # Test destinatario normalization
            if extracted_data.get('destinatario'):
                normalized_destinatario = self.dimensional_agent._normalize_destinatario_data(extracted_data['destinatario'])
                normalized_data['destinatario'] = normalized_destinatario
                print(f"   ✅ Destinatário normalized")
            
            # Test produtos normalization
            normalized_produtos = []
            for produto in extracted_data.get('produtos', []):
                normalized_produto = self.dimensional_agent._normalize_produto_data(produto)
                normalized_produtos.append(normalized_produto)
            normalized_data['produtos'] = normalized_produtos
            print(f"   ✅ Products normalized: {len(normalized_produtos)}")
            
            return normalized_data
            
        except Exception as e:
            print(f"   ❌ Data normalization failed: {str(e)}")
            raise
    
    async def _test_basic_categorization(self, normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test basic categorization methods"""
        try:
            categorized_data = normalized_data.copy()
            
            # Test product categorization
            categorized_produtos = []
            for produto in normalized_data.get('produtos', []):
                categorized_produto = await self.dimensional_agent._apply_basic_categorization(produto)
                categorized_produtos.append(categorized_produto)
            categorized_data['produtos'] = categorized_produtos
            
            # Count categories
            categories = set()
            for produto in categorized_produtos:
                if produto.get('categoria'):
                    categories.add(produto['categoria'])
            
            print(f"   🏷️  Products categorized: {len(categorized_produtos)} items, {len(categories)} categories")
            if categories:
                print(f"   📋 Categories found: {', '.join(sorted(categories))}")
            
            return categorized_data
            
        except Exception as e:
            print(f"   ❌ Categorization failed: {str(e)}")
            raise
    
    async def _test_data_validation(self, categorized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test data validation"""
        try:
            validation_results = {}
            
            # Validate emitente data
            emitente = categorized_data.get('emitente', {})
            if emitente:
                cnpj = emitente.get('cnpj', '')
                razao_social = emitente.get('razao_social', '')
                
                validation_results['emitente_valid'] = bool(cnpj and razao_social)
                validation_results['cnpj_format_valid'] = len(cnpj.replace('.', '').replace('/', '').replace('-', '')) == 14
                print(f"   ✅ Emitente validation: {'✅' if validation_results['emitente_valid'] else '❌'}")
            
            # Validate produtos data
            produtos = categorized_data.get('produtos', [])
            valid_produtos = 0
            for produto in produtos:
                if produto.get('codigo_produto') and produto.get('descricao'):
                    valid_produtos += 1
            
            validation_results['produtos_valid_count'] = valid_produtos
            validation_results['produtos_total_count'] = len(produtos)
            validation_results['produtos_valid_rate'] = (valid_produtos / len(produtos)) if produtos else 0
            
            print(f"   ✅ Products validation: {valid_produtos}/{len(produtos)} valid ({validation_results['produtos_valid_rate']:.1%})")
            
            # Validate NFE items
            nfe_items = categorized_data.get('nfe_items', [])
            valid_items = 0
            total_value = 0
            
            for item in nfe_items:
                if item.get('codigo_produto') and item.get('valor_total_bruto'):
                    valid_items += 1
                    try:
                        total_value += float(item['valor_total_bruto'])
                    except (ValueError, TypeError):
                        pass
            
            validation_results['nfe_items_valid_count'] = valid_items
            validation_results['nfe_items_total_count'] = len(nfe_items)
            validation_results['nfe_items_total_value'] = total_value
            
            print(f"   ✅ NFE items validation: {valid_items}/{len(nfe_items)} valid, R$ {total_value:,.2f} total")
            
            return validation_results
            
        except Exception as e:
            print(f"   ❌ Data validation failed: {str(e)}")
            return {"validation_error": str(e)}
    
    def _print_extraction_summary(self, extracted_data: Dict[str, Any], normalized_data: Dict[str, Any], categorized_data: Dict[str, Any]):
        """Print summary of extraction results"""
        print("   📊 Extraction Summary:")
        
        # Emitente info
        emitente = normalized_data.get('emitente', {})
        if emitente:
            print(f"     🏢 Company: {emitente.get('razao_social', 'N/A')}")
            print(f"     🆔 CNPJ: {emitente.get('cnpj', 'N/A')}")
            print(f"     📍 Location: {emitente.get('nome_municipio', 'N/A')}, {emitente.get('uf', 'N/A')}")
        
        # Products info
        produtos = categorized_data.get('produtos', [])
        if produtos:
            print(f"     📦 Products: {len(produtos)} items")
            categories = set(p.get('categoria', 'Unknown') for p in produtos)
            print(f"     🏷️  Categories: {', '.join(sorted(categories))}")
        
        # Financial info
        nfe_items = extracted_data.get('nfe_items', [])
        if nfe_items:
            total_value = sum(float(item.get('valor_total_bruto', 0)) for item in nfe_items)
            print(f"     💰 Total Value: R$ {total_value:,.2f}")
    
    def _generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 BASIC DIMENSIONAL PROCESSING REPORT")
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
            print(f"   Average Processing Time: {avg_time:.3f}s")
            print(f"   Fastest: {min(processing_times):.3f}s")
            print(f"   Slowest: {max(processing_times):.3f}s")
            
            # Data extraction analysis
            total_emitentes = sum(1 for r in self.test_results if r.get("success") and r.get("extracted_data", {}).get("emitente"))
            total_produtos = sum(len(r.get("extracted_data", {}).get("produtos", [])) for r in self.test_results if r.get("success"))
            total_items = sum(len(r.get("extracted_data", {}).get("nfe_items", [])) for r in self.test_results if r.get("success"))
            
            print(f"\n📊 Data Extraction:")
            print(f"   Emitentes Found: {total_emitentes}")
            print(f"   Products Extracted: {total_produtos}")
            print(f"   NFE Items Extracted: {total_items}")
            
            # Validation analysis
            valid_emitentes = sum(1 for r in self.test_results if r.get("success") and r.get("validation_results", {}).get("emitente_valid"))
            total_valid_produtos = sum(r.get("validation_results", {}).get("produtos_valid_count", 0) for r in self.test_results if r.get("success"))
            total_value = sum(r.get("validation_results", {}).get("nfe_items_total_value", 0) for r in self.test_results if r.get("success"))
            
            print(f"\n✅ Validation Results:")
            print(f"   Valid Emitentes: {valid_emitentes}/{total_emitentes}")
            print(f"   Valid Products: {total_valid_produtos}")
            print(f"   Total Document Value: R$ {total_value:,.2f}")
            
            # Category analysis
            all_categories = set()
            for result in self.test_results:
                if result.get("success"):
                    produtos = result.get("categorized_data", {}).get("produtos", [])
                    for produto in produtos:
                        if produto.get("categoria"):
                            all_categories.add(produto["categoria"])
            
            if all_categories:
                print(f"\n🏷️  Categories Found:")
                for category in sorted(all_categories):
                    print(f"   - {category}")
        
        # Failed tests analysis
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result.get("success"):
                    print(f"   {result['filename']}: {', '.join(result.get('errors', ['Unknown error']))}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"basic_dimensional_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_results": self.test_results,
                    "summary": {
                        "total_tests": total_tests,
                        "successful_tests": successful_tests,
                        "failed_tests": failed_tests,
                        "success_rate": (successful_tests/total_tests*100) if total_tests > 0 else 0,
                        "total_categories": len(all_categories) if successful_tests > 0 else 0,
                        "categories": sorted(list(all_categories)) if successful_tests > 0 else []
                    }
                }, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results: {str(e)}")


async def main():
    """Main test execution"""
    print("🧪 Basic Dimensional Processing Test Suite")
    print("Testing XML parsing and data extraction without database operations")
    print("This test validates core functionality independently of database setup")
    print()
    
    tester = BasicDimensionalTester()
    await tester.run_basic_tests()


if __name__ == "__main__":
    asyncio.run(main())