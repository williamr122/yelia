# Readme

Documento descriptivo del módulo.

<!-- 

# Backend YELIA


## Modo offline
El backend soporta un modo de continuidad cuando no hay conectividad o falla el proveedor LLM:
- Si el router de proveedores detecta error/timeout, se utiliza el proveedor local.
- El proveedor local responde con base en `temas.json` (conocimiento base) y reglas simples.

## Router de proveedores (Groq / DeepSeek / Gemini / Local)
La selección del proveedor se hace en el módulo `backend/nlp`:
- Se intenta el proveedor preferido/configurado por variables de entorno.
- En caso de fallo, se aplica fallback al siguiente proveedor disponible.
- En último caso, se usa el proveedor local (sin red) para no interrumpir el servicio.

Recomendación:
- Mantener métricas de “fallback_used” para cuantificar disponibilidad.
