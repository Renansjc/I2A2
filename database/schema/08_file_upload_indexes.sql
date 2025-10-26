-- Indexes for File Upload Tracking Tables
-- Optimizes query performance for file upload and processing operations

-- Indexes for fiscal_documents table
CREATE INDEX idx_fiscal_documents_user_id ON fiscal_documents(user_id);
CREATE INDEX idx_fiscal_documents_processing_status ON fiscal_documents(processing_status);
CREATE INDEX idx_fiscal_documents_document_type ON fiscal_documents(document_type);
CREATE INDEX idx_fiscal_documents_upload_timestamp ON fiscal_documents(upload_timestamp DESC);
CREATE INDEX idx_fiscal_documents_filename ON fiscal_documents(filename);
CREATE INDEX idx_fiscal_documents_chave_nfe ON fiscal_documents(chave_nfe) WHERE chave_nfe IS NOT NULL;
CREATE INDEX idx_fiscal_documents_id_nfse ON fiscal_documents(id_nfse) WHERE id_nfse IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_fiscal_documents_user_status ON fiscal_documents(user_id, processing_status);
CREATE INDEX idx_fiscal_documents_user_type ON fiscal_documents(user_id, document_type);
CREATE INDEX idx_fiscal_documents_status_timestamp ON fiscal_documents(processing_status, upload_timestamp DESC);

-- Indexes for document_metadata table
CREATE INDEX idx_document_metadata_document_id ON document_metadata(document_id);
CREATE INDEX idx_document_metadata_cnpj_emitente ON document_metadata(cnpj_emitente);
CREATE INDEX idx_document_metadata_cnpj_destinatario ON document_metadata(cnpj_destinatario);
CREATE INDEX idx_document_metadata_data_emissao ON document_metadata(data_emissao DESC);
CREATE INDEX idx_document_metadata_valor_total ON document_metadata(valor_total DESC);
CREATE INDEX idx_document_metadata_numero_documento ON document_metadata(numero_documento);

-- Composite indexes for business queries
CREATE INDEX idx_document_metadata_emitente_data ON document_metadata(cnpj_emitente, data_emissao DESC);
CREATE INDEX idx_document_metadata_valor_data ON document_metadata(valor_total DESC, data_emissao DESC);

-- Indexes for processing_results table
CREATE INDEX idx_processing_results_document_id ON processing_results(document_id);
CREATE INDEX idx_processing_results_agent_name ON processing_results(agent_name);
CREATE INDEX idx_processing_results_result_type ON processing_results(result_type);
CREATE INDEX idx_processing_results_created_at ON processing_results(created_at DESC);
CREATE INDEX idx_processing_results_confidence_score ON processing_results(confidence_score DESC);

-- Composite indexes for agent queries
CREATE INDEX idx_processing_results_agent_type ON processing_results(agent_name, result_type);
CREATE INDEX idx_processing_results_document_agent ON processing_results(document_id, agent_name);

-- GIN index for JSONB result_data for efficient JSON queries
CREATE INDEX idx_processing_results_data_gin ON processing_results USING GIN (result_data);

-- Indexes for document_processing_status table
CREATE INDEX idx_document_processing_status_document_id ON document_processing_status(document_id);
CREATE INDEX idx_document_processing_status_agent_name ON document_processing_status(agent_name);
CREATE INDEX idx_document_processing_status_status ON document_processing_status(status);
CREATE INDEX idx_document_processing_status_started_at ON document_processing_status(started_at DESC);
CREATE INDEX idx_document_processing_status_next_retry ON document_processing_status(next_retry_at) WHERE next_retry_at IS NOT NULL;

-- Composite indexes for workflow queries
CREATE INDEX idx_document_processing_agent_status ON document_processing_status(agent_name, status);
CREATE INDEX idx_document_processing_document_status ON document_processing_status(document_id, status);

-- Indexes for file_metadata table
CREATE INDEX idx_file_metadata_document_id ON file_metadata(document_id);
CREATE INDEX idx_file_metadata_file_hash ON file_metadata(file_hash);
CREATE INDEX idx_file_metadata_validation_status ON file_metadata(validation_status);
CREATE INDEX idx_file_metadata_original_filename ON file_metadata(original_filename);
CREATE INDEX idx_file_metadata_mime_type ON file_metadata(mime_type);

-- GIN index for JSONB validation_errors for efficient JSON queries
CREATE INDEX idx_file_metadata_validation_errors_gin ON file_metadata USING GIN (validation_errors) WHERE validation_errors IS NOT NULL;