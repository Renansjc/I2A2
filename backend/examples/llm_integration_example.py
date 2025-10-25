"""
Exemplo de uso do Serviço de Integração OpenAI
Demonstra como usar as capacidades LLM no sistema
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Importar serviços LLM
from backend.utils.llm_service import obter_servico_llm
from backend.utils.context_manager import ContextoEmpresarial, PreferenciasUsuario


async def exemplo_consulta_natural():
    """Exemplo de processamento de consulta natural"""
    print("=== Exemplo: Consulta Natural ===")
    
    # Obter serviço LLM
    servico = await obter_servico_llm()
    
    # Criar sessão para usuário
    contexto_empresarial = {
        "empresa_id": "empresa_exemplo_123",
        "setor_atuacao": "Indústria Alimentícia",
        "porte_empresa": "media",
        "regioes_operacao": ["São Paulo", "Rio de Janeiro"],
        "principais_fornecedores": ["Fornecedor A", "Fornecedor B"],
        "categorias_produtos": ["Matéria Prima", "Embalagens", "Insumos"]
    }
    
    preferencias = {
        "idioma_preferido": "pt-BR",
        "nivel_detalhamento": "executivo",
        "tipos_relatorio_preferidos": ["financeiro", "operacional"]
    }
    
    sessao_id = await servico.criar_sessao_usuario(
        usuario_id="ceo_exemplo",
        contexto_empresarial=contexto_empresarial,
        preferencias=preferencias
    )
    
    print(f"Sessão criada: {sessao_id}")
    
    # Processar consulta natural
    consulta = "Quais foram os maiores fornecedores no último trimestre e qual o impacto no nosso custo?"
    
    resultado = await servico.processar_consulta_natural(
        sessao_id=sessao_id,
        consulta=consulta,
        cargo_usuario="CEO"
    )
    
    print(f"Resultado da consulta:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Encerrar sessão
    await servico.encerrar_sessao_usuario(sessao_id)
    print("Sessão encerrada")


async def exemplo_analise_documento():
    """Exemplo de análise de documento fiscal"""
    print("\n=== Exemplo: Análise de Documento ===")
    
    servico = await obter_servico_llm()
    
    # Criar sessão
    sessao_id = await servico.criar_sessao_usuario("analista_fiscal")
    
    # Dados simulados de uma NF-e
    conteudo_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <NFe>
        <infNFe>
            <emit>
                <CNPJ>12345678000195</CNPJ>
                <xNome>Fornecedor Exemplo Ltda</xNome>
            </emit>
            <det>
                <prod>
                    <cProd>001</cProd>
                    <xProd>Matéria Prima Industrial</xProd>
                    <vProd>1500.00</vProd>
                </prod>
            </det>
        </infNFe>
    </NFe>"""
    
    info_fornecedor = {
        "cnpj": "12345678000195",
        "nome": "Fornecedor Exemplo Ltda",
        "tipo": "Fornecedor Nacional"
    }
    
    itens = [
        {
            "codigo": "001",
            "descricao": "Matéria Prima Industrial",
            "valor": 1500.00,
            "quantidade": 100,
            "unidade": "KG"
        }
    ]
    
    resultado = await servico.analisar_documento_fiscal(
        sessao_id=sessao_id,
        conteudo_xml=conteudo_xml,
        tipo_documento="NF-e",
        info_fornecedor=info_fornecedor,
        itens=itens,
        valor_total=1500.00
    )
    
    print("Resultado da análise:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    await servico.encerrar_sessao_usuario(sessao_id)


async def exemplo_categorizacao_produtos():
    """Exemplo de categorização inteligente de produtos"""
    print("\n=== Exemplo: Categorização de Produtos ===")
    
    servico = await obter_servico_llm()
    sessao_id = await servico.criar_sessao_usuario("gerente_compras")
    
    produtos = [
        "Açúcar cristal especial 50kg",
        "Embalagem plástica transparente 500ml",
        "Corante alimentício vermelho",
        "Papel para rótulos adesivos",
        "Óleo de soja refinado 20L"
    ]
    
    contexto_empresarial = {
        "setor_atuacao": "Indústria de Bebidas",
        "categorias_existentes": ["Matéria Prima", "Embalagens", "Insumos", "Material de Escritório"]
    }
    
    resultado = await servico.categorizar_produtos_inteligente(
        sessao_id=sessao_id,
        produtos=produtos,
        contexto_empresarial=contexto_empresarial
    )
    
    print("Resultado da categorização:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    await servico.encerrar_sessao_usuario(sessao_id)


async def exemplo_traducao_sql():
    """Exemplo de tradução de consulta natural para SQL"""
    print("\n=== Exemplo: Tradução SQL ===")
    
    servico = await obter_servico_llm()
    sessao_id = await servico.criar_sessao_usuario("analista_dados")
    
    consulta_natural = "Mostre os 10 fornecedores com maior valor total de compras nos últimos 6 meses"
    
    schema_banco = {
        "tabelas": {
            "fornecedores": {
                "campos": ["id", "cnpj", "nome", "tipo"],
                "descricao": "Dados dos fornecedores"
            },
            "notas_fiscais": {
                "campos": ["id", "fornecedor_id", "valor_total", "data_emissao"],
                "descricao": "Notas fiscais recebidas"
            }
        },
        "relacionamentos": [
            "fornecedores.id = notas_fiscais.fornecedor_id"
        ]
    }
    
    resultado = await servico.traduzir_consulta_sql(
        sessao_id=sessao_id,
        consulta_natural=consulta_natural,
        schema_banco=schema_banco
    )
    
    print("Resultado da tradução:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    await servico.encerrar_sessao_usuario(sessao_id)


async def exemplo_relatorio_executivo():
    """Exemplo de geração de relatório executivo"""
    print("\n=== Exemplo: Relatório Executivo ===")
    
    servico = await obter_servico_llm()
    sessao_id = await servico.criar_sessao_usuario("cfo")
    
    dados_analise = {
        "periodo": "Q3 2024",
        "total_fornecedores": 45,
        "valor_total_compras": 2500000.00,
        "crescimento_trimestre": 0.15,
        "principais_categorias": [
            {"categoria": "Matéria Prima", "valor": 1500000.00, "percentual": 60},
            {"categoria": "Embalagens", "valor": 600000.00, "percentual": 24},
            {"categoria": "Insumos", "valor": 400000.00, "percentual": 16}
        ],
        "fornecedores_top5": [
            {"nome": "Fornecedor A", "valor": 500000.00},
            {"nome": "Fornecedor B", "valor": 350000.00},
            {"nome": "Fornecedor C", "valor": 280000.00}
        ]
    }
    
    resultado = await servico.gerar_relatorio_executivo(
        sessao_id=sessao_id,
        dados_analise=dados_analise,
        publico_alvo="CFO",
        periodo_analise="Q3 2024"
    )
    
    print("Resultado do relatório:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    await servico.encerrar_sessao_usuario(sessao_id)


async def exemplo_metricas_servico():
    """Exemplo de obtenção de métricas do serviço"""
    print("\n=== Exemplo: Métricas do Serviço ===")
    
    servico = await obter_servico_llm()
    
    # Obter métricas gerais
    metricas = servico.obter_metricas_servico()
    print("Métricas do serviço:")
    print(json.dumps(metricas, indent=2, ensure_ascii=False))
    
    # Validar configuração
    validacao = servico.validar_configuracao()
    print("\nValidação da configuração:")
    print(json.dumps(validacao, indent=2, ensure_ascii=False))


async def main():
    """Função principal que executa todos os exemplos"""
    print("🚀 Iniciando exemplos do Serviço LLM Integrado")
    print("=" * 50)
    
    try:
        # Executar exemplos
        await exemplo_consulta_natural()
        await exemplo_analise_documento()
        await exemplo_categorizacao_produtos()
        await exemplo_traducao_sql()
        await exemplo_relatorio_executivo()
        await exemplo_metricas_servico()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução dos exemplos: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Finalizar serviços
        from backend.utils.llm_service import finalizar_servicos_llm
        await finalizar_servicos_llm()
        print("\n🔚 Serviços LLM finalizados")


if __name__ == "__main__":
    # Executar exemplos
    asyncio.run(main())