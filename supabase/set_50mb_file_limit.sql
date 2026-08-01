-- Keep the lyrics-pdfs bucket limit synchronized with config.js (50 MiB).
-- Run in Supabase Dashboard -> SQL Editor.
--
-- Also set Storage -> Settings -> Global file size limit to at least 50 MB.

update storage.buckets
set file_size_limit = 50 * 1024 * 1024
where id = 'lyrics-pdfs';

-- Verify the result. file_size_limit should be 52428800.
select id, name, public, file_size_limit, allowed_mime_types
from storage.buckets
where id = 'lyrics-pdfs';
