-- Fix the correlated tag id: unqualified id resolves to the inner songs.id.
-- Visitors may read metadata only for tags attached to approved songs.
-- Existing authenticated tag reads and all write policies are unchanged.
begin;

drop policy if exists "Visible tags are readable" on public.tags;
create policy "Visible tags are readable"
on public.tags for select
to anon, authenticated
using (
  (select public.is_admin())
  or exists (
    select 1
    from public.song_tags st
    join public.songs s on s.id = st.song_id
    where st.tag_id = tags.id
      and (s.status = 'approved' or s.uploader_id = (select auth.uid()))
  )
);

commit;
