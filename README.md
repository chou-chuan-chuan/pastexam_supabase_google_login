# Past Exam Library — Google Login + GitHub Pages + Supabase

This version replaces email/password authentication with **Sign in with Google**.
It does not use Supabase confirmation emails for normal sign-in.

## 1. Supabase database and storage

If you have not already run the database setup, open:

```text
Supabase Dashboard -> SQL Editor -> New query
```

Paste and run `supabase/setup.sql`.

## 2. Create the Google OAuth application

Open Google Cloud Console and create or select a project.

In **Google Auth Platform**:

1. **Branding** — enter an application name and support email.
2. **Audience** — choose the audience. For initial testing, add the Google accounts that will test the site.
3. **Data Access** — use only the normal sign-in scopes: `openid`, email, and profile.
4. **Clients** — create an OAuth client with application type **Web application**.

Add these **Authorized JavaScript origins**:

```text
http://localhost:8000
https://YOUR-GITHUB-USERNAME.github.io
```

An origin must not contain the repository path.

Add this exact **Authorized redirect URI**:

```text
https://hxzbuupsbawfeosnboie.supabase.co/auth/v1/callback
```

Copy the generated Google **Client ID** and **Client Secret**.

## 3. Enable Google in Supabase

Open:

```text
Supabase Dashboard -> Authentication -> Providers -> Google
```

Enable Google and paste the Google Client ID and Client Secret. Save the provider.
The Google Client Secret belongs in the Supabase dashboard, not in `config.js` or GitHub.

## 4. Configure the app redirect URLs in Supabase

Open:

```text
Authentication -> URL Configuration
```

Set **Site URL** to your final GitHub Pages address, including the repository path and trailing slash:

```text
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY/
```

Add these under **Redirect URLs**:

```text
http://localhost:8000/
https://YOUR-GITHUB-USERNAME.github.io/YOUR-REPOSITORY/
```

Use the exact production URL rather than a wildcard.

## 5. Add your Supabase publishable key

Open `config.js` and replace:

```javascript
PASTE_YOUR_SB_PUBLISHABLE_KEY_HERE
```

with the browser-safe key beginning with `sb_publishable_`.
Never use `sb_secret_...` or `service_role` in this file.

## 6. Test locally

Run:

```bash
python -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

Click **Sign in with Google**.

## 7. Publish on GitHub Pages

Push this folder to GitHub, then enable:

```text
Settings -> Pages -> Deploy from a branch -> main -> /(root)
```

## 8. Approve uploads

Open:

```text
Supabase -> Table Editor -> exams
```

Change an upload's `status` from `pending` to `approved`.

## Optional: allow only NTHU Google accounts

The default setup permits any Google account. To secure uploads to one email domain,
you must enforce that domain in Supabase Row Level Security, not only in JavaScript.
For example, policies can check the authenticated JWT email domain before allowing
an insert or Storage upload.
