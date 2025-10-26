# MVP Sistema Simplificado de Análise Fiscal - Setup Guide

Este guia descreve como configurar o MVP do Sistema Simplificado de Análise Fiscal, aproveitando o código do projeto alternativo com arquitetura moderna.

## 🎯 Visão Geral do MVP

O MVP implementa as funcionalidades essenciais:
- ✅ Upload simplificado de documentos XML (NF-e/NFS-e)
- ✅ Processamento automático com 3 agentes IA
- ✅ Dashboard executivo com dados reais
- ✅ Consultas em linguagem natural (português)
- ✅ Geração de relatórios PDF executivos
- ✅ Arquitetura moderna sem complexidade de autenticação

## 🏗️ Arquitetura Simplificada

```
Frontend (Nuxt.js) ←→ Backend (FastAPI) ←→ Supabase (PostgreSQL + Storage)
                                ↓
                        OpenAI GPT-4o-mini (3 Agentes IA)
```

## 📋 Pré-requisitos

- **Python 3.11+** (testado com 3.13.9)
- **Node.js 18+** para o frontend
- **Conta Supabase** (gratuita)
- **Chave OpenAI API** ou **OpenRouter API** (mais econômico)

## 🚀 Setup Rápido

### 1. Configuração do Backend

```bash
# Clone e navegue para o backend
cd backend

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Configure ambiente
copy .env.mvp.example .env
# Edite .env com suas configurações
```

### 2. Configuração do Supabase

#### 2.1 Criar Projeto Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Crie novo projeto
3. Anote a URL e Service Key

#### 2.2 Configurar Database
1. Vá para SQL Editor no Supabase
2. Execute o conteúdo de `database/mvp_setup.sql`
3. Isso criará as tabelas simplificadas:
   - `fiscal_documents` - Documentos fiscais
   - `extracted_data` - Dados extraídos do XML
   - `document_items` - Itens dos documentos
   - `executive_reports` - Relatórios executivos

#### 2.3 Configurar Storage
1. Vá para Storage no Supabase
2. Crie bucket `invoice-xmls` (público)
3. Execute `database/schema/mvp_storage_setup.sql` para políticas

### 3. Configuração do Frontend

```bash
# Navegue para frontend
cd frontend

# Instale dependências
npm install

# Configure ambiente
copy .env.example .env
# Configure NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4. Configuração das Variáveis de Ambiente

Edite o arquivo `.env` no backend:

```env
# Supabase (obrigatório)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=sua-service-key-aqui

# OpenAI (escolha uma opção)
OPENAI_API_KEY=sua-chave-openai
# OU OpenRouter (mais econômico)
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui

# Storage
STORAGE_BUCKET=invoice-xmls
```

## 🧪 Teste da Configuração

```bash
# Teste a configuração
cd backend
python setup_mvp.py --test

# Se tudo estiver OK, você verá:
# ✅ MVP setup test passed! You're ready to start the application.
```

## 🏃‍♂️ Executando o MVP

### Backend
```bash
cd backend
python main.py
# Acesse: http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev
# Acesse: http://localhost:3000
```

## 📊 Funcionalidades Implementadas

### 1. Upload de XML
- Interface drag-and-drop
- Validação automática de arquivos
- Suporte para NF-e e NFS-e
- Armazenamento seguro no Supabase

### 2. Processamento com IA
- **Agente XML**: Extrai dados estruturados
- **Agente Categorização**: Classifica produtos/serviços
- **Agente Insights**: Gera análises executivas

### 3. Dashboard Executivo
- Métricas financeiras em tempo real
- Gráficos de fornecedores principais
- Análise de categorias de produtos
- Evolução temporal

### 4. Consultas Naturais
- Perguntas em português
- Processamento com GPT-4o-mini
- Respostas executivas contextualizadas
- Sugestões inteligentes

### 5. Relatórios PDF
- Geração automática
- Templates executivos
- Insights de IA
- Download imediato

## 🔧 Estrutura do Banco de Dados

### Tabelas Principais

```sql
-- Documentos fiscais
fiscal_documents (id, filename, file_path, status, processing_progress, ...)

-- Dados extraídos
extracted_data (id, document_id, emitente, destinatario, valor_total, ...)

-- Itens dos documentos
document_items (id, document_id, descricao, quantidade, valor_total, categoria, ...)

-- Relatórios executivos
executive_reports (id, title, file_path, report_type, generated_at, ...)
```

## 🎨 Frontend Simplificado

### Páginas Principais
- `/` - Dashboard executivo
- `/upload` - Upload de XML
- `/documents` - Lista de documentos
- `/documents/[id]` - Detalhes do documento

### Componentes Reutilizados
- `XMLUpload.vue` - Upload com drag-and-drop
- `FinancialSummary.vue` - Métricas financeiras
- `SuppliersChart.vue` - Gráfico de fornecedores
- `QueryInput.vue` - Interface de consultas naturais

## 🔍 Troubleshooting

### Erro de Conexão Supabase
```bash
# Verifique as variáveis de ambiente
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Teste a conexão
python -c "from utils.mvp_database import mvp_supabase; print(mvp_supabase.client)"
```

### Erro de OpenAI API
```bash
# Verifique a chave
echo $OPENAI_API_KEY

# Teste a API
python -c "import openai; openai.api_key='sua-chave'; print('OK')"
```

### Erro de Storage
1. Verifique se o bucket `invoice-xmls` existe
2. Confirme que está configurado como público
3. Execute as políticas de storage

## 📈 Próximos Passos

Após o MVP funcionando:

1. **Autenticação**: Implementar login/registro
2. **Multi-tenant**: Separação por usuário
3. **Analytics Avançados**: Mais insights de IA
4. **Integração ERP**: Conectar com sistemas existentes
5. **Mobile App**: Versão mobile nativa

## 🆘 Suporte

Para problemas:
1. Verifique os logs: `tail -f backend/logs/app.log`
2. Execute testes: `python setup_mvp.py --test`
3. Consulte documentação do Supabase
4. Verifique limites da API OpenAI

## 📝 Notas Importantes

- **Sem RLS**: O MVP usa acesso direto ao banco (simplificado)
- **Chaves de API**: Mantenha seguras, não commite no Git
- **Limites**: OpenAI tem limites de rate, considere OpenRouter
- **Backup**: Configure backup automático no Supabase
- **Monitoramento**: Acompanhe uso de tokens OpenAI

---

**MVP Sistema Simplificado de Análise Fiscal** - Transformando documentos fiscais em insights executivos com IA! 🚀