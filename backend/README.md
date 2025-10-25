# AI Agents Invoice Analysis System - Backend

FastAPI-based backend with multi-agent architecture for processing Brazilian electronic invoices (NF-e and NFS-e).

## Architecture

### Multi-Agent System
The backend implements a coordinated multi-agent architecture using CrewAI:

- **Master Agent**: Central orchestrator for user interactions and workflow coordination
- **XML Processing Agent**: Automatic NF-e/NFS-e XML file processing and validation
- **AI Categorization Agent**: Machine learning-powered categorization and pattern detection
- **SQL Agent**: Natural language to SQL query translation
- **Report Agent**: Multi-format report generation (.xlsx, .pdf, .docx)
- **Scheduler Agent**: Automated task scheduling and recurring report delivery
- **Data Lake Agent**: Data storage, integrity, and optimized access management
- **Monitoring Agent**: Error logging, notifications, and system health monitoring

## Directory Structure

```
backend/
├── agents/                 # AI agent implementations
│   ├── __init__.py
│   └── base_agent.py      # Base agent class
├── models/                # Data models
│   ├── __init__.py
│   └── fiscal_data.py     # NF-e and NFS-e data models
├── utils/                 # Utilities
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database connections
│   └── logging.py         # Structured logging
├── api/                   # FastAPI routes
│   ├── __init__.py
│   └── routes.py          # API endpoints
├── main.py                # FastAPI application
├── requirements.txt       # Python dependencies
└── .env.example          # Environment configuration template
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL or Supabase
- Redis (for agent communication)

### Setup
1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Install spaCy Portuguese model:
   ```bash
   python -m spacy download pt_core_news_sm
   ```

## Configuration

### Environment Variables (.env)

```env
# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_agents_invoice_system
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis
REDIS_URL=redis://localhost:6379

# XML Processing
XML_WATCH_DIRECTORY=./xml_files
XML_PROCESSED_DIRECTORY=./xml_processed
XML_ERROR_DIRECTORY=./xml_errors

# Agent Configuration
AGENT_TIMEOUT=300
MAX_CONCURRENT_AGENTS=10

# Machine Learning
ML_MODEL_PATH=./models
SPACY_MODEL=pt_core_news_sm
```

## Running the Application

### Development
```bash
python main.py
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Docker
```bash
docker build -t ai-agents-backend .
docker run -p 8000:8000 ai-agents-backend
```

## API Endpoints

### Health and Status
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/status` - System status and agent health

### XML Processing
- `POST /api/v1/xml/upload` - Upload XML file
- `GET /api/v1/xml/status/{file_id}` - Get processing status

### Queries
- `POST /api/v1/query/natural-language` - Process natural language query
- `POST /api/v1/query/execute` - Execute SQL query

### Reports
- `POST /api/v1/reports/generate` - Generate report
- `GET /api/v1/reports/{report_id}` - Get generated report

### Scheduler
- `POST /api/v1/scheduler/create` - Create scheduled task
- `GET /api/v1/scheduler/tasks` - List scheduled tasks

### Analytics
- `GET /api/v1/analytics/suppliers` - Supplier analytics
- `GET /api/v1/analytics/products` - Product analytics
- `GET /api/v1/analytics/taxes` - Tax analytics

## Agent Development

### Creating New Agents

1. Inherit from `BaseAgent`:
```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent")
    
    async def initialize(self):
        # Initialize agent resources
        pass
    
    async def cleanup(self):
        # Cleanup resources
        pass
    
    async def process(self, data):
        # Main agent logic
        return processed_data
```

2. Register agent in the system
3. Configure agent communication via CrewAI

### Agent Communication
Agents communicate through:
- **Redis**: Message passing and task queues
- **CrewAI**: Workflow coordination and task delegation
- **WebSockets**: Real-time status updates to frontend

## Data Models

### Core Models
- `NFEData`: NF-e (Nota Fiscal Eletrônica) document structure
- `NFSEData`: NFS-e (Nota Fiscal de Serviços Eletrônica) document structure
- `Supplier`: Supplier/emitter information
- `Product`: Product catalog for NF-e
- `Service`: Service catalog for NFS-e
- `Tax`: Tax information (ICMS, IPI, PIS, COFINS, ISSQN)

### Processing Models
- `ProcessingError`: Error tracking and logging
- `CategorizedFiscalData`: AI-categorized data with confidence scores

## Database Integration

### Connection Management
- **asyncpg**: Direct PostgreSQL connection pool for high performance
- **Supabase**: Client for authentication and storage operations
- **Connection pooling**: Optimized for concurrent agent operations

### Query Execution
```python
from utils.database import DatabaseManager

# Execute query
results = await DatabaseManager.execute_query(
    "SELECT * FROM nfe_main WHERE data_emissao >= $1", 
    date_param
)

# Execute transaction
commands = [
    ("INSERT INTO table1 VALUES ($1, $2)", (val1, val2)),
    ("UPDATE table2 SET col1 = $1 WHERE id = $2", (new_val, id))
]
await DatabaseManager.execute_transaction(commands)
```

## Logging and Monitoring

### Structured Logging
```python
from utils.logging import get_agent_logger

logger = get_agent_logger("my_agent")
logger.info("Processing started", file_path="example.xml", user_id=123)
logger.error("Processing failed", error="Invalid XML format")
```

### Agent Monitoring
- Health checks for all agents
- Performance metrics collection
- Error tracking and alerting
- Task queue monitoring

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Agent Tests
```bash
pytest tests/agents/
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=false`
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Configure Sentry for error tracking
- [ ] Set up SSL certificates
- [ ] Configure CORS origins
- [ ] Set up monitoring and alerting

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance Optimization

### Database
- Connection pooling with asyncpg
- Optimized queries with proper indexing
- Query result caching with Redis

### Agent Processing
- Concurrent agent execution
- Task queue management with Celery
- Background processing for large files

### API Performance
- Async/await throughout the application
- Response caching for analytics endpoints
- Request rate limiting

## Security

### Authentication
- Supabase Auth integration
- JWT token validation
- Role-based access control

### Data Protection
- Row Level Security (RLS) policies
- Data encryption at rest
- Secure agent communication
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL configuration
   - Verify PostgreSQL/Supabase connectivity
   - Check connection pool settings

2. **Agent Communication Issues**
   - Verify Redis connectivity
   - Check agent registration
   - Review CrewAI configuration

3. **XML Processing Errors**
   - Validate XML schema compliance
   - Check file permissions
   - Review error logs in monitoring agent

4. **Performance Issues**
   - Monitor database query performance
   - Check Redis memory usage
   - Review agent task queues

### Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed logging
python main.py

# Check agent status
curl http://localhost:8000/api/v1/status
```