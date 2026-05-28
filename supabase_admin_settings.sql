-- Admin-only settings table for datascience_admin.
-- Run this once in the Supabase SQL editor for the portfolio project.

create table if not exists public.admin_settings (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

create or replace function public.set_admin_settings_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists admin_settings_updated_at on public.admin_settings;
create trigger admin_settings_updated_at
before update on public.admin_settings
for each row execute function public.set_admin_settings_updated_at();

alter table public.admin_settings enable row level security;

drop policy if exists "No public access to admin settings" on public.admin_settings;
create policy "No public access to admin settings"
on public.admin_settings
for all
to anon, authenticated
using (false)
with check (false);
