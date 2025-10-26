# API Documentation - AI Agents Invoice Analysis System

## Overview

The AI Agents Invoice Analysis System provides a comprehensive REST API for processing Brazilian electronic invoices (NF-e and NFS-e) using LLM-powered agents. The API supports natural language queries, automated document processing, and executive report generation.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses Supabase authentication with JWT tokens. Include the authorization header in all requests:

```
Authorization: Bearer <jwt_token>
```

## Content Type

All requests should use `application/json` content type unless specified otherwise.

## Error Handling

All errors follow a consistent format:

```json
{
  "codigo_erro": "ERRO_CODIGO",
  "mensagem": "Mensagem de erro em português",
  "detalhes": "Detalhes adicionais do erro",
  "sugestao_solucao": "Sugestão para resolver o problema",
  "timestamp": "2024-01-01T12:00:00Z",
  "id_rastreamento": "uuid-para-rastreamento"
}
```

### Common Error Codes

- `ERRO_VALIDACAO`: Validation error in request data
- `ERRO_AUTENTICACAO`: Authentication required or invalid
- `ERRO_AUTORIZACAO`: Insufficient permissions
- `ERRO_NAO_ENCONTRADO`: Resource not found
- `ERRO_INTERNO`: Internal server error
- `ERRO_LIMITE_TAXA`: Rate limit exceeded

## API Endpoints

### System Status

#### GET /status

Get system health and agent status.

**Response:**
```json
{
  "status_geral": "operacional",
  "agentes_ativos": {
    "processamento_xml": "ativo",
    "categorizacao_ia": "ativo",
    "agente_sql": "ativo",
    "agente_relatorio": "ativo",
    "master_agent": "ativo"
  },
  "versao_sistema": "1.0.0",
  "tempo_atividade": "Sistema iniciado",
  "estatisticas_uso": {
    "consultas_processadas": 150,
    "relatorios_gerados": 25,
    "xmls_processados": 300
  }
}
```

### Natural Language Queries

#### POST /agentes/consulta-natural

Process natural language queries about fiscal data using LLM agents.

**Request Body:**
```json
{
  "consulta": "Quais são os principais fornecedores por volume de compras nos últimos 6 meses?",
  "tipo_consulta": "fornecedores",
  "periodo_inicio": "2024-01-01T00:00:00Z",
  "periodo_fim": "2024-06-30T23:59:59Z",
  "contexto_usuario": {
    "empresa": "Exemplo Corp",
    "setor": "varejo"
  },
  "nivel_executivo": "ceo",
  "incluir_insights": true
}
```

**Response:**
```json
{
  "id_consulta": "uuid-da-consulta",
  "consulta_original": "Quais são os principais fornecedores...",
  "interpretacao_ia": "O usuário deseja analisar fornecedores por volume de compras",
  "sql_gerado": "SELECT e.razao_social, SUM(n.valor_total_nf) as volume...",
  "resultado": {
    "colunas": ["Fornecedor", "Volume Total", "Número de Notas"],
    "dados": [
      ["Fornecedor A", 150000.50, 45],
      ["Fornecedor B", 120000.30, 38]
    ],
    "total_registros": 2,
    "tempo_execucao": 0.15
  },
  "insights": [
    {
      "tipo": "tendencia",
      "descricao": "Concentração de compras em poucos fornecedores",
      "confianca": 0.92,
      "impacto_empresarial": "Risco de dependência de fornecedores",
      "recomendacao": "Diversificar base de fornecedores"
    }
  ],
  "explicacao_executiva": "Análise mostra concentração em top 5 fornecedores...",
  "recomendacoes": [
    "Negociar melhores condições com fornecedores principais",
    "Buscar fornecedores alternativos para reduzir risco"
  ],
  "confianca_geral": 0.89,
  "tempo_processamento": 2.3
}
```

### Executive Reports

#### POST /agentes/relatorio-executivo

Generate executive reports with AI-powered insights.

**Request Body:**
```json
{
  "titulo": "Relatório Mensal de Compras - Janeiro 2024",
  "tipo_relatorio": "compras",
  "formato": "pdf",
  "periodo_inicio": "2024-01-01T00:00:00Z",
  "periodo_fim": "2024-01-31T23:59:59Z",
  "nivel_executivo": "cfo",
  "incluir_resumo_executivo": true,
  "incluir_recomendacoes": true,
  "incluir_graficos": true,
  "filtros_adicionais": {
    "categoria": "eletrônicos",
    "valor_minimo": 1000
  },
  "contexto_empresarial": {
    "meta_reducao_custos": 0.05,
    "foco_sustentabilidade": true
  }
}
```

**Response:**
```json
{
  "id_relatorio": "uuid-do-relatorio",
  "titulo": "Relatório Mensal de Compras - Janeiro 2024",
  "status": "processando",
  "formato": "pdf",
  "url_download": null,
  "resumo_executivo": "Relatório sendo processado...",
  "principais_insights": [],
  "recomendacoes_estrategicas": [],
  "metricas_chave": {
    "periodo": "01/01/2024 - 31/01/2024",
    "tipo_relatorio": "compras",
    "nivel_executivo": "cfo"
  },
  "tempo_processamento": 0.5,
  "data_geracao": "2024-01-01T12:00:00Z"
}
```

#### GET /agentes/relatorio-executivo/{id_relatorio}

Get report status and download link.

**Response:**
```json
{
  "id_relatorio": "uuid-do-relatorio",
  "titulo": "Relatório Mensal de Compras - Janeiro 2024",
  "status": "concluido",
  "formato": "pdf",
  "url_download": "/downloads/relatorio_uuid.pdf",
  "resumo_executivo": "Janeiro apresentou crescimento de 15% nas compras...",
  "principais_insights": [
    {
      "tipo": "economia",
      "descricao": "Oportunidade de economia de R$ 50.000",
      "confianca": 0.87,
      "impacto_empresarial": "Redução de 3% nos custos operacionais"
    }
  ],
  "recomendacoes_estrategicas": [
    "Renegociar contratos com fornecedores de maior volume",
    "Implementar processo de cotação para compras acima de R$ 10.000"
  ],
  "metricas_chave": {
    "valor_total_periodo": 2500000.00,
    "numero_fornecedores": 45,
    "ticket_medio": 55555.56
  },
  "tempo_processamento": 5.2
}
```

### XML Document Processing

#### POST /agentes/upload-xml

Upload and process XML fiscal documents with Supabase integration.

**Request:** Multipart form data
- `arquivo`: XML file (max 10MB)

**Response:**
```json
{
  "id_processamento": "uuid-do-documento",
  "nome_arquivo": "nfe_exemplo.xml",
  "status": "processando",
  "documento": {
    "tipo_documento": "NFE",
    "chave_documento": "42240101234567890123456789012345678901234567",
    "fornecedor": "Fornecedor Exemplo Ltda",
    "valor_total": 15750.50,
    "data_emissao": "2024-01-15T10:30:00Z",
    "produtos_servicos": [],
    "categorias_identificadas": []
  },
  "insights_semanticos": [],
  "anomalias_detectadas": [],
  "validacoes_negocio": {},
  "validacao_brasileira": {},
  "confianca_processamento": 0.85,
  "tempo_processamento": 0.5,
  "proximos_passos": [
    "Processamento iniciado em background",
    "Análise semântica em andamento",
    "Categorização automática será executada",
    "Resultados estarão disponíveis em breve"
  ]
}
```

#### POST /agentes/processar-xml

Process XML content directly (alternative to file upload).

**Request Body:**
```json
{
  "nome_arquivo": "documento.xml",
  "conteudo_base64": "PD94bWwgdmVyc2lvbj0iMS4wIi...",
  "processar_com_ia": true,
  "extrair_insights": true,
  "categorizar_automaticamente": true,
  "validar_regras_negocio": true,
  "contexto_processamento": {
    "origem": "sistema_erp",
    "prioridade": "alta"
  }
}
```

#### GET /agentes/processar-xml/{id_processamento}

Get XML processing status and results.

**Response:**
```json
{
  "id_processamento": "uuid-do-processamento",
  "nome_arquivo": "documento.xml",
  "status": "concluido",
  "documento": {
    "tipo_documento": "NFE",
    "chave_documento": "42240101234567890123456789012345678901234567",
    "fornecedor": "Fornecedor ABC Ltda",
    "valor_total": 25430.75,
    "data_emissao": "2024-01-20T14:15:00Z",
    "produtos_servicos": [
      "Notebook Dell Inspiron 15",
      "Mouse Wireless Logitech",
      "Teclado Mecânico"
    ],
    "categorias_identificadas": [
      "Equipamentos de Informática",
      "Periféricos de Computador"
    ]
  },
  "insights_semanticos": [
    {
      "tipo": "categoria_produto",
      "descricao": "Produtos de tecnologia com alta demanda",
      "confianca": 0.94,
      "impacto_empresarial": "Oportunidade de negociação em volume"
    }
  ],
  "anomalias_detectadas": [],
  "validacoes_negocio": {
    "cnpj_valido": true,
    "valores_consistentes": true,
    "impostos_calculados_corretamente": true
  },
  "confianca_processamento": 0.95,
  "tempo_processamento": 1.8
}
```

### Document Management

#### GET /api/documents

List user's uploaded documents with pagination.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100, max: 1000)
- `status_filter`: Filter by processing status
- `document_type_filter`: Filter by document type (NFE/NFSE)

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid-documento-1",
      "filename": "nfe_janeiro_001.xml",
      "document_type": "NFE",
      "processing_status": "completed",
      "upload_timestamp": "2024-01-15T10:30:00Z",
      "file_size": 8456,
      "nome_emitente": "Fornecedor ABC Ltda",
      "valor_total": 15750.50,
      "data_emissao": "2024-01-15T08:00:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 100,
  "has_next": true
}
```

#### GET /api/documents/{document_id}

Get detailed document information.

**Response:**
```json
{
  "id": "uuid-documento",
  "filename": "nfe_exemplo.xml",
  "document_type": "NFE",
  "processing_status": "completed",
  "upload_timestamp": "2024-01-15T10:30:00Z",
  "file_size": 8456,
  "cnpj_emitente": "12345678000195",
  "nome_emitente": "Fornecedor ABC Ltda",
  "cnpj_destinatario": "98765432000187",
  "nome_destinatario": "Minha Empresa Ltda",
  "numero_documento": "000000123",
  "serie_documento": "001",
  "data_emissao": "2024-01-15T08:00:00Z",
  "valor_total": 15750.50,
  "valor_tributos": 2362.58,
  "natureza_operacao": "Venda de mercadorias",
  "processing_started_at": "2024-01-15T10:30:05Z",
  "processing_completed_at": "2024-01-15T10:32:18Z",
  "error_message": null,
  "chave_nfe": "42240101234567890123456789012345678901234567",
  "id_nfse": null
}
```

#### GET /api/documents/{document_id}/status

Get detailed processing status for a document.

**Response:**
```json
{
  "document_id": "uuid-documento",
  "overall_status": "completed",
  "agent_statuses": [
    {
      "agent_name": "xml_processing_agent",
      "status": "completed",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:30:45Z",
      "error_message": null,
      "retry_count": 0
    },
    {
      "agent_name": "ai_categorization_agent",
      "status": "completed",
      "started_at": "2024-01-15T10:30:45Z",
      "completed_at": "2024-01-15T10:31:20Z",
      "error_message": null,
      "retry_count": 0
    }
  ],
  "processing_results": [
    {
      "agent_name": "xml_processing_agent",
      "result_type": "document_analysis",
      "result_data": {
        "extracted_fields": 25,
        "validation_passed": true,
        "business_insights": 3
      },
      "confidence_score": 0.95,
      "processing_time_ms": 2000,
      "created_at": "2024-01-15T10:30:45Z"
    }
  ],
  "processing_started_at": "2024-01-15T10:30:05Z",
  "processing_completed_at": "2024-01-15T10:32:18Z",
  "total_processing_time_ms": 133000,
  "error_summary": null
}
```

### Agent Information

#### GET /agentes/capacidades

List available agents and their capabilities.

**Response:**
```json
{
  "agentes_disponiveis": {
    "master_agent": {
      "nome": "Agente Master",
      "descricao": "Orquestrador central com compreensão de linguagem natural",
      "capacidades": [
        "Interpretação de consultas em português",
        "Coordenação de workflow inteligente",
        "Comunicação executiva",
        "Geração de explicações de negócio"
      ]
    },
    "xml_processing_agent": {
      "nome": "Agente de Processamento XML",
      "descricao": "Processamento inteligente de documentos fiscais NF-e/NFS-e",
      "capacidades": [
        "Análise semântica de documentos",
        "Extração de contexto empresarial",
        "Detecção de anomalias",
        "Validação de regras de negócio"
      ]
    }
  },
  "formatos_suportados": {
    "entrada": ["XML (NF-e/NFS-e)", "Consultas em português", "JSON"],
    "saida": ["PDF", "XLSX", "DOCX", "JSON"]
  },
  "idiomas_suportados": ["Português Brasileiro"],
  "versao_api": "1.0.0"
}
```

#### GET /agentes/exemplos-consultas

Get example natural language queries.

**Response:**
```json
{
  "exemplos_consultas": {
    "fornecedores": [
      "Quais são os principais fornecedores por volume de compras nos últimos 6 meses?",
      "Mostre a evolução dos gastos com fornecedores de São Paulo",
      "Identifique fornecedores com comportamento de preço anômalo"
    ],
    "produtos": [
      "Quais produtos tiveram maior crescimento de vendas este ano?",
      "Analise a sazonalidade dos produtos de categoria eletrônicos",
      "Compare o desempenho de produtos nacionais vs importados"
    ]
  },
  "dicas_consultas": [
    "Use períodos específicos para análises mais precisas",
    "Mencione o nível de detalhamento desejado (resumo ou detalhado)",
    "Especifique se deseja comparações ou tendências",
    "Indique se precisa de recomendações de ação"
  ]
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard users**: 100 requests per minute
- **Premium users**: 500 requests per minute
- **Enterprise users**: 2000 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

The system supports webhooks for real-time notifications:

### Document Processing Complete
```json
{
  "event": "document.processing.completed",
  "document_id": "uuid-documento",
  "status": "completed",
  "processing_time_ms": 133000,
  "timestamp": "2024-01-15T10:32:18Z"
}
```

### Report Generation Complete
```json
{
  "event": "report.generation.completed",
  "report_id": "uuid-relatorio",
  "download_url": "/downloads/relatorio_uuid.pdf",
  "timestamp": "2024-01-15T10:45:30Z"
}
```

## SDK and Integration Examples

### Python SDK Example
```python
from ai_agents_client import AIAgentsClient

client = AIAgentsClient(
    base_url="https://api.example.com",
    api_key="your-api-key"
)

# Natural language query
result = client.query_natural(
    "Quais fornecedores tiveram maior crescimento este ano?",
    period_start="2024-01-01",
    period_end="2024-12-31"
)

# Upload XML document
with open("nfe.xml", "rb") as f:
    document = client.upload_xml(f)
    
# Check processing status
status = client.get_document_status(document.id)
```

### JavaScript/Node.js Example
```javascript
const { AIAgentsClient } = require('@ai-agents/client');

const client = new AIAgentsClient({
  baseURL: 'https://api.example.com',
  apiKey: 'your-api-key'
});

// Generate executive report
const report = await client.generateReport({
  title: 'Relatório Mensal',
  type: 'compras',
  format: 'pdf',
  periodStart: '2024-01-01',
  periodEnd: '2024-01-31'
});
```

## Support and Resources

- **API Status**: https://status.example.com
- **Documentation**: https://docs.example.com
- **Support**: support@example.com
- **Community**: https://community.example.com

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Natural language query processing
- XML document processing with Supabase integration
- Executive report generation
- Multi-agent coordination
- Portuguese language support
- Brazilian fiscal document validation

### Upcoming Features
- Real-time dashboard APIs
- Advanced analytics endpoints
- Bulk document processing
- Custom agent configuration
- Multi-language support expansion