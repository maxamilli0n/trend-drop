import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

type Row = {
  id: string;
  title: string | null;
  price: number | null;
  currency: string | null;
  image_url: string | null;
  url: string | null;
  keyword: string | null;
  seller_feedback: number | null;
  top_rated: boolean | null;
  provider: string | null;
  source: string | null;
  created_at: string;
};

function supa() {
  const url = Deno.env.get("SUPABASE_URL")!;
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  return createClient(url, key, { auth: { persistSession: false } });
}

function toCSV(rows: Row[]): string {
  if (!rows.length) return "";
  const headers = Object.keys(rows[0]) as (keyof Row)[];
  const headerLine = headers.join(",");
  const esc = (v: unknown) =>
    v == null ? "" : String(v).includes(",") || String(v).includes("\"") || String(v).includes("\n")
      ? `"${String(v).replaceAll("\"", "\"\"")}"`
      : String(v);
  const dataLines = rows.map((r) => headers.map((h) => esc((r as any)[h])).join(","));
  return [headerLine, ...dataLines].join("\n");
}

serve(async (req) => {
  try {
    const url = new URL(req.url);
    const type   = (url.searchParams.get("type") || "top").toLowerCase(); // top | recent | search
    const format = (url.searchParams.get("format") || "json").toLowerCase(); // json | csv
    const q      = url.searchParams.get("q") || "";
    const minFb  = Number(url.searchParams.get("min_feedback") || "0");
    const days   = Number(url.searchParams.get("days") || (type === "recent" ? "7" : "0"));
    const limit  = Math.min(Number(url.searchParams.get("limit") || "200"), 1000);

    const s = supa();
    let rows: Row[] = [];

    if (type === "top") {
      const { data, error } = await s.from("v_products_top_by_feedback").select("*").limit(limit);
      if (error) throw error;
      rows = (data || []) as Row[];
    } else if (type === "recent") {
      if (days === 7) {
        const { data, error } = await s.from("v_products_recent_7d").select("*").limit(limit);
        if (error) throw error;
        rows = (data || []) as Row[];
      } else {
        const { data, error } = await s.rpc("products_by_keyword", {
          q: "",
          min_feedback: 0,
          days,
          max_rows: limit,
        });
        if (error) throw error;
        rows = (data || []) as Row[];
      }
    } else {
      const { data, error } = await s.rpc("products_by_keyword", {
        q,
        min_feedback: minFb,
        days,
        max_rows: limit,
      });
      if (error) throw error;
      rows = (data || []) as Row[];
    }

    if (format === "csv") {
      const csv = toCSV(rows);
      return new Response(csv, {
        status: 200,
        headers: {
          "content-type": "text/csv; charset=utf-8",
          "cache-control": "public, max-age=60",
        },
      });
    }

    return new Response(JSON.stringify({ ok: true, count: rows.length, rows }, null, 2), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "cache-control": "public, max-age=30",
      },
    });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: String(e) }), {
      status: 500,
      headers: { "content-type": "application/json" },
    });
  }
});