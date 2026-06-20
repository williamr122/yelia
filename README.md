# Readme

Documento descriptivo del módulo.

<!-- 

# YELIA — Prototipo de Asistente Educativo (Flask + Web)

## 🚀 Ejecución rápida (Demo)

Pensado para sustentación (local o hosting).

### 1) Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2) Configurar variables (opcional)
Crea un archivo `.env` (o variables en el hosting):
```
ENV=demo
DEBUG=0
MAX_HISTORY=10
MAX_MESSAGE_LENGTH=800
LOG_LEVEL=INFO
```

### 3) Ejecutar
```bash
python app.py
```

Abrir:
- Interfaz: `http://localhost:5000/`
- Swagger: `http://localhost:5000/swagger/`
- Health: `http://localhost:5000/api/health`

> **Propósito**  
> Este repositorio contiene la guía operativa del prototipo **YELIA**: requisitos, configuración del entorno, ejecución en Windows y guías de despliegue/arquitectura.  
> **Nota académica:** esta guía está diseñada para ser **defendible ante jurado**: explica decisiones técnicas sin sobrecomentar ni alterar la lógica del sistema.

---

## 1) Descripción general

**YELIA** es un **prototipo académico de asistente educativo** con arquitectura **cliente–servidor**:

- **Backend:** API + servidor web con **Python + Flask**
- **Frontend:** interfaz **HTML/CSS/JS** (chat, avatar, voz y métricas)
- **Objetivo:** validar integración conversacional, seguimiento de progreso y visualización de métricas en un entorno web.

> Alcance del prototipo: demostrar el flujo extremo a extremo (UI ⇄ API ⇄ proveedor NLP) con énfasis en trazabilidad y mantenibilidad.

---

## 2) Requisitos

### Software recomendado
- **Python 3.x** (según `runtime.txt`)
- **pip** (gestor de paquetes)
- **Git** (opcional, recomendado)

### Dependencias del proyecto
- Se instalan desde `requirements.txt`.

---

## 3) Configuración rápida (Windows)

### Opción A — Recomendado (un solo script)
1. Doble clic en: `YELIA_START.bat`
2. El script realiza:
   - creación/activación de entorno virtual
   - instalación de dependencias
   - ejecución del servidor

### Opción B — Instalación y ejecución por separado
1. Instalar dependencias:
   - `install.bat`
2. Ejecutar:
   - `run.bat` (modo estándar)
   - `run_fast.bat` (modo rápido)

> Estos scripts son **utilitarios**: no cambian la lógica del sistema, solo automatizan pasos repetitivos de entorno.

---

## 4) Variables de entorno

- Revisa y copia `.env.example` → `.env` (si tu flujo lo requiere).
- Mantén credenciales fuera del repositorio (ver `.gitignore`).

---

## 5) Estructura del proyecto

Componentes principales:

- `app.py`: punto de entrada (Flask) y orquestación principal
- `backend/`: API, lógica de negocio, servicios, repositorios y módulos NLP
- `templates/`: vistas HTML del sistema
- `static/`: recursos del frontend (JS, CSS, avatar, voz, métricas)
- Scripts Windows:
  - `install.bat`: instalación inicial
  - `run.bat`: ejecución estándar
  - `run_fast.bat`: ejecución rápida
  - `YELIA_START.bat`: ejecución “todo en uno” (recomendado)

---


Dentro de `docs/` encontrarás:

- `STRUCTURE.md`: guía de estructura y convenciones
- `ARCHITECTURE.md`: arquitectura y flujo de alto nivel
- `RUN_WINDOWS.md`: ejecución detallada en Windows
- `TESTING.md`: guía de pruebas
- `DEPLOYMENT.md`: notas de despliegue

---


Este repositorio prioriza guía **profesional y mínima**:

- Explica responsabilidades, flujos y decisiones técnicas.
- Evita comentarios obvios (“incrementa i”, “crea variable”).
- Señala no-objetivos (lo que el prototipo *no* intenta resolver).
- Mantiene trazabilidad (qué módulo hace qué y por qué existe).

---

## 8) Solución de problemas (rápido)

- **`pip` no instala:** actualiza `pip` y verifica tu versión de Python.
- **Puerto ocupado:** detén el proceso previo o cambia el puerto (si tu configuración lo permite).
- **Permisos:** ejecuta la terminal con permisos adecuados cuando sea necesario.

---

### Licencia / uso académico
Uso orientado a fines académicos. Si este proyecto se reutiliza en producción, se recomienda añadir políticas de seguridad, hardening, monitoreo y manejo formal de secretos.
