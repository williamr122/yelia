'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../_components/api';

const UNITS = [
  {
    id: 1,
    title: 'Fundamentos de POO',
    subtitle: 'Introduccion, clases, objetos, atributos, metodos y encapsulamiento.',
    icon: 'bi-boxes',
    topics: ['Introduccion a POO', 'Clases y Objetos', 'Atributos y metodos', 'Encapsulamiento'],
    tasks: ['Lectura guiada', 'Ejercicios basicos', 'Taller de clases y objetos', 'Quiz de unidad'],
    prompt: 'Quiero empezar la Unidad 1: Fundamentos de POO. Explicame desde mi nivel y dame una actividad corta.',
  },
  {
    id: 2,
    title: 'Herencia, polimorfismo e interfaces',
    subtitle: 'Clases base y derivadas, sobrecarga, sobrescritura, clases abstractas e interfaces.',
    icon: 'bi-diagram-3',
    topics: ['Herencia', 'Polimorfismo', 'Sobrecarga y sobrescritura', 'Interfaces'],
    tasks: ['Ejemplos guiados', 'Taller de herencia', 'Preguntas de refuerzo', 'Quiz de unidad'],
    prompt: 'Quiero trabajar la Unidad 2: Herencia, polimorfismo e interfaces. Dame explicacion, ejemplo y practica.',
  },
  {
    id: 3,
    title: 'UML y patron MVC',
    subtitle: 'Diagramas UML, casos de uso, secuencia, actividad y estructura Modelo-Vista-Controlador.',
    icon: 'bi-bezier2',
    topics: ['Diagramas UML', 'Casos de uso', 'Secuencia y actividad', 'MVC'],
    tasks: ['Analisis de diagramas', 'Practica MVC', 'Taller aplicado', 'Quiz de unidad'],
    prompt: 'Quiero estudiar la Unidad 3: UML y patron MVC. Guiame con ejemplos y una practica aplicada.',
  },
  {
    id: 4,
    title: 'Archivos, base de datos y buenas practicas',
    subtitle: 'Acceso a archivos, bases de datos, ORM, integracion POO/MVC/datos, pruebas y buenas practicas.',
    icon: 'bi-database-check',
    topics: ['Acceso a archivos', 'Bases de Datos y ORM', 'Integracion POO/MVC/Datos', 'Pruebas'],
    tasks: ['Caso practico', 'Taller de integracion', 'Preguntas de repaso', 'Quiz de unidad'],
    prompt: 'Quiero avanzar con la Unidad 4: archivos, base de datos, ORM y buenas practicas.',
  },
];

function readProfile() {
  try {
    return JSON.parse(localStorage.getItem('yelia_profile') || '{}') || {};
  } catch {
    return {};
  }
}

function readRouteState() {
  try {
    const profile = readProfile();
    const key = routeStorageKey(profile);
    return JSON.parse(localStorage.getItem(key) || '{}') || {};
  } catch {
    return {};
  }
}

function routeStorageKey(profile = readProfile()) {
  const raw = profile.alias || localStorage.getItem('yelia_active_student') || localStorage.getItem('yelia_guest_alias') || 'anonimo';
  const safe = String(raw).replace(/[^A-Za-z0-9_-]/g, '-').slice(0, 48) || 'anonimo';
  return `yelia_learning_route_${safe}`;
}

function saveRouteState(next, profile) {
  localStorage.setItem(routeStorageKey(profile), JSON.stringify(next));
}

function statusFor(unit, routeState) {
  const saved = routeState?.units?.[unit.id];
  if (saved?.status) return saved.status;
  if (unit.id === 1) return 'active';
  return 'locked';
}

function statusLabel(status) {
  if (status === 'done') return 'Completada';
  if (status === 'active') return 'En curso';
  return 'Bloqueada';
}

function progressFor(unit, routeState) {
  const saved = routeState?.units?.[unit.id];
  if (Number.isFinite(saved?.progress)) return Math.max(0, Math.min(100, Number(saved.progress)));
  if (unit.id === 1) return 25;
  return 0;
}

function isFinalUnlocked(routeState, units = UNITS) {
  return units.every((unit) => statusFor(unit, routeState) === 'done');
}

export default function RutaClient() {
  const [profile, setProfile] = useState({});
  const [units, setUnits] = useState(UNITS);
  const [routeState, setRouteState] = useState({});
  const [activeUnit, setActiveUnit] = useState(UNITS[0]);
  const [quiz, setQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [finalQuiz, setFinalQuiz] = useState(null);
  const [finalAnswers, setFinalAnswers] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [error, setError] = useState('');

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'ruta-page ui desktop-pro';
    setProfile(readProfile());
    const saved = readRouteState();
    setRouteState(saved);
    const currentId = Number(saved.currentUnit || 1);
    setActiveUnit(UNITS.find((unit) => unit.id === currentId) || UNITS[0]);
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    setLoadingRoute(true);
    api.get('/api/learning-route')
      .then((data) => {
        if (!alive) return;
        const nextRoute = data.route || {};
        const enrichedUnits = Array.isArray(data.units) && data.units.length
          ? data.units.map((item) => ({
            ...item,
            icon: UNITS.find((unit) => unit.id === item.id)?.icon || 'bi-journal-code',
            tasks: [
              'Contenido oficial',
              'Taller de practica',
              `Leccion (${item.lesson_questions_count || 5} preguntas)`,
              `Examen de unidad (${item.unit_exam_questions_count || 10} preguntas)`,
            ],
            prompt: UNITS.find((unit) => unit.id === item.id)?.prompt || `Quiero estudiar la Unidad ${item.id}: ${item.title}.`,
          }))
          : UNITS;
        if (enrichedUnits.length) {
          setUnits(enrichedUnits);
        }
        setRouteState(nextRoute);
        saveRouteState(nextRoute, profile);
        const currentId = Number(nextRoute.currentUnit || 1);
        setActiveUnit(enrichedUnits.find((unit) => unit.id === currentId) || enrichedUnits[0]);
      })
      .catch((err) => {
        if (!alive) return;
        setError(`${err instanceof Error ? err.message : 'No se pudo cargar la ruta guardada.'} Se muestra la ruta local para que puedas seguir probando.`);
      })
      .finally(() => {
        if (alive) setLoadingRoute(false);
      });
    return () => {
      alive = false;
    };
  }, [profile]);

  const summary = useMemo(() => {
    const values = units.map((unit) => progressFor(unit, routeState));
    const total = Math.round(values.reduce((sum, value) => sum + value, 0) / units.length);
    const done = units.filter((unit) => statusFor(unit, routeState) === 'done').length;
    const final = routeState?.final_evaluation;
    return { total, done, final };
  }, [routeState, units]);

  function openUnit(unit) {
    if (statusFor(unit, routeState) === 'locked') return;
    setActiveUnit(unit);
    const next = { ...routeState, currentUnit: unit.id };
    setRouteState(next);
    saveRouteState(next, profile);
    setQuiz(null);
    setQuizResult(null);
  }

  function syncRoute(nextRoute) {
    setRouteState(nextRoute);
    saveRouteState(nextRoute, profile);
  }

  function goChat(unit = activeUnit) {
    localStorage.setItem('yelia_route_prompt', unit.prompt);
    window.location.href = `/chat?routeUnit=${unit.id}`;
  }

  function goLesson(unit = activeUnit, mode = 'content') {
    window.location.href = `/leccion?unidad=${unit.id}${mode === 'content' ? '' : `&modo=${mode}`}`;
  }

  async function markPractice() {
    const units = { ...(routeState.units || {}) };
    const current = units[activeUnit.id] || {};
    const progress = Math.max(progressFor(activeUnit, routeState), 50);
    units[activeUnit.id] = { ...current, status: 'active', progress };
    const next = { ...routeState, currentUnit: activeUnit.id, units };
    setRouteState(next);
    saveRouteState(next, profile);
    try {
      const data = await api.post(`/api/learning-route/unit/${activeUnit.id}/practice`, {});
      if (data.route) {
        syncRoute(data.route);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la practica.');
    }
  }

  async function startQuiz() {
    setQuizResult(null);
    setQuizAnswers({});
    try {
      const data = await api.get(`/api/learning-route/unit/${activeUnit.id}/quiz`);
      setQuiz(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo abrir el quiz.');
    }
  }

  async function submitQuiz() {
    if (!quiz?.questions?.length) return;
    if (Object.keys(quizAnswers).length < quiz.questions.length) {
      setError('Responde todas las preguntas del quiz antes de finalizar.');
      return;
    }
    setError('');
    try {
      const data = await api.post(`/api/learning-route/unit/${activeUnit.id}/quiz`, { answers: quizAnswers });
      setQuizResult(data);
      if (data.route) {
        syncRoute(data.route);
        const currentId = Number(data.route.currentUnit || activeUnit.id);
        setActiveUnit(UNITS.find((unit) => unit.id === currentId) || activeUnit);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar el quiz.');
    }
  }

  async function startFinalQuiz() {
    setFinalResult(null);
    setFinalAnswers({});
    try {
      const data = await api.get('/api/learning-route/final-quiz');
      setFinalQuiz(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'La evaluacion final aun no esta disponible.');
    }
  }

  async function submitFinalQuiz() {
    if (!finalQuiz?.questions?.length) return;
    if (Object.keys(finalAnswers).length < finalQuiz.questions.length) {
      setError('Responde todas las preguntas de la evaluacion final.');
      return;
    }
    setError('');
    try {
      const data = await api.post('/api/learning-route/final-quiz', { answers: finalAnswers });
      setFinalResult(data);
      if (data.route) syncRoute(data.route);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar la evaluacion final.');
    }
  }

  return (
    <main className="ruta-shell">
      <header className="ruta-topbar">
        <a className="ruta-brand" href="/launcher">
          <span><i className="bi bi-cpu" /></span>
          <b>YELIA4AP</b>
          <small>Ruta por unidades</small>
        </a>
        <nav className="ruta-nav">
          <a href="/diagnostico">Diagnostico</a>
          <a href="/chat">Chat</a>
          <a href="/progreso">Mi progreso</a>
        </nav>
      </header>

      <section className="ruta-hero">
        <div>
          <span className="ruta-kicker">Programacion Avanzada</span>
          <h1>Ruta modular de aprendizaje</h1>
          <p>
            Avanza por las 4 unidades del silabo. En cada unidad YELIA guia contenido,
            recomienda recursos, propone talleres, toma quiz y decide si conviene reforzar o avanzar.
          </p>
          <div className="ruta-actions">
            <button type="button" onClick={() => goLesson(activeUnit)}><i className="bi bi-book" /> Abrir leccion</button>
            <button type="button" onClick={() => goChat()}><i className="bi bi-chat-dots" /> Chat de dudas</button>
            <a href="/progreso"><i className="bi bi-grid-3x3-gap" /> Ver mi progreso</a>
          </div>
        </div>
        <aside className="ruta-profile">
          <span>Perfil academico</span>
          <strong>{profile.alias || 'Invitado 1'}</strong>
          <dl>
            <div><dt>Nivel</dt><dd>{profile.nivel || 'Por diagnosticar'}</dd></div>
            <div><dt>Ciclo</dt><dd>{profile.ciclo || 'No configurado'}</dd></div>
            <div><dt>Estado</dt><dd>{profile.estado || 'No configurado'}</dd></div>
          </dl>
        </aside>
      </section>

      {error && <div className="ruta-error"><i className="bi bi-exclamation-triangle" />{error}</div>}
      {loadingRoute && <div className="ruta-sync"><i className="bi bi-arrow-repeat" /> Sincronizando ruta guardada...</div>}

      <section className="ruta-summary-grid" aria-label="Resumen de avance">
        <article><span>Avance general</span><strong>{summary.total}%</strong><small>Promedio de las 4 unidades</small></article>
        <article><span>Unidades completadas</span><strong>{summary.done}/4</strong><small>Se desbloquean con quiz aprobado</small></article>
        <article><span>Unidad activa</span><strong>{activeUnit.id}</strong><small>{activeUnit.title}</small></article>
        <article>
          <span>Cierre esperado</span>
          <strong>{summary.final?.percent ? `${summary.final.percent}%` : 'Final'}</strong>
          <small>{summary.final?.passed ? 'Ruta completada' : 'Evaluacion general y mapa de calor'}</small>
        </article>
      </section>

      <section className="ruta-grid">
        <div className="ruta-unit-list">
        {units.map((unit) => {
            const status = statusFor(unit, routeState);
            const progress = progressFor(unit, routeState);
            return (
              <button
                className={`ruta-unit-card ${activeUnit.id === unit.id ? 'is-active' : ''} is-${status}`}
                key={unit.id}
                type="button"
                onClick={() => openUnit(unit)}
              >
                <span><i className={`bi ${unit.icon}`} /></span>
                <div>
                  <small>Unidad {unit.id} - {statusLabel(status)}</small>
                  <strong>{unit.title}</strong>
                  <em>{unit.subtitle}</em>
                  <i><b style={{ width: `${progress}%` }} /></i>
                </div>
              </button>
            );
          })}
        </div>

        <article className="ruta-detail">
          <div className="ruta-detail-head">
            <div>
              <span>Unidad {activeUnit.id}</span>
              <h2>{activeUnit.title}</h2>
              <p>{activeUnit.subtitle}</p>
            </div>
            <strong>{progressFor(activeUnit, routeState)}%</strong>
          </div>

          <div className="ruta-detail-columns">
            <section>
              <h3>Temas de la unidad</h3>
              <div className="ruta-chip-list">
                {activeUnit.topics.map((topic) => <span key={topic}>{topic}</span>)}
              </div>
            </section>
            <section>
              <h3>Lo que hara YELIA</h3>
              <div className="ruta-task-list">
                {activeUnit.tasks.map((task, index) => (
                  <div key={task}>
                    <b>{index + 1}</b>
                    <span>{task}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="ruta-teacher-note">
            <i className="bi bi-lightbulb" />
            <p>
              Primero se trabaja contenido y recursos; luego talleres y quiz. Si el estudiante no domina la unidad,
              YELIA manda refuerzo antes de avanzar.
            </p>
          </div>

          <div className="ruta-detail-actions">
            <button type="button" onClick={() => goLesson(activeUnit, 'content')}>Ver contenido</button>
            <button type="button" onClick={markPractice}>Marcar practica iniciada</button>
            <button type="button" onClick={() => goLesson(activeUnit, 'workshop')}>Abrir taller</button>
            <button type="button" onClick={() => goLesson(activeUnit, 'lesson')}>Leccion de 5 preguntas</button>
            <button type="button" onClick={() => goLesson(activeUnit, 'exam')}>Examen de unidad</button>
            <a href="/progreso">Revisar mi mapa de calor</a>
          </div>

          {quiz && (
            <section className="ruta-quiz-panel">
              <div className="ruta-detail-head">
                <div>
                  <span>Quiz de unidad</span>
                  <h2>{quiz.unit?.title || activeUnit.title}</h2>
                  <p>Necesitas al menos {quiz.passing_score || 70}% para desbloquear la siguiente unidad.</p>
                </div>
                <strong>{Object.keys(quizAnswers).length}/{quiz.questions.length}</strong>
              </div>
              <div className="ruta-quiz-list">
                {quiz.questions.map((question, index) => (
                  <article className="ruta-quiz-question" key={question.id}>
                    <div><b>{index + 1}</b><span>{question.topic}</span></div>
                    <h3>{question.question}</h3>
                    <div className="ruta-answer-grid">
                      {question.options.map((option, optionIndex) => (
                        <button
                          className={quizAnswers[question.id] === optionIndex ? 'is-picked' : ''}
                          key={option}
                          type="button"
                          onClick={() => setQuizAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
                        >
                          <strong>{String.fromCharCode(65 + optionIndex)}</strong>
                          <span>{option}</span>
                        </button>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
              <div className="ruta-detail-actions">
                <button type="button" onClick={submitQuiz}>Finalizar quiz</button>
                <button type="button" onClick={() => setQuiz(null)}>Cerrar quiz</button>
              </div>
            </section>
          )}

          {quizResult && (
            <section className={`ruta-result-panel ${quizResult.result?.passed ? 'is-pass' : 'is-retry'}`}>
              <span>{quizResult.result?.passed ? 'Unidad aprobada' : 'Reforzar unidad'}</span>
              <strong>{quizResult.result?.percent || 0}%</strong>
              <p>{quizResult.feedback}</p>
              <div className="ruta-detail-actions">
                <button type="button" onClick={() => goChat(activeUnit)}>
                  {quizResult.result?.passed ? 'Continuar con YELIA' : 'Pedir refuerzo'}
                </button>
                <a href="/progreso">Ver mi progreso</a>
              </div>
            </section>
          )}
        </article>
      </section>

      <section className={`ruta-final-card ${isFinalUnlocked(routeState, units) ? 'is-open' : 'is-locked'}`}>
        <div>
          <span>Evaluacion final</span>
          <h2>Cierre de Programacion Avanzada</h2>
          <p>
            Se habilita cuando completas las 4 unidades. Sirve para medir el dominio global
            y dejar evidencia final en tu progreso personal.
          </p>
          <div className="ruta-final-checklist">
            <article>
              <i className="bi bi-journal-check" />
              <b>Ruta por unidades</b>
              <small>Contenido, practica y quiz antes de avanzar.</small>
            </article>
            <article>
              <i className="bi bi-grid-3x3-gap" />
              <b>Mapa de calor</b>
              <small>Identifica temas dominados y temas por reforzar.</small>
            </article>
            <article>
              <i className="bi bi-stars" />
              <b>Refuerzo adaptativo</b>
              <small>YELIA ajusta explicaciones segun errores y avance.</small>
            </article>
          </div>
        </div>
        <aside>
          <strong>{summary.final?.percent ? `${summary.final.percent}%` : `${summary.done}/4`}</strong>
          <small>{isFinalUnlocked(routeState, units) ? 'Disponible' : 'Unidades completadas'}</small>
          <div className="ruta-final-heat" aria-label="Mapa de avance por unidades">
            {units.map((unit) => (
              <span
                key={unit.id}
                className={statusFor(unit, routeState) === 'done' ? 'is-done' : statusFor(unit, routeState) === 'active' ? 'is-active' : ''}
                title={`Unidad ${unit.id}: ${progressFor(unit, routeState)}%`}
              >
                {unit.id}
              </span>
            ))}
          </div>
          <button type="button" onClick={startFinalQuiz} disabled={!isFinalUnlocked(routeState, units)}>
            {summary.final?.passed ? 'Revisar evaluacion' : 'Tomar evaluacion final'}
          </button>
        </aside>

        {finalQuiz && (
          <section className="ruta-quiz-panel ruta-final-quiz">
            <div className="ruta-detail-head">
              <div>
                <span>Evaluacion final</span>
                <h2>{finalQuiz.title}</h2>
                <p>Necesitas al menos {finalQuiz.passing_score || 70}% para cerrar la ruta.</p>
              </div>
              <strong>{Object.keys(finalAnswers).length}/{finalQuiz.questions.length}</strong>
            </div>
            <div className="ruta-quiz-list">
              {finalQuiz.questions.map((question, index) => (
                <article className="ruta-quiz-question" key={question.id}>
                  <div><b>{index + 1}</b><span>{question.topic}</span></div>
                  <h3>{question.question}</h3>
                  <div className="ruta-answer-grid">
                    {question.options.map((option, optionIndex) => (
                      <button
                        className={finalAnswers[question.id] === optionIndex ? 'is-picked' : ''}
                        key={option}
                        type="button"
                        onClick={() => setFinalAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
                      >
                        <strong>{String.fromCharCode(65 + optionIndex)}</strong>
                        <span>{option}</span>
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
            <div className="ruta-detail-actions">
              <button type="button" onClick={submitFinalQuiz}>Finalizar evaluacion</button>
              <button type="button" onClick={() => setFinalQuiz(null)}>Cerrar</button>
            </div>
          </section>
        )}

        {finalResult && (
          <section className={`ruta-result-panel ${finalResult.result?.passed ? 'is-pass' : 'is-retry'}`}>
            <span>{finalResult.result?.passed ? 'Ruta completada' : 'Refuerzo final'}</span>
            <strong>{finalResult.result?.percent || 0}%</strong>
            <p>{finalResult.feedback}</p>
            <div className="ruta-detail-actions">
              <a href="/progreso">Ver mapa de calor personal</a>
              <button type="button" onClick={() => goChat(activeUnit)}>Pedir refuerzo con YELIA</button>
            </div>
          </section>
        )}
      </section>
    </main>
  );
}
