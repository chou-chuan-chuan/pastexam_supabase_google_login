# Past Exam Library — administrator interface

This package keeps the public archive in `index.html` and adds a separate review page at `admin.html`.

## Files to upload

Copy these files into the same GitHub repository:

```text
index.html
admin.html
assets/app.js
assets/admin.js
assets/style.css
supabase/admin_setup.sql
```

Keep your existing configured `config.js` in the repository root. Do not put a Supabase secret or service-role key in it.

## One-time setup

1. Deploy these files.
2. Sign in to the public website once using `ycchou@gapp.nthu.edu.tw`. This creates the Google user in Supabase Authentication.
3. Open Supabase Dashboard → SQL Editor.
4. Run `supabase/admin_setup.sql`.
5. Confirm that the final query returns `ycchou@gapp.nthu.edu.tw`.
6. In Supabase Dashboard → Authentication → URL Configuration → Redirect URLs, add:

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

You may instead use an appropriate wildcard for your GitHub Pages repository if you already configured one.

## Use

Open:

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

The administrator can preview PDFs on the same page, approve, reject, return a submission to pending, or permanently delete the PDF and database row.

## Changing the administrator

Edit the email near the bottom of `supabase/admin_setup.sql`, sign in once with that Google account, and rerun the final `insert into public.admin_users ...` statement.
