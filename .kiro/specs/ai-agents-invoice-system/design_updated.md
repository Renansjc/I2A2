# Design Document - Updated for PostgreSQL/Supabase

## Data Lake Schema (PostgreSQL/Supabase Compatible)

The Data Lake will be organized to handle both NF-e (Nota Fiscal Eletrônica - Products) and NFS-e (Nota Fiscal de Serviços Eletrônica - Services) following their respective official Brazilian XML schema structures:

```sql
-- Document type control table
CREATE TABLE dim_tipo_documento (
    tipo VARCHAR(10) PRIMARY KEY,
    descricao VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO dim_tipo_documento VALUES 
('NFE', 'Nota Fiscal Eletrônica - Produtos'),
('NFSE', 'Nota Fiscal de Serviços Eletrônica - Serviços');

-- Enable Row Level Security (RLS) for Supabase
ALTER TABLE dim_tipo_documento ENABLE ROW LEVEL SECURITY;

-- NF-e main table (based on official schema)
CREATE TABLE nfe_main (
    chave_nfe VARCHAR(44) PRIMARY KEY,  -- TChNFe: 44-digit NFe key
    numero_nf VARCHAR(9),               -- TNF: Invoice number (1-9 digits)
    serie VARCHAR(3),                   -- TSerie: Series (0-999)
    modelo VARCHAR(2) DEFAULT '55',     -- TMod: Model (always 55 for NFe)
    data_emissao DATE,                  -- Issue date
    data_saida_entrada DATE,            -- Exit/Entry date
    tipo_operacao CHAR(1),              -- 0=Entry, 1=Exit
    codigo_municipio VARCHAR(7),        -- TCodMunIBGE: IBGE municipality code
    uf_emitente VARCHAR(2),             -- TUfEmi: Issuer state
    natureza_operacao VARCHAR(60),      -- Operation nature
    forma_pagamento CHAR(1),            -- Payment method
    valor_total_nf NUMERIC(15,2),       -- Total invoice value
    valor_total_produtos NUMERIC(15,2), -- Total products value
    valor_total_servicos NUMERIC(15,2), -- Total services value
    base_calculo_icms NUMERIC(15,2),    -- ICMS calculation base
    valor_icms NUMERIC(15,2),           -- ICMS value
    base_calculo_icms_st NUMERIC(15,2), -- ICMS ST calculation base
    valor_icms_st NUMERIC(15,2),        -- ICMS ST value
    valor_total_ipi NUMERIC(15,2),      -- Total IPI value
    valor_pis NUMERIC(15,2),            -- PIS value
    valor_cofins NUMERIC(15,2),         -- COFINS value
    xml_file_path VARCHAR(500),         -- Original XML file path
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE nfe_main ENABLE ROW LEVEL SECURITY;

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

ALTER TABLE dim_emitente ENABLE ROW LEVEL SECURITY;

-- NFS-e main table (based on official NFS-e schema)
CREATE TABLE nfse_main (
    id_nfse VARCHAR(53) PRIMARY KEY,       -- TSIdNFSe: NFS + 50 digits
    numero_nfse VARCHAR(13),               -- TSNNFSe: Sequential number
    numero_dfse VARCHAR(15),               -- TSNDFSe: Sequential DFSe number
    codigo_municipio_emissao VARCHAR(7),   -- Municipality code of emission
    local_emissao VARCHAR(150),            -- Emission location description
    local_prestacao VARCHAR(150),          -- Service location description
    codigo_municipio_incidencia VARCHAR(7), -- ISSQN incidence municipality
    local_incidencia VARCHAR(150),         -- Incidence location description
    tributacao_nacional VARCHAR(600),      -- National taxation description
    tributacao_municipal VARCHAR(600),     -- Municipal taxation description
    codigo_nbs VARCHAR(600),               -- NBS code description
    data_emissao DATE,                     -- Emission date
    data_processamento TIMESTAMPTZ,        -- Processing date/time
    ambiente_gerador CHAR(1),              -- 1=Prefecture, 2=National System
    tipo_emissao CHAR(1),                  -- 1=Normal, 2=Transcribed
    processo_emissao CHAR(1),              -- 1=WebService, 2=Web, 3=App
    codigo_status VARCHAR(3),              -- Status code
    valor_total_servicos NUMERIC(15,2),    -- Total services value
    valor_total_deducoes NUMERIC(15,2),    -- Total deductions value
    valor_base_calculo NUMERIC(15,2),      -- Calculation base value
    valor_issqn NUMERIC(15,2),             -- ISSQN value
    valor_credito NUMERIC(15,2),           -- Credit value
    xml_file_path VARCHAR(500),            -- Original XML file path
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE nfse_main ENABLE ROW LEVEL SECURITY;

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

ALTER TABLE dim_produtos ENABLE ROW LEVEL SECURITY;

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

ALTER TABLE dim_servicos ENABLE ROW LEVEL SECURITY;

-- Invoice items fact table (detailed NFe items)
CREATE TABLE fact_itens_nfe (
    id BIGSERIAL PRIMARY KEY,
    chave_nfe VARCHAR(44),              -- Foreign key to nfe_main
    numero_item INTEGER,                -- TnItem: Item number (1-990)
    codigo_produto VARCHAR(60),         -- Foreign key to dim_produtos
    ean VARCHAR(14),                    -- EAN barcode
    descricao TEXT,                     -- Item description
    ncm VARCHAR(8),                     -- NCM classification
    cest VARCHAR(7),                    -- CEST code
    cfop VARCHAR(4),                    -- CFOP code
    unidade_comercial VARCHAR(6),       -- Commercial unit
    quantidade_comercial NUMERIC(15,4), -- TDec_1204: Commercial quantity
    valor_unitario_comercial NUMERIC(21,10), -- TDec_1110: Unit commercial value
    valor_total_bruto NUMERIC(15,2),    -- Gross total value
    -- ICMS tax information
    origem_produto CHAR(1),             -- Product origin (0-8)
    situacao_tributaria_icms VARCHAR(3), -- ICMS tax situation
    base_calculo_icms NUMERIC(15,2),    -- ICMS calculation base
    aliquota_icms NUMERIC(5,4),         -- ICMS rate
    valor_icms NUMERIC(15,2),           -- ICMS value
    -- IPI tax information
    situacao_tributaria_ipi VARCHAR(2), -- IPI tax situation
    base_calculo_ipi NUMERIC(15,2),     -- IPI calculation base
    aliquota_ipi NUMERIC(5,4),          -- IPI rate
    valor_ipi NUMERIC(15,2),            -- IPI value
    -- PIS tax information
    situacao_tributaria_pis VARCHAR(2), -- PIS tax situation
    base_calculo_pis NUMERIC(15,2),     -- PIS calculation base
    aliquota_pis NUMERIC(5,4),          -- PIS rate
    valor_pis NUMERIC(15,2),            -- PIS value
    -- COFINS tax information
    situacao_tributaria_cofins VARCHAR(2), -- COFINS tax situation
    base_calculo_cofins NUMERIC(15,2),  -- COFINS calculation base
    aliquota_cofins NUMERIC(5,4),       -- COFINS rate
    valor_cofins NUMERIC(15,2),         -- COFINS value
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_itens_nfe_chave FOREIGN KEY (chave_nfe) REFERENCES nfe_main(chave_nfe),
    CONSTRAINT fk_itens_produto FOREIGN KEY (codigo_produto) REFERENCES dim_produtos(codigo_produto)
);

ALTER TABLE fact_itens_nfe ENABLE ROW LEVEL SECURITY;

-- NFS-e services fact table
CREATE TABLE fact_servicos_nfse (
    id BIGSERIAL PRIMARY KEY,
    id_nfse VARCHAR(53),                   -- Foreign key to nfse_main
    codigo_servico VARCHAR(20),            -- Foreign key to dim_servicos
    descricao_servico TEXT,                -- Service description
    quantidade NUMERIC(15,4),              -- Service quantity
    valor_unitario NUMERIC(21,10),         -- Unit value
    valor_total NUMERIC(15,2),             -- Total value
    valor_deducoes NUMERIC(15,2),          -- Deductions value
    valor_base_calculo NUMERIC(15,2),      -- Calculation base
    aliquota_issqn NUMERIC(5,4),          -- ISSQN rate
    valor_issqn NUMERIC(15,2),             -- ISSQN value
    valor_credito NUMERIC(15,2),           -- Credit value
    codigo_cnae VARCHAR(7),                -- CNAE code
    codigo_tributacao_nacional VARCHAR(20), -- National taxation code
    codigo_tributacao_municipal VARCHAR(20), -- Municipal taxation code
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_servicos_nfse FOREIGN KEY (id_nfse) REFERENCES nfse_main(id_nfse),
    CONSTRAINT fk_servicos_codigo FOREIGN KEY (codigo_servico) REFERENCES dim_servicos(codigo_servico)
);

ALTER TABLE fact_servicos_nfse ENABLE ROW LEVEL SECURITY;

-- Unified document view for executive queries
CREATE OR REPLACE VIEW vw_documentos_fiscais AS
SELECT 
    'NFE'::text as tipo_documento,
    chave_nfe as identificador,
    data_emissao,
    valor_total_nf as valor_total,
    NULL::numeric as valor_servicos,
    valor_total_produtos,
    NULL::numeric as valor_issqn,
    valor_icms,
    valor_ipi,
    valor_pis,
    valor_cofins,
    created_at
FROM nfe_main
UNION ALL
SELECT 
    'NFSE'::text as tipo_documento,
    id_nfse as identificador,
    data_emissao,
    valor_total_servicos as valor_total,
    valor_total_servicos,
    NULL::numeric as valor_total_produtos,
    valor_issqn,
    NULL::numeric as valor_icms,
    NULL::numeric as valor_ipi,
    NULL::numeric as valor_pis,
    NULL::numeric as valor_cofins,
    created_at
FROM nfse_main;

-- Enhanced analytical views for executive queries
CREATE OR REPLACE VIEW vw_fornecedores_completo AS
SELECT 
    e.cnpj,
    e.razao_social,
    e.uf,
    COUNT(CASE WHEN n.chave_nfe IS NOT NULL THEN 1 END) as total_nfe,
    COUNT(CASE WHEN ns.id_nfse IS NOT NULL THEN 1 END) as total_nfse,
    COALESCE(SUM(n.valor_total_nf), 0) as valor_total_produtos,
    COALESCE(SUM(ns.valor_total_servicos), 0) as valor_total_servicos,
    COALESCE(SUM(n.valor_total_nf), 0) + COALESCE(SUM(ns.valor_total_servicos), 0) as valor_total_geral,
    LEAST(MIN(n.data_emissao), MIN(ns.data_emissao)) as primeira_transacao,
    GREATEST(MAX(n.data_emissao), MAX(ns.data_emissao)) as ultima_transacao
FROM dim_emitente e
LEFT JOIN nfe_main n ON e.cnpj = SUBSTRING(n.chave_nfe FROM 7 FOR 14)
LEFT JOIN nfse_main ns ON e.cnpj = SUBSTRING(ns.id_nfse FROM 9 FOR 14)
GROUP BY e.cnpj, e.razao_social, e.uf;

CREATE OR REPLACE VIEW vw_analise_tributaria AS
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFE'::text as tipo_documento,
    SUM(valor_total_nf) as valor_total,
    SUM(valor_icms) as icms,
    SUM(valor_ipi) as ipi,
    SUM(valor_pis) as pis,
    SUM(valor_cofins) as cofins,
    NULL::numeric as issqn,
    COUNT(*) as quantidade_documentos
FROM nfe_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM')
UNION ALL
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFSE'::text as tipo_documento,
    SUM(valor_total_servicos) as valor_total,
    NULL::numeric as icms,
    NULL::numeric as ipi,
    NULL::numeric as pis,
    NULL::numeric as cofins,
    SUM(valor_issqn) as issqn,
    COUNT(*) as quantidade_documentos
FROM nfse_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM');

-- Indexes for performance optimization
CREATE INDEX idx_nfe_data_emissao ON nfe_main(data_emissao);
CREATE INDEX idx_nfe_emitente ON nfe_main(chave_nfe);
CREATE INDEX idx_nfse_data_emissao ON nfse_main(data_emissao);
CREATE INDEX idx_nfse_emitente ON nfse_main(id_nfse);
CREATE INDEX idx_itens_produto ON fact_itens_nfe(codigo_produto);
CREATE INDEX idx_itens_nfe ON fact_itens_nfe(chave_nfe);
CREATE INDEX idx_servicos_nfse ON fact_servicos_nfse(id_nfse);
CREATE INDEX idx_servicos_codigo ON fact_servicos_nfse(codigo_servico);
CREATE INDEX idx_emitente_uf ON dim_emitente(uf);
CREATE INDEX idx_produtos_categoria ON dim_produtos(categoria);
CREATE INDEX idx_servicos_categoria ON dim_servicos(categoria);

-- Supabase specific: Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_dim_tipo_documento_updated_at BEFORE UPDATE ON dim_tipo_documento FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nfe_main_updated_at BEFORE UPDATE ON nfe_main FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dim_emitente_updated_at BEFORE UPDATE ON dim_emitente FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dim_produtos_updated_at BEFORE UPDATE ON dim_produtos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_nfse_main_updated_at BEFORE UPDATE ON nfse_main FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_dim_servicos_updated_at BEFORE UPDATE ON dim_servicos FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```