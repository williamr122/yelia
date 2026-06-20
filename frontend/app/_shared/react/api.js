'use client';

export async function requestJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
      ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });
  const raw = await res.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === 'object' ? raw.data : raw;
  if (!res.ok || raw?.ok === false || raw?.success === false) {
    throw new Error(data?.message || raw?.message || data?.error || raw?.error || `HTTP ${res.status}`);
  }
  return data;
}

export const api = {
  get: (url) => requestJson(url),
  post: (url, body) => requestJson(url, { method: 'POST', body: JSON.stringify(body || {}) }),
  patch: (url, body) => requestJson(url, { method: 'PATCH', body: JSON.stringify(body || {}) }),
  del: (url) => requestJson(url, { method: 'DELETE' }),
  upload: (url, form) => requestJson(url, { method: 'POST', body: form, headers: {} }),
};

export function formatNumber(value, digits) {
  if (value === null || value === undefined || value === '') return '--';
  const n = Number(value);
  if (Number.isNaN(n)) return '--';
  return typeof digits === 'number' ? n.toFixed(digits) : String(n);
}
