#!/usr/bin/env python3
"""
Script para verificar os dados fiscais extraídos
"""

import asyncio
import os
from pathlib import Path

# Add backend to path
import sys
sys.path.append(str(Path(__file__).parent / "backend"))

async def check_fiscal_data():
    """Verifica os dados fiscais extraídos das tabelas"""
    try:
        from utils.config import settings
        from supabase import create_client
        
        print("🔍 Verificando dados fiscais extraídos...")
        print("=" * 60)
        
        # Create admin client
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Check nfe_main fiscal data
        print("\n📊 NFE Main - Dados Fiscais:")
        try:
            result = supabase.table("nfe_main").select(
                "chave_nfe, numero_nf, valor_total_nf, valor_total_produtos, "
                "base_calculo_icms, valor_icms, valor_total_ipi, valor_pis, valor_cofins"
            ).limit(5).execute()
            
            if result.data:
                for row in result.data:
                    print(f"   📄 NF {row.get('numero_nf', 'N/A')}:")
                    print(f"      • Valor Total NF: R$ {row.get('valor_total_nf', 0):,.2f}")
                    print(f"      • Valor Produtos: R$ {row.get('valor_total_produtos', 0):,.2f}")
                    print(f"      • Base Cálculo ICMS: R$ {(row.get('base_calculo_icms') or 0):,.2f}")
                    print(f"      • Valor ICMS: R$ {(row.get('valor_icms') or 0):,.2f}")
                    print(f"      • Valor IPI: R$ {(row.get('valor_total_ipi') or 0):,.2f}")
                    print(f"      • Valor PIS: R$ {(row.get('valor_pis') or 0):,.2f}")
                    print(f"      • Valor COFINS: R$ {(row.get('valor_cofins') or 0):,.2f}")
                    print()
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        # Check fact_itens_nfe fiscal data
        print("\n📊 Itens NFE - Dados Fiscais:")
        try:
            result = supabase.table("fact_itens_nfe").select(
                "numero_item, descricao, valor_total_bruto, valor_desconto, valor_frete, "
                "base_calculo_icms, valor_icms, aliquota_icms, "
                "valor_pis, aliquota_pis, valor_cofins, aliquota_cofins"
            ).limit(10).execute()
            
            if result.data:
                for row in result.data:
                    print(f"   📦 Item {row.get('numero_item', 'N/A')}:")
                    print(f"      • Produto: {row.get('descricao', 'N/A')[:50]}...")
                    print(f"      • Valor Bruto: R$ {row.get('valor_total_bruto', 0):,.2f}")
                    print(f"      • Desconto: R$ {(row.get('valor_desconto') or 0):,.2f}")
                    print(f"      • Frete: R$ {(row.get('valor_frete') or 0):,.2f}")
                    print(f"      • Base ICMS: R$ {(row.get('base_calculo_icms') or 0):,.2f}")
                    print(f"      • Valor ICMS: R$ {(row.get('valor_icms') or 0):,.2f}")
                    print(f"      • Alíquota ICMS: {((row.get('aliquota_icms') or 0) * 100):,.2f}%")
                    print(f"      • Valor PIS: R$ {(row.get('valor_pis') or 0):,.2f}")
                    print(f"      • Alíquota PIS: {((row.get('aliquota_pis') or 0) * 100):,.2f}%")
                    print(f"      • Valor COFINS: R$ {(row.get('valor_cofins') or 0):,.2f}")
                    print(f"      • Alíquota COFINS: {((row.get('aliquota_cofins') or 0) * 100):,.2f}%")
                    print()
            else:
                print("   ❌ Nenhum registro encontrado")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print("=" * 60)
        print("✅ Verificação de dados fiscais concluída!")
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_fiscal_data())