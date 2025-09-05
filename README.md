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
