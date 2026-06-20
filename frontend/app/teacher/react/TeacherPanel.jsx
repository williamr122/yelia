'use client';

import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../../_shared/react/api.js';
import { notify } from '../../chat/react/core/notify.js';
import { asArray, fmtDate } from '../../_shared/react/format.js';

function KpiCard({ label, value, icon }) {
  return (
    <div className="teacher-kpi">
      <span>{label}</span>
      <b>{value ?? 0}</b>
      <i className={`bi ${icon}`}></i>
    </div>
  );
}

function MiniCard({ label, value, hint, icon }) {
  return (
    <div className="teacher-mini-card">
      <i className={`bi ${icon}`}></i>
      <span>{label}</span>
      <b>{value ?? '-'}</b>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

function RouteUnitDots({ units = [] }) {
  return (
    <div className="teacher-route-dots" aria-label="Avance por unidades">
      {[1, 2, 3, 4].map((unitId) => {
        const unit = units.find((item) => Number(item.id) === unitId) || {};
        return <span key={unitId} className={`is-${unit.status || 'locked'}`}>U{unitId}</span>;
      })}
    </div>
  );
}

function LearningRouteCard({ route, active = false, onClick, compact = false }) {
  const progress = Math.max(0, Math.min(100, Number(route?.progress || 0)));
  return (
    <article className={`teacher-route-card ${active ? 'is-active' : ''} ${compact ? 'is-compact' : ''}`}>
      <div className="teacher-route-card-head">
        <div>
          <strong>{route.display_name || route.usuario}</strong>
          <small>Unidad actual {route.current_unit || 1} - {route.done_units || 0}/4 completadas</small>
        </div>
        <b>{progress}%</b>
      </div>
      <RouteUnitDots units={route.units || []} />
      <div className="teacher-route-progress"><i style={{ width: `${progress}%` }} /></div>
      <p>{route.route_completed ? 'Ruta completada con evaluacion final.' : 'Ruta en progreso por unidades.'}</p>
      <small>{route.final_percent != null ? `Evaluacion final: ${route.final_percent}%` : 'Evaluacion final pendiente'}</small>
      {onClick ? <button type="button" onClick={onClick}>Ver detalle</button> : null}
    </article>
  );
}

function Table({ cols, rows, render }) {
  return (
    <div className="teacher-table-wrap">
      <table className="teacher-table">
        <thead><tr>{cols.map((col) => <th key={col}>{col}</th>)}</tr></thead>
        <tbody>
          {rows.length ? rows.map(render) : (
            <tr><td colSpan={cols.length} className="teacher-empty">Sin datos todavia</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

const emptyTeacherStudentForm = {
  alias: '',
  email: '',
  status: 'active',
  level_current: '',
  course: '',
  tags: '',
  notes: '',
};

export default function TeacherPanel() {
  const [me, setMe] = useState({});
  const [dash, setDash] = useState({});
  const [students, setStudents] = useState([]);
  const [chats, setChats] = useState([]);
  const [learningRoutes, setLearningRoutes] = useState([]);
  const [learningSummary, setLearningSummary] = useState({});
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [dbHealth, setDbHealth] = useState({});
  const [statusSummary, setStatusSummary] = useState({});
  const [view, setView] = useState('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [q, setQ] = useState('');
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(false);
  const [activeInsight, setActiveInsight] = useState('resources');
  const [activeTeacherAction, setActiveTeacherAction] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [showStudentForm, setShowStudentForm] = useState(false);
  const [newStudentForm, setNewStudentForm] = useState(emptyTeacherStudentForm);
  const [selectedChatStudent, setSelectedChatStudent] = useState('');
  const [selectedLearningUser, setSelectedLearningUser] = useState('');
  const [allowPdf, setAllowPdf] = useState(true);

  const kpis = dash.kpis || dash;
  const topTopics = useMemo(() => dash.top_topics || dash.top_temas || [], [dash]);
  const statusCounts = statusSummary.summary || {};
  const dbEngine = dbHealth.db_engine || dbHealth.engine || '';
  const dbConnectionLabel = dbEngine === 'postgresql' ? 'Conexion PostgreSQL' : dbEngine === 'sqlite' ? 'Conexion SQLite local' : 'Conexion por verificar';
  const activeStudents = useMemo(() => students.slice(0, 6), [students]);
  const recentChats = useMemo(() => chats.slice(0, 6), [chats]);
  const visibleLearningRoutes = useMemo(() => learningRoutes.slice(0, 40), [learningRoutes]);
  const selectedLearningRoute = useMemo(
    () => visibleLearningRoutes.find((route) => route.usuario === selectedLearningUser) || visibleLearningRoutes[0] || null,
    [visibleLearningRoutes, selectedLearningUser],
  );
  const chatGroups = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const groups = new Map();
    chats.forEach((chat) => {
      const student = studentLabel(chat);
      const topic = chat.tema || chat.topic || inferTopic(`${chat.title || ''} ${chat.tema || ''}`);
      const haystack = `${student} ${chat.title || ''} ${topic}`.toLowerCase();
      if (needle && !haystack.includes(needle)) return;
      if (!groups.has(student)) groups.set(student, { student, chats: [], topics: new Set(), last: null });
      const group = groups.get(student);
      group.chats.push(chat);
      if (topic) group.topics.add(topic);
      const date = chat.updated_at || chat.created_at || '';
      if (!group.last || String(date) > String(group.last)) group.last = date;
    });
    return Array.from(groups.values())
      .map((group) => ({ ...group, topics: Array.from(group.topics) }))
      .sort((a, b) => String(b.last || '').localeCompare(String(a.last || '')));
  }, [chats, q]);
  const activeChatGroup = useMemo(
    () => chatGroups.find((group) => group.student === selectedChatStudent) || chatGroups[0] || null,
    [chatGroups, selectedChatStudent],
  );

  function studentLabel(row) {
    const raw = row?.alias || row?.student_alias || row?.usuario || row?.username || row?.email || `Estudiante ${row?.id || ''}`;
    if (String(raw).startsWith('GUEST-')) return `Invitado ${String(raw).slice(6).replace(/[-_]+/g, ' ')}`;
    if (String(raw).startsWith('Anon-')) return `Estudiante anonimo ${String(raw).slice(5, 11)}`;
    return raw;
  }

  function chatLabel(row) {
    return row?.title || row?.titulo || row?.topic || row?.tema || `Chat ${row?.id || ''}`;
  }

  function shortText(value, max = 150) {
    const clean = String(value || '').replace(/\s+/g, ' ').trim();
    return clean.length > max ? `${clean.slice(0, max - 1)}...` : clean;
  }

  function chatPreview(row) {
    return shortText(row?.summary || row?.resumen || row?.last_message || row?.ultimo_mensaje || row?.topic || row?.tema || 'Sin resumen disponible.', 120);
  }

  function shortStudentName(row) {
    return shortText(studentLabel(row), 28);
  }

  function inferTopic(text, fallback = 'Tema sin clasificar') {
    const clean = String(text || '').toLowerCase();
    if (/clases|objetos|objeto|class/.test(clean)) return 'Clases y objetos';
    if (/herencia|extends|super/.test(clean)) return 'Herencia';
    if (/polimorf/.test(clean)) return 'Polimorfismo';
    if (/array|arreglo|lista/.test(clean)) return 'Arreglos y listas';
    if (/java/.test(clean)) return 'Java';
    if (/python/.test(clean)) return 'Python';
    if (/base de datos|sql|sqlite/.test(clean)) return 'Base de datos';
    return shortText(fallback, 70);
  }

  function inferNeed(text) {
    const clean = String(text || '').toLowerCase();
    if (/recom|recurso|material|guia/.test(clean)) return 'Quiere recursos o recomendacion';
    if (/no entiendo|confund|explica|explicame|simple|ayuda|duda/.test(clean)) return 'No entiende y pide explicacion simple';
    if (/practica|ejercicio|quiz|pregunta/.test(clean)) return 'Busca practica';
    if (/tarea|examen|evaluacion|prueba/.test(clean)) return 'Prepara tarea o evaluacion';
    return 'Explora un tema';
  }

  function chatStudentProfile() {
    const chatUser = String(selectedChat?.usuario || selectedChat?.student_alias || selectedChat?.alias || '').toLowerCase();
    const row = students.find((student) => {
      const haystack = `${student.alias || ''} ${student.student_alias || ''} ${student.usuario || ''} ${student.username || ''} ${student.email || ''}`.toLowerCase();
      return chatUser && haystack.includes(chatUser);
    }) || {};
    return {
      ciclo: selectedChat?.ciclo || selectedChat?.ciclo_academico || row.ciclo || row.ciclo_academico || 'No configurado',
      estado: selectedChat?.estado || selectedChat?.estado_materia || row.estado || row.estado_materia || 'No configurado',
      nivel: selectedChat?.nivel || selectedChat?.nivel_materia || selectedChat?.level || row.nivel || row.nivel_materia || row.level || 'No configurado',
    };
  }

  function conversationInsight() {
    const studentMessages = chatMessages.filter((msg) => msg.remitente === 'user');
    const yeliaMessages = chatMessages.filter((msg) => msg.remitente !== 'user');
    const studentText = studentMessages.map((msg) => msg.contenido || '').join(' ');
    const lastStudent = studentMessages[studentMessages.length - 1]?.contenido;
    const title = selectedChat?.tema || selectedChat?.topic || selectedChat?.title || 'Tema sin clasificar';
    const topic = inferTopic(`${title} ${studentText}`, title);
    const need = inferNeed(studentText || title);
    const needsHelp = /no entiendo|explica|explicame|ayuda|duda|confund|simple|recom/i.test(studentText);
    const profile = chatStudentProfile();

    return {
      topic,
      need,
      profile,
      signal: needsHelp ? 'Requiere acompanamiento' : 'Seguimiento normal',
      summary: lastStudent
        ? shortText(lastStudent, 170)
        : 'Aun no hay un mensaje del estudiante para resumir.',
      resources: topic === 'Clases y objetos'
        ? 'Sugerir recursos sobre clases, objetos, atributos, metodos y un ejemplo corto en Java o Python.'
        : `Sugerir recursos guiados sobre ${topic} y una practica corta segun su nivel.`,
      support: needsHelp
        ? 'Dar una explicacion breve, un ejemplo paso a paso y cerrar con un ejercicio pequeno.'
        : 'Revisar si el tema avanza y sugerir una practica corta para confirmar comprension.',
      adaptive: profile.nivel === 'No configurado'
        ? 'Pedir al estudiante completar ciclo, estado de materia y nivel para ajustar mejor las respuestas.'
        : `Responder con profundidad ${profile.nivel}, considerando ${profile.estado}.`,
      evidence: `${studentMessages.length} mensajes del estudiante, ${yeliaMessages.length} respuestas de YELIA.`,
      actions: {
        resources: [
          { label: 'Enviar lectura corta', detail: `Comparte una lectura breve sobre ${topic} con definicion, ejemplo y mini resumen.` },
          { label: 'Recomendar video/guia', detail: `Sugiere un video o guia introductoria de ${topic}, idealmente con ejemplo practico.` },
          { label: 'Pedir ejemplo aplicado', detail: 'Pide que el estudiante cree un ejemplo propio y explique que representa cada parte.' },
        ],
        feedback: [
          { label: 'Explicar mas simple', detail: 'Vuelve al concepto base, usa una analogia cotidiana y evita vocabulario tecnico al inicio.' },
          { label: 'Validar duda principal', detail: 'Pregunta que parte exacta no entiende: concepto, sintaxis, ejemplo o aplicacion.' },
          { label: 'Cerrar con pregunta corta', detail: 'Termina con una pregunta verificable para confirmar si ya entendio la idea central.' },
        ],
        adaptive: [
          { label: 'Ajustar nivel', detail: `Trabaja con nivel ${profile.nivel}; si no esta configurado, usa explicacion basica guiada.` },
          { label: 'Pedir completar perfil', detail: 'Pide ciclo, estado de materia y nivel de dominio para personalizar mejor la ayuda.' },
          { label: 'Cambiar ritmo', detail: 'Reduce la carga de texto y avanza con pasos pequenos, ejemplo y practica corta.' },
        ],
        profile: [
          { label: 'Revisar ciclo', detail: `Ciclo registrado: ${profile.ciclo}. Ajusta profundidad segun su avance academico.` },
          { label: 'Revisar estado', detail: `Estado en la materia: ${profile.estado}. Usa esto para decidir si reforzar o avanzar.` },
          { label: 'Revisar dominio', detail: `Nivel de dominio: ${profile.nivel}. Adapta vocabulario, dificultad y ejercicios.` },
        ],
        next: [
          { label: 'Asignar practica', detail: `Propone una practica pequena sobre ${topic} con solucion esperada.` },
          { label: 'Dar ejemplo paso a paso', detail: 'Construye un ejemplo completo y explica cada parte en orden.' },
          { label: 'Revisar en clase', detail: 'Marca este caso como duda recurrente para revisarlo con el grupo.' },
        ],
      },
    };
  }

  function renderChatInsight() {
    const insight = conversationInsight();
    const cards = [
      { key: 'resources', title: '1. Recomendacion de recursos', label: insight.topic, text: insight.resources, icon: 'bi-journal-bookmark' },
      { key: 'feedback', title: '2. Retroalimentacion personalizada', label: insight.need, text: insight.summary, icon: 'bi-chat-square-heart' },
      { key: 'adaptive', title: '3. Personalizacion adaptativa', label: `Nivel: ${insight.profile.nivel}`, text: insight.adaptive, icon: 'bi-sliders' },
      { key: 'profile', title: 'Perfil academico', label: `${insight.profile.ciclo} / ${insight.profile.nivel}`, text: `${insight.profile.estado}`, icon: 'bi-person-lines-fill' },
      { key: 'next', title: 'Accion docente', label: insight.signal, text: insight.support, icon: 'bi-lightning-charge' },
    ];
    const active = cards.find((card) => card.key === activeInsight) || cards[0];
    return (
      <div className="teacher-insight-zone">
        <div className="teacher-insight-title">
          <span>Sintesis docente</span>
          <b>Recursos, retroalimentacion y adaptacion</b>
        </div>
        <div className="teacher-chat-insight" aria-label="Sintesis docente del chat">
          {cards.map((card) => (
            <button
              className={`teacher-insight-card ${active.key === card.key ? 'active' : ''}`}
              key={card.key}
              type="button"
              onClick={() => setActiveInsight(card.key)}
            >
              <i className={`bi ${card.icon}`}></i>
              <span>{card.title}</span>
              <b>{card.label}</b>
              <p>{card.text}</p>
            </button>
          ))}
        </div>
        <div className="teacher-insight-detail">
          <div>
            <span>{active.title}</span>
            <b>{active.label}</b>
            <p>{active.text}</p>
            <small>{insight.evidence}</small>
          </div>
          <div className="teacher-insight-actions">
            {(insight.actions[active.key] || []).map((action) => (
              <button type="button" key={action.label} disabled={actionLoading} onClick={() => applyTeacherAction(action, active, insight)}>
                {action.label}
              </button>
            ))}
          </div>
        </div>
        {activeTeacherAction ? (
          <div className="teacher-action-preview">
            <span>Accion seleccionada</span>
            <b>{activeTeacherAction.label}</b>
            <p>{activeTeacherAction.detail}</p>
          </div>
        ) : null}
      </div>
    );
  }

  function chatsForStudent(student) {
    if (!student) return [];
    const alias = studentLabel(student).toLowerCase();
    return chats.filter((chat) => {
      const haystack = `${chat.usuario || ''} ${chat.student_alias || ''} ${chat.alias || ''} ${chat.title || ''}`.toLowerCase();
      return haystack.includes(alias) || haystack.includes((student.alias || '').toLowerCase());
    });
  }

  async function load() {
    setLoading(true);
    try {
      const m = await api.get('/api/teacher/me');
      if (!m.authenticated) {
        location.href = '/teacher/login';
        return;
      }
      setMe(m);
      const d = await api.get(`/api/teacher/dashboard?days=${days}`);
      setDash(d);
      const s = await api.get(`/api/teacher/students?limit=40&offset=0&q=${encodeURIComponent(q)}`);
      setStudents(asArray(s, 'students', 'items'));
      const c = await api.get(`/api/admin/chats?limit=30&offset=0&q=${encodeURIComponent(q)}&days=${days}&student=`);
      setChats(asArray(c, 'rows', 'chats', 'items', 'conversations'));
      const routes = await api.get(`/api/teacher/learning-routes?limit=80&q=${encodeURIComponent(q)}`);
      setLearningRoutes(asArray(routes, 'items', 'routes'));
      setLearningSummary(routes.summary || {});
      api.get('/api/db/health').then(setDbHealth).catch(() => setDbHealth({}));
      api.get('/api/status/summary').then(setStatusSummary).catch(() => setStatusSummary({}));
      const settingsData = await api.get('/api/teacher/settings').catch(() => ({}));
      if (settingsData && settingsData.settings) {
        setAllowPdf(settingsData.settings.allow_pdf_download === '1');
      }
    } catch (e) {
      notify(e.message, 'error');
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await api.post('/api/teacher/auth/logout', {}).catch(() => {});
    location.href = '/teacher/login';
  }

  async function openChat(chat) {
    const id = chat?.id || chat?.conversation_id;
    if (!id) return;
    setSelectedChat(chat);
    setActiveInsight('resources');
    setActiveTeacherAction(null);
    try {
      const data = await api.get(`/api/teacher/conversations/${id}/messages`);
      setChatMessages(data?.messages || data?.conversation?.messages || []);
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function applyTeacherAction(action, activeCard, insight) {
    const convId = selectedChat?.id || selectedChat?.conversation_id;
    if (!convId || !action?.label) return;
    setActionLoading(true);
    try {
      const result = await api.post(`/api/teacher/conversations/${convId}/actions`, {
        action_key: action.label.toLowerCase().replace(/\s+/g, '_'),
        insight_key: activeCard?.key || activeInsight,
        action_label: action.label,
        detail: action.detail,
        topic: insight?.topic || selectedChat?.tema || selectedChat?.topic || '',
      });
      await openChat(selectedChat);
      setActiveInsight(activeCard?.key || activeInsight);
      setActiveTeacherAction({ ...action, applied: true, serverMessage: result?.teacher_action?.detail || '' });
      notify('Accion enviada al perfil del estudiante.', 'success');
    } catch (e) {
      notify(e.message || 'No se pudo aplicar la accion.', 'error');
    } finally {
      setActionLoading(false);
    }
  }

  async function saveStudentEdit() {
    if (!editingStudent?.id) return;
    try {
      await api.patch(`/api/admin/students/${editingStudent.id}`, {
        email: editingStudent.email || '',
        role: editingStudent.role || 'student',
        status: editingStudent.status || 'active',
      });
      notify('Estudiante actualizado.', 'success');
      setEditingStudent(null);
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function createStudent() {
    const alias = newStudentForm.alias.trim();
    if (!alias) {
      notify('Alias del estudiante requerido.', 'error');
      return;
    }
    try {
      await api.post('/api/admin/students', {
        alias,
        email: newStudentForm.email.trim(),
        status: newStudentForm.status || 'active',
      });
      const profilePayload = {
        level_current: newStudentForm.level_current || undefined,
        course: newStudentForm.course.trim() || undefined,
        tags: newStudentForm.tags.trim() || undefined,
        notes: newStudentForm.notes.trim() || undefined,
      };
      if (Object.values(profilePayload).some(Boolean)) {
        await api.patch(`/api/admin/students/${encodeURIComponent(alias)}/profile`, profilePayload);
      }
      notify('Estudiante creado para seguimiento docente.', 'success');
      setNewStudentForm(emptyTeacherStudentForm);
      setShowStudentForm(false);
      load();
    } catch (e) {
      notify(e.message || 'No se pudo crear el estudiante.', 'error');
    }
  }

  async function handleTogglePdf(e) {
    const checked = e.target.checked;
    setAllowPdf(checked);
    try {
      const res = await api.post('/api/teacher/settings', {
        allow_pdf_download: checked ? '1' : '0'
      });
      if (res.success) {
        notify('Configuración de PDF actualizada.', 'success');
      } else {
        notify(res.message || 'Error al actualizar configuración.', 'error');
      }
    } catch (err) {
      notify(err.message || 'Error de red.', 'error');
      setAllowPdf(!checked);
    }
  }

  function go(nextView) {
    setView(nextView);
    window.location.hash = nextView;
  }

  useLayoutEffect(() => {
    document.body.className = 'teacher-pro desktop-pro';
    const initialHash = window.location.hash.replace('#', '');
    setView(['students', 'chats', 'synthesis', 'metrics', 'route', 'db', 'status'].includes(initialHash) ? initialHash : 'dashboard');
    try {
      setCollapsed(window.localStorage.getItem('yelia_teacher_sidebar') === 'collapsed');
    } catch {
      setCollapsed(false);
    }
    const onHashChange = () => {
      const next = window.location.hash.replace('#', '');
      setView(['students', 'chats', 'synthesis', 'metrics', 'route', 'db', 'status'].includes(next) ? next : 'dashboard');
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  useEffect(() => {
    load();
  }, [days]);

  useEffect(() => {
    if (!chatGroups.length) {
      setSelectedChatStudent('');
      return;
    }
    if (!chatGroups.some((group) => group.student === selectedChatStudent)) {
      setSelectedChatStudent(chatGroups[0].student);
    }
  }, [chatGroups, selectedChatStudent]);

  useEffect(() => {
    if (!visibleLearningRoutes.length) {
      setSelectedLearningUser('');
      return;
    }
    if (!visibleLearningRoutes.some((route) => route.usuario === selectedLearningUser)) {
      setSelectedLearningUser(visibleLearningRoutes[0].usuario);
    }
  }, [visibleLearningRoutes, selectedLearningUser]);

  useEffect(() => {
    try {
      window.localStorage.setItem('yelia_teacher_sidebar', collapsed ? 'collapsed' : 'open');
    } catch {
      /* Preferencia visual opcional. */
    }
  }, [collapsed]);

  return (
    <div className={`teacher-shell ${collapsed ? 'is-collapsed' : ''}`}>
      <aside className="teacher-sidebar">
        <div className="teacher-brand">
          <span><i className="bi bi-mortarboard"></i></span>
          <div><b>YELIA4AP</b><small>Panel Docente</small></div>
          <button className="teacher-collapse" type="button" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Mostrar menu' : 'Ocultar menu'}>
            <i className={`bi ${collapsed ? 'bi-layout-sidebar-inset' : 'bi-chevron-left'}`}></i>
          </button>
        </div>
        <nav>
          <a className={view === 'dashboard' ? 'active' : ''} href="#dashboard" onClick={(e) => { e.preventDefault(); go('dashboard'); }}><i className="bi bi-speedometer2"></i><span>Dashboard</span></a>
          <a className={view === 'students' ? 'active' : ''} href="#students" onClick={(e) => { e.preventDefault(); go('students'); }}><i className="bi bi-people"></i><span>Estudiantes</span></a>
          <a className={view === 'chats' ? 'active' : ''} href="#chats" onClick={(e) => { e.preventDefault(); go('chats'); }}><i className="bi bi-chat-dots"></i><span>Chats</span></a>
          <a className={view === 'synthesis' ? 'active' : ''} href="#synthesis" onClick={(e) => { e.preventDefault(); go('synthesis'); }}><i className="bi bi-stars"></i><span>Sintesis docente</span></a>
          <a className={view === 'metrics' ? 'active' : ''} href="#metrics" onClick={(e) => { e.preventDefault(); go('metrics'); }}><i className="bi bi-graph-up"></i><span>Metricas</span></a>
          <a className={view === 'route' ? 'active' : ''} href="#route" onClick={(e) => { e.preventDefault(); go('route'); }}><i className="bi bi-map"></i><span>Ruta academica</span></a>
          <a className={view === 'db' ? 'active' : ''} href="#db" onClick={(e) => { e.preventDefault(); go('db'); }}><i className="bi bi-database"></i><span>Base de datos</span></a>
          <a className={view === 'status' ? 'active' : ''} href="#status" onClick={(e) => { e.preventDefault(); go('status'); }}><i className="bi bi-activity"></i><span>Estado</span></a>
          <a href="/demo"><i className="bi bi-grid"></i><span>Portal</span></a>
        </nav>
        <button className="teacher-logout" type="button" onClick={logout} title="Salir"><i className="bi bi-box-arrow-left"></i><span>Salir</span></button>
      </aside>

      <main className="teacher-content">
        <header className="teacher-hero">
          <div>
            <span className="teacher-eyebrow">Seguimiento academico</span>
            <h1>Panel Docente</h1>
            <p>Revisa actividad, estudiantes, temas frecuentes y evidencia de uso del asistente.</p>
          </div>
          <div className="teacher-toolbar">
            <span className="teacher-pill">Usuario: {me.username || '-'}</span>
            <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
              <option value="7">Ultimos 7 dias</option>
              <option value="30">Ultimos 30 dias</option>
              <option value="90">Ultimos 90 dias</option>
            </select>
            <button type="button" onClick={load} disabled={loading}>{loading ? 'Cargando...' : 'Actualizar'}</button>
          </div>
        </header>

        <div className="teacher-workspace">
        {view === 'dashboard' && <section id="dashboard" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Resumen</h2><p>Indicadores principales del periodo seleccionado.</p></div>
          </div>
          <div className="teacher-kpi-grid">
            <KpiCard label="Interacciones" value={kpis.interactions} icon="bi-chat-square-text" />
            <KpiCard label="Conversaciones" value={kpis.conversations} icon="bi-chat-dots" />
            <KpiCard label="Adjuntos" value={kpis.attachments} icon="bi-paperclip" />
            <KpiCard label="Estudiantes activos" value={kpis.active_students} icon="bi-person-check" />
          </div>
          <div className="teacher-topic-box">
            <strong>Temas que buscan los estudiantes</strong>
            <div>
              {topTopics.length ? topTopics.map((topic, index) => (
                <span className="teacher-chip" key={index}>{topic.tema || topic.topic || topic.name} - {topic.n || topic.total || 0} consultas</span>
              )) : <span className="teacher-chip">Sin datos aun</span>}
            </div>
          </div>
          <div className="teacher-dashboard-live">
            <article className="teacher-live-card">
              <div className="teacher-live-head">
                <div>
                  <strong>Estudiantes activos</strong>
                  <p>Usuarios con actividad reciente en YELIA.</p>
                </div>
                <button type="button" onClick={() => go('students')}>Ver todos</button>
              </div>
              <div className="teacher-live-list">
                {activeStudents.length ? activeStudents.map((student) => (
                  <button className="teacher-live-row" type="button" key={student.id || studentLabel(student)} onClick={() => { setSelectedStudent(student); go('students'); }}>
                    <span className="teacher-live-avatar"><i className="bi bi-person"></i></span>
                    <span className="teacher-live-main">
                      <b>{studentLabel(student)}</b>
                      <small>{student.role || 'student'} - {student.status || 'active'}</small>
                    </span>
                    <span className="teacher-live-time">{fmtDate(student.last_seen || student.updated_at || student.created_at)}</span>
                    <i className="teacher-live-dot"></i>
                  </button>
                )) : <span className="teacher-empty-inline">Aun no hay estudiantes activos.</span>}
              </div>
            </article>

            <article className="teacher-live-card">
              <div className="teacher-live-head">
                <div>
                  <strong>Actividad reciente</strong>
                  <p>Ultimas conversaciones y temas trabajados.</p>
                </div>
                <button type="button" onClick={() => go('chats')}>Ver chats</button>
              </div>
              <div className="teacher-live-list">
                {recentChats.length ? recentChats.map((chat) => (
                  <button className="teacher-live-row" type="button" key={chat.id || chat.conversation_id} onClick={() => { openChat(chat); go('chats'); }}>
                    <span className="teacher-live-avatar chat"><i className="bi bi-chat-dots"></i></span>
                    <span className="teacher-live-main">
                      <b>{chatLabel(chat)}</b>
                      <small>{studentLabel(chat)} - {chat.tema || chat.topic || 'Tema sin clasificar'}</small>
                    </span>
                    <span className="teacher-live-time">{fmtDate(chat.updated_at || chat.created_at)}</span>
                  </button>
                )) : <span className="teacher-empty-inline">Aun no hay actividad reciente.</span>}
              </div>
            </article>
          </div>
        </section>}

        {view === 'students' && <section id="students" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Estudiantes en seguimiento</h2><p>Nombre visible, estado, ultima actividad y conversaciones relacionadas.</p></div>
            <div className="teacher-search">
              <input placeholder="Buscar alias o email..." value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') load(); }} />
              <button type="button" onClick={load}>Buscar</button>
              <button type="button" onClick={() => setShowStudentForm(!showStudentForm)}>{showStudentForm ? 'Cerrar' : 'Crear'}</button>
            </div>
          </div>
          {showStudentForm ? <div className="teacher-create-student-card">
            <div>
              <b>Crear estudiante</b>
              <p>Agrega un estudiante al seguimiento y configura un perfil inicial si ya conoces su nivel.</p>
            </div>
            <input value={newStudentForm.alias} placeholder="Alias o codigo" onChange={(e) => setNewStudentForm({ ...newStudentForm, alias: e.target.value })} />
            <input value={newStudentForm.email} placeholder="Email opcional" onChange={(e) => setNewStudentForm({ ...newStudentForm, email: e.target.value })} />
            <select value={newStudentForm.status} onChange={(e) => setNewStudentForm({ ...newStudentForm, status: e.target.value })}><option value="active">Activo</option><option value="blocked">Bloqueado</option></select>
            <select value={newStudentForm.level_current} onChange={(e) => setNewStudentForm({ ...newStudentForm, level_current: e.target.value })}><option value="">Nivel por definir</option><option value="basico">Basico</option><option value="intermedio">Intermedio</option><option value="avanzado">Avanzado</option></select>
            <input value={newStudentForm.course} placeholder="Materia / ciclo" onChange={(e) => setNewStudentForm({ ...newStudentForm, course: e.target.value })} />
            <input value={newStudentForm.tags} placeholder="Etiquetas: repaso, proyecto..." onChange={(e) => setNewStudentForm({ ...newStudentForm, tags: e.target.value })} />
            <textarea value={newStudentForm.notes} placeholder="Notas docentes opcionales" onChange={(e) => setNewStudentForm({ ...newStudentForm, notes: e.target.value })} />
            <div className="teacher-edit-actions">
              <button type="button" onClick={createStudent}>Crear estudiante</button>
              <button type="button" onClick={() => { setNewStudentForm(emptyTeacherStudentForm); setShowStudentForm(false); }}>Cancelar</button>
            </div>
          </div> : null}
          {editingStudent ? <div className="teacher-edit-card">
            <div><b>Editar estudiante</b><p>Actualiza datos basicos visibles para seguimiento.</p></div>
            <input value={editingStudent.email || ''} placeholder="Email" onChange={(e) => setEditingStudent({ ...editingStudent, email: e.target.value })} />
            <select value={editingStudent.status || 'active'} onChange={(e) => setEditingStudent({ ...editingStudent, status: e.target.value })}><option value="active">Activo</option><option value="blocked">Bloqueado</option></select>
            <select value={editingStudent.role || 'student'} onChange={(e) => setEditingStudent({ ...editingStudent, role: e.target.value })}><option value="student">Estudiante</option><option value="teacher">Docente</option><option value="admin">Admin</option></select>
            <div className="teacher-edit-actions"><button type="button" onClick={saveStudentEdit}>Guardar</button><button type="button" onClick={() => setEditingStudent(null)}>Cancelar</button></div>
          </div> : null}
          {selectedStudent ? <div className="teacher-detail-panel">
            <div className="teacher-detail-head">
              <div>
                <span className="teacher-chip">Detalle estudiante</span>
                <h3>{studentLabel(selectedStudent)}</h3>
                <p>{selectedStudent.email || 'Sin email'} - {selectedStudent.role || 'student'} - {selectedStudent.status || 'active'}</p>
              </div>
              <div className="teacher-detail-actions">
                <button type="button" onClick={() => setEditingStudent({ ...selectedStudent, role: selectedStudent.role || 'student', status: selectedStudent.status || 'active' })}>Editar</button>
                <button type="button" onClick={() => setSelectedStudent(null)}>Cerrar</button>
              </div>
            </div>
            <div className="teacher-detail-grid">
              <MiniCard label="Ultimo visto" value={fmtDate(selectedStudent.last_seen || selectedStudent.updated_at || selectedStudent.created_at)} hint="Actividad reciente" icon="bi-clock-history" />
              <MiniCard label="Nivel" value={selectedStudent.level || selectedStudent.nivel || 'Sin datos'} hint="Perfil registrado" icon="bi-bar-chart" />
              <MiniCard label="Puntos" value={selectedStudent.points || selectedStudent.puntos || 0} hint="Progreso guardado" icon="bi-trophy" />
              <MiniCard label="Chats relacionados" value={chatsForStudent(selectedStudent).length} hint="Conversaciones visibles" icon="bi-chat-dots" />
            </div>
            <div className="teacher-related-list">
              <strong>Conversaciones del estudiante</strong>
              {chatsForStudent(selectedStudent).length ? chatsForStudent(selectedStudent).slice(0, 5).map((chat) => (
                <button type="button" key={chat.id || chat.conversation_id} onClick={() => { openChat(chat); go('chats'); }}>
                  <span>{chatLabel(chat)}</span>
                  <small>{fmtDate(chat.updated_at || chat.created_at)}</small>
                </button>
              )) : <p>No hay chats relacionados en la carga actual.</p>}
            </div>
          </div> : null}
          <Table
            cols={['ID', 'Nombre visible', 'Email', 'Estado', 'Rol', 'Ultimo visto', 'Acciones']}
            rows={students}
            render={(row) => (
              <tr key={row.id} className="teacher-click-row" onClick={() => setSelectedStudent(row)}>
                <td>{row.id}</td>
                <td><b>{studentLabel(row)}</b><div className="muted small">{row.alias && studentLabel(row) !== row.alias ? row.alias : ''}</div></td>
                <td>{row.email || '-'}</td>
                <td><span className="teacher-status">{row.status || 'active'}</span></td>
                <td>{row.role || 'student'}</td>
                <td>{fmtDate(row.last_seen || row.updated_at || row.created_at)}</td>
                <td><button className="teacher-table-action" type="button" onClick={(event) => { event.stopPropagation(); setEditingStudent({ ...row, role: row.role || 'student', status: row.status || 'active' }); }}>Editar</button></td>
              </tr>
            )}
          />
        </section>}

        {view === 'chats' && <section id="chats" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Chats por estudiante</h2><p>Elige un estudiante para revisar sus conversaciones y mensajes guardados.</p></div>
            <div className="teacher-search">
              <input placeholder="Buscar estudiante o tema..." value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') load(); }} />
              <button type="button" onClick={load}>Buscar</button>
            </div>
          </div>
          <div className="teacher-chat-grid is-chat-browser">
            <div className="teacher-chat-list teacher-chat-students">
              {chatGroups.length ? chatGroups.map((group) => (
                <button
                  className={`teacher-student-chat-group ${activeChatGroup?.student === group.student ? 'active' : ''}`}
                  key={group.student}
                  type="button"
                  onClick={() => {
                    setSelectedChatStudent(group.student);
                    if (group.chats[0]) openChat(group.chats[0]);
                  }}
                >
                  <span className="teacher-live-avatar"><i className="bi bi-person"></i></span>
                  <span>
                    <b>{group.student}</b>
                    <small>{group.chats.length} chat{group.chats.length === 1 ? '' : 's'} - {fmtDate(group.last)}</small>
                    <em>{group.topics.slice(0, 2).join(', ') || 'Sin tema detectado'}</em>
                  </span>
                </button>
              )) : <div className="teacher-empty">Sin estudiantes con conversaciones.</div>}
            </div>
            <div className="teacher-conversation-column">
              <div className="teacher-conversation-head">
                <strong>Conversaciones</strong>
                <span>{activeChatGroup?.student || 'Sin estudiante'}</span>
              </div>
              <div className="teacher-conversation-list">
                {activeChatGroup?.chats?.length ? activeChatGroup.chats.map((chat) => (
                  <button className={`teacher-chat-item ${selectedChat?.id === chat.id ? 'active' : ''}`} key={chat.id} type="button" onClick={() => openChat(chat)}>
                    <strong>{shortText(chat.title || `Chat ${chat.id}`, 54)}</strong>
                    <span>{chat.tema || chat.topic || inferTopic(chat.title)}</span>
                    <small>{fmtDate(chat.updated_at || chat.created_at)}</small>
                  </button>
                )) : <div className="teacher-empty">Selecciona un estudiante.</div>}
              </div>
            </div>
            <div className="teacher-chat-detail">
              {selectedChat ? (
                <>
                  <div className="teacher-chat-head">
                    <div>
                      <b>{shortText(selectedChat.title || `Chat ${selectedChat.id}`, 64)}</b>
                      <small>Mensajes del estudiante y respuestas de YELIA</small>
                    </div>
                    <div className="teacher-chat-head-actions">
                      <span>{shortStudentName(selectedChat)}</span>
                    </div>
                  </div>
                  <div className="teacher-message-list">
                    {chatMessages.length ? chatMessages.map((msg) => (
                      <article className={`teacher-msg ${msg.remitente === 'user' ? 'user' : 'bot'}`} key={msg.id}>
                        <span>{msg.remitente === 'user' ? 'Estudiante' : 'YELIA'} · {fmtDate(msg.created_at)}</span>
                        <p>{msg.contenido}</p>
                      </article>
                    )) : <div className="teacher-empty">Selecciona un chat para ver mensajes.</div>}
                  </div>
                </>
              ) : <div className="teacher-empty">Selecciona una conversacion del listado.</div>}
            </div>
          </div>
        </section>}

        {view === 'synthesis' && <section id="synthesis" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Sintesis docente</h2><p>Define una accion pendiente para el perfil del estudiante, sin agregarla como mensaje del chat.</p></div>
            <div className="teacher-search">
              <input placeholder="Buscar estudiante o tema..." value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') load(); }} />
              <button type="button" onClick={load}>Buscar</button>
            </div>
          </div>
          <div className="teacher-chat-grid teacher-synthesis-grid">
            <div className="teacher-chat-list teacher-chat-students">
              {chatGroups.length ? chatGroups.map((group) => (
                <button
                  className={`teacher-student-chat-group ${activeChatGroup?.student === group.student ? 'active' : ''}`}
                  key={group.student}
                  type="button"
                  onClick={() => {
                    setSelectedChatStudent(group.student);
                    if (group.chats[0]) openChat(group.chats[0]);
                  }}
                >
                  <span className="teacher-live-avatar"><i className="bi bi-person"></i></span>
                  <span>
                    <b>{group.student}</b>
                    <small>{group.chats.length} chat{group.chats.length === 1 ? '' : 's'} - {fmtDate(group.last)}</small>
                    <em>{group.topics.slice(0, 2).join(', ') || 'Sin tema detectado'}</em>
                  </span>
                </button>
              )) : <div className="teacher-empty">Sin estudiantes con conversaciones.</div>}
            </div>
            <div className="teacher-chat-detail is-summary-only">
              {selectedChat ? (
                <>
                  <div className="teacher-chat-head">
                    <div>
                      <b>{shortText(selectedChat.title || `Chat ${selectedChat.id}`, 64)}</b>
                      <small>Acciones que llegaran al perfil del estudiante</small>
                    </div>
                    <div className="teacher-chat-head-actions">
                      <span>{shortStudentName(selectedChat)}</span>
                    </div>
                  </div>
                  {renderChatInsight()}
                </>
              ) : <div className="teacher-empty">Selecciona una conversacion para ver la sintesis docente.</div>}
            </div>
          </div>
        </section>}

        {view === 'metrics' && <section id="metrics" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Metricas</h2><p>Panel de evidencia y uso sin salir del entorno docente.</p></div>
            <a className="teacher-open-link" href="/teacher/metrics" target="_blank" rel="noreferrer">Abrir aparte</a>
          </div>
          <div className="teacher-mini-grid">
            <MiniCard label="Interacciones" value={kpis.interactions || 0} hint={`Ultimos ${days} dias`} icon="bi-chat-square-text" />
            <MiniCard label="Conversaciones" value={kpis.conversations || 0} hint="Chats creados" icon="bi-chat-dots" />
            <MiniCard label="Adjuntos" value={kpis.attachments || 0} hint="Evidencia subida" icon="bi-paperclip" />
            <MiniCard label="Activos" value={kpis.active_students || 0} hint="Estudiantes recientes" icon="bi-person-check" />
          </div>
          <div className="teacher-mini-grid">
            <MiniCard label="Rutas activas" value={learningSummary.active || 0} hint="Estudiantes avanzando" icon="bi-map" />
            <MiniCard label="Promedio ruta" value={`${learningSummary.avg_progress || 0}%`} hint="Avance por unidades" icon="bi-bar-chart-steps" />
            <MiniCard label="Rutas cerradas" value={learningSummary.completed || 0} hint="Con evaluacion final" icon="bi-patch-check" />
            <MiniCard label="Estudiantes con ruta" value={learningSummary.students || 0} hint="Evidencia modular" icon="bi-people" />
          </div>
          <div className="teacher-summary-box">
            <strong>Temas destacados</strong>
            <p>{topTopics.length ? topTopics.slice(0, 4).map((t) => `${t.tema || t.topic || t.name} (${t.n || t.total || 0})`).join(' · ') : 'Aun no hay temas frecuentes para este periodo.'}</p>
          </div>
        </section>}

        {view === 'route' && <section id="route" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Ruta academica</h2><p>Avance por unidades, quiz y evaluacion final de cada estudiante.</p></div>
            <div className="teacher-search">
              <input placeholder="Buscar estudiante..." value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') load(); }} />
              <button type="button" onClick={load}>Buscar</button>
            </div>
          </div>
          
          <div className="teacher-settings-bar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', marginBottom: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: '600', color: '#fff' }}>Descarga de PDF por estudiantes</span>
              <span style={{ fontSize: '0.75rem', color: '#aaa' }}>Permite a los alumnos descargar un PDF reporte con las preguntas y respuestas correctas al terminar una lección o examen.</span>
            </div>
            <label className="yelia-switch" style={{ position: 'relative', display: 'inline-block', width: '48px', height: '24px' }}>
              <input 
                type="checkbox" 
                checked={allowPdf} 
                onChange={handleTogglePdf} 
                style={{ opacity: 0, width: 0, height: 0 }}
              />
              <span className="yelia-slider" style={{ 
                position: 'absolute', 
                cursor: 'pointer', 
                top: 0, left: 0, right: 0, bottom: 0, 
                backgroundColor: allowPdf ? '#10b981' : '#4b5563', 
                transition: '0.3s', 
                borderRadius: '24px' 
              }}>
                <span style={{ 
                  position: 'absolute', 
                  content: '""', 
                  height: '18px', width: '18px', 
                  left: allowPdf ? '26px' : '4px', 
                  bottom: '3px', 
                  backgroundColor: 'white', 
                  transition: '0.3s', 
                  borderRadius: '50%' 
                }} />
              </span>
            </label>
          </div>

          <div className="teacher-mini-grid">
            <MiniCard label="Estudiantes con ruta" value={learningSummary.students || 0} hint="Registrados en fase 2" icon="bi-people" />
            <MiniCard label="En progreso" value={learningSummary.active || 0} hint="Aun avanzan unidades" icon="bi-clock-history" />
            <MiniCard label="Completadas" value={learningSummary.completed || 0} hint="Cierre final aprobado" icon="bi-patch-check" />
            <MiniCard label="Promedio" value={`${learningSummary.avg_progress || 0}%`} hint="Avance global" icon="bi-bar-chart" />
          </div>
          <div className="teacher-route-grid">
            <aside className="teacher-route-student-list">
              {visibleLearningRoutes.length ? visibleLearningRoutes.map((route) => (
                <button
                  className={selectedLearningRoute?.usuario === route.usuario ? 'active' : ''}
                  type="button"
                  key={route.usuario}
                  onClick={() => setSelectedLearningUser(route.usuario)}
                >
                  <strong>{route.display_name || route.usuario}</strong>
                  <span>Unidad {route.current_unit || 1} - {route.progress || 0}%</span>
                  <RouteUnitDots units={route.units || []} />
                </button>
              )) : <div className="teacher-empty">Cuando un estudiante use /ruta, aqui aparecera su avance por unidades.</div>}
            </aside>
            <section className="teacher-route-detail">
              {selectedLearningRoute ? (
                <>
                  <LearningRouteCard route={selectedLearningRoute} />
                  <div className="teacher-route-unit-detail">
                    {(selectedLearningRoute.units || []).map((unit) => (
                      <article key={unit.id}>
                        <span>Unidad {unit.id}</span>
                        <strong>{unit.status === 'done' ? 'Completada' : unit.status === 'active' ? 'En curso' : 'Bloqueada'}</strong>
                        <small>{unit.quiz_percent != null ? `Quiz ${unit.quiz_percent}%` : 'Quiz pendiente'}</small>
                      </article>
                    ))}
                  </div>
                </>
              ) : <div className="teacher-empty">Selecciona un estudiante para ver su ruta.</div>}
            </section>
          </div>
        </section>}

        {view === 'db' && <section id="db" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Base de datos</h2><p>Confirma que las conversaciones, mensajes y tablas se estan guardando correctamente.</p></div>
            <a className="teacher-open-link" href="/teacher/db" target="_blank" rel="noreferrer">Abrir aparte</a>
          </div>
          <div className="teacher-mini-grid">
            <MiniCard label="Estado" value={dbHealth.ok ? 'OK' : 'Sin verificar'} hint={dbConnectionLabel} icon="bi-database-check" />
            <MiniCard label="Tablas" value={dbHealth.count || dbHealth.tables?.length || 0} hint="Tablas detectadas" icon="bi-table" />
            <MiniCard label="Conversaciones" value={statusCounts.conversations_total || 0} hint="Total guardado" icon="bi-chat-dots" />
            <MiniCard label="Mensajes" value={statusCounts.messages_total || 0} hint="Total guardado" icon="bi-card-text" />
          </div>
          <div className="teacher-summary-box">
            <strong>Tablas principales</strong>
            <p>{(dbHealth.tables || []).slice(0, 8).join(' · ') || 'Sin datos de tablas disponibles.'}</p>
          </div>
        </section>}

        {view === 'status' && <section id="status" className="teacher-card">
          <div className="teacher-section-head">
            <div><h2>Estado del sistema</h2><p>Resumen corto para saber si hay cuentas, docentes, archivos y eventos registrados.</p></div>
            <a className="teacher-open-link" href="/status" target="_blank" rel="noreferrer">Abrir aparte</a>
          </div>
          <div className="teacher-mini-grid">
            <MiniCard label="Cuentas" value={statusCounts.accounts_total || 0} hint="Usuarios staff/estudiantes" icon="bi-person-badge" />
            <MiniCard label="Docentes" value={statusCounts.teachers_total || 0} hint="Cuentas docentes" icon="bi-mortarboard" />
            <MiniCard label="Adjuntos" value={statusCounts.attachments_total || 0} hint="Archivos guardados" icon="bi-paperclip" />
            <MiniCard label="Eventos" value={statusCounts.metrics_events_total || 0} hint="Actividad registrada" icon="bi-activity" />
          </div>
        </section>}
        </div>
      </main>
    </div>
  );
}
