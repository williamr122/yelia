'use client';

import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

type AnyObject = Record<string, any>;

const adminSections = [
  ['resumen', 'Resumen', 'dashboard'],
  ['auditoria', 'Auditoria', 'shield'],
  ['usuarios', 'Usuarios', 'users'],
  ['sistema', 'Sistema', 'activity'],
  ['evidencia', 'Evidencia', 'database'],
] as const;

function numberValue(value: any, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function fmt(value: any) {
  if (value === null || value === undefined || value === '') return '--';
  if (typeof value === 'number') return new Intl.NumberFormat('es-EC').format(value);
  return String(value);
}

function Icon({ name }: { name: string }) {
  const common = {
    width: 18,
    height: 18,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };
  const paths: Record<string, ReactNode> = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="2" /><rect x="14" y="3" width="7" height="7" rx="2" /><rect x="3" y="14" width="7" height="7" rx="2" /><rect x="14" y="14" width="7" height="7" rx="2" /></>,
    shield: <><path d="M12 3l7 3v5c0 4.5-2.8 8.2-7 10-4.2-1.8-7-5.5-7-10V6z" /><path d="M9 12l2 2 4-5" /></>,
    users: <><circle cx="9" cy="8" r="3" /><path d="M3.5 20c.8-3.4 2.7-5 5.5-5s4.7 1.6 5.5 5" /><circle cx="17" cy="9" r="2.4" /><path d="M15.8 15.2c2.1.4 3.6 1.9 4.2 4.8" /></>,
    activity: <><path d="M3 12h4l2-6 4 12 2-6h6" /></>,
    database: <><ellipse cx="12" cy="5" rx="7" ry="3" /><path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5" /><path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" /></>,
  };
  return <svg {...common}>{paths[name] || paths.dashboard}</svg>;
}

function unwrapData(payload: AnyObject | null) {
  return payload?.data && typeof payload.data === 'object' ? payload.data : payload || {};
}

async function getJson(url: string) {
  const res = await fetch(url, { cache: 'no-store', credentials: 'include' });
  if (!res.ok) return null;
  return res.json();
}

function Kpi({ label, value, note, icon }: { label: string; value: any; note: string; icon: string }) {
  return (
    <article className="metrics-kpi">
      <span className="metrics-kpi-label"><i className={`bi ${icon}`} /> {label}</span>
      <strong className="metrics-kpi-value">{fmt(value)}</strong>
      <span className="metrics-kpi-note">{note}</span>
    </article>
  );
}

function BarList({ title, rows, labelKey, valueKey }: { title: string; rows: AnyObject[]; labelKey: string; valueKey: string }) {
  const max = Math.max(1, ...rows.map((row) => numberValue(row[valueKey])));
  return (
    <article className="metrics-panel">
      <h3>{title}</h3>
      {rows.length ? (
        <div className="metrics-mini-bars">
          {rows.map((row, index) => {
            const label = row[labelKey] || row.tema || row.topic || 'Sin dato';
            const value = numberValue(row[valueKey]);
            return (
              <div className="metrics-mini-row" key={`${label}-${index}`}>
                <span title={label}>{label}</span>
                <div><i style={{ width: `${Math.max(8, (value / max) * 100)}%` }} /></div>
                <strong>{value}</strong>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="metrics-empty">Sin datos para esta vista.</div>
      )}
    </article>
  );
}

function LogoMark() {
  return (
    <span className="metrics-logo-mark" aria-hidden="true"><LogoGlyph /></span>
  );
}

function MenuGlyph() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </svg>
  );
}

function LogoGlyph() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9L12 3Z" />
      <path d="M12 7.2 16.2 9.6v4.8L12 16.8l-4.2-2.4V9.6L12 7.2Z" />
      <path d="M12 3v4.2M20 7.5l-3.8 2.1M4 7.5l3.8 2.1M12 16.8V21" />
    </svg>
  );
}

export default function AdminMetricsClient() {
  const [collapsed, setCollapsed] = useState(false);
  const [summary, setSummary] = useState<AnyObject>({});
  const [diagnostics, setDiagnostics] = useState<AnyObject>({});
  const [metrics, setMetrics] = useState<AnyObject>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState<(typeof adminSections)[number][0]>('resumen');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([
      getJson('/api/status/summary'),
      getJson('/api/status/diagnostics'),
      getJson('/api/metrics'),
    ]).then(([statusData, diagnosticData, metricData]) => {
      if (!alive) return;
      const statusPayload = unwrapData(statusData);
      const diagnosticPayload = unwrapData(diagnosticData);
      setSummary(statusPayload.summary || {});
      setDiagnostics(diagnosticPayload.diagnostics || {});
      const metricPayload = metricData?.data?.metrics || metricData?.metrics || metricData || {};
      setMetrics(metricPayload);
      setError(metricData ? '' : 'No se pudo leer /api/metrics. Si no hay sesion admin, entra desde /admin/login.');
    }).catch(() => {
      if (!alive) return;
      setError('No se pudo cargar la auditoria administrativa.');
    }).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  const topThemes = useMemo(() => metrics?.top_temas || metrics?.academic?.topics || [], [metrics]);
  const providers = diagnostics?.providers || {};
  const runtime = diagnostics?.runtime || {};

  return (
    <div className={`metrics-app metrics-admin-app ${collapsed ? 'is-collapsed' : ''}`}>
      <aside className="metrics-sidebar">
        <div className="metrics-brand">
          <button className="metrics-icon-button metrics-brand-toggle" type="button" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Mostrar menu' : 'Ocultar menu'} title={collapsed ? 'Mostrar menu' : 'Ocultar menu'}><MenuGlyph /></button>
          <LogoMark />
          <div><strong>YELIA4AP</strong><span>Metricas admin</span></div>
        </div>
        <nav className="metrics-nav" aria-label="Metricas admin">
          {adminSections.map(([id, label, icon]) => (
            <button className={activeSection === id ? 'is-active' : ''} type="button" key={id} onClick={() => setActiveSection(id)}>
              <span><Icon name={icon} /></span>
              <strong>{label}</strong>
            </button>
          ))}
        </nav>
        <div className="metrics-sidebar-footer">
          <span>Estado</span>
          <strong>{error ? 'Revisar' : 'OK'}</strong>
        </div>
      </aside>

      <div className="metrics-content">
        <header className="metrics-topbar">
          <div>
            <h1>Metricas administrativas</h1>
            <p>Auditoria general de usuarios, cuentas, conversaciones, adjuntos, rendimiento y salud del sistema.</p>
          </div>
          <div className="metrics-top-actions">
            <a className="metrics-pill" href="/admin"><i className="bi bi-speedometer2" /> Panel admin</a>
            <a className="metrics-pill" href="/metricas"><i className="bi bi-grid-1x2" /> Metricas globales</a>
            <button type="button" onClick={() => window.location.reload()}>Actualizar</button>
          </div>
        </header>

        <main className="metrics-main">
          {error ? <div className="metrics-empty">{error}</div> : null}
          {activeSection === 'resumen' ? <>
            <header className="metrics-section-head">
              <div><span className="metrics-section-kicker">ADMIN</span><h2>Resumen de control</h2></div>
              <span className="metrics-section-meta">{loading ? 'Cargando...' : 'Datos actuales'}</span>
            </header>
            <div className="metrics-kpi-grid">
              <Kpi label="Estudiantes" value={summary.students_total ?? metrics?.academic?.student_count} note="Registrados o con actividad" icon="bi-people" />
              <Kpi label="Cuentas" value={summary.accounts_total} note="Admin y docentes" icon="bi-person-badge" />
              <Kpi label="Conversaciones" value={summary.conversations_total ?? metrics.total_conversaciones} note="Evidencia guardada" icon="bi-chat-dots" />
              <Kpi label="Mensajes" value={summary.messages_total ?? metrics.total_mensajes} note="Usuario y asistente" icon="bi-chat-left-text" />
              <Kpi label="Adjuntos" value={summary.attachments_total ?? 0} note="Archivos registrados" icon="bi-paperclip" />
              <Kpi label="Eventos" value={summary.metrics_events_total ?? 0} note="Metricas tecnicas" icon="bi-activity" />
              <Kpi label="Latencia media" value={runtime.avg_chat_latency_ms ? `${runtime.avg_chat_latency_ms} ms` : metrics.avg_latency_ms ? `${metrics.avg_latency_ms} ms` : '--'} note="Respuesta de chat" icon="bi-speedometer" />
              <Kpi label="Consultas resueltas" value={metrics?.usabilidad?.tareas_completadas_percent != null ? `${metrics.usabilidad.tareas_completadas_percent}%` : '--'} note="Con usuario y respuesta" icon="bi-check2-circle" />
            </div>
          </> : null}

          {activeSection === 'auditoria' ? <div className="metrics-grid two">
            <BarList title="Temas con mayor uso" rows={topThemes} labelKey="tema" valueKey="total" />
            <article className="metrics-panel">
              <h3>Auditoria operativa</h3>
              <div className="metrics-kpi-grid compact">
                <Kpi label="Feedback" value={summary.feedback_total ?? `${metrics?.feedback?.up || 0}/${metrics?.feedback?.down || 0}`} note="Valoraciones" icon="bi-hand-thumbs-up" />
                <Kpi label="Abandono" value={metrics?.usabilidad?.abandono_percent != null ? `${metrics.usabilidad.abandono_percent}%` : '--'} note="Sin continuidad" icon="bi-box-arrow-right" />
              </div>
            </article>
          </div> : null}

          {activeSection === 'usuarios' ? <article className="metrics-panel">
            <h3>Usuarios y roles</h3>
            <div className="metrics-kpi-grid compact">
              <Kpi label="Admins" value={summary.admins_total} note="Cuentas admin" icon="bi-shield-lock" />
              <Kpi label="Docentes" value={summary.teachers_total} note="Cuentas docentes" icon="bi-mortarboard" />
              <Kpi label="Cuentas" value={summary.accounts_total} note="Total de accesos" icon="bi-person-badge" />
              <Kpi label="Estudiantes" value={summary.students_total} note="Cuentas estudiantiles" icon="bi-people" />
            </div>
          </article> : null}

          {activeSection === 'sistema' ? <article className="metrics-panel">
            <h3>Estado del sistema</h3>
            <div className="metrics-mini-bars">
              <div className="metrics-mini-row"><span>Proveedor IA</span><strong>{providers.selected || 'router'}</strong></div>
              <div className="metrics-mini-row"><span>Entorno</span><strong>{diagnostics.environment || 'development'}</strong></div>
              <div className="metrics-mini-row"><span>Rate limit</span><strong>{diagnostics?.rate_limit?.storage_uri || 'memory'}</strong></div>
              <div className="metrics-mini-row"><span>Mensajes 24h</span><strong>{runtime.recent_messages ?? '--'}</strong></div>
            </div>
          </article> : null}

          {activeSection === 'evidencia' ? <article className="metrics-panel">
            <h3>Evidencia para sustentacion</h3>
            <p className="metrics-muted">Este panel es para comprobar volumen, seguridad operativa, datos guardados y salud. El detalle pedagogico queda separado en metricas docentes.</p>
            <div className="metrics-kpi-grid compact">
              <Kpi label="Conversaciones" value={summary.conversations_total} note="Chats guardados" icon="bi-chat-dots" />
              <Kpi label="Adjuntos" value={summary.attachments_total} note="Archivos visibles" icon="bi-paperclip" />
            </div>
          </article> : null}
        </main>
      </div>
    </div>
  );
}
