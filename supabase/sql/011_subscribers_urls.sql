-- Add nullable columns for delivery links
alter table if exists public.subscribers
  add column if not exists pdf_url text,
  add column if not exists csv_url text;


