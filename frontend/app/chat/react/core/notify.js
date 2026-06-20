export function notify(message, type='info') {
  const text = String(message || '');
  if (!text) return;
  let host = document.getElementById('yelia-toast-host');
  if (!host) { host = document.createElement('div'); host.id='yelia-toast-host'; host.style.cssText='position:fixed;right:16px;bottom:16px;z-index:99999;display:grid;gap:8px;max-width:360px'; document.body.appendChild(host); }
  const el = document.createElement('div');
  el.textContent = text;
  el.style.cssText = `padding:10px 12px;border-radius:14px;color:white;background:${type==='error'?'#dc3545':type==='success'?'#198754':'#0d6efd'};box-shadow:0 12px 30px rgba(0,0,0,.25);font-weight:700`;
  host.appendChild(el); setTimeout(()=>el.remove(), 3500);
}
