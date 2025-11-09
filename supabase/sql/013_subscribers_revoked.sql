-- Add revoked_at to mark refunded/chargeback subscriptions
alter table if exists public.subscribers
  add column if not exists revoked_at timestamptz;


