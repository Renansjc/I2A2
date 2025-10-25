# AI Agents Invoice Analysis System

A multi-agent system for processing Brazilian electronic invoices (NF-e and NFS-e) that provides strategic fiscal insights for C-level executives through natural language queries and automated report generation.

## Project Structure

```
ai-agents-invoice-system/
├── backend/                 # Python FastAPI backend with multi-agent system
│   ├── agents/             # AI agents (XML Processing, Categorization, SQL, etc.)
│   ├── models/             # Data models for NF-e and NFS-e
│   ├── utils/              # Utilities (config, database, logging)
│   ├── api/                # FastAPI routes and endpoints
│   ├── main.py             # FastAPI application entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js TypeScript frontend
│   ├── src/
│   │   ├── app/           # Next.js 14 app directory
│   │   ├── components/    # React components (Shadcn/ui)
│   │   ├── lib/           # Utility functions
│   │   └── hooks/         # Custom React hooks
│   ├── package.json       # Node.js dependencies
│   └── tailwind.config.js # Tailwind CSS configuration
└── database/              # PostgreSQL/Supabase schema
    ├── schema/            # SQL schema files
    ├── setup.sql          # Complete database setup
    └── README.md          # Database documentation
```

## Features

### Multi-Agent Architecture

- **XML Processing Agent**: Automatically processes NF-e and NFS-e XML files
- **AI Categorization Agent**: Machine learning-powered categorization of products, suppliers, and operations
- **Master Agent**: Natural language query interpretation and workflow coordination
- **SQL Agent**: Converts business questions to SQL queries
- **Report Agent**: Generates executive reports in multiple formats (.xlsx, .pdf, .docx)
- **Scheduler Agent**: Manages automated recurring tasks and report delivery
- **Data Lake Agent**: Centralized data storage with integrity and optimization
- **Monitoring Agent**: Error logging, notifications, and system health monitoring

### Executive Features

- Natural language querying of fiscal data
- Automated XML file processing and categorization
- Multi-format report generation with executive templates
- Scheduled recurring reports and analytics
- Real-time dashboard with fiscal insights
- Supplier and product trend analysis

## Technology Stack

### Backend

- **Python 3.11+** with FastAPI for high-performance async API
- **CrewAI** for multi-agent coordination and workflow management
- **lxml + xmlschema** for Brazilian XML processing (NF-e/NFS-e)
- **scikit-learn + spaCy** for machine learning and NLP
- **asyncpg** for PostgreSQL/Supabase database integration
- **Redis + Celery** for background task processing

### Frontend

- **Next.js 14+** with TypeScript for modern web application
- **Shadcn/ui + Tailwind CSS** for professional executive interface
- **Recharts** for data visualization and executive dashboards
- **Supabase Auth** for authentication and authorization
- **React Dropzone** for XML file uploads

### Infrastructure

- **PostgreSQL** via Supabase for data storage
- **Supabase Storage** for XML file management
- **Redis** for agent communication and caching
- **Vercel** (frontend) + Railway/Render (backend) for deployment

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL or Supabase account
- Redis (for agent communication)

### Database Setup

1. Create a Supabase project or PostgreSQL database
2. Run the database setup:
   ```bash
   cd database
   # For Supabase: Copy contents of setup.sql to SQL Editor
   # For PostgreSQL: psql -d your_db -f setup.sql
   ```

### Backend Setup

1. Navigate to backend directory:

   ```bash
   cd backend
   ```

2. Create virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:

   ```bash
   cp .env.example .env
   # Edit .env with your database and API keys
   ```

5. Start the backend:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Navigate to frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Configure environment:

   ```bash
   cp .env.example .env.local
   # Edit .env.local with your Supabase and API configuration
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Configuration

### Environment Variables

#### Backend (.env)

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
REDIS_URL=redis://localhost:6379
XML_WATCH_DIRECTORY=./xml_files
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Usage

### Processing XML Files

1. Upload NF-e or NFS-e XML files through the web interface
2. Files are automatically processed by the XML Processing Agent
3. Data is categorized by the AI Categorization Agent
4. Structured data is stored in the Data Lake

### Natural Language Queries

1. Use the query interface to ask questions in Portuguese or English
2. Examples:
   - "Quais fornecedores aumentaram mais os preços este trimestre?"
   - "Which suppliers increased prices the most this quarter?"
   - "Mostre o resumo de impostos por categoria de produto"

### Report Generation

1. Execute queries through the natural language interface
2. Choose report format (.xlsx, .pdf, .docx)
3. Schedule recurring reports for automated delivery

## Requirements Addressed

This implementation addresses all requirements from the specification:

- **Requirement 1**: Automatic XML processing with error handling and notifications
- **Requirement 2**: AI-powered categorization of products, suppliers, and operations
- **Requirement 3**: Natural language query processing with SQL generation
- **Requirement 4**: Multi-format executive report generation
- **Requirement 5**: Automated scheduling and recurring task management
- **Requirement 6**: Centralized data lake with integrity and optimization

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8 .
black .

# Frontend linting
cd frontend
npm run lint
```

## Deployment

### Production Deployment

1. **Database**: Deploy PostgreSQL or use Supabase
2. **Backend**: Deploy to Railway, Render, or similar Python hosting
3. **Frontend**: Deploy to Vercel or Netlify
4. **Redis**: Use Redis Cloud or similar managed service

### Environment Configuration

- Set production environment variables
- Configure CORS origins for production domains
- Set up SSL certificates
- Configure monitoring and logging

## Support

For technical support or questions about the AI Agents Invoice Analysis System, please refer to the documentation in each component directory or contact the development team.

## License

This project is proprietary software developed for Brazilian fiscal document analysis.
