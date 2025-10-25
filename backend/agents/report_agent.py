"""
Report Agent for generating executive reports in multiple formats
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import structlog

from .base_agent import BaseAgent
from utils.config import settings


class ReportFormat(Enum):
    """Supported report formats"""
    PDF = "pdf"
    XLSX = "xlsx"
    DOCX = "docx"


class ReportTemplate(Enum):
    """Available report templates"""
    EXECUTIVE_SUMMARY = "executive_summary"
    SUPPLIER_ANALYSIS = "supplier_analysis"
    PRODUCT_ANALYSIS = "product_analysis"
    TAX_ANALYSIS = "tax_analysis"
    MONTHLY_REPORT = "monthly_report"
    CUSTOM = "custom"


class Report:
    """Report representation"""
    
    def __init__(self, title: str, format: ReportFormat, template: ReportTemplate):
        self.title = title
        self.format = format
        self.template = template
        self.content = {}
        self.metadata = {}
        self.file_path = None
        self.created_at = datetime.now()
        self.size_bytes = 0


class ReportAgent(BaseAgent):
    """Agent responsible for generating executive reports"""
    
    def __init__(self):
        super().__init__("ReportAgent")
        self.report_templates = {}
        self.output_directory = "./reports"
        
    async def initialize(self):
        """Initialize Report Agent resources"""
        try:
            # Create output directory
            os.makedirs(self.output_directory, exist_ok=True)
            
            # Load report templates
            await self._load_report_templates()
            
            # Initialize report generators
            await self._initialize_generators()
            
            self.logger.info("Report Agent initialized", output_dir=self.output_directory)
            
        except Exception as e:
            self.logger.error("Failed to initialize Report Agent", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Report Agent cleaned up")
    
    async def process(self, data: Dict[str, Any]) -> Report:
        """Process report generation request"""
        if isinstance(data, dict) and 'query_result' in data:
            query_result = data['query_result']
            format = ReportFormat(data.get('format', 'pdf'))
            template = ReportTemplate(data.get('template', 'executive_summary'))
            title = data.get('title', 'Relatório Executivo')
            
            return await self.generate_report(query_result, format, template, title)
        return None
    
    async def _load_report_templates(self):
        """Load report templates"""
        try:
            self.report_templates = {
                ReportTemplate.EXECUTIVE_SUMMARY: {
                    'title': 'Relatório Executivo',
                    'sections': [
                        'summary',
                        'key_metrics',
                        'trends',
                        'recommendations'
                    ],
                    'charts': ['summary_chart', 'trend_chart']
                },
                
                ReportTemplate.SUPPLIER_ANALYSIS: {
                    'title': 'Análise de Fornecedores',
                    'sections': [
                        'supplier_overview',
                        'top_suppliers',
                        'regional_distribution',
                        'performance_metrics'
                    ],
                    'charts': ['supplier_pie_chart', 'regional_bar_chart']
                },
                
                ReportTemplate.PRODUCT_ANALYSIS: {
                    'title': 'Análise de Produtos',
                    'sections': [
                        'product_overview',
                        'category_analysis',
                        'top_products',
                        'price_trends'
                    ],
                    'charts': ['category_chart', 'price_trend_chart']
                },
                
                ReportTemplate.TAX_ANALYSIS: {
                    'title': 'Análise Tributária',
                    'sections': [
                        'tax_overview',
                        'tax_by_type',
                        'tax_efficiency',
                        'compliance_status'
                    ],
                    'charts': ['tax_breakdown_chart', 'efficiency_chart']
                },
                
                ReportTemplate.MONTHLY_REPORT: {
                    'title': 'Relatório Mensal',
                    'sections': [
                        'monthly_summary',
                        'comparison',
                        'highlights',
                        'action_items'
                    ],
                    'charts': ['monthly_trend_chart', 'comparison_chart']
                }
            }
            
            self.logger.info("Report templates loaded", templates=len(self.report_templates))
            
        except Exception as e:
            self.logger.error("Error loading report templates", error=str(e))
    
    async def _initialize_generators(self):
        """Initialize report format generators"""
        try:
            # In a real implementation, you would initialize:
            # - reportlab for PDF generation
            # - openpyxl for Excel generation
            # - python-docx for Word generation
            
            self.logger.info("Report generators initialized")
            
        except Exception as e:
            self.logger.error("Error initializing generators", error=str(e))
    
    async def generate_report(self, query_result: Dict[str, Any], format: ReportFormat, 
                            template: ReportTemplate = ReportTemplate.EXECUTIVE_SUMMARY,
                            title: str = None) -> Report:
        """Generate report in specified format"""
        try:
            self.logger.info("Generating report", format=format.value, template=template.value)
            
            # Create report object
            report_title = title or self.report_templates[template]['title']
            report = Report(report_title, format, template)
            
            # Process data for report
            report.content = await self._process_data_for_report(query_result, template)
            
            # Generate visualizations
            report.content['charts'] = await self.create_visualizations(query_result, template)
            
            # Apply template formatting
            formatted_report = await self.apply_executive_template(report)
            
            # Export to specified format
            exported_report = await self.export_report(formatted_report, format)
            
            self.logger.info("Report generated successfully", 
                           file_path=exported_report.file_path,
                           size=f"{exported_report.size_bytes} bytes")
            
            return exported_report
            
        except Exception as e:
            self.logger.error("Error generating report", error=str(e))
            raise
    
    async def _process_data_for_report(self, query_result: Dict[str, Any], template: ReportTemplate) -> Dict[str, Any]:
        """Process query result data for report template"""
        
        data = query_result.get('data', [])
        metadata = query_result.get('metadata', {})
        
        processed_content = {
            'raw_data': data,
            'metadata': metadata,
            'summary': await self._generate_summary(data),
            'sections': {}
        }
        
        # Process data based on template
        template_config = self.report_templates[template]
        
        for section in template_config['sections']:
            processed_content['sections'][section] = await self._process_section(section, data)
        
        return processed_content
    
    async def _generate_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary from data"""
        if not data:
            return {'message': 'Nenhum dado disponível para análise'}
        
        summary = {
            'total_records': len(data),
            'date_range': 'Último período analisado',
            'key_insights': []
        }
        
        # Generate key insights based on data
        if data:
            # Find numeric columns for analysis
            numeric_columns = []
            for key, value in data[0].items():
                if isinstance(value, (int, float)):
                    numeric_columns.append(key)
            
            # Calculate totals and averages
            for col in numeric_columns:
                values = [row.get(col, 0) for row in data if row.get(col) is not None]
                if values:
                    total = sum(values)
                    avg = total / len(values)
                    summary[f'total_{col}'] = total
                    summary[f'avg_{col}'] = avg
            
            # Generate insights
            if 'valor_total' in data[0] or 'total_value' in data[0]:
                summary['key_insights'].append('Análise de valores totais concluída')
            
            if len(data) > 10:
                summary['key_insights'].append(f'Dataset robusto com {len(data)} registros')
            
            summary['key_insights'].append('Dados processados com sucesso')
        
        return summary
    
    async def _process_section(self, section: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process specific report section"""
        
        if section == 'supplier_overview':
            return {
                'title': 'Visão Geral dos Fornecedores',
                'content': f'Análise de {len(data)} registros de fornecedores',
                'data': data[:10]  # Top 10
            }
        
        elif section == 'top_suppliers':
            # Sort by value if available
            sorted_data = sorted(data, key=lambda x: x.get('total_value', x.get('valor_total', 0)), reverse=True)
            return {
                'title': 'Principais Fornecedores',
                'content': 'Ranking dos fornecedores por valor',
                'data': sorted_data[:5]
            }
        
        elif section == 'key_metrics':
            return {
                'title': 'Métricas Principais',
                'content': 'Indicadores chave de performance',
                'metrics': await self._calculate_key_metrics(data)
            }
        
        elif section == 'trends':
            return {
                'title': 'Tendências',
                'content': 'Análise de tendências identificadas',
                'trends': ['Crescimento estável', 'Diversificação de fornecedores']
            }
        
        elif section == 'recommendations':
            return {
                'title': 'Recomendações',
                'content': 'Recomendações estratégicas baseadas na análise',
                'recommendations': [
                    'Manter relacionamento com fornecedores principais',
                    'Avaliar oportunidades de otimização fiscal',
                    'Monitorar tendências de mercado'
                ]
            }
        
        else:
            return {
                'title': section.replace('_', ' ').title(),
                'content': f'Seção {section} processada',
                'data': data[:5]
            }
    
    async def _calculate_key_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate key business metrics"""
        if not data:
            return {}
        
        metrics = {}
        
        # Find numeric columns
        numeric_columns = []
        for key, value in data[0].items():
            if isinstance(value, (int, float)):
                numeric_columns.append(key)
        
        # Calculate metrics for each numeric column
        for col in numeric_columns:
            values = [row.get(col, 0) for row in data if row.get(col) is not None]
            if values:
                metrics[f'{col}_total'] = sum(values)
                metrics[f'{col}_average'] = sum(values) / len(values)
                metrics[f'{col}_max'] = max(values)
                metrics[f'{col}_min'] = min(values)
        
        return metrics
    
    async def create_visualizations(self, query_result: Dict[str, Any], template: ReportTemplate) -> List[Dict[str, Any]]:
        """Create charts and visualizations for the report"""
        try:
            data = query_result.get('data', [])
            charts = []
            
            if not data:
                return charts
            
            template_config = self.report_templates[template]
            chart_types = template_config.get('charts', [])
            
            for chart_type in chart_types:
                chart = await self._create_chart(chart_type, data)
                if chart:
                    charts.append(chart)
            
            return charts
            
        except Exception as e:
            self.logger.error("Error creating visualizations", error=str(e))
            return []
    
    async def _create_chart(self, chart_type: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create specific chart type"""
        
        # This is a placeholder implementation
        # In reality, you would use libraries like matplotlib, plotly, or Chart.js
        
        chart_config = {
            'type': chart_type,
            'title': chart_type.replace('_', ' ').title(),
            'data': data[:10],  # Limit data for charts
            'config': {
                'width': 800,
                'height': 400,
                'responsive': True
            }
        }
        
        if chart_type == 'summary_chart':
            chart_config.update({
                'chart_type': 'bar',
                'title': 'Resumo Executivo',
                'x_axis': 'categoria',
                'y_axis': 'valor'
            })
        
        elif chart_type == 'supplier_pie_chart':
            chart_config.update({
                'chart_type': 'pie',
                'title': 'Distribuição por Fornecedor',
                'label_field': 'razao_social',
                'value_field': 'total_value'
            })
        
        elif chart_type == 'trend_chart':
            chart_config.update({
                'chart_type': 'line',
                'title': 'Tendência Temporal',
                'x_axis': 'periodo',
                'y_axis': 'valor_total'
            })
        
        elif chart_type == 'regional_bar_chart':
            chart_config.update({
                'chart_type': 'bar',
                'title': 'Distribuição Regional',
                'x_axis': 'uf',
                'y_axis': 'valor_total'
            })
        
        return chart_config
    
    async def apply_executive_template(self, report: Report) -> Report:
        """Apply executive-level formatting to report"""
        try:
            # Add executive styling and formatting
            report.metadata.update({
                'style': 'executive',
                'font_family': 'Arial',
                'primary_color': '#1f4e79',
                'secondary_color': '#70ad47',
                'logo_path': './assets/company_logo.png',
                'header_text': f'{report.title} - {datetime.now().strftime("%B %Y")}',
                'footer_text': 'Confidencial - Uso Interno'
            })
            
            # Add executive summary to the beginning
            if 'summary' not in report.content:
                report.content['summary'] = await self._generate_summary(
                    report.content.get('raw_data', [])
                )
            
            # Ensure proper section ordering for executive consumption
            section_order = [
                'summary',
                'key_metrics',
                'charts',
                'sections',
                'recommendations'
            ]
            
            ordered_content = {}
            for section in section_order:
                if section in report.content:
                    ordered_content[section] = report.content[section]
            
            # Add any remaining sections
            for key, value in report.content.items():
                if key not in ordered_content:
                    ordered_content[key] = value
            
            report.content = ordered_content
            
            return report
            
        except Exception as e:
            self.logger.error("Error applying executive template", error=str(e))
            return report
    
    async def export_report(self, report: Report, format: ReportFormat) -> Report:
        """Export report to specified format"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report.title.replace(' ', '_')}_{timestamp}.{format.value}"
            file_path = os.path.join(self.output_directory, filename)
            
            if format == ReportFormat.PDF:
                await self._export_pdf(report, file_path)
            elif format == ReportFormat.XLSX:
                await self._export_xlsx(report, file_path)
            elif format == ReportFormat.DOCX:
                await self._export_docx(report, file_path)
            
            # Update report with file information
            report.file_path = file_path
            report.size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            return report
            
        except Exception as e:
            self.logger.error("Error exporting report", error=str(e))
            raise
    
    async def _export_pdf(self, report: Report, file_path: str):
        """Export report as PDF"""
        # Placeholder implementation
        # In reality, you would use reportlab or similar library
        
        content = f"""
        {report.title}
        Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        Summary:
        {report.content.get('summary', {})}
        
        Data processed successfully.
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info("PDF report exported", file_path=file_path)
    
    async def _export_xlsx(self, report: Report, file_path: str):
        """Export report as Excel"""
        # Placeholder implementation
        # In reality, you would use openpyxl or pandas
        
        import csv
        csv_path = file_path.replace('.xlsx', '.csv')
        
        data = report.content.get('raw_data', [])
        if data:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
        
        # Rename to xlsx for now (placeholder)
        os.rename(csv_path, file_path)
        
        self.logger.info("Excel report exported", file_path=file_path)
    
    async def _export_docx(self, report: Report, file_path: str):
        """Export report as Word document"""
        # Placeholder implementation
        # In reality, you would use python-docx
        
        content = f"""
        {report.title}
        
        Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        Executive Summary:
        {report.content.get('summary', {})}
        
        Sections:
        """
        
        sections = report.content.get('sections', {})
        for section_name, section_data in sections.items():
            content += f"\n\n{section_data.get('title', section_name)}:\n"
            content += f"{section_data.get('content', 'No content available')}\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info("Word report exported", file_path=file_path)
    
    async def get_report_preview(self, report: Report) -> Dict[str, Any]:
        """Generate report preview for user validation"""
        try:
            preview = {
                'title': report.title,
                'format': report.format.value,
                'template': report.template.value,
                'created_at': report.created_at.isoformat(),
                'sections': list(report.content.get('sections', {}).keys()),
                'charts': len(report.content.get('charts', [])),
                'data_points': len(report.content.get('raw_data', [])),
                'summary': report.content.get('summary', {})
            }
            
            return preview
            
        except Exception as e:
            self.logger.error("Error generating report preview", error=str(e))
            return {'error': str(e)}
    
    async def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available report templates"""
        templates = []
        
        for template, config in self.report_templates.items():
            templates.append({
                'id': template.value,
                'title': config['title'],
                'sections': config['sections'],
                'charts': config.get('charts', [])
            })
        
        return templates