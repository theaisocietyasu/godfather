// Thin wrapper around fetch for calls to the backend API.
// Every request carries a short-lived signed token from /api/auth/token as a Bearer header.

let cachedToken: { token: string; expiresAt: number } | null = null;

async function getApiToken(forceRefresh = false): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (!forceRefresh && cachedToken && cachedToken.expiresAt - now > 60) {
    return cachedToken.token;
  }

  const response = await fetch('/api/auth/token', { cache: 'no-store' });
  if (!response.ok) {
    cachedToken = null;
    throw new Error('Not signed in');
  }
  const data = await response.json();
  cachedToken = { token: data.token, expiresAt: data.expires_at };
  return data.token;
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const send = async (token: string) =>
    fetch(path, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${token}` },
    });

  let response = await send(await getApiToken());
  if (response.status === 401) {
    response = await send(await getApiToken(true));
  }
  return response;
}

export async function apiJson<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await apiFetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.error || data?.detail || `Request failed: ${response.status}`);
  }
  return data as T;
}
