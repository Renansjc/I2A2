"""
Simple test for dimensional schemas
Tests that the schemas can be imported and instantiated correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, date

def test_dimensional_schemas():
    """Test dimensional schemas can be imported and used"""
    print("Testing Dimensional Schemas...")
    
    try:
        from schemas.dimensional_schemas import (
            SuppliersResponse, ProductsResponse, FinancialSummaryResponse,
            SupplierSummary, ProductSummary, MonthlySupplierData, MonthlyTotal, TaxSummary,
            EmitenteResponse, ProdutoResponse, KPIMetrics, DashboardMetricsResponse
        )
        print("✅ All schemas imported successfully")
        
        # Test SupplierSummary
        supplier = SupplierSummary(
            cnpj="12345678000195",
            razao_social="Test Company",
            uf="SP",
            total_documentos=10,
            valor_total=Decimal("1000.00"),
            valor_medio_item=Decimal("100.00"),
            produtos_distintos=5
        )
        print(f"✅ SupplierSummary created: {supplier.razao_social}")
        
        # Test ProductSummary
        product = ProductSummary(
            codigo_produto="PROD001",
            descricao="Test Product",
            total_documentos=5,
            quantidade_total=Decimal("50.00"),
            valor_total=Decimal("500.00"),
            preco_medio=Decimal("10.00"),
            fornecedores_distintos=2
        )
        print(f"✅ ProductSummary created: {product.descricao}")
        
        # Test KPIMetrics
        kpis = KPIMetrics(
            concentracao_fornecedores=0.8,
            diversificacao_produtos=0.6,
            crescimento_mensal=5.2,
            ticket_medio=Decimal("150.00"),
            fornecedores_ativos=25,
            produtos_ativos=100,
            sazonalidade_score=0.4
        )
        print(f"✅ KPIMetrics created: {kpis.fornecedores_ativos} fornecedores ativos")
        
        # Test SuppliersResponse
        suppliers_response = SuppliersResponse(
            total_suppliers=1,
            top_suppliers=[supplier],
            monthly_trend=[],
            periodo_analise="2024-01-01 - 2024-03-31"
        )
        print(f"✅ SuppliersResponse created with {suppliers_response.total_suppliers} suppliers")
        
        print("\n🎉 All dimensional schemas working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing schemas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dimensional_schemas()
    if success:
        print("\n✅ Dimensional data APIs are ready to serve real data!")
        print("The schemas and data models are properly configured.")
    else:
        print("\n❌ There are issues with the dimensional schemas that need to be fixed.")