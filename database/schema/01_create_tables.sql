-- AI Agents Invoice Analysis System Database Schema
-- PostgreSQL/Supabase compatible schema for NF-e and NFS-e processing

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Document type control table
CREATE TABLE dim_tipo_documento (
    tipo VARCHAR(10) PRIMARY KEY,
    descricao VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert document types
INSERT INTO dim_tipo_documento VALUES 
('NFE', 'Nota Fiscal Eletrônica - Produtos'),
('NFSE', 'Nota Fiscal de Serviços Eletrônica - Serviços');

-- Emitter (supplier) dimension table
CREATE TABLE dim_emitente (
    cnpj VARCHAR(14) PRIMARY KEY,       -- TCnpj: 14-digit CNPJ
    cpf VARCHAR(11),                    -- TCpf: 11-digit CPF (for individuals)
    inscricao_estadual VARCHAR(14),     -- TIe: State registration
    razao_social VARCHAR(60),           -- Company name
    nome_fantasia VARCHAR(60),          -- Trade name
    logradouro VARCHAR(60),             -- Street address
    numero VARCHAR(60),                 -- Street number
    complemento VARCHAR(60),            -- Address complement
    bairro VARCHAR(60),                 -- Neighborhood
    codigo_municipio VARCHAR(7),        -- TCodMunIBGE: Municipality code
    nome_municipio VARCHAR(60),         -- Municipality name
    uf VARCHAR(2),                      -- TUf: State
    cep VARCHAR(8),                     -- ZIP code
    codigo_pais VARCHAR(4),             -- Tpais: Country code
    nome_pais VARCHAR(60),              -- Country name
    telefone VARCHAR(14),               -- Phone number
    email VARCHAR(60),                  -- Email address
    regime_tributario CHAR(1),          -- Tax regime
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recipient (customer) dimension table
CREATE TABLE dim_destinatario (
    id BIGSERIAL PRIMARY KEY,
    cnpj VARCHAR(14),                   -- TCnpj: 14-digit CNPJ
    cpf VARCHAR(11),                    -- TCpf: 11-digit CPF
    inscricao_estadual VARCHAR(14),     -- TIeDest: State registration
    razao_social VARCHAR(60),           -- Company name
    logradouro VARCHAR(60),             -- Street address
    numero VARCHAR(60),                 -- Street number
    complemento VARCHAR(60),            -- Address complement
    bairro VARCHAR(60),                 -- Neighborhood
    codigo_municipio VARCHAR(7),        -- Municipality code
    nome_municipio VARCHAR(60),         -- Municipality name
    uf VARCHAR(2),                      -- State
    cep VARCHAR(8),                     -- ZIP code
    codigo_pais VARCHAR(4),             -- Country code
    nome_pais VARCHAR(60),              -- Country name
    telefone VARCHAR(14),               -- Phone number
    email VARCHAR(60),                  -- Email address
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Products dimension table (based on NFe item structure)
CREATE TABLE dim_produtos (
    codigo_produto VARCHAR(60) PRIMARY KEY, -- Product code
    ean VARCHAR(14),                    -- EAN barcode
    descricao TEXT,                     -- Product description
    ncm VARCHAR(8),                     -- NCM classification
    cest VARCHAR(7),                    -- CEST code
    cfop VARCHAR(4),                    -- CFOP code
    unidade_comercial VARCHAR(6),       -- Commercial unit
    unidade_tributavel VARCHAR(6),      -- Taxable unit
    categoria VARCHAR(100),             -- AI-generated category
    subcategoria VARCHAR(100),          -- AI-generated subcategory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Services dimension table (for NFS-e)
CREATE TABLE dim_servicos (
    codigo_servico VARCHAR(20) PRIMARY KEY, -- Service code
    descricao TEXT,                        -- Service description
    codigo_cnae VARCHAR(7),                -- CNAE code
    codigo_tributacao_nacional VARCHAR(20), -- National taxation code
    codigo_tributacao_municipal VARCHAR(20), -- Municipal taxation code
    codigo_nbs VARCHAR(20),                -- NBS code
    categoria VARCHAR(100),                -- AI-generated category
    subcategoria VARCHAR(100),             -- AI-generated subcategory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);