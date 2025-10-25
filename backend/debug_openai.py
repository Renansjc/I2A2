"""
Script para debugar a configuração do OpenAI
"""

import os
import sys
from dotenv import load_dotenv

# Carregar o arquivo .env explicitamente
load_dotenv()

print("🔍 Debug da Configuração OpenAI")
print("="*50)

# Verificar se a API key está no ambiente
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OPENAI_API_KEY encontrada: {api_key[:20]}...{api_key[-10:]}")
else:
    print("❌ OPENAI_API_KEY não encontrada no ambiente")

# Verificar outras configurações
print(f"📋 OPENAI_DEFAULT_MODEL: {os.getenv('OPENAI_DEFAULT_MODEL')}")
print(f"📋 OPENAI_FALLBACK_MODEL: {os.getenv('OPENAI_FALLBACK_MODEL')}")
print(f"📋 OPENAI_MAX_TOKENS: {os.getenv('OPENAI_MAX_TOKENS')}")
print(f"📋 OPENAI_TEMPERATURE: {os.getenv('OPENAI_TEMPERATURE')}")

# Testar importação do OpenAI
try:
    import openai
    print("✅ Biblioteca openai importada com sucesso")
    
    # Testar configuração
    from utils.config import settings
    print(f"✅ Settings carregadas - API Key: {settings.OPENAI_API_KEY[:20] if settings.OPENAI_API_KEY else 'None'}...")
    print(f"✅ Modelo padrão: {settings.OPENAI_DEFAULT_MODEL}")
    
except ImportError as e:
    print(f"❌ Erro ao importar openai: {e}")
except Exception as e:
    print(f"❌ Erro ao carregar settings: {e}")

# Testar conexão com OpenAI (se a key estiver disponível)
if api_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        print("\n🧪 Testando conexão com OpenAI...")
        
        # Fazer uma chamada simples
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Responda apenas 'OK' se você conseguir me ouvir."}
            ],
            max_tokens=10
        )
        
        print(f"✅ Conexão bem-sucedida! Resposta: {response.choices[0].message.content}")
        print(f"📊 Tokens usados: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")

print("\n🔧 Próximos passos:")
print("1. Se a API key não foi encontrada, verifique o arquivo .env")
print("2. Se o modelo está incorreto, corrija no .env")
print("3. Se a conexão falhou, verifique se a API key é válida")
print("4. Execute: python debug_openai.py")