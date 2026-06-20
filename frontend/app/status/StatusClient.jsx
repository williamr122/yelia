'use client';

import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';

const kpiItems = [
  ['students_total', 'Estudiantes', 'bi-people'],
  ['teachers_total', 'Docentes', 'bi-mortarboard'],
  ['admins_total', 'Admins', 'bi-shield-lock'],
  ['accounts_total', 'Cuentas', 'bi-person-badge'],
  ['conversations_total', 'Conversaciones', 'bi-chat-left-text'],
  ['messages_total', 'Mensajes', 'bi-chat-dots'],
  ['attachments_total', 'Adjuntos', 'bi-paperclip'],
  ['metrics_events_total', 'Eventos metricas', 'bi-graph-up'],
  ['feedback_total', 'Feedback', 'bi-hand-thumbs-up'],
];

function pick(summary, key) {
  const legacy = {
    conversations_total: 'conversations',
    messages_total: 'messages',
    attachments_total: 'attachments',
    metrics_events_total: 'metrics_events',
    feedback_total: 'metrics_feedback',
  };
  return summary?.[key] ?? summary?.[legacy[key]] ?? 0;
}

function Pill({ kind = '', icon = 'bi-hourglass-split', text = 'Cargando...' }) {
  return <span className={`status-pill ${kind}`}><i className={`bi ${icon}`} /> {text}</span>;
}

function KpiCard({ value, label, icon }) {
  return (
    <article className="status-card status-kpi">
      <div>
        <span>{label}</span>
        <b>{value ?? '--'}</b>
      </div>
      <i className={`bi ${icon}`} />
    </article>
  );
}

export default function StatusClient() {
  const [backend, setBackend] = useState({ icon: 'bi-hourglass-split', text: 'Cargando...' });
  const [db, setDb] = useState({ icon: 'bi-hourglass-split', text: 'Cargando...' });
  const [dbEngine, setDbEngine] = useState('');
  const [summary, setSummary] = useState({});
  const [diagnostics, setDiagnostics] = useState(null);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'status-page desktop-pro';
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function readJson(url) {
      const response = await fetch(url, { cache: 'no-store', headers: { Accept: 'application/json' } });
      const raw = await response.json().catch(() => ({}));
      return raw?.data && typeof raw.data === 'object' ? { raw, data: raw.data } : { raw, data: raw };
    }

    async function load() {
      setError('');
      try {
        const { raw, data } = await readJson('/health');
        if (!active) return;
        const okBackend = raw?.ok === true || data?.status === 'ok' || raw?.status === 'ok';
        setBackend(okBackend
          ? { kind: 'ok', icon: 'bi-check-circle', text: 'OK' }
          : { kind: 'bad', icon: 'bi-x-circle', text: 'ERROR' });

        const dbStatus = data?.db || raw?.db || 'unknown';
        setDbEngine(data?.db_engine || raw?.db_engine || '');
        if (dbStatus === 'ok') setDb({ kind: 'ok', icon: 'bi-database-check', text: 'OK' });
        else if (dbStatus === 'missing') setDb({ kind: 'warn', icon: 'bi-database-exclamation', text: 'MISSING' });
        else setDb({ kind: 'bad', icon: 'bi-database-x', text: String(dbStatus || 'ERROR').toUpperCase() });
      } catch {
        if (!active) return;
        setBackend({ kind: 'bad', icon: 'bi-x-circle', text: 'ERROR' });
        setDb({ kind: 'bad', icon: 'bi-database-x', text: 'ERROR' });
        setError('No se pudo leer /health. Revisa que Flask este encendido.');
      }

      try {
        const { data } = await readJson('/api/status/summary');
        if (!active) return;
        setSummary(data?.summary || {});
        setNote(data?.note || '');
      } catch {
        if (active) setError('No se pudo cargar /api/status/summary.');
      }

      try {
        const { data } = await readJson('/api/status/diagnostics');
        if (active) setDiagnostics(data?.diagnostics || null);
      } catch {
        if (active) setDiagnostics(null);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, []);

  const providerText = useMemo(() => {
    const providers = diagnostics?.providers || {};
    return providers.last_used || providers.selected || 'router/local';
  }, [diagnostics]);

  const engineText = dbEngine === 'postgresql' ? 'PostgreSQL' : dbEngine === 'sqlite' ? 'SQLite local' : 'Base de datos';
  const teacherReady = Number(pick(summary, 'students_total') || 0) > 0 || Number(pick(summary, 'conversations_total') || 0) > 0;
  const adminReady = Number(pick(summary, 'accounts_total') || 0) > 0;

  return (
    <main className="status-shell">
      <header className="status-hero">
        <div>
          <span className="status-eyebrow">YELIA4AP</span>
          <h1>Estado del sistema</h1>
          <p>Vista rapida para confirmar que YELIA esta guardando datos y que docente/admin tienen evidencia para revisar.</p>
        </div>
        <nav className="status-actions">
          <a href="/demo"><i className="bi bi-grid-1x2" /> Demo</a>
          <a href="/chat"><i className="bi bi-chat-dots" /> Chat</a>
          <a href="/launcher"><i className="bi bi-rocket-takeoff" /> Launcher</a>
          <a href="/health"><i className="bi bi-heart-pulse" /> Health</a>
        </nav>
      </header>

      {error ? <section className="status-alert">{error}</section> : null}

      <section className="status-grid status-grid-two">
        <article className="status-card">
          <div className="status-card-head">
            <b>Backend</b>
            <Pill {...backend} />
          </div>
          <p>Endpoint <code>/health</code>. Confirma si Flask esta activo y responde JSON.</p>
        </article>
        <article className="status-card">
          <div className="status-card-head">
            <b>Base de datos</b>
            <Pill {...db} />
          </div>
          <p>Motor actual: <b>{engineText}</b>. Debe estar OK para guardar chats, estudiantes, metricas y adjuntos.</p>
        </article>
      </section>

      <section className="status-section">
        <div className="status-section-head">
          <div>
            <h2>Resumen</h2>
            <p>Conteos principales del sistema actual.</p>
          </div>
          <span>Fuente <code>/api/status/summary</code></span>
        </div>
        <div className="status-kpi-grid">
          {kpiItems.map(([key, label, icon]) => (
            <KpiCard key={key} value={pick(summary, key)} label={label} icon={icon} />
          ))}
        </div>
        {note ? <p className="status-note">{note}</p> : null}
      </section>

      <section className="status-section">
        <div className="status-section-head">
          <div>
            <h2>Lectura para docente y admin</h2>
            <p>Senales utiles para saber si el panel ya tiene evidencia real y que revisar primero.</p>
          </div>
          <span>Fuente <code>/api/status/diagnostics</code></span>
        </div>
        <div className="status-kpi-grid">
          <KpiCard value={teacherReady ? 'Con evidencia' : 'Sin actividad'} label="Panel docente" icon="bi-mortarboard" />
          <KpiCard value={adminReady ? 'Con cuentas' : 'Crear cuentas'} label="Panel admin" icon="bi-shield-check" />
          <KpiCard value={diagnostics?.runtime?.recent_messages ?? 0} label="Mensajes ultimas 24h" icon="bi-clock-history" />
          <KpiCard value={providerText} label="IA configurada" icon="bi-cpu" />
        </div>
      </section>
    </main>
  );
}
