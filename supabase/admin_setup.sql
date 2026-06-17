-- Past Exam Library: administrator approval setup
-- Run this in Supabase Dashboard -> SQL Editor.
-- The Google account below must sign in to your website at least once before
-- the final INSERT can find it in auth.users.

begin;

create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.admin_users enable row level security;

-- Do not expose the administrator list through the browser API.
revoke all on table public.admin_users from anon, authenticated;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1
    from public.admin_users
    where user_id = (select auth.uid())
  );
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to authenticated;

alter table public.exams
  add column if not exists reviewed_at timestamptz,
  add column if not exists reviewed_by uuid references auth.users(id) on delete set null;

alter table public.exams enable row level security;

-- These policy names are unique, so they can coexist with your current
-- public-reading and uploader policies.
drop policy if exists "Past exam admins can view all exams" on public.exams;
create policy "Past exam admins can view all exams"
on public.exams
for select
to authenticated
using ((select public.is_admin()));

drop policy if exists "Past exam admins can update all exams" on public.exams;
create policy "Past exam admins can update all exams"
on public.exams
for update
to authenticated
using ((select public.is_admin()))
with check (
  (select public.is_admin())
  and status in ('pending', 'approved', 'rejected')
);

drop policy if exists "Past exam admins can delete all exams" on public.exams;
create policy "Past exam admins can delete all exams"
on public.exams
for delete
to authenticated
using ((select public.is_admin()));

-- Storage remove() needs SELECT and DELETE access on storage.objects.
drop policy if exists "Past exam admins can select stored PDFs" on storage.objects;
create policy "Past exam admins can select stored PDFs"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'past-exams'
  and (select public.is_admin())
);

drop policy if exists "Past exam admins can delete stored PDFs" on storage.objects;
create policy "Past exam admins can delete stored PDFs"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'past-exams'
  and (select public.is_admin())
);

commit;

-- Designate the administrator account.
-- Change the email below if a different Google account should be the admin.
insert into public.admin_users (user_id)
select id
from auth.users
where lower(email) = lower('ycchou@gapp.nthu.edu.tw')
on conflict (user_id) do nothing;

-- Check the result. It should return one row.
select au.email, a.created_at
from public.admin_users a
join auth.users au on au.id = a.user_id
where lower(au.email) = lower('ycchou@gapp.nthu.edu.tw');
