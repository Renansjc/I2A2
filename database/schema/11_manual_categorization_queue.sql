-- Manual Categorization Queue Table
-- Table for managing manual review of low-confidence categorizations

-- Manual categorization queue table
CREATE TABLE IF NOT EXISTS manual_categorization_queue (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(20) NOT NULL CHECK (item_type IN ('product', 'service')),
    item_code VARCHAR(60) NOT NULL,
    item_description TEXT NOT NULL,
    suggested_category VARCHAR(100),
    suggested_subcategory VARCHAR(100),
    confidence_score DECIMAL(3,2) DEFAULT 0.00,
    categorization_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending_review' CHECK (status IN ('pending_review', 'in_review', 'completed', 'rejected')),
    final_category VARCHAR(100),
    final_subcategory VARCHAR(100),
    reviewer_id VARCHAR(50),
    reviewer_notes TEXT,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5), -- 1 = low, 5 = high
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for manual categorization queue
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_status ON manual_categorization_queue(status);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_item_type ON manual_categorization_queue(item_type);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_item_code ON manual_categorization_queue(item_code);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_confidence ON manual_categorization_queue(confidence_score);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_priority ON manual_categorization_queue(priority DESC);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_created ON manual_categorization_queue(created_at);
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_reviewer ON manual_categorization_queue(reviewer_id);

-- Composite index for efficient querying
CREATE INDEX IF NOT EXISTS idx_manual_cat_queue_status_priority ON manual_categorization_queue(status, priority DESC, created_at);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_manual_cat_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_manual_cat_queue_updated_at
    BEFORE UPDATE ON manual_categorization_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_manual_cat_queue_updated_at();

-- Function to get pending review statistics
CREATE OR REPLACE FUNCTION get_manual_review_stats()
RETURNS TABLE (
    total_pending INTEGER,
    high_priority_pending INTEGER,
    products_pending INTEGER,
    services_pending INTEGER,
    avg_confidence DECIMAL(3,2),
    oldest_pending_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_pending,
        COUNT(CASE WHEN priority >= 4 THEN 1 END)::INTEGER as high_priority_pending,
        COUNT(CASE WHEN item_type = 'product' THEN 1 END)::INTEGER as products_pending,
        COUNT(CASE WHEN item_type = 'service' THEN 1 END)::INTEGER as services_pending,
        AVG(confidence_score)::DECIMAL(3,2) as avg_confidence,
        COALESCE(EXTRACT(DAYS FROM NOW() - MIN(created_at))::INTEGER, 0) as oldest_pending_days
    FROM manual_categorization_queue
    WHERE status = 'pending_review';
END;
$$ LANGUAGE plpgsql;

-- Function to assign reviewer to pending items
CREATE OR REPLACE FUNCTION assign_reviewer_to_items(
    reviewer_id_param VARCHAR(50),
    max_items INTEGER DEFAULT 10,
    item_type_filter VARCHAR(20) DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    assigned_count INTEGER;
BEGIN
    UPDATE manual_categorization_queue
    SET status = 'in_review',
        reviewer_id = reviewer_id_param,
        updated_at = NOW()
    WHERE id IN (
        SELECT id 
        FROM manual_categorization_queue 
        WHERE status = 'pending_review'
        AND (item_type_filter IS NULL OR item_type = item_type_filter)
        ORDER BY priority DESC, created_at ASC
        LIMIT max_items
    );
    
    GET DIAGNOSTICS assigned_count = ROW_COUNT;
    RETURN assigned_count;
END;
$$ LANGUAGE plpgsql;

-- Function to complete review
CREATE OR REPLACE FUNCTION complete_manual_review(
    queue_id INTEGER,
    final_category_param VARCHAR(100),
    final_subcategory_param VARCHAR(100),
    reviewer_notes_param TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE manual_categorization_queue
    SET status = 'completed',
        final_category = final_category_param,
        final_subcategory = final_subcategory_param,
        reviewer_notes = reviewer_notes_param,
        reviewed_at = NOW(),
        updated_at = NOW()
    WHERE id = queue_id
    AND status = 'in_review';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to reject review (send back to pending)
CREATE OR REPLACE FUNCTION reject_manual_review(
    queue_id INTEGER,
    reviewer_notes_param TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE manual_categorization_queue
    SET status = 'rejected',
        reviewer_notes = reviewer_notes_param,
        reviewed_at = NOW(),
        updated_at = NOW()
    WHERE id = queue_id
    AND status = 'in_review';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- View for reviewer dashboard
CREATE OR REPLACE VIEW manual_review_dashboard AS
SELECT 
    mcq.*,
    CASE 
        WHEN mcq.item_type = 'product' THEN dp.descricao
        WHEN mcq.item_type = 'service' THEN ds.descricao
    END as current_description,
    CASE 
        WHEN mcq.item_type = 'product' THEN dp.categoria
        WHEN mcq.item_type = 'service' THEN ds.categoria
    END as current_category,
    CASE 
        WHEN mcq.item_type = 'product' THEN dp.subcategoria
        WHEN mcq.item_type = 'service' THEN ds.subcategoria
    END as current_subcategory,
    EXTRACT(DAYS FROM NOW() - mcq.created_at) as days_pending
FROM manual_categorization_queue mcq
LEFT JOIN dim_produtos dp ON mcq.item_type = 'product' AND mcq.item_code = dp.codigo_produto
LEFT JOIN dim_servicos ds ON mcq.item_type = 'service' AND mcq.item_code = ds.codigo_servico
WHERE mcq.status IN ('pending_review', 'in_review')
ORDER BY mcq.priority DESC, mcq.created_at ASC;

-- Comments for documentation
COMMENT ON TABLE manual_categorization_queue IS 'Queue for manual review of low-confidence AI categorizations';
COMMENT ON COLUMN manual_categorization_queue.priority IS 'Priority level: 1=low, 2=normal, 3=medium, 4=high, 5=critical';
COMMENT ON COLUMN manual_categorization_queue.confidence_score IS 'Original AI confidence score that triggered manual review';
COMMENT ON COLUMN manual_categorization_queue.status IS 'Review status: pending_review, in_review, completed, rejected';

COMMENT ON FUNCTION get_manual_review_stats() IS 'Returns statistics about pending manual reviews';
COMMENT ON FUNCTION assign_reviewer_to_items(VARCHAR, INTEGER, VARCHAR) IS 'Assigns pending items to a reviewer';
COMMENT ON FUNCTION complete_manual_review(INTEGER, VARCHAR, VARCHAR, TEXT) IS 'Marks a manual review as completed';
COMMENT ON FUNCTION reject_manual_review(INTEGER, TEXT) IS 'Rejects a manual review and sends back to pending';

COMMENT ON VIEW manual_review_dashboard IS 'Dashboard view for manual categorization reviewers';