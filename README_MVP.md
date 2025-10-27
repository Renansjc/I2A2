# MVP Sistema Simplificado de Análise Fiscal

Sistema MVP que aproveita código do projeto alternativo com arquitetura moderna Nuxt.js + FastAPI + Supabase.

## 🎯 Funcionalidades MVP

### ✅ Implementado
- **Upload de XML**: Interface drag-and-drop para documentos fiscais
- **3 Agentes IA**: Processamento XML, Categorização IA, Insights Executivos
- **Dashboard Executivo**: Métricas financeiras em tempo real
- **Consultas Naturais**: Interface em português com LLM
- **Frontend Nuxt 4**: Aproveitado do projeto atual com componentes modernos

### 🔄 Adaptações Realizadas
- **Backend**: Adaptado do `alternativa/I2A2_EntregaFinal/backend/api/main.py`
- **Requirements**: Mantido CrewAI + adicionado Supabase
- **Frontend**: Aproveitado Nuxt atual (mais avançado que React do alternativo)
- **Storage**: Migração de JSON file → Supabase PostgreSQL

## 🚀 Setup Rápido

### 1. Backend
```bash
cd backend

# Ativar ambiente virtual (já criado com Python 3.12)
activate_venv.bat

# OU manualmente:
# venv\Scripts\activate
# pip install -r requirements_minimal.txt

# Configurar API keys
copy .env.example .env
# Edite .env: OPENAI_API_KEY=sua-chave-aqui

# Iniciar servidor
python main.py
```

### 2. Database
```bash
# Execute no Supabase SQL Editor:
# database/mvp_schema.sql
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Arquitetura MVP

```
Frontend (Nuxt 4) ←→ Backend (FastAPI) ←→ Supabase (PostgreSQL)
                           ↓
                   3 Agentes IA (OpenAI GPT-4o-mini)
```

### Agentes IA (Simplificados)
1. **Agente XML**: Extrai dados estruturados de documentos fiscais
2. **Agente Categorização**: Classifica produtos/serviços com LLM
3. **Agente Insights**: Gera análises executivas automáticas

## 🔧 Principais Adaptações

### Do Projeto Alternativo
- ✅ **FastAPI structure**: CORS, middleware, error handling
- ✅ **LLM integration**: OpenAI GPT-4o-mini + Langchain
- ✅ **Document processing**: XML parsing, text extraction
- ✅ **Background tasks**: Async processing
- ✅ **Requirements.txt**: CrewAI + dependencies

### Melhorias MVP
- 🆕 **Supabase integration**: PostgreSQL + Storage
- 🆕 **Nuxt 4 frontend**: Mais moderno que React alternativo
- 🆕 **Simplified schema**: 4 tabelas otimizadas
- 🆕 **Executive dashboard**: Métricas em tempo real
- 🆕 **Natural language**: Consultas em português

## 📁 Estrutura do Projeto

```
├── alternativa/           # Projeto original (mantido para referência)
├── bkp/                  # Backup do projeto anterior
├── backend/              # FastAPI adaptado do alternativo
│   ├── main.py          # API principal (adaptada)
│   ├── requirements.txt # Dependencies (CrewAI mantido)
│   └── .env.example     # Configuration template
├── frontend/             # Nuxt 4 (aproveitado do projeto atual)
│   ├── app/             # Pages, components, composables
│   ├── package.json     # Nuxt dependencies
│   └── nuxt.config.ts   # Nuxt configuration
└── database/             # Supabase schema
    └── mvp_schema.sql   # Simplified tables
```

## 🎨 Frontend (Aproveitado)

### Páginas Mantidas
- `/` - Dashboard executivo principal
- `/upload` - Upload de XML com processamento
- `/documents` - Lista de documentos processados
- `/documents/[id]` - Detalhes do documento

### Componentes Reutilizados
- `XMLUpload.vue` - Upload com drag-and-drop
- `FinancialSummary.vue` - Métricas financeiras
- `SuppliersChart.vue` - Gráfico de fornecedores
- `QueryInput.vue` - Interface de consultas naturais

## 🔗 APIs Implementadas

### Upload e Processamento
- `POST /api/v1/documents/upload` - Upload de XML
- `GET /api/v1/documents` - Lista documentos
- `GET /api/v1/documents/{id}` - Detalhes do documento

### Dashboard Executivo
- `GET /api/v1/dashboard/summary` - Resumo financeiro
- `POST /api/v1/query/natural` - Consultas em linguagem natural

## 🧪 Teste Rápido

1. **Start backend**: `cd backend && python main.py`
2. **Teste API**: `cd backend && python test_mvp.py`
3. **Start frontend**: `cd frontend && npm run dev`
4. **Upload XML**: Acesse http://localhost:3000/upload
5. **Ver dashboard**: Acesse http://localhost:3000

### ⚠️ Configuração OpenAI
Para usar IA completa, configure no `.env`:
```
OPENAI_API_KEY=sua-chave-openai-aqui
```
Sem a chave, o sistema usa parser heurístico (funcional mas limitado).

## 📈 Próximos Passos

1. **Integrar Supabase**: Substituir JSON storage por PostgreSQL
2. **Melhorar agentes**: Adicionar mais inteligência aos 3 agentes
3. **Relatórios PDF**: Implementar geração automática
4. **Autenticação**: Adicionar login/registro
5. **Deploy**: Configurar produção

---

**MVP pronto em minutos aproveitando o melhor dos dois projetos!** 🚀