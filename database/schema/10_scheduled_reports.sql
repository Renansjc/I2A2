-- Scheduled Reports Table for MVP
-- Adds scheduling functionality for automated report generation

-- Scheduled reports table
CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('monthly', 'quarterly', 'custom', 'weekly')),
    schedule_expression TEXT NOT NULL, -- "monthly first monday", "weekly friday", etc.
    natural_language_input TEXT NOT NULL, -- Original user input
    report_title TEXT,
    report_parameters JSONB DEFAULT '{}', -- Additional parameters for report generation
    is_active BOOLEAN DEFAULT true,
    last_execution TIMESTAMP WITH TIME ZONE,
    next_execution TIMESTAMP WITH TIME ZONE,
    execution_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE scheduled_reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies for scheduled_reports
CREATE POLICY "Users can manage their own scheduled reports" 
ON scheduled_reports FOR ALL 
TO authenticated 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- Service role policy for automated execution
CREATE POLICY "Service role full access to scheduled reports" 
ON scheduled_reports FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Index for efficient querying
CREATE INDEX idx_scheduled_reports_user_id ON scheduled_reports(user_id);
CREATE INDEX idx_scheduled_reports_next_execution ON scheduled_reports(next_execution) WHERE is_active = true;
CREATE INDEX idx_scheduled_reports_active ON scheduled_reports(is_active, next_execution);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_scheduled_reports_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scheduled_reports_updated_at
    BEFORE UPDATE ON scheduled_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_scheduled_reports_updated_at();