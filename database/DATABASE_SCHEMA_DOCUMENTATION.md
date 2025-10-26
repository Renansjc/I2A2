# Database Schema Documentation - AI Agents Invoice Analysis System

## Overview

The AI Agents Invoice Analysis System uses a comprehensive PostgreSQL database schema designed specifically for Brazilian electronic invoices (NF-e and NFS-e). The schema supports multi-tenant access through Supabase Row Level Security (RLS) and is optimized for executive analytics and LLM-powered agent processing.

## Architecture Principles

- **Star Schema Design**: Optimized for analytical queries with fact and dimension tables
- **Brazilian Compliance**: Full support for Brazilian fiscal document standards
- **Multi-tenant Security**: RLS policies ensure data isolation between users
- **Performance Optimized**: Strategic indexing for complex analytical queries
- **Audit Trail**: Complete tracking of data changes and processing history
- **Scalability**: Designed to handle large volumes of fiscal documents

## Database Structure

### Core Schema Files

1. **01_create_tables.sql** - Core dimension tables and document types
2. **02_nfe_tables.sql** - NF-e (Nota Fiscal Eletrônica) tables for products
3. **03_nfse_tables.sql** - NFS-e (Nota Fiscal de Serviços Eletrônica) tables for services
4. **04_views.sql** - Analytical views for executive queries
5. **05_indexes.sql** - Performance optimization indexes
6. **06_rls_policies.sql** - Row Level Security policies for Supabase

### Supabase Integration Tables

7. **fiscal_documents** - File upload tracking and processing status
8. **document_metadata** - Extracted metadata from uploaded XML files
9. **processing_results** - Agent processing results and insights
10. **document_processing_status** - Real-time agent processing status

## Table Specifications

### Core Dimension Tables

#### dim_tipo_documento
Document type control table for NF-e and NFS-e classification.

```sql
CREATE TABLE dim_tipo_documento (
    tipo VARCHAR(10) PRIMARY KEY,           -- 'NFE' or 'NFSE'
    descricao VARCHAR(100),                 -- Human-readable description
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Only 'NFE' and 'NFSE' types are supported
- Used for document classification and routing to appropriate agents

#### dim_emitente
Supplier/emitter dimension table with complete Brazilian business information.

```sql
CREATE TABLE dim_emitente (
    cnpj VARCHAR(14) PRIMARY KEY,          -- 14-digit CNPJ (Brazilian tax ID)
    cpf VARCHAR(11),                       -- 11-digit CPF for individuals
    inscricao_estadual VARCHAR(14),        -- State registration number
    razao_social VARCHAR(60),              -- Legal company name
    nome_fantasia VARCHAR(60),             -- Trade name
    logradouro VARCHAR(60),                -- Street address
    numero VARCHAR(60),                    -- Street number
    complemento VARCHAR(60),               -- Address complement
    bairro VARCHAR(60),                    -- Neighborhood
    codigo_municipio VARCHAR(7),           -- IBGE municipality code
    nome_municipio VARCHAR(60),            -- Municipality name
    uf VARCHAR(2),                         -- State abbreviation
    cep VARCHAR(8),                        -- ZIP code (CEP)
    codigo_pais VARCHAR(4),                -- Country code
    nome_pais VARCHAR(60),                 -- Country name
    telefone VARCHAR(14),                  -- Phone number
    email VARCHAR(60),                     -- Email address
    regime_tributario CHAR(1),             -- Tax regime (1=Simples, 2=Normal, 3=MEI)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- CNPJ is the primary identifier for companies
- CPF is used for individual suppliers (MEI)
- All address fields follow Brazilian postal standards
- State (UF) must be valid Brazilian state code

#### dim_destinatario
Customer/recipient dimension table with similar structure to emitente.

```sql
CREATE TABLE dim_destinatario (
    id BIGSERIAL PRIMARY KEY,              -- Surrogate key for recipients
    cnpj VARCHAR(14),                      -- Company CNPJ
    cpf VARCHAR(11),                       -- Individual CPF
    inscricao_estadual VARCHAR(14),        -- State registration
    razao_social VARCHAR(60),              -- Legal name
    -- ... (similar address fields as dim_emitente)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Uses surrogate key as recipients can be duplicated across documents
- Either CNPJ or CPF must be provided
- Address information is optional for recipients

#### dim_produtos
Product catalog for NF-e items with AI categorization support.

```sql
CREATE TABLE dim_produtos (
    codigo_produto VARCHAR(60) PRIMARY KEY, -- Product code from supplier
    ean VARCHAR(14),                        -- EAN barcode
    descricao TEXT,                         -- Product description
    ncm VARCHAR(8),                         -- NCM classification (Brazilian)
    cest VARCHAR(7),                        -- CEST code for tax substitution
    cfop VARCHAR(4),                        -- CFOP operation code
    unidade_comercial VARCHAR(6),           -- Commercial unit (UN, KG, etc.)
    unidade_tributavel VARCHAR(6),          -- Taxable unit
    categoria VARCHAR(100),                 -- AI-generated category
    subcategoria VARCHAR(100),              -- AI-generated subcategory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Product code is unique per supplier
- NCM classification is mandatory for tax calculation
- Categories are generated by AI Categorization Agent
- Full-text search enabled on description field

#### dim_servicos
Service catalog for NFS-e items with municipal tax codes.

```sql
CREATE TABLE dim_servicos (
    codigo_servico VARCHAR(20) PRIMARY KEY,     -- Service code
    descricao TEXT,                             -- Service description
    codigo_cnae VARCHAR(7),                     -- CNAE economic activity code
    codigo_tributacao_nacional VARCHAR(20),     -- National taxation code
    codigo_tributacao_municipal VARCHAR(20),    -- Municipal taxation code
    codigo_nbs VARCHAR(20),                     -- NBS nomenclature code
    categoria VARCHAR(100),                     -- AI-generated category
    subcategoria VARCHAR(100),                  -- AI-generated subcategory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Service codes vary by municipality
- CNAE code determines economic activity classification
- Municipal taxation codes are location-specific
- Categories generated by AI for service classification

### NF-e Fact Tables

#### nfe_main
Main NF-e document table with complete fiscal information.

```sql
CREATE TABLE nfe_main (
    chave_nfe VARCHAR(44) PRIMARY KEY,     -- 44-digit NFe access key
    numero_nf VARCHAR(9),                  -- Invoice number (1-999999999)
    serie VARCHAR(3),                      -- Series (0-999)
    modelo VARCHAR(2) DEFAULT '55',        -- Model (always 55 for NFe)
    data_emissao DATE,                     -- Issue date
    data_saida_entrada DATE,               -- Exit/Entry date
    tipo_operacao CHAR(1),                 -- 0=Entry, 1=Exit
    codigo_municipio VARCHAR(7),           -- IBGE municipality code
    uf_emitente VARCHAR(2),                -- Issuer state
    natureza_operacao VARCHAR(60),         -- Operation nature description
    forma_pagamento CHAR(1),               -- Payment method
    valor_total_nf NUMERIC(15,2),          -- Total invoice value
    valor_total_produtos NUMERIC(15,2),    -- Total products value
    valor_total_servicos NUMERIC(15,2),    -- Total services value
    base_calculo_icms NUMERIC(15,2),       -- ICMS calculation base
    valor_icms NUMERIC(15,2),              -- ICMS tax value
    base_calculo_icms_st NUMERIC(15,2),    -- ICMS ST calculation base
    valor_icms_st NUMERIC(15,2),           -- ICMS ST tax value
    valor_total_ipi NUMERIC(15,2),         -- Total IPI tax value
    valor_pis NUMERIC(15,2),               -- PIS tax value
    valor_cofins NUMERIC(15,2),            -- COFINS tax value
    xml_file_path VARCHAR(500),            -- Original XML file path
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Access key (chave_nfe) is unique and generated by SEFAZ
- Model is always '55' for NF-e documents
- All monetary values use NUMERIC(15,2) for precision
- Tax calculations must follow Brazilian fiscal rules

#### fact_itens_nfe
Detailed NF-e items with complete tax information.

```sql
CREATE TABLE fact_itens_nfe (
    id BIGSERIAL PRIMARY KEY,
    chave_nfe VARCHAR(44),                      -- FK to nfe_main
    numero_item INT,                            -- Item sequence (1-990)
    codigo_produto VARCHAR(60),                 -- FK to dim_produtos
    ean VARCHAR(14),                            -- EAN barcode
    descricao TEXT,                             -- Item description
    ncm VARCHAR(8),                             -- NCM classification
    cest VARCHAR(7),                            -- CEST code
    cfop VARCHAR(4),                            -- CFOP operation code
    unidade_comercial VARCHAR(6),               -- Commercial unit
    quantidade_comercial DECIMAL(15,4),         -- Commercial quantity
    valor_unitario_comercial DECIMAL(21,10),    -- Unit commercial value
    valor_total_bruto DECIMAL(15,2),            -- Gross total value
    -- Tax information for each item
    origem_produto CHAR(1),                     -- Product origin (0-8)
    situacao_tributaria_icms VARCHAR(3),        -- ICMS tax situation
    base_calculo_icms DECIMAL(15,2),            -- ICMS calculation base
    aliquota_icms DECIMAL(5,4),                 -- ICMS rate (0-1)
    valor_icms DECIMAL(15,2),                   -- ICMS value
    -- Additional tax fields for IPI, PIS, COFINS...
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_itens_nfe_main FOREIGN KEY (chave_nfe) REFERENCES nfe_main(chave_nfe),
    CONSTRAINT fk_itens_produto FOREIGN KEY (codigo_produto) REFERENCES dim_produtos(codigo_produto)
);
```

**Business Rules:**
- Each item must have valid NCM classification
- Tax calculations are item-specific
- CFOP determines tax treatment
- Quantities support up to 4 decimal places

### NFS-e Fact Tables

#### nfse_main
Main NFS-e document table for service invoices.

```sql
CREATE TABLE nfse_main (
    id_nfse VARCHAR(53) PRIMARY KEY,           -- NFS + 50 digits identifier
    numero_nfse VARCHAR(13),                   -- Sequential NFS-e number
    numero_dfse VARCHAR(15),                   -- Sequential DFSe number
    codigo_municipio_emissao VARCHAR(7),       -- Emission municipality code
    local_emissao VARCHAR(150),                -- Emission location description
    local_prestacao VARCHAR(150),              -- Service location description
    codigo_municipio_incidencia VARCHAR(7),    -- ISSQN incidence municipality
    local_incidencia VARCHAR(150),             -- Incidence location description
    tributacao_nacional VARCHAR(600),          -- National taxation description
    tributacao_municipal VARCHAR(600),         -- Municipal taxation description
    codigo_nbs VARCHAR(600),                   -- NBS code description
    data_emissao DATE,                         -- Emission date
    data_processamento TIMESTAMPTZ,            -- Processing timestamp
    ambiente_gerador CHAR(1),                  -- 1=Prefecture, 2=National System
    tipo_emissao CHAR(1),                      -- 1=Normal, 2=Transcribed
    processo_emissao CHAR(1),                  -- 1=WebService, 2=Web, 3=App
    codigo_status VARCHAR(3),                  -- Status code
    valor_total_servicos DECIMAL(15,2),        -- Total services value
    valor_total_deducoes DECIMAL(15,2),        -- Total deductions value
    valor_base_calculo DECIMAL(15,2),          -- Calculation base value
    valor_issqn DECIMAL(15,2),                 -- ISSQN tax value
    valor_credito DECIMAL(15,2),               -- Credit value
    xml_file_path VARCHAR(500),                -- Original XML file path
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- NFS-e ID follows municipal standards (varies by city)
- ISSQN tax is calculated based on service location
- Municipal taxation rules vary by municipality
- Service location determines tax jurisdiction

#### fact_servicos_nfse
Detailed NFS-e services with municipal tax information.

```sql
CREATE TABLE fact_servicos_nfse (
    id BIGSERIAL PRIMARY KEY,
    id_nfse VARCHAR(53),                       -- FK to nfse_main
    codigo_servico VARCHAR(20),                -- FK to dim_servicos
    descricao_servico TEXT,                    -- Service description
    quantidade DECIMAL(15,4),                  -- Service quantity
    valor_unitario DECIMAL(21,10),             -- Unit value
    valor_total DECIMAL(15,2),                 -- Total value
    valor_deducoes DECIMAL(15,2),              -- Deductions value
    valor_base_calculo DECIMAL(15,2),          -- Calculation base
    aliquota_issqn DECIMAL(5,4),              -- ISSQN rate
    valor_issqn DECIMAL(15,2),                 -- ISSQN value
    valor_credito DECIMAL(15,2),               -- Credit value
    codigo_cnae VARCHAR(7),                    -- CNAE code
    codigo_tributacao_nacional VARCHAR(20),    -- National taxation code
    codigo_tributacao_municipal VARCHAR(20),   -- Municipal taxation code
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_servicos_nfse_main FOREIGN KEY (id_nfse) REFERENCES nfse_main(id_nfse),
    CONSTRAINT fk_servicos_codigo FOREIGN KEY (codigo_servico) REFERENCES dim_servicos(codigo_servico)
);
```

**Business Rules:**
- Service codes are municipality-specific
- ISSQN rates vary by service type and location
- Deductions follow municipal regulations
- CNAE code determines service classification

### Supabase Integration Tables

#### fiscal_documents
File upload tracking and processing status for Supabase integration.

```sql
CREATE TABLE fiscal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),   -- Supabase user reference
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    document_type VARCHAR(10) NOT NULL,       -- 'NFE' or 'NFSE'
    xml_content TEXT NOT NULL,                -- Complete XML content
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending/processing/completed/error
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Each document belongs to a specific user (multi-tenant)
- XML content is stored for agent processing
- Processing status tracks agent workflow progress
- Error messages provide debugging information

#### document_metadata
Extracted metadata from uploaded XML files.

```sql
CREATE TABLE document_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    cnpj_emitente VARCHAR(14),
    nome_emitente VARCHAR(255),
    cnpj_destinatario VARCHAR(14),
    nome_destinatario VARCHAR(255),
    numero_documento VARCHAR(50),
    serie_documento VARCHAR(10),
    data_emissao TIMESTAMPTZ,
    valor_total DECIMAL(15,2),
    valor_tributos DECIMAL(15,2),
    natureza_operacao VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Metadata is extracted immediately upon upload
- Used for quick document identification and filtering
- Supports both NF-e and NFS-e metadata formats
- Cascading delete maintains referential integrity

#### processing_results
Agent processing results and insights storage.

```sql
CREATE TABLE processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,          -- Name of processing agent
    result_type VARCHAR(50) NOT NULL,         -- Type of result (analysis, categorization, etc.)
    result_data JSONB NOT NULL,               -- Structured result data
    confidence_score DECIMAL(3,2),            -- Confidence level (0.00-1.00)
    processing_time_ms INTEGER,               -- Processing time in milliseconds
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Each agent stores its processing results separately
- JSONB format allows flexible result structures
- Confidence scores help evaluate result quality
- Processing times enable performance monitoring

#### document_processing_status
Real-time agent processing status tracking.

```sql
CREATE TABLE document_processing_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,              -- not_started/in_progress/completed/failed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Business Rules:**
- Tracks each agent's processing status independently
- Supports retry mechanisms for failed processing
- Real-time status updates for user interface
- Error tracking for debugging and monitoring

### Document Linking Tables

#### document_nfe_links
Links uploaded documents to processed NF-e records.

```sql
CREATE TABLE document_nfe_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    chave_nfe VARCHAR(44) REFERENCES nfe_main(chave_nfe),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, chave_nfe)
);
```

#### document_nfse_links
Links uploaded documents to processed NFS-e records.

```sql
CREATE TABLE document_nfse_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    id_nfse VARCHAR(53) REFERENCES nfse_main(id_nfse),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(document_id, id_nfse)
);
```

## Analytical Views

### vw_documentos_fiscais
Unified view of all fiscal documents for executive queries.

```sql
CREATE VIEW vw_documentos_fiscais AS
SELECT 
    'NFE' as tipo_documento,
    chave_nfe as identificador,
    data_emissao,
    valor_total_nf as valor_total,
    NULL as valor_servicos,
    valor_total_produtos,
    NULL as valor_issqn,
    valor_icms,
    valor_total_ipi as valor_ipi,
    valor_pis,
    valor_cofins
FROM nfe_main
UNION ALL
SELECT 
    'NFSE' as tipo_documento,
    id_nfse as identificador,
    data_emissao,
    valor_total_servicos as valor_total,
    valor_total_servicos,
    NULL as valor_total_produtos,
    valor_issqn,
    NULL as valor_icms,
    NULL as valor_ipi,
    NULL as valor_pis,
    NULL as valor_cofins
FROM nfse_main;
```

**Usage:**
- Executive dashboards showing all document types
- Unified reporting across NF-e and NFS-e
- Simplified queries for business intelligence

### vw_fornecedores_resumo
Supplier summary view for executive analysis.

```sql
CREATE VIEW vw_fornecedores_resumo AS
SELECT 
    e.cnpj,
    e.razao_social,
    e.uf,
    COUNT(n.chave_nfe) as total_notas,
    SUM(n.valor_total_nf) as valor_total,
    AVG(n.valor_total_nf) as valor_medio,
    MIN(n.data_emissao) as primeira_compra,
    MAX(n.data_emissao) as ultima_compra
FROM dim_emitente e
LEFT JOIN nfe_main n ON e.cnpj = SUBSTRING(n.chave_nfe, 7, 14)
GROUP BY e.cnpj, e.razao_social, e.uf;
```

**Usage:**
- Supplier performance analysis
- Purchase volume tracking
- Supplier relationship management

### vw_analise_tributaria
Tax analysis view by period and document type.

```sql
CREATE VIEW vw_analise_tributaria AS
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFE' as tipo_documento,
    SUM(valor_total_nf) as valor_total,
    SUM(valor_icms) as icms,
    SUM(valor_total_ipi) as ipi,
    SUM(valor_pis) as pis,
    SUM(valor_cofins) as cofins,
    NULL as issqn,
    COUNT(*) as quantidade_documentos
FROM nfe_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM')
UNION ALL
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFSE' as tipo_documento,
    SUM(valor_total_servicos) as valor_total,
    NULL as icms,
    NULL as ipi,
    NULL as pis,
    NULL as cofins,
    SUM(valor_issqn) as issqn,
    COUNT(*) as quantidade_documentos
FROM nfse_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM');
```

**Usage:**
- Monthly tax burden analysis
- Tax optimization opportunities
- Compliance monitoring

## Performance Optimization

### Strategic Indexing

#### Primary Indexes
```sql
-- Date-based queries (most common)
CREATE INDEX idx_nfe_data_emissao ON nfe_main(data_emissao);
CREATE INDEX idx_nfse_data_emissao ON nfse_main(data_emissao);

-- Supplier-based queries
CREATE INDEX idx_nfe_emitente_cnpj ON nfe_main USING btree (SUBSTRING(chave_nfe, 7, 14));
CREATE INDEX idx_nfse_emitente_cnpj ON nfse_main USING btree (SUBSTRING(id_nfse, 9, 14));

-- Value-based queries
CREATE INDEX idx_nfe_valor_total ON nfe_main(valor_total_nf);
CREATE INDEX idx_nfse_valor_total ON nfse_main(valor_total_servicos);
```

#### Composite Indexes
```sql
-- Combined supplier and date queries
CREATE INDEX idx_nfe_emitente_data ON nfe_main USING btree (SUBSTRING(chave_nfe, 7, 14), data_emissao);
CREATE INDEX idx_nfse_emitente_data ON nfse_main USING btree (SUBSTRING(id_nfse, 9, 14), data_emissao);
```

#### Full-Text Search Indexes
```sql
-- Product and service description search
CREATE INDEX idx_produtos_descricao ON dim_produtos USING gin(to_tsvector('portuguese', descricao));
CREATE INDEX idx_servicos_descricao ON dim_servicos USING gin(to_tsvector('portuguese', descricao));
```

### Query Optimization Guidelines

1. **Date Range Queries**: Always use indexed date columns
2. **Supplier Analysis**: Use SUBSTRING functions on document keys
3. **Product Search**: Leverage full-text search indexes
4. **Aggregations**: Use materialized views for complex calculations
5. **Joins**: Ensure proper foreign key relationships

## Security Implementation

### Row Level Security (RLS)

#### User Data Isolation
```sql
-- Fiscal documents - users can only see their own documents
CREATE POLICY "Users can only access their own fiscal documents" 
ON fiscal_documents FOR ALL 
TO authenticated 
USING (user_id = auth.uid()) 
WITH CHECK (user_id = auth.uid());
```

#### Service Role Access
```sql
-- Service role has full access for agent processing
CREATE POLICY "Service role full access to fiscal documents" 
ON fiscal_documents FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
```

#### Dimension Table Access
```sql
-- Authenticated users can read all dimension data
CREATE POLICY "Authenticated users can read dimension tables" 
ON dim_emitente FOR SELECT 
TO authenticated 
USING (true);
```

### Data Protection Measures

1. **Encryption at Rest**: Supabase provides automatic encryption
2. **Encryption in Transit**: All connections use TLS/SSL
3. **Access Control**: RLS policies enforce data isolation
4. **Audit Trail**: All tables include created_at/updated_at timestamps
5. **Input Validation**: Application-level validation before database insertion

## Backup and Recovery

### Automated Backups
- **Supabase**: Automatic daily backups with point-in-time recovery
- **Local PostgreSQL**: Configure pg_dump for regular backups

### Recovery Procedures
1. **Point-in-time Recovery**: Restore to specific timestamp
2. **Table-level Recovery**: Restore individual tables if needed
3. **Data Validation**: Verify data integrity after recovery
4. **Agent Reprocessing**: Rerun agents on recovered documents if necessary

## Monitoring and Maintenance

### Performance Monitoring
```sql
-- Query performance analysis
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Index usage statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

### Maintenance Tasks
1. **VACUUM and ANALYZE**: Regular table maintenance
2. **Index Rebuilding**: Periodic index optimization
3. **Statistics Updates**: Keep query planner statistics current
4. **Partition Management**: Consider partitioning for large tables

## Migration and Versioning

### Schema Versioning
- Use numbered migration files (001_initial_schema.sql, 002_add_indexes.sql)
- Track schema version in dedicated table
- Implement rollback procedures for each migration

### Data Migration
- Export/import procedures for system upgrades
- Data transformation scripts for schema changes
- Validation procedures to ensure data integrity

## Integration Points

### Agent Processing Integration
- **Document Upload**: fiscal_documents table tracks upload status
- **Processing Status**: document_processing_status provides real-time updates
- **Results Storage**: processing_results stores agent outputs
- **Data Linking**: Links processed documents to main fiscal tables

### API Integration
- **Document Management**: CRUD operations on fiscal_documents
- **Status Tracking**: Real-time processing status queries
- **Analytics**: Views optimized for API response times
- **Search**: Full-text search capabilities for documents and products

### Reporting Integration
- **Executive Views**: Pre-built views for common business queries
- **Data Export**: Optimized queries for report generation
- **Real-time Dashboards**: Efficient queries for live data updates
- **Historical Analysis**: Time-series data for trend analysis

## Troubleshooting Guide

### Common Issues

#### Slow Query Performance
```sql
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public' AND n_distinct > 100;
```

#### Lock Contention
```sql
-- Monitor active locks
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

#### Data Integrity Issues
```sql
-- Check foreign key violations
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f' AND NOT convalidated;
```

### Performance Tuning

#### Connection Pooling
- Configure appropriate connection pool size
- Monitor connection usage patterns
- Implement connection timeout settings

#### Memory Configuration
- Adjust shared_buffers for available RAM
- Configure work_mem for complex queries
- Set effective_cache_size appropriately

#### Query Optimization
- Use EXPLAIN ANALYZE for query planning
- Implement query result caching where appropriate
- Consider materialized views for complex aggregations

## Future Enhancements

### Planned Features
1. **Partitioning**: Implement date-based partitioning for large tables
2. **Materialized Views**: Create pre-computed aggregations for dashboards
3. **Data Archiving**: Implement archival strategy for old documents
4. **Advanced Analytics**: Add machine learning result storage tables
5. **Real-time Streaming**: Consider event-driven architecture for real-time updates

### Scalability Considerations
1. **Horizontal Scaling**: Plan for read replicas
2. **Sharding Strategy**: Consider document-based sharding
3. **Caching Layer**: Implement Redis for frequently accessed data
4. **CDN Integration**: Optimize file storage and delivery

This comprehensive database schema documentation provides the foundation for understanding, maintaining, and extending the AI Agents Invoice Analysis System's data architecture.