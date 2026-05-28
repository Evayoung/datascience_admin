# Segun Banji Portfolio Admin

FastHTML + Faststrap PWA admin for managing the Supabase-backed portfolio.

## Local Development

```powershell
python -m pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:8064`.

## Vercel Deployment

The app is configured for Vercel with `vercel.json`. Vercel should build `main.py` with `@vercel/python` and route all traffic to it.

Required environment variables:

```text
ADMIN_PASSWORD=
ADMIN_SECRET_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=portfolio-images
PORTFOLIO_PROFILE_ID=segun-banji
PORTFOLIO_OWNER_NAME=Segun Banji
ADMIN_APP_NAME=Segun Banji Admin
PORTFOLIO_SITE_URL=https://banjisegun.vercel.app
SUPABASE_TIMEOUT_SECONDS=10
```

Keep `SUPABASE_SERVICE_ROLE_KEY` only in this admin app. Do not expose it in the public portfolio app.

Run `supabase_admin_settings.sql` once in Supabase to enable in-app password changes. The reset action removes the stored override and falls back to `ADMIN_PASSWORD`.

## Notes

- `/login` protects the admin.
- `/admin/images` uploads images to Supabase Storage.
- `/admin/security` changes or resets the admin password.
- Project image fields accept either a hosted URL or a direct upload.
- Social icons are selected from a preset list so editors do not need to know Bootstrap Icon names.
