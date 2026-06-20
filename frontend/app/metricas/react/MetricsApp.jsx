'use client';

import React, { useEffect, useLayoutEffect, useMemo, useState } from "react";
import { api, formatNumber } from "../../_shared/react/api.js";

const navItems = [
  ["resumen", "Resumen", "dashboard"],
  ["estudiantes", "Estudiantes", "users"],
  ["calor", "Mapa de calor", "heatmap"],
  ["temas", "Temas", "book"],
  ["recursos", "Recursos", "book"],
  ["feedback", "Retroalimentacion", "spark"],
  ["adaptacion", "Adaptacion", "gauge"],
  ["avatar", "Avatar 3D", "avatar"],
  ["ruta", "Ruta academica", "gauge"],
  ["tecnico", "Tecnico", "gauge"]
];

const teacherNavItems = navItems.filter(([id]) => id !== "tecnico");

const adminNavItems = [
  ["resumen", "Resumen", "dashboard"],
  ["estudiantes", "Usuarios", "users"],
  ["temas", "Uso por temas", "book"],
  ["recursos", "Recursos usados", "book"],
  ["feedback", "Feedback", "spark"],
  ["ruta", "Ruta academica", "gauge"],
  ["tecnico", "Tecnico", "gauge"]
];

const kpisTeacherMain = [
  ["academic.student_count", "Estudiantes", "Con actividad o progreso"],
  ["total_conversaciones", "Conversaciones", "Sesiones registradas"],
  ["total_mensajes", "Mensajes", "Usuario y asistente"],
  ["mensajes_promedio_por_conversacion", "Profundidad", "Promedio por conversacion", 1]
];

const kpisLearning = [
  ["feedback.up_ratio_percent", "Claridad", "Feedback positivo", 1, "%"],
  ["usabilidad.tareas_completadas_percent", "Consultas resueltas", "Con usuario y respuesta", 1, "%"],
  ["usabilidad.abandono_percent", "Abandono", "Sin respuesta del bot", 1, "%"],
  ["academic.recommendations.recent.length", "Recomendaciones", "Ultimas evidencias"]
];

const kpisTechnical = [
  ["avg_latency_ms", "Latencia media", "Respuesta del backend", 1, " ms"],
  ["p95_latency_ms", "Latencia p95", "Pico del 95% de casos", 1, " ms"],
  ["feedbackPair", "Feedback + / -", "Valoraciones registradas"],
  ["usabilidad.mensajes_por_consulta", "Mensajes por consulta", "Esfuerzo promedio", 2]
];

function getValue(source, path) {
  if (!source) return undefined;
  if (path === "feedbackPair") return `${Number(source.feedback?.up || 0)} / ${Number(source.feedback?.down || 0)}`;
  return path.split(".").reduce((acc, key) => {
    if (acc == null) return undefined;
    if (key === "length" && Array.isArray(acc)) return acc.length;
    return acc[key];
  }, source);
}

function metricValue(metrics, path, digits, suffix = "") {
  const value = getValue(metrics, path);
  if (path === "feedbackPair") return value;
  if (value === null || value === undefined || value === "") return "--";
  return `${formatNumber(value, digits)}${suffix}`;
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function displayStudentName(value) {
  const raw = String(value || "Estudiante");
  if (raw.startsWith("GUEST-")) return `Invitado ${raw.slice(6).replace(/[-_]+/g, " ")}`;
  if (raw.startsWith("Anon-")) return `Estudiante anonimo ${raw.slice(5, 11)}`;
  return raw;
}

function Icon({ name }) {
  const common = {
    width: 20,
    height: 20,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg",
    "aria-hidden": "true"
  };
  const paths = {
    dashboard: <><rect x="3" y="4" width="7" height="7" rx="2" /><rect x="14" y="4" width="7" height="5" rx="2" /><rect x="14" y="13" width="7" height="7" rx="2" /><rect x="3" y="15" width="7" height="5" rx="2" /></>,
    users: <><circle cx="9" cy="8" r="3" /><path d="M3.8 19c.8-3.1 2.6-4.6 5.2-4.6s4.4 1.5 5.2 4.6" /><circle cx="17" cy="9" r="2.4" /><path d="M15.5 14.6c2.2.2 3.8 1.6 4.7 4.4" /></>,
    heatmap: <><rect x="4" y="4" width="4" height="4" rx="1" /><rect x="10" y="4" width="4" height="4" rx="1" /><rect x="16" y="4" width="4" height="4" rx="1" /><rect x="4" y="10" width="4" height="4" rx="1" /><rect x="10" y="10" width="4" height="4" rx="1" /><rect x="16" y="10" width="4" height="4" rx="1" /><rect x="4" y="16" width="4" height="4" rx="1" /><rect x="10" y="16" width="4" height="4" rx="1" /><rect x="16" y="16" width="4" height="4" rx="1" /></>,
    book: <><path d="M5 5.5c2.2-.9 4.2-.7 6 .6v13c-1.8-1.3-3.8-1.5-6-.6z" /><path d="M19 5.5c-2.2-.9-4.2-.7-6 .6v13c1.8-1.3 3.8-1.5 6-.6z" /></>,
    spark: <><path d="M12 3l1.4 5.2L18 10l-4.6 1.8L12 17l-1.4-5.2L6 10l4.6-1.8z" /><path d="M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7z" /><path d="M5 14l.6 1.9L7.5 16.5l-1.9.6L5 19l-.6-1.9-1.9-.6 1.9-.6z" /></>,
    gauge: <><path d="M4 15a8 8 0 1 1 16 0" /><path d="M12 15l4-5" /><path d="M7 18h10" /></>,
    menu: <><path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" /></>,
    avatar: <><rect x="5" y="4" width="14" height="14" rx="5" /><path d="M9 10h.01" /><path d="M15 10h.01" /><path d="M9 14c1.8 1.3 4.2 1.3 6 0" /><path d="M12 18v3" /><path d="M8 21h8" /></>,
    logo: <><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" /><path d="M8.5 9.2L12 7l3.5 2.2v5.6L12 17l-3.5-2.2z" /></>
  };
  return <svg {...common}>{paths[name] || paths.dashboard}</svg>;
}

function Kpi({ label, value, note }) {
  return (
    <article className="metrics-kpi">
      <span className="metrics-kpi-label">{label}</span>
      <strong className="metrics-kpi-value">{value}</strong>
      <span className="metrics-kpi-note">{note}</span>
    </article>
  );
}

function SectionHeader({ id, kicker, title, meta }) {
  return (
    <header className="metrics-section-head" id={id}>
      <div>
        <span className="metrics-section-kicker">{kicker}</span>
        <h2>{title}</h2>
      </div>
      {meta ? <span className="metrics-section-meta">{meta}</span> : null}
    </header>
  );
}

function EmptyState({ children }) {
  return <div className="metrics-empty">{children}</div>;
}

function ProgressBar({ value, label }) {
  const safeValue = Math.max(0, Math.min(100, Number(value || 0)));
  return (
    <div className="metrics-progress" aria-label={label}>
      <span style={{ width: `${safeValue}%` }} />
    </div>
  );
}

function MiniBars({ items, labelKey = "topic", valueKey = "total" }) {
  const rows = asList(items);
  const max = Math.max(1, ...rows.map((item) => Number(item[valueKey] || 0)));
  if (!rows.length) return <EmptyState>No hay datos suficientes todavia.</EmptyState>;
  return (
    <div className="metrics-mini-bars">
      {rows.map((item, index) => {
        const value = Number(item[valueKey] || 0);
        const label = item[labelKey] || item.type || item.level || item.emotion || item.kind || "Sin dato";
        return (
          <div className="metrics-mini-row" key={`${label}-${index}`}>
            <span title={label}>{label}</span>
            <div><i style={{ width: `${Math.max(8, (value / max) * 100)}%` }} /></div>
            <strong>{value}</strong>
          </div>
        );
      })}
    </div>
  );
}

function StudentTable({ students, selectedUser, onSelect }) {
  const [query, setQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const [progressFilter, setProgressFilter] = useState("all");
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return students.filter((student) => {
      const name = `${student.usuario || ""} ${displayStudentName(student.usuario)} ${student.nivel || ""}`.toLowerCase();
      const progress = Number(student.engagement_score || 0);
      const levelOk = levelFilter === "all" || String(student.nivel || "Inicial").toLowerCase() === levelFilter;
      const progressOk = progressFilter === "all"
        || (progressFilter === "high" && progress >= 70)
        || (progressFilter === "mid" && progress >= 35 && progress < 70)
        || (progressFilter === "low" && progress < 35);
      return (!needle || name.includes(needle)) && levelOk && progressOk;
    });
  }, [students, query, levelFilter, progressFilter]);
  if (!students.length) return <EmptyState>Aun no hay estudiantes con actividad registrada.</EmptyState>;
  return (
    <div className="metrics-students-board">
      <form className="metrics-student-toolbar" onSubmit={(event) => event.preventDefault()}>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar estudiante por nombre..." />
        <select value={levelFilter} onChange={(event) => setLevelFilter(event.target.value)}>
          <option value="all">Nivel: todos</option>
          <option value="inicial">Inicial</option>
          <option value="basico">Basico</option>
          <option value="intermedio">Intermedio</option>
          <option value="avanzado">Avanzado</option>
        </select>
        <select value={progressFilter} onChange={(event) => setProgressFilter(event.target.value)}>
          <option value="all">Progreso: todos</option>
          <option value="high">Alto</option>
          <option value="mid">Medio</option>
          <option value="low">Bajo</option>
        </select>
        <button type="button" onClick={() => { setQuery(""); setLevelFilter("all"); setProgressFilter("all"); }}>Limpiar filtros</button>
        <span>{filtered.length} registros</span>
      </form>
      <div className="metrics-table-wrap">
      <table className="metrics-table">
        <thead>
          <tr>
            <th>Nombre visible</th>
            <th>Nivel</th>
            <th>Progreso</th>
            <th>Temas</th>
            <th>Recomendacion mas usada</th>
            <th>Quizzes</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((student) => (
            <tr
              key={student.usuario}
              className={selectedUser === student.usuario ? "is-selected" : ""}
              onClick={() => onSelect(student.usuario)}
            >
              <td>
                <button className="metrics-student-button" type="button">
                  <strong>{displayStudentName(student.usuario)}</strong>
                  <span>{student.ultima_actividad || "Sin fecha"}</span>
                </button>
              </td>
              <td><span className="metrics-pill">{student.nivel || "Inicial"}</span></td>
              <td>
                <div className="metrics-progress-cell">
                  <strong>{student.engagement_score || 0}%</strong>
                  <ProgressBar value={student.engagement_score} label="Progreso estimado" />
                </div>
              </td>
              <td>{asList(student.temas_investigados).length}</td>
              <td>{student.tema_recomendado_preferido || student.recomendacion_preferida || "--"}</td>
              <td>{Number(student.quizzes_completados || 0)} / {Number(student.quizzes || 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      {!filtered.length ? <EmptyState>No hay estudiantes con esos filtros.</EmptyState> : null}
    </div>
  );
}

function Heatmap({ heatmap, selectedUser }) {
  const topics = asList(heatmap?.topics);
  const allRows = asList(heatmap?.rows);
  const [topicQuery, setTopicQuery] = useState("");
  const [activeUser, setActiveUser] = useState(selectedUser || "");
  const [activeTopic, setActiveTopic] = useState(topics[0] || "");
  useEffect(() => {
    if (selectedUser) setActiveUser(selectedUser);
  }, [selectedUser]);
  useEffect(() => {
    if (!activeTopic && topics[0]) setActiveTopic(topics[0]);
  }, [activeTopic, topics]);
  const filteredTopics = useMemo(() => {
    const needle = topicQuery.trim().toLowerCase();
    return topics.filter((topic) => !needle || String(topic).toLowerCase().includes(needle));
  }, [topics, topicQuery]);
  const rows = allRows;
  const selectedRow = rows.find((row) => row.usuario === activeUser) || rows[0] || null;
  const selectedName = selectedRow ? displayStudentName(selectedRow.usuario) : "Sin estudiante";
  const max = Math.max(1, Number(heatmap?.max_value || 0));
  if (!topics.length || !allRows.length) return <EmptyState>El mapa de calor aparecera cuando existan mensajes con tema clasificado.</EmptyState>;

  return (
    <div className="metrics-heatmap-board">
      <section className="metrics-heat-controls">
        <article>
          <span>Vista</span>
          <strong>Por estudiante</strong>
        </article>
        <article>
          <span>Filtrar temas</span>
          <form onSubmit={(event) => event.preventDefault()}>
            <input value={topicQuery} onChange={(event) => setTopicQuery(event.target.value)} placeholder="Buscar tema o subtema..." />
          </form>
        </article>
        <article>
          <span>Nivel de actividad</span>
          <div className="metrics-heat-activity-key">
            <i className="is-high" /> Alta
            <i className="is-mid" /> Media
            <i className="is-low" /> Baja
            <i className="is-none" /> Nula
          </div>
        </article>
        <article>
          <span>Tema activo</span>
          <strong title={activeTopic}>{activeTopic || "Sin tema"}</strong>
        </article>
      </section>

      <div className="metrics-heat-layout">
        <HeatmapFigure
          rows={rows}
          topics={filteredTopics.length ? filteredTopics : topics}
          activeTopic={activeTopic}
          activeUser={selectedRow?.usuario || ""}
          max={max}
          onSelect={(usuario, topic) => {
            setActiveUser(usuario);
            setActiveTopic(topic);
          }}
        />
        <HeatmapDetail row={selectedRow} topics={topics} activeTopic={activeTopic} max={max} selectedName={selectedName} />
      </div>
    </div>
  );
}

function HeatmapSummary({ rows, topics }) {
  const rowStats = rows.map((row) => {
    const values = asList(row.values);
    const total = values.reduce((sum, cell) => sum + Number(cell.value || 0), 0);
    const strongest = [...values].sort((a, b) => Number(b.value || 0) - Number(a.value || 0))[0] || null;
    const missing = topics.filter((topic) => !values.some((cell) => cell.topic === topic && Number(cell.value || 0) > 0));
    return { usuario: row.usuario, total, strongest, missing };
  });

  const mostActive = [...rowStats].sort((a, b) => b.total - a.total)[0] || null;
  const topicTotals = topics.map((topic) => ({
    topic,
    total: rows.reduce((sum, row) => {
      const cell = asList(row.values).find((item) => item.topic === topic);
      return sum + Number(cell?.value || 0);
    }, 0)
  }));
  const dominantTopic = [...topicTotals].sort((a, b) => b.total - a.total)[0] || null;
  const lowTopics = topicTotals.filter((item) => item.total === 0).map((item) => item.topic);
  const recommendation = lowTopics.length
    ? `Conviene activar una recomendacion o actividad corta sobre: ${lowTopics.slice(0, 2).join(", ")}.`
    : `El siguiente refuerzo deberia balancear el tema menos consultado: ${[...topicTotals].sort((a, b) => a.total - b.total)[0]?.topic || "sin datos"}.`;

  return (
    <div className="metrics-heat-summary">
      <article>
        <span>Mayor actividad</span>
        <strong>{mostActive?.usuario ? displayStudentName(mostActive.usuario) : "--"}</strong>
        <p>{mostActive ? `${mostActive.total} registros en el mapa.` : "Sin actividad suficiente."}</p>
      </article>
      <article>
        <span>Tema dominante</span>
        <strong>{dominantTopic?.topic || "--"}</strong>
        <p>{dominantTopic ? `${dominantTopic.total} consultas o avances acumulados.` : "Sin temas clasificados."}</p>
      </article>
      <article>
        <span>Lectura docente</span>
        <strong>{rows.length} estudiante{rows.length === 1 ? "" : "s"}</strong>
        <p>{recommendation}</p>
      </article>
    </div>
  );
}

function HeatmapFigure({ rows, topics, activeTopic, activeUser, max, onSelect }) {
  function colorFor(value) {
    const t = Math.max(0, Math.min(1, Number(value || 0) / Math.max(1, max)));
    if (t <= 0) return "hsl(190 52% 17%)";
    if (t < 0.18) return "hsl(162 46% 36%)";
    if (t < 0.45) return "hsl(68 54% 48%)";
    if (t < 0.75) return "hsl(38 82% 55%)";
    return "hsl(8 78% 54%)";
  }
  const topicAverages = topics.map((topic) => {
    const total = rows.reduce((sum, row) => {
      const cell = asList(row.values).find((item) => item.topic === topic);
      return sum + Number(cell?.value || 0);
    }, 0);
    return rows.length ? (total / rows.length).toFixed(1) : "0.0";
  });

  return (
    <div className="metrics-heat-figure-wrap metrics-heat-table-card" role="img" aria-label="Mapa de calor por estudiante y tema">
      <div className="metrics-heat-figure-head">
        <div>
          <h3>Temas vs. estudiantes</h3>
          <p>Los colores indican el nivel de actividad por tema.</p>
        </div>
      </div>

      <div
        className="metrics-heat-matrix"
        style={{ gridTemplateColumns: `minmax(180px, 240px) repeat(${topics.length}, minmax(130px, 1fr)) minmax(105px, 120px)` }}
      >
        <div className="metrics-heat-axis is-corner"><strong>Estudiantes</strong><span>{rows.length} en total</span></div>
        {topics.map((topic) => (
          <button
            className={`metrics-heat-axis ${activeTopic === topic ? "is-active-topic" : ""}`}
            key={`topic-${topic}`}
            title={topic}
            type="button"
            onClick={() => onSelect(activeUser || rows[0]?.usuario || "", topic)}
          >
            {topic}
          </button>
        ))}
        <div className="metrics-heat-axis">Total</div>

        {rows.map((row) => (
          <React.Fragment key={`heat-row-${row.usuario}`}>
            <button
              className={`metrics-heat-row-label ${activeUser === row.usuario ? "is-active-user" : ""}`}
              title={row.usuario}
              type="button"
              onClick={() => onSelect(row.usuario, activeTopic || topics[0])}
            >
              <span>{displayStudentName(row.usuario)}</span>
              <small>{row.usuario}</small>
            </button>
            {topics.map((topic) => {
              const cell = asList(row.values).find((item) => item.topic === topic) || { value: 0 };
              const value = Number(cell.value || 0);
              return (
                <button
                  className={`metrics-heat-big-cell ${activeUser === row.usuario && activeTopic === topic ? "is-selected" : ""}`}
                  key={`${row.usuario}-${topic}-big`}
                  type="button"
                  onClick={() => onSelect(row.usuario, topic)}
                  title={`${displayStudentName(row.usuario)}: ${topic} (${value})`}
                  style={{ background: colorFor(value) }}
                >
                  <strong>{value}</strong>
                </button>
              );
            })}
            <div className="metrics-heat-total-cell">
              <strong>{asList(row.values).reduce((sum, cell) => sum + Number(cell.value || 0), 0)}</strong>
            </div>
          </React.Fragment>
        ))}
        <div className="metrics-heat-row-label is-average"><span>Promedio por tema</span></div>
        {topicAverages.map((avg, index) => <div className="metrics-heat-average-cell" key={`${topics[index]}-avg`}>{avg}</div>)}
        <div className="metrics-heat-average-cell">{topicAverages.length ? (topicAverages.reduce((sum, value) => sum + Number(value || 0), 0) / topicAverages.length).toFixed(1) : "0.0"}</div>
      </div>
    </div>
  );
}

function HeatmapDetail({ row, topics, activeTopic, max, selectedName }) {
  if (!row) return <article className="metrics-panel"><EmptyState>Selecciona un estudiante.</EmptyState></article>;
  const values = asList(row.values);
  const activeValue = Number(values.find((item) => item.topic === activeTopic)?.value || 0);
  const total = values.reduce((sum, cell) => sum + Number(cell.value || 0), 0);
  const topTopics = [...values].sort((a, b) => Number(b.value || 0) - Number(a.value || 0)).slice(0, 5);
  const activityPct = Math.round((total / Math.max(1, topics.length * max)) * 100);
  return (
    <aside className="metrics-heat-detail metrics-panel">
      <header>
        <div className="metrics-heat-person">
          <span>{selectedName.slice(0, 2).toUpperCase()}</span>
          <div>
            <h3>{selectedName}</h3>
            <p>{activityPct >= 60 ? "Alta actividad" : activityPct >= 25 ? "Actividad media" : "Actividad baja"}</p>
          </div>
        </div>
        <strong>{activityPct}%</strong>
      </header>
      <section>
        <h4>Resumen en tema activo</h4>
        <article className="metrics-heat-topic-card">
          <strong>{activeTopic || "Sin tema"}</strong>
          <span>{activeValue} consultas o evidencias</span>
        </article>
      </section>
      <section>
        <h4>Temas mas consultados</h4>
        <div className="metrics-heat-topic-list">
          {topTopics.map((item, index) => {
            const value = Number(item.value || 0);
            return (
              <div key={`${item.topic}-${index}`}>
                <span>{index + 1}. {item.topic}</span>
                <i><b style={{ width: `${Math.max(4, (value / Math.max(1, max)) * 100)}%` }} /></i>
                <strong>{value}</strong>
              </div>
            );
          })}
        </div>
      </section>
      <section className="metrics-heat-recommendation">
        <h4>Recomendacion</h4>
        <p>{activeValue > 0
          ? `Refuerza ${activeTopic} con ejemplo guiado y practica corta.`
          : `No hay evidencia en ${activeTopic || "este tema"}; conviene asignar recurso inicial.`}</p>
      </section>
    </aside>
  );
}

function StudentInsight({ student }) {
  if (!student) return <EmptyState>Selecciona un estudiante para ver sus temas, nivel y recomendaciones.</EmptyState>;
  const studied = asList(student.temas_investigados);
  const learned = asList(student.temas_aprendidos);
  const missing = asList(student.temas_no_investigados);
  return (
    <div className="metrics-student-insight">
      <div className="metrics-profile-card">
        <span>Estudiante seleccionado</span>
        <h3>{displayStudentName(student.usuario)}</h3>
        <ProgressBar value={student.engagement_score} label="Progreso del estudiante" />
        <div className="metrics-profile-grid">
          <div><strong>{student.puntos || 0}</strong><span>Puntos</span></div>
          <div><strong>{student.nivel || "Inicial"}</strong><span>Nivel</span></div>
          <div><strong>{student.mensajes_usuario || 0}</strong><span>Preguntas</span></div>
          <div><strong>{student.recomendaciones || 0}</strong><span>Recomendaciones</span></div>
        </div>
      </div>
      <div className="metrics-topic-columns">
        <TopicList title="Temas investigados" items={studied} empty="Todavia no hay temas investigados." />
        <TopicList title="Temas aprendidos" items={learned} empty="Aun no marca temas aprendidos." />
        <TopicList title="Por reforzar" items={missing} empty="No hay brechas visibles con los datos actuales." tone="warning" />
      </div>
    </div>
  );
}

function TopicList({ title, items, empty, tone }) {
  return (
    <article className={`metrics-topic-card ${tone === "warning" ? "is-warning" : ""}`}>
      <h3>{title}</h3>
      {items.length ? (
        <div className="metrics-chip-list">
          {items.slice(0, 12).map((item) => <span key={item}>{item}</span>)}
        </div>
      ) : <p>{empty}</p>}
    </article>
  );
}

function hasTopic(student, topic) {
  if (!topic) return false;
  const needle = String(topic).toLowerCase();
  const buckets = [
    ...asList(student?.temas_investigados),
    ...asList(student?.temas_aprendidos),
    student?.tema_recomendado_preferido,
  ];
  return buckets.some((item) => String(item || "").toLowerCase().includes(needle));
}

function TopicMetric({ label, value, note }) {
  return (
    <article className="metrics-topic-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

function studentWorkedTopics(student) {
  if (!student) return [];
  return [...new Set([
    ...asList(student.temas_investigados),
    ...asList(student.temas_aprendidos),
    student.tema_recomendado_preferido,
  ].filter(Boolean))];
}

function studentResourceTypes(student) {
  if (!student?.recomendacion_preferida) return [];
  return [...new Set(asList(student.recomendacion_preferida).filter(Boolean))];
}

function TopicExplorer({ students, topics, selectedUser, selectedTopic, onSelectUser, onSelectTopic }) {
  const [topicQuery, setTopicQuery] = useState("");
  const [studentQuery, setStudentQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("all");
  const topicRows = asList(topics).map((topic, index) => ({
    label: topic.tema || topic.topic || topic.name || `Tema ${index + 1}`,
    total: Number(topic.n || topic.total || 0),
  }));
  const selectedStudent = students.find((student) => student.usuario === selectedUser) || students[0] || null;
  const activeTopic = selectedTopic || topicRows[0]?.label || studentWorkedTopics(selectedStudent)[0] || "";
  const studentsForTopic = students.filter((student) => hasTopic(student, activeTopic));
  const filteredStudentsForTopic = studentsForTopic.filter((student) => {
    const needle = studentQuery.trim().toLowerCase();
    const level = String(student.nivel || "Inicial").toLowerCase();
    const name = `${student.usuario || ""} ${displayStudentName(student.usuario)} ${level}`.toLowerCase();
    return (!needle || name.includes(needle)) && (levelFilter === "all" || level === levelFilter);
  });
  const resourceTypes = studentResourceTypes(selectedStudent);
  const activeTopicTotal = topicRows.find((item) => item.label === activeTopic)?.total || 0;
  const selectedStudentName = selectedStudent ? displayStudentName(selectedStudent.usuario) : "Sin estudiante";
  const filteredTopics = topicRows.filter((item) => {
    const needle = topicQuery.trim().toLowerCase();
    if (!needle) return true;
    const related = students.filter((student) => hasTopic(student, item.label)).map((student) => displayStudentName(student.usuario)).join(" ");
    return `${item.label} ${related}`.toLowerCase().includes(needle);
  });
  const selectedStudentTopics = studentWorkedTopics(selectedStudent);
  const maxTopicTotal = Math.max(1, ...topicRows.map((item) => item.total));

  return (
    <div className="metrics-topic-redesign">
      <header className="metrics-topic-hero metrics-panel">
        <div>
          <h3>Temas buscados por estudiantes</h3>
          <p>Explora los temas mas consultados y su nivel de cobertura.</p>
        </div>
        <span>Tema activo: <strong>{activeTopic || "Sin tema"}</strong></span>
      </header>
      <div className="metrics-topic-top-grid">
      <section className="metrics-topic-filter metrics-panel">
        <div className="metrics-topic-panel-head">
          <div>
            <h3>1. Temas mas buscados</h3>
            <p>Selecciona un tema para ver los estudiantes relacionados.</p>
          </div>
        </div>
        <form className="metrics-topic-search" onSubmit={(event) => event.preventDefault()}>
          <input value={topicQuery} onChange={(event) => setTopicQuery(event.target.value)} placeholder="Buscar tema o subtema..." />
        </form>
        <div className="metrics-topic-rank-list is-topic-picker">
          {filteredTopics.length ? filteredTopics.map((topic, index) => {
            const related = students.filter((student) => hasTopic(student, topic.label));
            const coverage = students.length ? Math.round((related.length / students.length) * 100) : 0;
            return (
              <button
                className={activeTopic === topic.label ? "is-active" : ""}
                type="button"
                key={topic.label}
                onClick={() => onSelectTopic(topic.label)}
              >
                <em>{index + 1}</em>
                <span>{topic.label}<small>{coverage}% cobertura</small></span>
                <i><b style={{ width: `${Math.max(8, (topic.total / maxTopicTotal) * 100)}%` }} /></i>
                <strong>{related.length} estudiante{related.length === 1 ? "" : "s"}</strong>
              </button>
            );
          }) : <EmptyState>No hay temas con esos filtros.</EmptyState>}
        </div>
      </section>

      <section className="metrics-topic-student metrics-panel">
        <div className="metrics-topic-panel-head">
          <div>
            <h3>2. Estudiantes que buscaron este tema</h3>
            <p>Filtra y selecciona un estudiante para ver su detalle.</p>
          </div>
          <span className="metrics-pill">{filteredStudentsForTopic.length} estudiantes</span>
        </div>
        <form className="metrics-topic-student-toolbar" onSubmit={(event) => event.preventDefault()}>
          <input value={studentQuery} onChange={(event) => setStudentQuery(event.target.value)} placeholder="Buscar estudiante..." />
          <select value={levelFilter} onChange={(event) => setLevelFilter(event.target.value)}>
            <option value="all">Todos</option>
            <option value="inicial">Inicial</option>
            <option value="basico">Basico</option>
            <option value="intermedio">Intermedio</option>
            <option value="avanzado">Avanzado</option>
          </select>
        </form>
        <div className="metrics-topic-student-table">
          <div className="metrics-topic-student-head"><span>Estudiante</span><span>Consultas</span><span>Nivel</span><span>Avance</span></div>
          {filteredStudentsForTopic.length ? filteredStudentsForTopic.map((student) => {
            const studentTopics = studentWorkedTopics(student);
            const consultations = Math.max(1, studentTopics.filter((topic) => hasTopic({ temas_investigados: [topic] }, activeTopic)).length || Number(student.mensajes_usuario || 0));
            return (
              <button
                className={selectedStudent?.usuario === student.usuario ? "is-active" : ""}
                type="button"
                key={student.usuario}
                onClick={() => onSelectUser(student.usuario)}
              >
                <strong>{displayStudentName(student.usuario)}<small>{studentTopics.slice(0, 2).join(" - ") || "Sin temas visibles"}</small></strong>
                <span>{consultations}</span>
                <span className="metrics-level-dot">{student.nivel || "Inicial"}</span>
                <span className="metrics-topic-progress"><b>{student.engagement_score || 0}%</b><i><em style={{ width: `${Math.max(4, Number(student.engagement_score || 0))}%` }} /></i></span>
              </button>
            );
          }) : <EmptyState>No hay estudiantes asociados a este tema.</EmptyState>}
        </div>
      </section>
      </div>

      <section className="metrics-topic-detail metrics-panel is-full">
        <div className="metrics-topic-panel-head">
          <div>
            <h3>3. Detalle del estudiante seleccionado</h3>
            <p>Lectura pedagogica para el estudiante dentro del tema activo.</p>
          </div>
          <span className="metrics-pill">{selectedStudentName}</span>
        </div>
        <div className="metrics-topic-detail-grid">
          <article className="metrics-topic-profile">
            <h3>{selectedStudentName}</h3>
            <span>{selectedStudent?.nivel || "Inicial"} - {selectedStudent?.engagement_score || 0}% avance</span>
            <div className="metrics-profile-grid">
              <div><strong>{activeTopicTotal}</strong><span>Consultas del tema</span></div>
              <div><strong>{studentsForTopic.length}</strong><span>Estudiantes</span></div>
              <div><strong>{students.length ? Math.round((studentsForTopic.length / students.length) * 100) : 0}%</strong><span>Cobertura</span></div>
            </div>
          </article>
          <div className="metrics-topic-card">
            <h3>Temas consultados por el estudiante</h3>
            <div className="metrics-topic-student-topics">
              {selectedStudentTopics.slice(0, 4).map((topic, index) => (
                <article key={topic}>
                  <strong>{index + 1}. {topic}</strong>
                  <span>{topic === activeTopic ? "Tema activo" : "Tema relacionado"}</span>
                  <i><b style={{ width: `${topic === activeTopic ? 88 : 48}%` }} /></i>
                </article>
              ))}
            </div>
          </div>
          <div className="metrics-topic-card is-warning">
            <h3>Recomendaciones</h3>
            <p>{selectedStudent && hasTopic(selectedStudent, activeTopic)
              ? `Refuerza ${activeTopic} con ejemplos guiados, practica corta y retroalimentacion personalizada.`
              : `Selecciona un estudiante relacionado para ver su lectura dentro de ${activeTopic || "este tema"}.`}</p>
            {resourceTypes.length ? <div className="metrics-chip-list">{resourceTypes.map((type) => <span key={type}>{metricLabel(type)}</span>)}</div> : null}
          </div>
        </div>
      </section>
    </div>
  );
}

function metricLabel(value) {
  const labels = {
    web_resource: "Enlaces y lecturas web",
    practice: "Ejercicios de practica",
    glossary: "Glosario de conceptos",
    history_practice: "Practica segun historial",
    quiz: "Mini quiz de refuerzo",
    advanced: "Material avanzado",
    foundation: "Base teorica",
    needs_help: "Necesita apoyo",
    confused: "Duda o confusion",
    progress: "Avance academico",
    understood: "Comprension lograda",
    practice_requested: "Pidio ejercicios",
    sin_clasificar: "Sin clasificar",
    neutral: "Neutral",
  };
  return labels[value] || String(value || "Sin dato").replace(/[_-]+/g, " ");
}

function ResourceMetricsPanel({ recommendations, onTopic }) {
  const recent = asList(recommendations?.recent);
  const typeRows = asList(recommendations?.by_type).map((item) => ({ ...item, label: metricLabel(item.type) }));
  const topicRows = asList(recommendations?.by_topic);
  const maxType = Math.max(1, ...typeRows.map((item) => Number(item.total || 0)));
  const maxTopic = Math.max(1, ...topicRows.map((item) => Number(item.total || 0)));
  return (
    <div className="metrics-resource-board">
      <article className="metrics-panel metrics-resource-hero">
        <div>
          <span className="metrics-section-kicker">Primero</span>
          <h3>Recomendacion de recursos</h3>
          <p className="metrics-panel-copy">Materiales que YELIA recomendo o genero para reforzar el aprendizaje.</p>
        </div>
        <div className="metrics-resource-total">
          <strong>{typeRows.reduce((sum, item) => sum + Number(item.total || 0), 0)}</strong>
          <span>recursos registrados</span>
        </div>
      </article>

      <article className="metrics-panel metrics-resource-section">
        <div className="metrics-resource-head">
          <div>
            <h3>Tipos de recursos</h3>
            <p className="metrics-panel-copy">Que pide o genera YELIA con mas frecuencia.</p>
          </div>
          <span>{typeRows.length} tipos</span>
        </div>
        <div className="metrics-resource-rail" aria-label="Tipos de recursos">
          {typeRows.length ? typeRows.map((item) => {
            const value = Number(item.total || 0);
            return (
              <article className="metrics-resource-card" key={item.type}>
                <strong>{item.label}</strong>
                <div className="metrics-resource-meter"><i style={{ width: `${Math.max(8, (value / maxType) * 100)}%` }} /></div>
                <span>{value} registros</span>
              </article>
            );
          }) : <EmptyState>No hay recursos registrados.</EmptyState>}
        </div>
      </article>

      <article className="metrics-panel metrics-resource-section">
        <div className="metrics-resource-head">
          <div>
            <h3>Temas con mas recursos</h3>
            <p className="metrics-panel-copy">Contenidos que requieren lecturas, guias, quiz o ejercicios de practica.</p>
          </div>
          <span>Grafica</span>
        </div>
        <div className="metrics-resource-rail is-topic-rail" aria-label="Temas con mas recursos">
          {topicRows.length ? topicRows.map((item) => {
            const value = Number(item.total || 0);
            return (
              <button className="metrics-resource-card is-topic" type="button" key={item.topic} onClick={() => onTopic(item.topic)} title="Abrir detalle del tema">
                <strong>{item.topic || "Sin tema"}</strong>
                <div className="metrics-resource-meter"><i style={{ width: `${Math.max(8, (value / maxTopic) * 100)}%` }} /></div>
                <span>{value} recomendaciones</span>
              </button>
            );
          }) : <EmptyState>No hay temas con recursos registrados.</EmptyState>}
        </div>
      </article>

      <article className="metrics-panel metrics-resource-section">
        <div className="metrics-resource-head">
          <div>
            <h3>Ultimos recursos generados</h3>
            <p className="metrics-panel-copy">Evidencia reciente por estudiante, tema y nivel.</p>
          </div>
          <span>{recent.length} visibles</span>
        </div>
        <div className="metrics-resource-rail is-recent-rail" aria-label="Ultimos recursos generados">
          {recent.length ? recent.slice(0, 10).map((item) => (
            <article className="metrics-resource-card is-recent" key={item.id}>
              <span>{metricLabel(item.recommendation_type)}</span>
              <strong>{item.title || item.topic || "Recurso"}</strong>
              <small>{displayStudentName(item.usuario || "Sin usuario")}</small>
              <small>{item.topic || "Sin tema"} - {item.level_used || "Sin nivel"}</small>
            </article>
          )) : <EmptyState>No hay recursos registrados.</EmptyState>}
        </div>
      </article>
    </div>
  );
}

function FeedbackMetricsPanel({ metrics }) {
  const adaptive = asList(metrics?.academic?.adaptive_feedback?.by_kind).map((item) => ({
    ...item,
    kind: metricLabel(item.kind),
  }));
  return (
    <div className="metrics-grid">
      <article className="metrics-panel">
        <h3>Segundo: retroalimentacion personalizada</h3>
        <p className="metrics-panel-copy">Senales detectadas para saber si el estudiante necesita ayuda, practica o una explicacion mas clara.</p>
        <MiniBars items={adaptive} labelKey="kind" />
      </article>
      <article className="metrics-panel">
        <h3>Claridad de respuestas</h3>
        <div className="metrics-kpi-grid is-compact">
          <Kpi label="Feedback positivo" value={`${metricValue(metrics, "feedback.up_ratio_percent", 1, "%")}`} note="Valoraciones claras" />
          <Kpi label="Feedback + / -" value={metricValue(metrics, "feedbackPair")} note="Balance registrado" />
          <Kpi label="Consultas resueltas" value={`${metricValue(metrics, "usabilidad.tareas_completadas_percent", 1, "%")}`} note="Con respuesta del bot" />
          <Kpi label="Abandono" value={`${metricValue(metrics, "usabilidad.abandono_percent", 1, "%")}`} note="Sin continuidad" />
        </div>
        <div className="metrics-action-list is-compact">
          <article><span>Lectura docente</span><strong>Revisar estudiantes con dudas repetidas o baja claridad.</strong></article>
          <article><span>Accion</span><strong>Enviar comentario breve con fortaleza, error frecuente y siguiente practica.</strong></article>
          <article><span>Evidencia</span><strong>Se apoya en conversaciones, feedback y continuidad de uso.</strong></article>
        </div>
      </article>
    </div>
  );
}

function AdaptationMetricsPanel({ metrics }) {
  const students = asList(metrics?.academic?.students);
  const levels = asList(metrics?.academic?.level_distribution);
  const totalStudents = students.length || levels.reduce((sum, item) => sum + Number(item.total || 0), 0);
  const dominant = [...levels].sort((a, b) => Number(b.total || 0) - Number(a.total || 0))[0] || { level: "Sin datos", total: 0 };
  const supportCount = students.filter((student) => Number(student.engagement_score || 0) < 35).length;
  const avgProgress = students.length
    ? Math.round(students.reduce((sum, student) => sum + Number(student.engagement_score || 0), 0) / students.length)
    : 0;
  const actionsCount = Number(metrics?.academic?.recommendations?.recent?.length || 0);
  const maxLevel = Math.max(1, ...levels.map((item) => Number(item.total || 0)));
  const actionCards = [
    { title: "Refuerzo en POO basico", text: "Fortalece conceptos base con ejemplos guiados.", priority: "Alta" },
    { title: "Ejercicios de practica", text: "Usa actividades cortas segun el nivel detectado.", priority: "Media" },
    { title: "Retroalimentacion personalizada", text: "Cierra brechas con comentario individual.", priority: "Media" },
    { title: "Recurso por tema debil", text: "Asigna lectura o guia al tema menos cubierto.", priority: "Media" },
  ];
  return (
    <div className="metrics-adaptation-board">
      <article className="metrics-panel metrics-adaptation-hero">
        <div>
          <h3>Adaptacion personalizada</h3>
          <p>Resumen general del nivel, ritmo de aprendizaje y proximas acciones sugeridas para el grupo.</p>
        </div>
        <Icon name="gauge" />
      </article>

      <div className="metrics-adaptation-kpis">
        <article><span>Nivel predominante</span><strong>{dominant.level}</strong><small>{totalStudents ? Math.round((Number(dominant.total || 0) / totalStudents) * 100) : 0}% del grupo</small></article>
        <article><span>Estudiantes en riesgo</span><strong>{supportCount}</strong><small>{totalStudents ? Math.round((supportCount / totalStudents) * 100) : 0}% del grupo</small></article>
        <article><span>Progreso promedio</span><strong>{avgProgress}%</strong><small>Avance visible del grupo</small></article>
        <article><span>Acciones recomendadas</span><strong>{actionsCount || actionCards.length}</strong><small>Personalizadas esta semana</small></article>
      </div>

      <div className="metrics-adaptation-main">
        <article className="metrics-panel metrics-adaptation-distribution">
          <h3>Distribucion por nivel de adaptacion</h3>
          <p className="metrics-panel-copy">Clasificacion de estudiantes segun desempeno actual.</p>
          <div className="metrics-adaptation-donut">
            <strong>{totalStudents}</strong>
            <span>estudiantes</span>
          </div>
          <div className="metrics-adaptation-levels">
            {levels.length ? levels.map((item) => {
              const value = Number(item.total || 0);
              const percent = totalStudents ? Math.round((value / totalStudents) * 100) : 0;
              return (
                <div key={item.level}>
                  <span>{item.level}</span>
                  <i><b style={{ width: `${Math.max(8, (value / maxLevel) * 100)}%` }} /></i>
                  <strong>{value} - {percent}%</strong>
                </div>
              );
            }) : <EmptyState>No hay niveles registrados.</EmptyState>}
          </div>
        </article>

        <article className="metrics-panel metrics-adaptation-focus">
          <h3>Proximo enfoque sugerido</h3>
          <p className="metrics-panel-copy">Basado en necesidades detectadas y progreso del grupo.</p>
          <div className="metrics-adaptation-focus-card">
            <strong>Refuerzo en POO basico</strong>
            <span>Se recomienda reforzar conceptos de POO, metodos y clases.</span>
            <dl>
              <dt>Prioridad</dt><dd>Media</dd>
              <dt>Area principal</dt><dd>POO, metodos y clases</dd>
              <dt>Objetivo</dt><dd>Fortalecer comprension y practica</dd>
              <dt>Siguiente accion</dt><dd>Ejercicios guiados y retroalimentacion</dd>
            </dl>
          </div>
        </article>
      </div>

      <div className="metrics-adaptation-main">
        <article className="metrics-panel">
          <h3>Estudiantes y necesidades de adaptacion</h3>
          <div className="metrics-adaptation-students">
            {students.slice(0, 6).map((student) => (
              <div key={student.usuario}>
                <strong>{displayStudentName(student.usuario)}</strong>
                <span>{student.nivel || "Inicial"}</span>
                <span>{Number(student.engagement_score || 0) < 35 ? "Alta" : "Media"}</span>
                <small>{student.tema_recomendado_preferido || "Refuerzo general"}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="metrics-panel">
          <h3>Acciones adaptativas recomendadas</h3>
          <div className="metrics-adaptation-actions">
            {actionCards.map((card) => (
              <article key={card.title}>
                <div>
                  <strong>{card.title}</strong>
                  <span>{card.text}</span>
                </div>
                <b>{card.priority}</b>
              </article>
            ))}
          </div>
        </article>
      </div>

      <article className="metrics-panel metrics-adaptation-route">
        <h3>Ruta adaptativa sugerida para el grupo</h3>
        <div>
          <span>1<br /><b>Refuerzo</b></span>
          <i />
          <span>2<br /><b>Practica</b></span>
          <i />
          <span>3<br /><b>Aplicacion</b></span>
          <i />
          <span>4<br /><b>Evaluacion</b></span>
        </div>
      </article>
    </div>
  );
}

function AvatarMetricsPanel() {
  return (
    <div className="metrics-avatar-grid">
      <article className="metrics-panel metrics-avatar-panel">
        <div className="metrics-avatar-orbit" aria-hidden="true">
          <span><Icon name="avatar" /></span>
        </div>
        <div>
          <h3>Ultimo: avatar 3D interactivo</h3>
          <p className="metrics-panel-copy">Representa visualmente a YELIA y acompana la explicacion cuando el estudiante recibe recursos, retroalimentacion y adaptacion.</p>
        </div>
      </article>
      <article className="metrics-panel">
        <h3>Lectura para el docente</h3>
        <div className="metrics-action-list">
          <article><span>Rol</span><strong>Apoyo visual del asistente virtual.</strong></article>
          <article><span>Uso</span><strong>Puede activarse despues de adaptar el contenido al nivel del estudiante.</strong></article>
          <article><span>Evidencia</span><strong>Se conecta con voz, expresiones y acompanamiento pedagogico.</strong></article>
        </div>
      </article>
    </div>
  );
}

function RouteMetricsPanel({ routeData }) {
  const items = asList(routeData?.items);
  const summary = routeData?.summary || {};
  const [selectedRouteUser, setSelectedRouteUser] = useState("");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [unitFilter, setUnitFilter] = useState("all");
  const filteredItems = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((item) => {
      const name = `${item.usuario || ""} ${item.display_name || ""}`.toLowerCase();
      const matchesQuery = !needle || name.includes(needle);
      const matchesStatus = statusFilter === "all"
        || (statusFilter === "completed" && item.route_completed)
        || (statusFilter === "active" && !item.route_completed && Number(item.progress || 0) > 0)
        || (statusFilter === "pending" && Number(item.progress || 0) <= 0);
      const matchesUnit = unitFilter === "all" || Number(item.current_unit || 1) === Number(unitFilter);
      return matchesQuery && matchesStatus && matchesUnit;
    });
  }, [items, query, statusFilter, unitFilter]);
  const selectedRoute = useMemo(
    () => filteredItems.find((item) => item.usuario === selectedRouteUser) || filteredItems[0] || null,
    [filteredItems, selectedRouteUser]
  );
  useEffect(() => {
    if (!filteredItems.length) {
      setSelectedRouteUser("");
      return;
    }
    if (!filteredItems.some((item) => item.usuario === selectedRouteUser)) {
      setSelectedRouteUser(filteredItems[0].usuario);
    }
  }, [filteredItems, selectedRouteUser]);

  return (
    <div className="metrics-route-dashboard">
      <article className="metrics-panel metrics-route-summary">
        <h3>Ruta por unidades</h3>
        <p className="metrics-panel-copy">Seguimiento de Unidad 1 a Unidad 4 y evaluacion final.</p>
        <div className="metrics-kpi-grid is-compact">
          <Kpi label="Estudiantes con ruta" value={summary.students || 0} note="Usaron /ruta" />
          <Kpi label="Promedio" value={`${summary.avg_progress || 0}%`} note="Avance modular" />
          <Kpi label="En progreso" value={summary.active || 0} note="Aun no cierran" />
          <Kpi label="Completadas" value={summary.completed || 0} note="Evaluacion final aprobada" />
        </div>
      </article>
      <article className="metrics-panel metrics-route-browser">
        <div className="metrics-route-toolbar">
          <div>
            <h3>Buscar estudiante</h3>
            <p className="metrics-panel-copy">Filtra por nombre, estado de ruta o unidad actual.</p>
          </div>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar estudiante..." />
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">Todos</option>
            <option value="active">En progreso</option>
            <option value="completed">Completados</option>
            <option value="pending">Sin avance</option>
          </select>
          <select value={unitFilter} onChange={(event) => setUnitFilter(event.target.value)}>
            <option value="all">Todas las unidades</option>
            <option value="1">Unidad 1</option>
            <option value="2">Unidad 2</option>
            <option value="3">Unidad 3</option>
            <option value="4">Unidad 4</option>
          </select>
        </div>
        <div className="metrics-route-rail" aria-label="Estudiantes filtrados">
          {filteredItems.length ? filteredItems.map((item) => (
            <button
              className={selectedRoute?.usuario === item.usuario ? "is-active" : ""}
              key={item.usuario}
              type="button"
              onClick={() => setSelectedRouteUser(item.usuario)}
            >
              <strong>{displayStudentName(item.display_name || item.usuario)}</strong>
              <span>Unidad {item.current_unit || 1} - {item.progress || 0}%</span>
              <div className="metrics-route-units">
                {asList(item.units).map((unit) => <i className={`is-${unit.status || "locked"}`} key={unit.id}>U{unit.id}</i>)}
              </div>
            </button>
          )) : <EmptyState>No hay estudiantes con esos filtros.</EmptyState>}
        </div>
        <div className="metrics-route-detail">
          <h3>Detalle del estudiante</h3>
          {selectedRoute ? (
            <div className="metrics-route-detail-card">
              <div className="metrics-route-detail-head">
                <div>
                  <strong>{displayStudentName(selectedRoute.usuario)}</strong>
                  <span>Unidad actual {selectedRoute.current_unit || 1} - {selectedRoute.done_units || 0}/4 completadas</span>
                </div>
                <b>{selectedRoute.progress || 0}%</b>
              </div>
              <div className="metrics-route-progress"><i style={{ width: `${Math.max(0, Math.min(100, Number(selectedRoute.progress || 0)))}%` }} /></div>
              <div className="metrics-route-unit-cards">
                {asList(selectedRoute.units).map((unit) => (
                  <article key={unit.id} className={`is-${unit.status || "locked"}`}>
                    <span>Unidad {unit.id}</span>
                    <strong>{unit.status === "done" ? "Completada" : unit.status === "active" ? "En curso" : "Bloqueada"}</strong>
                    <small>{unit.quiz_percent != null ? `Quiz ${unit.quiz_percent}%` : "Quiz pendiente"}</small>
                  </article>
                ))}
              </div>
              <div className="metrics-route-final">
                <span>Evaluacion final</span>
                <strong>{selectedRoute.final_percent != null ? `${selectedRoute.final_percent}%` : "Pendiente"}</strong>
                <small>{selectedRoute.route_completed ? "Ruta completada" : "Aun no cierra la ruta"}</small>
              </div>
            </div>
          ) : <EmptyState>Selecciona un estudiante para ver el desglose.</EmptyState>}
        </div>
      </article>
    </div>
  );
}

function RecommendationsPanel({ recommendations }) {
  const recent = asList(recommendations?.recent);
  return (
    <div className="metrics-recommendations-grid">
      <article className="metrics-panel">
        <h3>Tipos mas recomendados</h3>
        <MiniBars items={recommendations?.by_type} labelKey="type" />
      </article>
      <article className="metrics-panel">
        <h3>Temas que mas pide el sistema</h3>
        <MiniBars items={recommendations?.by_topic} labelKey="topic" />
      </article>
      <article className="metrics-panel metrics-recent-list">
        <h3>Ultimas recomendaciones generadas</h3>
        {recent.length ? recent.map((item) => (
          <div className="metrics-recent-item" key={item.id}>
            <strong>{item.title || item.topic || "Recomendacion"}</strong>
            <span>{displayStudentName(item.usuario || "Sin usuario")} - {item.level_used || "Sin nivel"} - {item.emotion_used || "neutral"}</span>
          </div>
        )) : <EmptyState>No hay recomendaciones registradas.</EmptyState>}
      </article>
    </div>
  );
}

export default function MetricsApp({ mode }) {
  const isTeacherView = mode === "teacher";
  const isGeneralView = mode === "general";
  const backHref = isTeacherView ? "/teacher" : isGeneralView ? "/demo" : "/admin";
  const visibleNavItems = isTeacherView ? teacherNavItems : isGeneralView ? navItems : adminNavItems;
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState("loading");
  const [error, setError] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");
  const [activeSection, setActiveSection] = useState("resumen");

  useLayoutEffect(() => {
    document.body.classList.add("metrics-page");
    try {
      const currentUrl = new URL(window.location.href);
      setToken(currentUrl.searchParams.get("token") || "");
      const hashSection = currentUrl.hash.replace("#", "");
      if (visibleNavItems.some(([id]) => id === hashSection)) {
        setActiveSection(hashSection);
      }
    } catch {
      setToken("");
    }
    const onHashChange = () => {
      const nextSection = window.location.hash.replace("#", "");
      if (visibleNavItems.some(([id]) => id === nextSection)) {
        setActiveSection(nextSection);
      }
    };
    window.addEventListener("hashchange", onHashChange);
    return () => {
      window.removeEventListener("hashchange", onHashChange);
      document.body.classList.remove("metrics-page");
    };
  }, [visibleNavItems]);

  function showSection(sectionId) {
    setActiveSection(sectionId);
    try {
      window.history.replaceState(null, "", `#${sectionId}`);
    } catch {
      // El panel funciona igual aunque el navegador bloquee history.
    }
  }

  async function loadMetrics() {
    setLoading(true);
    setError("");
    setHealth("loading");
    try {
      const headers = { Accept: "application/json" };
      if (token.trim()) headers["X-Admin-Token"] = token.trim();

      const urls = [new URL("/api/metrics", window.location.origin)];
      urls.forEach((url) => {
        if (token.trim()) url.searchParams.set("token", token.trim());
      });

      let res = null;
      let lastError = null;
      for (const url of urls) {
        try {
          res = await fetch(url.toString(), { method: "GET", cache: "no-store", headers });
          if (res.ok) break;
          lastError = new Error(`HTTP ${res.status}`);
        } catch (err) {
          lastError = err;
          res = null;
        }
      }

      if (!res || !res.ok) throw lastError || new Error("No response");
      const raw = await res.json();
      const next = raw?.data?.metrics || raw?.metrics || null;
      if (!next) throw new Error("Respuesta sin metricas");
      setMetrics(next);
      api.get("/api/teacher/learning-routes?limit=120").then(setRouteData).catch(() => setRouteData(null));
      setHealth("ok");
      setSelectedUser((current) => current);
    } catch (_) {
      setHealth("error");
      setError("No se pudieron cargar las metricas locales. Revisa que Python pueda leer yelia.db y pulsa Actualizar.");
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMetrics();
  }, []);

  useEffect(() => {
    if (!visibleNavItems.some(([id]) => id === activeSection)) {
      setActiveSection("resumen");
      try {
        window.history.replaceState(null, "", "#resumen");
      } catch {
        // La vista se corrige aunque el navegador no permita cambiar el hash.
      }
    }
  }, [activeSection, visibleNavItems]);

  const students = useMemo(() => asList(metrics?.academic?.students), [metrics]);
  const selectedStudent = useMemo(
    () => students.find((student) => student.usuario === selectedUser) || students[0] || null,
    [students, selectedUser]
  );

  const topTemas = useMemo(() => asList(metrics?.top_temas), [metrics]);
  const recommendations = metrics?.academic?.recommendations || {};
  const heatmap = metrics?.academic?.heatmap || {};
  const sidebarClass = collapsed ? "metrics-sidebar is-collapsed" : "metrics-sidebar";
  const activeLabel = visibleNavItems.find(([id]) => id === activeSection)?.[1] || "Resumen";

  return (
    <div className={`metrics-app ${collapsed ? "is-collapsed" : ""}`}>
      <aside className={sidebarClass}>
        <div className="metrics-brand">
          <button className="metrics-icon-button" type="button" onClick={() => setCollapsed((value) => !value)} title="Plegar menu"><Icon name="menu" /></button>
          <span className="metrics-logo-mark"><Icon name="logo" /></span>
          <div>
            <strong>YELIA4AP</strong>
            <span>Metricas</span>
          </div>
        </div>
        <nav className="metrics-nav" aria-label="Secciones de metricas">
          {visibleNavItems.map(([id, label, icon]) => (
            <button
              className={activeSection === id ? "is-active" : ""}
              type="button"
              key={id}
              aria-label={label}
              onClick={() => showSection(id)}
            >
              <span><Icon name={icon} /></span>
              <strong>{label}</strong>
            </button>
          ))}
        </nav>
        <div className="metrics-sidebar-footer">
          <span>Estado</span>
          <strong className={health === "ok" ? "is-ok" : health === "error" ? "is-error" : ""}>{health === "ok" ? "OK" : health === "error" ? "Error" : "Cargando"}</strong>
        </div>
      </aside>

      <div className="metrics-content">
        <header className="metrics-topbar">
          <div>
            <h1>{isTeacherView ? "Metricas docentes" : isGeneralView ? "Panel de metricas" : "Metricas admin"}</h1>
            <p>{isTeacherView
              ? `${activeLabel}: evidencia pedagogica de estudiantes, temas, ruta, recomendaciones y rendimiento.`
              : isGeneralView
                ? `${activeLabel}: seguimiento real de estudiantes, temas, progreso, recomendaciones y rendimiento.`
              : `${activeLabel}: auditoria general de uso, cuentas, chats, recursos y salud operativa.`}</p>
          </div>
          <div className="metrics-controls">
            {!isTeacherView && !isGeneralView ? (
              <input
                className="metrics-input"
                placeholder="Token de administrador"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") loadMetrics(); }}
              />
            ) : null}
            <button className="metrics-button is-primary" type="button" onClick={loadMetrics} disabled={loading}>{loading ? "Cargando..." : "Actualizar"}</button>
            <a className="metrics-button" href={backHref}>{isTeacherView ? "Docente" : isGeneralView ? "Portal" : "Admin"}</a>
          </div>
        </header>

        <main className="metrics-main">
          {error ? <div className="metrics-error" role="alert">{error}</div> : null}

          {activeSection === "resumen" ? <section className="metrics-section">
            <SectionHeader id="resumen" kicker="/api/metrics" title="Resumen visible" meta={metrics?.generated_at ? `Generado ${metrics.generated_at}` : "Esperando datos"} />
            <div className="metrics-kpi-grid">
              {kpisTeacherMain.map(([key, label, note, digits, suffix]) => (
                <Kpi key={key} label={label} note={note} value={metricValue(metrics, key, digits, suffix)} />
              ))}
            </div>
            <div className="metrics-kpi-grid">
              {kpisLearning.map(([key, label, note, digits, suffix]) => (
                <Kpi key={key} label={label} note={note} value={metricValue(metrics, key, digits, suffix)} />
              ))}
            </div>
          </section> : null}

          {activeSection === "estudiantes" ? <section className="metrics-section metrics-grid">
            <article className="metrics-panel metrics-wide">
              <SectionHeader id="estudiantes" kicker="seguimiento" title="Estudiantes, avance y necesidades" meta={`${students.length} registros`} />
              <StudentTable students={students} selectedUser={selectedStudent?.usuario} onSelect={setSelectedUser} />
            </article>
            <article className="metrics-panel">
              <SectionHeader id="temas" kicker="detalle" title="Lectura docente del estudiante" />
              <StudentInsight student={selectedStudent} />
            </article>
          </section> : null}

          {activeSection === "calor" ? <section className="metrics-section metrics-panel">
            <SectionHeader id="calor" kicker="estudiante x tema" title="Mapa de calor por estudiante" meta="Actividad por tema" />
            <Heatmap heatmap={heatmap} selectedUser={selectedUser} />
          </section> : null}

          {activeSection === "temas" ? <section className="metrics-section">
            <SectionHeader id="temas" kicker="busquedas" title="Temas buscados por estudiantes" meta={selectedTopic ? `Tema activo: ${selectedTopic}` : "Primero filtra por estudiante"} />
            <TopicExplorer
              students={students}
              topics={topTemas}
              selectedUser={selectedStudent?.usuario || ""}
              selectedTopic={selectedTopic}
              onSelectUser={setSelectedUser}
              onSelectTopic={setSelectedTopic}
            />
          </section> : null}

          {activeSection === "recursos" ? <section className="metrics-section">
            <SectionHeader id="recursos" kicker="primero" title="Recomendacion de recursos" />
            <ResourceMetricsPanel recommendations={recommendations} onTopic={(topic) => { setSelectedTopic(topic); showSection("temas"); }} />
          </section> : null}

          {activeSection === "feedback" ? <section className="metrics-section">
            <SectionHeader id="feedback" kicker="segundo" title="Retroalimentacion personalizada" />
            <FeedbackMetricsPanel metrics={metrics} />
          </section> : null}

          {activeSection === "adaptacion" ? <section className="metrics-section">
            <SectionHeader id="adaptacion" kicker="tercero" title="Personalizacion adaptativa" />
            <AdaptationMetricsPanel metrics={metrics} />
          </section> : null}

          {activeSection === "avatar" ? <section className="metrics-section">
            <SectionHeader id="avatar" kicker="ultimo" title="Avatar 3D interactivo" />
            <AvatarMetricsPanel />
          </section> : null}

          {activeSection === "ruta" ? <section className="metrics-section">
            <SectionHeader id="ruta" kicker="fase 2" title="Ruta academica por unidades" />
            <RouteMetricsPanel routeData={routeData} />
          </section> : null}

          {activeSection === "tecnico" ? <section className="metrics-section">
            <article className="metrics-panel">
              <SectionHeader id="tecnico" kicker="operacion" title="Rendimiento y uso" />
              <div className="metrics-kpi-grid is-compact">
                {kpisTechnical.map(([key, label, note, digits, suffix]) => (
                  <Kpi key={key} label={label} note={note} value={metricValue(metrics, key, digits, suffix)} />
                ))}
              </div>
              <div className="metrics-two-cols">
                <div>
                  <h3>Top temas consultados</h3>
                  <MiniBars items={topTemas} labelKey="tema" />
                </div>
                <div>
                  <h3>Niveles detectados</h3>
                  <MiniBars items={metrics?.academic?.level_distribution} labelKey="level" />
                </div>
              </div>
            </article>
          </section> : null}
        </main>
      </div>
    </div>
  );
}
