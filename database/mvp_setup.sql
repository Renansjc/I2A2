-- MVP Sistema Simplificado de Análise Fiscal - Database Setup
-- Execute this file in your Supabase database for MVP deployment

-- Load the simplified MVP schema
\i schema/mvp_simplified_tables.sql

-- Insert sample data for testing (optional)
INSERT INTO fiscal_documents (filename, file_path, status) VALUES 
('exemplo.xml', '/storage/exemplo.xml', 'uploaded'),
('test_nfe.xml', '/storage/test_nfe.xml', 'completed');

-- Verify setup
SELECT 'MVP Database setup completed successfully!' as status;

-- Show created tables
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('fiscal_documents', 'extracted_data', 'document_items', 'executive_reports')
ORDER BY table_name;