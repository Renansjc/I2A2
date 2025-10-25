# Technology Stack & Build System

## Backend Stack

### Core Framework
- **Python 3.11+** with FastAPI for high-performance async API
- **CrewAI** for multi-agent coordination and workflow management
- **LangChain** for LLM integration and natural language processing

### Data Processing
- **lxml + xmlschema** for Brazilian XML processing (NF-e/NFS-e)
- **scikit-learn + spaCy** for machine learning and NLP
- **pandas + numpy** for data manipulation and analysis

### Database & Storage
- **PostgreSQL** via Supabase for structured data storage
- **asyncpg** for async PostgreSQL connections
- **Supabase Storage** for XML file management

### Task Processing
- **Redis + Celery** for background task processing and agent communication
- **Watchdog** for file system monitoring

### Report Generation
- **openpyxl** for Excel reports
- **python-docx** for Word documents
- **reportlab** for PDF generation
- **Jinja2** for report templates

## Frontend Stack

### Core Framework
- **Nuxt.js 3+** with TypeScript for modern web application
- **Vue 3** with Composition API and server-side rendering

### UI & Styling
- **DaisyUI + Tailwind CSS** for professional executive interface
- **Heroicons** for consistent iconography
- **Chart.js + Vue-ChartJS** for data visualization and executive dashboards

### Authentication & Data
- **Supabase Auth** for authentication and authorization
- **Vue file upload components** for XML file uploads
- **Pinia** for state management
- **VueUse** for composition utilities

## Infrastructure

### Database
- **PostgreSQL** via Supabase with Row Level Security (RLS)
- **Redis** for caching and agent communication

### Deployment
- **Vercel** for frontend deployment
- **Railway/Render** for backend deployment
- **Docker** for containerized services

## Common Commands

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Start backend
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
# Start development server
npm run dev
# Build for production
npm run build
# Generate static site
npm run generate
# Preview production build
npm run preview
```

### Database Setup
```bash
cd database
# Copy setup.sql contents to Supabase SQL Editor
# Or for local PostgreSQL:
psql -d your_db -f setup.sql
```

### Docker Services
```bash
# Start Redis and supporting services
docker-compose up -d
# View logs
docker-compose logs -f
```

### Testing
```bash
# Backend tests
cd backend
pytest
# Frontend tests
cd frontend
npm test
# Linting
npm run lint
```

## Development Environment

### Required Tools
- Python 3.11+
- Node.js 18+
- PostgreSQL or Supabase account
- Redis (via Docker or local install)

### Environment Files
- `backend/.env` - Database URLs, API keys, Redis config
- `frontend/.env.local` - Supabase config, API endpoints

### Code Quality
- **Backend**: flake8, black for Python formatting
- **Frontend**: ESLint, Prettier for TypeScript/React
- **Structured logging**: structlog for consistent log format

## Architecture Patterns

### Multi-Agent System
- CrewAI agents communicate via Redis message queues
- Each agent has specific responsibilities (XML processing, categorization, SQL generation, etc.)
- Master Agent orchestrates workflows and user interactions

### Database Design
- Separate tables for NF-e (products) and NFS-e (services)
- Dimension tables for suppliers, products, services
- Fact tables for detailed transaction data
- Analytical views for executive queries

### API Design
- FastAPI with async/await for high performance
- RESTful endpoints with OpenAPI documentation
- WebSocket support for real-time updates