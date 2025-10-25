# Dependências do Backend - AI Agents Invoice Analysis System

## Visão Geral

Este documento descreve todas as dependências necessárias para o funcionamento do sistema de análise de notas fiscais com agentes de IA.

## Dependências Principais

### Framework Web
- **FastAPI 0.115.0**: Framework web moderno e rápido para APIs
- **Uvicorn 0.32.0**: Servidor ASGI para FastAPI
- **python-multipart 0.0.20**: Suporte para upload de arquivos

### Framework Multi-Agente
- **CrewAI 0.203.1**: Framework para coordenação de múltiplos agentes de IA
- **LangChain 0.3.9**: Framework para aplicações com LLM
- **langchain-community 0.3.9**: Extensões da comunidade para LangChain

### Processamento XML
- **lxml 6.0.2**: Biblioteca para processamento XML/HTML
- **xmlschema 4.2.0**: Validação de esquemas XML
- **elementpath 5.0.4**: Dependência do xmlschema para XPath

### Banco de Dados
- **asyncpg 0.30.0**: Driver assíncrono para PostgreSQL
- **supabase 2.9.1**: Cliente para Supabase (PostgreSQL como serviço)

### Processamento de Dados
- **numpy 2.3.4**: Biblioteca fundamental para computação científica

### Fila de Tarefas e Cache
- **celery 5.3.6**: Sistema de fila de tarefas distribuído
- **redis 5.2.1**: Banco de dados em memória para cache e filas

### Configuração e Validação
- **python-dotenv 1.1.1**: Carregamento de variáveis de ambiente
- **pydantic 2.12.3**: Validação de dados usando type hints
- **pydantic-settings 2.11.0**: Gerenciamento de configurações com Pydantic
- **typing-extensions 4.15.0**: Extensões para type hints
- **typing-inspection 0.4.2**: Inspeção de tipos em runtime
- **typing-inspect 0.9.0**: Utilitários para inspeção de tipos
- **annotated-types 0.7.0**: Tipos anotados para Pydantic
- **pydantic-core 2.41.4**: Core do Pydantic em Rust

### Logging e Monitoramento
- **structlog 25.4.0**: Logging estruturado
- **sentry-sdk[fastapi] 2.19.2**: Monitoramento de erros

### Processamento de Arquivos
- **watchdog 6.0.0**: Monitoramento de sistema de arquivos

### Geração de Relatórios
- **openpyxl 3.1.5**: Leitura/escrita de arquivos Excel
- **python-docx 1.1.2**: Criação de documentos Word
- **jinja2 3.1.4**: Engine de templates
- **reportlab 4.4.4**: Geração de PDFs

### Cliente HTTP
- **httpx 0.27.2**: Cliente HTTP assíncrono

### Testes (Desenvolvimento)
- **pytest 8.3.4**: Framework de testes
- **pytest-asyncio 0.24.0**: Suporte para testes assíncronos
- **pytest-mock 3.14.0**: Mocking para testes

## Instalação

### Pré-requisitos
- Python 3.13.9 ou superior
- Ambiente virtual (recomendado)

### Passos de Instalação

1. **Criar ambiente virtual:**
   ```bash
   python -m venv venv
   ```

2. **Ativar ambiente virtual:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

### Verificação da Instalação

Para verificar se todas as dependências foram instaladas corretamente:

```python
# Teste básico de imports
import structlog
import pydantic
import lxml
import xmlschema
import watchdog
import fastapi

print("✅ Todas as dependências principais estão funcionando!")
```

## Dependências Opcionais

As seguintes dependências são opcionais e podem ser instaladas conforme necessário:

- **pandas 2.2.3**: Para análise avançada de dados
- **scikit-learn ≥1.5.2**: Para recursos de machine learning (requer compilador C++)
- **spacy 3.8.7**: Para processamento de linguagem natural (requer compilador C++)

## Notas Importantes

1. **Compilador C++**: Algumas dependências opcionais (scikit-learn, spacy) requerem um compilador C++ instalado no sistema.

2. **Ambiente Windows**: Todas as dependências foram testadas no Windows com Python 3.13.9.

3. **Versões Fixas**: As versões estão fixadas para garantir compatibilidade e reprodutibilidade.

4. **Atualizações**: Antes de atualizar qualquer dependência, teste em ambiente de desenvolvimento.

## Resolução de Problemas

### Erro de Importação
Se encontrar erros de importação, verifique se:
- O ambiente virtual está ativado
- Todas as dependências foram instaladas
- As versões estão corretas

### Problemas de Compilação
Para dependências que requerem compilação:
- Windows: Instale Visual Studio Build Tools
- Linux: Instale build-essential
- Mac: Instale Xcode Command Line Tools

### Conflitos de Versão
Se houver conflitos de versão:
1. Recrie o ambiente virtual
2. Instale as dependências na ordem especificada
3. Use `pip freeze` para verificar as versões instaladas