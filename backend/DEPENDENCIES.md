# 📦 Dependencies - AI Agents Invoice System

Documentação completa das dependências do sistema de análise de faturas com agentes de IA.

## ✅ Status das Dependências

**Última verificação**: 2025-10-25  
**Python**: 3.13.9  
**Sistema**: Windows  
**Status**: ✅ Todas as 25 dependências instaladas e funcionando

## 🚀 Dependências Principais

### Web Framework

- **FastAPI** `0.115.0` - Framework web moderno e rápido
- **Uvicorn** `0.32.0` - Servidor ASGI de alta performance
- **python-multipart** `0.0.20` - Suporte para upload de arquivos

### Multi-Agent Framework

- **CrewAI** `0.203.1` - Framework para sistemas multi-agentes
- **LangChain** `0.3.9` - Framework para aplicações com LLM
- **LangChain Community** `0.3.9` - Extensões da comunidade

### Processamento de Dados

- **lxml** `6.0.2` - Processamento XML/HTML de alta performance
- **NumPy** `2.3.4` - Computação numérica fundamental

### Banco de Dados

- **AsyncPG** `0.30.0` - Driver PostgreSQL assíncrono
- **Supabase** `2.9.1` - Cliente Python para Supabase

### Cache e Filas

- **Celery** `5.3.6` - Sistema de filas de tarefas distribuídas
- **Redis** `5.2.1` - Cliente Python para Redis

### Configuração e Ambiente

- **python-dotenv** `1.1.1` - Carregamento de variáveis de ambiente
- **Pydantic** `2.12.3` - Validação de dados com type hints
- **Pydantic Settings** `2.11.0` - Gerenciamento de configurações

### Logging e Monitoramento

- **Structlog** `25.4.0` - Logging estruturado
- **Sentry SDK** `2.19.2` - Monitoramento de erros

### Processamento de Arquivos

- **Watchdog** `6.0.0` - Monitoramento de sistema de arquivos
- **OpenPyXL** `3.1.5` - Leitura/escrita de arquivos Excel
- **python-docx** `1.1.2` - Manipulação de documentos Word
- **Jinja2** `3.1.4` - Engine de templates

### HTTP Client

- **HTTPX** `0.27.2` - Cliente HTTP assíncrono

### Testes (Desenvolvimento)

- **pytest** `8.3.4` - Framework de testes
- **pytest-asyncio** `0.24.0` - Suporte para testes assíncronos
- **pytest-mock** `3.14.0` - Mocking para testes

## 🛠️ Instalação

### Instalação Completa

```bash
cd backend
pip install -r requirements.txt
```

### Verificação das Dependências

```bash
cd backend
python check_dependencies.py
```

### Instalação Individual (se necessário)

```bash
# Web Framework
pip install fastapi==0.115.0 uvicorn[standard]==0.32.0 python-multipart==0.0.20

# AI/ML Framework
pip install crewai==0.203.1 langchain==0.3.9 langchain-community==0.3.9

# Banco de Dados
pip install asyncpg==0.30.0 supabase==2.9.1

# Cache e Filas
pip install celery==5.3.6 redis==5.2.1

# Utilitários
pip install structlog==25.4.0 sentry-sdk[fastapi]==2.19.2
```

## 📋 Dependências Opcionais

Estas dependências requerem compilador C++ e não foram instaladas:

```bash
# Machine Learning (opcional)
pip install pandas==2.1.4
pip install scikit-learn==1.4.2
pip install spacy==3.7.4

# Geração de PDF (opcional)
pip install reportlab==4.2.5
```

## 🔧 Resolução de Problemas

### Erro de Compilação

Se encontrar erros de compilação (especialmente com pandas, numpy, etc.):

1. Instale o Visual Studio Build Tools
2. Ou use versões pré-compiladas (wheels)
3. Ou pule as dependências opcionais

### Conflitos de Versão

```bash
# Limpar cache do pip
pip cache purge

# Reinstalar dependências
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### Verificar Instalação

```bash
# Verificar todas as dependências
python check_dependencies.py

# Testar imports específicos
python -c "import fastapi, crewai, langchain; print('✅ Core packages OK')"
```

## 🐳 Docker (Alternativa)

Se tiver problemas com dependências locais, considere usar Docker:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## 📊 Estatísticas

- **Total de dependências**: 25
- **Tamanho aproximado**: ~500MB (com todas as dependências)
- **Tempo de instalação**: ~5-10 minutos
- **Compatibilidade**: Python 3.10+

## 🔄 Atualizações

Para atualizar dependências:

```bash
# Verificar versões desatualizadas
pip list --outdated

# Atualizar pacote específico
pip install --upgrade fastapi

# Atualizar requirements.txt
pip freeze > requirements.txt
```

## 📝 Notas

1. **Python 3.13**: Algumas dependências podem ter compatibilidade limitada
2. **Windows**: Algumas dependências podem precisar de Visual Studio Build Tools
3. **Produção**: Considere usar versões fixas (como no requirements.txt)
4. **Desenvolvimento**: Use ambiente virtual (venv) sempre
