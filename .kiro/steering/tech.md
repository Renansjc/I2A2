# Technology Stack & Build System

## Backend Stack
- **Python 3.11+** with FastAPI for async API
- **CrewAI** for multi-agent coordination and workflow management
- **lxml + xmlschema** for Brazilian XML processing (NF-e/NFS-e)
- **asyncpg** for PostgreSQL/Supabase database integration
- **Redis + Celery** for background task processing and agent communication
- **structlog** for structured logging
- **Pydantic** for data validation and settings management

## Frontend Stack
- **Nuxt.js 4+** with Vue 3 and TypeScript
- **Tailwind CSS 4.x** for styling
- **DaisyUI** for UI components
- **Vue Router** for navigation

## Infrastructure
- **PostgreSQL** via Supabase for data storage
- **Redis 7** for caching and agent communication
- **Docker** for containerization
- **Supabase** for authentication and storage

## Common Commands

### Backend Development
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Run tests
pytest
```

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Infrastructure
```bash
# Start Redis with Docker
docker-compose -f docker-compose.dev.yml up -d

# Stop Redis
docker-compose -f docker-compose.dev.yml down

# Use Makefile shortcuts
make redis-start
make redis-stop
make install
```

## Development Environment
- Python virtual environment required for backend
- Node.js 18+ required for frontend
- Docker required for Redis
- PostgreSQL or Supabase account for database

## Key Dependencies
- **FastAPI**: Modern async web framework
- **CrewAI**: Multi-agent orchestration
- **Nuxt 4**: Vue.js framework with SSR/SSG
- **Tailwind CSS**: Utility-first CSS framework
- **Redis**: In-memory data structure store