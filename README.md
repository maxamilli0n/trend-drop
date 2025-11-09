# TrendDrop — Zero-cost AI Affiliate Store (Starter Kit)

This repo is a **no-upfront-cost** starter for a fully automated affiliate store that:

- mines **trending topics**
- finds products via **eBay Finding API**
- wraps with your **eBay Partner Network (EPN)** affiliate links
- updates a **GitHub Pages storefront** (`/docs`) with a product grid
- optionally posts top picks to a **Telegram channel**

> You only need: a GitHub account, an eBay Developer account (free App ID), an EPN account (free), and a Telegram bot (free).

## Quick setup (TL;DR)

1. Create a GitHub repo and enable **Pages → branch main → /docs**.
2. Add GitHub Secrets: `EBAY_APP_ID`, optional `EPN_CAMPAIGN_ID`, `CUSTOM_ID_PREFIX`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
3. Go to **Actions → trenddrop-cron → Run workflow** once.
4. Visit your Pages URL; you should see products.

See the README in my earlier messages for the full plan.

## Supabase schema (run once)

```sql
create table if not exists runs (
  id uuid primary key default gen_random_uuid(),
  ran_at bigint not null,
  topics int not null,
  items int not null
);

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  inserted_at timestamp with time zone default now(),
  source text not null,
  title text not null,
  price numeric,
  currency text,
  image_url text,
  url text unique,
  keyword text,
  seller_feedback int,
  top_rated boolean default false
);

create table if not exists subscribers (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  created_at timestamp with time zone default now(),
  plan text default 'free'
);

create table if not exists clicks (
  id uuid primary key default gen_random_uuid(),
  product_url text not null,
  clicked_at timestamp with time zone default now()
);
```

## Lemon Squeezy webhook template

Create a Supabase Edge Function `lemon-webhook` and paste:

```ts
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { verifySignature } from "https://deno.land/x/lemon_squeezy_webhook@v1/mod.ts";

const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
const SECRET = Deno.env.get("LS_WEBHOOK_SECRET")!;

serve(async (req) => {
  const raw = await req.text();
  if (!verifySignature(SECRET, raw, req.headers)) return new Response("Bad sig", { status: 401 });
  const evt = JSON.parse(raw);

  const email = evt?.data?.attributes?.user_email;
  const status = evt?.data?.attributes?.status;
  if (email && status === "paid") {
    await supabase.from("subscribers").upsert({ email, plan: "pro" }, { onConflict: "email" });
  }

  return new Response("ok");
});
```

## Pricing (prep for Lemon Squeezy)

- **Free**: Site access + Telegram channel updates.
- **$5/mo (Weekly PDF)**: Access to the Top 10 Weekly PDF (auto‑generated, stored in Supabase). Customers receive a download link after checkout.
- **$15/mo (Niche Drops)**: Curated niche feeds (e.g., Gaming only, Fashion only, Home only), plus Weekly PDF.

Implementation status:

### Automation Status

[![Daily Report](https://github.com/${{ github.repository }}/actions/workflows/daily-report.yml/badge.svg)](.github/workflows/daily-report.yml)
[![Weekly Report](https://github.com/${{ github.repository }}/actions/workflows/weekly-report.yml/badge.svg)](.github/workflows/weekly-report.yml)

Implementation status:

- Weekly PDF generator: `python -m trenddrop.reports.generate_reports` (scheduled via `weekly-report.yml`).
- Daily PDF generator: `python -m trenddrop.reports.generate_reports` (scheduled via `daily-report.yml`).
- Storage: Supabase Storage bucket `reports` (public URLs).
- Hook-up: When LS is live, on successful checkout, email/serve the `reports/weekly/...pdf` link to subscribers based on tier.

## Phase 3 – Premium Community

This adds a minimal subscribers pipeline and a one-time Telegram invite flow.

### Deploy functions

```
supabase functions deploy gumroad-webhook
supabase functions deploy create-telegram-invite
```

### Set secrets

```
supabase secrets set \
  GUMROAD_WEBHOOK_SECRET=... \
  TELEGRAM_BOT_TOKEN=... \
  TELEGRAM_COMMUNITY_CHAT_ID=... \
  SUPABASE_SERVICE_ROLE_KEY=...
```

Make sure your `.env` (repo root) mirrors these for local tests; code reads only the real `.env` via the unified loader.

### Configure Gumroad Webhook

In Gumroad → Settings → Advanced → Webhooks set the URL to:

```
https://<YOUR-PROJECT-REF>.functions.supabase.co/gumroad-webhook
```

### Test locally

```
supabase functions serve gumroad-webhook
ngrok http 54321
```

Use `scripts/test_webhook_local.http` with your computed `gumroad_signature`.

### Claim flow

- Users visit `/claim.html`, enter their purchase email (and optional purchase_id)
- The `create-telegram-invite` function validates paid subscribers and returns a one-time invite link (7‑day expiry)
- The subscriber row is marked with `claimed_at` to prevent reclaims

## Phase 2 – Automated Reports

This repo now includes automated weekly/daily report generation via GitHub Actions, Supabase uploads with public URLs, smoke tests, and run logging.

### Required repository secrets

Set these in GitHub → Settings → Secrets and variables → Actions → New repository secret:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `REPORTS_BUCKET` (e.g. `trenddrop-reports`)
- `TELEGRAM_BOT_TOKEN` (optional, for failure alerts)
- `TELEGRAM_ALERT_CHAT_ID` (optional, for failure alerts)

You may also add existing generator-related keys as needed (no real secrets checked in): `EBAY_APP_ID`, `EPN_CAMPAIGN_ID`, `CUSTOM_ID_PREFIX`, `TELEGRAM_CHAT_ID`, `TELEGRAM_CHANNEL_ID`, `GUMROAD_CTA_URL`.

### Running the workflow

- Weekly: `.github/workflows/generate-weekly.yml` runs on Mondays 13:00 UTC and supports manual dispatch.
- Daily: `.github/workflows/generate-daily.yml` supports manual dispatch; its cron is commented out. Uncomment to enable.

Both workflows:
1) Install dependencies
2) Run `python -m trenddrop.reports.generate_reports`
3) Run `python -m scripts.smoke_test` to verify public URLs work and file sizes are sane
4) Log the run to `public.runs` with status, timings, artifact URLs, commit SHA, and workflow link
5) On failure, optionally Telegram‑alert a concise message with the job URL

### Where files go

- Latest: `${REPORTS_BUCKET}/weekly/latest.pdf` and `${REPORTS_BUCKET}/weekly/latest.csv`
- Dated: `${REPORTS_BUCKET}/weekly/YYYY-MM-DD/report.pdf` and `report.csv`

The generator also writes `out/artifacts.json` that includes the resolved public URLs for the smoke test and logging.

### Interpreting `runs` rows

Each CI execution inserts one row into `public.runs` (see `supabase/sql/001_runs.sql`). Fields include: `status`, `started_at`, `finished_at`, `duration_ms`, `pdf_url`, `csv_url`, `commit_sha`, `workflow_run_url`, `message`, `meta`.

### Local .env template

Create a `.env` (or `.env.example`) with the following keys:

```
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
REPORTS_BUCKET=trenddrop-reports
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALERT_CHAT_ID=

# Existing generator deps (no real secrets)
EBAY_APP_ID=
EPN_CAMPAIGN_ID=
CUSTOM_ID_PREFIX=
TELEGRAM_CHAT_ID=
TELEGRAM_CHANNEL_ID=
GUMROAD_CTA_URL=
```

### Troubleshooting

- Missing keys: Ensure `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` are set in repo secrets. The generator will skip uploads if credentials are absent.
- Bucket permissions: The code and `supabase/sql/002_storage_policies.sql` attempt to ensure a public bucket named `trenddrop-reports`. Adjust if you use a different name and run the SQL once.
- Network failures: The upload helper retries 3× with exponential backoff. Smoke test fetches public URLs and requires > 5KB files.
- Table missing: If `public.runs` is not created yet, logging will print a warning and continue; apply the SQL in `supabase/sql/001_runs.sql`.