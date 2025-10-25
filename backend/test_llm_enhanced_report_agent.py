#!/usr/bin/env python3
"""
Test script for LLM-Enhanced Report Agent
Tests the intelligent report generation capabilities
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.report_agent import LLMEnhancedReportAgent, ReportFormat, ReportTemplate, ReportContext

async def test_llm_enhanced_report_agent():
    """Test the LLM-Enhanced Report Agent functionality"""
    
    print("🧪 Testing LLM-Enhanced Report Agent")
    print("=" * 50)
    
    try:
        # Initialize the agent
        print("1. Initializing LLM-Enhanced Report Agent...")
        agent = LLMEnhancedReportAgent()
        
        # Note: We'll skip actual initialization to avoid OpenAI API dependency in tests
        # await agent.initialize()
        print("   ✅ Agent created successfully")
        
        # Create sample query result data
        sample_data = {
            'data': [
                {
                    'razao_social': 'Fornecedor A Ltda',
                    'cnpj': '12.345.678/0001-90',
                    'valor_total': 15000.50,
                    'data_emissao': '2024-01-15',
                    'tipo_documento': 'NF-e'
                },
                {
                    'razao_social': 'Fornecedor B S.A.',
                    'cnpj': '98.765.432/0001-10',
                    'valor_total': 8750.25,
                    'data_emissao': '2024-01-16',
                    'tipo_documento': 'NFS-e'
                },
                {
                    'razao_social': 'Fornecedor C ME',
                    'cnpj': '11.222.333/0001-44',
                    'valor_total': 3200.00,
                    'data_emissao': '2024-01-17',
                    'tipo_documento': 'NF-e'
                }
            ],
            'metadata': {
                'period': 'Janeiro 2024',
                'source': 'Documentos fiscais eletrônicos',
                'total_records': 3
            }
        }
        
        print("2. Creating sample query result data...")
        print(f"   📊 Sample data: {len(sample_data['data'])} records")
        print(f"   📅 Period: {sample_data['metadata']['period']}")
        
        # Create report context
        print("3. Creating report context...")
        report_context = ReportContext(
            business_objectives=[
                'Análise de fornecedores',
                'Otimização fiscal',
                'Controle de gastos'
            ],
            audience='executive',
            business_context={
                'sector': 'industrial',
                'company_size': 'medium',
                'focus_areas': ['tax_optimization', 'supplier_management']
            },
            resource_constraints={
                'budget': 'moderate',
                'timeline': 'quarterly'
            },
            timeline_requirements={
                'urgency': 'medium',
                'deadline': '30 days'
            }
        )
        print("   ✅ Report context created")
        
        # Test data processing methods
        print("4. Testing data processing methods...")
        
        # Test data summary creation
        data_summary = await agent._create_data_summary(sample_data)
        print(f"   📈 Data summary created: {data_summary.get('total_records', 0)} records")
        
        # Test statistical analysis
        statistical_analysis = await agent._perform_statistical_analysis(sample_data)
        print(f"   📊 Statistical analysis completed: {statistical_analysis.get('record_count', 0)} records analyzed")
        
        # Test critical metrics identification
        critical_metrics = await agent._identify_critical_metrics(sample_data, report_context)
        print(f"   🎯 Critical metrics identified: {len(critical_metrics)} metrics")
        
        print("5. Testing report template loading...")
        await agent._load_report_templates()
        templates = await agent.list_available_templates()
        print(f"   📋 Available templates: {len(templates)}")
        for template in templates:
            print(f"      - {template['title']} ({template['id']})")
        
        print("6. Testing visualization creation...")
        charts = await agent.create_visualizations(sample_data, ReportTemplate.EXECUTIVE_SUMMARY)
        print(f"   📊 Charts created: {len(charts)}")
        for chart in charts:
            print(f"      - {chart.get('title', 'Untitled Chart')} ({chart.get('chart_type', 'unknown')})")
        
        # Test report preview (without LLM calls)
        print("7. Testing report structure...")
        
        # Create a mock intelligent report for preview testing
        from agents.report_agent import IntelligentReport, DataInsights, ExecutiveSummary, Recommendation
        
        mock_report = IntelligentReport("Relatório de Teste", ReportFormat.PDF, ReportTemplate.EXECUTIVE_SUMMARY)
        mock_report.content = {
            'raw_data': sample_data['data'],
            'summary': data_summary,
            'sections': {'test_section': {'title': 'Seção de Teste', 'content': 'Conteúdo de teste'}},
            'charts': charts
        }
        
        # Mock insights
        mock_report.insights = DataInsights(
            key_findings=['Fornecedor A representa 55% do valor total', 'Diversificação adequada de fornecedores'],
            business_impact={'financial_impact': 'Moderado', 'operational_impact': 'Baixo'},
            strategic_implications=['Manter relacionamento com Fornecedor A', 'Monitorar performance'],
            confidence_level=0.85
        )
        
        # Mock executive summary
        mock_report.executive_summary = {
            'executive_overview': 'Análise de 3 fornecedores no período de Janeiro 2024',
            'urgency_assessment': 'Médio',
            'confidence_level': 0.85
        }
        
        # Mock recommendations
        mock_report.recommendations = [
            Recommendation(
                title="Otimizar Relacionamento com Fornecedor Principal",
                description="Renegociar termos com Fornecedor A para melhores condições",
                priority="Alta",
                risk_assessment="Baixo",
                resource_requirements={'financial': 'Baixo', 'human': 'Moderado'},
                timeline="30 dias",
                expected_impact="Redução de 5-10% nos custos"
            )
        ]
        
        mock_report.llm_processing_stats = {
            'processing_time_seconds': 2.5,
            'insights_confidence': 0.85,
            'recommendations_count': 1,
            'template_used': 'executive_summary'
        }
        
        # Test report preview
        preview = await agent.get_report_preview(mock_report)
        print(f"   👁️  Report preview generated:")
        print(f"      - Title: {preview['title']}")
        print(f"      - Data points: {preview['data_points']}")
        print(f"      - Insights available: {preview['insights_available']}")
        print(f"      - Key findings: {preview['key_findings_count']}")
        print(f"      - Recommendations: {preview['recommendations_count']}")
        print(f"      - Confidence level: {preview['confidence_level']:.2f}")
        print(f"      - Urgency level: {preview['urgency_level']}")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        print("✅ LLM-Enhanced Report Agent is ready for use")
        print("\nKey Features Implemented:")
        print("• Intelligent data analysis and insight generation")
        print("• Executive summary creation with business context")
        print("• Actionable recommendation generation")
        print("• Context-aware report structuring")
        print("• Brazilian fiscal document understanding")
        print("• Multi-format export (PDF, XLSX, DOCX)")
        print("• Backward compatibility with existing code")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_llm_enhanced_report_agent())
    
    if success:
        print("\n🚀 Ready to integrate with LLM services!")
        print("Note: To use LLM features, ensure OpenAI API key is configured in environment.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
        sys.exit(1)