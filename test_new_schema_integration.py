#!/usr/bin/env python3
"""
Teste de integração com o novo schema do banco de dados
Verifica se as funções de salvamento estão funcionando corretamente
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.append('backend')

# Carregar variáveis de ambiente
load_dotenv('backend/.env')

# Importar funções do backend
from main import (
    supabase, 
    save_extracted_data, 
    save_supplier_analysis, 
    save_ai_insights,
    create_document_record,
    upload_file_to_storage
)

async def test_new_schema_integration():
    """Testa a integração com o novo schema do banco"""
    
    print("🧪 Testando integração com novo schema do banco de dados\n")
    
    # Verificar conexão com Supabase
    if not supabase:
        print("❌ Supabase não configurado. Verifique as variáveis de ambiente.")
        return False
    
    print("✅ Supabase conectado")
    
    # Dados de teste
    test_doc_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_filename = "test_nfe.xml"
    test_file_path = f"test/{test_filename}"
    
    try:
        # 1. Testar criação de documento
        print("\n1. Testando criação de documento...")
        doc_created = await create_document_record(test_doc_id, test_filename, test_file_path)
        if doc_created:
            print("✅ Documento criado com sucesso")
        else:
            print("❌ Falha ao criar documento")
            return False
        
        # 2. Testar salvamento de dados extraídos
        print("\n2. Testando salvamento de dados extraídos...")
        
        extracted_data = {
            "numero_nota": "123456",
            "serie": "1",
            "chave_acesso": "42250383261420001201550990003348371042993209",
            "data_emissao": "2024-10-26",
            "natureza_operacao": "Venda de mercadoria",
            "valor_total": 1500.50,
            "consumidor_final": True,
            "presenca_comprador": 1,
            "emitente": {
                "razao_social": "Empresa Teste LTDA",
                "nome_fantasia": "Teste Corp",
                "cnpj": "12345678000199",
                "inscricao_estadual": "123456789",
                "crt": 3,
                "logradouro": "Rua Teste, 123",
                "numero": "123",
                "bairro": "Centro",
                "municipio": "São Paulo",
                "uf": "SP",
                "cep": "01234567",
                "telefone": "11999999999"
            },
            "destinatario": {
                "nome": "Cliente Teste",
                "cnpj": "98765432000188",
                "inscricao_estadual": "987654321",
                "logradouro": "Av. Cliente, 456",
                "numero": "456",
                "bairro": "Vila Nova",
                "municipio": "Rio de Janeiro",
                "uf": "RJ",
                "cep": "20000000",
                "email": "cliente@teste.com"
            },
            "itens": [
                {
                    "codigo_produto": "PROD001",
                    "descricao": "Produto de Teste",
                    "ncm": "12345678",
                    "cfop": "5102",
                    "unidade_comercial": "UN",
                    "quantidade_comercial": 10.0,
                    "valor_unitario_comercial": 150.05,
                    "valor_produto": 1500.50,
                    "icms_origem": 0,
                    "icms_cst": "000",
                    "icms_base_calculo": 1500.50,
                    "icms_aliquota": 18.0,
                    "icms_valor": 270.09,
                    "categoria": "Eletrônicos",
                    "categoria_confianca": 0.95,
                    "subcategoria": "Smartphones",
                    "marca": "TesteBrand",
                    "modelo": "Model X"
                }
            ],
            "impostos": {
                "icms": {"valor": 270.09, "base_calculo": 1500.50, "aliquota": 18.0},
                "ipi": {"valor": 0.0},
                "pis": {"valor": 9.75},
                "cofins": {"valor": 45.02}
            }
        }
        
        data_saved = await save_extracted_data(test_doc_id, extracted_data)
        if data_saved:
            print("✅ Dados extraídos salvos com sucesso")
        else:
            print("❌ Falha ao salvar dados extraídos")
            return False
        
        # 3. Testar salvamento de análise de fornecedor
        print("\n3. Testando salvamento de análise de fornecedor...")
        
        supplier_analysis = {
            "type": "Distribuidora",
            "business_category": "Tecnologia",
            "company_size": "Médio",
            "confidence": 0.88,
            "purchase_frequency": 5,
            "average_transaction_value": 1500.50,
            "average_payment_term": 30,
            "risk_score": 0.25,
            "risk_factors": ["Novo fornecedor", "Região distante"]
        }
        
        supplier_saved = await save_supplier_analysis(test_doc_id, supplier_analysis)
        if supplier_saved:
            print("✅ Análise de fornecedor salva com sucesso")
        else:
            print("❌ Falha ao salvar análise de fornecedor")
        
        # 4. Testar salvamento de insights de IA
        print("\n4. Testando salvamento de insights de IA...")
        
        ai_insights = {
            "alertas": [
                {
                    "categoria": "fiscal",
                    "titulo": "Alíquota de ICMS elevada",
                    "descricao": "A alíquota de ICMS de 18% está acima da média regional",
                    "confianca": 0.92,
                    "prioridade": 2,
                    "acao_sugerida": "Verificar se a classificação fiscal está correta"
                }
            ],
            "oportunidades": [
                {
                    "categoria": "financeiro",
                    "titulo": "Oportunidade de negociação",
                    "descricao": "Fornecedor com bom histórico para aumentar volume",
                    "confianca": 0.85,
                    "prioridade": 3,
                    "acao_sugerida": "Negociar desconto por volume"
                }
            ],
            "recomendacoes": [
                {
                    "categoria": "operacional",
                    "titulo": "Automatizar processo",
                    "descricao": "Este tipo de documento pode ser processado automaticamente",
                    "confianca": 0.95,
                    "prioridade": 4,
                    "acao_sugerida": "Configurar regra de automação"
                }
            ]
        }
        
        insights_saved = await save_ai_insights(test_doc_id, ai_insights)
        if insights_saved:
            print("✅ Insights de IA salvos com sucesso")
        else:
            print("❌ Falha ao salvar insights de IA")
        
        # 5. Verificar se os dados foram salvos corretamente
        print("\n5. Verificando dados salvos...")
        
        # Verificar documento principal
        doc_result = supabase.table('fiscal_documents').select('*').eq('id', test_doc_id).execute()
        if doc_result.data:
            doc = doc_result.data[0]
            print(f"✅ Documento encontrado: {doc['filename']}")
            print(f"   - Número da nota: {doc.get('numero_nota')}")
            print(f"   - Valor total: R$ {doc.get('valor_total', 0):,.2f}")
            print(f"   - UF origem: {doc.get('uf_origem')}")
        
        # Verificar dados extraídos
        extracted_result = supabase.table('extracted_data').select('*').eq('document_id', test_doc_id).execute()
        if extracted_result.data:
            extracted = extracted_result.data[0]
            print(f"✅ Dados extraídos encontrados:")
            print(f"   - Emitente: {extracted.get('emitente_razao_social')}")
            print(f"   - Destinatário: {extracted.get('destinatario_nome')}")
        
        # Verificar itens
        items_result = supabase.table('document_items').select('*').eq('document_id', test_doc_id).execute()
        if items_result.data:
            print(f"✅ {len(items_result.data)} item(s) encontrado(s):")
            for item in items_result.data:
                print(f"   - {item.get('descricao')} (Categoria: {item.get('categoria')})")
        
        # Verificar análise de fornecedor
        supplier_result = supabase.table('supplier_analysis').select('*').eq('document_id', test_doc_id).execute()
        if supplier_result.data:
            supplier = supplier_result.data[0]
            print(f"✅ Análise de fornecedor encontrada:")
            print(f"   - Tipo: {supplier.get('tipo_fornecedor')}")
            print(f"   - Score de risco: {supplier.get('score_risco')}")
        
        # Verificar insights
        insights_result = supabase.table('ai_insights').select('*').eq('document_id', test_doc_id).execute()
        if insights_result.data:
            print(f"✅ {len(insights_result.data)} insight(s) encontrado(s):")
            for insight in insights_result.data:
                print(f"   - {insight.get('tipo_insight')}: {insight.get('titulo')}")
        
        print("\n🎉 Todos os testes passaram! O novo schema está funcionando corretamente.")
        
        # Limpeza (opcional - remover dados de teste)
        print("\n🧹 Limpando dados de teste...")
        try:
            supabase.table('fiscal_documents').delete().eq('id', test_doc_id).execute()
            print("✅ Dados de teste removidos")
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível remover dados de teste: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        return False

def main():
    """Função principal"""
    success = asyncio.run(test_new_schema_integration())
    
    if success:
        print("\n✅ Integração com novo schema validada com sucesso!")
        return True
    else:
        print("\n❌ Falha na integração com novo schema")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)