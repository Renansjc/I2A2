-- Analytical views for executive queries

-- Unified document view for executive queries
CREATE VIEW vw_documentos_fiscais AS
SELECT 
    'NFE' as tipo_documento,
    chave_nfe as identificador,
    data_emissao,
    valor_total_nf as valor_total,
    NULL as valor_servicos,
    valor_total_produtos,
    NULL as valor_issqn,
    valor_icms,
    valor_total_ipi as valor_ipi,
    valor_pis,
    valor_cofins
FROM nfe_main
UNION ALL
SELECT 
    'NFSE' as tipo_documento,
    id_nfse as identificador,
    data_emissao,
    valor_total_servicos as valor_total,
    valor_total_servicos,
    NULL as valor_total_produtos,
    valor_issqn,
    NULL as valor_icms,
    NULL as valor_ipi,
    NULL as valor_pis,
    NULL as valor_cofins
FROM nfse_main;

-- Suppliers summary view
CREATE VIEW vw_fornecedores_resumo AS
SELECT 
    e.cnpj,
    e.razao_social,
    e.uf,
    COUNT(n.chave_nfe) as total_notas,
    SUM(n.valor_total_nf) as valor_total,
    AVG(n.valor_total_nf) as valor_medio,
    MIN(n.data_emissao) as primeira_compra,
    MAX(n.data_emissao) as ultima_compra
FROM dim_emitente e
LEFT JOIN nfe_main n ON e.cnpj = SUBSTRING(n.chave_nfe, 7, 14)
GROUP BY e.cnpj, e.razao_social, e.uf;

-- Most purchased products view
CREATE VIEW vw_produtos_mais_comprados AS
SELECT 
    p.codigo_produto,
    p.descricao,
    p.categoria,
    p.ncm,
    COUNT(i.id) as frequencia_compra,
    SUM(i.quantidade_comercial) as quantidade_total,
    SUM(i.valor_total_bruto) as valor_total,
    AVG(i.valor_unitario_comercial) as preco_medio
FROM dim_produtos p
JOIN fact_itens_nfe i ON p.codigo_produto = i.codigo_produto
GROUP BY p.codigo_produto, p.descricao, p.categoria, p.ncm
ORDER BY valor_total DESC;

-- Complete suppliers view (NFE + NFSE)
CREATE VIEW vw_fornecedores_completo AS
SELECT 
    e.cnpj,
    e.razao_social,
    e.uf,
    COUNT(CASE WHEN n.chave_nfe IS NOT NULL THEN 1 END) as total_nfe,
    COUNT(CASE WHEN ns.id_nfse IS NOT NULL THEN 1 END) as total_nfse,
    SUM(COALESCE(n.valor_total_nf, 0)) as valor_total_produtos,
    SUM(COALESCE(ns.valor_total_servicos, 0)) as valor_total_servicos,
    SUM(COALESCE(n.valor_total_nf, 0) + COALESCE(ns.valor_total_servicos, 0)) as valor_total_geral,
    MIN(COALESCE(n.data_emissao, ns.data_emissao)) as primeira_transacao,
    MAX(COALESCE(n.data_emissao, ns.data_emissao)) as ultima_transacao
FROM dim_emitente e
LEFT JOIN nfe_main n ON e.cnpj = SUBSTRING(n.chave_nfe, 7, 14)
LEFT JOIN nfse_main ns ON e.cnpj = SUBSTRING(ns.id_nfse, 9, 14)
GROUP BY e.cnpj, e.razao_social, e.uf;

-- Tax analysis view
CREATE VIEW vw_analise_tributaria AS
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFE' as tipo_documento,
    SUM(valor_total_nf) as valor_total,
    SUM(valor_icms) as icms,
    SUM(valor_total_ipi) as ipi,
    SUM(valor_pis) as pis,
    SUM(valor_cofins) as cofins,
    NULL as issqn,
    COUNT(*) as quantidade_documentos
FROM nfe_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM')
UNION ALL
SELECT 
    TO_CHAR(data_emissao, 'YYYY-MM') as periodo,
    'NFSE' as tipo_documento,
    SUM(valor_total_servicos) as valor_total,
    NULL as icms,
    NULL as ipi,
    NULL as pis,
    NULL as cofins,
    SUM(valor_issqn) as issqn,
    COUNT(*) as quantidade_documentos
FROM nfse_main
GROUP BY TO_CHAR(data_emissao, 'YYYY-MM');