# Project Structure & Organization

## Root Directory Layout
```
ai-agents-invoice-system/
├── backend/                 # Python FastAPI backend with multi-agent system
├── frontend/               # Nuxt.js TypeScript frontend
├── database/               # PostgreSQL/Supabase schema and setup
├── docker/                 # Docker configuration and documentation
├── scripts/                # Utility scripts (Redis startup, etc.)
├── Desafio_extra/          # Additional challenge implementation
├── Desafio_final/          # Final challenge documentation
├── docker-compose.yml      # Production Docker setup
├── docker-compose.dev.yml  # Development Docker setup
├── Makefile               # Build automation and shortcuts
└── README.md              # Main project documentation
```

## Backend Structure (`backend/`)
```
backend/
├── agents/                 # AI agent implementations
│   ├── base_agent.py      # Base agent class
│   └── __init__.py
├── api/                   # FastAPI routes and endpoints
│   ├── routes.py          # API endpoint definitions
│   └── __init__.py
├── models/                # Data models for NF-e and NFS-e
│   ├── fiscal_data.py     # Core fiscal document models
│   └── __init__.py
├── utils/                 # Utilities and configuration
│   ├── config.py          # Application configuration
│   ├── database.py        # Database connection management
│   ├── logging.py         # Structured logging setup
│   └── __init__.py
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
└── README.md             # Backend-specific documentation
```

## Frontend Structure (`frontend/`)
```
frontend/
├── app/                   # Nuxt 3 app directory structure
├── node_modules/          # Node.js dependencies (auto-generated)
├── public/               # Static assets
├── .nuxt/                # Nuxt build output (auto-generated)
├── nuxt.config.ts        # Nuxt configuration
├── package.json          # Node.js dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md             # Frontend documentation
```

## Database Structure (`database/`)
```
database/
├── schema/               # SQL schema files (organized by purpose)
│   ├── 01_create_tables.sql
│   ├── 02_nfe_tables.sql
│   ├── 03_nfse_tables.sql
│   ├── 04_views.sql
│   ├── 05_indexes.sql
│   └── 06_rls_policies.sql
├── setup.sql             # Complete database setup script
└── README.md             # Database documentation
```

## Configuration Files
- **Environment**: `.env` files for configuration (never commit actual .env files)
- **Docker**: `docker-compose.yml` for production, `docker-compose.dev.yml` for development
- **Build**: `Makefile` for common development tasks
- **Dependencies**: `requirements.txt` (Python), `package.json` (Node.js)

## Multi-Agent Architecture
The system implements 8 specialized agents:
- **Master Agent**: Central orchestrator
- **XML Processing Agent**: NF-e/NFS-e file processing
- **AI Categorization Agent**: ML-powered categorization
- **SQL Agent**: Natural language to SQL translation
- **Report Agent**: Multi-format report generation
- **Scheduler Agent**: Automated task management
- **Data Lake Agent**: Data storage and optimization
- **Monitoring Agent**: Error logging and system health

## File Naming Conventions
- **Python**: snake_case for files and functions
- **TypeScript/Vue**: kebab-case for files, camelCase for variables
- **SQL**: lowercase with underscores
- **Environment**: UPPERCASE for variables
- **Docker**: lowercase with hyphens for service names

## Key Directories to Know
- `backend/agents/`: Add new AI agents here
- `backend/api/`: API endpoint definitions
- `frontend/app/`: Nuxt 3 pages and components
- `database/schema/`: Database schema modifications
- `scripts/`: Utility scripts for development