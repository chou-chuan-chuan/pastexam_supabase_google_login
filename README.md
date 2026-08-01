# Past Exam Library — Google Login + GitHub Pages + Supabase

This static GitHub Pages site uses Google OAuth through Supabase Authentication.
The public archive is `index.html`; the administrator interface is `admin.html`.

## Current configuration status

`config.js` currently names this Supabase project URL:

```text
https://hxzbuupsbawfeosnboie.supabase.co
```

During the 2026-08-01 login repair, that hostname returned DNS `NXDOMAIN` while
GitHub resolved normally. Until that Supabase project is restored or `config.js`
is updated with the URL and matching publishable key from an active project,
database, storage, and Google login requests cannot reach Supabase. Do not guess
or mix the URL and key from different projects.

Only a browser-safe publishable/anon key belongs in `config.js`. Never commit a
Google Client Secret, `sb_secret_...` key, or Supabase `service_role` key.

## Authentication behavior

Both pages use the shared `assets/auth.js` helper and Supabase JS v2 PKCE:

- the public page redirects back to the repository root;
- the administrator page redirects back to `admin.html`;
- only the fixed `home` and `admin` destinations are accepted (no arbitrary
  return-to URL or open redirect);
- `detectSessionInUrl`, session persistence, and automatic refresh are enabled;
- Supabase exchanges the PKCE authorization code; application code never parses
  or stores OAuth tokens;
- callback query/hash values are removed only after `getSession()` has completed;
- query and hash OAuth errors are shown to the user;
- auth events are serialized and duplicate initial-session work is ignored;
- login performs a public `/auth/v1/settings` preflight, so an unreachable
  project or disabled Google provider produces an on-page error and re-enables
  the login button.

## 1. Supabase database and storage

In Supabase Dashboard, open **SQL Editor → New query** and run:

1. `supabase/setup.sql`
2. `supabase/admin_setup.sql` (for the administrator interface)

The Google account designated near the bottom of `admin_setup.sql` must sign in
once before its `auth.users` row can be inserted into `public.admin_users`.

## 2. Restore or verify the Supabase project

Open the intended Supabase project and copy both values from its API settings:

- Project URL
- browser-safe publishable key (or legacy anon key)

Put that matching pair in `config.js`. If the existing project reference
`hxzbuupsbawfeosnboie` is still the intended project, first resolve why its
hostname does not exist. A paused project normally must be restored from the
Supabase Dashboard; a deleted project requires a replacement project and rerun
of the SQL files above.

After updating `config.js`, this URL must return JSON instead of a DNS error:

```text
https://hxzbuupsbawfeosnboie.supabase.co/auth/v1/settings
```

If a replacement project is used, test the same `/auth/v1/settings` path on its
new Project URL and use that new project reference in the Google callback below.

### New project cutover checklist

Do these steps in order when moving the site to a replacement Supabase project:

1. Run `supabase/setup.sql` in the new project.
2. After the intended administrator has signed in once, run
   `supabase/admin_setup.sql`.
3. Enable and configure the Google provider in Supabase Authentication.
4. Set the production Site URL shown below.
5. Add all four exact Redirect URLs shown below.
6. Update `config.js` with the new Project URL and its matching browser-safe
   publishable/anon key.
7. Run the automated tests and the real local OAuth tests on both `/` and
   `/admin.html`.
8. Merge the OAuth repair branch into `main` only after those real OAuth tests
   succeed. Deploy GitHub Pages only after the tested configuration is merged.

## 3. Google Cloud Console

In **Google Auth Platform**:

1. Configure **Branding** with an application name, support email, and required
   contact information.
2. Under **Audience**, choose the intended Internal/External audience. If an
   External app is in Testing, add every Google account that will test login as
   a test user. Publish the app when appropriate.
3. Under **Data Access**, request only `openid`, email, and profile for ordinary
   sign-in.
4. Under **Clients**, create or edit a **Web application** OAuth client.

Authorized JavaScript origins (origin only; no repository path and no trailing
page name):

```text
http://localhost:8000
https://chou-chuan-chuan.github.io
```

Authorized redirect URI (Supabase callback, not a GitHub Pages URL):

```text
https://hxzbuupsbawfeosnboie.supabase.co/auth/v1/callback
```

If `config.js` is moved to a replacement Supabase project, replace the project
reference in that callback with the new one. Its required form is:

```text
https://ACTUAL_PROJECT_REFERENCE.supabase.co/auth/v1/callback
```

Paste the Google Client ID and Client Secret only into Supabase Dashboard →
Authentication → Providers → Google. The secret must not be placed in this
repository. Never use a GitHub Pages URL as the Google Authorized redirect URI.

## 4. Supabase Authentication settings

Open **Authentication → Providers → Google**, enable Google, and save the Google
Client ID and Client Secret.

Then open **Authentication → URL Configuration**.

Site URL:

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/
```

Redirect URLs — add all four exact values:

```text
http://localhost:8000/
http://localhost:8000/admin.html
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

`admin.html` is required because the administrator page passes that exact URL as
`redirectTo`. Supabase must allow the exact URLs sent by the application. Exact
production URLs are preferred over wildcards.

## 5. Local test

From the repository root:

```bash
python -m http.server 8000
```

Open and test both pages:

```text
http://localhost:8000/
http://localhost:8000/admin.html
```

For each page:

1. Click **Sign in with Google**.
2. Confirm the browser reaches Google through the Supabase authorize endpoint.
3. Finish Google login in the same browser/device where it started (PKCE stores
   its verifier locally).
4. Confirm the final page is respectively `/` or `/admin.html`, with no OAuth
   `code`, token, or error left in the address bar.
5. Refresh and confirm the session remains signed in.
6. Sign out and confirm the signed-out UI appears.

On `admin.html`, an authenticated account absent from `public.admin_users` must
see **This account is not an administrator**. That is a successful login followed
by an authorization denial, not an OAuth failure.

## 6. Automated tests

No dependency installation is needed. Run either:

```bash
npm test
```

or, if PowerShell blocks `npm.ps1`:

```powershell
npm.cmd test
```

The tests verify local and production redirect calculations, repository path
preservation, callback cleanup, OAuth error parsing, PKCE client options,
provider preflight behavior, and return-to safety.

## 7. GitHub Pages deployment and production check

Enable **Settings → Pages → Deploy from a branch → main → /(root)**, then open:

```text
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/
https://chou-chuan-chuan.github.io/pastexam_supabase_google_login/admin.html
```

Repeat the local test on both URLs. Confirm the repository path
`/pastexam_supabase_google_login/` remains present throughout the return to the
application.

## Common OAuth failures

- **`Cannot reach Supabase Authentication` / `Failed to fetch` / DNS error**:
  the Project URL is wrong, deleted, inactive, or unreachable. Verify the
  Project URL and its matching publishable key in `config.js`.
- **`redirect_uri_mismatch` from Google**: Google Authorized redirect URI must
  be the Supabase `/auth/v1/callback` URL, exactly; it is not the Pages URL.
- **Returns to Site URL or the wrong page**: the exact application `redirectTo`
  is missing from Supabase Redirect URLs. Check all four entries above,
  especially both `admin.html` values.
- **Google says access is blocked or denied**: for an External app in Testing,
  add the account under OAuth consent screen test users; also verify consent
  screen configuration.
- **Signed in but administrator access is denied**: login succeeded, but the
  user is not in `public.admin_users`. Run/check `supabase/admin_setup.sql`.
- **PKCE code exchange fails or a code is already used**: restart sign-in in the
  same browser/device and do not copy the callback URL between browsers. A PKCE
  authorization code is single-use.

## Approving uploads

Use `admin.html` after running `supabase/admin_setup.sql`, or update the status in
Supabase Table Editor. Database RLS remains the authority for uploads and
administrator actions.
