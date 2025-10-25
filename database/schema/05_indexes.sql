-- Indexes for performance optimization

-- NFE indexes
CREATE INDEX idx_nfe_data_emissao ON nfe_main(data_emissao);
CREATE INDEX idx_nfe_emitente_cnpj ON nfe_main USING btree (SUBSTRING(chave_nfe, 7, 14));
CREATE INDEX idx_nfe_valor_total ON nfe_main(valor_total_nf);
CREATE INDEX idx_nfe_uf_emitente ON nfe_main(uf_emitente);

-- NFSE indexes
CREATE INDEX idx_nfse_data_emissao ON nfse_main(data_emissao);
CREATE INDEX idx_nfse_emitente_cnpj ON nfse_main USING btree (SUBSTRING(id_nfse, 9, 14));
CREATE INDEX idx_nfse_valor_total ON nfse_main(valor_total_servicos);

-- Fact table indexes
CREATE INDEX idx_itens_produto ON fact_itens_nfe(codigo_produto);
CREATE INDEX idx_itens_nfe ON fact_itens_nfe(chave_nfe);
CREATE INDEX idx_itens_valor_total ON fact_itens_nfe(valor_total_bruto);

CREATE INDEX idx_servicos_nfse ON fact_servicos_nfse(id_nfse);
CREATE INDEX idx_servicos_codigo ON fact_servicos_nfse(codigo_servico);
CREATE INDEX idx_servicos_valor_total ON fact_servicos_nfse(valor_total);

-- Dimension table indexes
CREATE INDEX idx_emitente_uf ON dim_emitente(uf);
CREATE INDEX idx_emitente_razao_social ON dim_emitente(razao_social);

CREATE INDEX idx_produtos_categoria ON dim_produtos(categoria);
CREATE INDEX idx_produtos_ncm ON dim_produtos(ncm);
CREATE INDEX idx_produtos_descricao ON dim_produtos USING gin(to_tsvector('portuguese', descricao));

CREATE INDEX idx_servicos_categoria ON dim_servicos(categoria);
CREATE INDEX idx_servicos_cnae ON dim_servicos(codigo_cnae);
CREATE INDEX idx_servicos_descricao ON dim_servicos USING gin(to_tsvector('portuguese', descricao));

-- Composite indexes for common queries
CREATE INDEX idx_nfe_emitente_data ON nfe_main USING btree (SUBSTRING(chave_nfe, 7, 14), data_emissao);
CREATE INDEX idx_nfse_emitente_data ON nfse_main USING btree (SUBSTRING(id_nfse, 9, 14), data_emissao);