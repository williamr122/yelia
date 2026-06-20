'use client';

import React, { useLayoutEffect, useState } from "react";
import { getSafeNext, postJson } from "./http.js";

const roleConfig = {
  admin: {
    title: "Login Administrador",
    subtitle: <>Acceso para <b>Administrador</b></>,
    icon: "bi-shield-lock",
    badgeIcon: "bi-key",
    badgeText: "ADMIN",
    endpoint: "/api/admin/auth/login",
    fallback: "/admin",
    note: <>Dev tip: si está habilitado, puedes usar <code>?token=ADMIN_TOKEN</code> para entrar sin cuenta.</>,
    placeholder: "Ej: admin"
  },
  teacher: {
    title: "Login Docente",
    subtitle: <>Acceso para <b>Docente</b></>,
    icon: "bi-mortarboard",
    badgeIcon: "bi-journal-check",
    badgeText: "DOCENTE",
    endpoint: "/api/teacher/auth/login",
    fallback: "/teacher",
    note: <>Nota: este acceso es independiente del panel admin (sesión separada).</>,
    placeholder: "Ej: docente1"
  }
};

const USER_RE = /^[A-Za-z0-9._-]{4,32}$/;

function cleanUser(value) {
  return String(value || "").replace(/[^A-Za-z0-9._-]/g, "").slice(0, 32);
}

function validPassword(value, min = 8) {
  const text = String(value || "");
  return text.length >= min && text.length <= 128 && text.trim() === text;
}

function AdminMissingWarning({ show }) {
  if (!show) return null;
  return (
    <div className="alert alert-warning yelia-admin-warning">
      <div className="fw-semibold mb-1"><i className="bi bi-exclamation-triangle me-1" /> Aún no existe un administrador</div>
      <div className="small">Primero crea el usuario admin inicial en el asistente de configuración.</div>
      <div className="mt-3">
        <a className="btn btn-outline-light btn-sm" href="/admin/setup">
          <i className="bi bi-magic me-1" /> Ir a /admin/setup
        </a>
      </div>
    </div>
  );
}

async function getJson(url) {
  const response = await fetch(url, { credentials: "include", cache: "no-store", headers: { Accept: "application/json" } });
  const raw = await response.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === "object" ? raw.data : raw;
  return { ok: response.ok && raw?.ok !== false && raw?.success !== false, data };
}

export function AuthLoginApp({ role = "admin" }) {
  const cfg = roleConfig[role] || roleConfig.admin;
  const [flags, setFlags] = useState({});
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [requestOpen, setRequestOpen] = useState(false);
  const [teacherRequest, setTeacherRequest] = useState({ username: "", email: "", password: "", reason: "" });

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = role === "teacher" ? "teacher-login" : "admin-login";
    setFlags(window.__YELIA_PAGE__ || {});
    if (role === "admin") {
      getJson("/api/admin/setup/status")
        .then((result) => {
          if (result.ok) setFlags((current) => ({ ...current, ...result.data }));
        })
        .catch(() => {});
    }
    return () => {
      document.body.className = previous;
    };
  }, [role]);

  async function submit() {
    setError("");
    setInfo("");
    const user = cleanUser(username);
    if (!USER_RE.test(user) || !validPassword(password, 8)) {
      setError("Escribe usuario y contraseña.");
      return;
    }

    setLoading(true);
    try {
      const result = await postJson(cfg.endpoint, { username: user, password });
      if (!result.ok) {
        setError(result.message || "No se pudo iniciar sesión.");
        return;
      }
      window.location.href = getSafeNext() || cfg.fallback;
    } catch (_) {
      setError("Error de red. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  }

  async function requestTeacherAccount() {
    setError("");
    setInfo("");
    const payload = {
      username: cleanUser(teacherRequest.username),
      email: teacherRequest.email.trim(),
      password: teacherRequest.password,
      reason: teacherRequest.reason.trim(),
    };
    if (!USER_RE.test(payload.username) || !validPassword(payload.password, 8)) {
      setError("Para solicitar cuenta escribe usuario y contraseña.");
      return;
    }
    setLoading(true);
    try {
      const result = await postJson("/api/teacher/request-account", payload);
      if (!result.ok) {
        setError(result.message || "No se pudo enviar la solicitud.");
        return;
      }
      setInfo(result.message || "Solicitud enviada.");
      setRequestOpen(false);
      setTeacherRequest({ username: "", email: "", password: "", reason: "" });
    } catch (_) {
      setError("Error de red enviando la solicitud.");
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(event) {
    if (event.key === "Enter") submit();
  }

  return (
    <div className="container yelia-container-narrow">
      <div className="text-center mb-4">
        <div className="fs-3 fw-bold brand">YELIA4AP</div>
        <div className="muted">{cfg.subtitle}</div>
      </div>

      <div className="card glass rounded-4">
        <div className="card-body p-4">
          <div className="d-flex align-items-center justify-content-between mb-3">
            <div className="d-flex align-items-center gap-2">
              <i className={`bi ${cfg.icon} fs-4`} />
              <div className="fw-semibold">Iniciar sesión</div>
            </div>
            <span className="badgeRole"><i className={`bi ${cfg.badgeIcon}`} /> {cfg.badgeText}</span>
          </div>

          {error ? <div className="alert alert-danger">{error}</div> : null}
          {info ? <div className="alert alert-success">{info}</div> : null}
          {role === "admin" ? <AdminMissingWarning show={Boolean(flags.noAdmin)} /> : null}

          <label className="form-label" htmlFor="username">Usuario</label>
          <input
            className="form-control mb-3"
            id="username"
            placeholder={cfg.placeholder}
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(cleanUser(e.target.value))}
            onKeyDown={onKeyDown}
            maxLength={32}
            pattern="[A-Za-z0-9._-]{4,32}"
          />

          <label className="form-label" htmlFor="password">Contraseña</label>
          <input
            className="form-control mb-3"
            id="password"
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={onKeyDown}
          />

          <button className="btn btn-primary w-100" type="button" onClick={submit} disabled={loading}>
            {loading ? <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" /> : <i className="bi bi-box-arrow-in-right me-1" />}
            {loading ? "Entrando..." : "Entrar"}
          </button>

          <hr className="border-secondary my-4" />
          {role === "teacher" && (
            <div className="teacher-request-box">
              <button className="btn btn-outline-light w-100" type="button" onClick={() => setRequestOpen((value) => !value)}>
                <i className="bi bi-person-plus me-1" />
                {requestOpen ? "Ocultar solicitud" : "Solicitar cuenta docente"}
              </button>
              {requestOpen && (
                <div className="request-form mt-3">
                  <input className="form-control mb-2" placeholder="Usuario deseado" maxLength={32} value={teacherRequest.username} onChange={(e) => setTeacherRequest({ ...teacherRequest, username: cleanUser(e.target.value) })} />
                  <input className="form-control mb-2" placeholder="Email institucional (opcional)" value={teacherRequest.email} onChange={(e) => setTeacherRequest({ ...teacherRequest, email: e.target.value })} />
                  <input className="form-control mb-2" type="password" placeholder="Contrasena para tu cuenta (min. 8)" minLength="8" maxLength="128" value={teacherRequest.password} onChange={(e) => setTeacherRequest({ ...teacherRequest, password: e.target.value })} />
                  <textarea className="form-control mb-2" rows="2" placeholder="Motivo o materia asignada" value={teacherRequest.reason} onChange={(e) => setTeacherRequest({ ...teacherRequest, reason: e.target.value })} />
                  <button className="btn btn-primary w-100" type="button" onClick={requestTeacherAccount} disabled={loading}>
                    Enviar solicitud
                  </button>
                </div>
              )}
            </div>
          )}
          {role === "admin" && (
            <a className="btn btn-outline-light w-100" href="/admin/setup">
              <i className="bi bi-magic me-1" /> Crear primer admin si no existe
            </a>
          )}
          <hr className="border-secondary my-4" />
          <div className="muted small">{cfg.note}</div>
        </div>
      </div>

      <div className="text-center mt-3 muted small">
        <a href="/demo" className="link-light text-decoration-none"><i className="bi bi-arrow-left" /> Volver al portal</a>
      </div>
    </div>
  );
}
