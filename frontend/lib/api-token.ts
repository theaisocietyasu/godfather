// Server-only: mints the signed tokens the backend verifies (backend/domains/auth/tokens.py).
// Format: gf1.<base64url(JSON payload)>.<base64url(HMAC-SHA256 of "gf1.<payload>")>
import { createHmac } from 'crypto';

const PREFIX = 'gf1';

export const WEB_TOKEN_TTL_SECONDS = 60 * 60;
export const CLI_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60;

function base64url(data: Buffer | string): string {
  return Buffer.from(data).toString('base64url');
}

export function mintApiToken(discordId: string, ttlSeconds: number): { token: string; expiresAt: number } {
  const secret = process.env.GODFATHER_TOKEN_SECRET;
  if (!secret || secret.length < 32) {
    throw new Error('GODFATHER_TOKEN_SECRET must be set to at least 32 characters');
  }

  const expiresAt = Math.floor(Date.now() / 1000) + ttlSeconds;
  const body = base64url(JSON.stringify({ sub: discordId, exp: expiresAt }));
  const signature = base64url(createHmac('sha256', secret).update(`${PREFIX}.${body}`).digest());
  return { token: `${PREFIX}.${body}.${signature}`, expiresAt };
}
