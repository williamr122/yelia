'use client';

import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { api } from '../../_shared/react/api.js';
import { notify } from '../../chat/react/core/notify.js';
import { asArray, fmtDate } from '../../_shared/react/format.js';

function Table({ cols, rows, render }) {
  return (
    <div className="table-wrap">
      <div className="table-responsive">
        <table className="table table-sm align-middle table-pro">
          <thead><tr>{cols.map((col) => <th key={col}>{col}</th>)}</tr></thead>
          <tbody>{rows.length ? rows.map(render) : <tr><td colSpan={cols.length} className="text-center muted">Sin datos</td></tr>}</tbody>
        </table>
      </div>
    </div>
  );
}

function MiniCard({ label, value, hint, icon }) {
  return (
    <div className="admin-mini-card">
      <i className={`bi ${icon}`}></i>
      <span>{label}</span>
      <b>{value ?? '-'}</b>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

function LogoGlyph() {
  return (
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9L12 3Z" />
      <path d="M12 7.2 16.2 9.6v4.8L12 16.8l-4.2-2.4V9.6L12 7.2Z" />
      <path d="M12 3v4.2M20 7.5l-3.8 2.1M4 7.5l3.8 2.1M12 16.8V21" />
    </svg>
  );
}

const emptyStudentForm = {
  alias: '',
  email: '',
  status: 'active',
  level_current: '',
  course: '',
  tags: '',
  notes: '',
};

export default function AdminPanel() {
  const [view, setView] = useState('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [me, setMe] = useState({});
  const [students, setStudents] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [requests, setRequests] = useState([]);
  const [chats, setChats] = useState([]);
  const [att, setAtt] = useState([]);
  const [q, setQ] = useState('');
  const [activityQuery, setActivityQuery] = useState('');
  const [kpi, setKpi] = useState({});
  const [metricsPro, setMetricsPro] = useState({});
  const [dbHealth, setDbHealth] = useState({});
  const [statusSummary, setStatusSummary] = useState({});
  const [newAccount, setNewAccount] = useState({ username: '', email: '', password: '', role: 'teacher' });
  const [newStudentForm, setNewStudentForm] = useState(emptyStudentForm);
  const [showStudentForm, setShowStudentForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [editingStudent, setEditingStudent] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const statusCounts = statusSummary.summary || {};
  const dbEngine = dbHealth.db_engine || dbHealth.engine || '';
  const dbConnectionLabel = dbEngine === 'postgresql' ? 'Conexion PostgreSQL' : dbEngine === 'sqlite' ? 'Conexion SQLite local' : 'Conexion por verificar';
  const activityStats = useMemo(() => {
    const studentsSet = new Set();
    const topicsSet = new Set();
    chats.forEach((chat) => {
      studentsSet.add(studentLabel(chat));
      if (chat.topic || chat.tema) topicsSet.add(chat.topic || chat.tema);
    });
    return {
      chats: chats.length,
      students: studentsSet.size,
      topics: topicsSet.size,
      attachments: att.length,
    };
  }, [chats, att]);
  const activityByStudent = useMemo(() => {
    const groups = new Map();
    chats.forEach((chat) => {
      const name = studentLabel(chat);
      const topic = chat.topic || chat.tema || 'Sin tema';
      const current = groups.get(name) || { name, total: 0, topics: new Set(), latest: null };
      current.total += 1;
      current.topics.add(topic);
      const date = chat.updated_at || chat.created_at || '';
      if (!current.latest || String(date) > String(current.latest)) current.latest = date;
      groups.set(name, current);
    });
    return [...groups.values()]
      .map((item) => ({ ...item, topics: [...item.topics] }))
      .sort((a, b) => b.total - a.total);
  }, [chats]);
  const activityByTopic = useMemo(() => {
    const groups = new Map();
    chats.forEach((chat) => {
      const topic = chat.topic || chat.tema || 'Sin tema';
      const current = groups.get(topic) || { topic, total: 0, students: new Set() };
      current.total += 1;
      current.students.add(studentLabel(chat));
      groups.set(topic, current);
    });
    return [...groups.values()]
      .map((item) => ({ ...item, students: [...item.students] }))
      .sort((a, b) => b.total - a.total);
  }, [chats]);
  const filteredActivityByStudent = useMemo(() => {
    const needle = activityQuery.trim().toLowerCase();
    if (!needle) return activityByStudent;
    return activityByStudent.filter((item) => `${item.name} ${item.topics.join(' ')}`.toLowerCase().includes(needle));
  }, [activityByStudent, activityQuery]);
  const filteredActivityByTopic = useMemo(() => {
    const needle = activityQuery.trim().toLowerCase();
    if (!needle) return activityByTopic;
    return activityByTopic.filter((item) => `${item.topic} ${item.students.join(' ')}`.toLowerCase().includes(needle));
  }, [activityByTopic, activityQuery]);
  const maxActivityStudentChats = useMemo(
    () => Math.max(1, ...filteredActivityByStudent.map((item) => Number(item.total || 0))),
    [filteredActivityByStudent]
  );
  const maxActivityTopicTotal = useMemo(
    () => Math.max(1, ...filteredActivityByTopic.map((item) => Number(item.total || 0))),
    [filteredActivityByTopic]
  );

  async function load() {
    try {
      const m = await api.get('/api/admin/me');
      if (!m.authenticated) {
        location.href = '/admin/login';
        return;
      }
      setMe(m);
      const [s, a, r, c, at] = await Promise.all([
        api.get(`/api/admin/students?limit=50&offset=0&q=${encodeURIComponent(q)}`).catch(() => ({ students: [], items: [], total: 0 })),
        api.get(`/api/admin/accounts?limit=50&offset=0&q=${encodeURIComponent(q)}`).catch(() => ({ accounts: [], items: [], total: 0 })),
        api.get(`/api/admin/teacher-requests?limit=50&offset=0&q=${encodeURIComponent(q)}`).catch(() => ({ requests: [], items: [], total: 0 })),
        api.get('/api/admin/chats?limit=25&offset=0&q=&days=0&student=').catch(() => ({ rows: [], total: 0 })),
        api.get('/api/admin/attachments?limit=25&offset=0').catch(() => ({ rows: [], attachments: [], items: [], total: 0 })),
      ]);
      const studentRows = asArray(s, 'students', 'items');
      const accountRows = asArray(a, 'accounts', 'items');
      setStudents(studentRows);
      setAccounts(accountRows);
      setRequests(asArray(r, 'requests', 'items'));
      setChats(asArray(c, 'rows', 'chats', 'items', 'conversations'));
      setAtt(asArray(at, 'rows', 'attachments', 'items'));
      api.get('/api/metrics/pro').then(setMetricsPro).catch(() => setMetricsPro({}));
      api.get('/api/db/health').then(setDbHealth).catch(() => setDbHealth({}));
      api.get('/api/status/summary').then(setStatusSummary).catch(() => setStatusSummary({}));
      setKpi({
        students: s.total || s.total_students || studentRows.length,
        accounts: a.total || a.total_accounts || accountRows.length,
        requests: r.total || 0,
        attachments: at.total || asArray(at, 'attachments', 'items').length,
      });
    } catch (e) {
      notify(e.message || 'No se pudo validar la sesion de administrador.', 'error');
    }
  }

  useLayoutEffect(() => {
    document.body.className = 'desktop-pro';
    try {
      setCollapsed(window.localStorage.getItem('yelia_admin_sidebar') === 'collapsed');
    } catch {
      setCollapsed(false);
    }
    load();
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem('yelia_admin_sidebar', collapsed ? 'collapsed' : 'open');
    } catch {
      /* Preferencia visual opcional. */
    }
  }, [collapsed]);

  async function logout() {
    await api.post('/api/admin/auth/logout', {}).catch(() => {});
    location.href = '/admin/login';
  }

  async function createAccount() {
    if (!newAccount.username.trim() || !newAccount.password.trim()) {
      notify('Usuario y contrasena son obligatorios.', 'error');
      return;
    }
    try {
      await api.post('/api/admin/accounts', newAccount);
      notify('Cuenta creada.', 'success');
      setNewAccount({ username: '', email: '', password: '', role: 'teacher' });
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function newStudent() {
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
      notify('Estudiante creado con datos de seguimiento.', 'success');
      setNewStudentForm(emptyStudentForm);
      setShowStudentForm(false);
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function delStudent(id) {
    if (!window.confirm('Eliminar estudiante?')) return;
    try {
      await api.del(`/api/admin/students/${id}`);
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function delAccount(id) {
    if (!window.confirm('Eliminar cuenta?')) return;
    try {
      await api.del(`/api/admin/accounts/${id}`);
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  async function saveAccountEdit() {
    if (!editingAccount?.id) return;
    try {
      const payload = {
        email: editingAccount.email || '',
        role: editingAccount.role || 'teacher',
        status: editingAccount.status || 'active',
      };
      if ((editingAccount.password || '').trim()) payload.password = editingAccount.password.trim();
      await api.patch(`/api/admin/accounts/${editingAccount.id}`, payload);
      notify('Cuenta actualizada.', 'success');
      setEditingAccount(null);
      load();
    } catch (e) {
      notify(e.message, 'error');
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

  async function decideRequest(id, action) {
    try {
      await api.post(`/api/admin/teacher-requests/${id}/${action}`, {});
      notify(action === 'approve' ? 'Solicitud aprobada.' : 'Solicitud rechazada.', 'success');
      load();
    } catch (e) {
      notify(e.message, 'error');
    }
  }

  const nav = [
    ['dashboard', 'Dashboard', 'bi-speedometer2'],
    ['students', 'Estudiantes', 'bi-people'],
    ['accounts', 'Cuentas', 'bi-person-badge'],
    ['requests', 'Solicitudes docentes', 'bi-person-plus'],
    ['metrics', 'Metricas', 'bi-graph-up-arrow'],
    ['activity', 'Chats y adjuntos', 'bi-chat-dots'],
    ['db', 'Base de datos', 'bi-database'],
    ['status', 'Estado del sistema', 'bi-activity'],
  ];

  const dashboardCards = [
    ['students', 'Estudiantes', kpi.students, 'bi-people'],
    ['accounts', 'Cuentas', kpi.accounts, 'bi-person-badge'],
    ['requests', 'Solicitudes', kpi.requests, 'bi-person-plus'],
    ['activity', 'Adjuntos', kpi.attachments, 'bi-paperclip'],
  ];

  const globalMetricsValue = statusCounts.conversations_total || metricsPro.total_conversaciones || 0;

  function studentLabel(row) {
    const raw = row?.alias || row?.student_alias || row?.usuario || row?.username || row?.email || `Estudiante ${row?.id || ''}`;
    if (String(raw).startsWith('GUEST-')) return `Invitado ${String(raw).slice(6).replace(/[-_]+/g, ' ')}`;
    if (String(raw).startsWith('Anon-')) return `Estudiante anonimo ${String(raw).slice(5, 11)}`;
    return raw;
  }

  function chatLabel(row) {
    return row?.title || row?.titulo || row?.topic || row?.tema || `Chat ${row?.id || ''}`;
  }

  function MenuGlyph() {
    return (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 7h16" />
        <path d="M4 12h16" />
        <path d="M4 17h16" />
      </svg>
    );
  }

  function chatsForStudent(student) {
    if (!student) return [];
    const alias = studentLabel(student).toLowerCase();
    return chats.filter((chat) => `${chat.usuario || ''} ${chat.student_alias || ''} ${chat.alias || ''} ${chat.title || ''}`.toLowerCase().includes(alias));
  }

  return (
    <div className={`app-shell ${collapsed ? 'is-collapsed' : ''}`}>
      <aside className="sb glass d-flex flex-column">
        <div className="brand">
          <div className="logo"><i className="bi bi-stars"></i></div>
          <div className="brand-copy"><div className="t1">YELIA4AP</div><div className="t2">Panel Administrador</div></div>
          <button className="sidebar-collapse" type="button" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Mostrar menu' : 'Ocultar menu'}>
            <MenuGlyph />
          </button>
        </div>
        <div className="sb-scroll">
          <nav className="nav d-flex flex-column">
            {nav.map((item) => (
              <a key={item[0]} className={view === item[0] ? 'active' : ''} href="#" onClick={(e) => { e.preventDefault(); setView(item[0]); }}>
                <span className="ic"><i className={`bi ${item[2]}`}></i></span><span className="nav-label">{item[1]}</span>
              </a>
            ))}
            <a href="/demo" className="portal-link">
              <span className="ic"><i className="bi bi-grid"></i></span><span className="nav-label">Portal</span>
            </a>
            <a href="/metricas" className="portal-link">
              <span className="ic"><i className="bi bi-bar-chart-line"></i></span><span className="nav-label">Metricas globales</span>
            </a>
          </nav>
        </div>
        <div className="foot">
          <button className="btn btn-outline-light w-100 admin-foot-btn" onClick={load} title="Actualizar"><i className="bi bi-arrow-clockwise"></i><span>Actualizar</span></button>
          <button className="btn btn-danger w-100 admin-foot-btn" onClick={logout} title="Salir"><i className="bi bi-box-arrow-left"></i><span>Salir</span></button>
        </div>
      </aside>

      <main className="content glass">
        <div className="topbar">
          <div><div className="fs-4 fw-bold">Administrador</div><div className="muted">Controla cuentas, estudiantes, evidencia guardada y estado de la plataforma.</div></div>
          <div className="kpi"><div className="pill">Sesion: {me.role || '-'}</div><div className="pill">Usuario: {me.username || '-'}</div></div>
          {['students', 'accounts', 'requests'].includes(view) ? (
            <form className="input-group input-group-sm yelia-min-w-320" onSubmit={(e) => { e.preventDefault(); load(); }}>
              <input className="form-control bg-transparent text-light border-secondary" value={q} onChange={(e) => setQ(e.target.value)} placeholder={view === 'students' ? 'Buscar estudiante...' : view === 'accounts' ? 'Buscar cuenta...' : 'Buscar solicitud...'} />
              <button className="btn btn-outline-secondary" type="submit">Buscar</button>
            </form>
          ) : null}
        </div>

        <div className="page">
          {view === 'dashboard' && <section className="admin-dashboard">
            <div className="admin-dashboard-grid">
              {dashboardCards.map((item) => (
                <button className="admin-dash-card" type="button" key={item[0]} onClick={() => setView(item[0])}>
                  <span>{item[1]}</span>
                  <b>{item[2] ?? '-'}</b>
                  <i className={`bi ${item[3]}`}></i>
                </button>
              ))}
              <a className="admin-dash-card admin-dash-link" href="/metricas" key="global-metrics">
                <span>Metricas globales</span>
                <b>{globalMetricsValue}</b>
                <small>Vista completa del prototipo</small>
                <i className="bi bi-bar-chart-line"></i>
              </a>
            </div>
            <div className="admin-dashboard-live">
              <article>
                <div className="admin-live-head"><b>Actividad reciente</b><button type="button" onClick={() => setView('activity')}>Ver todo</button></div>
                <div className="admin-live-list">
                  {chats.slice(0, 5).map((chat) => (
                    <button type="button" key={chat.id || chat.conversation_id} onClick={() => setView('activity')}>
                      <span><i className="bi bi-chat-dots"></i>{chatLabel(chat)}</span>
                      <small>{chat.usuario || chat.student_alias || '-'} - {fmtDate(chat.updated_at || chat.created_at)}</small>
                    </button>
                  ))}
                  {!chats.length ? <p>Sin conversaciones recientes.</p> : null}
                </div>
              </article>
              <article>
                <div className="admin-live-head"><b>Solicitudes pendientes</b><button type="button" onClick={() => setView('requests')}>Revisar</button></div>
                <div className="admin-live-list">
                  {requests.slice(0, 5).map((req) => (
                    <button type="button" key={req.id} onClick={() => { setSelectedRequest(req); setView('requests'); }}>
                      <span><i className="bi bi-person-plus"></i>{req.username || req.email || `Solicitud ${req.id}`}</span>
                      <small>{req.status || 'pending'} - {fmtDate(req.created_at)}</small>
                    </button>
                  ))}
                  {!requests.length ? <p>No hay solicitudes nuevas.</p> : null}
                </div>
              </article>
            </div>
          </section>}

          {view === 'students' && <section>
            <div className="d-flex justify-content-between mb-2"><div><b>Estudiantes registrados</b><div className="muted small">Alias visible, contacto, nivel, estado y acciones de administracion.</div></div><button className="btn btn-sm btn-primary" onClick={() => setShowStudentForm(!showStudentForm)}>{showStudentForm ? 'Cerrar' : 'Nuevo estudiante'}</button></div>
            {showStudentForm ? <div className="admin-create-student-card">
              <div>
                <b>Crear estudiante</b>
                <p className="muted small">Registra alias, contacto y perfil inicial para que YELIA pueda adaptar recomendaciones.</p>
              </div>
              <input className="form-control" value={newStudentForm.alias} placeholder="Alias o codigo" onChange={(e) => setNewStudentForm({ ...newStudentForm, alias: e.target.value })} />
              <input className="form-control" value={newStudentForm.email} placeholder="Email opcional" onChange={(e) => setNewStudentForm({ ...newStudentForm, email: e.target.value })} />
              <select className="form-select" value={newStudentForm.status} onChange={(e) => setNewStudentForm({ ...newStudentForm, status: e.target.value })}><option value="active">Activo</option><option value="blocked">Bloqueado</option></select>
              <select className="form-select" value={newStudentForm.level_current} onChange={(e) => setNewStudentForm({ ...newStudentForm, level_current: e.target.value })}><option value="">Nivel por definir</option><option value="basico">Basico</option><option value="intermedio">Intermedio</option><option value="avanzado">Avanzado</option></select>
              <input className="form-control" value={newStudentForm.course} placeholder="Materia / ciclo" onChange={(e) => setNewStudentForm({ ...newStudentForm, course: e.target.value })} />
              <input className="form-control" value={newStudentForm.tags} placeholder="Etiquetas: repaso, examen..." onChange={(e) => setNewStudentForm({ ...newStudentForm, tags: e.target.value })} />
              <textarea className="form-control" value={newStudentForm.notes} placeholder="Notas de seguimiento opcionales" onChange={(e) => setNewStudentForm({ ...newStudentForm, notes: e.target.value })} />
              <div className="admin-create-actions">
                <button className="btn btn-primary" onClick={newStudent}>Crear</button>
                <button className="btn btn-outline-light" onClick={() => { setNewStudentForm(emptyStudentForm); setShowStudentForm(false); }}>Cancelar</button>
              </div>
            </div> : null}
            {editingStudent ? <div className="admin-edit-card">
              <div><b>Editar estudiante</b><p className="muted small">Puedes ajustar email, estado y rol del usuario seleccionado.</p></div>
              <input className="form-control" value={editingStudent.email || ''} placeholder="Email" onChange={(e) => setEditingStudent({ ...editingStudent, email: e.target.value })} />
              <select className="form-select" value={editingStudent.status || 'active'} onChange={(e) => setEditingStudent({ ...editingStudent, status: e.target.value })}><option value="active">Activo</option><option value="blocked">Bloqueado</option></select>
              <select className="form-select" value={editingStudent.role || 'student'} onChange={(e) => setEditingStudent({ ...editingStudent, role: e.target.value })}><option value="student">Estudiante</option><option value="teacher">Docente</option><option value="admin">Admin</option></select>
              <div className="admin-edit-actions"><button className="btn btn-primary" onClick={saveStudentEdit}>Guardar</button><button className="btn btn-outline-light" onClick={() => setEditingStudent(null)}>Cancelar</button></div>
            </div> : null}
            {selectedStudent ? <div className="admin-detail-panel">
              <div className="admin-detail-head">
                <div><span className="admin-detail-tag">Detalle estudiante</span><h3>{studentLabel(selectedStudent)}</h3><p>{selectedStudent.email || 'Sin email'} - {selectedStudent.role || 'student'} - {selectedStudent.status || 'active'}</p></div>
                <div className="admin-detail-actions"><button className="btn btn-sm btn-outline-light" onClick={() => setEditingStudent({ ...selectedStudent, role: selectedStudent.role || 'student', status: selectedStudent.status || 'active' })}>Editar</button><button className="btn btn-sm btn-outline-light" onClick={() => setSelectedStudent(null)}>Cerrar</button></div>
              </div>
              <div className="admin-mini-grid">
                <MiniCard label="Nivel" value={selectedStudent.level || selectedStudent.nivel || '-'} hint="Perfil academico" icon="bi-bar-chart" />
                <MiniCard label="Puntos" value={selectedStudent.points || selectedStudent.puntos || 0} hint="Progreso" icon="bi-trophy" />
                <MiniCard label="Creado" value={fmtDate(selectedStudent.created_at)} hint="Registro" icon="bi-calendar" />
                <MiniCard label="Chats" value={chatsForStudent(selectedStudent).length} hint="Relacionados" icon="bi-chat-dots" />
              </div>
            </div> : null}
            <Table cols={['ID', 'Nombre visible', 'Email', 'Nivel', 'Puntos', 'Estado', 'Rol', 'Creado', 'Acciones']} rows={students} render={(r) => <tr key={r.id} className="admin-click-row" onClick={() => setSelectedStudent(r)}><td>{r.id}</td><td><b>{studentLabel(r)}</b><div className="muted small">{r.alias && studentLabel(r) !== r.alias ? r.alias : ''}</div></td><td>{r.email}</td><td>{r.level || r.nivel || '-'}</td><td>{r.points || r.puntos || 0}</td><td>{r.status}</td><td>{r.role || 'student'}</td><td>{fmtDate(r.created_at)}</td><td className="text-end"><div className="admin-row-actions"><button className="btn btn-sm btn-outline-light" onClick={(event) => { event.stopPropagation(); setEditingStudent({ ...r, role: r.role || 'student', status: r.status || 'active' }); }}>Editar</button><button className="btn btn-sm btn-outline-danger" onClick={(event) => { event.stopPropagation(); delStudent(r.id); }}>Eliminar</button></div></td></tr>} />
          </section>}

          {view === 'accounts' && <section>
            <div className="glass rounded-4 p-3 mb-3">
              <b>Crear cuenta docente/admin</b>
              <div className="row g-2 mt-2">
                <div className="col-md-3"><input className="form-control" placeholder="Usuario" value={newAccount.username} onChange={(e) => setNewAccount({ ...newAccount, username: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" placeholder="Email" value={newAccount.email} onChange={(e) => setNewAccount({ ...newAccount, email: e.target.value })} /></div>
                <div className="col-md-3"><input className="form-control" type="password" placeholder="Contrasena" value={newAccount.password} onChange={(e) => setNewAccount({ ...newAccount, password: e.target.value })} /></div>
                <div className="col-md-2"><select className="form-select" value={newAccount.role} onChange={(e) => setNewAccount({ ...newAccount, role: e.target.value })}><option value="teacher">Docente</option><option value="admin">Admin</option></select></div>
                <div className="col-md-1"><button className="btn btn-primary w-100" onClick={createAccount}>Crear</button></div>
              </div>
            </div>
            {editingAccount ? <div className="admin-edit-card">
              <div><b>Editar cuenta</b><p className="muted small">Cambia email, rol, estado o define una nueva contrasena.</p></div>
              <input className="form-control" value={editingAccount.email || ''} placeholder="Email" onChange={(e) => setEditingAccount({ ...editingAccount, email: e.target.value })} />
              <select className="form-select" value={editingAccount.role || 'teacher'} onChange={(e) => setEditingAccount({ ...editingAccount, role: e.target.value })}><option value="teacher">Docente</option><option value="admin">Admin</option></select>
              <select className="form-select" value={editingAccount.status || 'active'} onChange={(e) => setEditingAccount({ ...editingAccount, status: e.target.value })}><option value="active">Activo</option><option value="blocked">Bloqueado</option></select>
              <input className="form-control" type="password" value={editingAccount.password || ''} placeholder="Nueva contrasena opcional" onChange={(e) => setEditingAccount({ ...editingAccount, password: e.target.value })} />
              <div className="admin-edit-actions"><button className="btn btn-primary" onClick={saveAccountEdit}>Guardar</button><button className="btn btn-outline-light" onClick={() => setEditingAccount(null)}>Cancelar</button></div>
            </div> : null}
            <Table cols={['ID', 'Usuario', 'Email', 'Rol', 'Estado', 'Creado', 'Acciones']} rows={accounts} render={(r) => <tr key={r.id}><td>{r.id}</td><td>{r.username}</td><td>{r.email}</td><td>{r.role}</td><td>{r.status}</td><td>{fmtDate(r.created_at)}</td><td className="text-end"><div className="admin-row-actions"><button className="btn btn-sm btn-outline-light" onClick={() => setEditingAccount({ ...r, password: '' })}>Editar</button><button className="btn btn-sm btn-outline-danger" onClick={() => delAccount(r.id)}>Eliminar</button></div></td></tr>} />
          </section>}

          {view === 'requests' && <section><div className="mb-2"><b>Solicitudes docentes</b><div className="muted small">Docentes sin usuario pueden pedir acceso desde /teacher/login.</div></div>
            {selectedRequest ? <div className="admin-detail-panel">
              <div className="admin-detail-head">
                <div><span className="admin-detail-tag">Detalle solicitud</span><h3>{selectedRequest.username || selectedRequest.email}</h3><p>{selectedRequest.email || 'Sin email'} - {selectedRequest.status || 'pending'}</p></div>
                <div className="admin-detail-actions">
                  {selectedRequest.status === 'pending' ? <><button className="btn btn-sm btn-success" onClick={() => decideRequest(selectedRequest.id, 'approve')}>Aprobar</button><button className="btn btn-sm btn-outline-danger" onClick={() => decideRequest(selectedRequest.id, 'reject')}>Rechazar</button></> : null}
                  <button className="btn btn-sm btn-outline-light" onClick={() => setSelectedRequest(null)}>Cerrar</button>
                </div>
              </div>
              <div className="admin-request-body">
                <b>Motivo</b>
                <p>{selectedRequest.reason || 'Sin motivo registrado.'}</p>
                <small>Recibida: {fmtDate(selectedRequest.created_at)}</small>
              </div>
            </div> : null}
            <Table cols={['ID', 'Usuario', 'Email', 'Motivo', 'Estado', 'Fecha', 'Acciones']} rows={requests} render={(r) => <tr key={r.id} className="admin-click-row" onClick={() => setSelectedRequest(r)}><td>{r.id}</td><td>{r.username}</td><td>{r.email || '-'}</td><td>{r.reason || '-'}</td><td>{r.status}</td><td>{fmtDate(r.created_at)}</td><td className="text-end">{r.status === 'pending' ? <div className="d-flex gap-2 justify-content-end"><button className="btn btn-sm btn-success" onClick={(event) => { event.stopPropagation(); decideRequest(r.id, 'approve'); }}>Aprobar</button><button className="btn btn-sm btn-outline-danger" onClick={(event) => { event.stopPropagation(); decideRequest(r.id, 'reject'); }}>Rechazar</button></div> : <span className="muted small">Procesada</span>}</td></tr>} /></section>}

          {view === 'metrics' && <section className="admin-frame-card">
            <div className="admin-frame-head"><div><b>Metricas</b><p className="muted small">Resumen corto de evidencia y uso. El detalle completo queda en su panel.</p></div><div className="admin-frame-actions"><a className="btn btn-outline-light" href="/metricas" target="_blank" rel="noreferrer">Metricas globales</a><a className="btn btn-outline-light" href="/admin/metrics" target="_blank" rel="noreferrer">Abrir panel admin</a></div></div>
            <div className="admin-mini-grid">
              <MiniCard label="Conversaciones" value={metricsPro.total_conversaciones || kpi.conversations || 0} hint="Total registrado" icon="bi-chat-dots" />
              <MiniCard label="Mensajes" value={metricsPro.total_mensajes || 0} hint="Mensajes guardados" icon="bi-card-text" />
              <MiniCard label="Usuarios" value={metricsPro.total_usuarios || kpi.students || 0} hint="Usuarios con actividad" icon="bi-people" />
              <MiniCard label="Claridad" value={`${metricsPro.clarity_ratio || 0}%`} hint="Feedback positivo" icon="bi-hand-thumbs-up" />
            </div>
            <div className="admin-summary-box">
              <strong>Temas frecuentes</strong>
              <p>{(metricsPro.top_topics || []).slice(0, 5).map((t) => `${t.tema} (${t.total})`).join(' · ') || 'Aun no hay temas suficientes para resumir.'}</p>
            </div>
          </section>}

          {view === 'activity' && <section>
            <b>Auditoria de chats y adjuntos</b>
            <div className="muted small mb-2">Vista general para el administrador: volumen, estudiantes, temas y archivos guardados.</div>
            <form className="admin-local-search" onSubmit={(e) => e.preventDefault()}>
              <i className="bi bi-search"></i>
              <input value={activityQuery} onChange={(e) => setActivityQuery(e.target.value)} placeholder="Buscar estudiante o tema..." />
            </form>
            <div className="admin-mini-grid admin-activity-figure mb-3">
              <MiniCard label="Chats cargados" value={activityStats.chats} hint="Ultimos registros" icon="bi-chat-dots" />
              <MiniCard label="Estudiantes" value={activityStats.students} hint="Con chats visibles" icon="bi-people" />
              <MiniCard label="Temas" value={activityStats.topics} hint="Detectados" icon="bi-tags" />
              <MiniCard label="Adjuntos" value={activityStats.attachments} hint="Archivos visibles" icon="bi-paperclip" />
            </div>
            <div className="admin-activity-grid">
              <article className="admin-activity-panel">
                <div className="admin-live-head"><b>Chats por estudiante</b><span className="muted small">{filteredActivityByStudent.length} visibles</span></div>
                <div className="admin-activity-list admin-activity-slider admin-activity-slider-vertical" aria-label="Chats por estudiante">
                  {filteredActivityByStudent.length ? filteredActivityByStudent.map((item) => (
                    <div className="admin-activity-row admin-activity-bar-row" key={item.name}>
                      <div><b>{item.name}</b><small>{item.topics.slice(0, 3).join(' - ') || 'Sin tema'}</small></div>
                      <div className="admin-activity-meter" aria-label={`${item.total} chats`}>
                        <i style={{ width: `${Math.max(8, Math.round((Number(item.total || 0) / maxActivityStudentChats) * 100))}%` }} />
                      </div>
                      <span>{item.total} chats</span>
                    </div>
                  )) : <p className="muted mb-0">Aun no hay chats guardados.</p>}
                </div>
              </article>
              <article className="admin-activity-panel">
                <div className="admin-live-head"><b>Temas detectados</b><span className="muted small">Resumen global</span></div>
                <div className="admin-activity-list admin-activity-slider admin-activity-slider-vertical" aria-label="Temas detectados">
                  {filteredActivityByTopic.length ? filteredActivityByTopic.map((item) => (
                    <div className="admin-activity-row admin-activity-bar-row" key={item.topic}>
                      <div><b>{item.topic}</b><small>{item.students.length} estudiantes relacionados</small></div>
                      <div className="admin-activity-meter" aria-label={`${item.total} registros`}>
                        <i style={{ width: `${Math.max(8, Math.round((Number(item.total || 0) / maxActivityTopicTotal) * 100))}%` }} />
                      </div>
                      <span>{item.total} registros</span>
                    </div>
                  )) : <p className="muted mb-0">Aun no hay temas detectados.</p>}
                </div>
              </article>
              <article className="admin-activity-panel">
                <div className="admin-live-head"><b>Adjuntos guardados</b><span className="muted small">{att.length} archivos</span></div>
                <div className="admin-activity-list">
                  {att.length ? att.slice(0, 8).map((file, index) => (
                    <div className="admin-activity-row" key={file.id || index}>
                      <div><b>{file.filename || file.name || 'Archivo'}</b><small>{studentLabel(file)} - {fmtDate(file.created_at)}</small></div>
                      <span>Adjunto</span>
                    </div>
                  )) : <p className="muted mb-0">No hay adjuntos guardados todavia.</p>}
                </div>
              </article>
            </div>
          </section>}

          {view === 'db' && <section className="admin-frame-card">
            <div className="admin-frame-head"><div><b>Base de datos</b><p className="muted small">Conexion actual, tablas y registros principales guardados en el sistema.</p></div><a className="btn btn-outline-light" href="/db" target="_blank" rel="noreferrer">Abrir visor completo</a></div>
            <div className="admin-mini-grid">
              <MiniCard label="Estado" value={dbHealth.ok ? 'OK' : 'Sin verificar'} hint={dbConnectionLabel} icon="bi-database-check" />
              <MiniCard label="Tablas" value={dbHealth.count || dbHealth.tables?.length || 0} hint="Tablas detectadas" icon="bi-table" />
              <MiniCard label="Conversaciones" value={statusCounts.conversations_total || metricsPro.total_conversaciones || 0} hint="Total guardado" icon="bi-chat-dots" />
              <MiniCard label="Mensajes" value={statusCounts.messages_total || metricsPro.total_mensajes || 0} hint="Total guardado" icon="bi-card-text" />
            </div>
            <div className="admin-summary-box">
              <strong>Tablas principales</strong>
              <p>{(dbHealth.tables || []).slice(0, 10).join(' · ') || 'Sin datos de tablas disponibles.'}</p>
            </div>
          </section>}

          {view === 'status' && <section className="admin-frame-card">
            <div className="admin-frame-head"><div><b>Estado del sistema</b><p className="muted small">Resumen para confirmar cuentas, docentes, archivos y eventos antes de revisar evidencia.</p></div><a className="btn btn-outline-light" href="/status" target="_blank" rel="noreferrer">Abrir estado completo</a></div>
            <div className="admin-mini-grid admin-status-grid">
              <MiniCard label="Backend" value="OK" hint="API conectada" icon="bi-hdd-network" />
              <MiniCard label="Base de datos" value={dbHealth.ok ? 'OK' : 'Sin verificar'} hint={dbConnectionLabel} icon="bi-database-check" />
              <MiniCard label="Estudiantes" value={statusCounts.students_total || kpi.students || 0} hint="Usuarios estudiante" icon="bi-people" />
              <MiniCard label="Cuentas" value={statusCounts.accounts_total || kpi.accounts || 0} hint="Total del sistema" icon="bi-person-badge" />
              <MiniCard label="Docentes" value={statusCounts.teachers_total || 0} hint="Cuentas docentes" icon="bi-mortarboard" />
              <MiniCard label="Admins" value={statusCounts.admins_total || 0} hint="Administradores" icon="bi-shield-lock" />
              <MiniCard label="Conversaciones" value={statusCounts.conversations_total || metricsPro.total_conversaciones || 0} hint={statusCounts.conversations_table || 'Tabla activa'} icon="bi-chat-dots" />
              <MiniCard label="Mensajes" value={statusCounts.messages_total || metricsPro.total_mensajes || 0} hint="Mensajes guardados" icon="bi-card-text" />
              <MiniCard label="Adjuntos" value={statusCounts.attachments_total || kpi.attachments || 0} hint="Archivos guardados" icon="bi-paperclip" />
              <MiniCard label="Eventos" value={statusCounts.metrics_events_total || 0} hint="Metricas registradas" icon="bi-activity" />
              <MiniCard label="Feedback" value={statusCounts.feedback_total || 0} hint="Valoraciones guardadas" icon="bi-hand-thumbs-up" />
            </div>
            <div className="admin-summary-box">
              <strong>Lectura de admin</strong>
              <p>Este panel confirma que la plataforma guarda estudiantes, chats, mensajes, archivos y metricas en PostgreSQL. Para revisar tablas completas usa Base de datos; para auditoria usa Chats y adjuntos.</p>
            </div>
          </section>}
        </div>
      </main>
    </div>
  );
}
