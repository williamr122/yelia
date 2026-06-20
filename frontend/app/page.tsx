'use client';

import React from 'react';

function EntryPortal() {
  return (
    <div className="wrap yelia-student-home portal-wrapper">
      <header className="student-topbar">
        <a className="student-brand" href="/" aria-label="YELIA4AP inicio">
          <span className="student-logo"><i className="bi bi-cpu" /></span>
          <span><b>YELIA4AP</b><small>Plataforma Académica</small></span>
        </a>
        <div style={{ color: '#a9c3df', fontSize: '0.9rem', fontWeight: 650 }}>
          Universidad de Guayaquil
        </div>
      </header>

      <section className="portal-hero" style={{ marginTop: '40px', marginBottom: '40px', textAlign: 'center' }}>
        <h1 style={{ color: '#fff', fontSize: 'clamp(2rem, 4vw, 3.5rem)', fontWeight: 800, letterSpacing: '-0.03em', lineHeight: 1.1 }}>
          Bienvenido a <span style={{ background: 'linear-gradient(135deg, #59d2ff, #7c5cff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>YELIA4AP</span>
        </h1>
        <p style={{ color: '#c7d7ea', fontSize: '1.15rem', maxWidth: '700px', margin: '15px auto 0', lineHeight: 1.6 }}>
          Selecciona tu rol para acceder a la plataforma adaptativa de aprendizaje y seguimiento en Programación Avanzada.
        </p>
      </section>

      <section className="portal-roles-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginTop: '20px' }}>
        
        {/* CARD ESTUDIANTE */}
        <article className="student-login-card hero-login student-flow-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '30px', borderRadius: '24px', border: '1px solid rgba(89, 210, 255, 0.3)', background: 'linear-gradient(135deg, rgba(7, 28, 44, 0.85), rgba(5, 18, 31, 0.95))', transition: 'all 0.3s ease' }}>
          <div className="student-card-head" style={{ flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '15px' }}>
            <span className="student-logo" style={{ width: '60px', height: '60px', borderRadius: '20px', background: 'linear-gradient(135deg, rgba(89,210,255,0.25), rgba(124,92,255,0.25))', border: '1px solid rgba(89,210,255,0.4)', fontSize: '1.5rem' }}>
              <i className="bi bi-mortarboard-fill" />
            </span>
            <div>
              <h2 style={{ fontSize: '1.6rem', color: '#fff', fontWeight: 750 }}>Estudiante</h2>
              <p style={{ color: '#a9bad0', fontSize: '0.95rem', marginTop: '8px' }}>
                Resuelve diagnósticos, avanza por las unidades del sílabo, interactúa con el chat inteligente y revisa tu progreso.
              </p>
            </div>
          </div>
          <div style={{ flexGrow: 1, marginTop: '20px' }}>
            <div style={{ padding: '12px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)', color: '#bfdbfe', fontSize: '0.85rem', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Diagnóstico inicial de nivel</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Ruta con 4 unidades académicas</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Quizzes y reporte descargable</span>
            </div>
          </div>
          <div className="student-login-actions" style={{ marginTop: '25px', display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
            <a className="btn primary" href="/launcher" style={{ width: '100%', height: '48px', fontSize: '1rem' }}>
              Entrar como Estudiante
            </a>
          </div>
        </article>

        {/* CARD DOCENTE */}
        <article className="student-login-card hero-login student-flow-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '30px', borderRadius: '24px', border: '1px solid rgba(124, 92, 255, 0.3)', background: 'linear-gradient(135deg, rgba(7, 28, 44, 0.85), rgba(5, 18, 31, 0.95))', transition: 'all 0.3s ease' }}>
          <div className="student-card-head" style={{ flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '15px' }}>
            <span className="student-logo" style={{ width: '60px', height: '60px', borderRadius: '20px', background: 'linear-gradient(135deg, rgba(124,92,255,0.25), rgba(56,217,150,0.25))', border: '1px solid rgba(124,92,255,0.4)', fontSize: '1.5rem' }}>
              <i className="bi bi-person-workspace" />
            </span>
            <div>
              <h2 style={{ fontSize: '1.6rem', color: '#fff', fontWeight: 750 }}>Docente</h2>
              <p style={{ color: '#a9bad0', fontSize: '0.95rem', marginTop: '8px' }}>
                Monitorea el avance de los estudiantes, revisa estadísticas de chats y configura restricciones de evaluación.
              </p>
            </div>
          </div>
          <div style={{ flexGrow: 1, marginTop: '20px' }}>
            <div style={{ padding: '12px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)', color: '#bfdbfe', fontSize: '0.85rem', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Control de rutas de aprendizaje</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Síntesis docente de consultas</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Activar/desactivar descargas PDF</span>
            </div>
          </div>
          <div className="student-login-actions" style={{ marginTop: '25px', display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
            <a className="btn primary" href="/teacher/login" style={{ width: '100%', height: '48px', fontSize: '1rem', background: 'linear-gradient(135deg, rgba(124,92,255,0.22), rgba(124,92,255,0.10))', borderColor: 'rgba(124,92,255,0.45)' }}>
              Acceso Docente
            </a>
          </div>
        </article>

        {/* CARD ADMINISTRADOR */}
        <article className="student-login-card hero-login student-flow-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', padding: '30px', borderRadius: '24px', border: '1px solid rgba(56, 217, 150, 0.3)', background: 'linear-gradient(135deg, rgba(7, 28, 44, 0.85), rgba(5, 18, 31, 0.95))', transition: 'all 0.3s ease' }}>
          <div className="student-card-head" style={{ flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '15px' }}>
            <span className="student-logo" style={{ width: '60px', height: '60px', borderRadius: '20px', background: 'linear-gradient(135deg, rgba(56,217,150,0.25), rgba(89,210,255,0.25))', border: '1px solid rgba(56,217,150,0.4)', fontSize: '1.5rem' }}>
              <i className="bi bi-shield-lock-fill" />
            </span>
            <div>
              <h2 style={{ fontSize: '1.6rem', color: '#fff', fontWeight: 750 }}>Administrador</h2>
              <p style={{ color: '#a9bad0', fontSize: '0.95rem', marginTop: '8px' }}>
                Administra cuentas de usuario, audita registros del sistema y realiza copias de seguridad de la base de datos.
              </p>
            </div>
          </div>
          <div style={{ flexGrow: 1, marginTop: '20px' }}>
            <div style={{ padding: '12px', borderRadius: '14px', background: 'rgba(255,255,255,0.03)', color: '#bfdbfe', fontSize: '0.85rem', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Gestión total de usuarios y roles</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Bitácora de auditoría detallada</span>
              <span><i className="bi bi-check2-circle" style={{ color: '#2dd4bf', marginRight: '6px' }} /> Monitoreo e inspección de tablas</span>
            </div>
          </div>
          <div className="student-login-actions" style={{ marginTop: '25px', display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
            <a className="btn primary" href="/admin/login" style={{ width: '100%', height: '48px', fontSize: '1rem', background: 'linear-gradient(135deg, rgba(56,217,150,0.22), rgba(56,217,150,0.10))', borderColor: 'rgba(56,217,150,0.45)' }}>
              Acceso Administrador
            </a>
          </div>
        </article>

      </section>

      <footer className="student-footer" style={{ marginTop: '50px' }}>
        <span>YELIA4AP — Facultad de Ingeniería Industrial — Universidad de Guayaquil</span>
        <span>Asistente Adaptativo Inteligente de Programación</span>
      </footer>
    </div>
  );
}

export default function RootPage() {
  return (
    <>
      <link rel="icon" href="/static/favicon.ico" />
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet" />
      <link rel="stylesheet" href="/static/css/base/yelia-theme-tokens.css" />
      <link rel="stylesheet" href="/static/css/pages/launcher.css" />
      <script dangerouslySetInnerHTML={{ __html: "document.body.className='launcher ui desktop-pro';" }} />
      <EntryPortal />
    </>
  );
}
