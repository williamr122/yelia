# ============================================================
# Procfile — Proyecto YELIA
#
# Este archivo define el proceso principal que debe ejecutar
# la plataforma de despliegue (PaaS) al iniciar la aplicación.
#
# PLATAFORMAS COMPATIBLES:
# - Heroku
# - Render (modo compatible)
# - Railway
# - Otros proveedores PaaS que soporten Procfile
#
# FUNCIÓN PRINCIPAL:
# - Indicar explícitamente cómo se debe levantar la aplicación
#   en un entorno de producción o pruebas controladas.
#
# DECISIÓN TÉCNICA:
# - Se utiliza Gunicorn como servidor WSGI:
#   * Estable y ampliamente adoptado
#   * Adecuado para producción
#   * Maneja múltiples workers/procesos
#
# ARQUITECTURA:
# - La aplicación Flask se inicia mediante el patrón
#   Application Factory.
# - Esto permite:
#   * Separar configuración de ejecución
#   * Facilitar testing
#   * Escalar correctamente en producción
#
# NOTA:
# - Este archivo no se utiliza en ejecución local directa
#   (ej: flask run), solo en despliegues PaaS.
# ============================================================

web: gunicorn "app:create_app()" --workers 1 --threads 1 --timeout 120 --bind 0.0.0.0:$PORT

