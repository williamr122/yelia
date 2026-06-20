export async function requestJson(url: string, options: RequestInit = {}) {
  const hasJsonBody = Boolean(options.body) && !(options.body instanceof FormData);
  const response = await fetch(url, {
    credentials: 'include',
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
      ...(hasJsonBody ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  const raw = await response.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === 'object' ? raw.data : raw;
  if (!response.ok || raw?.ok === false || raw?.success === false) {
    throw new Error(data?.message || raw?.message || data?.error || raw?.error || `HTTP ${response.status}`);
  }
  return data;
}

export const api = {
  get: (url: string) => requestJson(url),
  post: (url: string, body?: unknown) => requestJson(url, { method: 'POST', body: JSON.stringify(body || {}) }),
};
