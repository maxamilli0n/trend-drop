// TD-AUTO: BEGIN report-links
// deno-lint-ignore-file no-explicit-any
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

function supaService() {
  const url = Deno.env.get("SUPABASE_URL");
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("supabase not configured");
  return createClient(url, key);
}

function requireAuth(req: Request): boolean {
  const auth = req.headers.get("authorization") || req.headers.get("Authorization");
  return !!auth; // rely on Supabase edge auth to validate JWT; presence check only
}

serve(async (req) => {
  if (req.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  if (!requireAuth(req)) return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), { status: 401 });
  let body: any = {};
  try { body = await req.json(); } catch {}
  const mode = (String(body?.mode || "weekly").toLowerCase());
  const fmt  = (String(body?.format || "pdf").toLowerCase());
  const bucket = Deno.env.get("REPORTS_BUCKET") || "trenddrop-reports";

  const key = `${mode}/latest.${fmt === "csv" ? "csv" : "pdf"}`;
  const expiresIn = 60 * 60 * 24; // 24h

  try {
    const s = supaService();
    const { data, error } = await s.storage.from(bucket).createSignedUrl(key, expiresIn);
    if (error) throw error;
    return new Response(JSON.stringify({ ok: true, url: data?.signedUrl, key }), { headers: { "content-type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: String(e) }), { status: 500 });
  }
});
// TD-AUTO: END report-links


