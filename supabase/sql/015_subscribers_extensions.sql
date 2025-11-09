-- TD-AUTO: BEGIN subscribers-extensions
DO $$ BEGIN
  ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'basic';
EXCEPTION WHEN others THEN
  -- TD-AUTO: ignore duplicate/exists errors
  NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
EXCEPTION WHEN others THEN
  NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS renewal_status TEXT;
EXCEPTION WHEN others THEN
  NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS source TEXT;
EXCEPTION WHEN others THEN
  NULL;
END $$;

CREATE OR REPLACE VIEW v_active_subscribers AS
SELECT * FROM subscribers
WHERE revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now());
-- TD-AUTO: END subscribers-extensions


