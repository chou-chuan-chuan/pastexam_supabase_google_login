-- Private personal playlists for the Lyrics PDF Library.
-- Run once in production after the application PR is merged.

begin;

create table if not exists public.playlists (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null check (length(btrim(name)) between 1 and 120),
  description text check (description is null or length(description) <= 1000),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.playlist_items (
  playlist_id uuid not null references public.playlists(id) on delete cascade,
  song_id uuid not null references public.songs(id) on delete cascade,
  position bigint not null check (position > 0),
  added_at timestamptz not null default now(),
  primary key (playlist_id, song_id),
  constraint playlist_items_playlist_position_unique
    unique (playlist_id, position) deferrable initially deferred
);

create index if not exists playlist_items_playlist_position
  on public.playlist_items (playlist_id, position);
create index if not exists playlist_items_song_id
  on public.playlist_items (song_id);

drop trigger if exists playlists_set_updated_at on public.playlists;
create trigger playlists_set_updated_at
before update on public.playlists
for each row execute function public.set_updated_at();

alter table public.playlists enable row level security;
alter table public.playlist_items enable row level security;

revoke all on table public.playlists, public.playlist_items from anon;
grant select, insert, update, delete on table public.playlists, public.playlist_items to authenticated;

drop policy if exists "Owners read playlists" on public.playlists;
create policy "Owners read playlists"
on public.playlists for select to authenticated
using (owner_id = (select auth.uid()));

drop policy if exists "Owners create playlists" on public.playlists;
create policy "Owners create playlists"
on public.playlists for insert to authenticated
with check (owner_id = (select auth.uid()));

drop policy if exists "Owners update playlists" on public.playlists;
create policy "Owners update playlists"
on public.playlists for update to authenticated
using (owner_id = (select auth.uid()))
with check (owner_id = (select auth.uid()));

drop policy if exists "Owners delete playlists" on public.playlists;
create policy "Owners delete playlists"
on public.playlists for delete to authenticated
using (owner_id = (select auth.uid()));

drop policy if exists "Owners read playlist items" on public.playlist_items;
create policy "Owners read playlist items"
on public.playlist_items for select to authenticated
using (
  exists (
    select 1 from public.playlists p
    where p.id = playlist_id
      and p.owner_id = (select auth.uid())
  )
);

drop policy if exists "Owners add approved playlist items" on public.playlist_items;
create policy "Owners add approved playlist items"
on public.playlist_items for insert to authenticated
with check (
  exists (
    select 1 from public.playlists p
    where p.id = playlist_id
      and p.owner_id = (select auth.uid())
  )
  and exists (
    select 1 from public.songs s
    where s.id = song_id
      and s.status = 'approved'
  )
);

drop policy if exists "Owners update playlist items" on public.playlist_items;
create policy "Owners update playlist items"
on public.playlist_items for update to authenticated
using (
  exists (
    select 1 from public.playlists p
    where p.id = playlist_id
      and p.owner_id = (select auth.uid())
  )
)
with check (
  exists (
    select 1 from public.playlists p
    where p.id = playlist_id
      and p.owner_id = (select auth.uid())
  )
  and exists (
    select 1 from public.songs s
    where s.id = song_id
      and s.status = 'approved'
  )
);

drop policy if exists "Owners delete playlist items" on public.playlist_items;
create policy "Owners delete playlist items"
on public.playlist_items for delete to authenticated
using (
  exists (
    select 1 from public.playlists p
    where p.id = playlist_id
      and p.owner_id = (select auth.uid())
  )
);

create or replace function public.add_song_to_playlist(
  p_playlist_id uuid,
  p_song_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  next_position bigint;
begin
  if (select auth.uid()) is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;

  if not exists (
    select 1 from public.playlists p
    where p.id = p_playlist_id
      and p.owner_id = (select auth.uid())
  ) then
    raise exception 'Playlist not found' using errcode = '42501';
  end if;

  if not exists (
    select 1 from public.songs s
    where s.id = p_song_id
      and s.status = 'approved'
  ) then
    raise exception 'Approved song not found' using errcode = '42501';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_playlist_id::text, 0)
  );

  select coalesce(max(pi.position), 0) + 1024
  into next_position
  from public.playlist_items pi
  where pi.playlist_id = p_playlist_id;

  insert into public.playlist_items (playlist_id, song_id, position)
  values (p_playlist_id, p_song_id, next_position)
  on conflict (playlist_id, song_id) do nothing;
end;
$$;

revoke all on function public.add_song_to_playlist(uuid, uuid) from public;
grant execute on function public.add_song_to_playlist(uuid, uuid) to authenticated;

create or replace function public.move_playlist_item(
  p_playlist_id uuid,
  p_song_id uuid,
  p_direction integer
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  current_position bigint;
  adjacent_song_id uuid;
  adjacent_position bigint;
begin
  if (select auth.uid()) is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;

  if p_direction not in (-1, 1) then
    raise exception 'Direction must be -1 or 1' using errcode = '22023';
  end if;

  if not exists (
    select 1 from public.playlists p
    where p.id = p_playlist_id
      and p.owner_id = (select auth.uid())
  ) then
    raise exception 'Playlist not found' using errcode = '42501';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(p_playlist_id::text, 0)
  );

  select pi.position
  into current_position
  from public.playlist_items pi
  where pi.playlist_id = p_playlist_id
    and pi.song_id = p_song_id
  for update;

  if current_position is null then
    return;
  end if;

  if p_direction = -1 then
    select pi.song_id, pi.position
    into adjacent_song_id, adjacent_position
    from public.playlist_items pi
    where pi.playlist_id = p_playlist_id
      and pi.position < current_position
    order by pi.position desc
    limit 1
    for update;
  else
    select pi.song_id, pi.position
    into adjacent_song_id, adjacent_position
    from public.playlist_items pi
    where pi.playlist_id = p_playlist_id
      and pi.position > current_position
    order by pi.position
    limit 1
    for update;
  end if;

  if adjacent_song_id is null then
    return;
  end if;

  update public.playlist_items
  set position = case
    when song_id = p_song_id then adjacent_position
    when song_id = adjacent_song_id then current_position
  end
  where playlist_id = p_playlist_id
    and song_id in (p_song_id, adjacent_song_id);
end;
$$;

revoke all on function public.move_playlist_item(uuid, uuid, integer) from public;
grant execute on function public.move_playlist_item(uuid, uuid, integer) to authenticated;

commit;
