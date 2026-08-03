import { apiJson } from '@/lib/api-client';

export interface VerifyResult {
  success: boolean;
  is_admin: boolean;
  error?: string;
}

export async function verifyDiscordUser(discordUserId: string): Promise<VerifyResult> {
  return apiJson<VerifyResult>('/api/auth/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ discord_user_id: discordUserId }),
  });
}
