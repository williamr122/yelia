'use client';

import { useEffect, useLayoutEffect, useState } from 'react';

const teacherAccess = [
  { label: 'Login docente', href: '/teacher/login', icon: 'bi-mortarboard', tone: 'green' },
  { label: 'Panel docente', href: '/teacher', icon: 'bi-easel2', tone: 'green' },
  { label: 'Estudiantes', href: '/teacher#students', icon: 'bi-people', tone: 'blue' },
  { label: 'Chats por estudiante', href: '/teacher#chats', icon: 'bi-chat-dots', tone: 'purple' },
  { label: 'Sintesis docente', href: '/teacher#synthesis', icon: 'bi-stars', tone: 'orange' },
  { label: 'Ruta academica', href: '/teacher#route', icon: 'bi-map', tone: 'green' },
  { label: 'Metricas academicas', href: '/teacher/metrics', icon: 'bi-graph-up-arrow', tone: 'blue' },
];

const teacherFocus = [
  {
    icon: 'bi-person-lines-fill',
    title: 'Seguimiento por estudiante',
    text: 'Consulta quien uso YELIA, que temas trabajo, conversaciones recientes y estado academico.',
  },
  {
    icon: 'bi-stars',
    title: 'Sintesis y acciones',
    text: 'Genera recomendaciones, retroalimentacion y adaptacion para que lleguen al perfil del estudiante.',
  },
  {
    icon: 'bi-map',
    title: 'Ruta por unidades',
    text: 'Revisa Unidad 1 a Unidad 4, quiz, evaluacion final y avance modular de cada estudiante.',
  },
];

export default function TeacherPortalClient() {
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
        <a className="mgmt-brand" href="/demo-docente">
          <span><i className="bi bi-mortarboard" /></span>
          <strong>YELIA4AP</strong>
          <small>Portal docente</small>
        </a>
        <div className="mgmt-top-actions">
          <span className="mgmt-pill"><i className="bi bi-clock" />{now || 'Hora local'}</span>
          <a className="btn ghost" href="/launcher"><i className="bi bi-house" /> Estudiantes</a>
        </div>
      </header>

      <main className="mgmt-layout">
        <section className="mgmt-hero">
          <span className="badge">Seguimiento docente</span>
          <h1>Control academico del aprendizaje</h1>
          <p>
            Revisa estudiantes, conversaciones, temas buscados, sintesis docente,
            recomendaciones enviadas y avance por las cuatro unidades.
          </p>
          <div className="chips">
            <span className="chip">Estudiantes</span>
            <span className="chip">Chats y dudas</span>
            <span className="chip">Ruta por unidades</span>
          </div>
          <div className="cta">
            <a className="btn primary xl" href="/teacher/login"><i className="bi bi-mortarboard" /> Entrar como docente</a>
            <a className="btn ghost xl" href="/teacher#route"><i className="bi bi-map" /> Ver ruta academica</a>
          </div>
        </section>

        <aside className="mgmt-side-card">
          <h2>Vista pedagogica</h2>
          <p>El docente ve evidencia academica y acciones para orientar al estudiante.</p>
          <div className="mgmt-status-list">
            <span><i className="bi bi-check-circle" /> Chats agrupados por estudiante</span>
            <span><i className="bi bi-check-circle" /> Sintesis docente separada</span>
            <span><i className="bi bi-check-circle" /> Progreso por unidades</span>
          </div>
        </aside>
      </main>

      <section className="mgmt-section">
        <div className="sectionTitle">
          <h2>Accesos docentes</h2>
          <span>Seguimiento, evidencias y acciones pedagogicas</span>
        </div>
        <div className="mgmt-access-grid">
          {teacherAccess.map((item) => (
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
          <h2>Que revisa el docente</h2>
          <span>Resumen para seguimiento academico</span>
        </div>
        <div className="mgmt-focus-grid">
          {teacherFocus.map((item) => (
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
