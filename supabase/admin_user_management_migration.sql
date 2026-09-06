-- Admin User Management v1: protected user listing and role management RPCs.
-- Run separately after the frontend is merged. This file does not change memberships.

begin;

create or replace function public.admin_list_users(
  p_query text default null,
  p_role text default null,
  p_limit integer default 25,
  p_offset integer default 0
)
returns table (
  user_id uuid,
  email text,
  display_name text,
  provider text,
  created_at timestamptz,
  last_sign_in_at timestamptz,
  is_admin boolean,
  submission_count bigint,
  pending_count bigint,
  approved_count bigint,
  rejected_count bigint,
  total_count bigint
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  normalized_query text := nullif(btrim(coalesce(p_query, '')), '');
  normalized_role text := lower(btrim(coalesce(p_role, '')));
  effective_limit integer := greatest(1, least(coalesce(p_limit, 25), 100));
  effective_offset integer := greatest(0, coalesce(p_offset, 0));
begin
  if not public.is_admin() then
    raise exception 'Administrator access required' using errcode = '42501';
  end if;

  if normalized_role not in ('', 'admin', 'user') then
    raise exception 'Invalid user role filter' using errcode = '22023';
  end if;

  return query
  with submission_stats as (
    select
      s.uploader_id,
      count(*)::bigint as submission_count,
      count(*) filter (where s.status = 'pending')::bigint as pending_count,
      count(*) filter (where s.status = 'approved')::bigint as approved_count,
      count(*) filter (where s.status = 'rejected')::bigint as rejected_count
    from public.songs as s
    group by s.uploader_id
  ),
  safe_users as (
    select
      u.id as user_id,
      u.email::text as email,
      left(
        regexp_replace(
          coalesce(
            nullif(btrim(u.raw_user_meta_data ->> 'full_name'), ''),
            nullif(btrim(u.raw_user_meta_data ->> 'name'), ''),
            nullif(btrim(u.raw_user_meta_data ->> 'display_name'), ''),
            nullif(btrim(u.raw_user_meta_data ->> 'preferred_username'), ''),
            nullif(btrim(u.email), ''),
            '未命名使用者'
          ),
          '[[:cntrl:]]',
          '',
          'g'
        ),
        120
      ) as display_name,
      left(
        coalesce(
          nullif(btrim(u.raw_app_meta_data ->> 'provider'), ''),
          nullif(btrim(u.raw_app_meta_data -> 'providers' ->> 0), ''),
          nullif(btrim(u.raw_user_meta_data ->> 'provider'), ''),
          'unknown'
        ),
        40
      ) as provider,
      u.created_at,
      u.last_sign_in_at,
      (au.user_id is not null) as is_admin,
      coalesce(ss.submission_count, 0)::bigint as submission_count,
      coalesce(ss.pending_count, 0)::bigint as pending_count,
      coalesce(ss.approved_count, 0)::bigint as approved_count,
      coalesce(ss.rejected_count, 0)::bigint as rejected_count
    from auth.users as u
    left join public.admin_users as au on au.user_id = u.id
    left join submission_stats as ss on ss.uploader_id = u.id
  ),
  filtered_users as (
    select su.*
    from safe_users as su
    where (
      normalized_query is null
      or lower(coalesce(su.email, '')) like '%' || lower(normalized_query) || '%'
      or lower(su.display_name) like '%' || lower(normalized_query) || '%'
      or lower(su.provider) like '%' || lower(normalized_query) || '%'
    )
    and (
      normalized_role = ''
      or (normalized_role = 'admin' and su.is_admin)
      or (normalized_role = 'user' and not su.is_admin)
    )
  )
  select
    fu.user_id,
    fu.email,
    fu.display_name,
    fu.provider,
    fu.created_at,
    fu.last_sign_in_at,
    fu.is_admin,
    fu.submission_count,
    fu.pending_count,
    fu.approved_count,
    fu.rejected_count,
    count(*) over()::bigint as total_count
  from filtered_users as fu
  order by
    (fu.user_id = (select auth.uid())) desc,
    fu.is_admin desc,
    fu.last_sign_in_at desc nulls last,
    fu.created_at desc,
    fu.user_id
  limit effective_limit
  offset effective_offset;
end;
$$;

revoke all on function public.admin_list_users(text, text, integer, integer) from public;
grant execute on function public.admin_list_users(text, text, integer, integer) to authenticated;

create or replace function public.admin_set_user_role(
  p_user_id uuid,
  p_is_admin boolean
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  admin_count bigint;
begin
  if not public.is_admin() then
    raise exception 'Administrator access required' using errcode = '42501';
  end if;

  if p_user_id is null or p_is_admin is null then
    raise exception 'User id and administrator role are required' using errcode = '22023';
  end if;

  if not exists (select 1 from auth.users as u where u.id = p_user_id) then
    raise exception 'User not found' using errcode = 'P0002';
  end if;

  if not p_is_admin and p_user_id = (select auth.uid()) then
    raise exception 'You cannot remove your own administrator role' using errcode = '42501';
  end if;

  lock table public.admin_users in share row exclusive mode;

  if p_is_admin then
    insert into public.admin_users (user_id)
    values (p_user_id)
    on conflict (user_id) do nothing;
  elsif exists (select 1 from public.admin_users as au where au.user_id = p_user_id) then
    select count(*) into admin_count from public.admin_users;
    if admin_count <= 1 then
      raise exception 'Cannot remove the last administrator' using errcode = '23514';
    end if;
    delete from public.admin_users as au where au.user_id = p_user_id;
  end if;
end;
$$;

revoke all on function public.admin_set_user_role(uuid, boolean) from public;
grant execute on function public.admin_set_user_role(uuid, boolean) to authenticated;

commit;
