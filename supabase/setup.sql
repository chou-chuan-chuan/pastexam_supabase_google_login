-- Run once in Supabase Dashboard -> SQL Editor.

create table if not exists public.exams (
  id uuid primary key default gen_random_uuid(),
  course text not null,
  teacher text,
  year integer not null check (year between 1900 and 2100),
  semester text,
  exam_type text,
  notes text,
  file_path text not null,
  original_filename text not null,
  uploader_id uuid references auth.users(id) on delete set null default auth.uid(),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  created_at timestamptz not null default now()
);

alter table public.exams enable row level security;

grant select on public.exams to anon, authenticated;
grant insert, delete on public.exams to authenticated;

drop policy if exists "Read approved exams or own submissions" on public.exams;
drop policy if exists "Authenticated users submit pending exams" on public.exams;
drop policy if exists "Users delete their own pending exams" on public.exams;

create policy "Read approved exams or own submissions"
on public.exams for select
to anon, authenticated
using (status = 'approved' or uploader_id = (select auth.uid()));

create policy "Authenticated users submit pending exams"
on public.exams for insert
to authenticated
with check (
  uploader_id = (select auth.uid())
  and status = 'pending'
  and split_part(file_path, '/', 1) = (select auth.uid()::text)
);

create policy "Users delete their own pending exams"
on public.exams for delete
to authenticated
using (uploader_id = (select auth.uid()) and status = 'pending');

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'past-exams',
  'past-exams',
  true,
  52428800,
  array['application/pdf']
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "Authenticated users upload PDFs to own folder" on storage.objects;
drop policy if exists "Users delete PDFs from own folder" on storage.objects;

create policy "Authenticated users upload PDFs to own folder"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'past-exams'
  and lower(storage.extension(name)) = 'pdf'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "Users delete PDFs from own folder"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'past-exams'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

-- Approve uploads in Table Editor by changing exams.status to 'approved'.
