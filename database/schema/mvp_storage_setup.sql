-- MVP Supabase Storage Setup
-- Configure storage bucket and policies for XML file uploads

-- Create storage bucket for XML files (run this in Supabase SQL Editor)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'invoice-xmls',
    'invoice-xmls',
    true,  -- Public bucket for simplified MVP
    10485760,  -- 10MB limit
    ARRAY['application/xml', 'text/xml']
);

-- Create simplified storage policies (no RLS for MVP)
-- Allow public access for MVP simplicity

-- Policy for uploading files
CREATE POLICY "MVP Upload XML files" ON storage.objects
FOR INSERT WITH CHECK (
    bucket_id = 'invoice-xmls' 
    AND (storage.extension(name) = 'xml' OR storage.extension(name) = 'XML')
);

-- Policy for reading files
CREATE POLICY "MVP Read XML files" ON storage.objects
FOR SELECT USING (bucket_id = 'invoice-xmls');

-- Policy for updating files
CREATE POLICY "MVP Update XML files" ON storage.objects
FOR UPDATE USING (bucket_id = 'invoice-xmls');

-- Policy for deleting files
CREATE POLICY "MVP Delete XML files" ON storage.objects
FOR DELETE USING (bucket_id = 'invoice-xmls');

-- Enable RLS on storage.objects (required by Supabase)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Create function to validate XML file content
CREATE OR REPLACE FUNCTION validate_xml_file()
RETURNS TRIGGER AS $$
BEGIN
    -- Check file extension
    IF NOT (NEW.name ILIKE '%.xml' OR NEW.name ILIKE '%.XML') THEN
        RAISE EXCEPTION 'Only XML files are allowed';
    END IF;
    
    -- Check file size (10MB limit)
    IF NEW.metadata->>'size' IS NOT NULL AND (NEW.metadata->>'size')::bigint > 10485760 THEN
        RAISE EXCEPTION 'File size exceeds 10MB limit';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for file validation
CREATE TRIGGER validate_xml_upload
    BEFORE INSERT OR UPDATE ON storage.objects
    FOR EACH ROW
    WHEN (NEW.bucket_id = 'invoice-xmls')
    EXECUTE FUNCTION validate_xml_file();

-- Create function to clean up old files (optional for MVP)
CREATE OR REPLACE FUNCTION cleanup_old_xml_files()
RETURNS void AS $$
BEGIN
    -- Delete files older than 90 days
    DELETE FROM storage.objects
    WHERE bucket_id = 'invoice-xmls'
    AND created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_storage_objects_bucket_created 
ON storage.objects(bucket_id, created_at);

-- Verify storage setup
SELECT 'MVP Storage setup completed successfully!' as status;