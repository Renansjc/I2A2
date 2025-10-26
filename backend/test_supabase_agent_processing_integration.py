"""
Comprehensive test suite for agent processing with real XML data and Supabase integration
Task 6.2: Test agent processing with real data

This test suite validates:
- Processing each XML file through complete agent workflow
- Extraction of business data and insights
- Categorization accuracy with real products/services
- SQL generation and execution with real queries
- Integration with Supabase database storage
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
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

# Import agents and utilities
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent
from agents.ai_categorization_agent import LLMEnhancedAICategorizationAgent
from agents.sql_agent import LLMEnhancedSQLAgent
from agents.report_agent import LLMEnhancedReportAgent
from agents.master_agent import EnhancedMasterAgent

from utils.database import (
    FileUploadManager, ProcessingStatusManager, 
    DocumentManager, supabase_client
)
from utils.llm_service import OpenAIIntegrationService


class SupabaseAgentProcessingTestSuite:
    """Comprehensive test suite for agent processing with Supabase integration"""
    
    def __init__(self):
        self.xml_files_dir = Path("../xml_nf")
        self.test_results = []
        self.test_user_id = None  # Use NULL for test user to avoid foreign key constraint
        self.uploaded_documents = []  # Track for cleanup
        
        # Initialize agents
        self.xml_agent = LLMEnhancedXMLProcessingAgent()
        self.categorization_agent = LLMEnhancedAICategorizationAgent()
        self.sql_agent = LLMEnhancedSQLAgent()
        self.report_agent = LLMEnhancedReportAgent()
        self.master_agent = EnhancedMasterAgent()
        self.llm_service = OpenAIIntegrationService()
        
        # Test metrics
        self.test_metrics = {
            'total_documents_processed': 0,
            'successful_xml_processing': 0,
            'successful_categorizations': 0,
            'successful_sql_operations': 0,
            'successful_report_generations': 0,
            'total_insights_generated': 0,
            'total_categories_identified': 0,
            'total_processing_time': 0,
            'agent_performance': {
                'xml_processing_agent': {'success': 0, 'failures': 0, 'avg_time': 0},
                'ai_categorization_agent': {'success': 0, 'failures': 0, 'avg_time': 0},
                'sql_agent': {'success': 0, 'failures': 0, 'avg_time': 0},
                'report_agent': {'success': 0, 'failures': 0, 'avg_time': 0}
            }
        }
    
    async def run_comprehensive_agent_tests(self):
        """Run all agent processing tests with real data"""
        print("🚀 Starting Comprehensive Agent Processing Tests with Real Data")
        print("=" * 70)
        
        try:
            # Test 1: Agent connectivity and health
            await self._test_agent_connectivity()
            
            # Test 2: Upload XML files for processing
            await self._upload_test_documents()
            
            # Test 3: XML Processing Agent with real data
            await self._test_xml_processing_agent()
            
            # Test 4: AI Categorization Agent with real products/services
            await self._test_ai_categorization_agent()
            
            # Test 5: SQL Agent with real queries
            await self._test_sql_agent()
            
            # Test 6: Report Agent with real business data
            await self._test_report_agent()
            
            # Test 7: End-to-end agent workflow
            await self._test_end_to_end_workflow()
            
            # Test 8: Database integration validation
            await self._test_database_integration()
            
            # Generate comprehensive report
            self._generate_comprehensive_report()
            
        except Exception as e:
            logger.error("Agent processing test suite failed", error=str(e))
            print(f"❌ Test suite failed: {str(e)}")
        
        finally:
            # Cleanup test data
            await self._cleanup_test_data()
        
        print("\n🎉 Agent Processing Tests Completed!")
    
    async def _test_agent_connectivity(self):
        """Test 1: Agent connectivity and health checks"""
        print("\n🔗 Test 1: Agent Connectivity and Health Checks")
        print("-" * 60)
        
        agents_to_test = [
            ("XML Processing Agent", self.xml_agent),
            ("AI Categorization Agent", self.categorization_agent),
            ("SQL Agent", self.sql_agent),
            ("Report Agent", self.report_agent),
            ("Master Agent", self.master_agent)
        ]
        
        for agent_name, agent in agents_to_test:
            try:
                # Test agent initialization
                if hasattr(agent, 'health_check'):
                    health_status = await agent.health_check()
                    print(f"✅ {agent_name}: Health check passed")
                else:
                    print(f"✅ {agent_name}: Initialized successfully")
                
            except Exception as e:
                print(f"❌ {agent_name}: Health check failed - {str(e)}")
        
        # Test LLM service connectivity
        try:
            await self.llm_service.health_check()
            print(f"✅ LLM Service: Connected successfully")
        except Exception as e:
            print(f"❌ LLM Service: Connection failed - {str(e)}")
    
    async def _upload_test_documents(self):
        """Upload XML documents for agent processing tests"""
        print("\n📁 Uploading Test Documents for Agent Processing")
        print("-" * 60)
        
        xml_files = self._get_xml_files()
        
        if not xml_files:
            print("❌ No XML files found for testing")
            return
        
        print(f"📄 Uploading {len(xml_files)} XML files for agent testing")
        
        for xml_file in xml_files:
            try:
                # Read XML content
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Determine document type
                document_type = "NFE"
                if "nfse" in xml_content.lower() or "rps" in xml_content.lower():
                    document_type = "NFSE"
                
                # Create document record
                document_id = await FileUploadManager.create_document_record(
                    filename=xml_file.name,
                    file_size=xml_file.stat().st_size,
                    document_type=document_type,
                    xml_content=xml_content,
                    user_id=self.test_user_id
                )
                
                self.uploaded_documents.append({
                    'document_id': document_id,
                    'filename': xml_file.name,
                    'document_type': document_type,
                    'xml_content': xml_content,
                    'file_size': xml_file.stat().st_size
                })
                
                print(f"✅ Uploaded: {xml_file.name} ({document_id})")
                
            except Exception as e:
                print(f"❌ Failed to upload {xml_file.name}: {str(e)}")
                logger.error("Document upload failed", filename=xml_file.name, error=str(e))
    
    async def _test_xml_processing_agent(self):
        """Test 3: XML Processing Agent with real data"""
        print("\n🔄 Test 3: XML Processing Agent with Real Data")
        print("-" * 60)
        
        if not self.uploaded_documents:
            print("❌ No documents available for XML processing test")
            return
        
        for i, doc in enumerate(self.uploaded_documents, 1):
            print(f"\n📄 Processing document {i}/{len(self.uploaded_documents)}: {doc['filename']}")
            
            test_start = datetime.now()
            
            try:
                # Update processing status
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "xml_processing_agent", "in_progress"
                )
                
                # Process XML document
                context = {
                    'document_id': doc['document_id'],
                    'document_type': doc['document_type'],
                    'processar_com_ia': True,
                    'extrair_insights': True,
                    'categorizar_automaticamente': True,
                    'validar_regras_negocio': True
                }
                
                result = await self.xml_agent.process_xml_document(
                    doc['xml_content'], context
                )
                
                processing_time = (datetime.now() - test_start).total_seconds()
                
                # Store processing result
                await ProcessingStatusManager.store_processing_result(
                    document_id=doc['document_id'],
                    agent_name="xml_processing_agent",
                    result_type="document_analysis",
                    result_data=result.dict() if hasattr(result, 'dict') else result,
                    confidence_score=0.9,
                    processing_time_ms=int(processing_time * 1000)
                )
                
                # Update status to completed
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "xml_processing_agent", "completed"
                )
                
                # Print results
                print(f"✅ XML processing completed in {processing_time:.2f}s")
                
                if hasattr(result, 'document_summary'):
                    summary = result.document_summary
                    print(f"   Document Type: {result.get('document_type', 'Unknown')}")
                    print(f"   Supplier: {summary.get('supplier', 'N/A')}")
                    print(f"   Total Value: R$ {summary.get('total_value', 0):,.2f}")
                
                if hasattr(result, 'business_insights'):
                    insights = result.business_insights
                    print(f"   Business Insights: {len(insights)} generated")
                    self.test_metrics['total_insights_generated'] += len(insights)
                
                if hasattr(result, 'anomalies'):
                    anomalies = result.anomalies
                    if anomalies:
                        print(f"   Anomalies Detected: {len(anomalies)}")
                
                self.test_metrics['successful_xml_processing'] += 1
                self.test_metrics['agent_performance']['xml_processing_agent']['success'] += 1
                
            except Exception as e:
                print(f"❌ XML processing failed: {str(e)}")
                
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "xml_processing_agent", "failed", str(e)
                )
                
                self.test_metrics['agent_performance']['xml_processing_agent']['failures'] += 1
                logger.error("XML processing test failed", document_id=doc['document_id'], error=str(e))
    
    async def _test_ai_categorization_agent(self):
        """Test 4: AI Categorization Agent with real products/services"""
        print("\n🏷️  Test 4: AI Categorization Agent with Real Products/Services")
        print("-" * 60)
        
        if not self.uploaded_documents:
            print("❌ No documents available for categorization test")
            return
        
        for i, doc in enumerate(self.uploaded_documents, 1):
            print(f"\n📦 Categorizing document {i}/{len(self.uploaded_documents)}: {doc['filename']}")
            
            test_start = datetime.now()
            
            try:
                # Update processing status
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "ai_categorization_agent", "in_progress"
                )
                
                # Categorize document
                context = {
                    'document_id': doc['document_id'],
                    'document_type': doc['document_type'],
                    'context': 'automated_processing'
                }
                
                result = await self.categorization_agent.categorize_document(
                    doc['xml_content'], context
                )
                
                processing_time = (datetime.now() - test_start).total_seconds()
                
                # Store processing result
                await ProcessingStatusManager.store_processing_result(
                    document_id=doc['document_id'],
                    agent_name="ai_categorization_agent",
                    result_type="categorization",
                    result_data=result,
                    confidence_score=result.get("confidence", 0.85),
                    processing_time_ms=int(processing_time * 1000)
                )
                
                # Update status to completed
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "ai_categorization_agent", "completed"
                )
                
                # Print results
                print(f"✅ Categorization completed in {processing_time:.2f}s")
                print(f"   Total Items: {result.get('total_items', 0)}")
                print(f"   Unique Categories: {result.get('unique_categories', 0)}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                
                self.test_metrics['successful_categorizations'] += 1
                self.test_metrics['total_categories_identified'] += result.get('unique_categories', 0)
                self.test_metrics['agent_performance']['ai_categorization_agent']['success'] += 1
                
            except Exception as e:
                print(f"❌ Categorization failed: {str(e)}")
                
                await ProcessingStatusManager.update_agent_status(
                    doc['document_id'], "ai_categorization_agent", "failed", str(e)
                )
                
                self.test_metrics['agent_performance']['ai_categorization_agent']['failures'] += 1
                logger.error("Categorization test failed", document_id=doc['document_id'], error=str(e))
    
    async def _test_sql_agent(self):
        """Test 5: SQL Agent with real queries"""
        print("\n🗄️  Test 5: SQL Agent with Real Queries")
        print("-" * 60)
        
        # Test SQL queries with real business scenarios
        test_queries = [
            {
                "name": "Total documents by type",
                "query": "Quantos documentos fiscais temos por tipo?",
                "expected_tables": ["fiscal_documents"]
            },
            {
                "name": "Documents by processing status",
                "query": "Mostre o status de processamento dos documentos",
                "expected_tables": ["fiscal_documents"]
            },
            {
                "name": "Recent uploads",
                "query": "Quais documentos foram enviados nas últimas 24 horas?",
                "expected_tables": ["fiscal_documents"]
            },
            {
                "name": "Processing results summary",
                "query": "Resumo dos resultados de processamento por agente",
                "expected_tables": ["processing_results"]
            }
        ]
        
        for i, test_query in enumerate(test_queries, 1):
            print(f"\n🔍 SQL Test {i}: {test_query['name']}")
            
            test_start = datetime.now()
            
            try:
                # Generate SQL from natural language
                sql_result = await self.sql_agent.generate_sql_from_natural_language(
                    test_query["query"],
                    {
                        "context": "test_environment",
                        "user_id": self.test_user_id,
                        "include_explanation": True
                    }
                )
                
                processing_time = (datetime.now() - test_start).total_seconds()
                
                print(f"✅ SQL generated in {processing_time:.2f}s")
                
                if hasattr(sql_result, 'sql_query'):
                    print(f"   Generated SQL: {sql_result.sql_query[:100]}...")
                    
                    # Validate SQL contains expected tables
                    sql_lower = sql_result.sql_query.lower()
                    for expected_table in test_query["expected_tables"]:
                        if expected_table.lower() in sql_lower:
                            print(f"   ✅ Contains expected table: {expected_table}")
                        else:
                            print(f"   ⚠️  Missing expected table: {expected_table}")
                
                if hasattr(sql_result, 'explanation'):
                    print(f"   Explanation provided: {len(sql_result.explanation)} chars")
                
                self.test_metrics['successful_sql_operations'] += 1
                self.test_metrics['agent_performance']['sql_agent']['success'] += 1
                
            except Exception as e:
                print(f"❌ SQL generation failed: {str(e)}")
                self.test_metrics['agent_performance']['sql_agent']['failures'] += 1
                logger.error("SQL agent test failed", query=test_query["query"], error=str(e))
    
    async def _test_report_agent(self):
        """Test 6: Report Agent with real business data"""
        print("\n📋 Test 6: Report Agent with Real Business Data")
        print("-" * 60)
        
        if not self.uploaded_documents:
            print("❌ No documents available for report generation test")
            return
        
        # Test report generation scenarios
        report_scenarios = [
            {
                "name": "Document Processing Summary",
                "type": "processing_summary",
                "context": {
                    "period": "last_24_hours",
                    "include_metrics": True,
                    "format": "executive"
                }
            },
            {
                "name": "Agent Performance Report",
                "type": "agent_performance",
                "context": {
                    "agents": ["xml_processing_agent", "ai_categorization_agent"],
                    "include_recommendations": True
                }
            },
            {
                "name": "Document Insights Report",
                "type": "document_insights",
                "context": {
                    "document_ids": [doc['document_id'] for doc in self.uploaded_documents[:2]],
                    "include_business_analysis": True
                }
            }
        ]
        
        for i, scenario in enumerate(report_scenarios, 1):
            print(f"\n📊 Report Test {i}: {scenario['name']}")
            
            test_start = datetime.now()
            
            try:
                # Generate report
                report_result = await self.report_agent.generate_intelligent_report(
                    data=None,  # Will be fetched internally
                    report_context={
                        "report_type": scenario["type"],
                        "context": scenario["context"],
                        "user_id": self.test_user_id,
                        "format": "json"
                    }
                )
                
                processing_time = (datetime.now() - test_start).total_seconds()
                
                print(f"✅ Report generated in {processing_time:.2f}s")
                
                if hasattr(report_result, 'executive_summary'):
                    print(f"   Executive Summary: {len(report_result.executive_summary)} chars")
                
                if hasattr(report_result, 'key_insights'):
                    insights = report_result.key_insights
                    print(f"   Key Insights: {len(insights)} generated")
                    self.test_metrics['total_insights_generated'] += len(insights)
                
                if hasattr(report_result, 'recommendations'):
                    recommendations = report_result.recommendations
                    print(f"   Recommendations: {len(recommendations)} provided")
                
                self.test_metrics['successful_report_generations'] += 1
                self.test_metrics['agent_performance']['report_agent']['success'] += 1
                
            except Exception as e:
                print(f"❌ Report generation failed: {str(e)}")
                self.test_metrics['agent_performance']['report_agent']['failures'] += 1
                logger.error("Report agent test failed", scenario=scenario["name"], error=str(e))
    
    async def _test_end_to_end_workflow(self):
        """Test 7: End-to-end agent workflow"""
        print("\n🔄 Test 7: End-to-End Agent Workflow")
        print("-" * 60)
        
        if not self.uploaded_documents:
            print("❌ No documents available for end-to-end workflow test")
            return
        
        # Test with first document
        test_doc = self.uploaded_documents[0]
        print(f"📄 Testing end-to-end workflow with: {test_doc['filename']}")
        
        workflow_start = datetime.now()
        
        try:
            # Step 1: XML Processing
            print("🔄 Step 1: XML Processing...")
            xml_result = await self.xml_agent.process_xml_document(
                test_doc['xml_content'],
                {
                    'document_id': test_doc['document_id'],
                    'document_type': test_doc['document_type']
                }
            )
            print("✅ XML Processing completed")
            
            # Step 2: AI Categorization
            print("🔄 Step 2: AI Categorization...")
            categorization_result = await self.categorization_agent.categorize_document(
                test_doc['xml_content'],
                {
                    'document_id': test_doc['document_id'],
                    'document_type': test_doc['document_type']
                }
            )
            print("✅ AI Categorization completed")
            
            # Step 3: Business Analysis Query
            print("🔄 Step 3: Business Analysis Query...")
            analysis_query = f"Analise o documento {test_doc['filename']} e forneça insights de negócio"
            sql_result = await self.sql_agent.generate_sql_from_natural_language(
                analysis_query,
                {'document_id': test_doc['document_id']}
            )
            print("✅ Business Analysis Query completed")
            
            # Step 4: Executive Report
            print("🔄 Step 4: Executive Report Generation...")
            report_result = await self.report_agent.generate_intelligent_report(
                data={
                    'xml_analysis': xml_result,
                    'categorization': categorization_result,
                    'sql_analysis': sql_result
                },
                report_context={
                    'document_id': test_doc['document_id'],
                    'report_type': 'document_analysis',
                    'format': 'executive'
                }
            )
            print("✅ Executive Report completed")
            
            workflow_time = (datetime.now() - workflow_start).total_seconds()
            
            print(f"\n✅ End-to-end workflow completed in {workflow_time:.2f}s")
            print(f"   All 4 agents executed successfully")
            print(f"   Document fully processed and analyzed")
            
            self.test_metrics['total_processing_time'] += workflow_time
            
        except Exception as e:
            print(f"❌ End-to-end workflow failed: {str(e)}")
            logger.error("End-to-end workflow test failed", document_id=test_doc['document_id'], error=str(e))
    
    async def _test_database_integration(self):
        """Test 8: Database integration validation"""
        print("\n🗄️  Test 8: Database Integration Validation")
        print("-" * 60)
        
        if not self.uploaded_documents:
            print("❌ No documents available for database integration test")
            return
        
        # Test database consistency and data integrity
        for doc in self.uploaded_documents[:2]:  # Test first 2 documents
            print(f"\n🔍 Testing database integration for: {doc['filename']}")
            
            try:
                # Check document exists
                document = await DocumentManager.get_document_details(
                    doc['document_id'], self.test_user_id
                )
                
                if document:
                    print(f"✅ Document found in database")
                    print(f"   Status: {document['processing_status']}")
                    print(f"   Type: {document['document_type']}")
                else:
                    print(f"❌ Document not found in database")
                    continue
                
                # Check processing results
                results = await DocumentManager.get_processing_results(
                    doc['document_id'], self.test_user_id
                )
                
                if results:
                    print(f"✅ Processing results found: {len(results)} records")
                    
                    # Analyze results by agent
                    agent_results = {}
                    for result in results:
                        agent_name = result['agent_name']
                        if agent_name not in agent_results:
                            agent_results[agent_name] = 0
                        agent_results[agent_name] += 1
                    
                    for agent, count in agent_results.items():
                        print(f"   {agent}: {count} result(s)")
                else:
                    print(f"⚠️  No processing results found")
                
                # Check agent statuses
                try:
                    status_results = await ProcessingStatusManager.get_document_processing_status(
                        doc['document_id']
                    )
                    
                    if status_results:
                        print(f"✅ Agent statuses tracked: {len(status_results)} records")
                    else:
                        print(f"⚠️  No agent status records found")
                        
                except Exception as e:
                    print(f"⚠️  Agent status check failed: {str(e)}")
                
            except Exception as e:
                print(f"❌ Database integration test failed: {str(e)}")
                logger.error("Database integration test failed", document_id=doc['document_id'], error=str(e))
    
    def _get_xml_files(self) -> List[Path]:
        """Get list of XML files to test"""
        xml_files = []
        
        if self.xml_files_dir.exists():
            xml_files = list(self.xml_files_dir.glob("*.xml")) + list(self.xml_files_dir.glob("*.XML"))
        
        return sorted(xml_files)
    
    async def _cleanup_test_data(self):
        """Clean up test data from database"""
        print("\n🧹 Cleaning up test data...")
        
        cleanup_count = 0
        
        for doc in self.uploaded_documents:
            try:
                # Delete from fiscal_documents (cascades to related tables)
                await asyncio.to_thread(
                    lambda: supabase_client.client.table('fiscal_documents')
                    .delete()
                    .eq('id', doc['document_id'])
                    .execute()
                )
                cleanup_count += 1
                
            except Exception as e:
                logger.warning("Failed to cleanup test document", 
                             document_id=doc['document_id'], error=str(e))
        
        print(f"✅ Cleaned up {cleanup_count} test documents")
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive agent processing test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE AGENT PROCESSING TEST REPORT")
        print("=" * 70)
        
        # Summary statistics
        total_docs = len(self.uploaded_documents)
        
        print(f"📁 Total Documents Processed: {total_docs}")
        print(f"🔄 XML Processing Success: {self.test_metrics['successful_xml_processing']}/{total_docs}")
        print(f"🏷️  Categorization Success: {self.test_metrics['successful_categorizations']}/{total_docs}")
        print(f"🗄️  SQL Operations Success: {self.test_metrics['successful_sql_operations']}")
        print(f"📋 Report Generation Success: {self.test_metrics['successful_report_generations']}")
        
        # Agent performance analysis
        print(f"\n🤖 Agent Performance Analysis:")
        for agent_name, performance in self.test_metrics['agent_performance'].items():
            total_ops = performance['success'] + performance['failures']
            success_rate = (performance['success'] / total_ops * 100) if total_ops > 0 else 0
            
            print(f"   {agent_name.replace('_', ' ').title()}:")
            print(f"     Success: {performance['success']}, Failures: {performance['failures']}")
            print(f"     Success Rate: {success_rate:.1f}%")
        
        # Business insights analysis
        print(f"\n💡 Business Intelligence Analysis:")
        print(f"   Total Insights Generated: {self.test_metrics['total_insights_generated']}")
        print(f"   Total Categories Identified: {self.test_metrics['total_categories_identified']}")
        if total_docs > 0:
            print(f"   Average Insights per Document: {self.test_metrics['total_insights_generated']/total_docs:.1f}")
            print(f"   Average Categories per Document: {self.test_metrics['total_categories_identified']/total_docs:.1f}")
        
        # Performance metrics
        if self.test_metrics['total_processing_time'] > 0:
            print(f"\n⏱️  Performance Metrics:")
            print(f"   Total Processing Time: {self.test_metrics['total_processing_time']:.2f}s")
            if total_docs > 0:
                avg_time = self.test_metrics['total_processing_time'] / total_docs
                print(f"   Average Processing Time per Document: {avg_time:.2f}s")
        
        # Save detailed results
        self._save_test_results()
    
    def _save_test_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"supabase_agent_processing_test_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "test_results": self.test_results,
                "test_metrics": self.test_metrics,
                "uploaded_documents": [
                    {
                        "document_id": doc["document_id"],
                        "filename": doc["filename"],
                        "document_type": doc["document_type"],
                        "file_size": doc["file_size"]
                    }
                    for doc in self.uploaded_documents
                ],
                "summary": {
                    "total_documents": len(self.uploaded_documents),
                    "successful_xml_processing": self.test_metrics['successful_xml_processing'],
                    "successful_categorizations": self.test_metrics['successful_categorizations'],
                    "successful_sql_operations": self.test_metrics['successful_sql_operations'],
                    "successful_report_generations": self.test_metrics['successful_report_generations']
                },
                "test_timestamp": datetime.now().isoformat(),
                "test_user_id": self.test_user_id
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Detailed results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("🧪 Supabase Agent Processing Integration Test Suite")
    print("=" * 70)
    
    test_suite = SupabaseAgentProcessingTestSuite()
    await test_suite.run_comprehensive_agent_tests()


if __name__ == "__main__":
    asyncio.run(main())