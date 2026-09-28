import { apiJson } from '@/lib/api-client';

export interface MeResult {
  success: boolean;
  discord_user_id: string;
  is_admin: boolean;
}

// Confirms the signed-in user is in the Discord server and reports whether they are an admin.
export async function fetchMe(): Promise<MeResult> {
  return apiJson<MeResult>('/api/me');
}

// Long-lived token the user pastes into the godfather CLI.
export async function fetchCliToken(): Promise<string> {
  const response = await fetch('/api/auth/token?kind=cli', { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to generate CLI token');
  const data = await response.json();
  return data.token;
}
