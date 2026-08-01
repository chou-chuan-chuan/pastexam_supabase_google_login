# Past Exam Library — administrator interface

The administrator UI is:

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

It uses the same shared PKCE/session implementation as the public archive. See
`README.md` for the complete Google Cloud and Supabase configuration, including
the currently unreachable Supabase project warning.

## One-time administrator setup

1. Configure a working Project URL and matching browser-safe publishable key in
   `config.js`.
2. Run `supabase/setup.sql`.
3. Sign in once with the intended administrator Google account so it exists in
   `auth.users`.
4. If necessary, edit the designated email near the bottom of
   `supabase/admin_setup.sql`, then run that SQL file.
5. Confirm its final query returns the intended email.
6. Add both exact administrator callback destinations to Supabase
   Authentication → URL Configuration → Redirect URLs:

```text
http://localhost:8000/admin.html
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

The root callbacks listed in `README.md` are also required for public-page login.

## Expected authorization behavior

After Google login, the page calls the security-definer `public.is_admin()`
function. RLS authorizes viewing and changing all submissions only for a user in
`public.admin_users`.

A signed-in non-admin sees an explicit **This account is not an administrator**
screen. They must not see the dashboard; this is distinct from login failure.

The administrator can preview PDFs, approve, reject, return a submission to
pending, or permanently delete its PDF and database row. Never put a Google
Client Secret, Supabase secret key, or `service_role` key in the browser files.
