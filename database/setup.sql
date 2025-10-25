-- AI Agents Invoice Analysis System - Complete Database Setup
-- Execute this file in your PostgreSQL/Supabase database

-- Load all schema files in order
\i schema/01_create_tables.sql
\i schema/02_nfe_tables.sql
\i schema/03_nfse_tables.sql
\i schema/04_views.sql
\i schema/05_indexes.sql
\i schema/06_rls_policies.sql

-- Verify setup
SELECT 'Database setup completed successfully!' as status;