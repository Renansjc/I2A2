# Database Setup for AI Agents Invoice Analysis System

This directory contains the complete database schema for the AI Agents Invoice Analysis System, designed to handle Brazilian electronic invoices (NF-e and NFS-e).

## Files Structure

- `setup.sql` - Main setup file that executes all schema files in order
- `schema/01_create_tables.sql` - Core dimension tables and document types
- `schema/02_nfe_tables.sql` - NF-e (Nota Fiscal Eletrônica) tables for products
- `schema/03_nfse_tables.sql` - NFS-e (Nota Fiscal de Serviços Eletrônica) tables for services
- `schema/04_views.sql` - Analytical views for executive queries
- `schema/05_indexes.sql` - Performance optimization indexes
- `schema/06_rls_policies.sql` - Row Level Security policies for Supabase

## Setup Instructions

### For Supabase (Recommended)

1. Create a new Supabase project
2. Go to SQL Editor in your Supabase dashboard
3. Copy and paste the contents of `setup.sql` or execute each schema file individually
4. Run the SQL to create all tables, views, indexes, and RLS policies

### For Local PostgreSQL

1. Create a new database:
   ```sql
   CREATE DATABASE ai_agents_invoice_system;
   ```

2. Connect to the database and run:
   ```bash
   psql -d ai_agents_invoice_system -f setup.sql
   ```

## Database Schema Overview

### Core Tables

- **dim_tipo_documento**: Document type control (NFE/NFSE)
- **dim_emitente**: Supplier/emitter information
- **dim_destinatario**: Customer/recipient information
- **dim_produtos**: Product catalog for NF-e
- **dim_servicos**: Service catalog for NFS-e

### NF-e Tables (Products)

- **nfe_main**: Main NF-e document information
- **fact_itens_nfe**: Detailed NF-e items with tax information
- **nfe_eventos**: NF-e lifecycle events

### NFS-e Tables (Services)

- **nfse_main**: Main NFS-e document information
- **fact_servicos_nfse**: Detailed NFS-e services with tax information

### Analytical Views

- **vw_documentos_fiscais**: Unified view of all fiscal documents
- **vw_fornecedores_resumo**: Supplier summary for executive analysis
- **vw_produtos_mais_comprados**: Most purchased products analysis
- **vw_fornecedores_completo**: Complete supplier analysis (NFE + NFSE)
- **vw_analise_tributaria**: Tax analysis by period and document type

## Security Features

- Row Level Security (RLS) enabled on all tables
- Policies for authenticated users (C-level executives)
- Service role policies for automated agent processing
- Full audit trail with created_at/updated_at timestamps

## Performance Optimizations

- Indexes on frequently queried columns
- Composite indexes for common query patterns
- Full-text search indexes for product/service descriptions
- Optimized views for executive dashboards

## Requirements Addressed

- **Requirement 6.1**: Centralized data storage with integrity and consistency
- **Requirement 6.2**: Data integrity maintenance and referential constraints
- **Requirement 6.3**: Historical data preservation for trend analysis
- **Requirement 6.4**: Referential integrity between invoices, suppliers, and products
- **Requirement 6.5**: Optimized access for complex queries and advanced analytics