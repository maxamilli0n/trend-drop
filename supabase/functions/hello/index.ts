// TD-AUTO: BEGIN hello
// Minimal Supabase Edge Function using Deno.serve
function json(s: number, b: unknown) {
  return new Response(JSON.stringify(b), { status: s, headers: { "content-type": "application/json" } });
}

console.log("[hello] loaded");

Deno.serve((_req: Request) => {
  return json(200, { ok: true, name: "hello", ts: new Date().toISOString() });
});
// TD-AUTO: END hello


