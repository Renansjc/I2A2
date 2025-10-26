# Integration Examples and Usage Patterns

## Overview

This document provides comprehensive examples and usage patterns for integrating with the AI Agents Invoice Analysis System. It includes code samples, best practices, and common integration scenarios for developers and system integrators.

## Table of Contents

1. [Authentication Setup](#authentication-setup)
2. [File Upload Integration](#file-upload-integration)
3. [Natural Language Query Integration](#natural-language-query-integration)
4. [Report Generation Integration](#report-generation-integration)
5. [Real-time Status Monitoring](#real-time-status-monitoring)
6. [Batch Processing](#batch-processing)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Performance Optimization](#performance-optimization)
9. [SDK Examples](#sdk-examples)
10. [Webhook Integration](#webhook-integration)

## Authentication Setup

### Supabase Authentication

#### JavaScript/TypeScript Client
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseAnonKey = 'your-anon-key'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Sign in user
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session token for API calls
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Use token in API requests
const response = await fetch('http://localhost:8000/api/documents', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

#### Python Client
```python
import requests
from supabase import create_client, Client

# Initialize Supabase client
url = "https://your-project.supabase.co"
key = "your-anon-key"
supabase: Client = create_client(url, key)

# Sign in user
auth_response = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "password"
})

# Get access token
token = auth_response.session.access_token

# Use token for API requests
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

response = requests.get('http://localhost:8000/api/documents', headers=headers)
```

## File Upload Integration

### Single File Upload

#### JavaScript/TypeScript
```typescript
async function uploadXMLFile(file: File, token: string) {
  const formData = new FormData()
  formData.append('arquivo', file)

  try {
    const response = await fetch('http://localhost:8000/agentes/upload-xml', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`)
    }

    const result = await response.json()
    console.log('Upload successful:', result)
    
    // Start monitoring processing status
    monitorProcessingStatus(result.id_processamento, token)
    
    return result
  } catch (error) {
    console.error('Upload error:', error)
    throw error
  }
}

// Usage example
const fileInput = document.getElementById('xmlFile') as HTMLInputElement
const file = fileInput.files?.[0]

if (file && file.name.endsWith('.xml')) {
  await uploadXMLFile(file, token)
}
```

#### Python
```python
import requests
from pathlib import Path

def upload_xml_file(file_path: str, token: str):
    """Upload XML file to the system"""
    
    with open(file_path, 'rb') as file:
        files = {'arquivo': (Path(file_path).name, file, 'application/xml')}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            'http://localhost:8000/agentes/upload-xml',
            files=files,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Upload successful: {result['id_processamento']}")
            
            # Monitor processing status
            monitor_processing_status(result['id_processamento'], token)
            
            return result
        else:
            error_detail = response.json()
            raise Exception(f"Upload failed: {error_detail}")

# Usage example
try:
    result = upload_xml_file('path/to/nfe.xml', token)
    document_id = result['id_processamento']
except Exception as e:
    print(f"Error uploading file: {e}")
```

### Batch File Upload

#### Python Batch Processing
```python
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Any

async def upload_xml_batch(file_paths: List[str], token: str, max_concurrent: int = 5):
    """Upload multiple XML files concurrently"""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def upload_single_file(session: aiohttp.ClientSession, file_path: str):
        async with semaphore:
            try:
                with open(file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('arquivo', file, filename=Path(file_path).name)
                    
                    headers = {'Authorization': f'Bearer {token}'}
                    
                    async with session.post(
                        'http://localhost:8000/agentes/upload-xml',
                        data=data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                'file_path': file_path,
                                'success': True,
                                'document_id': result['id_processamento'],
                                'result': result
                            }
                        else:
                            error = await response.json()
                            return {
                                'file_path': file_path,
                                'success': False,
                                'error': error
                            }
            except Exception as e:
                return {
                    'file_path': file_path,
                    'success': False,
                    'error': str(e)
                }
    
    async with aiohttp.ClientSession() as session:
        tasks = [upload_single_file(session, file_path) for file_path in file_paths]
        results = await asyncio.gather(*tasks)
        
        successful_uploads = [r for r in results if r['success']]
        failed_uploads = [r for r in results if not r['success']]
        
        print(f"Successful uploads: {len(successful_uploads)}")
        print(f"Failed uploads: {len(failed_uploads)}")
        
        return {
            'successful': successful_uploads,
            'failed': failed_uploads
        }

# Usage example
xml_files = [
    'xml_nf/42054072257653110000170000000000000725050541353120.xml',
    'xml_nf/42250383261420001201550990003348371042993209-nfe.xml',
    'xml_nf/42250802314041001583650100000616501312602792.XML'
]

results = asyncio.run(upload_xml_batch(xml_files, token))
```

## Natural Language Query Integration

### Executive Dashboard Queries

#### JavaScript/TypeScript
```typescript
interface QueryRequest {
  consulta: string
  tipo_consulta?: string
  periodo_inicio?: string
  periodo_fim?: string
  nivel_executivo?: string
  incluir_insights?: boolean
}

async function executeNaturalQuery(query: QueryRequest, token: string) {
  try {
    const response = await fetch('http://localhost:8000/agentes/consulta-natural', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(query)
    })

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`)
    }

    const result = await response.json()
    return result
  } catch (error) {
    console.error('Query error:', error)
    throw error
  }
}

// Example queries for executive dashboard
const executiveQueries = [
  {
    consulta: "Quais são os 10 principais fornecedores por volume de compras nos últimos 6 meses?",
    tipo_consulta: "fornecedores",
    periodo_inicio: "2024-01-01T00:00:00Z",
    periodo_fim: "2024-06-30T23:59:59Z",
    nivel_executivo: "ceo",
    incluir_insights: true
  },
  {
    consulta: "Mostre a evolução mensal dos gastos com impostos este ano",
    tipo_consulta: "impostos",
    periodo_inicio: "2024-01-01T00:00:00Z",
    periodo_fim: "2024-12-31T23:59:59Z",
    nivel_executivo: "cfo",
    incluir_insights: true
  },
  {
    consulta: "Identifique produtos com maior crescimento de vendas no último trimestre",
    tipo_consulta: "produtos",
    periodo_inicio: "2024-04-01T00:00:00Z",
    periodo_fim: "2024-06-30T23:59:59Z",
    nivel_executivo: "coo",
    incluir_insights: true
  }
]

// Execute queries and build dashboard
async function buildExecutiveDashboard(token: string) {
  const dashboardData = {}
  
  for (const query of executiveQueries) {
    try {
      const result = await executeNaturalQuery(query, token)
      dashboardData[query.tipo_consulta] = {
        query: query.consulta,
        data: result.resultado.dados,
        insights: result.insights,
        recommendations: result.recomendacoes
      }
    } catch (error) {
      console.error(`Failed to execute query: ${query.consulta}`, error)
    }
  }
  
  return dashboardData
}
```

#### Python Analytics Integration
```python
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AIAgentsAnalytics:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def execute_query(self, query_text: str, query_type: str = None, 
                     start_date: str = None, end_date: str = None,
                     executive_level: str = "gerente") -> Dict[str, Any]:
        """Execute natural language query"""
        
        payload = {
            "consulta": query_text,
            "nivel_executivo": executive_level,
            "incluir_insights": True
        }
        
        if query_type:
            payload["tipo_consulta"] = query_type
        if start_date:
            payload["periodo_inicio"] = start_date
        if end_date:
            payload["periodo_fim"] = end_date
        
        response = requests.post(
            f"{self.base_url}/agentes/consulta-natural",
            json=payload,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed: {response.json()}")
    
    def get_supplier_analysis(self, months_back: int = 6) -> pd.DataFrame:
        """Get supplier analysis as pandas DataFrame"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        query = f"Analise os fornecedores por volume de compras nos últimos {months_back} meses"
        
        result = self.execute_query(
            query,
            query_type="fornecedores",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Convert to DataFrame
        columns = result['resultado']['colunas']
        data = result['resultado']['dados']
        
        df = pd.DataFrame(data, columns=columns)
        
        # Add insights as metadata
        df.attrs['insights'] = result['insights']
        df.attrs['recommendations'] = result['recomendacoes']
        
        return df
    
    def get_tax_analysis(self, year: int = None) -> Dict[str, pd.DataFrame]:
        """Get comprehensive tax analysis"""
        
        if year is None:
            year = datetime.now().year
        
        start_date = f"{year}-01-01T00:00:00Z"
        end_date = f"{year}-12-31T23:59:59Z"
        
        queries = {
            'monthly_taxes': f"Mostre a evolução mensal dos impostos em {year}",
            'tax_by_type': f"Analise os impostos por tipo de documento em {year}",
            'tax_efficiency': f"Identifique oportunidades de otimização fiscal em {year}"
        }
        
        results = {}
        
        for key, query in queries.items():
            try:
                result = self.execute_query(
                    query,
                    query_type="impostos",
                    start_date=start_date,
                    end_date=end_date,
                    executive_level="cfo"
                )
                
                columns = result['resultado']['colunas']
                data = result['resultado']['dados']
                
                df = pd.DataFrame(data, columns=columns)
                df.attrs['insights'] = result['insights']
                
                results[key] = df
                
            except Exception as e:
                print(f"Failed to execute query {key}: {e}")
                results[key] = pd.DataFrame()
        
        return results

# Usage example
analytics = AIAgentsAnalytics('http://localhost:8000', token)

# Get supplier analysis
supplier_df = analytics.get_supplier_analysis(months_back=12)
print("Top 5 suppliers:")
print(supplier_df.head())
print("\nInsights:")
for insight in supplier_df.attrs['insights']:
    print(f"- {insight['descricao']} (Confidence: {insight['confianca']:.2f})")

# Get tax analysis
tax_analysis = analytics.get_tax_analysis(2024)
monthly_taxes = tax_analysis['monthly_taxes']
print("\nMonthly tax evolution:")
print(monthly_taxes)
```

## Report Generation Integration

### Automated Report Generation

#### Python Report Scheduler
```python
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class ReportScheduler:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def generate_report(self, report_config: Dict[str, Any]) -> str:
        """Generate executive report"""
        
        response = requests.post(
            f"{self.base_url}/agentes/relatorio-executivo",
            json=report_config,
            headers=self.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['id_relatorio']
        else:
            raise Exception(f"Report generation failed: {response.json()}")
    
    def check_report_status(self, report_id: str) -> Dict[str, Any]:
        """Check report generation status"""
        
        response = requests.get(
            f"{self.base_url}/agentes/relatorio-executivo/{report_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get report status: {response.json()}")
    
    def wait_for_report_completion(self, report_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for report completion with timeout"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_report_status(report_id)
            
            if status['status'] == 'concluido':
                return status
            elif status['status'] == 'erro':
                raise Exception(f"Report generation failed: {status.get('error_message', 'Unknown error')}")
            
            time.sleep(10)  # Check every 10 seconds
        
        raise TimeoutError(f"Report generation timed out after {timeout} seconds")
    
    def generate_monthly_reports(self):
        """Generate monthly reports for all executives"""
        
        # Calculate previous month
        today = datetime.now()
        first_day_current_month = today.replace(day=1)
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        first_day_previous_month = last_day_previous_month.replace(day=1)
        
        period_start = first_day_previous_month.isoformat()
        period_end = last_day_previous_month.isoformat()
        
        reports_config = [
            {
                "titulo": f"Relatório Executivo CEO - {last_day_previous_month.strftime('%B %Y')}",
                "tipo_relatorio": "geral",
                "formato": "pdf",
                "periodo_inicio": period_start,
                "periodo_fim": period_end,
                "nivel_executivo": "ceo",
                "incluir_resumo_executivo": True,
                "incluir_recomendacoes": True,
                "incluir_graficos": True
            },
            {
                "titulo": f"Relatório Financeiro CFO - {last_day_previous_month.strftime('%B %Y')}",
                "tipo_relatorio": "impostos",
                "formato": "xlsx",
                "periodo_inicio": period_start,
                "periodo_fim": period_end,
                "nivel_executivo": "cfo",
                "incluir_resumo_executivo": True,
                "incluir_recomendacoes": True,
                "incluir_graficos": True
            },
            {
                "titulo": f"Relatório Operacional COO - {last_day_previous_month.strftime('%B %Y')}",
                "tipo_relatorio": "fornecedores",
                "formato": "pdf",
                "periodo_inicio": period_start,
                "periodo_fim": period_end,
                "nivel_executivo": "coo",
                "incluir_resumo_executivo": True,
                "incluir_recomendacoes": True,
                "incluir_graficos": True
            }
        ]
        
        generated_reports = []
        
        for config in reports_config:
            try:
                print(f"Generating report: {config['titulo']}")
                report_id = self.generate_report(config)
                
                print(f"Waiting for report completion: {report_id}")
                completed_report = self.wait_for_report_completion(report_id)
                
                generated_reports.append({
                    'config': config,
                    'report_id': report_id,
                    'status': completed_report,
                    'download_url': completed_report.get('url_download')
                })
                
                print(f"Report completed: {completed_report['url_download']}")
                
            except Exception as e:
                print(f"Failed to generate report {config['titulo']}: {e}")
                generated_reports.append({
                    'config': config,
                    'error': str(e)
                })
        
        return generated_reports

# Schedule monthly reports
scheduler = ReportScheduler('http://localhost:8000', token)

# Schedule to run on the 1st day of each month at 9 AM
schedule.every().month.at("09:00").do(scheduler.generate_monthly_reports)

# Keep the scheduler running
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

## Real-time Status Monitoring

### WebSocket-like Polling Implementation

#### JavaScript/TypeScript
```typescript
class DocumentStatusMonitor {
  private intervalId: number | null = null
  private callbacks: Map<string, (status: any) => void> = new Map()
  
  constructor(private token: string, private baseUrl: string = 'http://localhost:8000') {}
  
  startMonitoring(documentId: string, callback: (status: any) => void, interval: number = 5000) {
    this.callbacks.set(documentId, callback)
    
    const checkStatus = async () => {
      try {
        const response = await fetch(`${this.baseUrl}/api/documents/${documentId}/status`, {
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          }
        })
        
        if (response.ok) {
          const status = await response.json()
          callback(status)
          
          // Stop monitoring if processing is complete or failed
          if (status.overall_status === 'completed' || status.overall_status === 'error') {
            this.stopMonitoring(documentId)
          }
        }
      } catch (error) {
        console.error('Error checking document status:', error)
      }
    }
    
    // Initial check
    checkStatus()
    
    // Set up periodic checking
    this.intervalId = window.setInterval(checkStatus, interval)
  }
  
  stopMonitoring(documentId: string) {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    this.callbacks.delete(documentId)
  }
  
  stopAllMonitoring() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
    this.callbacks.clear()
  }
}

// Usage example
const monitor = new DocumentStatusMonitor(token)

// Monitor document processing
monitor.startMonitoring('document-uuid', (status) => {
  console.log('Document status update:', status)
  
  // Update UI based on status
  updateProcessingUI(status)
  
  if (status.overall_status === 'completed') {
    console.log('Processing completed!')
    showCompletionNotification(status)
  } else if (status.overall_status === 'error') {
    console.error('Processing failed:', status.error_summary)
    showErrorNotification(status.error_summary)
  }
})

function updateProcessingUI(status: any) {
  const progressContainer = document.getElementById('processing-progress')
  
  if (progressContainer) {
    const agentStatuses = status.agent_statuses
    const totalAgents = agentStatuses.length
    const completedAgents = agentStatuses.filter((agent: any) => agent.status === 'completed').length
    const failedAgents = agentStatuses.filter((agent: any) => agent.status === 'failed').length
    
    const progressPercentage = (completedAgents / totalAgents) * 100
    
    progressContainer.innerHTML = `
      <div class="progress-bar">
        <div class="progress-fill" style="width: ${progressPercentage}%"></div>
      </div>
      <div class="progress-text">
        ${completedAgents}/${totalAgents} agents completed
        ${failedAgents > 0 ? `(${failedAgents} failed)` : ''}
      </div>
      <div class="agent-details">
        ${agentStatuses.map((agent: any) => `
          <div class="agent-status ${agent.status}">
            ${agent.agent_name}: ${agent.status}
            ${agent.error_message ? `<span class="error">${agent.error_message}</span>` : ''}
          </div>
        `).join('')}
      </div>
    `
  }
}
```

## Error Handling Patterns

### Comprehensive Error Handling

#### Python Error Handler
```python
import logging
from typing import Dict, Any, Optional
from enum import Enum

class ErrorType(Enum):
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PROCESSING = "processing"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"

class AIAgentsError(Exception):
    def __init__(self, error_type: ErrorType, message: str, details: Optional[Dict[str, Any]] = None):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_api_error(self, response: requests.Response) -> AIAgentsError:
        """Handle API error responses"""
        
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"mensagem": response.text}
        
        error_code = error_data.get("codigo_erro", "UNKNOWN")
        message = error_data.get("mensagem", "Unknown error")
        details = error_data.get("detalhes", "")
        suggestion = error_data.get("sugestao_solucao", "")
        
        # Map HTTP status codes to error types
        if response.status_code == 401:
            error_type = ErrorType.AUTHENTICATION
        elif response.status_code == 400:
            error_type = ErrorType.VALIDATION
        elif response.status_code == 429:
            error_type = ErrorType.RATE_LIMIT
        elif response.status_code >= 500:
            error_type = ErrorType.INTERNAL
        else:
            error_type = ErrorType.PROCESSING
        
        self.logger.error(
            f"API Error: {error_code} - {message}",
            extra={
                "error_code": error_code,
                "status_code": response.status_code,
                "details": details,
                "suggestion": suggestion
            }
        )
        
        return AIAgentsError(
            error_type=error_type,
            message=f"{message} (Code: {error_code})",
            details={
                "error_code": error_code,
                "status_code": response.status_code,
                "details": details,
                "suggestion": suggestion
            }
        )
    
    def retry_with_backoff(self, func, max_retries: int = 3, backoff_factor: float = 2.0):
        """Retry function with exponential backoff"""
        
        for attempt in range(max_retries):
            try:
                return func()
            except AIAgentsError as e:
                if e.error_type == ErrorType.RATE_LIMIT and attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                elif e.error_type in [ErrorType.NETWORK, ErrorType.INTERNAL] and attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(f"Temporary error, retrying in {wait_time}s: {e.message}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    self.logger.warning(f"Unexpected error, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIAgentsError(
                        error_type=ErrorType.INTERNAL,
                        message=f"Unexpected error after {max_retries} attempts: {str(e)}"
                    )

# Usage example with error handling
class RobustAIAgentsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.error_handler = ErrorHandler()
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def upload_file_with_retry(self, file_path: str) -> Dict[str, Any]:
        """Upload file with automatic retry and error handling"""
        
        def upload_attempt():
            with open(file_path, 'rb') as file:
                files = {'arquivo': (Path(file_path).name, file, 'application/xml')}
                headers = {'Authorization': f'Bearer {self.token}'}
                
                response = requests.post(
                    f"{self.base_url}/agentes/upload-xml",
                    files=files,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise self.error_handler.handle_api_error(response)
        
        return self.error_handler.retry_with_backoff(upload_attempt)
    
    def query_with_retry(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute query with automatic retry and error handling"""
        
        def query_attempt():
            payload = {
                "consulta": query,
                "incluir_insights": True,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/agentes/consulta-natural",
                json=payload,
                headers=self.headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise self.error_handler.handle_api_error(response)
        
        return self.error_handler.retry_with_backoff(query_attempt)

# Usage with comprehensive error handling
client = RobustAIAgentsClient('http://localhost:8000', token)

try:
    # Upload file with automatic retry
    result = client.upload_file_with_retry('path/to/nfe.xml')
    print(f"File uploaded successfully: {result['id_processamento']}")
    
    # Execute query with automatic retry
    query_result = client.query_with_retry(
        "Quais são os principais fornecedores?",
        tipo_consulta="fornecedores",
        nivel_executivo="ceo"
    )
    print(f"Query executed successfully: {len(query_result['resultado']['dados'])} results")
    
except AIAgentsError as e:
    if e.error_type == ErrorType.AUTHENTICATION:
        print("Authentication failed. Please check your credentials.")
    elif e.error_type == ErrorType.VALIDATION:
        print(f"Validation error: {e.message}")
        if e.details.get("suggestion"):
            print(f"Suggestion: {e.details['suggestion']}")
    elif e.error_type == ErrorType.RATE_LIMIT:
        print("Rate limit exceeded. Please wait before making more requests.")
    else:
        print(f"Error: {e.message}")
        
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

## Performance Optimization

### Caching and Optimization Strategies

#### Redis Caching Implementation
```python
import redis
import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1 hour
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def cache_result(self, key: str, data: Any, ttl: int = None) -> None:
        """Cache result with TTL"""
        ttl = ttl or self.default_ttl
        serialized_data = json.dumps(data, default=str)
        self.redis_client.setex(key, ttl, serialized_data)
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result"""
        cached_data = self.redis_client.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def cached_query(self, ttl: int = None):
        """Decorator for caching query results"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.generate_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = self.get_cached_result(cache_key)
                if cached_result:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.cache_result(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Optimized client with caching
class OptimizedAIAgentsClient:
    def __init__(self, base_url: str, token: str, cache_manager: CacheManager):
        self.base_url = base_url
        self.token = token
        self.cache_manager = cache_manager
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    @property
    def cached_query(self):
        return self.cache_manager.cached_query(ttl=1800)  # 30 minutes
    
    @cached_query
    def get_supplier_summary(self, months_back: int = 6) -> Dict[str, Any]:
        """Get supplier summary with caching"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        payload = {
            "consulta": f"Resumo dos fornecedores nos últimos {months_back} meses",
            "tipo_consulta": "fornecedores",
            "periodo_inicio": start_date.isoformat(),
            "periodo_fim": end_date.isoformat(),
            "nivel_executivo": "gerente",
            "incluir_insights": True
        }
        
        response = requests.post(
            f"{self.base_url}/agentes/consulta-natural",
            json=payload,
            headers=self.headers
        )
        
        return response.json()
    
    @cached_query
    def get_product_categories(self) -> Dict[str, Any]:
        """Get product categories with caching"""
        payload = {
            "consulta": "Liste todas as categorias de produtos disponíveis",
            "tipo_consulta": "produtos",
            "incluir_insights": False
        }
        
        response = requests.post(
            f"{self.base_url}/agentes/consulta-natural",
            json=payload,
            headers=self.headers
        )
        
        return response.json()
    
    def get_documents_with_pagination(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Get documents with efficient pagination"""
        skip = (page - 1) * page_size
        
        response = requests.get(
            f"{self.base_url}/api/documents",
            params={
                'skip': skip,
                'limit': page_size
            },
            headers=self.headers
        )
        
        return response.json()

# Usage with caching
cache_manager = CacheManager()
optimized_client = OptimizedAIAgentsClient('http://localhost:8000', token, cache_manager)

# First call - executes query and caches result
supplier_data = optimized_client.get_supplier_summary(months_back=12)

# Second call - returns cached result (much faster)
supplier_data_cached = optimized_client.get_supplier_summary(months_back=12)
```

## SDK Examples

### Complete Python SDK

```python
# ai_agents_sdk.py
from typing import Dict, List, Any, Optional, Union
import requests
from pathlib import Path
import time
from datetime import datetime

class AIAgentsSDK:
    """Complete SDK for AI Agents Invoice Analysis System"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    # Document Management
    def upload_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Upload XML document for processing"""
        file_path = Path(file_path)
        
        with open(file_path, 'rb') as file:
            files = {'arquivo': (file_path.name, file, 'application/xml')}
            headers = {'Authorization': f'Bearer {self.token}'}
            
            response = requests.post(
                f"{self.base_url}/agentes/upload-xml",
                files=files,
                headers=headers
            )
            
            response.raise_for_status()
            return response.json()
    
    def list_documents(self, page: int = 1, page_size: int = 50, 
                      status_filter: str = None, document_type: str = None) -> Dict[str, Any]:
        """List user documents with pagination"""
        params = {
            'skip': (page - 1) * page_size,
            'limit': page_size
        }
        
        if status_filter:
            params['status_filter'] = status_filter
        if document_type:
            params['document_type_filter'] = document_type
        
        response = requests.get(
            f"{self.base_url}/api/documents",
            params=params,
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document details"""
        response = requests.get(
            f"{self.base_url}/api/documents/{document_id}",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get document processing status"""
        response = requests.get(
            f"{self.base_url}/api/documents/{document_id}/status",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    # Natural Language Queries
    def query(self, text: str, query_type: str = None, start_date: str = None,
             end_date: str = None, executive_level: str = "gerente",
             include_insights: bool = True) -> Dict[str, Any]:
        """Execute natural language query"""
        payload = {
            "consulta": text,
            "nivel_executivo": executive_level,
            "incluir_insights": include_insights
        }
        
        if query_type:
            payload["tipo_consulta"] = query_type
        if start_date:
            payload["periodo_inicio"] = start_date
        if end_date:
            payload["periodo_fim"] = end_date
        
        response = requests.post(
            f"{self.base_url}/agentes/consulta-natural",
            json=payload,
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    # Report Generation
    def generate_report(self, title: str, report_type: str, format: str = "pdf",
                       start_date: str = None, end_date: str = None,
                       executive_level: str = "ceo", **kwargs) -> str:
        """Generate executive report"""
        payload = {
            "titulo": title,
            "tipo_relatorio": report_type,
            "formato": format,
            "nivel_executivo": executive_level,
            "incluir_resumo_executivo": kwargs.get("include_summary", True),
            "incluir_recomendacoes": kwargs.get("include_recommendations", True),
            "incluir_graficos": kwargs.get("include_charts", True)
        }
        
        if start_date:
            payload["periodo_inicio"] = start_date
        if end_date:
            payload["periodo_fim"] = end_date
        
        response = requests.post(
            f"{self.base_url}/agentes/relatorio-executivo",
            json=payload,
            headers=self.headers
        )
        
        response.raise_for_status()
        result = response.json()
        return result['id_relatorio']
    
    def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """Get report generation status"""
        response = requests.get(
            f"{self.base_url}/agentes/relatorio-executivo/{report_id}",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def wait_for_report(self, report_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for report completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_report_status(report_id)
            
            if status['status'] == 'concluido':
                return status
            elif status['status'] == 'erro':
                raise Exception(f"Report generation failed: {status.get('error_message', 'Unknown error')}")
            
            time.sleep(10)
        
        raise TimeoutError(f"Report generation timed out after {timeout} seconds")
    
    # System Information
    def get_system_status(self) -> Dict[str, Any]:
        """Get system health status"""
        response = requests.get(
            f"{self.base_url}/status",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Get available agents and their capabilities"""
        response = requests.get(
            f"{self.base_url}/agentes/capacidades",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_query_examples(self) -> Dict[str, Any]:
        """Get example natural language queries"""
        response = requests.get(
            f"{self.base_url}/agentes/exemplos-consultas",
            headers=self.headers
        )
        
        response.raise_for_status()
        return response.json()

# Usage examples
if __name__ == "__main__":
    # Initialize SDK
    sdk = AIAgentsSDK('http://localhost:8000', 'your-jwt-token')
    
    # Upload document
    result = sdk.upload_document('path/to/nfe.xml')
    document_id = result['id_processamento']
    print(f"Document uploaded: {document_id}")
    
    # Execute query
    query_result = sdk.query(
        "Quais são os principais fornecedores nos últimos 6 meses?",
        query_type="fornecedores",
        executive_level="ceo"
    )
    print(f"Query results: {len(query_result['resultado']['dados'])} records")
    
    # Generate report
    report_id = sdk.generate_report(
        title="Relatório Mensal de Fornecedores",
        report_type="fornecedores",
        format="pdf",
        start_date="2024-01-01T00:00:00Z",
        end_date="2024-01-31T23:59:59Z"
    )
    
    # Wait for report completion
    completed_report = sdk.wait_for_report(report_id)
    print(f"Report completed: {completed_report['url_download']}")
```

This comprehensive integration documentation provides developers with practical examples and patterns for integrating with the AI Agents Invoice Analysis System, covering all major use cases from file uploads to advanced analytics and reporting.