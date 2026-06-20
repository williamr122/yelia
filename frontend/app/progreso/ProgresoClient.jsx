'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../_components/api';

const UNITS = [
  {
    id: 1,
    title: 'Fundamentos de POO',
    topics: ['Introduccion a POO', 'Clases y Objetos', 'Atributos y metodos', 'Encapsulamiento'],
  },
  {
    id: 2,
    title: 'Herencia, polimorfismo e interfaces',
    topics: ['Herencia', 'Polimorfismo', 'Sobrecarga y sobrescritura', 'Interfaces'],
  },
  {
    id: 3,
    title: 'UML y patron MVC',
    topics: ['Diagramas UML', 'Casos de uso', 'Secuencia y actividad', 'MVC'],
  },
  {
    id: 4,
    title: 'Archivos, base de datos y buenas practicas',
    topics: ['Acceso a archivos', 'Bases de Datos y ORM', 'Integracion POO/MVC/Datos', 'Pruebas'],
  },
];

function readProfile() {
  try {
    return JSON.parse(localStorage.getItem('yelia_profile') || '{}') || {};
  } catch {
    return {};
  }
}

function routeStorageKey(profile = readProfile()) {
  const raw = profile.alias || localStorage.getItem('yelia_active_student') || localStorage.getItem('yelia_guest_alias') || 'anonimo';
  const safe = String(raw).replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 48) || 'anonimo';
  return `yelia_learning_route_${safe}`;
}

function readRouteState(profile) {
  try {
    return JSON.parse(localStorage.getItem(routeStorageKey(profile)) || '{}') || {};
  } catch {
    return {};
  }
}

function normalize(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

function topicSeen(topic, learned) {
  const clean = normalize(topic);
  return learned.some((item) => {
    const value = normalize(item);
    return value.includes(clean) || clean.includes(value);
  });
}

function progressFor(unit, routeState, learned) {
  const saved = routeState?.units?.[unit.id];
  if (Number.isFinite(saved?.progress)) return Math.max(0, Math.min(100, Number(saved.progress)));
  const hits = unit.topics.filter((topic) => topicSeen(topic, learned)).length;
  return Math.round((hits / unit.topics.length) * 100);
}

function heatTone(value) {
  if (value >= 75) return 'high';
  if (value >= 40) return 'mid';
  if (value > 0) return 'low';
  return 'empty';
}

export default function ProgresoClient() {
  const [profile, setProfile] = useState({});
  const [routeState, setRouteState] = useState({});
  const [progress, setProgress] = useState(null);
  const [teacherActions, setTeacherActions] = useState([]);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'student-progress-page ui desktop-pro';
    const localProfile = readProfile();
    setProfile(localProfile);
    setRouteState(readRouteState(localProfile));
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    Promise.allSettled([api.get('/api/progreso'), api.get('/api/learning-route')])
      .then((results) => {
        if (!alive) return;
        const progressResult = results[0];
        const routeResult = results[1];
        if (progressResult.status === 'fulfilled') {
          setProgress(progressResult.value.progreso || {});
          setTeacherActions(Array.isArray(progressResult.value.teacher_actions) ? progressResult.value.teacher_actions : []);
        }
        if (routeResult.status === 'fulfilled' && routeResult.value.route) {
          setRouteState(routeResult.value.route);
        }
        if (progressResult.status === 'rejected' && routeResult.status === 'rejected') {
          throw progressResult.reason || routeResult.reason;
        }
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar tu progreso.');
      });
    return () => {
      alive = false;
    };
  }, []);

  const learned = useMemo(() => {
    const topics = progress?.temas_aprendidos;
    return Array.isArray(topics) ? topics : [];
  }, [progress]);

  const unitRows = useMemo(() => UNITS.map((unit) => {
    const value = progressFor(unit, routeState, learned);
    const missing = unit.topics.filter((topic) => !topicSeen(topic, learned));
    return { ...unit, value, missing };
  }), [routeState, learned]);

  const overall = useMemo(() => {
    if (!unitRows.length) return 0;
    return Math.round(unitRows.reduce((sum, unit) => sum + unit.value, 0) / unitRows.length);
  }, [unitRows]);

  const activeUnit = useMemo(() => {
    const currentId = Number(routeState?.currentUnit || 1);
    return unitRows.find((unit) => unit.id === currentId) || unitRows[0];
  }, [routeState, unitRows]);

  const weakTopics = unitRows.flatMap((unit) => unit.missing.slice(0, 2)).slice(0, 5);

  return (
    <main className="progress-shell">
      <header className="progress-topbar">
        <a className="progress-brand" href="/ruta">
          <span><i className="bi bi-grid-3x3-gap" /></span>
          <b>Mi progreso</b>
          <small>Mapa de calor del estudiante</small>
        </a>
        <nav>
          <a href="/ruta">Ruta</a>
          <a href="/chat">Chat</a>
          <a href="/diagnostico">Diagnostico</a>
        </nav>
      </header>

      <section className="progress-hero">
        <div>
          <span className="progress-kicker">Vista del estudiante</span>
          <h1>Mapa de calor personal</h1>
          <p>
            Esta vista muestra tu avance por unidades. No es el panel del docente ni del administrador:
            aqui ves que has trabajado, que falta reforzar y cual es el siguiente paso.
          </p>
        </div>
        <aside className="progress-profile">
          <strong>{profile.alias || progress?.usuario || 'Estudiante'}</strong>
          <div><span>Nivel</span><b>{profile.nivel || progress?.nivel_materia || progress?.nivel || 'Por diagnosticar'}</b></div>
          <div><span>Puntos</span><b>{Number(progress?.puntos || 0)}</b></div>
          <div><span>Avance</span><b>{overall}%</b></div>
        </aside>
      </section>

      {error && <div className="progress-error"><i className="bi bi-exclamation-triangle" />{error}</div>}

      <section className="progress-grid">
        <article className="progress-panel progress-heat-panel">
          <div className="progress-panel-head">
            <div>
              <h2>Mapa de calor por unidad</h2>
              <p>Verde indica mayor avance; rojo indica que conviene reforzar.</p>
            </div>
            <span>Bajo - Alto</span>
          </div>

          <div className="progress-heat-table">
            {unitRows.map((unit) => (
              <div className="progress-heat-row" key={unit.id}>
                <div>
                  <strong>Unidad {unit.id}</strong>
                  <span>{unit.title}</span>
                </div>
                <div className={`progress-heat-cell is-${heatTone(unit.value)}`}>
                  <b>{unit.value}%</b>
                  <small>{unit.missing.length ? `${unit.missing.length} temas por reforzar` : 'Lista para avanzar'}</small>
                </div>
              </div>
            ))}
          </div>
        </article>

        <aside className="progress-panel">
          <h2>Siguiente mejora</h2>
          {activeUnit && (
            <div className="progress-current-unit">
              <span>Unidad activa</span>
              <strong>Unidad {activeUnit.id}: {activeUnit.title}</strong>
              <small>{activeUnit.value}% registrado</small>
            </div>
          )}
          {weakTopics.length ? (
            <>
              <p>Refuerza primero estos temas antes de avanzar con seguridad:</p>
              <div className="progress-chip-list">
                {weakTopics.map((topic) => <span key={topic}>{topic}</span>)}
              </div>
              <a className="progress-primary" href={`/chat?refuerzo=${encodeURIComponent(weakTopics[0])}`}>Pedir refuerzo a YELIA</a>
            </>
          ) : (
            <>
              <p>Tu ruta visible esta al dia. Puedes pedir un quiz de unidad o avanzar a la siguiente unidad.</p>
              <a className="progress-primary" href="/ruta">Volver a la ruta</a>
            </>
          )}
        </aside>
      </section>

      <section className="progress-grid is-lower">
        <article className="progress-panel">
          <h2>Temas trabajados</h2>
          <div className="progress-chip-list">
            {learned.length ? learned.map((topic) => <span key={topic}>{topic}</span>) : <span>Sin temas registrados aun</span>}
          </div>
        </article>

        <article className="progress-panel">
          <h2>Indicaciones del docente</h2>
          <div className="progress-action-list">
            {teacherActions.length ? teacherActions.slice().reverse().map((action, index) => (
              <div key={`${action.created_at || index}-${action.action_label || index}`}>
                <strong>{action.action_label || 'Accion recomendada'}</strong>
                <span>{action.topic || 'Seguimiento'}</span>
                <p>{action.detail || 'Tu docente dejo una indicacion para continuar.'}</p>
              </div>
            )) : <p>No tienes indicaciones pendientes.</p>}
          </div>
        </article>
      </section>
    </main>
  );
}
