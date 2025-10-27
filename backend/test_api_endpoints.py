#!/usr/bin/env python3
"""
Test script for the new API endpoints
Tests the 4 main API groups implemented in task 4
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test basic health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_dashboard_metrics():
    """Test dashboard metrics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/metrics")
        print(f"✅ Dashboard metrics: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total documentos: {data.get('total_documentos', 0)}")
            print(f"   Valor total: R$ {data.get('valor_total', 0):,.2f}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Dashboard metrics failed: {e}")
        return False

def test_suppliers_endpoint():
    """Test suppliers endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/suppliers")
        print(f"✅ Suppliers: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            suppliers = data.get('suppliers', [])
            print(f"   Fornecedores encontrados: {len(suppliers)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Suppliers failed: {e}")
        return False

def test_categories_endpoint():
    """Test categories endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/dashboard/categories")
        print(f"✅ Categories: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"   Categorias encontradas: {len(categories)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Categories failed: {e}")
        return False

def test_natural_query():
    """Test natural language query endpoint"""
    try:
        query_data = {"query": "Qual o valor total processado?"}
        response = requests.post(
            f"{BASE_URL}/api/v1/query/natural",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Natural query: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Resposta: {data.get('response', 'N/A')[:100]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Natural query failed: {e}")
        return False

def test_query_suggestions():
    """Test query suggestions endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/query/suggestions")
        print(f"✅ Query suggestions: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            print(f"   Sugestões disponíveis: {len(suggestions)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Query suggestions failed: {e}")
        return False

def test_reports_list():
    """Test reports listing endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/reports")
        print(f"✅ Reports list: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            reports = data.get('reports', [])
            print(f"   Relatórios encontrados: {len(reports)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Reports list failed: {e}")
        return False

def test_report_generation():
    """Test report generation endpoint"""
    try:
        report_data = {
            "title": "Teste de Relatório API",
            "include_sections": ["summary", "suppliers"]
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/generate",
            json=report_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Report generation: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Report ID: {data.get('report_id', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testando APIs Backend implementadas na Task 4")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Dashboard Metrics", test_dashboard_metrics),
        ("Suppliers API", test_suppliers_endpoint),
        ("Categories API", test_categories_endpoint),
        ("Natural Query API", test_natural_query),
        ("Query Suggestions", test_query_suggestions),
        ("Reports List", test_reports_list),
        ("Report Generation", test_report_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testando: {test_name}")
        if test_func():
            passed += 1
        time.sleep(0.5)  # Pequena pausa entre testes
    
    print("\n" + "=" * 50)
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os endpoints da Task 4 estão funcionando!")
    else:
        print("⚠️  Alguns endpoints precisam de atenção")
    
    return passed == total

if __name__ == "__main__":
    main()