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

-- Invoice items fact table (detailed NFe items)
CREATE TABLE fact_itens_nfe (
    id BIGSERIAL PRIMARY KEY,
    chave_nfe VARCHAR(44),              -- Foreign key to nfe_main
    numero_item INT,                    -- TnItem: Item number (1-990)
    codigo_produto VARCHAR(60),         -- Foreign key to dim_produtos
    ean VARCHAR(14),                    -- EAN barcode
    descricao TEXT,                     -- Item description
    ncm VARCHAR(8),                     -- NCM classification
    cest VARCHAR(7),                    -- CEST code
    cfop VARCHAR(4),                    -- CFOP code
    unidade_comercial VARCHAR(6),       -- Commercial unit
    quantidade_comercial DECIMAL(15,4), -- TDec_1204: Commercial quantity
    valor_unitario_comercial DECIMAL(21,10), -- TDec_1110: Unit commercial value
    valor_total_bruto DECIMAL(15,2),    -- Gross total value
    ean_tributavel VARCHAR(14),         -- Taxable EAN
    unidade_tributavel VARCHAR(6),      -- Taxable unit
    quantidade_tributavel DECIMAL(15,4), -- Taxable quantity
    valor_unitario_tributavel DECIMAL(21,10), -- Unit taxable value
    valor_frete DECIMAL(15,2),          -- Freight value
    valor_seguro DECIMAL(15,2),         -- Insurance value
    valor_desconto DECIMAL(15,2),       -- Discount value
    valor_outras_despesas DECIMAL(15,2), -- Other expenses value
    -- ICMS tax information
    origem_produto CHAR(1),             -- Product origin (0-8)
    situacao_tributaria_icms VARCHAR(3), -- ICMS tax situation
    base_calculo_icms DECIMAL(15,2),    -- ICMS calculation base
    aliquota_icms DECIMAL(5,4),         -- ICMS rate
    valor_icms DECIMAL(15,2),           -- ICMS value
    -- IPI tax information
    situacao_tributaria_ipi VARCHAR(2), -- IPI tax situation
    base_calculo_ipi DECIMAL(15,2),     -- IPI calculation base
    aliquota_ipi DECIMAL(5,4),          -- IPI rate
    valor_ipi DECIMAL(15,2),            -- IPI value
    -- PIS tax information
    situacao_tributaria_pis VARCHAR(2), -- PIS tax situation
    base_calculo_pis DECIMAL(15,2),     -- PIS calculation base
    aliquota_pis DECIMAL(5,4),          -- PIS rate
    valor_pis DECIMAL(15,2),            -- PIS value
    -- COFINS tax information
    situacao_tributaria_cofins VARCHAR(2), -- COFINS tax situation
    base_calculo_cofins DECIMAL(15,2),  -- COFINS calculation base
    aliquota_cofins DECIMAL(5,4),       -- COFINS rate
    valor_cofins DECIMAL(15,2),         -- COFINS value
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_itens_nfe_main FOREIGN KEY (chave_nfe) REFERENCES nfe_main(chave_nfe),
    CONSTRAINT fk_itens_produto FOREIGN KEY (codigo_produto) REFERENCES dim_produtos(codigo_produto)
);

-- NFe events table (for tracking document lifecycle)
CREATE TABLE nfe_eventos (
    id BIGSERIAL PRIMARY KEY,
    chave_nfe VARCHAR(44),              -- NFe key
    tipo_evento VARCHAR(6),             -- Event type code
    sequencia_evento INT,               -- Event sequence
    data_evento TIMESTAMPTZ,            -- Event date/time
    descricao_evento VARCHAR(255),      -- Event description
    protocolo VARCHAR(15),              -- TProt: Protocol number
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_eventos_nfe FOREIGN KEY (chave_nfe) REFERENCES nfe_main(chave_nfe)
);