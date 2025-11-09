create extension if not exists pgcrypto; -- for gen_random_uuid

create table if not exists public.runs (
  id uuid primary key default gen_random_uuid(),
  status text not null check (status in ('success','failure')),
  started_at timestamptz not null,
  finished_at timestamptz not null,
  duration_ms bigint not null,
  pdf_url text,
  csv_url text,
  commit_sha text,
  workflow_run_url text,
  message text,
  meta jsonb default '{}'::jsonb
);


