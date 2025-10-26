# MVP Sistema Simplificado de Análise Fiscal

## 🎯 Visão Geral

Este MVP combina o melhor do projeto alternativo com arquitetura moderna Supabase, criando um sistema simplificado para análise de documentos fiscais brasileiros com 3 agentes IA especializados.

## 🚀 Características do MVP

### Aproveitamento do Código Existente
- ✅ **FastAPI Structure**: Adaptado do projeto alternativo com CORS e middleware
- ✅ **CrewAI Integration**: Mantém framework de agentes multi-IA
- ✅ **XML Processing**: Lógica de processamento NF-e/NFS-e já testada
- ✅ **Frontend Nuxt**: Interface moderna já construída e funcional

### Arquitetura Simplificada
- 🔄 **3 Agentes IA**: XML Processing → AI Categorization → Insights Generation
- 💾 **Supabase**: Substitui JSON file storage por PostgreSQL gerenciado
- 🎨 **Frontend Responsivo**: Nuxt 4 + Tailwind CSS + DaisyUI
- 📊 **Dashboard Executivo**: Métricas em tempo real com dados reais

### Funcionalidades Principais
- 📤 **Upload XML**: Drag-and-drop com validação e processamento automático
- 🤖 **Processamento IA**: 3 agentes especializados com status em tempo real
- 📈 **Dashboard**: Métricas financeiras, fornecedores e categorização
- 💬 **Consultas Naturais**: Perguntas em português com respostas executivas
- 📄 **Relatórios PDF**: Geração automática com insights de IA

## 🛠️ Setup Rápido

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- Conta Supabase (gratuita)
- Chave OpenAI API (opcional: OpenRouter para economia)

### Instalação Automática

```bash
# Clone o repositório
git clone <repository-url>
cd ai-agents-invoice-system

# Execute o setup automático
python setup_mvp.py
```

### Configuração Manual

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Instalar modelo português do spaCy
python -m spacy download pt_core_news_sm

# Configurar ambiente
cp .env.example .env
# Editar .env com suas credenciais
```

#### 2. Frontend Setup
```bash
cd frontend
npm install

# Configurar ambiente
cp .env.example .env
# Editar .env com URL da API
```

#### 3. Configuração do Supabase

Crie um projeto no [Supabase](https://supabase.com) e configure:

**backend/.env:**
```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-chave-anonima
SUPABASE_SERVICE_KEY=sua-chave-service-role
OPENAI_API_KEY=sua-chave-openai
```

**frontend/.env:**
```env
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-chave-anonima
```

## 🚀 Executando o MVP

### 1. Iniciar Backend
```bash
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python main.py
```

### 2. Iniciar Frontend
```bash
cd frontend
npm run dev
```

### 3. Acessar Aplicação
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
ai-agents-invoice-system/
├── backend/                 # FastAPI + 3 Agentes IA
│   ├── agents/             # Agentes especializados
│   ├── api/                # Endpoints REST
│   ├── utils/              # Utilitários e configuração
│   ├── main.py             # Aplicação principal (adaptada)
│   └── requirements.txt    # Dependências (+ CrewAI)
├── frontend/               # Nuxt.js Interface
│   ├── app/                # Páginas e componentes
│   ├── components/         # Componentes reutilizáveis
│   └── composables/        # Lógica de negócio
├── xml_nf/                 # Documentos de teste
├── setup_mvp.py           # Script de setup automático
└── README_MVP_SETUP.md    # Este arquivo
```

## 🧪 Testando o Sistema

### 1. Upload de Documentos
- Acesse http://localhost:3000/upload
- Arraste arquivos XML da pasta `xml_nf/`
- Acompanhe processamento em tempo real

### 2. Dashboard Executivo
- Acesse http://localhost:3000
- Visualize métricas financeiras
- Explore gráficos de fornecedores e produtos

### 3. Consultas Naturais
- Faça perguntas em português sobre seus dados
- Receba insights executivos com IA

## 🔧 Arquitetura dos Agentes

### Agente 1: XML Processing
- **Função**: Extração e validação de dados XML
- **Input**: Arquivo XML NF-e/NFS-e
- **Output**: Dados estruturados + metadados

### Agente 2: AI Categorization
- **Função**: Categorização inteligente de produtos/serviços
- **Input**: Dados extraídos do XML
- **Output**: Categorias + subcategorias + confiança

### Agente 3: Insights Generation
- **Função**: Geração de insights executivos
- **Input**: Dados categorizados
- **Output**: Resumos + recomendações + análises

## 📊 Dados Processados

O sistema armazena no Supabase:
- **fiscal_documents**: Registros de upload
- **document_metadata**: Metadados extraídos
- **processing_results**: Resultados dos agentes
- **dim_emitente**: Dimensão de emitentes
- **dim_destinatario**: Dimensão de destinatários
- **dim_produtos**: Dimensão de produtos

## 🎯 Próximos Passos

1. **Configurar Supabase**: Criar projeto e configurar credenciais
2. **Testar Upload**: Usar arquivos da pasta xml_nf/
3. **Explorar Dashboard**: Visualizar dados processados
4. **Personalizar**: Adaptar para suas necessidades específicas

## 🆘 Solução de Problemas

### Erro de Conexão Supabase
- Verifique URL e chaves no .env
- Confirme que o projeto Supabase está ativo

### Erro de Dependências Python
- Confirme Python 3.11+
- Reinstale: `pip install -r requirements.txt`

### Erro de spaCy
- Instale modelo: `python -m spacy download pt_core_news_sm`

### Erro de Upload
- Verifique se backend está rodando na porta 8000
- Confirme formato XML válido

## 📞 Suporte

Para problemas específicos:
1. Verifique logs do backend
2. Confirme configuração do .env
3. Teste com arquivos XML da pasta xml_nf/

---

**🎉 Pronto para processar documentos fiscais com IA!**