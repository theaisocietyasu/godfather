// Thin wrapper around fetch for calls to this app's own /api routes.
// Handles the X-Discord-User-ID header convention used across the backend proxy routes.

export interface ApiFetchOptions extends RequestInit {
  discordId?: string;
}

export async function apiFetch(path: string, options: ApiFetchOptions = {}): Promise<Response> {
  const { discordId, headers, ...rest } = options;
  return fetch(path, {
    ...rest,
    headers: {
      ...(discordId ? { 'X-Discord-User-ID': discordId } : {}),
      ...headers,
    },
  });
}

export async function apiJson<T = unknown>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const response = await apiFetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.error || data?.detail || `Request failed: ${response.status}`);
  }
  return data as T;
}
