-- Row Level Security (RLS) policies for Supabase

-- Enable RLS on all tables
ALTER TABLE dim_tipo_documento ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_emitente ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_destinatario ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_servicos ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfe_main ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_itens_nfe ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfe_eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfse_main ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_servicos_nfse ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users (C-level executives)
-- Allow full access to authenticated users for all tables

-- Dimension tables policies
CREATE POLICY "Allow authenticated users full access to dim_tipo_documento" 
ON dim_tipo_documento FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to dim_emitente" 
ON dim_emitente FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to dim_destinatario" 
ON dim_destinatario FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to dim_produtos" 
ON dim_produtos FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to dim_servicos" 
ON dim_servicos FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- NFE tables policies
CREATE POLICY "Allow authenticated users full access to nfe_main" 
ON nfe_main FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to fact_itens_nfe" 
ON fact_itens_nfe FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to nfe_eventos" 
ON nfe_eventos FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- NFSE tables policies
CREATE POLICY "Allow authenticated users full access to nfse_main" 
ON nfse_main FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow authenticated users full access to fact_servicos_nfse" 
ON fact_servicos_nfse FOR ALL 
TO authenticated 
USING (true) 
WITH CHECK (true);

-- Service role policies (for backend agents)
-- Allow service role full access for automated processing

CREATE POLICY "Allow service role full access to dim_emitente" 
ON dim_emitente FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to dim_destinatario" 
ON dim_destinatario FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to dim_produtos" 
ON dim_produtos FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to dim_servicos" 
ON dim_servicos FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to nfe_main" 
ON nfe_main FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to fact_itens_nfe" 
ON fact_itens_nfe FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to nfe_eventos" 
ON nfe_eventos FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to nfse_main" 
ON nfse_main FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Allow service role full access to fact_servicos_nfse" 
ON fact_servicos_nfse FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);