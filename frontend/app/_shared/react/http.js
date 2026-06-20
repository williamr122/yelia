'use client';

export function getApiPrefix() {
  const raw = String(window.__API_PREFIX__ || '/api').trim() || '/api';
  let prefix = raw.startsWith('/') ? raw : `/${raw}`;
  if (prefix.length > 1 && prefix.endsWith('/')) prefix = prefix.slice(0, -1);
  return prefix;
}

export function apiUrl(url) {
  const prefix = getApiPrefix();
  if (prefix === '/api') return url;
  if (url === '/api' || url.startsWith('/api/')) return prefix + url.slice(4);
  return url;
}

export async function postJson(url, body) {
  const response = await fetch(apiUrl(url), {
    method: 'POST',
    credentials: 'include',
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(body || {}),
  });

  const raw = await response.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === 'object' ? raw.data : raw;
  const okFlag = raw?.ok === true || raw?.success === true || data?.ok === true || data?.success === true;

  return {
    ok: response.ok && okFlag !== false,
    status: response.status,
    raw,
    data,
    message: data?.message || raw?.message || data?.error || raw?.error || '',
  };
}

export function getSafeNext() {
  try {
    const next = new URLSearchParams(window.location.search).get('next') || '';
    return next.trim().startsWith('/') ? next.trim() : '';
  } catch {
    return '';
  }
}
