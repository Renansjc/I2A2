# Technology Stack & Build System

## Backend Stack
- **Python 3.13.9** with FastAPI 0.115.0 for async API
- **CrewAI 0.203.1** for multi-agent coordination and workflow management
- **lxml 6.0.2** for Brazilian XML processing (NF-e/NFS-e)
- **asyncpg 0.30.0** for PostgreSQL/Supabase database integration
- **Redis 5.2.1 + Celery 5.3.6** for background task processing and agent communication
- **structlog 25.4.0** for structured logging
- **Pydantic 2.12.3** for data validation and settings management
- **LangChain 0.3.9** for AI agent framework integration

## Frontend Stack
- **Nuxt.js 4.2.0** with Vue 3.5.22 and TypeScript
- **Tailwind CSS 4.1.16** with @tailwindcss/vite plugin for styling
- **DaisyUI 5.3.9** for UI components
- **Vue Router 4.6.3** for navigation

## Infrastructure
- **PostgreSQL** via Supabase for data storage
- **Redis 7** for caching and agent communication
- **Docker** for containerization
- **Supabase** for authentication and storage

## Common Commands

### Backend Development
```bash
# Setup virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

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
- **Python 3.13.9** with virtual environment required for backend
- **Node.js 18+** required for frontend (tested with latest versions)
- **Docker** required for Redis development environment
- **PostgreSQL** or **Supabase** account for database
- **Windows** development environment supported

## Key Dependencies
- **FastAPI 0.115.0**: Modern async web framework
- **CrewAI 0.203.1**: Multi-agent orchestration
- **Nuxt 4.2.0**: Vue.js framework with SSR/SSG
- **Tailwind CSS 4.1.16**: Utility-first CSS framework with Vite plugin
- **Redis 5.2.1**: In-memory data structure store
- **LangChain 0.3.9**: AI agent framework
- **Uvicorn 0.32.0**: ASGI server for FastAPI
- **Supabase 2.9.1**: Backend-as-a-Service platform