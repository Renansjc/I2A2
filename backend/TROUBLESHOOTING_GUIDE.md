# Troubleshooting Guide - AI Agents Invoice Analysis System

## Overview

This guide provides solutions for common issues encountered when using the AI Agents Invoice Analysis System, including API errors, database problems, agent processing failures, and integration challenges.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [File Upload Problems](#file-upload-problems)
3. [Agent Processing Failures](#agent-processing-failures)
4. [Database Connection Issues](#database-connection-issues)
5. [Performance Problems](#performance-problems)
6. [API Error Codes](#api-error-codes)
7. [Natural Language Query Issues](#natural-language-query-issues)
8. [Report Generation Problems](#report-generation-problems)
9. [Supabase Integration Issues](#supabase-integration-issues)
10. [Development Environment Setup](#development-environment-setup)

## Authentication Issues

### Problem: 401 Unauthorized Error

**Symptoms:**
```json
{
  "codigo_erro": "ERRO_AUTENTICACAO",
  "mensagem": "Token de autenticação inválido ou expirado",
  "detalhes": "JWT token validation failed"
}
```

**Solutions:**

1. **Check Token Validity**
```python
import jwt
from datetime import datetime

def check_token_validity(token):
    try:
        # Decode without verification to check expiration
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded.get('exp')
        
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            if exp_date < datetime.now():
                print(f"Token expired at: {exp_date}")
                return False
        
        print("Token is valid")
        return True
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return False

# Usage
is_valid = check_token_validity(your_token)
```

2. **Refresh Token**
```javascript
// JavaScript/TypeScript
async function refreshAuthToken() {
  const { data, error } = await supabase.auth.refreshSession()
  
  if (error) {
    console.error('Token refresh failed:', error)
    // Redirect to login
    window.location.href = '/login'
    return null
  }
  
  return data.session?.access_token
}
```

3. **Verify Token Format**
```python
def verify_token_format(token):
    # JWT tokens have 3 parts separated by dots
    parts = token.split('.')
    if len(parts) != 3:
        print("Invalid JWT format - should have 3 parts")
        return False
    
    # Check if it starts with Bearer
    if token.startswith('Bearer '):
        print("Remove 'Bearer ' prefix from token")
        return False
    
    return True
```

### Problem: 403 Forbidden Error

**Symptoms:**
```json
{
  "codigo_erro": "ERRO_AUTORIZACAO",
  "mensagem": "Acesso negado - permissões insuficientes"
}
```

**Solutions:**

1. **Check User Permissions**
```sql
-- Check user role in Supabase
SELECT auth.uid(), auth.role();

-- Check RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE schemaname = 'public';
```

2. **Verify Service Role Usage**
```python
# For admin operations, use service role key
import os
from supabase import create_client

# User operations (with RLS)
supabase_user = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Admin operations (bypass RLS)
supabase_admin = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)
```

## File Upload Problems

### Problem: File Upload Fails with Large Files

**Symptoms:**
- Upload timeout errors
- "Request Entity Too Large" (413) errors
- Connection reset errors

**Solutions:**

1. **Check File Size Limits**
```python
def validate_file_size(file_path, max_size_mb=10):
    file_size = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise ValueError(f"File size {file_size} bytes exceeds limit of {max_size_bytes} bytes")
    
    return file_size

# Usage
try:
    file_size = validate_file_size('large_nfe.xml', max_size_mb=10)
    print(f"File size OK: {file_size} bytes")
except ValueError as e:
    print(f"File too large: {e}")
```

2. **Implement Chunked Upload**
```python
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

def upload_with_progress(file_path, token, chunk_size=8192):
    def progress_callback(monitor):
        progress = (monitor.bytes_read / monitor.len) * 100
        print(f"Upload progress: {progress:.1f}%")
    
    with open(file_path, 'rb') as file:
        encoder = MultipartEncoder(
            fields={'arquivo': (os.path.basename(file_path), file, 'application/xml')}
        )
        
        monitor = MultipartEncoderMonitor(encoder, progress_callback)
        
        response = requests.post(
            'http://localhost:8000/agentes/upload-xml',
            data=monitor,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': monitor.content_type
            },
            timeout=300  # 5 minutes timeout
        )
        
        return response.json()
```

3. **Configure Server Limits**
```python
# FastAPI configuration for large files
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Increase file size limit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# Configure Uvicorn for large files
# uvicorn main:app --host 0.0.0.0 --port 8000 --limit-max-requests 1000 --timeout-keep-alive 30
```

### Problem: Invalid XML Format Error

**Symptoms:**
```json
{
  "codigo_erro": "FORMATO_ARQUIVO_INVALIDO",
  "mensagem": "Arquivo XML inválido ou corrompido"
}
```

**Solutions:**

1. **Validate XML Structure**
```python
from lxml import etree
import xml.etree.ElementTree as ET

def validate_xml_file(file_path):
    try:
        # Try parsing with lxml (more strict)
        with open(file_path, 'rb') as file:
            etree.parse(file)
        
        print("XML is valid")
        return True
        
    except etree.XMLSyntaxError as e:
        print(f"XML syntax error: {e}")
        return False
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

def detect_xml_encoding(file_path):
    with open(file_path, 'rb') as file:
        first_line = file.readline()
        
    # Look for encoding declaration
    if b'encoding=' in first_line:
        encoding_start = first_line.find(b'encoding=') + 10
        encoding_end = first_line.find(b'"', encoding_start)
        if encoding_end == -1:
            encoding_end = first_line.find(b"'", encoding_start)
        
        if encoding_end != -1:
            encoding = first_line[encoding_start:encoding_end].decode('ascii')
            print(f"Detected encoding: {encoding}")
            return encoding
    
    return 'utf-8'  # Default
```

2. **Fix Common XML Issues**
```python
def fix_common_xml_issues(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    
    # Fix common issues
    fixes = [
        # Remove BOM if present
        ('\ufeff', ''),
        # Fix common encoding issues
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        # Fix malformed tags
        ('</', '</'),
        ('< /', '</'),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    # Validate fixed content
    try:
        ET.fromstring(content)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Fixed XML saved to: {output_path}")
        return True
    except ET.ParseError as e:
        print(f"Could not fix XML: {e}")
        return False
```

## Agent Processing Failures

### Problem: XML Processing Agent Timeout

**Symptoms:**
- Agent status stuck in "in_progress"
- Processing timeout errors
- No results after extended time

**Solutions:**

1. **Check Agent Status**
```python
def diagnose_agent_processing(document_id, token):
    response = requests.get(
        f'http://localhost:8000/api/documents/{document_id}/status',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    status_data = response.json()
    
    for agent_status in status_data['agent_statuses']:
        agent_name = agent_status['agent_name']
        status = agent_status['status']
        started_at = agent_status.get('started_at')
        error_message = agent_status.get('error_message')
        
        print(f"Agent: {agent_name}")
        print(f"Status: {status}")
        
        if started_at:
            from datetime import datetime
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed = datetime.now(start_time.tzinfo) - start_time
            print(f"Running for: {elapsed}")
        
        if error_message:
            print(f"Error: {error_message}")
        
        print("---")
```

2. **Restart Failed Agents**
```python
def restart_failed_processing(document_id, token):
    # Get current status
    status_response = requests.get(
        f'http://localhost:8000/api/documents/{document_id}/status',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    status_data = status_response.json()
    
    # Check for failed or stuck agents
    failed_agents = [
        agent for agent in status_data['agent_statuses']
        if agent['status'] in ['failed', 'error'] or 
        (agent['status'] == 'in_progress' and agent.get('started_at'))
    ]
    
    if failed_agents:
        print(f"Found {len(failed_agents)} failed/stuck agents")
        
        # Trigger reprocessing (implementation depends on your system)
        reprocess_response = requests.post(
            f'http://localhost:8000/api/documents/{document_id}/reprocess',
            headers={'Authorization': f'Bearer {token}'},
            json={'agents': [agent['agent_name'] for agent in failed_agents]}
        )
        
        if reprocess_response.status_code == 200:
            print("Reprocessing triggered successfully")
        else:
            print(f"Reprocessing failed: {reprocess_response.json()}")
```

### Problem: AI Categorization Agent Low Confidence

**Symptoms:**
- Low confidence scores in categorization results
- Incorrect product/service categories
- Missing category assignments

**Solutions:**

1. **Analyze Categorization Results**
```python
def analyze_categorization_quality(document_id, token):
    response = requests.get(
        f'http://localhost:8000/api/documents/{document_id}/status',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    status_data = response.json()
    
    # Find categorization results
    categorization_results = [
        result for result in status_data['processing_results']
        if result['agent_name'] == 'ai_categorization_agent'
    ]
    
    for result in categorization_results:
        confidence = result.get('confidence_score', 0)
        result_data = result['result_data']
        
        print(f"Categorization confidence: {confidence:.2f}")
        
        if confidence < 0.7:
            print("Low confidence detected. Possible issues:")
            print("- Unclear product descriptions")
            print("- Missing NCM codes")
            print("- Unusual product names")
            
        # Analyze specific categories
        categories = result_data.get('categories', [])
        for category in categories:
            print(f"Category: {category.get('name')} (confidence: {category.get('confidence', 0):.2f})")
```

2. **Improve Input Data Quality**
```python
def improve_xml_for_categorization(xml_content):
    """Enhance XML content for better categorization"""
    from lxml import etree
    
    root = etree.fromstring(xml_content.encode('utf-8'))
    
    # Find product items
    items = root.xpath('.//det')  # NFe items
    
    improvements = []
    
    for item in items:
        prod = item.find('.//prod')
        if prod is not None:
            # Check for missing or poor descriptions
            desc = prod.find('xProd')
            if desc is not None and len(desc.text) < 10:
                improvements.append(f"Short description: '{desc.text}'")
            
            # Check for missing NCM
            ncm = prod.find('NCM')
            if ncm is None:
                improvements.append("Missing NCM code")
            
            # Check for generic descriptions
            generic_terms = ['produto', 'item', 'mercadoria', 'diversos']
            if desc is not None and any(term in desc.text.lower() for term in generic_terms):
                improvements.append(f"Generic description: '{desc.text}'")
    
    return improvements
```

## Database Connection Issues

### Problem: Connection Pool Exhaustion

**Symptoms:**
- "Connection pool exhausted" errors
- Slow database queries
- Timeout errors

**Solutions:**

1. **Monitor Connection Usage**
```sql
-- Check active connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE state = 'active';

-- Check connection limits
SELECT 
    setting as max_connections,
    (SELECT count(*) FROM pg_stat_activity) as current_connections,
    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
FROM pg_settings 
WHERE name = 'max_connections';
```

2. **Optimize Connection Pool**
```python
import asyncpg
import asyncio
from contextlib import asynccontextmanager

class DatabaseManager:
    def __init__(self, database_url: str, min_size: int = 5, max_size: int = 20):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def initialize_pool(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=60,
            server_settings={
                'application_name': 'ai_agents_system',
                'jit': 'off'  # Disable JIT for better connection reuse
            }
        )
    
    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            await self.initialize_pool()
        
        async with self.pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                # Log connection issues
                print(f"Database connection error: {e}")
                raise
    
    async def execute_query(self, query: str, *args):
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def close_pool(self):
        if self.pool:
            await self.pool.close()

# Usage
db_manager = DatabaseManager(
    "postgresql://user:pass@localhost:5432/dbname",
    min_size=5,
    max_size=20
)

# Execute queries
results = await db_manager.execute_query(
    "SELECT * FROM fiscal_documents WHERE user_id = $1",
    user_id
)
```

### Problem: Slow Query Performance

**Symptoms:**
- Long response times for API calls
- Database timeout errors
- High CPU usage on database server

**Solutions:**

1. **Identify Slow Queries**
```sql
-- Enable query statistics (if not already enabled)
-- Add to postgresql.conf: shared_preload_libraries = 'pg_stat_statements'

-- Find slowest queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Find queries with high I/O
SELECT 
    query,
    calls,
    shared_blks_hit,
    shared_blks_read,
    shared_blks_dirtied,
    shared_blks_written
FROM pg_stat_statements 
ORDER BY (shared_blks_read + shared_blks_written) DESC 
LIMIT 10;
```

2. **Optimize Queries**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_fiscal_documents_user_status 
ON fiscal_documents(user_id, processing_status);

CREATE INDEX CONCURRENTLY idx_nfe_main_emitente_data 
ON nfe_main USING btree (SUBSTRING(chave_nfe, 7, 14), data_emissao);

-- Analyze query plans
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM fiscal_documents 
WHERE user_id = 'uuid' AND processing_status = 'completed';

-- Update table statistics
ANALYZE fiscal_documents;
ANALYZE nfe_main;
ANALYZE fact_itens_nfe;
```

3. **Implement Query Optimization**
```python
async def optimized_document_query(user_id: str, status: str = None, limit: int = 50):
    """Optimized document listing with proper indexing"""
    
    base_query = """
    SELECT 
        fd.id,
        fd.filename,
        fd.document_type,
        fd.processing_status,
        fd.upload_timestamp,
        fd.file_size,
        dm.nome_emitente,
        dm.valor_total,
        dm.data_emissao
    FROM fiscal_documents fd
    LEFT JOIN document_metadata dm ON fd.id = dm.document_id
    WHERE fd.user_id = $1
    """
    
    params = [user_id]
    
    if status:
        base_query += " AND fd.processing_status = $2"
        params.append(status)
    
    base_query += " ORDER BY fd.upload_timestamp DESC LIMIT $" + str(len(params) + 1)
    params.append(limit)
    
    async with db_manager.get_connection() as conn:
        return await conn.fetch(base_query, *params)
```

## Performance Problems

### Problem: High Memory Usage

**Symptoms:**
- Out of memory errors
- Slow processing of large XML files
- System becomes unresponsive

**Solutions:**

1. **Monitor Memory Usage**
```python
import psutil
import gc
from memory_profiler import profile

@profile
def process_large_xml(xml_content):
    """Memory-efficient XML processing"""
    
    # Process in chunks instead of loading entire content
    from lxml import etree
    
    # Use iterparse for large files
    def parse_xml_iteratively(xml_content):
        context = etree.iterparse(
            io.StringIO(xml_content),
            events=('start', 'end')
        )
        
        for event, elem in context:
            if event == 'end':
                # Process element
                yield elem
                
                # Clear element to free memory
                elem.clear()
                
                # Also eliminate now-empty references from the root node to elem
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
    
    # Process elements one by one
    for element in parse_xml_iteratively(xml_content):
        # Process individual element
        process_element(element)
        
        # Force garbage collection periodically
        if random.randint(1, 100) == 1:
            gc.collect()

def monitor_memory_usage():
    """Monitor system memory usage"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS Memory: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS Memory: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # System memory
    system_memory = psutil.virtual_memory()
    print(f"System Memory Usage: {system_memory.percent}%")
    
    return memory_info.rss
```

2. **Implement Memory Limits**
```python
import resource

def set_memory_limit(max_memory_mb):
    """Set memory limit for the process"""
    max_memory_bytes = max_memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

def process_with_memory_monitoring(xml_content, max_memory_mb=512):
    """Process XML with memory monitoring"""
    
    set_memory_limit(max_memory_mb)
    
    initial_memory = monitor_memory_usage()
    
    try:
        result = process_large_xml(xml_content)
        
        final_memory = monitor_memory_usage()
        memory_used = (final_memory - initial_memory) / 1024 / 1024
        
        print(f"Memory used during processing: {memory_used:.2f} MB")
        
        return result
        
    except MemoryError:
        print("Memory limit exceeded during processing")
        gc.collect()  # Force cleanup
        raise
```

### Problem: Slow API Response Times

**Symptoms:**
- API calls taking more than 30 seconds
- Timeout errors from clients
- Poor user experience

**Solutions:**

1. **Implement Response Caching**
```python
from functools import lru_cache
import hashlib
import json

class ResponseCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint and parameters"""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_cached_response(self, endpoint: str, params: dict):
        """Get cached response if available"""
        cache_key = self.cache_key(endpoint, params)
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def cache_response(self, endpoint: str, params: dict, response_data: dict, ttl: int = None):
        """Cache response data"""
        cache_key = self.cache_key(endpoint, params)
        ttl = ttl or self.default_ttl
        
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(response_data, default=str)
        )

# FastAPI middleware for caching
from fastapi import Request, Response
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    
    # Check cache for GET requests
    if request.method == "GET":
        cache_key = f"{request.url.path}:{str(request.query_params)}"
        cached_response = await response_cache.get_cached_response(
            request.url.path,
            dict(request.query_params)
        )
        
        if cached_response:
            return JSONResponse(cached_response)
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    
    # Cache successful GET responses
    if request.method == "GET" and response.status_code == 200:
        # Note: This is simplified - in practice, you'd need to extract response body
        pass
    
    return response
```

2. **Optimize Database Queries**
```python
async def optimized_supplier_analysis(user_id: str, months_back: int = 6):
    """Optimized supplier analysis with materialized view"""
    
    # Use materialized view for better performance
    query = """
    SELECT 
        e.cnpj,
        e.razao_social,
        e.uf,
        COALESCE(stats.total_notas, 0) as total_notas,
        COALESCE(stats.valor_total, 0) as valor_total,
        COALESCE(stats.valor_medio, 0) as valor_medio
    FROM dim_emitente e
    LEFT JOIN (
        SELECT 
            SUBSTRING(n.chave_nfe, 7, 14) as cnpj_emitente,
            COUNT(*) as total_notas,
            SUM(n.valor_total_nf) as valor_total,
            AVG(n.valor_total_nf) as valor_medio
        FROM nfe_main n
        WHERE n.data_emissao >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY SUBSTRING(n.chave_nfe, 7, 14)
    ) stats ON e.cnpj = stats.cnpj_emitente
    WHERE stats.total_notas > 0
    ORDER BY stats.valor_total DESC
    LIMIT 50
    """
    
    async with db_manager.get_connection() as conn:
        return await conn.fetch(query, months_back)
```

## API Error Codes

### Complete Error Code Reference

| Error Code | HTTP Status | Description | Solution |
|------------|-------------|-------------|----------|
| `ERRO_AUTENTICACAO` | 401 | Authentication failed | Check token validity and format |
| `ERRO_AUTORIZACAO` | 403 | Insufficient permissions | Verify user role and RLS policies |
| `FORMATO_ARQUIVO_INVALIDO` | 400 | Invalid file format | Ensure file is valid XML |
| `ARQUIVO_MUITO_GRANDE` | 400 | File size exceeds limit | Reduce file size or increase limits |
| `ARQUIVO_INSEGURO` | 400 | Security validation failed | Check file content for malicious code |
| `ERRO_VALIDACAO` | 400 | Request validation failed | Check request parameters |
| `ERRO_PROCESSAMENTO_XML` | 500 | XML processing failed | Check XML structure and content |
| `ERRO_RELATORIO_EXECUTIVO` | 500 | Report generation failed | Check report parameters |
| `ERRO_CONSULTA_NATURAL` | 500 | Natural query failed | Simplify query or check parameters |
| `ERRO_BANCO_DADOS` | 500 | Database error | Check database connectivity |
| `ERRO_LIMITE_TAXA` | 429 | Rate limit exceeded | Implement backoff strategy |
| `ERRO_TIMEOUT` | 504 | Request timeout | Increase timeout or optimize query |

### Error Handling Best Practices

```python
class APIErrorHandler:
    def __init__(self):
        self.retry_codes = ['ERRO_TIMEOUT', 'ERRO_BANCO_DADOS', 'ERRO_LIMITE_TAXA']
        self.permanent_codes = ['ERRO_AUTENTICACAO', 'ERRO_AUTORIZACAO', 'FORMATO_ARQUIVO_INVALIDO']
    
    def should_retry(self, error_code: str) -> bool:
        return error_code in self.retry_codes
    
    def get_retry_delay(self, attempt: int, error_code: str) -> int:
        if error_code == 'ERRO_LIMITE_TAXA':
            return min(60, 2 ** attempt)  # Exponential backoff, max 60s
        else:
            return min(30, 2 ** attempt)  # Standard backoff, max 30s
    
    def handle_error(self, error_response: dict, attempt: int = 1) -> dict:
        error_code = error_response.get('codigo_erro', 'UNKNOWN')
        message = error_response.get('mensagem', 'Unknown error')
        suggestion = error_response.get('sugestao_solucao', '')
        
        return {
            'error_code': error_code,
            'message': message,
            'suggestion': suggestion,
            'should_retry': self.should_retry(error_code),
            'retry_delay': self.get_retry_delay(attempt, error_code) if self.should_retry(error_code) else None,
            'is_permanent': error_code in self.permanent_codes
        }
```

## Natural Language Query Issues

### Problem: Query Returns No Results

**Symptoms:**
- Empty result sets for valid queries
- "No data found" messages
- Incorrect SQL generation

**Solutions:**

1. **Debug Query Interpretation**
```python
def debug_natural_query(query_text: str, token: str):
    """Debug natural language query processing"""
    
    payload = {
        "consulta": query_text,
        "incluir_insights": True,
        "nivel_executivo": "gerente"
    }
    
    response = requests.post(
        'http://localhost:8000/agentes/consulta-natural',
        json=payload,
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"Original Query: {result['consulta_original']}")
        print(f"AI Interpretation: {result['interpretacao_ia']}")
        print(f"Generated SQL: {result['sql_gerado']}")
        print(f"Result Count: {result['resultado']['total_registros']}")
        
        # Check if SQL is valid
        if "SELECT" not in result['sql_gerado'].upper():
            print("WARNING: Generated SQL may be invalid")
        
        # Check for common issues
        if result['resultado']['total_registros'] == 0:
            print("No results found. Possible issues:")
            print("- Date range too restrictive")
            print("- No data in specified period")
            print("- Incorrect table joins")
            print("- Missing data in database")
        
        return result
    else:
        print(f"Query failed: {response.json()}")
        return None

# Usage
debug_result = debug_natural_query(
    "Mostre os fornecedores de janeiro de 2024",
    token
)
```

2. **Improve Query Specificity**
```python
def suggest_query_improvements(original_query: str) -> list:
    """Suggest improvements for natural language queries"""
    
    suggestions = []
    
    # Check for date specificity
    if not any(word in original_query.lower() for word in ['janeiro', 'fevereiro', 'março', '2024', '2023', 'último', 'últimos']):
        suggestions.append("Add specific time period (e.g., 'nos últimos 6 meses', 'em 2024')")
    
    # Check for metric specificity
    if not any(word in original_query.lower() for word in ['valor', 'quantidade', 'volume', 'total', 'média']):
        suggestions.append("Specify what metric to analyze (e.g., 'por valor total', 'por quantidade')")
    
    # Check for entity specificity
    if not any(word in original_query.lower() for word in ['fornecedor', 'produto', 'categoria', 'estado']):
        suggestions.append("Specify what to analyze (e.g., 'fornecedores', 'produtos', 'categorias')")
    
    # Check for action specificity
    if not any(word in original_query.lower() for word in ['listar', 'mostrar', 'analisar', 'comparar', 'identificar']):
        suggestions.append("Use specific action verbs (e.g., 'liste', 'mostre', 'analise', 'compare')")
    
    return suggestions

# Example usage
query = "fornecedores"
improvements = suggest_query_improvements(query)
print("Suggested improvements:")
for improvement in improvements:
    print(f"- {improvement}")

# Better query
better_query = "Liste os 10 principais fornecedores por valor total de compras nos últimos 6 meses"
```

## Report Generation Problems

### Problem: Report Generation Timeout

**Symptoms:**
- Reports stuck in "processando" status
- Timeout errors after long wait
- Empty or incomplete reports

**Solutions:**

1. **Monitor Report Generation**
```python
async def monitor_report_generation(report_id: str, token: str, max_wait: int = 600):
    """Monitor report generation with detailed logging"""
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f'http://localhost:8000/agentes/relatorio-executivo/{report_id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data['status']
                
                if current_status != last_status:
                    elapsed = time.time() - start_time
                    print(f"[{elapsed:.1f}s] Report status: {current_status}")
                    last_status = current_status
                
                if current_status == 'concluido':
                    print(f"Report completed in {elapsed:.1f}s")
                    return status_data
                elif current_status == 'erro':
                    error_msg = status_data.get('error_message', 'Unknown error')
                    raise Exception(f"Report generation failed: {error_msg}")
                
            else:
                print(f"Error checking report status: {response.status_code}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"Error monitoring report: {e}")
            await asyncio.sleep(10)
    
    raise TimeoutError(f"Report generation timed out after {max_wait} seconds")
```

2. **Optimize Report Parameters**
```python
def optimize_report_parameters(report_config: dict) -> dict:
    """Optimize report parameters for better performance"""
    
    optimized_config = report_config.copy()
    
    # Limit date range for large datasets
    if 'periodo_inicio' in optimized_config and 'periodo_fim' in optimized_config:
        start_date = datetime.fromisoformat(optimized_config['periodo_inicio'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(optimized_config['periodo_fim'].replace('Z', '+00:00'))
        
        date_range = (end_date - start_date).days
        
        if date_range > 365:  # More than 1 year
            print("WARNING: Large date range may cause timeout")
            print("Consider splitting into smaller periods")
    
    # Optimize format for speed
    if optimized_config.get('formato') == 'xlsx' and optimized_config.get('incluir_graficos'):
        print("INFO: XLSX with charts may be slower than PDF")
        optimized_config['incluir_graficos'] = False  # Disable charts for faster generation
    
    # Limit data complexity
    if optimized_config.get('tipo_relatorio') == 'geral':
        print("INFO: General reports are more complex and slower")
        print("Consider using specific report types (fornecedores, produtos, impostos)")
    
    return optimized_config

# Usage
original_config = {
    "titulo": "Relatório Anual Completo",
    "tipo_relatorio": "geral",
    "formato": "xlsx",
    "periodo_inicio": "2023-01-01T00:00:00Z",
    "periodo_fim": "2024-12-31T23:59:59Z",
    "incluir_graficos": True
}

optimized_config = optimize_report_parameters(original_config)
```

## Supabase Integration Issues

### Problem: RLS Policy Conflicts

**Symptoms:**
- Users can't access their own data
- Service role operations fail
- Inconsistent data visibility

**Solutions:**

1. **Debug RLS Policies**
```sql
-- Check current RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Test policy with specific user
SET ROLE authenticated;
SET request.jwt.claim.sub = 'user-uuid-here';

-- Test query that should work
SELECT * FROM fiscal_documents WHERE user_id = 'user-uuid-here';

-- Reset role
RESET ROLE;
```

2. **Fix Common RLS Issues**
```sql
-- Ensure service role has full access
CREATE POLICY "Service role full access to fiscal_documents" 
ON fiscal_documents FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Ensure authenticated users can access their own data
CREATE POLICY "Users can access their own fiscal documents" 
ON fiscal_documents FOR ALL 
TO authenticated 
USING (user_id = auth.uid()) 
WITH CHECK (user_id = auth.uid());

-- Fix policy conflicts by dropping and recreating
DROP POLICY IF EXISTS "conflicting_policy_name" ON fiscal_documents;

-- Create comprehensive policy
CREATE POLICY "fiscal_documents_user_access" 
ON fiscal_documents FOR ALL 
TO authenticated 
USING (
    user_id = auth.uid() OR 
    auth.role() = 'service_role'
) 
WITH CHECK (
    user_id = auth.uid() OR 
    auth.role() = 'service_role'
);
```

### Problem: Storage Bucket Access Issues

**Symptoms:**
- File upload fails to storage
- "Access denied" errors for file operations
- Files not visible after upload

**Solutions:**

1. **Configure Storage Policies**
```sql
-- Create storage bucket policy for XML files
INSERT INTO storage.buckets (id, name, public) 
VALUES ('invoice-xmls', 'invoice-xmls', false);

-- Allow authenticated users to upload files
CREATE POLICY "Users can upload XML files" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (
    bucket_id = 'invoice-xmls' AND 
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to read their own files
CREATE POLICY "Users can read their own XML files" 
ON storage.objects FOR SELECT 
TO authenticated 
USING (
    bucket_id = 'invoice-xmls' AND 
    (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow service role full access
CREATE POLICY "Service role full access to XML files" 
ON storage.objects FOR ALL 
TO service_role 
USING (bucket_id = 'invoice-xmls') 
WITH CHECK (bucket_id = 'invoice-xmls');
```

2. **Test Storage Operations**
```python
def test_storage_operations(supabase_client, user_id: str):
    """Test Supabase storage operations"""
    
    bucket_name = 'invoice-xmls'
    test_file_path = f"{user_id}/test.xml"
    test_content = b'<?xml version="1.0"?><test>content</test>'
    
    try:
        # Test upload
        upload_result = supabase_client.storage.from_(bucket_name).upload(
            test_file_path,
            test_content,
            file_options={"content-type": "application/xml"}
        )
        print(f"Upload successful: {upload_result}")
        
        # Test download
        download_result = supabase_client.storage.from_(bucket_name).download(test_file_path)
        print(f"Download successful: {len(download_result)} bytes")
        
        # Test list files
        list_result = supabase_client.storage.from_(bucket_name).list(user_id)
        print(f"List successful: {len(list_result)} files")
        
        # Cleanup
        delete_result = supabase_client.storage.from_(bucket_name).remove([test_file_path])
        print(f"Cleanup successful: {delete_result}")
        
        return True
        
    except Exception as e:
        print(f"Storage operation failed: {e}")
        return False
```

## Development Environment Setup

### Problem: Environment Configuration Issues

**Symptoms:**
- Services fail to start
- Connection errors between components
- Missing environment variables

**Solutions:**

1. **Validate Environment Configuration**
```python
import os
from typing import Dict, List

def validate_environment() -> Dict[str, List[str]]:
    """Validate all required environment variables"""
    
    required_vars = {
        'backend': [
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'SUPABASE_SERVICE_KEY',
            'OPENAI_API_KEY',
            'REDIS_URL',
            'DATABASE_URL'
        ],
        'frontend': [
            'NUXT_PUBLIC_API_BASE_URL',
            'NUXT_PUBLIC_SUPABASE_URL',
            'NUXT_PUBLIC_SUPABASE_ANON_KEY'
        ]
    }
    
    issues = {'missing': [], 'empty': [], 'invalid': []}
    
    for component, vars_list in required_vars.items():
        for var in vars_list:
            value = os.getenv(var)
            
            if value is None:
                issues['missing'].append(f"{component}: {var}")
            elif not value.strip():
                issues['empty'].append(f"{component}: {var}")
            elif var.endswith('_URL') and not value.startswith(('http://', 'https://', 'postgresql://', 'redis://')):
                issues['invalid'].append(f"{component}: {var} - Invalid URL format")
    
    return issues

def print_environment_report():
    """Print environment validation report"""
    issues = validate_environment()
    
    if not any(issues.values()):
        print("✅ All environment variables are properly configured")
        return True
    
    print("❌ Environment configuration issues found:")
    
    if issues['missing']:
        print("\nMissing variables:")
        for var in issues['missing']:
            print(f"  - {var}")
    
    if issues['empty']:
        print("\nEmpty variables:")
        for var in issues['empty']:
            print(f"  - {var}")
    
    if issues['invalid']:
        print("\nInvalid variables:")
        for var in issues['invalid']:
            print(f"  - {var}")
    
    return False

# Usage
if __name__ == "__main__":
    print_environment_report()
```

2. **Setup Development Environment**
```bash
#!/bin/bash
# setup_dev_environment.sh

echo "Setting up AI Agents Invoice Analysis System development environment..."

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    if [[ $(echo "$python_version 3.9" | tr ' ' '\n' | sort -V | head -n1) != "3.9" ]]; then
        echo "❌ Python 3.9+ required, found $python_version"
        exit 1
    fi
    echo "✅ Python $python_version"
    
    # Check Node.js version
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found"
        exit 1
    fi
    node_version=$(node --version | cut -d'v' -f2)
    echo "✅ Node.js $node_version"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found"
        exit 1
    fi
    echo "✅ Docker available"
}

# Setup backend
setup_backend() {
    echo "Setting up backend..."
    
    cd backend
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Install spaCy model
    python -m spacy download pt_core_news_sm
    
    # Copy environment template
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "⚠️  Please configure backend/.env file"
    fi
    
    cd ..
}

# Setup frontend
setup_frontend() {
    echo "Setting up frontend..."
    
    cd frontend
    
    # Install dependencies
    npm install
    
    # Copy environment template
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "⚠️  Please configure frontend/.env file"
    fi
    
    cd ..
}

# Setup infrastructure
setup_infrastructure() {
    echo "Setting up infrastructure..."
    
    # Start Redis with Docker
    docker-compose -f docker-compose.dev.yml up -d redis
    
    echo "✅ Redis started"
}

# Run setup
check_prerequisites
setup_backend
setup_frontend
setup_infrastructure

echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure backend/.env with your Supabase and OpenAI credentials"
echo "2. Configure frontend/.env with your API endpoints"
echo "3. Run 'cd backend && python main.py' to start the backend"
echo "4. Run 'cd frontend && npm run dev' to start the frontend"
```

This comprehensive troubleshooting guide covers the most common issues developers encounter when working with the AI Agents Invoice Analysis System, providing practical solutions and debugging techniques for each scenario.