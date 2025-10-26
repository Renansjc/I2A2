"""
Real Dimensional Processing Test with File Upload
Tests the complete workflow: Upload → Processing → Validation

This test simulates the real workflow:
1. Upload XML files to create fiscal_documents entries
2. Process through dimensional pipeline
3. Validate results in database
4. Generate comprehensive reports
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

# Import components
from agents.dimensional_coordinator import DimensionalCoordinator
from utils.database import get_supabase_client


class RealDimensionalTester:
    """Real dimensional processing tester with complete workflow"""
    
    def __init__(self):
        self.coordinator = DimensionalCoordinator()
        self.supabase_client = get_supabase_client(admin_mode=True)
        self.test_results = []
        self.uploaded_documents = []
    
    async def run_real_tests(self):
        """Run real dimensional processing tests with upload workflow"""
        print("🚀 REAL DIMENSIONAL PROCESSING TESTS")
        print("=" * 70)
        print("Complete workflow: Upload → Process → Validate")
        print()
        
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
            
            print(f"📁 Found {len(xml_files)} XML files for real testing")
            
            # Phase 1: Upload all files
            print(f"\n📤 PHASE 1: Uploading XML Files")
            print("-" * 50)
            await self._upload_xml_files(xml_files)
            
            # Phase 2: Process through dimensional pipeline
            print(f"\n🔄 PHASE 2: Processing Through Dimensional Pipeline")
            print("-" * 50)
            await self._process_uploaded_files()
            
            # Phase 3: Validate results
            print(f"\n✅ PHASE 3: Validating Results")
            print("-" * 50)
            await self._validate_processing_results()
            
            # Generate comprehensive report
            await self._generate_comprehensive_report()
            
            print("\n🎉 Real Dimensional Tests Completed!")
            
        finally:
            # Cleanup coordinator
            await self.coordinator.cleanup()
    
    async def _upload_xml_files(self, xml_files: List[Path]):
        """Upload XML files to create fiscal_documents entries"""
        print("Uploading XML files to fiscal_documents table...")
        
        for i, xml_file in enumerate(xml_files, 1):
            print(f"   📤 Uploading {i}/{len(xml_files)}: {xml_file.name}")
            
            try:
                # Read XML content
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Generate document ID
                document_id = str(uuid.uuid4())
                
                # Extract basic metadata from XML
                metadata = await self._extract_basic_metadata(xml_content, xml_file.name)
                
                # Create fiscal_documents entry (using required columns)
                fiscal_doc_data = {
                    'id': document_id,
                    'filename': xml_file.name,
                    'file_size': xml_file.stat().st_size,
                    'document_type': metadata.get('document_type', 'NFE'),
                    'xml_content': xml_content
                }
                
                # Insert into fiscal_documents
                result = self.supabase_client.client.table('fiscal_documents').insert(fiscal_doc_data).execute()
                
                if result.data:
                    self.uploaded_documents.append({
                        'document_id': document_id,
                        'filename': xml_file.name,
                        'xml_content': xml_content,
                        'metadata': metadata,
                        'upload_success': True
                    })
                    print(f"      ✅ Uploaded successfully (ID: {document_id[:8]}...)")
                else:
                    print(f"      ❌ Upload failed")
                
            except Exception as e:
                print(f"      ❌ Upload failed: {str(e)}")
                logger.error("File upload failed", filename=xml_file.name, error=str(e))
        
        print(f"\n📊 Upload Summary: {len(self.uploaded_documents)}/{len(xml_files)} files uploaded successfully")
    
    async def _extract_basic_metadata(self, xml_content: str, filename: str) -> Dict[str, Any]:
        """Extract basic metadata from XML for fiscal_documents"""
        try:
            from lxml import etree
            
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Detect document type (NFe vs NFSe)
            document_type = 'NFE'  # Default
            
            # Check for NFSe indicators - improved detection
            nfse_indicators = [
                # Root element checks
                root.tag.lower() == 'nfse',
                'nfse' in root.tag.lower(),
                
                # Namespace checks
                'nfse' in str(root.nsmap) if root.nsmap else False,
                'http://www.sped.fazenda.gov.br/nfse' in str(root.nsmap.values()) if root.nsmap else False,
                
                # Element checks (using xpath for local-name or direct namespace)
                len(root.xpath('.//*[local-name()="NFSe"]')) > 0 if hasattr(root, 'xpath') else False,
                len(root.xpath('.//*[local-name()="infNFSe"]')) > 0 if hasattr(root, 'xpath') else False,
                len(root.xpath('.//*[local-name()="DPS"]')) > 0 if hasattr(root, 'xpath') else False,
                len(root.xpath('.//*[local-name()="CompNfse"]')) > 0 if hasattr(root, 'xpath') else False,
                len(root.xpath('.//*[local-name()="RPS"]')) > 0 if hasattr(root, 'xpath') else False,
                
                # Fallback namespace-aware search
                root.find('.//NFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}NFSe') is not None,
                root.find('.//infNFSe') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}infNFSe') is not None,
                root.find('.//DPS') is not None or root.find('.//{http://www.sped.fazenda.gov.br/nfse}DPS') is not None,
                
                # Content checks
                'nfse' in xml_content.lower(),
                'infnfse' in xml_content.lower(),
                'servico' in xml_content.lower() and 'prestador' in xml_content.lower()
            ]
            
            if any(nfse_indicators):
                document_type = 'NFSE'
            
            metadata = {
                'filename': filename,
                'document_type': document_type
            }
            
            # Try to extract basic info based on document type
            try:
                if document_type == 'NFE':
                    # Extract NFe data
                    emit = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
                    if emit is not None:
                        cnpj_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}CNPJ')
                        if cnpj_elem is not None:
                            metadata['emitente_cnpj'] = cnpj_elem.text
                        
                        nome_elem = emit.find('.//{http://www.portalfiscal.inf.br/nfe}xNome')
                        if nome_elem is not None:
                            metadata['emitente_nome'] = nome_elem.text
                    
                    # Extract document key
                    inf_nfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
                    if inf_nfe is not None:
                        chave = inf_nfe.get('Id', '').replace('NFe', '')
                        if chave:
                            metadata['chave_nfe'] = chave
                    
                    # Extract total value
                    total_elem = root.find('.//{http://www.portalfiscal.inf.br/nfe}vNF')
                    if total_elem is not None:
                        metadata['valor_total'] = float(total_elem.text or 0)
                
                else:  # NFSE
                    # Extract NFSe data - try multiple patterns
                    
                    # Pattern 1: SPED NFSe format (like our file)
                    emit = root.find('.//{http://www.sped.fazenda.gov.br/nfse}emit')
                    if emit is not None:
                        cnpj_elem = emit.find('.//{http://www.sped.fazenda.gov.br/nfse}CNPJ')
                        if cnpj_elem is not None:
                            metadata['emitente_cnpj'] = cnpj_elem.text
                        
                        nome_elem = emit.find('.//{http://www.sped.fazenda.gov.br/nfse}xNome')
                        if nome_elem is not None:
                            metadata['emitente_nome'] = nome_elem.text
                    
                    # Pattern 2: Common NFSe patterns (fallback)
                    if 'emitente_cnpj' not in metadata:
                        prestador = root.find('.//*[local-name()="Prestador"]')
                        if prestador is not None:
                            cnpj_elem = prestador.find('.//*[local-name()="Cnpj"]')
                            if cnpj_elem is not None:
                                metadata['emitente_cnpj'] = cnpj_elem.text
                            
                            nome_elem = prestador.find('.//*[local-name()="RazaoSocial"]')
                            if nome_elem is not None:
                                metadata['emitente_nome'] = nome_elem.text
                    
                    # Extract service value - try multiple patterns
                    valor_elem = root.find('.//{http://www.sped.fazenda.gov.br/nfse}vLiq')
                    if valor_elem is not None:
                        metadata['valor_total'] = float(valor_elem.text or 0)
                    else:
                        # Fallback to common patterns
                        valor_elem = root.find('.//*[local-name()="ValorServicos"]')
                        if valor_elem is not None:
                            metadata['valor_total'] = float(valor_elem.text or 0)
                
            except Exception as e:
                logger.warning("Failed to extract metadata", error=str(e))
            
            return metadata
            
        except Exception as e:
            logger.error("Metadata extraction failed", error=str(e))
            return {'filename': filename, 'extraction_error': str(e)}
    
    async def _process_uploaded_files(self):
        """Process uploaded files through dimensional pipeline"""
        print("Processing uploaded files through dimensional pipeline...")
        
        for i, doc in enumerate(self.uploaded_documents, 1):
            print(f"\n   🔄 Processing {i}/{len(self.uploaded_documents)}: {doc['filename']}")
            
            processing_start = datetime.now()
            
            try:
                # Process through dimensional coordinator using detected document type
                document_type = doc.get('metadata', {}).get('document_type', 'NFE')
                result = await self.coordinator.process_document_pipeline(
                    doc['xml_content'],
                    doc['document_id'],
                    document_type
                )
                
                processing_end = datetime.now()
                processing_time = (processing_end - processing_start).total_seconds()
                
                # Update processing status in fiscal_documents (if status column exists)
                try:
                    await self._update_processing_status(doc['document_id'], 'completed', result)
                except Exception as status_error:
                    logger.warning("Could not update processing status", error=str(status_error))
                
                # Store test result
                test_result = {
                    'document_id': doc['document_id'],
                    'filename': doc['filename'],
                    'processing_success': True,
                    'processing_time': processing_time,
                    'pipeline_result': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.test_results.append(test_result)
                
                print(f"      ✅ Processing completed in {processing_time:.2f}s")
                
                # Print summary of results
                summary = result.get('summary', {})
                print(f"      📊 Emitente: {'✅' if summary.get('emitente_processed') else '❌'}")
                print(f"      📦 Products: {summary.get('produtos_count', 0)}")
                print(f"      🧾 Fact records: {summary.get('fact_records_count', 0)}")
                
            except Exception as e:
                processing_end = datetime.now()
                processing_time = (processing_end - processing_start).total_seconds()
                
                # Update processing status as failed (if status column exists)
                try:
                    await self._update_processing_status(doc['document_id'], 'failed', {'error': str(e)})
                except Exception as status_error:
                    logger.warning("Could not update processing status", error=str(status_error))
                
                test_result = {
                    'document_id': doc['document_id'],
                    'filename': doc['filename'],
                    'processing_success': False,
                    'processing_time': processing_time,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.test_results.append(test_result)
                
                print(f"      ❌ Processing failed in {processing_time:.2f}s: {str(e)}")
                logger.error("Document processing failed", 
                           document_id=doc['document_id'], 
                           filename=doc['filename'], 
                           error=str(e))
        
        successful_processing = sum(1 for r in self.test_results if r.get('processing_success'))
        print(f"\n📊 Processing Summary: {successful_processing}/{len(self.test_results)} documents processed successfully")
    
    async def _update_processing_status(self, document_id: str, status: str, result: Dict[str, Any]):
        """Update processing status in fiscal_documents table"""
        try:
            update_data = {
                'processing_status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 'completed':
                update_data['processing_result'] = result
            elif status == 'failed':
                update_data['processing_error'] = result
            
            self.supabase_client.client.table('fiscal_documents').update(update_data).eq('id', document_id).execute()
            
        except Exception as e:
            logger.error("Failed to update processing status", document_id=document_id, error=str(e))
    
    async def _validate_processing_results(self):
        """Validate processing results in database"""
        print("Validating processing results in database...")
        
        validation_summary = {
            'fiscal_documents_created': 0,
            'emitentes_created': 0,
            'destinatarios_created': 0,
            'produtos_created': 0,
            'fact_records_created': 0,
            'processing_statuses_created': 0
        }
        
        # Check fiscal_documents
        fiscal_docs = self.supabase_client.client.table('fiscal_documents').select('*').execute()
        validation_summary['fiscal_documents_created'] = len(fiscal_docs.data)
        print(f"   📄 Fiscal documents in DB: {validation_summary['fiscal_documents_created']}")
        
        # Check dim_emitente
        emitentes = self.supabase_client.client.table('dim_emitente').select('cnpj').execute()
        validation_summary['emitentes_created'] = len(emitentes.data)
        print(f"   🏢 Emitentes in DB: {validation_summary['emitentes_created']}")
        
        # Check dim_destinatario
        destinatarios = self.supabase_client.client.table('dim_destinatario').select('id').execute()
        validation_summary['destinatarios_created'] = len(destinatarios.data)
        print(f"   👤 Destinatários in DB: {validation_summary['destinatarios_created']}")
        
        # Check dim_produtos
        produtos = self.supabase_client.client.table('dim_produtos').select('codigo_produto').execute()
        validation_summary['produtos_created'] = len(produtos.data)
        print(f"   📦 Products in DB: {validation_summary['produtos_created']}")
        
        # Check fact_itens_nfe
        fact_records = self.supabase_client.client.table('fact_itens_nfe').select('id').execute()
        validation_summary['fact_records_created'] = len(fact_records.data)
        print(f"   🧾 Fact records in DB: {validation_summary['fact_records_created']}")
        
        # Check document_processing_status
        processing_statuses = self.supabase_client.client.table('document_processing_status').select('id').execute()
        validation_summary['processing_statuses_created'] = len(processing_statuses.data)
        print(f"   📊 Processing statuses in DB: {validation_summary['processing_statuses_created']}")
        
        # Detailed validation for each processed document
        print(f"\n   🔍 Detailed Validation:")
        for result in self.test_results:
            if result.get('processing_success'):
                document_id = result['document_id']
                filename = result['filename']
                
                # Check if document has processing status records
                doc_statuses = self.supabase_client.client.table('document_processing_status').select('*').eq('document_id', document_id).execute()
                
                print(f"      📄 {filename[:30]}...")
                print(f"         Status records: {len(doc_statuses.data)}")
                
                # Check specific agent statuses
                agent_statuses = {}
                for status in doc_statuses.data:
                    agent_name = status.get('agent_name')
                    agent_status = status.get('status')
                    agent_statuses[agent_name] = agent_status
                
                print(f"         Agents: {', '.join(f'{k}:{v}' for k, v in agent_statuses.items())}")
        
        return validation_summary
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE REAL DIMENSIONAL PROCESSING REPORT")
        print("=" * 70)
        
        # Overall statistics
        total_files = len(self.uploaded_documents)
        successful_uploads = len(self.uploaded_documents)
        successful_processing = sum(1 for r in self.test_results if r.get('processing_success'))
        failed_processing = len(self.test_results) - successful_processing
        
        print(f"📁 Total Files: {total_files}")
        print(f"📤 Successful Uploads: {successful_uploads}")
        print(f"✅ Successful Processing: {successful_processing}")
        print(f"❌ Failed Processing: {failed_processing}")
        print(f"📈 Overall Success Rate: {(successful_processing/total_files*100):.1f}%" if total_files > 0 else "📈 Overall Success Rate: 0.0%")
        
        if successful_processing > 0:
            # Processing time analysis
            processing_times = [r.get('processing_time', 0) for r in self.test_results if r.get('processing_success')]
            avg_time = sum(processing_times) / len(processing_times)
            
            print(f"\n⏱️  Performance Analysis:")
            print(f"   Average Processing Time: {avg_time:.2f}s")
            print(f"   Fastest Processing: {min(processing_times):.2f}s")
            print(f"   Slowest Processing: {max(processing_times):.2f}s")
            
            # Data processing analysis
            total_emitentes = 0
            total_produtos = 0
            total_facts = 0
            
            for result in self.test_results:
                if result.get('processing_success'):
                    pipeline_result = result.get('pipeline_result', {})
                    summary = pipeline_result.get('summary', {})
                    
                    if summary.get('emitente_processed'):
                        total_emitentes += 1
                    total_produtos += summary.get('produtos_count', 0)
                    total_facts += summary.get('fact_records_count', 0)
            
            print(f"\n📊 Data Processing Analysis:")
            print(f"   Emitentes Processed: {total_emitentes}")
            print(f"   Products Processed: {total_produtos}")
            print(f"   Fact Records Created: {total_facts}")
            
            # Business insights
            print(f"\n💼 Business Insights:")
            companies_processed = []
            total_value = 0
            
            for doc in self.uploaded_documents:
                metadata = doc.get('metadata', {})
                if metadata.get('emitente_nome'):
                    companies_processed.append(metadata['emitente_nome'])
                if metadata.get('valor_total'):
                    total_value += metadata['valor_total']
            
            print(f"   Companies Processed: {len(set(companies_processed))}")
            print(f"   Total Document Value: R$ {total_value:,.2f}")
            
            if companies_processed:
                print(f"   Companies:")
                for company in sorted(set(companies_processed)):
                    print(f"     - {company}")
        
        # Failed processing analysis
        if failed_processing > 0:
            print(f"\n❌ Failed Processing Analysis:")
            for result in self.test_results:
                if not result.get('processing_success'):
                    print(f"   {result['filename']}: {result.get('error', 'Unknown error')}")
        
        # Database validation summary
        print(f"\n🗄️  Database Validation:")
        try:
            # Get current database state
            fiscal_docs = self.supabase_client.client.table('fiscal_documents').select('*', count='exact').execute()
            emitentes = self.supabase_client.client.table('dim_emitente').select('*', count='exact').execute()
            produtos = self.supabase_client.client.table('dim_produtos').select('*', count='exact').execute()
            fact_records = self.supabase_client.client.table('fact_itens_nfe').select('*', count='exact').execute()
            
            print(f"   Fiscal Documents: {fiscal_docs.count}")
            print(f"   Emitentes: {emitentes.count}")
            print(f"   Products: {produtos.count}")
            print(f"   Fact Records: {fact_records.count}")
            
        except Exception as e:
            print(f"   ⚠️  Database validation error: {str(e)}")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_dimensional_processing_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "test_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_files": total_files,
                    "successful_uploads": successful_uploads,
                    "successful_processing": successful_processing,
                    "failed_processing": failed_processing,
                    "success_rate": (successful_processing/total_files*100) if total_files > 0 else 0
                },
                "uploaded_documents": self.uploaded_documents,
                "test_results": self.test_results,
                "performance_metrics": {
                    "average_processing_time": avg_time if successful_processing > 0 else 0,
                    "total_processing_time": sum(processing_times) if successful_processing > 0 else 0
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("🚀 Real Dimensional Processing Test Suite")
    print("Complete workflow: Upload → Process → Validate")
    print("This test simulates the real production workflow")
    print()
    
    # Auto-proceed for automated testing
    print("Starting automated test execution...")
    
    tester = RealDimensionalTester()
    await tester.run_real_tests()


if __name__ == "__main__":
    asyncio.run(main())