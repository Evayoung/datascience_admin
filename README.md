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
SUPABASE_TIMEOUT_SECONDS=10
```

Keep `SUPABASE_SERVICE_ROLE_KEY` only in this admin app. Do not expose it in the public portfolio app.

## Notes

- `/login` protects the admin.
- `/admin/images` uploads images to Supabase Storage.
- Project image fields accept either a hosted URL or a direct upload.
- Social icons are selected from a preset list so editors do not need to know Bootstrap Icon names.
