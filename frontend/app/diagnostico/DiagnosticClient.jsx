'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../_components/api';

const CYCLES = [
  ['Primero', 'Estoy iniciando la carrera y necesito bases claras.'],
  ['Segundo', 'Ya curse materias introductorias y necesito ejemplos guiados.'],
  ['Tercero', 'Estoy fortaleciendo programacion y logica.'],
  ['Cuarto', 'Puedo avanzar con problemas un poco mas aplicados.'],
  ['Quinto', 'Busco explicaciones mas tecnicas y ejercicios completos.'],
  ['Sexto', 'Necesito conectar teoria con desarrollo real.'],
  ['Septimo', 'Quiero repasar y resolver dudas puntuales.'],
  ['Octavo', 'Busco practica avanzada y retroalimentacion directa.'],
  ['Noveno', 'Quiero consolidar conocimientos para proyectos.'],
  ['Decimo', 'Estoy cerca del cierre y necesito precision academica.'],
  ['Egresado', 'Uso el asistente para repaso, tesis o practica profesional.'],
  ['Graduado', 'Ya termine la carrera y uso YELIA para repaso o practica profesional.'],
];

const STATES = [
  ['No la veo aun', 'Todavia no cursas la materia y quieres empezar desde cero.'],
  ['La estoy cursando', 'Estas viendo la materia ahora y quieres acompanamiento segun la clase.'],
  ['Aprendiendo', 'Estas entendiendo poco a poco y necesitas explicaciones paso a paso.'],
  ['Repitiendo', 'Repites la materia y necesitas apoyo mas guiado.'],
  ['Ya la vi', 'Ya cursaste la materia y quieres repasar, aclarar dudas o practicar.'],
  ['Ya la aprobe', 'Ya aprobaste la materia y quieres reforzar para proyectos, tesis o practica profesional.'],
  ['Repasando', 'Ya viste el tema y quieres reforzar.'],
  ['Preparando examen', 'Necesitas preguntas, resumenes y practica.'],
];

const LEVEL_ICONS = {
  'Sin conocimientos': 'bi-brain',
  Basico: 'bi-book',
  Intermedio: 'bi-bar-chart-line',
  Avanzado: 'bi-rocket-takeoff',
};

function readProfile() {
  try {
    return JSON.parse(localStorage.getItem('yelia_profile') || '{}') || {};
  } catch {
    return {};
  }
}

function nextGuestAlias() {
  const existing = localStorage.getItem('yelia_guest_alias');
  if (existing) return existing;
  const count = Number(localStorage.getItem('yelia_guest_count') || '0') + 1;
  const alias = `Invitado ${count}`;
  localStorage.setItem('yelia_guest_count', String(count));
  localStorage.setItem('yelia_guest_alias', alias);
  return alias;
}

function cleanAlias(value) {
  return String(value || '').replace(/[^A-Za-z0-9._ -]/g, '').slice(0, 32);
}

function saveProfile(profile, mode) {
  const clean = {
    alias: profile.alias,
    ciclo: profile.ciclo,
    estado: profile.estado,
    nivel: profile.nivel,
    diagnostic: profile.diagnostic || null,
  };
  localStorage.setItem('yelia_profile', JSON.stringify(clean));
  localStorage.setItem('yelia_guest_mode', mode === 'guest' ? '1' : '0');
  if (mode === 'guest') {
    localStorage.setItem('yelia_guest_alias', profile.alias);
  } else {
    localStorage.setItem('yelia_active_student', profile.alias);
  }
}

function OptionGrid({ items, value, onChange }) {
  return (
    <div className="diag-option-grid">
      {items.map(([label, detail]) => (
        <button
          className={`diag-option ${value === label ? 'is-active' : ''}`}
          key={label}
          onClick={() => onChange(label)}
          type="button"
        >
          <strong>{label}</strong>
          <span>{detail}</span>
        </button>
      ))}
    </div>
  );
}

export default function DiagnosticClient() {
  const [mode, setMode] = useState('student');
  const [alias, setAlias] = useState('');
  const [password, setPassword] = useState('');
  const [cycle, setCycle] = useState('Primero');
  const [state, setState] = useState('La estoy cursando');
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState('registro');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'diagnostic-page ui desktop-pro';
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const guest = params.get('guest') === '1';
    const profile = readProfile();
    setMode(guest ? 'guest' : 'student');
    setAlias(guest ? nextGuestAlias() : (profile.alias || localStorage.getItem('yelia_active_student') || ''));
    if (profile.ciclo) setCycle(profile.ciclo);
    if (profile.estado) setState(profile.estado);
  }, []);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);

  async function loadQuestions() {
    const cleanAlias = alias.trim();
    if (!cleanAlias) {
      setError('Escribe un codigo, alias o usa el invitado generado.');
      return;
    }
    if (!cycle || !state) {
      setError('Selecciona ciclo/semestre y estado respecto a la materia.');
      return;
    }
    if (mode !== 'guest' && password.trim().length < 6) {
      setError('Escribe tu clave de estudiante. Si es tu primera vez, crea una de al menos 6 caracteres.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const status = await api.post('/api/diagnostic/status', {
        alias: cleanAlias,
        mode,
        guest: mode === 'guest',
        password: password.trim(),
      });
      if (status.diagnostic_completed) {
        localStorage.setItem('yelia_active_student', cleanAlias);
        window.location.href = '/ruta';
        return;
      }
      const data = await api.get('/api/diagnostic/questions?count=5');
      setQuestions(data.questions || []);
      setAnswers({});
      setStep('preguntas');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las preguntas.');
    } finally {
      setLoading(false);
    }
  }

  async function submitDiagnostic() {
    if (answeredCount < questions.length) {
      setError('Responde las 5 preguntas para detectar tu nivel.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.post('/api/diagnostic/submit', {
        alias: alias.trim(),
        mode,
        guest: mode === 'guest',
        ciclo_academico: cycle,
        estado_materia: state,
        password: password.trim(),
        answers,
      });
      const diagnostic = data.diagnostic;
      const profile = {
        alias: data.alias || alias.trim(),
        ciclo: cycle,
        estado: state,
        nivel: diagnostic?.level || 'Basico',
        diagnostic,
      };
      saveProfile(profile, mode);
      setResult({ ...diagnostic, usuario: data.usuario, alias: profile.alias });
      setStep('resultado');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar el diagnostico.');
    } finally {
      setLoading(false);
    }
  }

  function goChat() {
    window.location.href = '/chat';
  }

  return (
    <main className="diag-shell">
      <header className="diag-topbar">
        <a className="diag-brand" href="/launcher">
          <span><i className="bi bi-cpu" /></span>
          <b>YELIA4AP</b>
          <small>Diagnostico adaptativo</small>
        </a>
        <div className="diag-progress" aria-label="Progreso">
          {['registro', 'preguntas', 'resultado'].map((item, index) => (
            <span className={step === item ? 'is-current' : ''} key={item}>{index + 1}</span>
          ))}
        </div>
      </header>

      <section className="diag-hero">
        <div>
          <span className="diag-kicker">Flujo del estudiante</span>
          <h1>Registro, diagnostico y nivel real antes de conversar</h1>
          <p>YELIA ajustara contenido, ejemplos, ejercicios y recomendaciones segun tu ciclo, estado y resultado inicial.</p>
        </div>
        <div className="diag-flow-card">
          {[
            ['bi-person-circle', 'Registro'],
            ['bi-ui-checks', '5 preguntas'],
            ['bi-bullseye', 'Nivel detectado'],
            ['bi-stars', 'Chat adaptativo'],
          ].map(([icon, text]) => (
            <span key={text}><i className={`bi ${icon}`} />{text}</span>
          ))}
        </div>
      </section>

      {error && <div className="diag-error"><i className="bi bi-exclamation-triangle" />{error}</div>}

      {step === 'registro' && (
        <section className="diag-card diag-register">
          <div className="diag-section-head">
            <span><i className="bi bi-person-vcard" /></span>
            <div>
              <h2>Registro del estudiante</h2>
              <p>Define quien entra y como esta frente a la materia.</p>
            </div>
          </div>

          <div className="diag-mode">
            <button className={mode === 'student' ? 'is-active' : ''} onClick={() => setMode('student')} type="button">
              <i className="bi bi-person-check" /> Usuario
            </button>
            <button className={mode === 'guest' ? 'is-active' : ''} onClick={() => { setMode('guest'); setAlias(nextGuestAlias()); }} type="button">
              <i className="bi bi-incognito" /> Invitado
            </button>
          </div>

          <label className="diag-label" htmlFor="diagAlias">Codigo / alias</label>
          <input
            id="diagAlias"
            className="diag-input"
            value={alias}
            onChange={(event) => setAlias(cleanAlias(event.target.value))}
            placeholder="Ej.: 2020123456, Erick o Invitado 1"
            maxLength={32}
          />
          <p className="diag-help-text">
            En esta PC se recuerda el ultimo alias usado. En otra PC el campo aparece vacio.
          </p>
          {mode !== 'guest' && (
            <>
              <label className="diag-label" htmlFor="diagPassword">Clave del estudiante</label>
              <input
                id="diagPassword"
                className="diag-input"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Minimo 6 caracteres"
                minLength={6}
                maxLength={128}
                autoComplete="current-password"
              />
              <p className="diag-help-text">
                Si ya tienes cuenta, esta clave te deja entrar a tu ruta. Si eres nuevo, se crea al finalizar el diagnostico.
              </p>
            </>
          )}

          <div className="diag-field-block">
            <h3>Ciclo / semestre</h3>
            <p>Selecciona tu avance academico para ajustar profundidad y vocabulario.</p>
            <OptionGrid items={CYCLES} value={cycle} onChange={setCycle} />
          </div>

          <div className="diag-field-block">
            <h3>Estado respecto a la materia</h3>
            <p>Indica como estas usando YELIA en este momento.</p>
            <OptionGrid items={STATES} value={state} onChange={setState} />
          </div>

          <div className="diag-actions">
            <a className="diag-secondary" href="/launcher">Volver</a>
            <button className="diag-primary" onClick={loadQuestions} disabled={loading} type="button">
              {loading ? 'Cargando...' : 'Continuar al diagnostico'} <i className="bi bi-arrow-right" />
            </button>
          </div>
        </section>
      )}

      {step === 'bloqueado' && (
        <section className="diag-card diag-result">
          <div className="diag-result-main">
            <span className="diag-result-icon"><i className="bi bi-lock-check" /></span>
            <div>
              <small>Diagnostico ya completado</small>
              <h2>Tu nivel inicial ya esta guardado</h2>
              <p>Las 5 preguntas iniciales se responden una sola vez. Ahora continua con la ruta academica, el chat de dudas o tu progreso.</p>
            </div>
            <strong>OK</strong>
          </div>
          <div className="diag-actions">
            <a className="diag-secondary" href="/progreso">Ver mi progreso</a>
            <a className="diag-secondary" href="/ruta">Ir a mi ruta</a>
            <button className="diag-primary" onClick={goChat} type="button">Entrar al chat <i className="bi bi-chat-dots" /></button>
          </div>
        </section>
      )}

      {step === 'preguntas' && (
        <section className="diag-card">
          <div className="diag-section-head">
            <span><i className="bi bi-clipboard-check" /></span>
            <div>
              <h2>Evaluacion diagnostica</h2>
              <p>Responde 5 preguntas aleatorias de Programacion Avanzada.</p>
            </div>
          </div>

          <div className="diag-questions">
            {questions.map((question, index) => (
              <article className="diag-question" key={question.id}>
                <div className="diag-question-title">
                  <b>{index + 1}</b>
                  <span>{question.topic}</span>
                  <em>{question.level}</em>
                </div>
                <h3>{question.question}</h3>
                <div className="diag-answer-grid">
                  {question.options.map((option, optionIndex) => (
                    <button
                      className={answers[question.id] === optionIndex ? 'is-picked' : ''}
                      key={option}
                      onClick={() => setAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
                      type="button"
                    >
                      <strong>{String.fromCharCode(65 + optionIndex)}</strong>
                      <span>{option}</span>
                    </button>
                  ))}
                </div>
              </article>
            ))}
          </div>

          <div className="diag-actions">
            <button className="diag-secondary" onClick={() => setStep('registro')} type="button">Atras</button>
            <button className="diag-primary" onClick={submitDiagnostic} disabled={loading} type="button">
              {loading ? 'Guardando...' : `Finalizar (${answeredCount}/${questions.length})`} <i className="bi bi-check2-circle" />
            </button>
          </div>
        </section>
      )}

      {step === 'resultado' && result && (
        <section className="diag-card diag-result">
          <div className="diag-result-main">
            <span className="diag-result-icon"><i className={`bi ${LEVEL_ICONS[result.level] || 'bi-bullseye'}`} /></span>
            <div>
              <small>Nivel detectado</small>
              <h2>{result.level}</h2>
              <p>{result.feedback}</p>
            </div>
            <strong>{result.score}/{result.total}</strong>
          </div>

          <div className="diag-next-grid">
            <article>
              <i className="bi bi-sliders" />
              <h3>Personalizacion adaptativa</h3>
              <p>YELIA usara este nivel para ajustar dificultad, vocabulario, ejemplos y ejercicios.</p>
            </article>
            <article>
              <i className="bi bi-folder2-open" />
              <h3>Recursos recomendados</h3>
              <p>{(result.recommendations || []).map((item) => item.topic).join(', ') || 'Programacion Avanzada'}</p>
            </article>
            <article>
              <i className="bi bi-grid-3x3-gap" />
              <h3>Mapa de calor</h3>
              <p>Los temas fallados y reforzados alimentaran las metricas del estudiante.</p>
            </article>
          </div>

          <div className="diag-actions">
            <button className="diag-secondary" onClick={() => setStep('preguntas')} type="button">Revisar respuestas</button>
            <button className="diag-primary" onClick={goChat} type="button">Entrar al chat con YELIA <i className="bi bi-chat-dots" /></button>
          </div>
        </section>
      )}
    </main>
  );
}
