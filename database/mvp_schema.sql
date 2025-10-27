-- Enhanced MVP Sistema Simplificado de Análise Fiscal - Database Schema
-- Schema melhorado com campos detalhados para análise fiscal e IA
-- Baseado na análise do XML de exemplo

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main fiscal documents table (enhanced)
CREATE TABLE fiscal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_path TEXT,
    status VARCHAR(50) DEFAULT 'uploaded' CHECK (
        status IN ('uploaded', 'processing', 'completed', 'error')
    ),
    processing_progress INTEGER DEFAULT 0 CHECK (processing_progress >= 0 AND processing_progress <= 100),
    
    -- Dados básicos da nota
    numero_nota VARCHAR(20),
    serie VARCHAR(10),
    chave_acesso VARCHAR(44) UNIQUE NOT NULL, -- Chave única para upsert
    data_emissao TIMESTAMP,
    data_saida TIMESTAMP,
    dh_evento TIMESTAMP, -- Data e hora do evento para controle de versão
    dh_emi TIMESTAMP,    -- Data e hora de emissão para controle de versão
    natureza_operacao TEXT,
    
    -- Valores principais da nota
    valor_produtos DECIMAL(15,2),           -- vProd
    valor_frete DECIMAL(15,2),              -- vFrete  
    valor_seguro DECIMAL(15,2),             -- vSeg
    valor_desconto DECIMAL(15,2),           -- vDesc
    valor_outros DECIMAL(15,2),             -- vOutro
    valor_total DECIMAL(15,2),              -- vNF (valor final da nota)
    
    -- Impostos totais da nota
    icms_base_calculo DECIMAL(15,2),        -- vBC
    icms_valor DECIMAL(15,2),               -- vICMS
    icms_st_base_calculo DECIMAL(15,2),     -- vBCST
    icms_st_valor DECIMAL(15,2),            -- vST
    ipi_valor DECIMAL(15,2),                -- vIPI
    pis_valor DECIMAL(15,2),                -- vPIS
    cofins_valor DECIMAL(15,2),             -- vCOFINS
    total_tributos DECIMAL(15,2),           -- vTotTrib
    
    -- Informações de transporte
    modalidade_frete INTEGER,               -- modFrete (0=Emitente, 1=Destinatário)
    transportadora VARCHAR(255),            -- xNome da transportadora
    peso_liquido DECIMAL(10,3),             -- pesoL
    peso_bruto DECIMAL(10,3),               -- pesoB
    quantidade_volumes INTEGER,             -- qVol
    
    -- Informações de pagamento
    forma_pagamento INTEGER,                -- tPag (01=Dinheiro, 02=Cheque, etc.)
    valor_pagamento DECIMAL(15,2),          -- vPag
    data_vencimento DATE,                   -- dVenc
    
    -- Metadados para IA
    uf_origem VARCHAR(2),                   -- UF do emitente
    uf_destino VARCHAR(2),                  -- UF do destinatário
    tipo_operacao VARCHAR(20),              -- Venda, Compra, Transferência, etc.
    consumidor_final BOOLEAN,               -- indFinal
    presenca_comprador INTEGER,             -- indPres (0=Não se aplica, 1=Presencial, etc.)
    
    uploaded_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced extracted data table (emitente/destinatário detalhados)
CREATE TABLE extracted_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    
    -- Emitente detalhado
    emitente_razao_social VARCHAR(255),
    emitente_nome_fantasia VARCHAR(255),
    emitente_cnpj VARCHAR(14),
    emitente_ie VARCHAR(20),
    emitente_crt INTEGER,                   -- Código de Regime Tributário
    emitente_logradouro VARCHAR(255),
    emitente_numero VARCHAR(10),
    emitente_complemento VARCHAR(100),
    emitente_bairro VARCHAR(100),
    emitente_municipio VARCHAR(100),
    emitente_uf VARCHAR(2),
    emitente_cep VARCHAR(8),
    emitente_telefone VARCHAR(20),
    
    -- Destinatário detalhado
    destinatario_nome VARCHAR(255),
    destinatario_cnpj VARCHAR(14),
    destinatario_cpf VARCHAR(11),
    destinatario_ie VARCHAR(20),
    destinatario_logradouro VARCHAR(255),
    destinatario_numero VARCHAR(10),
    destinatario_complemento VARCHAR(100),
    destinatario_bairro VARCHAR(100),
    destinatario_municipio VARCHAR(100),
    destinatario_uf VARCHAR(2),
    destinatario_cep VARCHAR(8),
    destinatario_telefone VARCHAR(20),
    destinatario_email VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enhanced document items table (produtos/serviços detalhados)
CREATE TABLE document_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    
    -- Identificação do produto
    codigo_produto VARCHAR(50),             -- cProd
    codigo_ean VARCHAR(14),                 -- cEAN
    descricao TEXT NOT NULL,                -- xProd
    ncm VARCHAR(8),                         -- NCM
    cfop VARCHAR(4),                        -- CFOP
    
    -- Quantidades e unidades
    unidade_comercial VARCHAR(10),          -- uCom
    quantidade_comercial DECIMAL(10,4),     -- qCom
    valor_unitario_comercial DECIMAL(15,6), -- vUnCom
    unidade_tributavel VARCHAR(10),         -- uTrib
    quantidade_tributavel DECIMAL(10,4),    -- qTrib
    valor_unitario_tributavel DECIMAL(15,6), -- vUnTrib
    
    -- Valores do item
    valor_produto DECIMAL(15,2),            -- vProd (valor total do produto)
    valor_frete DECIMAL(15,2),              -- vFrete
    valor_seguro DECIMAL(15,2),             -- vSeg
    valor_desconto DECIMAL(15,2),           -- vDesc
    valor_outros DECIMAL(15,2),             -- vOutro
    
    -- Impostos do item
    icms_origem INTEGER,                    -- orig (0=Nacional, 1=Estrangeira)
    icms_cst VARCHAR(3),                    -- CST
    icms_base_calculo DECIMAL(15,2),        -- vBC
    icms_aliquota DECIMAL(5,2),             -- pICMS
    icms_valor DECIMAL(15,2),               -- vICMS
    
    ipi_cst VARCHAR(2),                     -- CST do IPI
    ipi_valor DECIMAL(15,2),                -- vIPI
    
    pis_cst VARCHAR(2),                     -- CST do PIS
    pis_base_calculo DECIMAL(15,2),         -- vBC do PIS
    pis_aliquota DECIMAL(5,4),              -- pPIS
    pis_valor DECIMAL(15,2),                -- vPIS
    
    cofins_cst VARCHAR(2),                  -- CST do COFINS
    cofins_base_calculo DECIMAL(15,2),      -- vBC do COFINS
    cofins_aliquota DECIMAL(5,4),           -- pCOFINS
    cofins_valor DECIMAL(15,2),             -- vCOFINS
    
    total_tributos_item DECIMAL(15,2),      -- vTotTrib do item
    
    -- Campos para IA
    categoria VARCHAR(100),
    categoria_confianca DECIMAL(3,2),
    subcategoria VARCHAR(100),
    marca VARCHAR(100),                     -- Extraída da descrição pela IA
    modelo VARCHAR(100),                    -- Extraído da descrição pela IA
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Executive reports (unchanged)
CREATE TABLE executive_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    period_start DATE,
    period_end DATE,
    generated_at TIMESTAMP DEFAULT NOW(),
    report_type VARCHAR(50) DEFAULT 'executive_summary',
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela para análises de fornecedores (nova)
CREATE TABLE supplier_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    
    -- Classificação do fornecedor
    tipo_fornecedor VARCHAR(50),            -- Distribuidora, Indústria, Varejo, etc.
    categoria_negocio VARCHAR(100),         -- Tecnologia, Alimentação, etc.
    porte_empresa VARCHAR(20),              -- Pequeno, Médio, Grande
    confianca_classificacao DECIMAL(3,2),
    
    -- Métricas de relacionamento
    frequencia_compras INTEGER DEFAULT 1,
    valor_medio_transacao DECIMAL(15,2),
    prazo_medio_pagamento INTEGER,
    
    -- Análise de risco
    score_risco DECIMAL(3,2),               -- 0.0 a 1.0
    fatores_risco TEXT[],                   -- Array de fatores identificados
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabela para insights de IA (nova)
CREATE TABLE ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES fiscal_documents(id) ON DELETE CASCADE,
    
    -- Tipo de insight
    tipo_insight VARCHAR(50),               -- 'alerta', 'oportunidade', 'recomendacao'
    categoria VARCHAR(100),                 -- 'fiscal', 'financeiro', 'operacional'
    titulo VARCHAR(255),
    descricao TEXT,
    
    -- Metadados
    confianca DECIMAL(3,2),
    prioridade INTEGER CHECK (prioridade BETWEEN 1 AND 5),
    acao_sugerida TEXT,
    
    -- Dados para tracking
    visualizado BOOLEAN DEFAULT FALSE,
    acao_tomada BOOLEAN DEFAULT FALSE,
    feedback_usuario INTEGER,              -- 1-5 stars
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_fiscal_documents_status ON fiscal_documents(status);
CREATE INDEX idx_fiscal_documents_uploaded_at ON fiscal_documents(uploaded_at);
CREATE INDEX idx_fiscal_documents_data_emissao ON fiscal_documents(data_emissao);
CREATE INDEX idx_fiscal_documents_valor_total ON fiscal_documents(valor_total);
CREATE INDEX idx_fiscal_documents_uf_origem ON fiscal_documents(uf_origem);
CREATE INDEX idx_fiscal_documents_uf_destino ON fiscal_documents(uf_destino);
CREATE UNIQUE INDEX idx_fiscal_documents_chave_acesso ON fiscal_documents(chave_acesso);
CREATE INDEX idx_fiscal_documents_dh_evento ON fiscal_documents(dh_evento);
CREATE INDEX idx_fiscal_documents_dh_emi ON fiscal_documents(dh_emi);

CREATE INDEX idx_extracted_data_document_id ON extracted_data(document_id);
CREATE INDEX idx_extracted_data_emitente_cnpj ON extracted_data(emitente_cnpj);
CREATE INDEX idx_extracted_data_emitente_uf ON extracted_data(emitente_uf);
CREATE INDEX idx_extracted_data_destinatario_uf ON extracted_data(destinatario_uf);

CREATE INDEX idx_document_items_document_id ON document_items(document_id);
CREATE INDEX idx_document_items_categoria ON document_items(categoria);
CREATE INDEX idx_document_items_ncm ON document_items(ncm);
CREATE INDEX idx_document_items_cfop ON document_items(cfop);
CREATE INDEX idx_document_items_valor_produto ON document_items(valor_produto);

CREATE INDEX idx_supplier_analysis_document_id ON supplier_analysis(document_id);
CREATE INDEX idx_supplier_analysis_tipo_fornecedor ON supplier_analysis(tipo_fornecedor);
CREATE INDEX idx_supplier_analysis_score_risco ON supplier_analysis(score_risco);

CREATE INDEX idx_ai_insights_document_id ON ai_insights(document_id);
CREATE INDEX idx_ai_insights_tipo_insight ON ai_insights(tipo_insight);
CREATE INDEX idx_ai_insights_categoria ON ai_insights(categoria);
CREATE INDEX idx_ai_insights_prioridade ON ai_insights(prioridade);
CREATE INDEX idx_ai_insights_visualizado ON ai_insights(visualizado);

-- Views para análises comuns
CREATE VIEW vw_dashboard_metrics AS
SELECT 
    COUNT(*) as total_documentos,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as documentos_processados,
    SUM(valor_total) as valor_total_geral,
    SUM(total_tributos) as total_tributos_geral,
    AVG(valor_total) as valor_medio_documento,
    COUNT(CASE WHEN DATE(data_emissao) = CURRENT_DATE THEN 1 END) as documentos_hoje
FROM fiscal_documents
WHERE status != 'error';

CREATE VIEW vw_top_fornecedores AS
SELECT 
    ed.emitente_razao_social,
    ed.emitente_cnpj,
    ed.emitente_uf,
    COUNT(*) as total_documentos,
    SUM(fd.valor_total) as valor_total,
    AVG(fd.valor_total) as valor_medio,
    sa.tipo_fornecedor,
    sa.categoria_negocio,
    AVG(sa.score_risco) as risco_medio
FROM extracted_data ed
JOIN fiscal_documents fd ON ed.document_id = fd.id
LEFT JOIN supplier_analysis sa ON sa.document_id = fd.id
WHERE fd.status = 'completed'
GROUP BY ed.emitente_razao_social, ed.emitente_cnpj, ed.emitente_uf, sa.tipo_fornecedor, sa.categoria_negocio
ORDER BY valor_total DESC;

CREATE VIEW vw_categorias_produtos AS
SELECT 
    categoria,
    subcategoria,
    COUNT(*) as total_itens,
    SUM(valor_produto) as valor_total,
    AVG(valor_produto) as valor_medio,
    SUM(quantidade_comercial) as quantidade_total,
    COUNT(DISTINCT document_id) as documentos_distintos
FROM document_items
WHERE categoria IS NOT NULL
GROUP BY categoria, subcategoria
ORDER BY valor_total DESC;

CREATE VIEW vw_insights_pendentes AS
SELECT 
    ai.tipo_insight,
    ai.categoria,
    ai.titulo,
    ai.descricao,
    ai.prioridade,
    ai.confianca,
    fd.numero_nota,
    ed.emitente_razao_social,
    ai.created_at
FROM ai_insights ai
JOIN fiscal_documents fd ON ai.document_id = fd.id
JOIN extracted_data ed ON ed.document_id = fd.id
WHERE ai.visualizado = FALSE
ORDER BY ai.prioridade DESC, ai.confianca DESC, ai.created_at DESC;