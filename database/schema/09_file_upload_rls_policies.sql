-- Row Level Security (RLS) policies for File Upload Tracking Tables
-- Extends existing RLS policies to include file upload functionality

-- Enable RLS on all new tables
ALTER TABLE fiscal_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_processing_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;

-- Policies for fiscal_documents table
-- Users can only access their own documents
CREATE POLICY "Users can view their own fiscal documents" 
ON fiscal_documents FOR SELECT 
TO authenticated 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own fiscal documents" 
ON fiscal_documents FOR INSERT 
TO authenticated 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own fiscal documents" 
ON fiscal_documents FOR UPDATE 
TO authenticated 
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own fiscal documents" 
ON fiscal_documents FOR DELETE 
TO authenticated 
USING (auth.uid() = user_id);

-- Service role policies for fiscal_documents (for backend agents)
CREATE POLICY "Service role full access to fiscal documents" 
ON fiscal_documents FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Policies for document_metadata table
-- Users can only access metadata for their own documents
CREATE POLICY "Users can view metadata for their own documents" 
ON document_metadata FOR SELECT 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can insert metadata for their own documents" 
ON document_metadata FOR INSERT 
TO authenticated 
WITH CHECK (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can update metadata for their own documents" 
ON document_metadata FOR UPDATE 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete metadata for their own documents" 
ON document_metadata FOR DELETE 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

-- Service role policies for document_metadata
CREATE POLICY "Service role full access to document metadata" 
ON document_metadata FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Policies for processing_results table
-- Users can only view processing results for their own documents
CREATE POLICY "Users can view processing results for their own documents" 
ON processing_results FOR SELECT 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = processing_results.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

-- Only service role can insert/update/delete processing results (agents only)
CREATE POLICY "Service role full access to processing results" 
ON processing_results FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Policies for document_processing_status table
-- Users can only view processing status for their own documents
CREATE POLICY "Users can view processing status for their own documents" 
ON document_processing_status FOR SELECT 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = document_processing_status.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

-- Only service role can manage processing status (agents only)
CREATE POLICY "Service role full access to processing status" 
ON document_processing_status FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Policies for file_metadata table
-- Users can only access file metadata for their own documents
CREATE POLICY "Users can view file metadata for their own documents" 
ON file_metadata FOR SELECT 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = file_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can insert file metadata for their own documents" 
ON file_metadata FOR INSERT 
TO authenticated 
WITH CHECK (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = file_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can update file metadata for their own documents" 
ON file_metadata FOR UPDATE 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = file_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = file_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

CREATE POLICY "Users can delete file metadata for their own documents" 
ON file_metadata FOR DELETE 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM fiscal_documents 
        WHERE fiscal_documents.id = file_metadata.document_id 
        AND fiscal_documents.user_id = auth.uid()
    )
);

-- Service role policies for file_metadata
CREATE POLICY "Service role full access to file metadata" 
ON file_metadata FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);