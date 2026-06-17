-- Increase the existing past-exams bucket limit to 50 MiB.
-- Run in Supabase Dashboard -> SQL Editor.
--
-- Also set Storage -> Settings -> Global file size limit to at least 50 MB.

update storage.buckets
set file_size_limit = 50 * 1024 * 1024
where id = 'past-exams';

-- Verify the result. file_size_limit should be 52428800.
select id, name, public, file_size_limit, allowed_mime_types
from storage.buckets
where id = 'past-exams';
