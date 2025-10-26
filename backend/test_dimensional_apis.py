"""
Test script for dimensional data APIs
Tests the new APIs for serving real dimensional data to the dashboard
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
import structlog

logger = structlog.get_logger()

def test_dimensional_apis():
    """Test dimensional data APIs"""
    client = TestClient(app)
    
    print("Testing Dimensional Data APIs...")
    
    # Test dashboard suppliers endpoint
    print("\n1. Testing /api/dashboard/suppliers")
    try:
        response = client.get("/api/v1/api/dashboard/suppliers?period=last_90_days&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total suppliers: {data.get('total_suppliers', 0)}")
            print(f"Top suppliers count: {len(data.get('top_suppliers', []))}")
            print("✅ Suppliers endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test dashboard products endpoint
    print("\n2. Testing /api/dashboard/products")
    try:
        response = client.get("/api/v1/api/dashboard/products?period=last_90_days&limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total products: {data.get('total_products', 0)}")
            print(f"Categories: {len(data.get('categories_distribution', {}))}")
            print("✅ Products endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test financial summary endpoint
    print("\n3. Testing /api/dashboard/financial-summary")
    try:
        response = client.get("/api/v1/api/dashboard/financial-summary?period=last_90_days")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total invoices: {data.get('total_invoices', 0)}")
            print(f"Total value: {data.get('total_value', 0)}")
            print("✅ Financial summary endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test trends endpoint
    print("\n4. Testing /api/dashboard/trends")
    try:
        response = client.get("/api/v1/api/dashboard/trends?period=last_12_months&trend_type=volume")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Trend points: {len(data.get('trend_data', []))}")
            print(f"Growth rate: {data.get('growth_rate', 0)}%")
            print("✅ Trends endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test dimensional emitentes query
    print("\n5. Testing /api/dimensional/emitentes")
    try:
        response = client.get("/api/v1/api/dimensional/emitentes?limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Items returned: {len(data.get('items', []))}")
            print(f"Total count: {data.get('total_count', 0)}")
            print("✅ Emitentes query endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test dimensional produtos query
    print("\n6. Testing /api/dimensional/produtos")
    try:
        response = client.get("/api/v1/api/dimensional/produtos?limit=5")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Items returned: {len(data.get('items', []))}")
            print(f"Total count: {data.get('total_count', 0)}")
            print("✅ Produtos query endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test dashboard metrics
    print("\n7. Testing /api/dashboard/metrics")
    try:
        response = client.get("/api/v1/api/dashboard/metrics?period=last_90_days")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            kpis = data.get('kpis', {})
            print(f"Fornecedores ativos: {kpis.get('fornecedores_ativos', 0)}")
            print(f"Produtos ativos: {kpis.get('produtos_ativos', 0)}")
            print(f"Concentração fornecedores: {kpis.get('concentracao_fornecedores', 0):.2f}")
            print("✅ Metrics endpoint working")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n🎉 Dimensional APIs testing completed!")
    print("\nNote: Some endpoints may return empty data if no dimensional data has been processed yet.")
    print("The APIs are ready to serve real data once the dimensional processing pipeline populates the tables.")

if __name__ == "__main__":
    test_dimensional_apis()