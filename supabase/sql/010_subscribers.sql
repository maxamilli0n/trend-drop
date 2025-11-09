create extension if not exists pgcrypto;

create table if not exists public.subscribers (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  provider text not null check (provider in ('gumroad','payhip')),
  product_id text not null,
  purchase_id text not null,
  price_cents int,
  currency text default 'USD',
  status text not null check (status in ('paid','refunded','chargeback')),
  purchased_at timestamptz not null default now(),
  license_key text,
  metadata jsonb default '{}'::jsonb,
  claimed_at timestamptz,
  unique (provider, purchase_id)
);

-- Idempotent: ensure claimed_at exists for older deployments
alter table public.subscribers
  add column if not exists claimed_at timestamptz;

create index if not exists idx_subscribers_email on public.subscribers(email);


