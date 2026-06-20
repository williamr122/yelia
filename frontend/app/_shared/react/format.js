export const fmtDate = (v) => v ? new Date(v).toLocaleString('es-EC', {dateStyle:'short', timeStyle:'short'}) : '—';
export const asArray = (d, ...keys) => { for (const k of keys) if (Array.isArray(d?.[k])) return d[k]; return Array.isArray(d) ? d : []; };
