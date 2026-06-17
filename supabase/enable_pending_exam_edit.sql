-- Past Exam Library: let users edit the metadata of their own pending exams.
--
-- Run this once in:
-- Supabase Dashboard -> SQL Editor -> New query
--
-- This function intentionally does NOT allow users to change:
-- status, uploader_id, file_path, original_filename, created_at,
-- reviewed_at, or reviewed_by.

begin;

create or replace function public.update_own_pending_exam(
  p_exam_id uuid,
  p_course text,
  p_teacher text,
  p_year integer,
  p_semester text,
  p_exam_type text,
  p_notes text
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  if auth.uid() is null then
    raise exception 'You must be signed in.';
  end if;

  if p_course is null or btrim(p_course) = '' then
    raise exception 'Course name is required.';
  end if;

  if char_length(btrim(p_course)) > 120 then
    raise exception 'Course name is too long.';
  end if;

  if p_teacher is not null and char_length(btrim(p_teacher)) > 120 then
    raise exception 'Teacher name is too long.';
  end if;

  if p_notes is not null and char_length(p_notes) > 1000 then
    raise exception 'Notes are too long.';
  end if;

  if p_year is null or p_year < 1900 or p_year > 2100 then
    raise exception 'Invalid exam year.';
  end if;

  if p_semester is not null
     and p_semester not in ('Spring', 'Fall', 'Summer', 'Winter') then
    raise exception 'Invalid semester.';
  end if;

  if p_exam_type is not null
     and p_exam_type not in (
       'Midterm',
       'Final',
       'Quiz',
       'Homework',
       'Solution',
       'Other'
     ) then
    raise exception 'Invalid exam type.';
  end if;

  update public.exams
  set
    course = btrim(p_course),
    teacher = nullif(btrim(coalesce(p_teacher, '')), ''),
    year = p_year,
    semester = nullif(btrim(coalesce(p_semester, '')), ''),
    exam_type = nullif(btrim(coalesce(p_exam_type, '')), ''),
    notes = nullif(btrim(coalesce(p_notes, '')), '')
  where id = p_exam_id
    and uploader_id = auth.uid()
    and status = 'pending';

  if not found then
    raise exception
      'This submission does not exist, is not yours, or is no longer pending.';
  end if;
end;
$$;

revoke all
on function public.update_own_pending_exam(
  uuid,
  text,
  text,
  integer,
  text,
  text,
  text
)
from public;

grant execute
on function public.update_own_pending_exam(
  uuid,
  text,
  text,
  integer,
  text,
  text,
  text
)
to authenticated;

commit;
