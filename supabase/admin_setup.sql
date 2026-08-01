-- Lyrics PDF Library: designate an administrator after setup.sql.
-- The Google account must sign in once before this INSERT can find auth.users.

begin;

create table if not exists public.admin_users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.admin_users enable row level security;
revoke all on table public.admin_users from anon, authenticated;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.admin_users
    where user_id = (select auth.uid())
  );
$$;

revoke all on function public.is_admin() from public;
grant execute on function public.is_admin() to anon, authenticated;

commit;

-- Change this email before running if another account should be the admin.
insert into public.admin_users (user_id)
select id from auth.users
where lower(email) = lower('ycchou@gapp.nthu.edu.tw')
on conflict (user_id) do nothing;

select au.email, a.created_at
from public.admin_users a
join auth.users au on au.id = a.user_id
where lower(au.email) = lower('ycchou@gapp.nthu.edu.tw');
