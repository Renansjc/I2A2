# Product Overview

## AI Agents Invoice Analysis System

A multi-agent system for processing Brazilian electronic invoices (NF-e and NFS-e) that provides strategic fiscal insights for C-level executives through natural language queries and automated report generation.

### Core Purpose
- Automatic processing of Brazilian XML fiscal documents (NF-e/NFS-e)
- AI-powered categorization of products, suppliers, and operations
- Natural language query interface for executives
- Multi-format report generation (.xlsx, .pdf, .docx)
- Automated scheduling and recurring analytics

### Target Users
- C-level executives requiring fiscal insights
- Finance teams managing Brazilian tax compliance
- Operations teams analyzing supplier and product trends

### Key Features
- **Multi-agent architecture** with 8 specialized AI agents
- **Real-time dashboard** with fiscal insights using Nuxt 4 + Tailwind CSS
- **Automated XML file processing** and validation for NF-e/NFS-e documents
- **Machine learning-powered categorization** using CrewAI and LangChain
- **Executive report templates** and scheduling (.xlsx, .pdf, .docx formats)
- **Natural language query processing** in Portuguese and English
- **FastAPI backend** with async processing and structured logging
- **Supabase integration** for authentication and data storage
- **Redis-based task queue** for background processing
##
# Technical Architecture
- **Frontend**: Nuxt 4.2.0 with Vue 3.5.22, TypeScript, and Tailwind CSS 4.1.16
- **Backend**: Python 3.13.9 with FastAPI 0.115.0 and CrewAI 0.203.1
- **Database**: PostgreSQL via Supabase with structured schema for fiscal data
- **AI Framework**: LangChain 0.3.9 for agent coordination and natural language processing
- **Task Processing**: Redis 5.2.1 + Celery 5.3.6 for background jobs
- **Development**: Docker containerization with development and production configurations

### Multi-Agent System
The system implements 8 specialized agents working in coordination:
1. **Master Agent**: Central orchestrator managing workflow
2. **XML Processing Agent**: NF-e/NFS-e document parsing and validation
3. **AI Categorization Agent**: ML-powered product and supplier classification
4. **SQL Agent**: Natural language to SQL query translation
5. **Report Agent**: Multi-format report generation and templates
6. **Scheduler Agent**: Automated task management and recurring jobs
7. **Data Lake Agent**: Data storage optimization and management
8. **Monitoring Agent**: System health monitoring and error logging

### Current Implementation Status
- ✅ Project structure and development environment setup
- ✅ FastAPI backend with structured logging and configuration
- ✅ Nuxt 4 frontend with Tailwind CSS and DaisyUI
- ✅ Database schema design for Brazilian fiscal documents
- ✅ Multi-agent architecture foundation with CrewAI
- 🔄 Agent implementations and XML processing logic
- 🔄 Frontend dashboard and user interface
- 🔄 Integration testing and deployment configuration