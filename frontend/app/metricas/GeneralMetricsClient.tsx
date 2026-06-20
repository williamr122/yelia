'use client';

import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

type AnyObject = Record<string, any>;

const sections = [
  ['vision', 'Vision general', 'dashboard'],
  ['flujo', 'Flujo fase 2', 'flow'],
  ['estudiante', 'Estudiante', 'student'],
  ['docente', 'Docente', 'teacher'],
  ['sistema', 'Sistema', 'activity'],
] as const;

async function getJson(url: string) {
  const res = await fetch(url, { cache: 'no-store', credentials: 'include' });
  if (!res.ok) return null;
  return res.json();
}

function unwrapData(payload: AnyObject | null) {
  return payload?.data && typeof payload.data === 'object' ? payload.data : payload || {};
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
    flow: <><circle cx="6" cy="6" r="3" /><circle cx="18" cy="18" r="3" /><path d="M9 6h3a6 6 0 0 1 6 6v3" /><path d="M15 18h-3a6 6 0 0 1-6-6V9" /></>,
    student: <><circle cx="12" cy="8" r="4" /><path d="M4 21c1.2-4.2 3.9-6.3 8-6.3s6.8 2.1 8 6.3" /></>,
    teacher: <><path d="M3 7l9-4 9 4-9 4z" /><path d="M7 10v5c1.5 1.5 8.5 1.5 10 0v-5" /><path d="M21 8v6" /></>,
    activity: <><path d="M3 12h4l2-6 4 12 2-6h6" /></>,
  };
  return <svg {...common}>{paths[name] || paths.dashboard}</svg>;
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

function FlowCard({ number, title, text, state }: { number: string; title: string; text: string; state: string }) {
  return (
    <article className="metrics-flow-card">
      <span>{number}</span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
        <em>{state}</em>
      </div>
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

export default function GeneralMetricsClient() {
  const [collapsed, setCollapsed] = useState(false);
  const [summary, setSummary] = useState<AnyObject>({});
  const [diagnostics, setDiagnostics] = useState<AnyObject>({});
  const [metrics, setMetrics] = useState<AnyObject>({});
  const [routes, setRoutes] = useState<AnyObject>({});
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<(typeof sections)[number][0]>('vision');

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([
      getJson('/api/status/summary'),
      getJson('/api/status/diagnostics'),
      getJson('/api/metrics'),
      getJson('/api/teacher/learning-routes?limit=120'),
    ]).then(([statusData, diagnosticData, metricData, routeData]) => {
      if (!alive) return;
      const statusPayload = unwrapData(statusData);
      const diagnosticPayload = unwrapData(diagnosticData);
      const metricPayload = metricData?.data?.metrics || metricData?.metrics || metricData || {};
      const routePayload = routeData?.summary
        ? routeData
        : (metricPayload?.academic?.learning_routes || {});
      setSummary(statusPayload.summary || {});
      setDiagnostics(diagnosticPayload.diagnostics || {});
      setMetrics(metricPayload);
      setRoutes(routePayload);
    }).finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, []);

  const routeSummary = routes?.summary || {};
  const provider = diagnostics?.providers?.selected || 'router';

  return (
    <div className={`metrics-app metrics-general-app ${collapsed ? 'is-collapsed' : ''}`}>
      <aside className="metrics-sidebar">
        <div className="metrics-brand">
          <button className="metrics-icon-button metrics-brand-toggle" type="button" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Mostrar menu' : 'Ocultar menu'} title={collapsed ? 'Mostrar menu' : 'Ocultar menu'}><MenuGlyph /></button>
          <LogoMark />
          <div><strong>YELIA4AP</strong><span>Metricas globales</span></div>
        </div>
        <nav className="metrics-nav" aria-label="Metricas generales">
          {sections.map(([id, label, icon]) => (
            <button className={activeSection === id ? 'is-active' : ''} type="button" key={id} onClick={() => setActiveSection(id)}>
              <span><Icon name={icon} /></span>
              <strong>{label}</strong>
            </button>
          ))}
        </nav>
        <div className="metrics-sidebar-footer">
          <span>Estado</span>
          <strong>{loading ? 'Cargando' : 'OK'}</strong>
        </div>
      </aside>

      <div className="metrics-content">
        <header className="metrics-topbar">
          <div>
            <h1>Metricas globales del prototipo</h1>
            <p>Vista general para comprobar que fase 2 conecta estudiante, docente, admin, ruta por unidades y evidencia guardada.</p>
          </div>
          <div className="metrics-top-actions">
            <a className="metrics-pill" href="/launcher"><i className="bi bi-house" /> Estudiante</a>
            <a className="metrics-pill" href="/demo-docente"><i className="bi bi-mortarboard" /> Docente</a>
            <a className="metrics-pill" href="/admin"><i className="bi bi-shield-lock" /> Admin</a>
          </div>
        </header>

        <main className="metrics-main">
          {activeSection === 'vision' ? <>
            <header className="metrics-section-head">
              <div><span className="metrics-section-kicker">FASE 2</span><h2>Estado general del sistema</h2></div>
              <span className="metrics-section-meta">{loading ? 'Cargando...' : 'Datos visibles'}</span>
            </header>
            <div className="metrics-kpi-grid">
              <Kpi label="Estudiantes" value={summary.students_total ?? metrics?.academic?.student_count} note="Con cuenta o actividad" icon="bi-people" />
              <Kpi label="Conversaciones" value={summary.conversations_total ?? metrics.total_conversaciones} note="Chats guardados" icon="bi-chat-dots" />
              <Kpi label="Rutas registradas" value={routeSummary.students} note="Unidad 1 a Unidad 4" icon="bi-map" />
              <Kpi label="Promedio ruta" value={routeSummary.avg_progress != null ? `${routeSummary.avg_progress}%` : '--'} note="Avance modular" icon="bi-bar-chart" />
              <Kpi label="Mensajes" value={summary.messages_total ?? metrics.total_mensajes} note="Usuario y YELIA" icon="bi-chat-left-text" />
              <Kpi label="Proveedor IA" value={provider} note="Router activo" icon="bi-cpu" />
            </div>
          </> : null}

          {activeSection === 'flujo' ? <section className="metrics-panel">
            <h3>Flujo fase 2</h3>
            <div className="metrics-flow-grid">
              <FlowCard number="1" title="Registro y diagnostico" text="Alias, clave, ciclo, estado y 5 preguntas iniciales." state="Base del estudiante" />
              <FlowCard number="2" title="Nivel detectado" text="YELIA adapta explicacion, ejemplos y dificultad." state="Sin conocimientos, basico, intermedio o avanzado" />
              <FlowCard number="3" title="Ruta por unidades" text="Unidad 1 a Unidad 4 con leccion, practica y quiz." state="Progreso modular" />
              <FlowCard number="4" title="Cierre y evidencia" text="Examen final, mapa de calor, progreso y seguimiento docente." state="Sustentacion" />
            </div>
          </section> : null}

          {activeSection === 'estudiante' ? <article className="metrics-panel">
            <h3>Vista estudiante</h3>
            <p className="metrics-muted">Debe entrar por launcher/diagnostico, consultar dudas en chat, abrir ruta, tomar lecciones y revisar progreso personal.</p>
            <div className="metrics-link-row">
              <a href="/launcher">Launcher</a>
              <a href="/diagnostico">Diagnostico</a>
              <a href="/ruta">Ruta</a>
              <a href="/progreso">Progreso</a>
            </div>
          </article> : null}

          {activeSection === 'docente' ? <article className="metrics-panel">
            <h3>Vista docente</h3>
            <p className="metrics-muted">Debe revisar estudiantes, chats agrupados, sintesis docente, recomendaciones y avance por unidades.</p>
            <div className="metrics-kpi-grid compact">
              <Kpi label="Panel docente" value="Activo" note="Seguimiento academico" icon="bi-mortarboard" />
              <Kpi label="Metricas docentes" value="Separadas" note="Sin mezclar admin" icon="bi-bar-chart" />
            </div>
            <div className="metrics-link-row">
              <a href="/teacher">Panel</a>
              <a href="/teacher#chats">Chats</a>
              <a href="/teacher#synthesis">Sintesis</a>
              <a href="/teacher/metrics">Metricas</a>
            </div>
          </article> : null}

          {activeSection === 'sistema' ? <article className="metrics-panel">
            <h3>Lectura rapida del sistema</h3>
            <p className="metrics-muted">Este panel general no reemplaza el detalle docente ni la auditoria admin. Sirve para ver si el prototipo completo esta conectado y listo para demostrar el flujo.</p>
            <div className="metrics-kpi-grid compact">
              <Kpi label="Entorno" value={diagnostics.environment || 'development'} note="Configuracion activa" icon="bi-activity" />
              <Kpi label="Rate limit" value={diagnostics?.rate_limit?.storage_uri || 'memory'} note="Almacenamiento de limites" icon="bi-speedometer" />
            </div>
          </article> : null}
        </main>
      </div>
    </div>
  );
}
