-- Script para adicionar colunas de controle de versão para upsert
-- Execute este script no Supabase SQL Editor para atualizar o schema existente

-- 1. Adicionar as novas colunas de controle de versão
ALTER TABLE fiscal_documents 
ADD COLUMN IF NOT EXISTS dh_evento TIMESTAMP,
ADD COLUMN IF NOT EXISTS dh_emi TIMESTAMP;

-- 2. Adicionar constraint de chave única na chave_acesso (se não existir)
DO $$ 
BEGIN
    -- Verificar se a constraint já existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fiscal_documents_chave_acesso_key' 
        AND table_name = 'fiscal_documents'
    ) THEN
        -- Remover duplicatas primeiro (manter o mais recente por created_at)
        DELETE FROM fiscal_documents 
        WHERE id NOT IN (
            SELECT DISTINCT ON (chave_acesso) id 
            FROM fiscal_documents 
            ORDER BY chave_acesso, created_at DESC
        );
        
        -- Adicionar constraint de chave única
        ALTER TABLE fiscal_documents 
        ADD CONSTRAINT fiscal_documents_chave_acesso_key UNIQUE (chave_acesso);
    END IF;
END $$;

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_chave_acesso ON fiscal_documents(chave_acesso);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_dh_evento ON fiscal_documents(dh_evento);
CREATE INDEX IF NOT EXISTS idx_fiscal_documents_dh_emi ON fiscal_documents(dh_emi);

-- 4. Atualizar registros existentes com dh_emi baseado em data_emissao
UPDATE fiscal_documents 
SET dh_emi = data_emissao 
WHERE dh_emi IS NULL AND data_emissao IS NOT NULL;

-- 5. Comentários para documentação
COMMENT ON COLUMN fiscal_documents.dh_evento IS 'Data e hora do evento para controle de versão (formato AAAA-MM-DDThh:mm:ssTZD)';
COMMENT ON COLUMN fiscal_documents.dh_emi IS 'Data e hora de emissão para controle de versão (formato AAAA-MM-DDThh:mm:ssTZD)';
COMMENT ON CONSTRAINT fiscal_documents_chave_acesso_key ON fiscal_documents IS 'Chave de acesso única para implementar upsert baseado em versão mais atual';

-- Verificar se as alterações foram aplicadas
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'fiscal_documents' 
AND column_name IN ('dh_evento', 'dh_emi', 'chave_acesso')
ORDER BY column_name;