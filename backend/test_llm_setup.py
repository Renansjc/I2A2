#!/usr/bin/env python3
"""
Script de teste para verificar se o setup do LLM está funcionando
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("🔍 Testando imports...")
    
    try:
        from utils.llm_config import configuracoes_llm_padrao, ConfiguracoesLLM
        print("✅ llm_config importado com sucesso")
        
        from utils.prompt_manager import gerenciador_prompts
        print(f"✅ prompt_manager importado - {len(gerenciador_prompts.templates)} templates disponíveis")
        
        # Listar templates disponíveis
        templates = gerenciador_prompts.listar_templates()
        for template in templates:
            print(f"   📝 Template: {template}")
        
        from utils.openai_integration import ServicoIntegracaoOpenAI
        print("✅ openai_integration importado com sucesso")
        
        from utils.context_manager import GerenciadorContexto
        print("✅ context_manager importado com sucesso")
        
        from utils.llm_service import ServicoLLMIntegrado
        print("✅ llm_service importado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no import: {e}")
        traceback.print_exc()
        return False

def test_configurations():
    """Testa se as configurações estão válidas"""
    print("\n🔧 Testando configurações...")
    
    try:
        from utils.llm_config import configuracoes_llm_padrao
        
        # Validar configurações
        problemas = configuracoes_llm_padrao.validar_configuracao()
        
        if not problemas:
            print("✅ Configurações válidas")
        else:
            print("⚠️ Problemas encontrados nas configurações:")
            for problema in problemas:
                print(f"   - {problema}")
        
        # Mostrar configurações principais
        print(f"   🤖 Modelo padrão: {configuracoes_llm_padrao.modelo_padrao}")
        print(f"   🤖 Modelo fallback: {configuracoes_llm_padrao.modelo_fallback}")
        print(f"   💾 Cache habilitado: {configuracoes_llm_padrao.cache.habilitado}")
        print(f"   🚦 Rate limit RPM: {configuracoes_llm_padrao.rate_limiting.requests_per_minute}")
        
        return len(problemas) == 0
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        traceback.print_exc()
        return False

def test_prompt_rendering():
    """Testa se os templates de prompt podem ser renderizados"""
    print("\n📝 Testando renderização de prompts...")
    
    try:
        from utils.prompt_manager import gerenciador_prompts
        
        # Testar template de interpretação de consulta
        variaveis_teste = {
            "consulta": "Quais foram os maiores fornecedores no último trimestre?",
            "cargo_usuario": "CEO"
        }
        
        template_renderizado, erros = gerenciador_prompts.renderizar_template(
            "master_agent_interpretacao_consulta", 
            variaveis_teste
        )
        
        if not erros:
            print("✅ Template renderizado com sucesso")
            print(f"   📏 Tamanho do prompt: {len(template_renderizado)} caracteres")
        else:
            print("❌ Erros na renderização:")
            for erro in erros:
                print(f"   - {erro}")
            return False
        
        # Testar template de categorização
        variaveis_categorizacao = {
            "itens": ["Açúcar cristal", "Embalagem plástica"],
            "tipo_categoria": "produto"
        }
        
        template_cat, erros_cat = gerenciador_prompts.renderizar_template(
            "categorizacao_produtos",
            variaveis_categorizacao
        )
        
        if not erros_cat:
            print("✅ Template de categorização renderizado com sucesso")
        else:
            print("❌ Erros na renderização de categorização:")
            for erro in erros_cat:
                print(f"   - {erro}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na renderização: {e}")
        traceback.print_exc()
        return False

def test_environment_variables():
    """Testa se as variáveis de ambiente estão configuradas"""
    print("\n🌍 Testando variáveis de ambiente...")
    
    try:
        from utils.config import settings
        
        # Verificar variáveis críticas
        variaveis_criticas = [
            ("OPENAI_API_KEY", settings.OPENAI_API_KEY),
            ("REDIS_URL", settings.REDIS_URL),
            ("DEBUG", settings.DEBUG)
        ]
        
        for nome, valor in variaveis_criticas:
            if valor:
                if nome == "OPENAI_API_KEY":
                    # Mascarar a chave
                    valor_mostrar = f"{valor[:8]}...{valor[-4:]}" if len(valor) > 12 else "***"
                    print(f"✅ {nome}: {valor_mostrar}")
                else:
                    print(f"✅ {nome}: {valor}")
            else:
                print(f"⚠️ {nome}: não configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar variáveis: {e}")
        traceback.print_exc()
        return False

def main():
    """Função principal do teste"""
    print("🚀 Iniciando testes do setup LLM")
    print("=" * 50)
    print(f"⏰ Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 50)
    
    testes = [
        ("Imports", test_imports),
        ("Configurações", test_configurations),
        ("Renderização de Prompts", test_prompt_rendering),
        ("Variáveis de Ambiente", test_environment_variables)
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        try:
            resultado = funcao_teste()
            resultados.append((nome_teste, resultado))
        except Exception as e:
            print(f"❌ Erro crítico no teste {nome_teste}: {e}")
            resultados.append((nome_teste, False))
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    sucessos = 0
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"{nome}: {status}")
        if resultado:
            sucessos += 1
    
    print(f"\n🎯 Resultado: {sucessos}/{len(resultados)} testes passaram")
    
    if sucessos == len(resultados):
        print("🎉 Todos os testes passaram! O setup LLM está funcionando.")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique as configurações.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)