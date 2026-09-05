begin;

create table if not exists public.song_display_order (
  song_id uuid primary key references public.songs(id) on delete cascade,
  position bigint not null,
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id) on delete set null
);

insert into public.song_display_order (song_id, position)
select id, row_number() over (order by created_at desc, id) * 1024
from public.songs
where status = 'approved'
on conflict (song_id) do nothing;

alter table public.song_display_order enable row level security;

revoke all on table public.song_display_order from anon, authenticated;
grant select on table public.song_display_order to anon, authenticated;

drop policy if exists "Public song order is readable" on public.song_display_order;
create policy "Public song order is readable"
on public.song_display_order for select
to anon, authenticated
using (
  exists (
    select 1
    from public.songs s
    where s.id = song_id
      and s.status = 'approved'
  )
);

create or replace function public.append_approved_song_to_display_order()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  next_position bigint;
begin
  if new.status <> 'approved' then
    return new;
  end if;
  if tg_op = 'UPDATE' and old.status = 'approved' then
    return new;
  end if;

  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('public.song_display_order'));

  select coalesce(max(song_order.position), 0) + 1024
  into next_position
  from public.song_display_order song_order
  join public.songs song on song.id = song_order.song_id
  where song.status = 'approved';

  insert into public.song_display_order (song_id, position)
  values (new.id, next_position)
  on conflict (song_id) do nothing;
  return new;
end;
$$;

revoke all on function public.append_approved_song_to_display_order() from public;

drop trigger if exists songs_append_public_display_order on public.songs;
create trigger songs_append_public_display_order
after insert or update of status on public.songs
for each row execute function public.append_approved_song_to_display_order();

create or replace function public.move_song_in_public_order(
  p_song_id uuid,
  p_direction integer
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  neighbor_song_id uuid;
  current_position bigint;
  neighbor_position bigint;
begin
  if not public.is_admin() then
    raise exception 'Administrator access required' using errcode = '42501';
  end if;

  if p_direction not in (-1, 1) then
    raise exception 'Direction must be -1 or 1' using errcode = '22023';
  end if;

  if not exists (
    select 1 from public.songs
    where id = p_song_id and status = 'approved'
  ) then
    raise exception 'Approved song not found' using errcode = 'P0002';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('public.song_display_order'));

  with ordered as (
    select
      song_order.song_id,
      lag(song_order.song_id) over (
        order by song_order.position, song.created_at desc, song.id
      ) as previous_song_id,
      lead(song_order.song_id) over (
        order by song_order.position, song.created_at desc, song.id
      ) as next_song_id
    from public.song_display_order song_order
    join public.songs song on song.id = song_order.song_id
    where song.status = 'approved'
  )
  select case when p_direction = -1 then previous_song_id else next_song_id end
  into neighbor_song_id
  from ordered
  where song_id = p_song_id;

  if neighbor_song_id is null then
    return;
  end if;

  perform 1
  from public.song_display_order
  where song_id in (p_song_id, neighbor_song_id)
  for update;

  select position into current_position
  from public.song_display_order
  where song_id = p_song_id;

  select position into neighbor_position
  from public.song_display_order
  where song_id = neighbor_song_id;

  update public.song_display_order
  set position = case
        when song_id = p_song_id then neighbor_position
        else current_position
      end,
      updated_at = now(),
      updated_by = (select auth.uid())
  where song_id in (p_song_id, neighbor_song_id);
end;
$$;

revoke all on function public.move_song_in_public_order(uuid, integer) from public;
grant execute on function public.move_song_in_public_order(uuid, integer) to authenticated;

commit;
