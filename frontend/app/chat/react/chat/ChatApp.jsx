'use client';

import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { api } from '../core/api.js';
import { notify } from '../core/notify.js';
import { readStorage, removeStorage, writeStorage } from '../core/storage.js';
import AvatarPanel from '../avatar/AvatarPanel.jsx';
import { useSpeech } from '../voice/useSpeech.js';

function getProfile() {
  try {
    return JSON.parse(readStorage('yelia_profile', '{}') || '{}');
  } catch {
    return {};
  }
}

function saveProfile(profile) {
  writeStorage('yelia_profile', JSON.stringify(profile || {}));
}

function profileNeedsSetup(profile = {}) {
  return Boolean(profile?.alias?.trim()) && !(profile.ciclo && profile.estado && profile.nivel);
}

function profileFromProgress(current = {}, progreso = {}) {
  const next = {
    ...current,
    ciclo: progreso.ciclo_academico || current.ciclo || '',
    estado: progreso.estado_materia || current.estado || '',
    nivel: progreso.nivel_materia || current.nivel || '',
  };
  if (next.ciclo || next.estado || next.nivel) saveProfile(next);
  return next;
}

const ROUTE_UNITS = {
  1: {
    id: 1,
    title: 'Fundamentos de POO',
    topics: ['Introduccion a POO', 'Clases y Objetos', 'Atributos y metodos', 'Encapsulamiento'],
    prompt: 'Quiero empezar la Unidad 1: Fundamentos de POO. Explicame desde mi nivel y dame una actividad corta.',
  },
  2: {
    id: 2,
    title: 'Herencia, polimorfismo e interfaces',
    topics: ['Herencia', 'Polimorfismo', 'Sobrecarga y sobrescritura', 'Interfaces'],
    prompt: 'Quiero trabajar la Unidad 2: Herencia, polimorfismo e interfaces. Dame explicacion, ejemplo y practica.',
  },
  3: {
    id: 3,
    title: 'UML y patron MVC',
    topics: ['Diagramas UML', 'Casos de uso', 'Secuencia y actividad', 'MVC'],
    prompt: 'Quiero estudiar la Unidad 3: UML y patron MVC. Guiame con ejemplos y una practica aplicada.',
  },
  4: {
    id: 4,
    title: 'Archivos, base de datos y buenas practicas',
    topics: ['Acceso a archivos', 'Bases de Datos y ORM', 'Integracion POO/MVC/Datos', 'Pruebas'],
    prompt: 'Quiero avanzar con la Unidad 4: archivos, base de datos, ORM y buenas practicas.',
  },
};

function readRouteContext() {
  if (typeof window === 'undefined') return null;
  const params = new URLSearchParams(window.location.search);
  const rawUnit = Number(params.get('routeUnit') || readStorage('yelia_route_unit', '0'));
  const unit = ROUTE_UNITS[rawUnit];
  const prompt = readStorage('yelia_route_prompt', '') || unit?.prompt || '';
  if (!unit && !prompt) return null;
  return {
    ...(unit || { id: rawUnit || 1, title: 'Ruta de aprendizaje', topics: ['Programacion Avanzada'] }),
    prompt,
  };
}

function newGuestId() {
  const id = (typeof window !== 'undefined' && window.crypto?.randomUUID?.()) || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const safe = id.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 48);
  writeStorage('yelia_guest_id', safe);
  return safe;
}

function topicFromText(text = '') {
  const value = text.toLowerCase();
  if (value.includes('mvc') || value.includes('modelo vista controlador')) return 'Arquitectura MVC';
  if (value.includes('uml') || value.includes('diagrama')) return 'Diagramas UML';
  if (value.includes('jdbc') || value.includes('orm') || value.includes('base de datos') || value.includes('sql')) return 'Bases de Datos y ORM';
  if (value.includes('herencia')) return 'Herencia';
  if (value.includes('clase') || value.includes('objeto')) return 'Clases y Objetos';
  if (value.includes('polimorf')) return 'Polimorfismo';
  return 'Programacion Avanzada';
}

function shouldKeepCurrentTopic(text = '') {
  const value = text.toLowerCase();
  if (/(?:^|[\s,;])\d+\s*[:.)-]?\s*[abcd](?:$|[\s,;])/i.test(value)) return true;
  return [
    'esta respuesta',
    'este tema',
    'explicame mejor',
    'dame un ejemplo',
    'hazme un quiz',
    'repasemos',
    'mis errores',
  ].some((fragment) => value.includes(fragment));
}

function normalizeRecommendation(item = {}) {
  const action = item.action || item.prompt || item.suggested_action || item.next_action || '';
  return {
    ...item,
    title: item.title || item.label || item.topic || item.type || 'Recomendacion',
    description: item.explanation || item.reason || item.description || item.motivo || 'Sugerencia adaptada por YELIA.',
    prompt: action || item.title || item.label || item.topic || 'Dame una practica guiada',
  };
}

const LEVEL_LABELS = {
  basico: 'Basico',
  intermedio: 'Intermedio',
  avanzado: 'Avanzado',
};

const STRATEGY_LABELS = {
  reinforce_foundations: 'Reforzar bases',
  increase_challenge: 'Subir el reto',
  guided_practice: 'Practica guiada',
  review_answer: 'Revisar respuesta',
  continue_learning: 'Continuar aprendiendo',
};

const ACTION_LABELS = {
  explain_simpler: 'Explicacion mas simple',
  practice_or_quiz: 'Practica o quiz',
  guided_practice: 'Practica guiada',
  review_answer: 'Revision de respuesta',
  recommend_next_resource: 'Recomendar recurso',
};

function humanLevel(value) {
  return LEVEL_LABELS[String(value || '').toLowerCase()] || value || 'Sin definir';
}

function humanStrategy(value) {
  return STRATEGY_LABELS[String(value || '').toLowerCase()] || value || 'Continuar aprendiendo';
}

function humanAction(value) {
  return ACTION_LABELS[String(value || '').toLowerCase()] || value || 'Siguiente paso';
}

function syllabusUnit(item = {}) {
  return item.syllabus_unit || item.syllabusUnit || item.unit || item.extra?.syllabus_unit || '';
}

function isResourceItem(item = {}) {
  const type = String(item.type || '').toLowerCase();
  return ['web_resource', 'resource', 'recurso'].includes(type)
    || Boolean(item.url || item.source);
}

function wantsVisibleResources(text = '') {
  const value = String(text || '').toLowerCase();
  return [
    'recurso',
    'recursos',
    'link',
    'enlace',
    'pagina',
    'página',
    'web',
    'fuente',
    'fuentes',
    'tutorial',
    'documentacion',
    'documentación',
    'material',
    'guia',
    'guía',
  ].some((term) => value.includes(term));
}

function wantsLearningFollowup(text = '') {
  const value = String(text || '').toLowerCase();
  return [
    'corrige',
    'corregir',
    'retroaliment',
    'feedback',
    'revisa',
    'revisar',
    'mejorar',
    'progreso',
    'ruta',
    'nivel',
    'que sigo',
    'qué sigo',
    'siguiente paso',
  ].some((term) => value.includes(term));
}

function extractLearningEvidence(data = {}) {
  const userText = data.user_text || data.userText || '';
  const structuredQuiz = Boolean(data.structured_quiz);
  const structuredGrade = Boolean(data.structured_grade);
  const showResources = wantsVisibleResources(userText);
  const showFollowup = structuredGrade || wantsLearningFollowup(userText);
  const rawItems = [
    ...(Array.isArray(data.recommendations) ? data.recommendations : []),
    ...(Array.isArray(data.suggestions) ? data.suggestions : []),
  ];
  const resources = [];
  const actions = [];

  rawItems.forEach((item) => {
    const normalized = normalizeRecommendation(item);
    if (isResourceItem(item)) {
      if (showResources) resources.push(normalized);
    } else if (!structuredQuiz && showFollowup) {
      actions.push(normalized);
    }
  });

  const rawFeedback = data.personalized_feedback && typeof data.personalized_feedback === 'object'
    ? data.personalized_feedback
    : null;
  const feedback = showFollowup ? rawFeedback : null;
  if (feedback?.action || feedback?.summary) {
    actions.push(normalizeRecommendation({
      title: feedback.summary || 'Retroalimentacion personalizada',
      description: feedback.reason || feedback.recommendation || feedback.action || 'Siguiente paso recomendado.',
      prompt: feedback.action || 'Ayudame a reforzar este tema',
      type: 'feedback',
    }));
  }

  const adaptivePlan = data.adaptive_plan && typeof data.adaptive_plan === 'object' && showFollowup
    ? data.adaptive_plan
    : null;
  if (adaptivePlan?.next_best_action) {
    actions.push(normalizeRecommendation({
      title: `Ruta adaptativa: ${humanStrategy(adaptivePlan.strategy)}`,
      description: adaptivePlan.rationale || adaptivePlan.prompt_hint || 'Ajuste de nivel y ritmo segun tu progreso.',
      prompt: adaptivePlan.next_best_action === 'explain_simpler'
        ? `Explicame ${adaptivePlan.topic || data.tema || 'este tema'} mas simple`
        : adaptivePlan.next_best_action === 'practice_or_quiz'
          ? `Dame una practica corta de ${adaptivePlan.topic || data.tema || 'este tema'}`
          : adaptivePlan.prompt_hint || 'Continua con la ruta adaptativa',
      type: 'adaptive_plan',
    }));
  }

  const unique = (items) => {
    const seen = new Set();
    return items.filter((item) => {
      const key = `${item.title}|${item.description}|${item.url || ''}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  return {
    resources: unique(resources).slice(0, 5),
    feedback,
    adaptivePlan,
    actions: unique(actions).slice(0, 6),
  };
}

function mergeRecommendationPayload(data = {}) {
  const items = [];
  if (Array.isArray(data.recommendations)) items.push(...data.recommendations);
  if (Array.isArray(data.suggestions)) items.push(...data.suggestions);
  if (data.tutor?.exercise) {
    items.push({
      title: data.tutor.exercise.title || 'Practica adaptativa',
      description: data.tutor.exercise.description || 'Ejercicio sugerido segun tu nivel.',
      prompt: data.tutor.exercise.prompt || `Practiquemos ${data.tema || 'este tema'} paso a paso`,
      type: 'practica',
    });
  }
  if (data.personalized_feedback?.action || data.personalized_feedback?.summary) {
    items.push({
      title: data.personalized_feedback.summary || 'Retroalimentacion personalizada',
      description: data.personalized_feedback.reason || data.personalized_feedback.action || 'Siguiente paso recomendado.',
      prompt: data.personalized_feedback.action || 'Ayudame a reforzar este tema',
      type: 'feedback',
    });
  }
  if (data.structured_grade) {
    const score = `${data.structured_grade.score || 0}/${data.structured_grade.total || 0}`;
    items.push({
      title: `Resultado del quiz: ${score}`,
      description: 'Refuerza los puntos incorrectos o sube la dificultad.',
      prompt: 'Repasemos mis errores del quiz y dame una practica guiada',
      type: 'quiz_result',
    });
  }
  const seen = new Set();
  return items.map(normalizeRecommendation).filter((item) => {
    const key = `${item.title}|${item.description}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function plain(html = '') {
  return String(html).replace(/<[^>]+>/g, ' ').slice(0, 500);
}

function cleanAssistantReply(text = '') {
  const value = String(text || '');
  const markers = [
    '\n\nRecomendacion por historial:',
    '\n\nRecomendación por historial:',
    '\n\nActividades sugeridas según tu nivel',
    '\n\nActividades sugeridas segun tu nivel',
    '\n\nRetroalimentacion personalizada:',
    '\n\nRetroalimentación personalizada:',
  ];
  const positions = markers.map((marker) => value.indexOf(marker)).filter((index) => index >= 0);
  if (!positions.length) return value;
  return value.slice(0, Math.min(...positions)).trim();
}

function cleanControlledAssistantReply(text = '', hasControlledEvidence = false) {
  let value = String(text || '');
  if (!hasControlledEvidence) return value;
  const markers = [
    '\n\nRecomendaciones',
    '\nRecomendaciones\n',
    '\n\nRecursos recomendados',
    '\nRecursos web recomendados:',
  ];
  const positions = markers.map((marker) => value.indexOf(marker)).filter((index) => index >= 0);
  if (positions.length) value = value.slice(0, Math.min(...positions)).trim();
  return value;
}

function speechPlain(text = '') {
  return String(text || '')
    .replace(/```[\s\S]*?```/g, ' bloque de codigo. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/^\s*\d+[.)]\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/[_*~>#|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function speechAutoText(text = '', data = {}) {
  const quiz = data?.structured_quiz;
  if (quiz) {
    const total = Number(quiz.total || quiz.questions?.length || 0);
    const topic = quiz.topic || data.topic || data.tema || 'este tema';
    return `Te prepare un quiz de ${total || 'varias'} preguntas sobre ${topic}. Puedes responder con el formato 1a, 2b, 3c.`;
  }

  const grade = data?.structured_grade;
  if (grade) {
    const score = Number(grade.score || 0);
    const total = Number(grade.quiz_total || grade.total || 0);
    return `Resultado del quiz: obtuviste ${score} de ${total}. Revisa la correccion breve en pantalla.`;
  }

  return speechPlain(text);
}

function normalizeBackendAvatarState(contract) {
  if (!contract || typeof contract !== 'object') return contract;
  if (contract.state !== 'speaking' && contract.speaking !== true) return contract;
  return {
    ...contract,
    state: 'idle',
    speaking: false,
    mouth_shape: contract.mouth_shape === 'open' ? 'closed' : contract.mouth_shape,
  };
}

function inlineMarkdown(text = '') {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    return part;
  });
}

function looksLikeCodeLine(rawLine = '') {
  const line = String(rawLine || '').trim();
  if (!line) return false;
  return /^(?:public|private|protected|class|static|final|return|if|else|for|while|switch|case|break|continue|try|catch|finally|throw|throws|import|package)\b/.test(line)
    || /^System\.out\./.test(line)
    || /^this\./.test(line)
    || /^[{}]$/.test(line)
    || /^}\s*(?:else|catch|finally)\b/.test(line)
    || /[;{}]$/.test(line)
    || /^[A-Z][A-Za-z0-9_<>[\]]*\s+[a-zA-Z_$][\w$]*\s*\(/.test(line)
    || /^(?:String|int|double|float|boolean|char|long|short|byte|void)\b/.test(line);
}

function renderMarkdown(text = '') {
  const normalized = String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(/\s---\s/g, '\n\n')
    .replace(/\s(#{1,3}\s+)/g, '\n$1')
    .replace(/\s(\d+[.)]\s+)/g, '\n$1')
    .replace(/\s([a-d][.)]\s+)/gi, '\n$1');
  const lines = normalized.split('\n');
  const nodes = [];
  let listItems = [];
  let orderedItems = [];
  let alphaItems = [];
  let codeLines = [];
  let inCode = false;
  let autoCode = false;

  function flushList(includeAlpha = true) {
    if (listItems.length) {
      nodes.push(<ul key={`ul-${nodes.length}`}>{listItems.map((item, index) => <li key={index}>{inlineMarkdown(item)}</li>)}</ul>);
      listItems = [];
    }
    if (orderedItems.length) {
      const start = orderedItems[0]?.number || 1;
      nodes.push(
        <ol key={`ol-${nodes.length}`} start={start}>
          {orderedItems.map((item, index) => <li key={index}>{inlineMarkdown(item.text)}</li>)}
        </ol>
      );
      orderedItems = [];
    }
    if (includeAlpha && alphaItems.length) {
      const start = alphaItems[0]?.number || 1;
      nodes.push(
        <ol className="yelia-alpha-list" key={`alpha-${nodes.length}`} start={start} type="a">
          {alphaItems.map((item, index) => <li key={index}>{inlineMarkdown(item.text)}</li>)}
        </ol>
      );
      alphaItems = [];
    }
  }

  function flushCode(keyPrefix = 'code') {
    if (!codeLines.length) return;
    nodes.push(<pre className="yelia-code-block" key={`${keyPrefix}-${nodes.length}`}><code>{codeLines.join('\n')}</code></pre>);
    codeLines = [];
    autoCode = false;
  }

  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (line.startsWith('```')) {
      if (inCode) {
        flushCode('code');
        inCode = false;
      } else {
        flushList();
        if (autoCode) flushCode('autocode');
        inCode = true;
      }
      return;
    }
    if (inCode) {
      codeLines.push(rawLine);
      return;
    }
    if (autoCode) {
      if (!line) {
        flushCode('autocode');
        return;
      }
      if (looksLikeCodeLine(rawLine)) {
        codeLines.push(rawLine);
        return;
      }
      flushCode('autocode');
    }
    if (!line) {
      flushList();
      return;
    }
    if (/^#{1,6}$/.test(line)) {
      flushList();
      return;
    }
    if (line.startsWith('### ')) {
      flushList();
      nodes.push(<h3 key={`h3-${nodes.length}`}>{inlineMarkdown(line.slice(4))}</h3>);
      return;
    }
    if (line.startsWith('## ')) {
      flushList();
      nodes.push(<h2 key={`h2-${nodes.length}`}>{inlineMarkdown(line.slice(3))}</h2>);
      return;
    }
    if (line.startsWith('# ')) {
      flushList();
      nodes.push(<h2 key={`h2-${nodes.length}`}>{inlineMarkdown(line.slice(2))}</h2>);
      return;
    }
    if (/^[-*]\s+/.test(line)) {
      if (alphaItems.length) flushList();
      orderedItems = [];
      alphaItems = [];
      listItems.push(line.replace(/^[-*]\s+/, ''));
      return;
    }
    const numberedMatch = line.match(/^(\d+)[.)]\s+(.+)/);
    if (numberedMatch) {
      if (alphaItems.length) flushList();
      listItems = [];
      alphaItems = [];
      orderedItems.push({ number: Number(numberedMatch[1]) || 1, text: numberedMatch[2] });
      return;
    }
    const alphaMatch = line.match(/^([a-d])[.)]\s+(.+)/i);
    if (alphaMatch) {
      flushList(false);
      const number = alphaMatch[1].toLowerCase().charCodeAt(0) - 96;
      alphaItems.push({ number, text: alphaMatch[2] });
      return;
    }
    if (looksLikeCodeLine(rawLine)) {
      flushList();
      autoCode = true;
      codeLines.push(rawLine);
      return;
    }
    flushList();
    nodes.push(<p key={`p-${nodes.length}`}>{inlineMarkdown(line)}</p>);
  });
  flushList();
  flushCode('code-open');
  return nodes;
}

function parseMiniQuiz(text = '') {
  const raw = String(text || '');
  const quizMatch = raw.match(/(^|\n)\s*(?:#{1,6}\s*)?(?:mini\s+)?quiz\b[^\n]*/i);
  if (!quizMatch) return null;

  const quizIndex = (quizMatch.index || 0) + (quizMatch[1] || '').length;
  const intro = raw.slice(0, quizIndex).trim();
  const quizText = raw.slice(quizIndex)
    .replace(/^\s*#{1,6}\s*/, '')
    .replace(/\s(\d+[.)]\s+)/g, '\n$1')
    .replace(/\s([a-d][.)]\s+)/gi, '\n$1')
    .trim();
  const lines = quizText.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && line !== '---');
  const title = lines[0] && !/^\d+[.)]\s+/.test(lines[0]) && !/^[a-d][.)]\s+/i.test(lines[0])
    ? lines.shift().replace(/^mini\s+quiz\s*:?\s*/i, 'Quiz: ').trim()
    : 'Mini quiz';
  const questions = [];
  let current = null;

  lines.forEach((line) => {
    if (/cual de las preguntas|cu[aá]l de las preguntas|responder primero/i.test(line)) return;
    const optionMatch = line.match(/^([a-d])[.)]\s+(.+)/i);
    if (optionMatch && current) {
      current.options.push({ letter: optionMatch[1].toLowerCase(), text: optionMatch[2].trim() });
      return;
    }

    const numberedMatch = line.match(/^(\d+)[.)]\s+(.+)/);
    const looksLikeQuestion = /[?¿]\s*$/.test(line) || numberedMatch;
    if (looksLikeQuestion) {
      if (current) questions.push(current);
      current = {
        text: (numberedMatch ? numberedMatch[2] : line).trim(),
        options: [],
      };
      return;
    }

    if (current && !current.options.length) {
      current.text = `${current.text} ${line}`.trim();
    }
  });

  if (current) questions.push(current);
  const usableQuestions = questions.filter((question) => question.text && question.options.length >= 2);
  if (!usableQuestions.length) return null;
  return { intro, title, questions: usableQuestions };
}

function renderMiniQuiz(text = '', onQuizOption) {
  const parsed = parseMiniQuiz(text);
  if (!parsed) return null;
  return (
    <>
      {parsed.intro && <div className="yelia-markdown">{renderMarkdown(parsed.intro)}</div>}
      <section className="yelia-mini-quiz-card">
        <div className="yelia-mini-quiz-head">
          <span><i className="bi bi-ui-checks"></i> Quiz</span>
          <strong>{parsed.title}</strong>
        </div>
        <div className="yelia-mini-quiz-list">
          {parsed.questions.map((question, questionIndex) => (
            <article className="yelia-mini-quiz-question" key={`${question.text}-${questionIndex}`}>
              <h3>
                <span>{questionIndex + 1}</span>
                <span className="yelia-mini-quiz-question-text">{inlineMarkdown(question.text)}</span>
              </h3>
              <div className="yelia-mini-quiz-options">
                {question.options.map((option) => (
                  <button
                    type="button"
                    key={`${questionIndex}-${option.letter}`}
                    onClick={() => onQuizOption?.({
                      questionNumber: questionIndex + 1,
                      question: question.text,
                      letter: option.letter,
                      text: option.text,
                    })}
                    title="Usar esta respuesta"
                  >
                    <b>{option.letter}</b>
                    <span>{inlineMarkdown(option.text)}</span>
                  </button>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function renderMessageContent(message = {}, onQuizOption) {
  const text = message.html || message.text || '';
  const quiz = message.role !== 'user' ? renderMiniQuiz(text, onQuizOption) : null;
  if (quiz) return quiz;
  return <div className="yelia-markdown">{renderMarkdown(text)}</div>;
}

function parseBackendDate(value) {
  if (!value) return new Date();
  if (value instanceof Date) return value;
  const raw = String(value).trim();
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T');
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(normalized);
  const date = new Date(hasZone ? normalized : `${normalized}Z`);
  if (!Number.isNaN(date.getTime())) return date;
  const fallback = new Date(raw);
  return Number.isNaN(fallback.getTime()) ? new Date() : fallback;
}

function formatDateTime(value) {
  const date = parseBackendDate(value);
  return new Intl.DateTimeFormat('es-EC', {
    timeZone: 'America/Guayaquil',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);
}

function messageTime(value) {
  return formatDateTime(value || new Date());
}

function providerLabel(value) {
  const provider = String(value || '').toLowerCase();
  if (!provider) return 'Proveedor no registrado';
  if (provider.includes('gemini')) return 'Gemini';
  if (provider.includes('groq')) return 'Groq';
  if (provider.includes('deep')) return 'DeepSeek';
  if (provider.includes('local')) return 'Local';
  if (provider.includes('error')) return 'Error';
  return provider.charAt(0).toUpperCase() + provider.slice(1);
}

function formatDurationMs(value) {
  const ms = Number(value || 0);
  if (!ms) return '';
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  if (seconds < 10) return `${seconds.toFixed(1)} s`;
  return `${Math.round(seconds)} s`;
}

function providerMeta(message = {}) {
  const provider = providerLabel(message.provider);
  const duration = formatDurationMs(message.responseMs || message.response_ms);
  return duration ? `${provider} · ${duration}` : provider;
}

function titleOfConversation(item) {
  return item?.title || item?.titulo || item?.resumen || 'Conversacion';
}

function messageText(message = {}) {
  return String(message.html || message.text || '').replace(/<[^>]+>/g, ' ');
}

function lastTopicFromMessages(messages, fallback) {
  for (let index = messages.length - 1; index >= 0; index -= 1) {
    if (messages[index]?.tema) return messages[index].tema;
  }
  return fallback;
}

const PROFILE_OPTIONS = {
  ciclo: [
    { value: 'Primero', label: 'Primero', detail: 'Estoy iniciando la carrera y necesito bases claras.' },
    { value: 'Segundo', label: 'Segundo', detail: 'Ya curse materias introductorias y necesito ejemplos guiados.' },
    { value: 'Tercero', label: 'Tercero', detail: 'Estoy fortaleciendo programacion y logica.' },
    { value: 'Cuarto', label: 'Cuarto', detail: 'Puedo avanzar con problemas un poco mas aplicados.' },
    { value: 'Quinto', label: 'Quinto', detail: 'Busco explicaciones mas tecnicas y ejercicios completos.' },
    { value: 'Sexto', label: 'Sexto', detail: 'Necesito conectar teoria con desarrollo real.' },
    { value: 'Septimo', label: 'Septimo', detail: 'Quiero repasar y resolver dudas puntuales.' },
    { value: 'Octavo', label: 'Octavo', detail: 'Busco practica avanzada y retroalimentacion directa.' },
    { value: 'Noveno', label: 'Noveno', detail: 'Quiero consolidar conocimientos para proyectos.' },
    { value: 'Decimo', label: 'Decimo', detail: 'Estoy cerca del cierre y necesito precision academica.' },
    { value: 'Egresado', label: 'Egresado', detail: 'Uso el asistente para repaso, tesis o practica profesional.' },
    { value: 'Graduado', label: 'Graduado', detail: 'Ya termine la carrera y uso YELIA para repaso o practica profesional.' },
  ],
  estado: [
    { value: 'No la veo aun', label: 'No la veo aun', detail: 'Elige esto si todavia no cursas la materia y quieres empezar desde cero.' },
    { value: 'La estoy cursando', label: 'La estoy cursando', detail: 'Estoy viendo la materia ahora y quiero acompanamiento segun la clase.' },
    { value: 'Aprendiendo', label: 'Aprendiendo', detail: 'Estoy entendiendo poco a poco y necesito explicaciones paso a paso.' },
    { value: 'Repitiendo', label: 'Repitiendo', detail: 'Elige esto si repites la materia y necesitas apoyo mas guiado.' },
    { value: 'Ya la vi', label: 'Ya la vi', detail: 'Ya curse la materia y uso YELIA para repasar, aclarar dudas o practicar.' },
    { value: 'Ya la aprobe', label: 'Ya la aprobe', detail: 'Ya aprobe la materia y quiero reforzar para proyectos, tesis o practica profesional.' },
    { value: 'Repasando', label: 'Repasando', detail: 'Elige esto si ya viste el tema y quieres reforzar.' },
    { value: 'Preparando examen', label: 'Preparando examen', detail: 'Elige esto si necesitas preguntas, resumenes y practica.' },
  ],
  nivel: [
    { value: 'Sin conocimientos', label: 'Sin conocimientos', detail: 'Necesito empezar desde lo mas basico, sin asumir conocimientos previos.' },
    { value: 'Basico', label: 'Basico', detail: 'Necesito ejemplos simples y conceptos desde cero.' },
    { value: 'Intermedio', label: 'Intermedio', detail: 'Entiendo lo esencial y quiero practicar con casos.' },
    { value: 'Avanzado', label: 'Avanzado', detail: 'Puedo trabajar con retos y explicaciones tecnicas.' },
  ],
};

function selectedDetail(group, value) {
  return PROFILE_OPTIONS[group].find((item) => item.value === value)?.detail || '';
}

function ProfileOptionGroup({ group, value, onChange }) {
  return (
    <div className="yelia-profile-option-grid" role="listbox">
      {PROFILE_OPTIONS[group].map((item) => {
        const active = item.value === value;
        return (
          <button
            aria-selected={active}
            className={`yelia-profile-option ${active ? 'is-selected' : ''}`}
            key={item.value}
            onClick={() => onChange(item.value)}
            role="option"
            type="button"
          >
            <span className="yelia-profile-option-title">
              {item.label}
              {active && <i className="bi bi-check2-circle"></i>}
            </span>
            <span>{item.detail}</span>
          </button>
        );
      })}
    </div>
  );
}

function Message({ m, index, isSearchMatch, isCurrentMatch, onFeedback, onCopy, onSpeak, onQuick, onQuizOption }) {
  const evidence = m.learningEvidence || {};
  const resources = Array.isArray(evidence.resources) ? evidence.resources : [];
  const feedback = evidence.feedback;
  const adaptivePlan = evidence.adaptivePlan;
  return (
    <div
      className={`yelia-message ${m.role === 'user' ? 'yelia-message-user' : 'yelia-message-bot'} ${isSearchMatch ? 'is-search-match' : ''} ${isCurrentMatch ? 'is-current-match' : ''}`}
      data-message-index={index}
    >
      <div className="yelia-message-header">
        <span className="yelia-message-name">{m.role === 'user' ? 'Tu' : 'YELIA'}</span>
        {m.role !== 'user' && m.provider && <span className="yelia-provider-chip">{providerMeta(m)}</span>}
        {m.role !== 'user' && m.structuredGrade && (
          <span className="yelia-provider-chip yelia-score-chip">
            Quiz {m.structuredGrade.score || 0}/{m.structuredGrade.total || 0}
          </span>
        )}
        <span>{m.time}</span>
      </div>
      <div className="yelia-message-body">
        {renderMessageContent(m, onQuizOption)}
      </div>
      {m.role !== 'user' && !m.welcome && (resources.length || feedback || adaptivePlan) && (
        <div className="yelia-learning-evidence">
          {resources.length > 0 && (
            <section className="yelia-evidence-card">
              <span className="yelia-evidence-kicker"><i className="bi bi-book"></i> Recursos controlados</span>
              <div className="yelia-evidence-list">
                {resources.slice(0, 3).map((item, itemIndex) => {
                  const unit = syllabusUnit(item);
                  return (
                    <div className="yelia-evidence-resource" key={`${item.title}-${itemIndex}`}>
                      <strong>{item.title}</strong>
                      {unit && <em>{unit}</em>}
                      <small>{item.description}</small>
                      <span className="yelia-resource-actions">
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noreferrer">
                            Abrir recurso <i className="bi bi-box-arrow-up-right"></i>
                          </a>
                        )}
                        <button type="button" onClick={() => onQuick?.(item.prompt || item.title)}>
                          Usar en chat
                        </button>
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
          {feedback && (
            <section className="yelia-evidence-card">
              <span className="yelia-evidence-kicker"><i className="bi bi-star"></i> Retroalimentacion</span>
              <strong>{feedback.summary || feedback.message || 'Siguiente paso personalizado'}</strong>
              <small>{feedback.reason || feedback.recommendation || feedback.action || 'YELIA ajusto el apoyo segun tu mensaje.'}</small>
            </section>
          )}
          {adaptivePlan && (
            <section className="yelia-evidence-card">
              <span className="yelia-evidence-kicker"><i className="bi bi-diagram-3"></i> Ruta adaptativa</span>
              {adaptivePlan.rationale && <small>{adaptivePlan.rationale}</small>}
              <div className="yelia-evidence-grid">
                <span>Nivel recomendado</span><b>{humanLevel(adaptivePlan.current_level)} {'->'} {humanLevel(adaptivePlan.selected_level)}</b>
                <span>Que hara YELIA</span><b>{humanStrategy(adaptivePlan.strategy)}</b>
                <span>Siguiente paso</span><b>{humanAction(adaptivePlan.next_best_action)}</b>
              </div>
            </section>
          )}
        </div>
      )}
      {m.role !== 'user' && !m.welcome && (
        <div className="yelia-message-tools">
          <div className="yelia-message-tool-row">
            <button onClick={() => onCopy?.(m)} type="button"><i className="bi bi-copy"></i> Copiar</button>
            <button onClick={() => onSpeak?.(m)} type="button"><i className="bi bi-volume-up"></i> Escuchar</button>
            <button onClick={() => onQuick?.('Explicame mejor esta respuesta')} type="button">Explicame mejor</button>
            <button onClick={() => onQuick?.('Dame un ejemplo practico de esta respuesta')} type="button">Dame ejemplo</button>
            <button onClick={() => onQuick?.('Hazme un quiz corto sobre esta respuesta')} type="button">Hazme quiz</button>
          </div>
          <div className="yelia-feedback-inline">
            <span>Fue claro?</span>
            <button className="yelia-icon-button" onClick={() => onFeedback?.(m, 'up')} type="button">
              <i className="bi bi-hand-thumbs-up"></i>
            </button>
            <button className="yelia-icon-button" onClick={() => onFeedback?.(m, 'down')} type="button">
              <i className="bi bi-hand-thumbs-down"></i>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileModal({ open, onClose, onSave, onGuest }) {
  const [profile, setProfile] = useState(getProfile());
  useEffect(() => {
    if (open) setProfile(getProfile());
  }, [open]);
  if (!open) return null;
  return (
    <div className="modal fade show yelia-profile-modal-wrap" style={{ display: 'block', background: 'rgba(0,0,0,.55)' }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content yelia-modal">
          <div className="modal-header">
            <div>
              <h5 className="modal-title">Perfil academico</h5>
              <p className="yelia-modal-subtitle">Estos datos ayudan a YELIA a adaptar explicaciones, recomendaciones y retroalimentacion.</p>
            </div>
            <button type="button" className="btn-close" onClick={onClose} aria-label="Cerrar"></button>
          </div>
          <div className="modal-body">
            <div className="yelia-profile-intro">
              <i className="bi bi-shield-check"></i>
              <span>Es opcional y se guarda en este navegador. Sirve para personalizar el aprendizaje, no para bloquear el chat.</span>
            </div>

            <label className="form-label">Codigo / alias</label>
            <input className="form-control mb-3" placeholder="Ej.: 2020123456 o tu alias" value={profile.alias || ''} onChange={(e) => setProfile({ ...profile, alias: e.target.value })} />

            <div className="yelia-guided-field">
              <label className="form-label">Ciclo / semestre</label>
              <small>Selecciona tu avance academico para ajustar profundidad y vocabulario.</small>
              <ProfileOptionGroup group="ciclo" value={profile.ciclo || ''} onChange={(ciclo) => setProfile({ ...profile, ciclo })} />
            </div>

            <div className="yelia-guided-field">
              <label className="form-label">Estado respecto a la materia</label>
              <small>Indica como estas usando YELIA en este momento.</small>
              <ProfileOptionGroup group="estado" value={profile.estado || ''} onChange={(estado) => setProfile({ ...profile, estado })} />
            </div>

            <div className="yelia-guided-field">
              <label className="form-label">Nivel de dominio</label>
              <small>Elige el nivel que mejor describe tu comprension actual.</small>
              <ProfileOptionGroup group="nivel" value={profile.nivel || ''} onChange={(nivel) => setProfile({ ...profile, nivel })} />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-outline-secondary me-auto" onClick={onGuest} type="button">Usar como invitado</button>
            <button className="btn btn-outline-secondary" onClick={onClose} type="button">Cancelar</button>
            <button className="btn btn-primary" onClick={() => { saveProfile(profile); onSave(profile); onClose(); }} type="button">Guardar</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ConversationActionModal({ state, onClose, onConfirm, onTitleChange }) {
  if (!state?.type) return null;
  const isRename = state.type === 'rename';
  const isDeleteAll = state.type === 'deleteAll';
  const title = isRename ? 'Renombrar chat' : isDeleteAll ? 'Borrar todo el historial' : 'Eliminar chat';
  const text = isRename
    ? 'Escribe un nombre claro para ubicar esta conversacion despues.'
    : isDeleteAll
      ? 'Esta accion elimina todas tus conversaciones guardadas en este navegador/usuario.'
      : `Se eliminara "${titleOfConversation(state.item)}" junto con sus mensajes.`;
  return (
    <div className="modal fade show yelia-profile-modal-wrap" style={{ display: 'block', background: 'rgba(0,0,0,.55)' }}>
      <div className="modal-dialog modal-dialog-centered yelia-action-dialog">
        <div className="modal-content yelia-modal yelia-action-modal">
          <div className="modal-header">
            <div>
              <h5 className="modal-title">{title}</h5>
              <p className="yelia-modal-subtitle">{text}</p>
            </div>
            <button type="button" className="btn-close" onClick={onClose} aria-label="Cerrar"></button>
          </div>
          <div className="modal-body">
            {isRename ? (
              <>
                <label className="form-label">Nombre del chat</label>
                <input className="form-control" value={state.title || ''} onChange={(event) => onTitleChange(event.target.value)} autoFocus />
              </>
            ) : (
              <div className="yelia-danger-box">
                <i className="bi bi-exclamation-triangle"></i>
                <span>{isDeleteAll ? 'No se puede deshacer desde la interfaz.' : 'Podras crear un nuevo chat cuando quieras.'}</span>
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button className="btn btn-outline-secondary" onClick={onClose} type="button">Cancelar</button>
            <button className={`btn ${isRename ? 'btn-primary' : 'btn-danger'}`} onClick={onConfirm} type="button">
              {isRename ? 'Guardar nombre' : 'Eliminar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function DrawerSection({ title, icon, children }) {
  return (
    <section className="yelia-drawer-card">
      <h3><i className={`bi ${icon}`}></i>{title}</h3>
      {children}
    </section>
  );
}

function RecommendationItem({ item, index, onSelect }) {
  const normalized = normalizeRecommendation(item);
  const title = normalized.title;
  const detail = normalized.description;
  const unit = syllabusUnit(normalized);
  const icon = index % 3 === 0 ? 'bi-journal-code' : index % 3 === 1 ? 'bi-ui-checks' : 'bi-collection';
  if (normalized.url) {
    return (
      <div className="yelia-resource-row yelia-resource-card">
        <span className="yelia-resource-icon"><i className={`bi ${icon}`}></i></span>
        <span>
          <strong>{title}</strong>
          <small>{detail}</small>
          {unit && <em>{unit}</em>}
          <span className="yelia-resource-actions">
            <a href={normalized.url} target="_blank" rel="noreferrer">
              Abrir recurso <i className="bi bi-box-arrow-up-right"></i>
            </a>
            <button onClick={() => onSelect(normalized.prompt || title || detail)} type="button">Usar en chat</button>
          </span>
        </span>
      </div>
    );
  }
  return (
    <button className="yelia-resource-row" onClick={() => onSelect(normalized.prompt || title || detail)} type="button">
      <span className="yelia-resource-icon"><i className={`bi ${icon}`}></i></span>
      <span>
        <strong>{title}</strong>
        <small>{detail}</small>
        {unit && <em>{unit}</em>}
      </span>
    </button>
  );
}

export default function ChatApp() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: 'Hola. Soy YELIA, tu asistente para Programacion Avanzada. En que puedo ayudarte hoy?',
      time: '',
      welcome: true,
    },
  ]);
  const [input, setInput] = useState('');
  const [topic, setTopic] = useState('Programacion Avanzada');
  const [history, setHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [resourceCards, setResourceCards] = useState([]);
  const [feedbackCard, setFeedbackCard] = useState(null);
  const [adaptivePlan, setAdaptivePlan] = useState(null);
  const [teacherActions, setTeacherActions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [profile, setProfileState] = useState({});
  const [showProfile, setShowProfile] = useState(false);
  const [user, setUser] = useState('Invitado');
  const [conversationId, setConversationId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [drawerView, setDrawerView] = useState('chats');
  const [query, setQuery] = useState('');
  const [historyDate, setHistoryDate] = useState('all');
  const [historyTopic, setHistoryTopic] = useState('all');
  const [chatQuery, setChatQuery] = useState('');
  const [chatSearchIndex, setChatSearchIndex] = useState(0);
  const [theme, setTheme] = useState('dark');
  const [density, setDensity] = useState('comfortable');
  const [fontSize, setFontSize] = useState('normal');
  const [avatarVisible, setAvatarVisible] = useState(true);
  const [guestMode, setGuestMode] = useState(false);
  const [prefsReady, setPrefsReady] = useState(false);
  const [actionModal, setActionModal] = useState(null);
  const [backendAvatar, setBackendAvatar] = useState(null);
  const [routeContext, setRouteContext] = useState(null);
  const [routeNoticeOpen, setRouteNoticeOpen] = useState(false);
  const [showScrollDown, setShowScrollDown] = useState(false);

  const chatRef = useRef(null);
  const fileRef = useRef(null);
  const inputRef = useRef(null);
  const { listening, speaking, voiceEnabled, setVoiceEnabled, speak, stop, listen } = useSpeech();

  const displayUser = profile?.alias?.trim() || (guestMode ? 'Invitado 1' : (user || 'Invitado 1'));
  const avatarState = !voiceEnabled ? 'muted' : listening ? 'listening' : speaking ? 'speaking' : loading ? 'thinking' : 'idle';
  const backendAvatarVisual = normalizeBackendAvatarState(backendAvatar);
  const effectiveAvatarState = backendAvatarVisual && voiceEnabled
    ? { ...backendAvatarVisual, state: avatarState, speaking: avatarState === 'speaking' }
    : avatarState;
  const filteredHistory = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const now = Date.now();
    return history.filter((item) => {
      const matchesText = !needle || `${titleOfConversation(item)} ${item.tema || ''}`.toLowerCase().includes(needle);
      const matchesTopic = historyTopic === 'all' || String(item.tema || '').toLowerCase() === historyTopic;
      const created = parseBackendDate(item.created_at).getTime();
      const ageDays = (now - created) / 86400000;
      const matchesDate = historyDate === 'all'
        || (historyDate === 'today' && ageDays < 1)
        || (historyDate === 'week' && ageDays <= 7)
        || (historyDate === 'month' && ageDays <= 30);
      return matchesText && matchesTopic && matchesDate;
    });
  }, [history, query, historyDate, historyTopic]);

  const historyTopics = useMemo(() => {
    const topics = new Set(history.map((item) => String(item.tema || '').trim()).filter(Boolean));
    return Array.from(topics).sort((a, b) => a.localeCompare(b));
  }, [history]);

  const chatMatches = useMemo(() => {
    const needle = chatQuery.trim().toLowerCase();
    if (!needle) return [];
    return messages
      .map((message, index) => ({ index, text: messageText(message) }))
      .filter((item) => item.text.toLowerCase().includes(needle));
  }, [messages, chatQuery]);

  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    const nextHeight = Math.min(el.scrollHeight, 260);
    el.style.height = `${Math.max(nextHeight, 28)}px`;
    el.style.overflowY = el.scrollHeight > 260 ? 'auto' : 'hidden';
  }, [input]);

  const currentChatMatch = chatMatches.length ? chatMatches[Math.min(chatSearchIndex, chatMatches.length - 1)] : null;

  useLayoutEffect(() => {
    setTheme(readStorage('yelia_theme', 'dark'));
    setDensity(readStorage('yelia_density', 'comfortable'));
    setFontSize(readStorage('yelia_font_size', 'normal'));
    setAvatarVisible(readStorage('yelia_avatar_visible', '1') !== '0');
    setGuestMode(readStorage('yelia_guest_mode', '0') === '1');
    setProfileState(getProfile());
    const nextRouteContext = readRouteContext();
    if (nextRouteContext) {
      setRouteContext(nextRouteContext);
      setRouteNoticeOpen(false);
      setTopic(nextRouteContext.topics?.[0] || nextRouteContext.title || 'Programacion Avanzada');
      writeStorage('yelia_route_unit', String(nextRouteContext.id || 1));
    }
    setMessages((items) => items.map((item) => (
      item.welcome && !item.time ? { ...item, time: messageTime(new Date()) } : item
    )));
    setPrefsReady(true);
  }, []);

  useLayoutEffect(() => {
    document.body.className = `yelia-body desktop-pro yelia-redesign ${theme === 'dark' ? 'dark-mode' : ''} yelia-density-${density} yelia-font-${fontSize}`;
    if (prefsReady) {
      writeStorage('yelia_theme', theme);
      writeStorage('yelia_density', density);
      writeStorage('yelia_font_size', fontSize);
    }
  }, [theme, density, fontSize, prefsReady]);

  useEffect(() => {
    if (!prefsReady) return;
    writeStorage('yelia_avatar_visible', avatarVisible ? '1' : '0');
  }, [avatarVisible, prefsReady]);

  useEffect(() => {
    if (!prefsReady) return;
    writeStorage('yelia_guest_mode', guestMode ? '1' : '0');
  }, [guestMode, prefsReady]);

  useEffect(() => {
    let alive = true;
    async function boot() {
      const localProfile = getProfile();
      const localGuest = readStorage('yelia_guest_mode', '0') === '1';
      try {
        const who = await api.get('/api/auth/whoami');
        if (!alive) return;
        const isGuest = localGuest || who?.mode === 'guest' || String(who?.usuario || '').startsWith('GUEST-') || String(who?.usuario || '').startsWith('Anon-');
        const visibleName = localProfile.alias || who?.nickname || (isGuest ? 'Invitado 1' : who?.usuario) || 'Invitado 1';
        setGuestMode(isGuest);
        setUser(visibleName);
      } catch {
        if (!alive) return;
        setGuestMode(localGuest);
        setUser(localGuest ? 'Invitado 1' : (localProfile.alias || 'Invitado 1'));
      }
      try {
        const progressData = await api.get('/api/progreso');
        if (alive && progressData?.progreso) {
          setProfileState((current) => profileFromProgress({ ...localProfile, ...current }, progressData.progreso));
          setTeacherActions(Array.isArray(progressData.teacher_actions) ? progressData.teacher_actions : []);
        }
      } catch {
        /* El diagnostico local sigue disponible aunque no cargue progreso. */
      }
      try {
        const data = await api.get('/api/history');
        if (alive) setHistory(data.conversations || data.items || data.history || []);
      } catch {
        /* Mantener el chat usable aunque falle el historial. */
      }
    }
    boot();
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    const chat = chatRef.current;
    if (!chat) return undefined;
    const updateScrollButton = () => {
      const distanceFromBottom = chat.scrollHeight - chat.scrollTop - chat.clientHeight;
      setShowScrollDown(distanceFromBottom > 140);
    };
    updateScrollButton();
    chat.addEventListener('scroll', updateScrollButton, { passive: true });
    return () => chat.removeEventListener('scroll', updateScrollButton);
  }, []);

  useEffect(() => {
    if (chatSearchIndex >= chatMatches.length) setChatSearchIndex(0);
  }, [chatMatches.length, chatSearchIndex]);

  useEffect(() => {
    if (!currentChatMatch || !chatRef.current) return;
    const target = chatRef.current.querySelector(`[data-message-index="${currentChatMatch.index}"]`);
    target?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [currentChatMatch]);

  async function refreshHistory() {
    try {
      const data = await api.get('/api/history');
      setHistory(data.conversations || data.items || data.history || []);
    } catch {
      /* Mantener el chat usable aunque falle el historial. */
    }
  }

  async function loadConversation(item) {
    const id = item?.id || item?.conversation_id;
    if (!id) return;
    try {
      const data = await api.get(`/api/conversation/${id}`);
      const loaded = data?.conversation?.messages || [];
      setConversationId(id);
      setMessages(loaded.map((msg) => ({
        role: msg.remitente === 'user' ? 'user' : 'bot',
        text: msg.remitente === 'bot' ? cleanAssistantReply(msg.contenido || '') : (msg.contenido || ''),
        html: msg.remitente === 'bot' ? cleanAssistantReply(msg.contenido || '') : '',
        time: messageTime(msg.created_at),
        provider: msg.proveedor || msg.provider || '',
        responseMs: msg.response_ms || msg.responseMs || 0,
      })));
      setRecommendations([]);
      setResourceCards([]);
      setFeedbackCard(null);
      setAdaptivePlan(null);
      setTopic(item.tema || item.topic || data?.conversation?.tema || lastTopicFromMessages(loaded, topic));
      setDrawerOpen(false);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  function newChat() {
    setConversationId(null);
    setRecommendations([]);
    setResourceCards([]);
    setFeedbackCard(null);
    setAdaptivePlan(null);
    setMessages([
      {
        role: 'bot',
        text: 'Nuevo chat iniciado. Que tema de Programacion Avanzada quieres revisar?',
        time: messageTime(new Date()),
      },
    ]);
  }

  async function renameConversation(item) {
    const id = item?.id || item?.conversation_id;
    if (!id) return;
    setActionModal({ type: 'rename', item, title: titleOfConversation(item) });
  }

  async function confirmRenameConversation() {
    const item = actionModal?.item;
    const id = item?.id || item?.conversation_id;
    const current = titleOfConversation(item);
    const title = String(actionModal?.title || '').trim();
    if (!id || !title || title === current) {
      setActionModal(null);
      return;
    }
    try {
      await api.post(`/api/conversation/${id}/rename`, { titulo: title });
      setHistory((items) => items.map((entry) => {
        const entryId = entry?.id || entry?.conversation_id;
        return entryId === id ? { ...entry, titulo: title, title } : entry;
      }));
      notify('Chat renombrado.', 'success');
      setActionModal(null);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  function deleteConversation(item) {
    const id = item?.id || item?.conversation_id;
    if (!id) return;
    setActionModal({ type: 'delete', item });
  }

  async function confirmDeleteConversation() {
    const item = actionModal?.item;
    const id = item?.id || item?.conversation_id;
    if (!id) return;
    try {
      await api.del(`/api/conversation/${id}`);
      setHistory((items) => items.filter((entry) => (entry?.id || entry?.conversation_id) !== id));
      if (conversationId === id) newChat();
      notify('Chat eliminado.', 'success');
      setActionModal(null);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  function askDeleteAllHistory() {
    setActionModal({ type: 'deleteAll' });
  }

  async function confirmDeleteAllHistory() {
    try {
      await api.del('/api/history');
      setHistory([]);
      newChat();
      notify('Historial eliminado.', 'success');
      setActionModal(null);
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  function confirmActionModal() {
    if (actionModal?.type === 'rename') return confirmRenameConversation();
    if (actionModal?.type === 'deleteAll') return confirmDeleteAllHistory();
    return confirmDeleteConversation();
  }

  async function handleProfileSave(nextProfile) {
    const previousAlias = profile?.alias?.trim() || '';
    setProfileState(nextProfile);
    const alias = nextProfile?.alias?.trim();
    setGuestMode(!alias);
    if (alias) setUser(alias);
    try {
      if (alias) {
        await api.post('/api/auth/login', { student_code: alias });
        writeStorage('yelia_active_student', alias);
        if (previousAlias && previousAlias !== alias) {
          setConversationId(null);
          setRecommendations([]);
          setResourceCards([]);
          setFeedbackCard(null);
          setAdaptivePlan(null);
          newChat();
        }
      }
      await api.post('/api/update-profile', {
        nickname: alias || '',
        ciclo_academico: nextProfile?.ciclo || '',
        estado_materia: nextProfile?.estado || '',
        nivel_materia: nextProfile?.nivel || '',
      });
      await refreshHistory();
    } catch {
      /* El perfil local sigue funcionando si el backend no puede guardarlo. */
    }
  }

  async function continueAsGuest() {
    setGuestMode(true);
    setUser('Invitado 1');
    removeStorage('yelia_active_student');
    saveProfile({});
    setProfileState({});
    setConversationId(null);
    setRecommendations([]);
    setResourceCards([]);
    setFeedbackCard(null);
    setAdaptivePlan(null);
    newChat();
    await api.post('/api/auth/login', { guest_id: newGuestId() }).catch(() => {});
    await refreshHistory();
    notify('Modo invitado activado.', 'success');
    setShowProfile(false);
  }

  async function exitChat() {
    stop();
    await api.post('/api/auth/logout', {}).catch(() => {});
    setGuestMode(true);
    setUser('Invitado 1');
    removeStorage('yelia_active_student');
    saveProfile({});
    setProfileState({});
    await api.post('/api/auth/login', { guest_id: newGuestId() }).catch(() => {});
    newChat();
    refreshHistory();
    notify('Sesion cerrada. Puedes seguir como invitado.', 'success');
  }

  async function send(text = input) {
    const question = String(text || '').trim();
    if (!question || loading) return;

    stop();
    setInput('');
    setBackendAvatar(null);
    const inferredTopic = topicFromText(question);
    const nextTopic = inferredTopic === 'Programacion Avanzada' && shouldKeepCurrentTopic(question)
      ? topic
      : inferredTopic;
    setTopic(nextTopic);
    setMessages((items) => [...items, { role: 'user', text: question, time: messageTime(new Date()) }]);

    setLoading(true);
    const startedAt = performance.now();
    try {
      const data = await api.post('/api/chat', {
        message: question,
        perfil: guestMode ? { ...profile, alias: '' } : profile,
        profile: guestMode ? { ...profile, alias: '' } : profile,
        topic: nextTopic,
        conversation_id: conversationId,
      });
      const resolvedTopic = data.tema || data.topic || nextTopic;
      const evidence = extractLearningEvidence({ ...data, tema: resolvedTopic, user_text: question });
      const hasControlledEvidence = Boolean(evidence.resources.length || evidence.feedback || evidence.adaptivePlan);
      const showActionChips = !data.structured_quiz || wantsVisibleResources(question) || wantsLearningFollowup(question);
      const answer = cleanControlledAssistantReply(
        data.response || data.reply || data.answer || data.message || 'Listo, revise tu consulta.',
        hasControlledEvidence,
      );
      setConversationId(data.conversation_id || conversationId);
      setTopic(resolvedTopic);
      setRecommendations(showActionChips ? (evidence.actions.length ? evidence.actions : mergeRecommendationPayload({ ...data, tema: resolvedTopic })) : []);
      setResourceCards(evidence.resources);
      setFeedbackCard(evidence.feedback);
      setAdaptivePlan(evidence.adaptivePlan);
      if (data.avatar) setBackendAvatar(data.avatar);
      setMessages((items) => [
        ...items,
        {
          role: 'bot',
          html: String(answer),
          text: plain(answer),
          time: messageTime(new Date()),
          provider: data.provider || data.proveedor || data.modo || '',
          responseMs: data.response_ms || Math.round(performance.now() - startedAt),
          structuredQuiz: data.structured_quiz || null,
          structuredGrade: data.structured_grade || null,
          learningEvidence: evidence,
        },
      ]);
      if (data.structured_grade) {
        const score = data.structured_grade.score || 0;
        const total = data.structured_grade.total || 0;
        if (total > 0 && (score / total) >= 0.7) {
          window.dispatchEvent(new Event('yelia_correct_answer'));
        }
      }
      speak(speechAutoText(answer, data));
      refreshHistory();
    } catch (error) {
      setBackendAvatar({ version: 'avatar.v1', state: 'error', emotion: 'error', expression: 'concerned', gesture: 'none', intensity: 0.5, speaking: false, mouth_shape: 'small' });
      notify(error.message, 'error');
      setMessages((items) => [
        ...items,
        {
          role: 'bot',
          text: 'No pude responder en este momento. Revisa la conexion o la API.',
          time: messageTime(new Date()),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function upload(file) {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    if (conversationId) form.append('conversation_id', String(conversationId));
    try {
      const data = await api.upload('/api/attachments/upload', form);
      setConversationId(data.conversation_id || conversationId);
      notify('Archivo adjuntado.', 'success');
      refreshHistory();
    } catch (error) {
      notify(error.message, 'error');
    }
  }

  async function feedback(message, value) {
    try {
      await api.post('/api/feedback', {
        rating: value,
        note: (message.text || plain(message.html) || '').trim(),
        conversation_id: conversationId
      });
      notify('Gracias por tu valoracion.', 'success');
    } catch (error) {
      notify(error.message || 'No se pudo guardar la valoracion.', 'error');
    }
  }

  async function copyMessage(message) {
    const text = messageText(message).trim();
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      notify('Respuesta copiada.', 'success');
    } catch {
      notify('No pude copiar automaticamente. Selecciona el texto manualmente.', 'error');
    }
  }

  function speakMessage(message) {
    const ok = speak(speechPlain(message.html || message.text || ''));
    if (!ok) notify('Tu navegador no permite leer esta respuesta en voz alta.', 'error');
  }

  function quickReply(prompt) {
    send(prompt);
  }

  function useQuizOption({ questionNumber, letter }) {
    const answer = `${questionNumber}${letter}`;
    setInput((value) => {
      const current = String(value || '').trim();
      const pattern = new RegExp(`(^|[,;\\s])${questionNumber}\\s*[:.)-]?\\s*[a-d](?=$|[,;\\s])`, 'i');
      if (!current) return answer;
      if (pattern.test(current)) {
        return current.replace(pattern, (match, prefix) => `${prefix || ''}${answer}`).trim();
      }
      return `${current}, ${answer}`;
    });
    setTimeout(() => inputRef.current?.focus(), 0);
  }

  function clearRouteContext() {
    removeStorage('yelia_route_prompt');
    removeStorage('yelia_route_unit');
    setRouteContext(null);
    setRouteNoticeOpen(false);
  }

  function sendRouteGuide() {
    const prompt = routeContext?.prompt || input;
    clearRouteContext();
    send(prompt);
  }

  function moveChatSearch(direction) {
    if (!chatMatches.length) return;
    setChatSearchIndex((value) => (value + direction + chatMatches.length) % chatMatches.length);
  }

  function testVoice() {
    setVoiceEnabled(true);
    const ok = speak('Hola, soy YELIA. La voz de respuestas esta activada.', { force: true });
    if (!ok) notify('Tu navegador no permite leer respuestas en voz alta.', 'error');
  }

  return (
    <>
      <header className="yelia-header yelia-redesign-header" style={{ minHeight: '44px', padding: '4px 16px' }}>
        <div className="header-left" style={{ padding: '2px 6px', borderRadius: '6px' }}><img src="/static/img/logo-fii.png" alt="Facultad de Ingenieria Industrial" style={{ height: '24px' }} /></div>
        <div className="header-center" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <h1 style={{ fontSize: '15px', margin: 0, letterSpacing: '0.08em' }}>YELIA4AP</h1>
          <span style={{ fontSize: '12px', color: '#e5e7eb', opacity: 0.85 }}>|</span>
          <p className="subtitle" style={{ fontSize: '12px', margin: 0, fontWeight: '500' }}>Asistente Educativo Interactivo para Programación Avanzada</p>
          <span style={{ fontSize: '12px', color: '#e5e7eb', opacity: 0.85 }}>|</span>
          <small style={{ fontSize: '11px', display: 'inline', marginTop: 0, opacity: 0.7 }}>Proyecto Académico de Titulación</small>
        </div>
        <div className="header-right" style={{ padding: '2px 6px', borderRadius: '6px' }}><img src="/static/img/logo-ug.png" alt="Universidad de Guayaquil" style={{ height: '24px' }} /></div>
      </header>

      <main className="yelia-main yelia-redesign-main">
        <div className={`yelia-redesign-layout ${drawerOpen ? 'is-drawer-open' : ''} ${avatarVisible ? 'is-avatar-open' : 'is-avatar-hidden'}`}>
          <nav className="yelia-rail" aria-label="Navegacion del chat">
            <button className="yelia-rail-toggle" onClick={() => setDrawerOpen((value) => !value)} type="button" aria-label="Abrir panel">
              <i className={`bi ${drawerOpen ? 'bi-layout-sidebar-inset' : 'bi-layout-sidebar'}`}></i>
            </button>
            {[
              ['chats', 'bi-chat-left-text', 'Chats'],
              ['avisos', 'bi-megaphone', 'Avisos del docente'],
              ['recomendaciones', 'bi-stars', 'Recomendaciones'],
              ['perfil', 'bi-person-gear', 'Perfil'],
              ['apariencia', 'bi-sliders', 'Apariencia'],
            ].map(([view, icon, label]) => (
              <button
                key={view}
                className={drawerView === view ? 'active' : ''}
                onClick={() => { setDrawerView(view); setDrawerOpen(true); }}
              type="button"
              title={label}
              aria-label={label}
            >
              <i className={`bi ${icon}`}></i>
              {view === 'avisos' && teacherActions.length ? <span className="yelia-rail-badge">{teacherActions.length}</span> : null}
            </button>
          ))}
            <button
              className={avatarVisible ? 'active' : ''}
              onClick={() => setAvatarVisible((value) => !value)}
              type="button"
              title={avatarVisible ? 'Ocultar avatar' : 'Mostrar avatar'}
              aria-label={avatarVisible ? 'Ocultar avatar' : 'Mostrar avatar'}
            >
              <i className={`bi ${avatarVisible ? 'bi-person-video3' : 'bi-person-video'}`}></i>
            </button>
            <button onClick={exitChat} type="button" title="Cerrar sesion" aria-label="Cerrar sesion">
              <i className="bi bi-box-arrow-right"></i>
            </button>
          </nav>

          <aside className="yelia-control-drawer" aria-label="Panel lateral">
            <div className="yelia-drawer-head">
              <div>
                <span>Panel</span>
                <strong>{drawerView === 'chats' ? 'Chats' : drawerView === 'avisos' ? 'Avisos docente' : drawerView === 'recomendaciones' ? 'Recomendaciones' : drawerView === 'perfil' ? 'Perfil' : 'Apariencia'}</strong>
              </div>
              <button className="yelia-icon-button" onClick={() => setDrawerOpen(false)} type="button" aria-label="Cerrar panel">
                <i className="bi bi-chevron-left"></i>
              </button>
            </div>

            {drawerView === 'chats' && (
              <>
                <button className="yelia-drawer-primary" onClick={newChat} type="button"><i className="bi bi-plus-lg"></i>Nuevo chat</button>
                <div className="yelia-search-box">
                  <i className="bi bi-search"></i>
                  <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar chat..." />
                </div>
                <div className="yelia-history-filters">
                  <select value={historyDate} onChange={(e) => setHistoryDate(e.target.value)} aria-label="Filtrar por fecha">
                    <option value="all">Todas las fechas</option>
                    <option value="today">Hoy</option>
                    <option value="week">Ultimos 7 dias</option>
                    <option value="month">Ultimos 30 dias</option>
                  </select>
                  <select value={historyTopic} onChange={(e) => setHistoryTopic(e.target.value)} aria-label="Filtrar por tema">
                    <option value="all">Todos los temas</option>
                    {historyTopics.map((item) => <option key={item} value={item.toLowerCase()}>{item}</option>)}
                  </select>
                </div>
                <button className="yelia-history-danger" onClick={askDeleteAllHistory} type="button">
                  <i className="bi bi-trash3"></i>Borrar todo el historial
                </button>
                <div className="yelia-conversation-list yelia-drawer-list">
                  {filteredHistory.length ? filteredHistory.map((item, index) => (
                    <div key={item.id || index} className={`yelia-conversation-item ${conversationId === (item.id || item.conversation_id) ? 'active' : ''}`}>
                      <button className="yelia-conversation-open" onClick={() => loadConversation(item)} type="button">
                        <strong>{titleOfConversation(item)}</strong>
                        {item.tema && <em>{item.tema}</em>}
                        <small>{formatDateTime(item.created_at)}</small>
                      </button>
                      <div className="yelia-conversation-actions">
                        <button onClick={() => renameConversation(item)} type="button" title="Renombrar chat" aria-label="Renombrar chat">
                          <i className="bi bi-pencil"></i>
                        </button>
                        <button onClick={() => deleteConversation(item)} type="button" title="Eliminar chat" aria-label="Eliminar chat">
                          <i className="bi bi-trash"></i>
                        </button>
                      </div>
                    </div>
                  )) : <p className="yelia-empty-text">No hay conversaciones</p>}
                </div>
              </>
            )}

            {drawerView === 'avisos' && (
              <div className="yelia-drawer-scroll yelia-recommendations-board">
                <DrawerSection title="Avisos del docente" icon="bi-megaphone">
                  <p className="yelia-drawer-help">Indicaciones que tu docente envio a tu perfil para continuar, reforzar o practicar.</p>
                  {teacherActions.length ? (
                    <div className="yelia-teacher-action-list">
                      {teacherActions.slice().reverse().map((action, index) => (
                        <article className="yelia-teacher-action-card" key={`${action.created_at || index}-${action.action_label || index}`}>
                          <span>{action.topic || 'Seguimiento personalizado'}</span>
                          <strong>{action.action_label || 'Accion recomendada'}</strong>
                          <p>{action.detail || 'Tu docente dejo una indicacion para continuar tu aprendizaje.'}</p>
                          <small>{action.created_at ? formatDateTime(action.created_at) : 'Pendiente'}</small>
                          <button type="button" onClick={() => send(action.detail || action.action_label || 'Quiero trabajar la recomendacion del docente')}>
                            Trabajar con YELIA
                          </button>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="yelia-empty-evidence">
                      <i className="bi bi-check2-circle"></i>
                      <span>No tienes avisos pendientes del docente.</span>
                    </div>
                  )}
                </DrawerSection>
              </div>
            )}

            {drawerView === 'recomendaciones' && (
              <div className="yelia-drawer-scroll yelia-recommendations-board">
                <DrawerSection title="Recomendacion de recursos" icon="bi-book">
                  <p className="yelia-drawer-help">Materiales sugeridos segun el tema actual y tu nivel academico.</p>
                  <div className="yelia-resource-list">
                    {resourceCards.length ? resourceCards.map((item, index) => (
                      <RecommendationItem key={index} item={item} index={index} onSelect={send} />
                    )) : (
                      <>
                        <div className="yelia-empty-evidence">
                          <i className="bi bi-info-circle"></i>
                          <span>Pregunta por recursos o materiales y aqui apareceran las recomendaciones controladas por YELIA.</span>
                        </div>
                      </>
                    )}
                  </div>
                </DrawerSection>

                <DrawerSection title="Personalizacion adaptativa" icon="bi-diagram-3">
                  <div className="yelia-adaptive-card">
                    <span className="yelia-status-pill">Ruta sugerida</span>
                    <div><b>Nivel actual</b><strong>{adaptivePlan?.current_level ? humanLevel(adaptivePlan.current_level) : humanLevel(profile.nivel) || 'No configurado'}</strong></div>
                    <div><b>Nivel recomendado</b><strong>{adaptivePlan?.selected_level ? humanLevel(adaptivePlan.selected_level) : 'Sin ajuste aun'}</strong></div>
                    <div><b>Que hara YELIA</b><strong>{adaptivePlan?.strategy ? humanStrategy(adaptivePlan.strategy) : 'Esperando senales'}</strong></div>
                    <div><b>Siguiente paso</b><strong>{adaptivePlan?.next_best_action ? humanAction(adaptivePlan.next_best_action) : 'Recomendar recurso'}</strong></div>
                    {adaptivePlan?.rationale && <p className="yelia-evidence-note">{adaptivePlan.rationale}</p>}
                  </div>
                  <button className="yelia-mini-action" onClick={() => { window.location.href = guestMode ? '/diagnostico?guest=1' : '/diagnostico'; }} type="button">
                    Repetir diagnostico <i className="bi bi-clipboard2-check"></i>
                  </button>
                </DrawerSection>

                <DrawerSection title="Retroalimentacion personalizada" icon="bi-star">
                  <div className="yelia-feedback-card">
                    <strong>{feedbackCard?.summary || feedbackCard?.message || 'Sin retroalimentacion activa'}</strong>
                    <span>{feedbackCard?.reason || feedbackCard?.recommendation || feedbackCard?.action || 'Cuando YELIA detecte confusion, avance o practica, aqui aparecera la recomendacion personalizada.'}</span>
                  </div>
                  <div className="yelia-feedback-actions">
                    <button type="button" onClick={() => send(feedbackCard?.action || 'Explicame mejor este tema')}>Aplicar feedback</button>
                    <button type="button" onClick={() => send('Dame un ejemplo practico')}>Dar ejemplo</button>
                    <button type="button" onClick={() => send('Hazme un quiz corto')}>Quiz</button>
                  </div>
                </DrawerSection>

                <DrawerSection title="Acciones sugeridas" icon="bi-lightning-charge">
                  <div className="yelia-resource-list">
                    {recommendations.length ? recommendations.map((item, index) => (
                      <RecommendationItem key={index} item={item} index={index} onSelect={send} />
                    )) : (
                      <div className="yelia-empty-evidence">
                        <i className="bi bi-stars"></i>
                        <span>Las acciones apareceran despues de una respuesta con evidencia adaptativa.</span>
                      </div>
                    )}
                  </div>
                </DrawerSection>
              </div>
            )}

            {drawerView === 'perfil' && (
              <div className="yelia-drawer-scroll">
                <DrawerSection title="Perfil academico" icon="bi-person-vcard">
                  <p className="yelia-drawer-help">Estos datos vienen del registro y de la evaluacion inicial. YELIA los usa para adaptar profundidad, ritmo y recomendaciones.</p>
                  <dl className="yelia-profile-summary">
                    <div><dt>Ciclo</dt><dd>{profile.ciclo || 'No configurado'}</dd></div>
                    <div><dt>Estado</dt><dd>{profile.estado || 'No configurado'}</dd></div>
                    <div><dt>Nivel detectado</dt><dd>{profile.nivel || 'No configurado'}</dd></div>
                  </dl>
                  <div className="yelia-profile-tips">
                    <span><i className="bi bi-person-vcard"></i> Registro: alias, ciclo y estado de la materia.</span>
                    <span><i className="bi bi-ui-checks"></i> Nivel: se usa para adaptar explicaciones y ejercicios.</span>
                    <span><i className="bi bi-stars"></i> Adaptacion: ejemplos y ejercicios segun nivel.</span>
                  </div>
                  {profile.ciclo && profile.estado && profile.nivel ? (
                    <div className="yelia-empty-evidence">
                      <i className="bi bi-check2-circle"></i>
                      <span>Perfil listo. No hace falta repetir la prueba para continuar usando el chat.</span>
                    </div>
                  ) : (
                    <button className="yelia-drawer-primary yelia-drawer-primary-flat" onClick={() => { window.location.href = guestMode ? '/diagnostico?guest=1' : '/diagnostico'; }} type="button">
                      <i className="bi bi-clipboard2-check"></i>Completar perfil
                    </button>
                  )}
                </DrawerSection>
              </div>
            )}

            {drawerView === 'apariencia' && (
              <div className="yelia-drawer-scroll yelia-appearance-panel">
                <DrawerSection title="Tema visual" icon="bi-palette">
                  <div className="yelia-segmented">
                    <button className={theme === 'light' ? 'active' : ''} onClick={() => setTheme('light')} type="button">Claro</button>
                    <button className={theme === 'dark' ? 'active' : ''} onClick={() => setTheme('dark')} type="button">Oscuro</button>
                  </div>
                  <label className="yelia-setting-row">
                    <span><b>Voz de respuestas</b><small>YELIA lee sus respuestas al contestar.</small></span>
                    <input type="checkbox" checked={voiceEnabled} onChange={(event) => setVoiceEnabled(event.target.checked)} />
                  </label>
                  <button className="yelia-mini-action" onClick={testVoice} type="button">
                    Probar voz <i className="bi bi-volume-up"></i>
                  </button>
                  <div className="yelia-font-control">
                    <span><b>Tamano de letra</b><small>Ajusta lectura de respuestas y paneles.</small></span>
                    <div className="yelia-segmented yelia-segmented-3">
                      <button className={fontSize === 'small' ? 'active' : ''} onClick={() => setFontSize('small')} type="button">A</button>
                      <button className={fontSize === 'medium' ? 'active' : ''} onClick={() => setFontSize('medium')} type="button">A</button>
                      <button className={fontSize === 'large' ? 'active' : ''} onClick={() => setFontSize('large')} type="button">A</button>
                    </div>
                  </div>
                  <label className="yelia-setting-row">
                    <span><b>Vista compacta</b><small>Reduce espacios del chat.</small></span>
                    <input type="checkbox" checked={density === 'compact'} onChange={(e) => setDensity(e.target.checked ? 'compact' : 'comfortable')} />
                  </label>
                  <div className="yelia-settings-note">
                    <i className="bi bi-check2-circle"></i>
                    <span>Preferencias guardadas en este navegador.</span>
                  </div>
                </DrawerSection>
              </div>
            )}
          </aside>

          <section className="yelia-panel yelia-chat-panel yelia-redesign-chat">
            <div className="yelia-chat-header">
              <div className="yelia-chat-header-grid d-flex align-items-center justify-content-between">
                <div className="yelia-title-block">
                  <div className="yelia-title-row">
                    <h1 className="yelia-title mb-0">YELIA4AP</h1>
                    <button className="yelia-dark-toggle yelia-title-control" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} type="button" title="Cambiar tema" aria-label="Cambiar tema claro u oscuro">
                      <i className={`bi ${theme === 'dark' ? 'bi-sun-fill' : 'bi-moon-fill'}`}></i>
                    </button>
                  </div>
                </div>
                <div className="yelia-chat-header-actions d-flex align-items-center gap-2">
                  <span className="yelia-user-badge yelia-title-user">Usuario: {displayUser}</span>
                  
                  <div className="yelia-topic-bar-compact" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.06)', padding: '4px 10px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.08)', fontSize: '0.8rem' }}>
                    <span className="yelia-topic-label" style={{ color: '#aaa', fontWeight: '500' }}>Tema:</span>
                    <span className="yelia-topic-value" style={{ color: '#fff', fontWeight: '600' }}>{topic}</span>
                  </div>

                  <div className="yelia-chat-search-box" style={{ maxWidth: '140px' }}>
                    <i className="bi bi-search"></i>
                    <input value={chatQuery} onChange={(e) => { setChatQuery(e.target.value); setChatSearchIndex(0); }} placeholder="Buscar" style={{ width: '100%' }} />
                    {chatQuery && (
                      <span>{chatMatches.length ? `${Math.min(chatSearchIndex + 1, chatMatches.length)}/${chatMatches.length}` : '0/0'}</span>
                    )}
                  </div>
                  {chatQuery && (
                    <div className="yelia-chat-search-nav">
                      <button onClick={() => moveChatSearch(-1)} disabled={!chatMatches.length} type="button" aria-label="Anterior">
                        <i className="bi bi-chevron-up"></i>
                      </button>
                      <button onClick={() => moveChatSearch(1)} disabled={!chatMatches.length} type="button" aria-label="Siguiente">
                        <i className="bi bi-chevron-down"></i>
                      </button>
                      <button onClick={() => setChatQuery('')} type="button" aria-label="Limpiar busqueda">
                        <i className="bi bi-x-lg"></i>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {routeContext && routeNoticeOpen && (
              <div className="yelia-route-context-card yelia-route-floating-card">
                <div>
                  <span>Unidad activa</span>
                  <strong>Unidad {routeContext.id}: {routeContext.title}</strong>
                  <small>{(routeContext.topics || []).slice(0, 4).join(' - ')}</small>
                </div>
                <div className="yelia-route-context-actions">
                  <button type="button" onClick={() => setInput(routeContext.prompt || '')}>
                    Usar
                  </button>
                  <button className="yelia-route-primary-action" type="button" onClick={sendRouteGuide} disabled={loading}>
                    Enviar
                  </button>
                  <a href="/ruta">Ver ruta</a>
                  <button type="button" onClick={() => setRouteNoticeOpen(false)} aria-label="Minimizar sugerencia de unidad">
                    <i className="bi bi-x-lg"></i>
                  </button>
                </div>
              </div>
            )}

            {!routeContext && routeNoticeOpen && (
              <div className="yelia-route-context-card yelia-route-floating-card yelia-route-empty-card">
                <div>
                  <span>Notificaciones</span>
                  <strong>Sin notificaciones pendientes</strong>
                  <small>Aqui apareceran recursos sugeridos, feedback o una unidad activa cuando YELIA detecte que debes revisar algo.</small>
                </div>
                <div className="yelia-route-context-actions">
                  <a href="/ruta">Ver ruta</a>
                  <button type="button" onClick={() => setRouteNoticeOpen(false)} aria-label="Cerrar notificaciones">
                    <i className="bi bi-x-lg"></i>
                  </button>
                </div>
              </div>
            )}

            <div ref={chatRef} className="yelia-chat-container">
              {currentChatMatch && (
                <div className="yelia-chat-search-preview">
                  <small>{messages[currentChatMatch.index]?.role === 'user' ? 'Tu' : 'YELIA'}</small>
                  <strong>{messageText(messages[currentChatMatch.index]).slice(0, 120)}{messageText(messages[currentChatMatch.index]).length > 120 ? '...' : ''}</strong>
                  <span>{chatSearchIndex + 1} de {chatMatches.length}</span>
                </div>
              )}
              {messages.map((message, index) => (
                <Message
                  key={index}
                  index={index}
                  m={message}
                  isSearchMatch={chatMatches.some((item) => item.index === index)}
                  isCurrentMatch={currentChatMatch?.index === index}
                  onFeedback={feedback}
                  onCopy={copyMessage}
                  onSpeak={speakMessage}
                  onQuick={quickReply}
                  onQuizOption={useQuizOption}
                />
              ))}
              {chatQuery && chatMatches.length > 0 && (
                <div className="yelia-search-markers" aria-label="Coincidencias en el chat">
                  {chatMatches.map((item, markerIndex) => (
                    <button
                      key={`${item.index}-${markerIndex}`}
                      className={currentChatMatch?.index === item.index ? 'active' : ''}
                      style={{ top: `${messages.length <= 1 ? 8 : 8 + (item.index / (messages.length - 1)) * 84}%` }}
                      onClick={() => setChatSearchIndex(markerIndex)}
                      title={messageText(messages[item.index]).slice(0, 90)}
                      type="button"
                    />
                  ))}
                </div>
              )}
              {loading && (
                <div className="yelia-typing-indicator">
                  <span className="yelia-typing-dot"></span>
                  <span className="yelia-typing-dot"></span>
                  <span className="yelia-typing-dot"></span>
                  <span className="yelia-typing-text">YELIA4AP esta escribiendo...</span>
                </div>
              )}
            </div>

            {showScrollDown && (
              <button
                className="yelia-scroll-bottom-button"
                type="button"
                onClick={() => chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })}
                aria-label="Bajar al final del chat"
                title="Bajar al final"
              >
                <i className="bi bi-arrow-down"></i>
              </button>
            )}

            <input ref={fileRef} type="file" className="d-none" onChange={(e) => upload(e.target.files?.[0])} />
            <div className="yelia-input-bar">
              <div className="yelia-composer-side yelia-composer-left" aria-label="Acciones de conversacion">
                <button className="yelia-icon-button" onClick={newChat} type="button" title="Nuevo chat" aria-label="Nuevo chat">
                  <i className="bi bi-plus-circle"></i>
                </button>
                <button className="yelia-icon-button" onClick={() => fileRef.current?.click()} type="button" title="Adjuntar archivo" aria-label="Adjuntar archivo">
                  <i className="bi bi-paperclip"></i>
                </button>
              </div>
              <div className="yelia-input-wrapper">
                <textarea
                  ref={inputRef}
                  id="user-input"
                  rows="1"
                  value={input}
                  disabled={loading}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      send();
                    }
                  }}
                  placeholder="Escribe tu consulta..."
                />
              </div>
              <div className="yelia-composer-side yelia-composer-right" aria-label="Voz y envio">
                <button className="yelia-icon-button" onClick={() => listen((text) => setInput((value) => (value ? `${value} ` : '') + text))} type="button" title="Dictar por voz" aria-label="Dictar por voz">
                  <i className={`bi ${listening ? 'bi-mic-mute-fill' : 'bi-mic-fill'}`}></i>
                </button>
                <button className="yelia-send-button-modern" onClick={() => send()} type="button" aria-label="Enviar" disabled={loading || !input.trim()}>
                  <i className="bi bi-send-fill"></i>
                </button>
              </div>
            </div>
          </section>

          {avatarVisible && (
            <AvatarPanel 
              state={effectiveAvatarState} 
              voiceEnabled={voiceEnabled} 
              setVoiceEnabled={setVoiceEnabled} 
            />
          )}
        </div>
      </main>

      <footer className="yelia-footer">Derechos Reservados &copy; 2026 Universidad de Guayaquil, Facultad de Ingenieria Industrial, Carrera Telematica</footer>
      <ConversationActionModal
        state={actionModal}
        onClose={() => setActionModal(null)}
        onConfirm={confirmActionModal}
        onTitleChange={(title) => setActionModal((state) => ({ ...state, title }))}
      />
    </>
  );
}
