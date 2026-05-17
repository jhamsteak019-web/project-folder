# Supabase Setup

1. Run `supabase_schema.sql` in your Supabase SQL editor.
2. Add these environment variables in Vercel:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_TABLE` (optional, defaults to `visitor_logs`)
3. Redeploy the Vercel app.

The app stores visitor logs in Supabase when the environment variables are present. Without them, it falls back to the local in-memory list for development.
