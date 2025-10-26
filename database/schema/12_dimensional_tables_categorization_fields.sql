-- Add categorization fields to dimensional tables
-- These fields support the enhanced AI categorization with confidence tracking

-- Add categorization fields to dim_produtos table
ALTER TABLE dim_produtos 
ADD COLUMN IF NOT EXISTS categorization_confidence DECIMAL(3,2) DEFAULT 0.80,
ADD COLUMN IF NOT EXISTS categorization_method VARCHAR(50) DEFAULT 'rule_based',
ADD COLUMN IF NOT EXISTS categorization_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add categorization fields to dim_servicos table  
ALTER TABLE dim_servicos
ADD COLUMN IF NOT EXISTS categorization_confidence DECIMAL(3,2) DEFAULT 0.80,
ADD COLUMN IF NOT EXISTS categorization_method VARCHAR(50) DEFAULT 'rule_based',
ADD COLUMN IF NOT EXISTS categorization_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create indexes for categorization fields
CREATE INDEX IF NOT EXISTS idx_dim_produtos_cat_confidence ON dim_produtos(categorization_confidence);
CREATE INDEX IF NOT EXISTS idx_dim_produtos_cat_method ON dim_produtos(categorization_method);
CREATE INDEX IF NOT EXISTS idx_dim_produtos_cat_timestamp ON dim_produtos(categorization_timestamp);

CREATE INDEX IF NOT EXISTS idx_dim_servicos_cat_confidence ON dim_servicos(categorization_confidence);
CREATE INDEX IF NOT EXISTS idx_dim_servicos_cat_method ON dim_servicos(categorization_method);
CREATE INDEX IF NOT EXISTS idx_dim_servicos_cat_timestamp ON dim_servicos(categorization_timestamp);

-- Create composite indexes for categorization analysis
CREATE INDEX IF NOT EXISTS idx_dim_produtos_cat_analysis ON dim_produtos(categoria, categorization_method, categorization_confidence);
CREATE INDEX IF NOT EXISTS idx_dim_servicos_cat_analysis ON dim_servicos(categoria, categorization_method, categorization_confidence);

-- View for categorization quality analysis
CREATE OR REPLACE VIEW categorization_quality_analysis AS
SELECT 
    'product' as item_type,
    categoria,
    subcategoria,
    categorization_method,
    COUNT(*) as item_count,
    AVG(categorization_confidence) as avg_confidence,
    MIN(categorization_confidence) as min_confidence,
    MAX(categorization_confidence) as max_confidence,
    COUNT(CASE WHEN categorization_confidence < 0.6 THEN 1 END) as low_confidence_count,
    COUNT(CASE WHEN categorization_confidence >= 0.8 THEN 1 END) as high_confidence_count
FROM dim_produtos
WHERE categoria IS NOT NULL
GROUP BY categoria, subcategoria, categorization_method

UNION ALL

SELECT 
    'service' as item_type,
    categoria,
    subcategoria,
    categorization_method,
    COUNT(*) as item_count,
    AVG(categorization_confidence) as avg_confidence,
    MIN(categorization_confidence) as min_confidence,
    MAX(categorization_confidence) as max_confidence,
    COUNT(CASE WHEN categorization_confidence < 0.6 THEN 1 END) as low_confidence_count,
    COUNT(CASE WHEN categorization_confidence >= 0.8 THEN 1 END) as high_confidence_count
FROM dim_servicos
WHERE categoria IS NOT NULL
GROUP BY categoria, subcategoria, categorization_method

ORDER BY item_type, categoria, subcategoria;

-- View for low confidence items that may need review
CREATE OR REPLACE VIEW low_confidence_items AS
SELECT 
    'product' as item_type,
    codigo_produto as item_code,
    descricao as item_description,
    categoria,
    subcategoria,
    categorization_confidence,
    categorization_method,
    categorization_timestamp,
    updated_at
FROM dim_produtos
WHERE categorization_confidence < 0.6
AND categoria IS NOT NULL

UNION ALL

SELECT 
    'service' as item_type,
    codigo_servico as item_code,
    descricao as item_description,
    categoria,
    subcategoria,
    categorization_confidence,
    categorization_method,
    categorization_timestamp,
    updated_at
FROM dim_servicos
WHERE categorization_confidence < 0.6
AND categoria IS NOT NULL

ORDER BY categorization_confidence ASC, categorization_timestamp DESC;

-- Function to get categorization method distribution
CREATE OR REPLACE FUNCTION get_categorization_method_stats()
RETURNS TABLE (
    item_type TEXT,
    categorization_method VARCHAR(50),
    item_count BIGINT,
    avg_confidence DECIMAL(5,3),
    percentage DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH method_stats AS (
        SELECT 
            'product'::TEXT as item_type,
            p.categorization_method,
            COUNT(*) as item_count,
            AVG(p.categorization_confidence) as avg_confidence
        FROM dim_produtos p
        WHERE p.categoria IS NOT NULL
        GROUP BY p.categorization_method
        
        UNION ALL
        
        SELECT 
            'service'::TEXT as item_type,
            s.categorization_method,
            COUNT(*) as item_count,
            AVG(s.categorization_confidence) as avg_confidence
        FROM dim_servicos s
        WHERE s.categoria IS NOT NULL
        GROUP BY s.categorization_method
    ),
    totals AS (
        SELECT 
            item_type,
            SUM(item_count) as total_items
        FROM method_stats
        GROUP BY item_type
    )
    SELECT 
        ms.item_type,
        ms.categorization_method,
        ms.item_count,
        ms.avg_confidence::DECIMAL(5,3),
        (ms.item_count * 100.0 / t.total_items)::DECIMAL(5,2) as percentage
    FROM method_stats ms
    JOIN totals t ON ms.item_type = t.item_type
    ORDER BY ms.item_type, ms.item_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to update categorization timestamp when category changes
CREATE OR REPLACE FUNCTION update_categorization_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    -- Update timestamp if category or subcategory changed
    IF (OLD.categoria IS DISTINCT FROM NEW.categoria) OR 
       (OLD.subcategoria IS DISTINCT FROM NEW.subcategoria) THEN
        NEW.categorization_timestamp = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to update categorization timestamp
CREATE TRIGGER trigger_update_produtos_categorization_timestamp
    BEFORE UPDATE ON dim_produtos
    FOR EACH ROW
    EXECUTE FUNCTION update_categorization_timestamp();

CREATE TRIGGER trigger_update_servicos_categorization_timestamp
    BEFORE UPDATE ON dim_servicos
    FOR EACH ROW
    EXECUTE FUNCTION update_categorization_timestamp();

-- Comments for documentation
COMMENT ON COLUMN dim_produtos.categorization_confidence IS 'Confidence score of the categorization (0.0 to 1.0)';
COMMENT ON COLUMN dim_produtos.categorization_method IS 'Method used for categorization (ai_enhanced, cached, rule_based, manual_override)';
COMMENT ON COLUMN dim_produtos.categorization_timestamp IS 'Timestamp when the item was last categorized';

COMMENT ON COLUMN dim_servicos.categorization_confidence IS 'Confidence score of the categorization (0.0 to 1.0)';
COMMENT ON COLUMN dim_servicos.categorization_method IS 'Method used for categorization (ai_enhanced, cached, rule_based, manual_override)';
COMMENT ON COLUMN dim_servicos.categorization_timestamp IS 'Timestamp when the item was last categorized';

COMMENT ON VIEW categorization_quality_analysis IS 'Analysis of categorization quality by category and method';
COMMENT ON VIEW low_confidence_items IS 'Items with low categorization confidence that may need manual review';
COMMENT ON FUNCTION get_categorization_method_stats() IS 'Statistics about categorization methods used';
COMMENT ON FUNCTION update_categorization_timestamp() IS 'Updates categorization timestamp when categories change';