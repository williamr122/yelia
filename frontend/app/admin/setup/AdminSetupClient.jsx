'use client';

import React, { useLayoutEffect, useState } from "react";
import { postJson } from "../../_shared/react/http.js";

const demoToken = "";
const USER_RE = /^[A-Za-z0-9._-]{4,32}$/;

function cleanUser(value) {
  return String(value || "").replace(/[^A-Za-z0-9._-]/g, "").slice(0, 32);
}

function KeyIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7.5 14a5.5 5.5 0 1 1 4.7 2.7L9.5 19H8v-1.5H6.5V16H5v-1.5l2.2-2.2A5.6 5.6 0 0 1 7.5 14Z" stroke="white" opacity=".85" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/><path d="M14.8 8.7h.01" stroke="white" strokeWidth="3" strokeLinecap="round"/></svg>;
}

function UserIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 21v-1a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v1" stroke="white" opacity=".85" strokeWidth="1.6" strokeLinecap="round"/><path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z" stroke="white" opacity=".9" strokeWidth="1.6" strokeLinecap="round"/></svg>;
}

function MailIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 4h16v16H4V4Z" stroke="white" opacity=".75" strokeWidth="1.6"/><path d="M4 7l8 6 8-6" stroke="white" opacity=".9" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/></svg>;
}

function LockIcon({ confirm = false }) {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M7 11V8a5 5 0 0 1 10 0v3" stroke="white" opacity=".85" strokeWidth="1.6" strokeLinecap="round"/><path d="M6 11h12v10H6V11Z" stroke="white" opacity=".9" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>{confirm ? <path d="M9 16h6" stroke="white" opacity=".85" strokeWidth="1.6" strokeLinecap="round"/> : null}</svg>;
}

function StarIcon() {
  return <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 2l1.4 6.1L20 10l-6.6 1.9L12 18l-1.4-6.1L4 10l6.6-1.9L12 2Z" stroke="#111" strokeWidth="1.6" strokeLinejoin="round"/></svg>;
}

function Tip({ children, type = "check" }) {
  const paths = {
    check: "M20 6 9 17l-5-5",
    plus: "M8 12h8M12 8v8",
    clock: "M12 6v6l4 2",
  };
  return (
    <div className="tip">
      <div className="ic" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d={paths[type] || paths.check} stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg></div>
      <p>{children}</p>
    </div>
  );
}

function Field({ label, icon, children, hint }) {
  return <div className="field"><label>{icon}{label}</label>{children}{hint ? <div className="hint">{hint}</div> : null}</div>;
}

async function getJson(url) {
  const response = await fetch(url, { credentials: "include", cache: "no-store", headers: { Accept: "application/json" } });
  const raw = await response.json().catch(() => ({}));
  const data = raw?.data && typeof raw.data === "object" ? raw.data : raw;
  return { ok: response.ok && raw?.ok !== false && raw?.success !== false, data };
}

export default function AdminSetupClient() {
  const [flags, setFlags] = useState({});
  const adminExists = Boolean(flags.adminExists);
  const setupEnabled = flags.setupEnabled !== false;

  const [form, setForm] = useState({ token: demoToken, username: "admin", email: "", password: "", confirm: "" });
  const [message, setMessage] = useState({ text: "", kind: "" });
  const [loading, setLoading] = useState(false);

  useLayoutEffect(() => {
    const previous = document.body.className;
    document.body.className = "admin-setup-page desktop-pro";
    setFlags(window.__YELIA_PAGE__ || {});
    getJson("/api/admin/setup/status")
      .then((result) => {
        if (result.ok) setFlags((current) => ({ ...current, ...result.data }));
      })
      .catch(() => {});
    return () => {
      document.body.className = previous;
    };
  }, []);

  function update(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function setMsg(text, kind = "") {
    setMessage({ text, kind });
  }

  async function submit(event) {
    event.preventDefault();
    setMsg("");

    const token = form.token.trim();
    const username = cleanUser(form.username);
    const email = form.email.trim();
    const password = form.password;
    const confirm = form.confirm;

    if (!token) return setMsg("Token requerido.", "err");
    if (!USER_RE.test(username)) return setMsg("El usuario debe tener 4 a 32 caracteres: letras, numeros, punto, guion o guion bajo.", "err");
    if (!password || password.length < 8) return setMsg("La contrasena debe tener minimo 8 caracteres.", "err");
    if (password !== confirm) return setMsg("Las contrasenas no coinciden.", "err");

    setLoading(true);
    try {
      const result = await postJson("/api/admin/setup", { token, username, email, password });
      if (!result.ok) {
        setMsg(result.message || "No se pudo crear el admin.", "err");
        return;
      }
      setMsg("Administrador creado. Redirigiendo...", "ok");
      const to = String(result.data?.redirect || "/admin/login");
      window.setTimeout(() => { window.location.href = to; }, 700);
    } catch (_) {
      setMsg("Error de red. Reintenta.", "err");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page setup-onboarding">
      <section className="setup-shell">
        <header className="setup-hero">
          <div className="setup-brand" aria-label="YELIA4AP primer arranque">
            <span className="logo" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 2c5.5 0 10 4.5 10 10s-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2Z" stroke="white" opacity=".85" strokeWidth="1.6"/><path d="M7.2 13.1c1.7 3.4 7.9 3.4 9.6 0" stroke="white" opacity=".9" strokeWidth="1.6" strokeLinecap="round"/><path d="M9 9.6h.01M15 9.6h.01" stroke="white" strokeWidth="3" strokeLinecap="round"/></svg>
            </span>
            <span><b>YELIA4AP</b><small>Primer arranque del sistema</small></span>
          </div>
          <div className="setup-hero-actions">
            <a className="btn btn-secondary" href="/demo">Volver al portal</a>
            <a className="btn btn-secondary" href="/admin/login">Ir a login</a>
          </div>
        </header>

        <section className="setup-intro card">
          <div>
            <span className="setup-eyebrow">Configuracion inicial</span>
            <h1>Crear primer administrador</h1>
            <p>Habilita la cuenta principal para gestionar docentes, estudiantes, metricas y evidencia academica.</p>
          </div>
          <div className="setup-state">
            <span className={adminExists ? "danger" : "ok"}>{adminExists ? "Admin ya existe" : "Listo para crear"}</span>
            <small>Este proceso se usa una sola vez.</small>
          </div>
        </section>

        <section className="setup-layout">
          <article className="card setup-form-card">
            {adminExists ? <div className="notice yelia-setup-warning"><b>Ya existe un administrador.</b> Si has olvidado tus credenciales, puedes usar el SETUP_TOKEN para restablecer el administrador (se eliminará la cuenta anterior y se creará una nueva).</div> : null}
            {!setupEnabled ? <div className="notice yelia-setup-danger"><b>SETUP_TOKEN no esta configurado.</b> Define SETUP_TOKEN para habilitar la creacion del primer admin.</div> : null}

            <form className="form" autoComplete="off" noValidate onSubmit={submit}>
              <details className="setup-token-box" open>
                <summary><KeyIcon /> Codigo de configuracion</summary>
                <Field label="SETUP TOKEN" icon={<KeyIcon />} hint="Valida que esta pantalla solo cree el primer administrador autorizado.">
                  <input className="input" name="token" value={form.token} placeholder="Pega aqui el SETUP_TOKEN configurado en el servidor" required onChange={(e) => update("token", e.target.value)} />
                </Field>
              </details>

              <div className="setup-section-title">
                <h2>Datos de la cuenta</h2>
                <p>Estas credenciales se usaran luego desde el login de administrador.</p>
              </div>

              <div className="grid">
                <Field label="Usuario admin" icon={<UserIcon />}><input className="input" name="username" placeholder="admin" maxLength="32" pattern="[A-Za-z0-9._-]{4,32}" value={form.username} required onChange={(e) => update("username", cleanUser(e.target.value))} /></Field>
                <Field label="Email (opcional)" icon={<MailIcon />}><input className="input" name="email" placeholder="admin@yelia.local" value={form.email} onChange={(e) => update("email", e.target.value)} /></Field>
              </div>

              <div className="grid">
                <Field label="Contrasena" icon={<LockIcon />}><input className="input" name="password" type="password" placeholder="minimo 8 caracteres" minLength="8" required value={form.password} onChange={(e) => update("password", e.target.value)} /></Field>
                <Field label="Confirmar contrasena" icon={<LockIcon confirm />}><input className="input" name="confirm" type="password" placeholder="repite la contrasena" minLength="8" required value={form.confirm} onChange={(e) => update("confirm", e.target.value)} /></Field>
              </div>

              <div className="actions">
                <button className="btn btn-primary" type="submit" disabled={loading || !setupEnabled}><StarIcon />{loading ? "Procesando..." : adminExists ? "Restablecer y crear admin" : "Crear administrador"}</button>
                <a className="btn btn-secondary" href="/admin/login">Ya tengo admin</a>
              </div>

              <div className={`msg ${message.kind}`}>{message.text}</div>
            </form>
          </article>

          <aside className="card setup-side">
            <h2>Estado de configuracion</h2>
            <div className="setup-step-list">
              <Tip>Valida el token de configuracion inicial.</Tip>
              <Tip type="plus">Crea la cuenta principal del administrador.</Tip>
              <Tip type="clock">Luego entra al panel desde <code>/admin/login</code>.</Tip>
            </div>
            <div className="setup-note">
              <b>Recomendacion</b>
              <p>Para hosting, elimina o cambia el token despues de crear el primer administrador.</p>
            </div>
          </aside>
        </section>
      </section>
    </main>
  );
}
