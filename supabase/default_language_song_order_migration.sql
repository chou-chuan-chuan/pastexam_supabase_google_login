begin;

-- This migration intentionally resets the existing public display positions
-- once to establish the new language-based default. Manual ordering performed
-- before this migration will therefore be replaced.
do $$
begin
  if to_regclass('public.song_display_order') is null then
    raise exception 'public.song_display_order must exist before applying this migration';
  end if;
end;
$$;

insert into public.song_display_order (song_id, position, updated_at, updated_by)
select
  id,
  row_number() over (
    order by
      case when language is null or btrim(language) = '' then 1 else 0 end,
      lower(btrim(language)),
      created_at desc,
      id
  ) * 1024,
  now(),
  null
from public.songs
where status = 'approved'
on conflict (song_id) do update
set position = excluded.position,
    updated_at = excluded.updated_at,
    updated_by = excluded.updated_by;

create or replace function public.append_approved_song_to_display_order()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  predecessor_song_id uuid;
  successor_song_id uuid;
  predecessor_position bigint;
  successor_position bigint;
  new_language_key text := lower(btrim(coalesce(new.language, '')));
  new_language_is_blank boolean := btrim(coalesce(new.language, '')) = '';
  needs_renumber boolean := false;
begin
  if new.status <> 'approved' then
    return new;
  end if;
  if tg_op = 'UPDATE' and old.status = 'approved' then
    return new;
  end if;

  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtext('public.song_display_order'));

  if exists (
    select 1 from public.song_display_order where song_id = new.id
  ) then
    return new;
  end if;

  -- Place a newly approved song after the last currently displayed song in
  -- the same normalized language group, without re-sorting existing rows.
  select song_order.song_id
  into predecessor_song_id
  from public.song_display_order song_order
  join public.songs song on song.id = song_order.song_id
  where song.status = 'approved'
    and (
      (new_language_is_blank and btrim(coalesce(song.language, '')) = '')
      or (
        not new_language_is_blank
        and btrim(coalesce(song.language, '')) <> ''
        and lower(btrim(song.language)) = new_language_key
      )
    )
  order by song_order.position desc, song.created_at, song.id desc
  limit 1;

  if predecessor_song_id is not null then
    with ordered as (
      select
        song_order.song_id,
        lead(song_order.song_id) over (
          order by song_order.position, song.created_at desc, song.id
        ) as next_song_id
      from public.song_display_order song_order
      join public.songs song on song.id = song_order.song_id
      where song.status = 'approved'
    )
    select next_song_id into successor_song_id
    from ordered
    where song_id = predecessor_song_id;
  else
    -- If the language is new, insert before the first displayed group that
    -- follows it in the canonical language order (blank languages are last).
    select song_order.song_id
    into successor_song_id
    from public.song_display_order song_order
    join public.songs song on song.id = song_order.song_id
    where song.status = 'approved'
      and not new_language_is_blank
      and (
        btrim(coalesce(song.language, '')) = ''
        or (
          btrim(coalesce(song.language, '')) <> ''
          and lower(btrim(song.language)) > new_language_key
        )
      )
    order by song_order.position, song.created_at desc, song.id
    limit 1;

    if successor_song_id is not null then
      with ordered as (
        select
          song_order.song_id,
          lag(song_order.song_id) over (
            order by song_order.position, song.created_at desc, song.id
          ) as previous_song_id
        from public.song_display_order song_order
        join public.songs song on song.id = song_order.song_id
        where song.status = 'approved'
      )
      select previous_song_id into predecessor_song_id
      from ordered
      where song_id = successor_song_id;
    else
      select song_order.song_id
      into predecessor_song_id
      from public.song_display_order song_order
      join public.songs song on song.id = song_order.song_id
      where song.status = 'approved'
      order by song_order.position desc, song.created_at, song.id desc
      limit 1;
    end if;
  end if;

  if predecessor_song_id is not null then
    select position into predecessor_position
    from public.song_display_order
    where song_id = predecessor_song_id;
  end if;
  if successor_song_id is not null then
    select position into successor_position
    from public.song_display_order
    where song_id = successor_song_id;
  end if;

  needs_renumber := (
    predecessor_position is not null
    and successor_position is not null
    and successor_position::numeric - predecessor_position::numeric <= 1
  ) or (
    predecessor_position is not null
    and successor_position is null
    and predecessor_position > 9223372036854774783 - 1024
  ) or (
    predecessor_position is null
    and successor_position is not null
    and successor_position < -9223372036854775808 + 1024
  );

  if needs_renumber then
    -- Restore gaps while preserving the current displayed order, including
    -- any cross-language arrangement previously chosen with admin controls.
    with ranked as (
      select
        song_order.song_id,
        row_number() over (
          order by song_order.position, song.created_at desc, song.id
        ) * 1024 as new_position
      from public.song_display_order song_order
      join public.songs song on song.id = song_order.song_id
      where song.status = 'approved'
    )
    update public.song_display_order song_order
    set position = ranked.new_position,
        updated_at = now(),
        updated_by = (select auth.uid())
    from ranked
    where song_order.song_id = ranked.song_id;

    if predecessor_song_id is not null then
      select position into predecessor_position
      from public.song_display_order
      where song_id = predecessor_song_id;
    end if;
    if successor_song_id is not null then
      select position into successor_position
      from public.song_display_order
      where song_id = successor_song_id;
    end if;
  end if;

  insert into public.song_display_order (song_id, position, updated_by)
  values (
    new.id,
    case
      when predecessor_position is not null and successor_position is not null
        then ((predecessor_position::numeric + successor_position::numeric) / 2)::bigint
      when predecessor_position is not null then predecessor_position + 1024
      when successor_position is not null then successor_position - 1024
      else 1024
    end,
    (select auth.uid())
  )
  on conflict (song_id) do nothing;
  return new;
end;
$$;

revoke all on function public.append_approved_song_to_display_order() from public;

commit;
