import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { CLI_TOKEN_TTL_SECONDS, WEB_TOKEN_TTL_SECONDS, mintApiToken } from '@/lib/api-token';

// Returns a backend API token for the signed-in Discord user.
// ?kind=cli returns a long-lived token for the godfather CLI; the default is a short-lived one for this site.
export async function GET(request: NextRequest) {
  const session = await auth();
  const discordId = session?.user?.discordId;
  if (!discordId) {
    return NextResponse.json({ error: 'Not signed in' }, { status: 401 });
  }

  const kind = request.nextUrl.searchParams.get('kind') === 'cli' ? 'cli' : 'web';
  const ttl = kind === 'cli' ? CLI_TOKEN_TTL_SECONDS : WEB_TOKEN_TTL_SECONDS;
  const { token, expiresAt } = mintApiToken(discordId, ttl);

  return NextResponse.json(
    { token, expires_at: expiresAt },
    { headers: { 'Cache-Control': 'no-store' } }
  );
}
