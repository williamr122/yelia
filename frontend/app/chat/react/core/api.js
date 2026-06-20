export async function requestJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    cache: 'no-store',
    headers: { Accept: 'application/json', ...(options.body && !(options.body instanceof FormData) ? {'Content-Type':'application/json'} : {}), ...(options.headers||{}) },
    ...options,
  });
  const raw = await res.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === 'object' ? raw.data : raw;
  if (!res.ok || raw?.ok === false || raw?.success === false) throw new Error(data?.message || raw?.message || data?.error || raw?.error || `HTTP ${res.status}`);
  return data;
}
export const api = {
  get: (u) => requestJson(u),
  post: (u,b) => requestJson(u,{method:'POST', body: JSON.stringify(b||{})}),
  patch: (u,b) => requestJson(u,{method:'PATCH', body: JSON.stringify(b||{})}),
  del: (u) => requestJson(u,{method:'DELETE'}),
  upload: (u, form) => requestJson(u,{method:'POST', body: form, headers: {}}),
};
