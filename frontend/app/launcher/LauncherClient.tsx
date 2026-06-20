'use client';

import { useLayoutEffect, useState } from 'react';
import { api } from '../_components/api';

function saveStudentProfile(alias: string) {
  const current = JSON.parse(localStorage.getItem('yelia_profile') || '{}');
  const next = current.alias && current.alias !== alias ? { alias } : { ...current, alias };
  localStorage.setItem('yelia_profile', JSON.stringify(next));
  localStorage.setItem('yelia_guest_mode', alias ? '0' : '1');
}

function newGuestId() {
  const id = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const safe = id.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 48);
  localStorage.setItem('yelia_guest_id', safe);
  return safe;
}

const features = [
  ['bi-chat-dots', 'Chat guiado', 'Pregunta sobre POO, MVC, excepciones, colecciones y mas.'],
  ['bi-clipboard2-check', 'Diagnostico inicial', 'Cinco preguntas detectan si estas en base, intermedio o avanzado.'],
  ['bi-map', 'Ruta por unidades', 'Avanza por las 4 unidades del silabo con recursos, talleres y quiz.'],
  ['bi-ui-checks-grid', 'Quizzes exactos', 'Practica con preguntas estructuradas y correccion mas confiable.'],
  ['bi-stars', 'Recomendaciones', 'Recibe repaso, recursos y siguientes pasos sin mezclar la respuesta.'],
];

export default function LauncherClient() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'launcher ui desktop-pro';
    return () => {
      document.body.className = previous;
    };
  }, []);

  async function enterAsGuest() {
    setLoading(true);
    setError('');
    try {
      saveStudentProfile('');
      localStorage.removeItem('yelia_active_student');
      await api.post('/api/auth/login', { guest_id: newGuestId() });
      window.location.href = '/diagnostico?guest=1';
    } catch {
      window.location.href = '/diagnostico?guest=1';
    }
  }

  return (
    <div className="wrap yelia-student-home">
      <header className="student-topbar">
        <a className="student-brand" href="/launcher" aria-label="YELIA4AP inicio">
          <span className="student-logo"><i className="bi bi-cpu" /></span>
          <span><b>YELIA4AP</b><small>Asistente educativo virtual</small></span>
        </a>
        <nav>
          <a href="#flujo-estudiante">Como funciona</a>
        </nav>
      </header>

      <section className="student-hero">
        <div className="student-hero-copy">
          <span className="badge">Entrada del estudiante</span>
          <h1>Aprendizaje inteligente para Programacion Avanzada</h1>
          <p>
            Registrate, responde un diagnostico corto y conversa con YELIA segun tu nivel real,
            ciclo y estado frente a la materia.
          </p>
          <div className="student-hero-actions">
            <a className="btn primary xl" href="/diagnostico"><i className="bi bi-clipboard2-check" /> Empezar diagnostico</a>
            <a className="btn ghost xl" href="/ruta"><i className="bi bi-map" /> Ver ruta</a>
            <a className="btn ghost xl" href="/progreso"><i className="bi bi-bar-chart-line" /> Mi progreso</a>
            <button className="btn ghost xl" onClick={enterAsGuest} disabled={loading} type="button">
              <i className="bi bi-incognito" /> Probar como invitado
            </button>
          </div>
          <div className="student-proof">
            <span><i className="bi bi-check2-circle" /> Perfil opcional</span>
            <span><i className="bi bi-check2-circle" /> Historial por usuario</span>
            <span><i className="bi bi-check2-circle" /> IA adaptativa</span>
          </div>
        </div>

        <article className="student-login-card hero-login student-flow-card" id="flujo-estudiante">
          <div className="student-card-head">
            <span className="student-icon"><i className="bi bi-signpost-split" /></span>
            <div>
              <h2>Flujo del estudiante</h2>
              <p>Primero crea o usa tu alias en el diagnostico. Despues YELIA adapta la ruta, el chat y tus recomendaciones.</p>
            </div>
          </div>

          {error && <div className="entry-error">{error}</div>}

          <div className="student-flow-list" aria-label="Ruta resumida del estudiante">
            <a href="/diagnostico">
              <span>1</span>
              <b>Registro y diagnostico</b>
              <small>Alias, ciclo, estado y 5 preguntas para detectar nivel.</small>
            </a>
            <a href="/ruta">
              <span>2</span>
              <b>Ruta por unidades</b>
              <small>Unidad 1 a Unidad 4 con recursos, talleres y quiz.</small>
            </a>
            <a href="/chat">
              <span>3</span>
              <b>Chat adaptativo</b>
              <small>YELIA responde segun nivel, unidad activa y necesidad.</small>
            </a>
            <a href="/progreso">
              <span>4</span>
              <b>Control del avance</b>
              <small>Mapa de calor, recomendaciones, autoevaluacion y progreso.</small>
            </a>
          </div>

          <div className="student-login-actions">
            <a className="btn primary" href="/diagnostico">
              Ir al diagnostico
            </a>
            <button className="btn ghost" type="button" onClick={enterAsGuest} disabled={loading}>
              {loading ? 'Preparando...' : 'Probar como invitado'}
            </button>
          </div>
        </article>
      </section>

      <section className="student-feature-grid">
        {features.map(([icon, title, text]) => (
          <article className="student-feature" key={title}>
            <span><i className={`bi ${icon}`} /></span>
            <h3>{title}</h3>
            <p>{text}</p>
          </article>
        ))}
      </section>

      <footer className="student-footer">
        <span>YELIA4AP - Universidad de Guayaquil</span>
        <span>Aprende, practica y mejora con apoyo adaptativo.</span>
      </footer>
    </div>
  );
}
