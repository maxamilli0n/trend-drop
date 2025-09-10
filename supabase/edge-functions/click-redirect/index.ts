// deno-lint-ignore-file no-explicit-any
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

serve(async (req) => {
  try{
    const urlObj = new URL(req.url);
    const target = urlObj.searchParams.get("url");
    if(!target){
      return new Response("missing url", { status: 400 });
    }
    await supabase.from("clicks").insert({ product_url: target });
    return Response.redirect(target, 302);
  }catch(e){
    return new Response("error", { status: 500 });
  }
});


