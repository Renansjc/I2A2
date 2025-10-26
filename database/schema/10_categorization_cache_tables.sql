-- Categorization Cache Tables
-- Tables for caching AI categorization results to improve performance

-- Categorization cache table
CREATE TABLE IF NOT EXISTS categorization_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(32) UNIQUE NOT NULL,
    item_description VARCHAR(200) NOT NULL,
    item_ncm VARCHAR(8),
    item_cfop VARCHAR(4),
    item_type VARCHAR(20) DEFAULT 'product',
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) NOT NULL DEFAULT 0.80,
    categorization_method VARCHAR(50) DEFAULT 'ai_enhanced',
    usage_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes for categorization cache
CREATE INDEX IF NOT EXISTS idx_categorization_cache_key ON categorization_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_categorization_cache_expires ON categorization_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_categorization_cache_category ON categorization_cache(category);
CREATE INDEX IF NOT EXISTS idx_categorization_cache_description ON categorization_cache USING gin(to_tsvector('portuguese', item_description));
CREATE INDEX IF NOT EXISTS idx_categorization_cache_ncm ON categorization_cache(item_ncm);
CREATE INDEX IF NOT EXISTS idx_categorization_cache_type ON categorization_cache(item_type);

-- Function to increment cache usage count
CREATE OR REPLACE FUNCTION increment_cache_usage(cache_key_param VARCHAR(32))
RETURNS VOID AS $$
BEGIN
    UPDATE categorization_cache 
    SET usage_count = usage_count + 1,
        updated_at = NOW()
    WHERE cache_key = cache_key_param;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up expired cache entries (can be called by a scheduled job)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM categorization_cache 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Categorization performance metrics table
CREATE TABLE IF NOT EXISTS categorization_metrics (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    total_categorizations INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    ai_categorizations INTEGER DEFAULT 0,
    fallback_categorizations INTEGER DEFAULT 0,
    average_confidence DECIMAL(3,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for categorization metrics
CREATE INDEX IF NOT EXISTS idx_categorization_metrics_date ON categorization_metrics(date);
CREATE INDEX IF NOT EXISTS idx_categorization_metrics_created ON categorization_metrics(created_at);

-- Function to update daily categorization metrics
CREATE OR REPLACE FUNCTION update_categorization_metrics(
    cache_hits_param INTEGER DEFAULT 0,
    cache_misses_param INTEGER DEFAULT 0,
    ai_categorizations_param INTEGER DEFAULT 0,
    fallback_categorizations_param INTEGER DEFAULT 0,
    confidence_param DECIMAL(3,2) DEFAULT NULL,
    processing_time_param INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
BEGIN
    INSERT INTO categorization_metrics (
        date, 
        total_categorizations,
        cache_hits, 
        cache_misses, 
        ai_categorizations, 
        fallback_categorizations,
        average_confidence,
        processing_time_ms
    )
    VALUES (
        current_date,
        cache_hits_param + cache_misses_param + ai_categorizations_param + fallback_categorizations_param,
        cache_hits_param,
        cache_misses_param,
        ai_categorizations_param,
        fallback_categorizations_param,
        confidence_param,
        processing_time_param
    )
    ON CONFLICT (date) DO UPDATE SET
        total_categorizations = categorization_metrics.total_categorizations + EXCLUDED.total_categorizations,
        cache_hits = categorization_metrics.cache_hits + EXCLUDED.cache_hits,
        cache_misses = categorization_metrics.cache_misses + EXCLUDED.cache_misses,
        ai_categorizations = categorization_metrics.ai_categorizations + EXCLUDED.ai_categorizations,
        fallback_categorizations = categorization_metrics.fallback_categorizations + EXCLUDED.fallback_categorizations,
        average_confidence = CASE 
            WHEN EXCLUDED.average_confidence IS NOT NULL THEN 
                (COALESCE(categorization_metrics.average_confidence, 0) + EXCLUDED.average_confidence) / 2
            ELSE categorization_metrics.average_confidence
        END,
        processing_time_ms = CASE 
            WHEN EXCLUDED.processing_time_ms IS NOT NULL THEN 
                (COALESCE(categorization_metrics.processing_time_ms, 0) + EXCLUDED.processing_time_ms) / 2
            ELSE categorization_metrics.processing_time_ms
        END;
END;
$$ LANGUAGE plpgsql;

-- Add unique constraint on date for metrics
ALTER TABLE categorization_metrics ADD CONSTRAINT unique_metrics_date UNIQUE (date);

-- Comments for documentation
COMMENT ON TABLE categorization_cache IS 'Cache table for AI categorization results to improve performance and reduce API calls';
COMMENT ON COLUMN categorization_cache.cache_key IS 'MD5 hash of normalized item data for unique identification';
COMMENT ON COLUMN categorization_cache.usage_count IS 'Number of times this cache entry has been used';
COMMENT ON COLUMN categorization_cache.expires_at IS 'Expiration timestamp for cache entry';

COMMENT ON TABLE categorization_metrics IS 'Daily metrics for categorization performance monitoring';
COMMENT ON FUNCTION increment_cache_usage(VARCHAR) IS 'Increments usage count for a cache entry';
COMMENT ON FUNCTION cleanup_expired_cache() IS 'Removes expired cache entries and returns count of deleted rows';
COMMENT ON FUNCTION update_categorization_metrics(INTEGER, INTEGER, INTEGER, INTEGER, DECIMAL, INTEGER) IS 'Updates daily categorization performance metrics';