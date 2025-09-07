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

```
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
```

## Lemon Squeezy webhook template

Create a Supabase Edge Function `lemon-webhook` and paste:

```
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