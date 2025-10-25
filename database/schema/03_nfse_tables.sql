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
    valor_total_servicos DECIMAL(15,2),    -- Total services value
    valor_total_deducoes DECIMAL(15,2),    -- Total deductions value
    valor_base_calculo DECIMAL(15,2),      -- Calculation base value
    valor_issqn DECIMAL(15,2),             -- ISSQN value
    valor_credito DECIMAL(15,2),           -- Credit value
    xml_file_path VARCHAR(500),            -- Original XML file path
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- NFS-e services fact table
CREATE TABLE fact_servicos_nfse (
    id BIGSERIAL PRIMARY KEY,
    id_nfse VARCHAR(53),                   -- Foreign key to nfse_main
    codigo_servico VARCHAR(20),            -- Foreign key to dim_servicos
    descricao_servico TEXT,                -- Service description
    quantidade DECIMAL(15,4),              -- Service quantity
    valor_unitario DECIMAL(21,10),         -- Unit value
    valor_total DECIMAL(15,2),             -- Total value
    valor_deducoes DECIMAL(15,2),          -- Deductions value
    valor_base_calculo DECIMAL(15,2),      -- Calculation base
    aliquota_issqn DECIMAL(5,4),          -- ISSQN rate
    valor_issqn DECIMAL(15,2),             -- ISSQN value
    valor_credito DECIMAL(15,2),           -- Credit value
    codigo_cnae VARCHAR(7),                -- CNAE code
    codigo_tributacao_nacional VARCHAR(20), -- National taxation code
    codigo_tributacao_municipal VARCHAR(20), -- Municipal taxation code
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_servicos_nfse_main FOREIGN KEY (id_nfse) REFERENCES nfse_main(id_nfse),
    CONSTRAINT fk_servicos_codigo FOREIGN KEY (codigo_servico) REFERENCES dim_servicos(codigo_servico)
);