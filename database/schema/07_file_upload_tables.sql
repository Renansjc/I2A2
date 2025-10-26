-- File Upload Tracking Tables for Supabase Integration
-- Extends existing schema with file upload and processing status tracking

-- Main fiscal documents upload tracking table
CREATE TABLE fiscal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    document_type VARCHAR(10) NOT NULL CHECK (document_type IN ('NFE', 'NFSE')),
    xml_content TEXT NOT NULL,
    upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'error', 'cancelled')
    ),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    error_message TEXT,
    -- Link to processed documents
    chave_nfe VARCHAR(44) REFERENCES nfe_main(chave_nfe) ON DELETE SET NULL,
    id_nfse VARCHAR(53) REFERENCES nfse_main(id_nfse) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_document_link CHECK (
        (document_type = 'NFE' AND chave_nfe IS NOT NULL AND id_nfse IS NULL) OR
        (document_type = 'NFSE' AND id_nfse IS NOT NULL AND chave_nfe IS NULL) OR
        (chave_nfe IS NULL AND id_nfse IS NULL)  -- Allow null during processing
    ),
    CONSTRAINT check_processing_times CHECK (
        processing_started_at IS NULL OR processing_started_at >= upload_timestamp
    ),
    CONSTRAINT check_completion_times CHECK (
        processing_completed_at IS NULL OR 
        (processing_started_at IS NOT NULL AND processing_completed_at >= processing_started_at)
    )
);

-- Document metadata extracted from XML files
CREATE TABLE document_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    -- Emitter information
    cnpj_emitente VARCHAR(14),
    nome_emitente VARCHAR(255),
    inscricao_estadual_emitente VARCHAR(14),
    -- Recipient information  
    cnpj_destinatario VARCHAR(14),
    nome_destinatario VARCHAR(255),
    inscricao_estadual_destinatario VARCHAR(14),
    -- Document information
    numero_documento VARCHAR(50),
    serie_documento VARCHAR(10),
    data_emissao DATE,
    data_saida_entrada DATE,
    -- Financial information
    valor_total DECIMAL(15,2),
    valor_tributos DECIMAL(15,2),
    valor_produtos DECIMAL(15,2),
    valor_servicos DECIMAL(15,2),
    -- Operation information
    natureza_operacao VARCHAR(255),
    tipo_operacao CHAR(1), -- 0=Entry, 1=Exit
    codigo_municipio VARCHAR(7),
    uf VARCHAR(2),
    -- Additional metadata
    ambiente_gerador CHAR(1), -- For NFS-e
    forma_pagamento CHAR(1), -- For NF-e
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate metadata
    CONSTRAINT unique_document_metadata UNIQUE (document_id)
);

-- Processing results from AI agents
CREATE TABLE processing_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL CHECK (
        agent_name IN (
            'xml_processing_agent',
            'ai_categorization_agent', 
            'sql_agent',
            'report_agent',
            'master_agent',
            'scheduler_agent',
            'data_lake_agent',
            'monitoring_agent'
        )
    ),
    result_type VARCHAR(50) NOT NULL,
    result_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_ms INTEGER CHECK (processing_time_ms >= 0),
    error_details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Index for efficient querying
    CONSTRAINT unique_agent_result UNIQUE (document_id, agent_name, result_type)
);

-- Document processing status tracking for agent workflow
CREATE TABLE document_processing_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (
        status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')
    ),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_agent_processing_times CHECK (
        completed_at IS NULL OR 
        (started_at IS NOT NULL AND completed_at >= started_at)
    ),
    CONSTRAINT unique_document_agent_status UNIQUE (document_id, agent_name)
);

-- File metadata for XML file information
CREATE TABLE file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_extension VARCHAR(10),
    mime_type VARCHAR(100),
    file_hash VARCHAR(64), -- SHA-256 hash for duplicate detection
    encoding VARCHAR(20) DEFAULT 'UTF-8',
    xml_version VARCHAR(10),
    xml_encoding VARCHAR(20),
    schema_version VARCHAR(20),
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (
        validation_status IN ('pending', 'valid', 'invalid', 'warning')
    ),
    validation_errors JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate files
    CONSTRAINT unique_file_hash UNIQUE (file_hash),
    CONSTRAINT unique_document_file_metadata UNIQUE (document_id)
);