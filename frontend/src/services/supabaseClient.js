import { createClient } from '@supabase/supabase-js';

// Supabase 설정 (백엔드와 동일한 URL 사용)
const supabaseUrl = 'https://orjplexhlzipkjlngoua.supabase.co';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

if (!supabaseAnonKey) {
  throw new Error('REACT_APP_SUPABASE_ANON_KEY 환경 변수가 설정되지 않았습니다.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
}); 