# Project Structure & Organization

## Root Directory Layout

```
ai-agents-invoice-system/
├── backend/                 # Python FastAPI backend with multi-agent system
├── frontend/               # Next.js TypeScript frontend
├── database/               # PostgreSQL/Supabase schema and setup
├── docker/                 # Docker configurations and documentation
├── scripts/                # Utility scripts (Redis startup, etc.)
├── Desafio_extra/          # Additional challenge implementation
├── Desafio_final/          # Final challenge documentation
├── .kiro/                  # Kiro AI assistant configuration
├── docker-compose.yml      # Main Docker services
├── docker-compose.dev.yml  # Development Docker services
├── Makefile               # Build and deployment commands
└── README.md              # Main project documentation
```

## Backend Structure (`backend/`)

```
backend/
├── agents/                 # Multi-agent system implementations
│   ├── master_agent.py    # Main orchestrator agent
│   ├── xml_processing_agent.py  # XML file processing
│   ├── ai_categorization_agent.py  # ML categorization
│   ├── sql_agent.py       # Natural language to SQL
│   ├── report_agent.py    # Report generation
│   ├── scheduler_agent.py # Task scheduling
│   ├── data_lake_agent.py # Data management
│   └── monitoring_agent.py # System monitoring
├── api/                   # FastAPI routes and endpoints
│   ├── routes/           # API route definitions
│   └── middleware/       # Custom middleware
├── models/               # Data models and schemas
│   ├── nfe_models.py    # NF-e data structures
│   ├── nfse_models.py   # NFS-e data structures
│   └── common_models.py # Shared data models
├── utils/               # Utility functions and helpers
│   ├── config.py       # Configuration management
│   ├── database.py     # Database connections
│   ├── logging.py      # Structured logging setup
│   └── xml_parser.py   # XML processing utilities
├── venv/               # Python virtual environment
├── __pycache__/        # Python bytecode cache
├── main.py             # FastAPI application entry point
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── .env.example       # Environment template
├── DEPENDENCIES.md    # Dependency documentation
└── README.md          # Backend documentation
```

## Frontend Structure (`frontend/`)

```
frontend/
├── assets/              # Static assets
│   └── css/            # Global CSS files
│       └── main.css    # Main Tailwind CSS file
├── components/          # Vue components
│   ├── Icon.vue        # Custom icon component
│   └── ui/             # Reusable UI components
├── layouts/            # Nuxt layouts
│   └── default.vue     # Default layout with sidebar
├── pages/              # Nuxt pages (auto-routing)
│   ├── index.vue       # Dashboard page
│   ├── notas-fiscais.vue # Invoice management page
│   ├── fornecedores.vue  # Suppliers page
│   ├── relatorios.vue    # Reports page
│   ├── upload.vue        # File upload page
│   ├── analytics.vue     # Analytics page
│   └── configuracoes.vue # Settings page
├── plugins/            # Nuxt plugins
├── stores/             # Pinia stores
│   ├── auth.ts         # Authentication store
│   ├── invoices.ts     # Invoice management store
│   └── app.ts          # General app state
├── utils/              # Utility functions
│   ├── api.ts          # API client functions
│   ├── formatters.ts   # Data formatting utilities
│   └── constants.ts    # Application constants
├── types/              # TypeScript type definitions
│   ├── invoice.ts      # Invoice-related types
│   ├── supplier.ts     # Supplier-related types
│   └── api.ts          # API response types
├── node_modules/       # Node.js dependencies
├── .nuxt/             # Nuxt build output
├── .output/           # Production build output
├── app.vue            # Root Vue component
├── nuxt.config.ts     # Nuxt configuration
├── package.json       # Node.js dependencies and scripts
├── package-lock.json  # Dependency lock file
├── tailwind.config.js # Tailwind CSS configuration
├── .env.example       # Environment template
├── INSTALACAO.md      # Installation guide (Portuguese)
└── README.md          # Frontend documentation
```

## Database Structure (`database/`)

```
database/
├── schema/              # SQL schema files
│   ├── 01_create_tables.sql    # Base table creation
│   ├── 02_nfe_tables.sql       # NF-e specific tables
│   ├── 03_nfse_tables.sql      # NFS-e specific tables
│   ├── 04_views.sql            # Analytical views
│   ├── 05_indexes.sql          # Performance indexes
│   └── 06_rls_policies.sql     # Row Level Security
├── setup.sql           # Complete database setup script
└── README.md          # Database documentation
```

## Configuration Structure (`.kiro/`)

```
.kiro/
├── specs/              # Project specifications
│   └── ai-agents-invoice-system/
│       ├── requirements.md  # Functional requirements
│       ├── design.md       # Technical design
│       └── tasks.md        # Implementation tasks
├── steering/           # AI assistant guidance
│   ├── product.md     # Product overview
│   ├── tech.md        # Technology stack
│   └── structure.md   # Project structure (this file)
└── settings/          # Kiro configuration
```

## File Naming Conventions

### Python Files
- **Snake case**: `xml_processing_agent.py`, `data_lake_agent.py`
- **Models**: End with `_models.py` or `_schemas.py`
- **Tests**: Prefix with `test_` or end with `_test.py`

### TypeScript/Vue Files
- **PascalCase** for components: `Dashboard.vue`, `ReportGenerator.vue`
- **camelCase** for utilities: `apiClient.ts`, `authUtils.ts`
- **kebab-case** for pages: `notas-fiscais.vue`, `fornecedores.vue`

### SQL Files
- **Numbered prefixes** for schema: `01_create_tables.sql`
- **Descriptive names**: `nfe_tables.sql`, `analytical_views.sql`

## Import Conventions

### Python Imports
```python
# Standard library first
import os
from datetime import datetime

# Third-party packages
from fastapi import FastAPI
from pydantic import BaseModel

# Local imports
from models.nfe_models import NFEData
from utils.config import settings
```

### TypeScript Imports
```typescript
// Vue and Nuxt
import { ref, computed } from 'vue'
import type { Ref } from 'vue'

// Third-party libraries
import { useSupabaseClient } from '@supabase/auth-helpers-vue'

// Local imports
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/utils/api'
```

## Environment Management

### Development
- Use `.env` files for configuration
- Never commit sensitive data
- Use `.env.example` templates

### Production
- Environment variables via deployment platform
- Separate configs for frontend/backend
- Secure secret management

## Documentation Standards

### Code Comments
- **Python**: Use docstrings for functions and classes
- **TypeScript**: Use JSDoc comments for complex functions
- **SQL**: Comment complex queries and business logic

### README Files
- Each major directory has its own README.md
- Include setup instructions and usage examples
- Document any special requirements or dependencies