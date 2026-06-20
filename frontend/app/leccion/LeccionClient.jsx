'use client';

import { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../_components/api';

const FALLBACK_UNITS = [
  { id: 1, title: 'Introduccion a la Programacion Orientada a Objetos', subtitle: 'Clases, objetos, atributos, metodos y encapsulamiento.', topics: ['Introduccion a POO', 'Clases y Objetos', 'Atributos y metodos', 'Encapsulamiento'] },
  { id: 2, title: 'Lenguaje de Modelado Unificado', subtitle: 'Herencia, polimorfismo, clases abstractas e interfaces.', topics: ['Herencia', 'Polimorfismo', 'Sobrecarga y sobrescritura', 'Interfaces'] },
  { id: 3, title: 'Aplicacion de la Programacion Orientada a Objetos', subtitle: 'UML, patrones de diseno y MVC.', topics: ['Diagramas UML', 'Casos de uso', 'Secuencia y actividad', 'MVC'] },
  { id: 4, title: 'Acceso a Archivos y Base de Datos', subtitle: 'Persistencia, ORM, integracion y pruebas.', topics: ['Acceso a archivos', 'Bases de Datos y ORM', 'Integracion POO/MVC/Datos', 'Pruebas'] },
];

function unitFromLocation() {
  if (typeof window === 'undefined') return 1;
  const params = new URLSearchParams(window.location.search);
  return Math.max(1, Math.min(4, Number(params.get('unidad') || params.get('unit') || 1)));
}

function modeFromLocation() {
  if (typeof window === 'undefined') return 'content';
  const params = new URLSearchParams(window.location.search);
  const mode = params.get('modo') || params.get('mode') || 'content';
  return mode === 'quiz' ? 'exam' : mode;
}

function publicQuestions(questions = []) {
  return questions.map(({ answer: _answer, source: _source, ...item }) => item);
}

function scoreLocalQuiz(questions, answers) {
  let score = 0;
  const details = questions.map((question) => {
    const selected = Number(answers[question.id]);
    const correct = selected === Number(question.answer);
    if (correct) score += 1;
    return { id: question.id, topic: question.topic, correct, selected, answer: question.answer };
  });
  const total = questions.length;
  const percent = total ? Math.round((score / total) * 100) : 0;
  return { score, total, percent, details };
}

function hintFor(unit, text) {
  const clean = String(text || '').toLowerCase();
  if (!clean.trim()) return 'Escribe tu duda y te doy una pista sin resolver la respuesta por ti.';
  if (clean.includes('respuesta') || clean.includes('examen') || clean.includes('quiz')) {
    return 'No puedo darte la respuesta directa. Te puedo explicar el concepto clave y darte una pista para razonar la opcion.';
  }
  if (clean.includes('ejemplo')) {
    return `Pista: toma un caso pequeno de ${unit.topics?.[0] || unit.title}. Primero separa datos, acciones y responsabilidad.`;
  }
  if (clean.includes('no entiendo') || clean.includes('duda') || clean.includes('explica')) {
    return `Pista de ${unit.title}: identifica que problema resuelve el concepto y luego comparalo con un ejemplo simple.`;
  }
  return `Conecta tu duda con uno de estos temas: ${(unit.topics || []).join(', ')}.`;
}

export default function LeccionClient() {
  const [unitId, setUnitId] = useState(1);
  const [units, setUnits] = useState(FALLBACK_UNITS);
  const [unitContent, setUnitContent] = useState(null);
  const [activePanel, setActivePanel] = useState('content');
  const [lessonAnswers, setLessonAnswers] = useState({});
  const [lessonResult, setLessonResult] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [finalQuiz, setFinalQuiz] = useState(null);
  const [finalAnswers, setFinalAnswers] = useState({});
  const [finalResult, setFinalResult] = useState(null);
  const [assistantText, setAssistantText] = useState('');
  const [assistantMessages, setAssistantMessages] = useState([
    { role: 'assistant', text: 'Estoy aqui para darte pistas y aclarar conceptos. Durante evaluaciones no doy respuestas directas.' },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [completedQuiz, setCompletedQuiz] = useState(null);
  const [completedFinalQuiz, setCompletedFinalQuiz] = useState(null);
  const [allowPdf, setAllowPdf] = useState(true);

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = 'lesson-page ui desktop-pro';
    setUnitId(unitFromLocation());
    setActivePanel(modeFromLocation());
    return () => {
      document.body.className = previous;
    };
  }, []);

  useEffect(() => {
    api.get('/api/learning-route')
      .then((data) => {
        if (Array.isArray(data.units) && data.units.length) setUnits(data.units);
      })
      .catch(() => {});

    api.get('/api/settings')
      .then((res) => {
        if (res && res.settings) {
          setAllowPdf(res.settings.allow_pdf_download === '1');
        }
      })
      .catch(() => {});
  }, []);

  const unit = useMemo(() => units.find((item) => Number(item.id) === Number(unitId)) || FALLBACK_UNITS[0], [units, unitId]);
  const resources = unitContent?.resources || unit.resources || [];
  const contentResource = resources.find((item) => item.type === 'unit_content') || resources[0];
  const workshopResource = resources.find((item) => item.type === 'workshop');
  const lessonQuestions = unitContent?.lesson_questions || [];

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError('');
    setUnitContent(null);
    api.get(`/api/learning-route/unit/${unitId}/content`)
      .then((data) => {
        if (!alive) return;
        setUnitContent(data);
        if (data.unit) {
          setUnits((current) => current.map((item) => (Number(item.id) === Number(unitId) ? { ...item, ...data.unit } : item)));
        }
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar el contenido oficial de la unidad.');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [unitId]);

  useEffect(() => {
    if (activePanel === 'exam') openQuiz();
    if (activePanel === 'final') openFinalQuiz();
  }, [activePanel, unitId]);

  function changeUnit(nextId) {
    setUnitId(nextId);
    setActivePanel('content');
    setLessonAnswers({});
    setLessonResult(null);
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setFinalQuiz(null);
    setFinalAnswers({});
    setFinalResult(null);
    window.history.replaceState(null, '', `/leccion?unidad=${nextId}`);
  }

  function switchPanel(panel) {
    setActivePanel(panel);
    if (panel !== 'exam') {
      setQuiz(null);
      setAnswers({});
      setResult(null);
    }
    if (panel !== 'final') {
      setFinalQuiz(null);
      setFinalAnswers({});
      setFinalResult(null);
    }
    window.history.replaceState(null, '', `/leccion?unidad=${unit.id}${panel === 'content' ? '' : `&modo=${panel}`}`);
  }

  async function markPractice() {
    setError('');
    try {
      await api.post(`/api/learning-route/unit/${unit.id}/practice`, {});
      setAssistantMessages((items) => [...items, { role: 'assistant', text: 'Taller iniciado. Resuelvelo y luego toma la leccion o el examen cuando estes lista.' }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la practica.');
    }
  }

  function submitLessonCheck() {
    if (!lessonQuestions.length) return;
    if (Object.keys(lessonAnswers).length < lessonQuestions.length) {
      setError('Responde todas las preguntas de la leccion antes de finalizar.');
      return;
    }
    setError('');
    const scoreObj = scoreLocalQuiz(lessonQuestions, lessonAnswers);
    setLessonResult(scoreObj);
  }

  async function openQuiz() {
    setError('');
    setResult(null);
    setAnswers({});
    try {
      const data = await api.get(`/api/learning-route/unit/${unit.id}/quiz`);
      setQuiz(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo abrir el examen de unidad.');
    }
  }

  async function submitQuiz() {
    if (!quiz?.questions?.length) return;
    if (Object.keys(answers).length < quiz.questions.length) {
      setError('Responde todas las preguntas antes de finalizar.');
      return;
    }
    setError('');
    try {
      const data = await api.post(`/api/learning-route/unit/${unit.id}/quiz`, { answers });
      setCompletedQuiz(quiz);
      setResult(data);
      setQuiz(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar el examen.');
    }
  }

  async function openFinalQuiz() {
    setError('');
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setFinalResult(null);
    setFinalAnswers({});
    try {
      const data = await api.get('/api/learning-route/final-quiz');
      setFinalQuiz(data);
      window.history.replaceState(null, '', '/leccion?modo=final');
    } catch (err) {
      setFinalQuiz(null);
      setError(err instanceof Error ? err.message : 'Completa las 4 unidades antes de abrir la evaluacion final.');
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
      setCompletedFinalQuiz(finalQuiz);
      setFinalResult(data);
      setFinalQuiz(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo calificar la evaluacion final.');
    }
  }

  async function downloadPdf(type, unitTitle, scoreObj, questionsData, userAnswers) {
    if (!allowPdf) {
      alert('La descarga de reportes PDF ha sido desactivada por el docente.');
      return;
    }
    const studentAlias = typeof window !== 'undefined' ? (JSON.parse(localStorage.getItem('yelia_profile') || '{}').alias || localStorage.getItem('yelia_active_student') || localStorage.getItem('yelia_guest_alias') || 'Estudiante') : 'Estudiante';
    
    const formattedQuestions = (questionsData || []).map((q) => {
      const selected = userAnswers[q.id] !== undefined ? Number(userAnswers[q.id]) : null;
      let correct = null;
      if (scoreObj?.details) {
        const det = scoreObj.details.find((d) => d.id === q.id);
        if (det && det.answer !== undefined) correct = Number(det.answer);
      }
      if (correct === null && q.answer !== undefined) {
        correct = Number(q.answer);
      }
      return {
        topic: q.topic || '',
        question: q.question || '',
        options: q.options || [],
        selected: selected,
        correct: correct
      };
    });
    
    const payload = {
      alias: studentAlias,
      type_label: type === 'lesson' ? 'Lección' : type === 'exam' ? 'Examen de Unidad' : 'Evaluación Final',
      unit_title: unitTitle,
      score: scoreObj?.score || 0,
      total: scoreObj?.total || 0,
      percent: scoreObj?.percent || 0,
      questions: formattedQuestions
    };
    
    try {
      const response = await fetch('/api/export/quiz-report.pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.message || 'No se pudo descargar el PDF.');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Reporte_${type === 'lesson' ? 'Leccion' : type === 'exam' ? 'Examen' : 'Evaluacion_Final'}_U${unitId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message || 'Error al generar el PDF.');
    }
  }

  function askAssistant() {
    const text = assistantText.trim();
    if (!text) return;
    setAssistantMessages((items) => [
      ...items,
      { role: 'user', text },
      { role: 'assistant', text: hintFor(unit, text) },
    ]);
    setAssistantText('');
  }

  function renderQuestionSet({ questions, currentAnswers, setCurrentAnswers }) {
    return questions.map((question, index) => (
      <section className="lesson-question" key={question.id}>
        <small>{index + 1}. {question.topic}</small>
        <h3>{question.question}</h3>
        <div className="lesson-answer-grid">
          {question.options.map((option, optionIndex) => (
            <button
              className={currentAnswers[question.id] === optionIndex ? 'is-picked' : ''}
              key={`${question.id}-${optionIndex}`}
              type="button"
              onClick={() => setCurrentAnswers((current) => ({ ...current, [question.id]: optionIndex }))}
            >
              <b>{String.fromCharCode(65 + optionIndex)}</b>
              <span>{option}</span>
            </button>
          ))}
        </div>
      </section>
    ));
  }

  return (
    <main className="lesson-shell" style={{ position: 'relative' }}>
      <aside className="lesson-helper">
        <a className="lesson-brand" href="/ruta">
          <span><i className="bi bi-stars" /></span>
          <b>YELIA apoyo</b>
          <small>Solo pistas</small>
        </a>
        <div className="lesson-helper-log">
          {assistantMessages.map((message, index) => (
            <div className={`lesson-helper-msg is-${message.role}`} key={`${message.role}-${index}`}>
              {message.text}
            </div>
          ))}
        </div>
        <div className="lesson-helper-input">
          <textarea value={assistantText} onChange={(event) => setAssistantText(event.target.value)} placeholder="Pregunta una duda, no la respuesta..." />
          <button type="button" onClick={askAssistant}><i className="bi bi-send-fill" /></button>
        </div>
      </aside>

      <section className="lesson-main">
        <header className="lesson-topbar">
          <div>
            <span>Leccion por unidad</span>
            <h1>Unidad {unit.id}: {unit.title}</h1>
            <p>{unit.subtitle}</p>
          </div>
          <nav>
            <a href="/ruta">Ruta</a>
            <a href="/progreso">Progreso</a>
            <a href="/chat">Chat general</a>
          </nav>
        </header>

        {error ? <div className="lesson-error">{error}</div> : null}
        {loading ? <div className="lesson-error is-info">Cargando contenido oficial de la unidad...</div> : null}

        <div className="lesson-unit-tabs">
          {units.map((item) => (
            <button className={Number(item.id) === Number(unit.id) ? 'is-active' : ''} key={item.id} type="button" onClick={() => changeUnit(item.id)}>
              U{item.id}
            </button>
          ))}
          <button className={activePanel === 'final' ? 'is-active' : ''} type="button" onClick={() => switchPanel('final')}>
            Examen final
          </button>
        </div>

        <div className="lesson-mode-tabs">
          <button className={activePanel === 'content' ? 'is-active' : ''} type="button" onClick={() => switchPanel('content')}>Contenido</button>
          <button className={activePanel === 'workshop' ? 'is-active' : ''} type="button" onClick={() => switchPanel('workshop')}>Taller</button>
          <button className={activePanel === 'lesson' ? 'is-active' : ''} type="button" onClick={() => switchPanel('lesson')}>Leccion</button>
          <button className={activePanel === 'exam' ? 'is-active' : ''} type="button" onClick={() => switchPanel('exam')}>Examen unidad</button>
        </div>

        {activePanel === 'content' ? (
          <article className="lesson-card">
            <div className="lesson-section-head">
              <span><i className="bi bi-book" /></span>
              <div>
                <h2>Contenido oficial</h2>
                <p>Material base cargado desde tu ZIP academico.</p>
              </div>
            </div>
            <div className="lesson-resource-card">
              <strong>{contentResource?.title || unit.title}</strong>
              <small>{contentResource?.source || 'Contenido de unidad'}</small>
              <p>{contentResource?.text_preview || 'No se encontro vista previa del contenido.'}</p>
            </div>
            <div className="lesson-topic-list">
              {(unit.topics || []).map((topic) => <span key={topic}>{topic}</span>)}
            </div>
          </article>
        ) : null}

        {activePanel === 'workshop' ? (
          <article className="lesson-card">
            <div className="lesson-section-head">
              <span><i className="bi bi-pencil-square" /></span>
              <div>
                <h2>Taller de practica</h2>
                <p>Actividad oficial de la unidad. Marcala como iniciada cuando empieces a resolverla.</p>
              </div>
            </div>
            <div className="lesson-resource-card">
              <strong>{workshopResource?.title || `Taller Unidad ${unit.id}`}</strong>
              <small>{workshopResource?.source || 'Taller de practica'}</small>
              <p>{workshopResource?.text_preview || 'No se encontro taller para esta unidad.'}</p>
            </div>
            <div className="lesson-actions">
              <button type="button" onClick={markPractice}>Marcar taller iniciado</button>
              <button type="button" onClick={() => switchPanel('lesson')}>Ir a leccion</button>
            </div>
          </article>
        ) : null}

        {activePanel === 'lesson' ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-ui-checks" /></span>
              <div>
                <h2>Leccion Unidad {unit.id}</h2>
                <p>Autoevaluacion de 5 preguntas antes del examen de unidad.</p>
              </div>
            </div>
            {lessonQuestions.length ? renderQuestionSet({
              questions: publicQuestions(lessonQuestions),
              currentAnswers: lessonAnswers,
              setCurrentAnswers: setLessonAnswers,
            }) : <p className="lesson-empty">No se encontraron preguntas de leccion para esta unidad.</p>}
            <div className="lesson-actions">
              <button type="button" onClick={submitLessonCheck}>Finalizar leccion</button>
              <button type="button" onClick={() => switchPanel('exam')}>Ir al examen</button>
            </div>
          </article>
        ) : null}

        {lessonResult ? (
          <article className={`lesson-result ${lessonResult.percent >= 70 ? 'is-pass' : 'is-retry'}`}>
            <span>{lessonResult.percent >= 70 ? 'Leccion aprobada' : 'Conviene repasar'}</span>
            <strong>{lessonResult.percent}%</strong>
            <p>Resultado de leccion: {lessonResult.score}/{lessonResult.total}. {lessonResult.percent >= 70 ? 'Puedes pasar al examen de unidad.' : 'Revisa el contenido y vuelve a intentar.'}</p>
            {allowPdf ? (
              <button 
                type="button" 
                className="lesson-pdf-btn" 
                style={{ marginTop: '12px', background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '500' }}
                onClick={() => downloadPdf('lesson', unit.title, lessonResult, lessonQuestions, lessonAnswers)}
              >
                <i className="bi bi-file-pdf"></i> Descargar Reporte PDF
              </button>
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginTop: '8px', display: 'block' }}>
                <i className="bi bi-info-circle"></i> Descarga de PDF desactivada por el docente
              </span>
            )}
          </article>
        ) : null}

        {activePanel === 'exam' && quiz ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-clipboard-check" /></span>
              <div>
                <h2>Examen Unidad {unit.id}</h2>
                <p>Examen oficial de 10 preguntas. Necesitas {quiz.passing_score || 70}% para desbloquear la siguiente unidad.</p>
              </div>
            </div>
            {renderQuestionSet({ questions: quiz.questions, currentAnswers: answers, setCurrentAnswers: setAnswers })}
            <div className="lesson-actions">
              <button type="button" onClick={submitQuiz}>Finalizar examen</button>
              <button type="button" onClick={() => switchPanel('content')}>Cerrar</button>
            </div>
          </article>
        ) : null}

        {result ? (
          <article className={`lesson-result ${result.result?.passed ? 'is-pass' : 'is-retry'}`}>
            <span>{result.result?.passed ? 'Unidad aprobada' : 'Necesita refuerzo'}</span>
            <strong>{result.result?.percent || 0}%</strong>
            <p>{result.feedback}</p>
            {allowPdf ? (
              <button 
                type="button" 
                className="lesson-pdf-btn" 
                style={{ marginTop: '0px', marginBottom: '12px', background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '500' }}
                onClick={() => downloadPdf('exam', unit.title, result.result, completedQuiz?.questions, answers)}
              >
                <i className="bi bi-file-pdf"></i> Descargar Reporte PDF
              </button>
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginBottom: '12px', display: 'block' }}>
                <i className="bi bi-info-circle"></i> Descarga de PDF desactivada por el docente
              </span>
            )}
            <div className="lesson-actions">
              <a href="/ruta">Volver a ruta</a>
              <a href="/progreso">Ver progreso</a>
            </div>
          </article>
        ) : null}

        {activePanel === 'final' && finalQuiz ? (
          <article className="lesson-card lesson-quiz">
            <div className="lesson-section-head">
              <span><i className="bi bi-award" /></span>
              <div>
                <h2>Evaluacion final</h2>
                <p>Solo se habilita al completar Unidad 1, Unidad 2, Unidad 3 y Unidad 4. Necesitas {finalQuiz.passing_score || 70}%.</p>
              </div>
            </div>
            {renderQuestionSet({ questions: finalQuiz.questions, currentAnswers: finalAnswers, setCurrentAnswers: setFinalAnswers })}
            <div className="lesson-actions">
              <button type="button" onClick={submitFinalQuiz}>Finalizar evaluacion</button>
              <button type="button" onClick={() => switchPanel('content')}>Cerrar</button>
            </div>
          </article>
        ) : null}

        {finalResult ? (
          <article className={`lesson-result ${finalResult.result?.passed ? 'is-pass' : 'is-retry'}`}>
            <span>{finalResult.result?.passed ? 'Ruta completada' : 'Refuerzo final'}</span>
            <strong>{finalResult.result?.percent || 0}%</strong>
            <p>{finalResult.feedback}</p>
            {allowPdf ? (
              <button 
                type="button" 
                className="lesson-pdf-btn" 
                style={{ marginTop: '0px', marginBottom: '12px', background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: '500' }}
                onClick={() => downloadPdf('final', 'Evaluación Final', finalResult.result, completedFinalQuiz?.questions, finalAnswers)}
              >
                <i className="bi bi-file-pdf"></i> Descargar Reporte PDF
              </button>
            ) : (
              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)', marginBottom: '12px', display: 'block' }}>
                <i className="bi bi-info-circle"></i> Descarga de PDF desactivada por el docente
              </span>
            )}
            <div className="lesson-actions">
              <a href="/ruta">Volver a ruta</a>
              <a href="/progreso">Ver progreso</a>
            </div>
          </article>
        ) : null}
      </section>
    </main>
  );
}
