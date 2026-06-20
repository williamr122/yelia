'use client';

import { useEffect, useLayoutEffect, useState } from 'react';

const quickAccess = [
  { label: 'Login admin', href: '/admin/login', icon: 'bi-shield-lock', tone: 'blue' },
  { label: 'Crear admin', href: '/admin/setup', icon: 'bi-person-plus', tone: 'purple' },
  { label: 'Panel admin', href: '/admin', icon: 'bi-speedometer2', tone: 'blue' },
  { label: 'Metricas admin', href: '/admin/metrics', icon: 'bi-graph-up-arrow', tone: 'orange' },
  { label: 'Base de datos', href: '/db', icon: 'bi-database', tone: 'purple' },
  { label: 'Estado', href: '/status', icon: 'bi-activity', tone: 'blue' },
  { label: 'Portal docente', href: '/demo-docente', icon: 'bi-mortarboard', tone: 'green' },
];

const managementFocus = [
  {
    icon: 'bi-person-check',
    title: 'Cuentas y permisos',
    text: 'Crea administradores, revisa docentes, valida solicitudes y controla accesos institucionales.',
  },
  {
    icon: 'bi-database-check',
    title: 'Auditoria de evidencia',
    text: 'Revisa conversaciones, adjuntos, conteos, base de datos y registros que sustentan el prototipo.',
  },
  {
    icon: 'bi-shield-check',
    title: 'Estado del sistema',
    text: 'Confirma backend, PostgreSQL, metricas y salud operativa antes de una demostracion.',
  },
];

export default function DemoClient() {
  const [now, setNow] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'demo ui desktop-pro';
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    setNow(new Date().toLocaleString('es-EC', {
      timeZone: 'America/Guayaquil',
      dateStyle: 'medium',
      timeStyle: 'short',
    }));
  }, []);

  return (
    <div className="wrap yelia-management-home">
      <header className="mgmt-topbar">
        <a className="mgmt-brand" href="/demo">
          <span><i className="bi bi-cpu" /></span>
          <strong>YELIA4AP</strong>
          <small>Portal de gestion</small>
        </a>
        <div className="mgmt-top-actions">
          <span className="mgmt-pill"><i className="bi bi-clock" />{now || 'Hora local'}</span>
          <a className="btn ghost" href="/demo-docente"><i className="bi bi-mortarboard" /> Docente</a>
          <a className="btn ghost" href="/launcher"><i className="bi bi-house" /> Estudiantes</a>
        </div>
      </header>

      <main className="mgmt-layout">
        <section className="mgmt-hero">
          <span className="badge">Portal administrador</span>
          <h1>Control y auditoria del sistema</h1>
          <p>
            Administra YELIA4AP, revisa cuentas, solicitudes docentes, evidencia guardada,
            metricas generales, base de datos y estado operativo.
          </p>
          <div className="chips">
            <span className="chip">Usuarios y permisos</span>
            <span className="chip">Auditoria</span>
            <span className="chip">Estado tecnico</span>
          </div>
          <div className="cta">
            <a className="btn primary xl" href="/admin/login"><i className="bi bi-shield-lock" /> Entrar como admin</a>
            <a className="btn ghost xl" href="/admin"><i className="bi bi-speedometer2" /> Abrir panel admin</a>
          </div>
        </section>

        <aside className="mgmt-side-card">
          <h2>Vista de administrador</h2>
          <p>Control general sin mezclar el seguimiento pedagogico del docente.</p>
          <div className="mgmt-status-list">
            <span><i className="bi bi-check-circle" /> Gestion de cuentas</span>
            <span><i className="bi bi-check-circle" /> Auditoria de chats y adjuntos</span>
            <span><i className="bi bi-check-circle" /> Base de datos y salud del sistema</span>
          </div>
        </aside>
      </main>

      <section className="mgmt-section">
        <div className="sectionTitle">
          <h2>Accesos rapidos</h2>
          <span>Administracion, auditoria y evidencia tecnica</span>
        </div>
        <div className="mgmt-access-grid">
          {quickAccess.map((item) => (
            <a className={`mgmt-access-card tone-${item.tone}`} href={item.href} key={item.href}>
              <span><i className={`bi ${item.icon}`} /></span>
              <strong>{item.label}</strong>
              <small>{item.href}</small>
              <em>Entrar <i className="bi bi-arrow-right" /></em>
            </a>
          ))}
        </div>
      </section>

      <section className="mgmt-section">
        <div className="sectionTitle">
          <h2>Que revisa el administrador</h2>
          <span>Resumen para control, sustentacion y operacion</span>
        </div>
        <div className="mgmt-focus-grid">
          {managementFocus.map((item) => (
            <article className="mgmt-focus-card" key={item.title}>
              <span><i className={`bi ${item.icon}`} /></span>
              <div>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
