'use client';

import { useEffect, useMemo, useState } from 'react';

type AnyObject = Record<string, any>;

const teacherSections = [
  ['resumen', 'Resumen', 'bi-grid-1x2'],
  ['estudiantes', 'Estudiantes', 'bi-people'],
  ['temas', 'Temas', 'bi-book'],
  ['ruta', 'Ruta', 'bi-map'],
  ['acciones', 'Acciones', 'bi-stars'],
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

function displayStudentName(value: string) {
  const raw = String(value || 'Estudiante');
  if (raw.startsWith('GUEST-')) return `Invitado ${raw.slice(6).replace(/[-_]+/g, ' ')}`;
  if (raw.startsWith('Anon-')) return `Estudiante anonimo ${raw.slice(5, 11)}`;
  return raw;
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

function Progress({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, numberValue(value)));
  return <div className="metrics-progress"><span style={{ width: `${safe}%` }} /></div>;
}

function TopicBars({ rows }: { rows: AnyObject[] }) {
  const max = Math.max(1, ...rows.map((row) => numberValue(row.n ?? row.total)));
  if (!rows.length) return <div className="metrics-empty">Aun no hay temas suficientes.</div>;
  return (
    <div className="metrics-mini-bars">
      {rows.map((row, index) => {
        const label = row.tema || row.topic || 'Sin tema';
        const value = numberValue(row.n ?? row.total);
        return (
          <div className="metrics-mini-row" key={`${label}-${index}`}>
            <span title={label}>{label}</span>
            <div><i style={{ width: `${Math.max(8, (value / max) * 100)}%` }} /></div>
            <strong>{value}</strong>
          </div>
        );
      })}
    </div>
  );
}

function LogoMark() {
  return (
    <span className="metrics-logo-mark" aria-hidden="true">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9L12 3Z" />
        <path d="M12 7.2 16.2 9.6v4.8L12 16.8l-4.2-2.4V9.6L12 7.2Z" />
        <path d="M12 3v4.2M20 7.5l-3.8 2.1M4 7.5l3.8 2.1M12 16.8V21" />
      </svg>
    </span>
  );
}

export default function TeacherMetricsClient() {
  const [collapsed, setCollapsed] = useState(false);
  const [dashboard, setDashboard] = useState<AnyObject>({});
  const [routes, setRoutes] = useState<AnyObject>({});
  const [students, setStudents] = useState<AnyObject[]>([]);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    Promise.all([
      getJson('/api/teacher/dashboard?days=30'),
      getJson('/api/teacher/learning-routes?limit=120'),
      getJson('/api/teacher/students?limit=120'),
    ]).then(([dashboardData, routeData, studentData]) => {
      if (!alive) return;
      setDashboard(dashboardData || {});
      setRoutes(routeData || {});
      const studentItems = studentData?.items || studentData?.students || [];
      setStudents(Array.isArray(studentItems) ? studentItems : []);
      setError(dashboardData ? '' : 'No se pudo leer el panel docente. Entra con /teacher/login para ver datos reales.');
    }).catch(() => {
      if (!alive) return;
      setError('No se pudo cargar la vista docente.');
    });
    return () => { alive = false; };
  }, []);

  const routeItems: AnyObject[] = useMemo(() => Array.isArray(routes.items) ? routes.items : [], [routes]);
  const routeSummary = routes.summary || {};
  const topTopics: AnyObject[] = useMemo(() => Array.isArray(dashboard.top_temas) ? dashboard.top_temas : [], [dashboard]);
  const selectedRoute = routeItems.find((item) => item.usuario === selected) || routeItems[0] || {};
  const visibleRoutes = routeItems.slice(0, 8);

  return (
    <div className={`metrics-app metrics-teacher-app ${collapsed ? 'is-collapsed' : ''}`}>
      <aside className="metrics-sidebar">
        <div className="metrics-brand">
          <button className="metrics-icon-button" type="button" onClick={() => setCollapsed(!collapsed)} aria-label="Menu"><i className="bi bi-list" /></button>
          <LogoMark />
          <div><strong>YELIA4AP</strong><span>Metricas docentes</span></div>
        </div>
        <nav className="metrics-nav" aria-label="Metricas docentes">
          {teacherSections.map(([id, label, icon]) => (
            <a href={`#${id}`} key={id}>
              <span><i className={`bi ${icon}`} /></span>
              <strong>{label}</strong>
            </a>
          ))}
        </nav>
        <div className="metrics-sidebar-footer">
          <span>Vista</span>
          <strong>Docente</strong>
        </div>
      </aside>

      <main className="metrics-main">
        <header className="metrics-topbar">
          <div>
            <h1>Metricas docentes</h1>
            <p>Seguimiento academico: estudiantes, temas trabajados, ruta por unidades y acciones pedagogicas.</p>
          </div>
          <div className="metrics-top-actions">
            <a className="metrics-pill" href="/teacher"><i className="bi bi-easel2" /> Panel docente</a>
            <button type="button" onClick={() => window.location.reload()}>Actualizar</button>
          </div>
        </header>

        <section className="metrics-content">
          {error ? <div className="metrics-empty">{error}</div> : null}
          <header className="metrics-section-head" id="resumen">
            <div><span className="metrics-section-kicker">DOCENTE</span><h2>Resumen pedagogico</h2></div>
            <span className="metrics-section-meta">Ultimos registros academicos</span>
          </header>

          <div className="metrics-kpi-grid">
            <Kpi label="Estudiantes activos" value={dashboard?.kpis?.active_students ?? routeSummary.students} note="Con evidencia de uso" icon="bi-people" />
            <Kpi label="Conversaciones" value={dashboard?.kpis?.conversations} note="Chats de aprendizaje" icon="bi-chat-dots" />
            <Kpi label="Rutas activas" value={routeSummary.active} note="Avanzan unidades" icon="bi-map" />
            <Kpi label="Rutas completadas" value={routeSummary.completed} note="Evaluacion final aprobada" icon="bi-patch-check" />
            <Kpi label="Promedio de avance" value={routeSummary.avg_progress != null ? `${routeSummary.avg_progress}%` : '--'} note="Unidad 1 a Unidad 4" icon="bi-bar-chart" />
            <Kpi label="Adjuntos" value={dashboard?.kpis?.attachments} note="Evidencia entregada" icon="bi-paperclip" />
          </div>

          <div className="metrics-grid two" id="estudiantes">
            <article className="metrics-panel">
              <h3>Estudiantes con ruta</h3>
              <div className="metrics-student-list">
                {visibleRoutes.length ? visibleRoutes.map((item) => (
                  <button
                    type="button"
                    className={`metrics-student-card ${selectedRoute.usuario === item.usuario ? 'is-selected' : ''}`}
                    key={item.usuario}
                    onClick={() => setSelected(item.usuario)}
                  >
                    <strong>{displayStudentName(item.display_name || item.usuario)}</strong>
                    <span>Unidad {item.current_unit || 1} - {item.completed_units || 0}/4 completadas</span>
                    <Progress value={item.progress || 0} />
                  </button>
                )) : <div className="metrics-empty">Aun no hay rutas registradas.</div>}
              </div>
            </article>

            <article className="metrics-panel" id="ruta">
              <h3>Detalle del estudiante</h3>
              {selectedRoute.usuario ? (
                <>
                  <div className="metrics-detail-title">
                    <strong>{displayStudentName(selectedRoute.display_name || selectedRoute.usuario)}</strong>
                    <span>{selectedRoute.progress || 0}%</span>
                  </div>
                  <Progress value={selectedRoute.progress || 0} />
                  <div className="metrics-unit-row">
                    {[1, 2, 3, 4].map((unit) => (
                      <span key={unit} className={unit <= (selectedRoute.completed_units || 0) ? 'done' : unit === selectedRoute.current_unit ? 'active' : ''}>U{unit}</span>
                    ))}
                  </div>
                  <p className="metrics-muted">{selectedRoute.route_completed ? 'Ruta completada con evaluacion final.' : 'Necesita seguimiento por unidad antes del cierre final.'}</p>
                </>
              ) : (
                <div className="metrics-empty">Selecciona un estudiante.</div>
              )}
            </article>
          </div>

          <div className="metrics-grid two" id="temas">
            <article className="metrics-panel">
              <h3>Temas mas trabajados</h3>
              <p className="metrics-muted">Sirve para saber que dudas se repiten y preparar refuerzo.</p>
              <TopicBars rows={topTopics} />
            </article>
            <article className="metrics-panel" id="acciones">
              <h3>Lectura docente</h3>
              <div className="metrics-action-list">
                <article>
                  <span>1. Recursos</span>
                  <strong>Enviar lectura, guia o video segun el tema dominante.</strong>
                </article>
                <article>
                  <span>2. Retroalimentacion</span>
                  <strong>Revisar dudas repetidas y pedir ejemplo aplicado.</strong>
                </article>
                <article>
                  <span>3. Adaptacion</span>
                  <strong>Ajustar nivel si el estudiante no avanza en quiz o unidad.</strong>
                </article>
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
