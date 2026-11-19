// Nécessite que le script CDN @supabase/supabase-js et config.js soient
// chargés avant celui-ci.
const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
