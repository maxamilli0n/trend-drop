-- Idempotent storage setup for public-read reports bucket
-- Uses REPORTS_BUCKET env at runtime; hardcode default that matches .env.example

-- Replace 'trenddrop-reports' if you use a different bucket name
do $$
begin
  perform 1 from storage.buckets where name = 'trenddrop-reports';
  if not found then
    insert into storage.buckets (id, name, public)
    values ('trenddrop-reports', 'trenddrop-reports', true);
  else
    update storage.buckets set public = true where name = 'trenddrop-reports';
  end if;
exception when others then
  -- best-effort: storage schema might differ; ignore errors
  null;
end $$;

-- Public read policy (best-effort/idempotent)
do $$
begin
  create policy if not exists "public read trenddrop-reports"
    on storage.objects for select
    using (bucket_id = 'trenddrop-reports');
exception when others then
  null;
end $$;


