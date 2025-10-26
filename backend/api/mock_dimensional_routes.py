"""
Mock dimensional routes for testing frontend integration
APIs mockadas para testar integração do frontend
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

# Create mock dimensional data router
mock_dimensional_router = APIRouter(prefix="/api/dashboard", tags=["Mock Dashboard"])
mock_query_router = APIRouter(prefix="/api/dimensional", tags=["Mock Dimensional"])

@mock_dimensional_router.get("/financial-summary")
async def get_mock_financial_summary(
    period: str = Query("last_90_days", description="Período de análise")
):
    """Mock financial summary with real-like data"""
    return {
        "total_invoices": 1247,
        "total_value": 2847650.50,
        "average_invoice_value": 2284.32,
        "monthly_totals": [
            {
                "mes": "2024-08-01",
                "total_invoices": 387,
                "total_value": 892340.25,
                "total_taxes": 178468.05
            },
            {
                "mes": "2024-09-01", 
                "total_invoices": 421,
                "total_value": 967890.75,
                "total_taxes": 193578.15
            },
            {
                "mes": "2024-10-01",
                "total_invoices": 439,
                "total_value": 987419.50,
                "total_taxes": 197483.90
            }
        ],
        "tax_summary": {
            "total_icms": 284765.50,
            "total_ipi": 56953.10,
            "total_pis": 28476.55,
            "total_cofins": 131334.85
        },
        "periodo_analise": "01/08/2024 - 26/10/2024"
    }

@mock_dimensional_router.get("/suppliers")
async def get_mock_suppliers(
    period: str = Query("last_90_days", description="Período de análise"),
    limit: int = Query(10, description="Número de fornecedores")
):
    """Mock suppliers data"""
    return {
        "total_suppliers": 89,
        "top_suppliers": [
            {
                "cnpj": "12345678000195",
                "razao_social": "TECH SOLUTIONS LTDA",
                "nome_fantasia": "TechSol",
                "uf": "SP",
                "total_documentos": 156,
                "valor_total": 487650.75,
                "valor_medio_item": 3125.33,
                "primeira_compra": "2024-01-15",
                "ultima_compra": "2024-10-25",
                "produtos_distintos": 23
            },
            {
                "cnpj": "98765432000187",
                "razao_social": "MATERIAIS INDUSTRIAIS S.A.",
                "nome_fantasia": "MatInd",
                "uf": "RJ",
                "total_documentos": 134,
                "valor_total": 398420.50,
                "valor_medio_item": 2973.29,
                "primeira_compra": "2024-02-03",
                "ultima_compra": "2024-10-24",
                "produtos_distintos": 45
            },
            {
                "cnpj": "11223344000156",
                "razao_social": "EQUIPAMENTOS ELETRONICOS LTDA",
                "nome_fantasia": "EletroEquip",
                "uf": "MG",
                "total_documentos": 98,
                "valor_total": 287340.25,
                "valor_medio_item": 2932.04,
                "primeira_compra": "2024-03-12",
                "ultima_compra": "2024-10-23",
                "produtos_distintos": 18
            }
        ],
        "monthly_trend": [
            {
                "mes": "2024-08-01",
                "fornecedores_ativos": 67,
                "valor_total_mes": 892340.25
            },
            {
                "mes": "2024-09-01",
                "fornecedores_ativos": 73,
                "valor_total_mes": 967890.75
            },
            {
                "mes": "2024-10-01",
                "fornecedores_ativos": 89,
                "valor_total_mes": 987419.50
            }
        ],
        "periodo_analise": "01/08/2024 - 26/10/2024"
    }

@mock_dimensional_router.get("/products")
async def get_mock_products(
    period: str = Query("last_90_days", description="Período de análise"),
    category: Optional[str] = Query(None, description="Categoria"),
    limit: int = Query(10, description="Número de produtos")
):
    """Mock products data"""
    return {
        "total_products": 234,
        "categories_distribution": {
            "Eletrônicos": {
                "total_produtos": 45,
                "valor_total": 567890.25
            },
            "Materiais de Escritório": {
                "total_produtos": 67,
                "valor_total": 234567.80
            },
            "Equipamentos": {
                "total_produtos": 32,
                "valor_total": 789123.45
            },
            "Software": {
                "total_produtos": 18,
                "valor_total": 345678.90
            },
            "Serviços": {
                "total_produtos": 72,
                "valor_total": 456789.12
            }
        },
        "top_products_by_value": [
            {
                "codigo_produto": "PROD001",
                "descricao": "Notebook Dell Inspiron 15",
                "categoria": "Eletrônicos",
                "subcategoria": "Informática",
                "ncm": "84713012",
                "total_documentos": 23,
                "quantidade_total": 45,
                "valor_total": 123456.78,
                "preco_medio": 2743.48,
                "fornecedores_distintos": 3
            },
            {
                "codigo_produto": "PROD002",
                "descricao": "Impressora HP LaserJet Pro",
                "categoria": "Eletrônicos",
                "subcategoria": "Periféricos",
                "ncm": "84433210",
                "total_documentos": 18,
                "quantidade_total": 28,
                "valor_total": 98765.43,
                "preco_medio": 3527.34,
                "fornecedores_distintos": 2
            }
        ],
        "periodo_analise": "01/08/2024 - 26/10/2024"
    }

@mock_dimensional_router.get("/trends")
async def get_mock_trends(
    period: str = Query("last_12_months", description="Período de análise"),
    trend_type: str = Query("volume", description="Tipo de tendência")
):
    """Mock trends data"""
    
    if trend_type == "valor":
        trend_data = [
            {"periodo": "2024-01-01", "valor": 756890.25, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-02-01", "valor": 823456.78, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-03-01", "valor": 789123.45, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-04-01", "valor": 867234.56, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-05-01", "valor": 934567.89, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-06-01", "valor": 876543.21, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-07-01", "valor": 923456.78, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-08-01", "valor": 892340.25, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-09-01", "valor": 967890.75, "metrica": "Valor Total (R$)"},
            {"periodo": "2024-10-01", "valor": 987419.50, "metrica": "Valor Total (R$)"}
        ]
    elif trend_type == "fornecedores":
        trend_data = [
            {"periodo": "2024-01-01", "valor": 45, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-02-01", "valor": 52, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-03-01", "valor": 48, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-04-01", "valor": 56, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-05-01", "valor": 63, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-06-01", "valor": 59, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-07-01", "valor": 67, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-08-01", "valor": 67, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-09-01", "valor": 73, "metrica": "Fornecedores Ativos"},
            {"periodo": "2024-10-01", "valor": 89, "metrica": "Fornecedores Ativos"}
        ]
    else:  # volume
        trend_data = [
            {"periodo": "2024-01-01", "valor": 298, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-02-01", "valor": 342, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-03-01", "valor": 315, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-04-01", "valor": 367, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-05-01", "valor": 389, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-06-01", "valor": 356, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-07-01", "valor": 398, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-08-01", "valor": 387, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-09-01", "valor": 421, "metrica": "Documentos Fiscais"},
            {"periodo": "2024-10-01", "valor": 439, "metrica": "Documentos Fiscais"}
        ]
    
    return {
        "trend_data": trend_data,
        "growth_rate": 12.5,
        "trend_type": trend_type,
        "periodo_analise": "01/01/2024 - 26/10/2024",
        "insights": [
            f"Crescimento de 12.5% no período analisado",
            f"Análise baseada em {len(trend_data)} pontos de dados mensais",
            "Tendência calculada com base em dados reais processados"
        ]
    }

@mock_dimensional_router.get("/metrics")
async def get_mock_metrics(
    period: str = Query("last_90_days", description="Período de análise")
):
    """Mock dashboard metrics"""
    return {
        "kpis": {
            "concentracao_fornecedores": 0.15,
            "diversificacao_produtos": 0.78,
            "crescimento_mensal": 8.3,
            "ticket_medio": 2284.32,
            "fornecedores_ativos": 89,
            "produtos_ativos": 234,
            "sazonalidade_score": 0.65,
            "confiabilidade_dados": 0.95
        },
        "periodo_analise": "01/08/2024 - 26/10/2024",
        "ultima_atualizacao": datetime.now().isoformat(),
        "confiabilidade_dados": 0.95
    }

# Mock activity routes
mock_activity_router = APIRouter(prefix="/api/activity", tags=["Mock Activity"])

@mock_activity_router.get("/recent")
async def get_mock_recent_activities(
    limit: int = Query(10, description="Número de atividades"),
    hours: int = Query(24, description="Horas para buscar")
):
    """Mock recent activities"""
    return {
        "activities": [
            {
                "id": "act_001",
                "type": "success",
                "title": "Processamento XML Concluído",
                "description": "3 arquivos NF-e processados com sucesso",
                "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat()
            },
            {
                "id": "act_002",
                "type": "info",
                "title": "Categorização IA Executada",
                "description": "45 produtos categorizados automaticamente",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
            },
            {
                "id": "act_003",
                "type": "success",
                "title": "Relatório Gerado",
                "description": "Análise mensal de fornecedores concluída",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "id": "act_004",
                "type": "warning",
                "title": "Novas Categorias Detectadas",
                "description": "Sistema identificou 3 novas categorias de produtos",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat()
            },
            {
                "id": "act_005",
                "type": "info",
                "title": "Backup Automático",
                "description": "Backup diário dos dados fiscais realizado",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat()
            }
        ],
        "total_count": 5,
        "period_hours": hours,
        "generated_at": datetime.now().isoformat()
    }

@mock_activity_router.get("/system-status")
async def get_mock_system_status():
    """Mock system status"""
    return {
        "system_health": {
            "overall_health": 94.2,
            "status": "healthy",
            "uptime_days": 15,
            "last_restart": (datetime.now() - timedelta(days=15)).isoformat()
        },
        "processing_stats": {
            "total_documents": 1247,
            "completed_documents": 1175,
            "error_documents": 72,
            "success_rate": 94.2,
            "documents_today": 23
        },
        "api_status": {
            "dimensional_apis": "active",
            "search_apis": "active", 
            "upload_api": "active",
            "export_api": "active"
        },
        "generated_at": datetime.now().isoformat()
    }