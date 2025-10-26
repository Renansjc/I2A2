"""
End-to-end workflow test with real Brazilian fiscal documents
Task 4.3: Validate end-to-end workflow with real data
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

# Import agents
from agents.xml_processing_agent import LLMEnhancedXMLProcessingAgent
from agents.ai_categorization_agent import LLMEnhancedAICategorizationAgent


class EndToEndWorkflowTester:
    """End-to-end workflow tester for the AI Agents system"""
    
    def __init__(self):
        self.xml_processing_agent = LLMEnhancedXMLProcessingAgent()
        self.categorization_agent = LLMEnhancedAICategorizationAgent()
        self.test_results = []
        self.workflow_metrics = {
            'total_processing_time': 0,
            'documents_processed': 0,
            'items_categorized': 0,
            'insights_generated': 0,
            'anomalies_detected': 0,
            'business_validations': 0
        }
    
    async def run_end_to_end_tests(self):
        """Run complete end-to-end workflow tests"""
        print("🚀 Starting End-to-End Workflow Tests with Real Data")
        print("=" * 70)
        
        # Get XML files
        xml_files_dir = Path("../xml_nf")
        if not xml_files_dir.exists():
            print("❌ XML files directory not found")
            return
        
        xml_files = list(xml_files_dir.glob("*.xml")) + list(xml_files_dir.glob("*.XML"))
        
        if not xml_files:
            print("❌ No XML files found")
            return
        
        print(f"📁 Found {len(xml_files)} XML files for end-to-end testing")
        
        # Test each file through complete workflow
        for i, xml_file in enumerate(xml_files, 1):
            await self._test_complete_workflow(xml_file, i, len(xml_files))
        
        # Generate comprehensive report
        self._generate_comprehensive_report()
        
        print("\n🎉 End-to-End Workflow Tests Completed!")
    
    async def _test_complete_workflow(self, xml_file: Path, file_num: int, total_files: int):
        """Test complete workflow for a single XML file"""
        print(f"\n📄 Testing Complete Workflow {file_num}/{total_files}: {xml_file.name}")
        print("-" * 60)
        
        workflow_start_time = datetime.now()
        
        test_result = {
            "filename": xml_file.name,
            "file_size": xml_file.stat().st_size,
            "timestamp": workflow_start_time.isoformat(),
            "success": False,
            "workflow_stages": {},
            "total_processing_time": 0,
            "document_data": {},
            "categorization_data": {},
            "business_insights": [],
            "executive_summary": {},
            "errors": []
        }
        
        try:
            # Read XML content
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print(f"📊 File size: {test_result['file_size']:,} bytes")
            
            # Prepare context for workflow
            context = {
                'document_id': f"e2e_test_{xml_file.stem}",
                'document_type': 'NFE',
                'workflow_id': f"workflow_{file_num}",
                'test_mode': True
            }
            
            # Stage 1: XML Processing
            print("🔄 Stage 1: XML Document Processing...")
            stage1_start = datetime.now()
            
            xml_result = await self.xml_processing_agent.process_xml_document(xml_content, context)
            
            stage1_end = datetime.now()
            stage1_time = (stage1_end - stage1_start).total_seconds()
            
            test_result["workflow_stages"]["xml_processing"] = {
                "success": True,
                "processing_time": stage1_time,
                "result": xml_result
            }
            
            print(f"   ✅ XML Processing completed in {stage1_time:.2f}s")
            print(f"   📋 Document Type: {xml_result.get('document_type', 'Unknown')}")
            
            document_summary = xml_result.get('document_summary', {})
            print(f"   🏢 Supplier: {document_summary.get('supplier', 'N/A')}")
            print(f"   💰 Total Value: R$ {document_summary.get('total_value', 0):,.2f}")
            
            # Stage 2: AI Categorization
            print("\n🏷️  Stage 2: AI Categorization...")
            stage2_start = datetime.now()
            
            categorization_result = await self.categorization_agent.categorize_document(xml_content, context)
            
            stage2_end = datetime.now()
            stage2_time = (stage2_end - stage2_start).total_seconds()
            
            test_result["workflow_stages"]["ai_categorization"] = {
                "success": True,
                "processing_time": stage2_time,
                "result": categorization_result
            }
            
            print(f"   ✅ AI Categorization completed in {stage2_time:.2f}s")
            print(f"   📦 Items Categorized: {categorization_result.get('total_items', 0)}")
            print(f"   🏷️  Unique Categories: {categorization_result.get('unique_categories', 0)}")
            
            # Stage 3: Business Intelligence Analysis
            print("\n🧠 Stage 3: Business Intelligence Analysis...")
            stage3_start = datetime.now()
            
            business_analysis = await self._perform_business_analysis(xml_result, categorization_result)
            
            stage3_end = datetime.now()
            stage3_time = (stage3_end - stage3_start).total_seconds()
            
            test_result["workflow_stages"]["business_analysis"] = {
                "success": True,
                "processing_time": stage3_time,
                "result": business_analysis
            }
            
            print(f"   ✅ Business Analysis completed in {stage3_time:.2f}s")
            print(f"   💡 Business Insights: {len(business_analysis.get('insights', []))}")
            print(f"   📊 Risk Score: {business_analysis.get('risk_score', 0):.2f}")
            
            # Stage 4: Executive Reporting
            print("\n📋 Stage 4: Executive Report Generation...")
            stage4_start = datetime.now()
            
            executive_report = await self._generate_executive_report(xml_result, categorization_result, business_analysis)
            
            stage4_end = datetime.now()
            stage4_time = (stage4_end - stage4_start).total_seconds()
            
            test_result["workflow_stages"]["executive_reporting"] = {
                "success": True,
                "processing_time": stage4_time,
                "result": executive_report
            }
            
            print(f"   ✅ Executive Report generated in {stage4_time:.2f}s")
            print(f"   📈 Key Metrics: {len(executive_report.get('key_metrics', []))}")
            print(f"   🎯 Recommendations: {len(executive_report.get('recommendations', []))}")
            
            # Stage 5: Database Storage Simulation
            print("\n💾 Stage 5: Database Storage Simulation...")
            stage5_start = datetime.now()
            
            storage_result = await self._simulate_database_storage(xml_result, categorization_result, business_analysis, executive_report)
            
            stage5_end = datetime.now()
            stage5_time = (stage5_end - stage5_start).total_seconds()
            
            test_result["workflow_stages"]["database_storage"] = {
                "success": True,
                "processing_time": stage5_time,
                "result": storage_result
            }
            
            print(f"   ✅ Database Storage simulated in {stage5_time:.2f}s")
            print(f"   🗄️  Records Created: {storage_result.get('records_created', 0)}")
            
            # Calculate total workflow time
            workflow_end_time = datetime.now()
            total_workflow_time = (workflow_end_time - workflow_start_time).total_seconds()
            
            # Update test result
            test_result.update({
                "success": True,
                "total_processing_time": total_workflow_time,
                "document_data": xml_result,
                "categorization_data": categorization_result,
                "business_insights": business_analysis.get('insights', []),
                "executive_summary": executive_report
            })
            
            # Update metrics
            self.workflow_metrics['total_processing_time'] += total_workflow_time
            self.workflow_metrics['documents_processed'] += 1
            self.workflow_metrics['items_categorized'] += categorization_result.get('total_items', 0)
            self.workflow_metrics['insights_generated'] += len(business_analysis.get('insights', []))
            self.workflow_metrics['anomalies_detected'] += len(xml_result.get('anomalies', []))
            self.workflow_metrics['business_validations'] += len(xml_result.get('business_validation', {}))
            
            print(f"\n✅ Complete Workflow finished in {total_workflow_time:.2f}s")
            
        except Exception as e:
            test_result["errors"].append(str(e))
            print(f"❌ Workflow failed: {str(e)}")
            logger.error("End-to-end workflow failed", filename=xml_file.name, error=str(e))
        
        self.test_results.append(test_result)
    
    async def _perform_business_analysis(self, xml_result: Dict[str, Any], categorization_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform business intelligence analysis"""
        try:
            document_summary = xml_result.get('document_summary', {})
            total_value = document_summary.get('total_value', 0)
            supplier = document_summary.get('supplier', 'Unknown')
            
            # Calculate risk score
            risk_score = 0.0
            risk_factors = []
            
            # Value-based risk
            if total_value > 10000:
                risk_score += 0.3
                risk_factors.append("High value transaction")
            elif total_value > 1000:
                risk_score += 0.1
                risk_factors.append("Medium value transaction")
            
            # Anomaly-based risk
            anomalies = xml_result.get('anomalies', [])
            if anomalies:
                risk_score += len(anomalies) * 0.2
                risk_factors.extend(anomalies)
            
            # Category diversity analysis
            unique_categories = categorization_result.get('unique_categories', 0)
            if unique_categories > 3:
                risk_factors.append("High category diversity")
            
            # Generate business insights
            insights = []
            
            # Supplier analysis
            insights.append({
                "type": "supplier_analysis",
                "description": f"Transação com fornecedor: {supplier}",
                "value": total_value,
                "recommendation": "Monitorar histórico de transações com este fornecedor"
            })
            
            # Value analysis
            if total_value > 5000:
                insights.append({
                    "type": "high_value_alert",
                    "description": f"Transação de alto valor detectada: R$ {total_value:,.2f}",
                    "recommendation": "Revisar aprovações e documentação adicional"
                })
            
            # Category analysis
            if unique_categories > 1:
                insights.append({
                    "type": "category_diversity",
                    "description": f"Documento com {unique_categories} categorias diferentes",
                    "recommendation": "Verificar se todas as categorias são apropriadas para este fornecedor"
                })
            
            return {
                "risk_score": min(risk_score, 1.0),  # Cap at 1.0
                "risk_factors": risk_factors,
                "insights": insights,
                "analysis_timestamp": datetime.now().isoformat(),
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.warning("Business analysis failed", error=str(e))
            return {"error": str(e)}
    
    async def _generate_executive_report(self, xml_result: Dict[str, Any], categorization_result: Dict[str, Any], business_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive-level report"""
        try:
            document_summary = xml_result.get('document_summary', {})
            
            # Key metrics
            key_metrics = [
                {
                    "metric": "Document Value",
                    "value": f"R$ {document_summary.get('total_value', 0):,.2f}",
                    "status": "normal"
                },
                {
                    "metric": "Risk Score",
                    "value": f"{business_analysis.get('risk_score', 0):.2f}",
                    "status": "high" if business_analysis.get('risk_score', 0) > 0.7 else "normal"
                },
                {
                    "metric": "Categories",
                    "value": str(categorization_result.get('unique_categories', 0)),
                    "status": "normal"
                },
                {
                    "metric": "Items",
                    "value": str(categorization_result.get('total_items', 0)),
                    "status": "normal"
                }
            ]
            
            # Executive summary
            executive_summary = f"""
            Documento fiscal processado com sucesso. 
            Fornecedor: {document_summary.get('supplier', 'N/A')}
            Valor total: R$ {document_summary.get('total_value', 0):,.2f}
            Risco calculado: {business_analysis.get('risk_score', 0):.2f}
            """
            
            # Recommendations
            recommendations = []
            
            risk_score = business_analysis.get('risk_score', 0)
            if risk_score > 0.7:
                recommendations.append("Revisão executiva recomendada devido ao alto risco")
            elif risk_score > 0.3:
                recommendations.append("Monitoramento adicional recomendado")
            else:
                recommendations.append("Documento dentro dos parâmetros normais")
            
            # Add category-specific recommendations
            unique_categories = categorization_result.get('unique_categories', 0)
            if unique_categories > 2:
                recommendations.append("Verificar diversidade de categorias com o departamento de compras")
            
            return {
                "executive_summary": executive_summary.strip(),
                "key_metrics": key_metrics,
                "recommendations": recommendations,
                "report_timestamp": datetime.now().isoformat(),
                "document_id": xml_result.get('document_summary', {}).get('document_key', 'Unknown'),
                "approval_required": risk_score > 0.5
            }
            
        except Exception as e:
            logger.warning("Executive report generation failed", error=str(e))
            return {"error": str(e)}
    
    async def _simulate_database_storage(self, xml_result: Dict[str, Any], categorization_result: Dict[str, Any], business_analysis: Dict[str, Any], executive_report: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate database storage operations"""
        try:
            records_created = 0
            
            # Simulate storing document metadata
            records_created += 1
            
            # Simulate storing categorized items
            records_created += categorization_result.get('total_items', 0)
            
            # Simulate storing business insights
            records_created += len(business_analysis.get('insights', []))
            
            # Simulate storing executive report
            records_created += 1
            
            return {
                "records_created": records_created,
                "storage_timestamp": datetime.now().isoformat(),
                "database_status": "simulated_success"
            }
            
        except Exception as e:
            logger.warning("Database storage simulation failed", error=str(e))
            return {"error": str(e)}
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive end-to-end test report"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE END-TO-END WORKFLOW REPORT")
        print("=" * 70)
        
        total_files = len(self.test_results)
        successful_files = sum(1 for r in self.test_results if r.get("success", False))
        failed_files = total_files - successful_files
        
        print(f"📁 Total Files Tested: {total_files}")
        print(f"✅ Successful Workflows: {successful_files}")
        print(f"❌ Failed Workflows: {failed_files}")
        print(f"📈 Success Rate: {(successful_files/total_files*100):.1f}%")
        
        if successful_files > 0:
            # Performance metrics
            avg_processing_time = self.workflow_metrics['total_processing_time'] / successful_files
            
            print(f"\n⏱️  Performance Metrics:")
            print(f"   Total Processing Time: {self.workflow_metrics['total_processing_time']:.2f}s")
            print(f"   Average per Document: {avg_processing_time:.2f}s")
            print(f"   Documents Processed: {self.workflow_metrics['documents_processed']}")
            print(f"   Items Categorized: {self.workflow_metrics['items_categorized']}")
            print(f"   Insights Generated: {self.workflow_metrics['insights_generated']}")
            print(f"   Anomalies Detected: {self.workflow_metrics['anomalies_detected']}")
            
            # Stage performance analysis
            stage_times = {}
            for result in self.test_results:
                if result.get("success"):
                    for stage, data in result.get("workflow_stages", {}).items():
                        if stage not in stage_times:
                            stage_times[stage] = []
                        stage_times[stage].append(data.get("processing_time", 0))
            
            print(f"\n🔄 Stage Performance Analysis:")
            for stage, times in stage_times.items():
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                print(f"   {stage.replace('_', ' ').title()}:")
                print(f"     Average: {avg_time:.2f}s, Max: {max_time:.2f}s, Min: {min_time:.2f}s")
            
            # Business insights analysis
            all_insights = []
            risk_scores = []
            
            for result in self.test_results:
                if result.get("success"):
                    all_insights.extend(result.get("business_insights", []))
                    
                    # Extract risk score from business analysis
                    business_stage = result.get("workflow_stages", {}).get("business_analysis", {})
                    if business_stage.get("success"):
                        risk_score = business_stage.get("result", {}).get("risk_score", 0)
                        risk_scores.append(risk_score)
            
            print(f"\n🧠 Business Intelligence Analysis:")
            print(f"   Total Business Insights: {len(all_insights)}")
            if successful_files > 0:
                print(f"   Average Insights per Document: {len(all_insights)/successful_files:.1f}")
            
            if risk_scores:
                avg_risk = sum(risk_scores) / len(risk_scores)
                max_risk = max(risk_scores)
                high_risk_docs = sum(1 for r in risk_scores if r > 0.7)
                
                print(f"   Average Risk Score: {avg_risk:.2f}")
                print(f"   Maximum Risk Score: {max_risk:.2f}")
                print(f"   High Risk Documents: {high_risk_docs}")
            
            # Executive reporting analysis
            approval_required = 0
            for result in self.test_results:
                if result.get("success"):
                    exec_summary = result.get("executive_summary", {})
                    if exec_summary.get("approval_required", False):
                        approval_required += 1
            
            print(f"\n📋 Executive Reporting Analysis:")
            print(f"   Documents Requiring Approval: {approval_required}")
            print(f"   Approval Rate: {(approval_required/successful_files*100):.1f}%")
        
        # Failed workflows analysis
        if failed_files > 0:
            print(f"\n❌ Failed Workflows Analysis:")
            for result in self.test_results:
                if not result.get("success"):
                    print(f"   {result['filename']}: {', '.join(result.get('errors', ['Unknown error']))}")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"end_to_end_workflow_results_{timestamp}.json"
        
        try:
            comprehensive_results = {
                "test_results": self.test_results,
                "workflow_metrics": self.workflow_metrics,
                "summary": {
                    "total_files": total_files,
                    "successful_files": successful_files,
                    "failed_files": failed_files,
                    "success_rate": (successful_files/total_files*100) if total_files > 0 else 0
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Comprehensive results saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️  Could not save results to file: {str(e)}")


async def main():
    """Main test execution"""
    print("🧪 End-to-End Workflow Test Suite")
    print("=" * 70)
    
    tester = EndToEndWorkflowTester()
    await tester.run_end_to_end_tests()


if __name__ == "__main__":
    asyncio.run(main())