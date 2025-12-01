# API de Valinor

Servicio FastAPI para exponer el dashboard de variables económicas y los puntos de sondeo de datos.

## Configuración
- Archivo de versión: `config/version.yaml`.
- Variables de entorno clave:
  - `APP_ENV`: entorno de ejecución (por defecto `development`).
  - `CACHE_BACKEND`: `memory` o `redis`.
  - `CACHE_URL`: URL de redis si se usa caché externa.
  - `VERSION_FILE`: ruta al fichero de versión (por defecto `config/version.yaml`).

## Ejecución local
```bash
uvicorn app.main:app --reload --port 8000
```

## Puntos de entrada
- `GET /health`: estado básico.
- `GET /version`: devuelve versión y nombre en clave.
- `GET /sources/probe`: sondea Eurostat, Banco de España e INE y aplica la capa de caché configurada.
- `GET /dashboard`: panel HTML de diagnóstico con la información recibida desde cada fuente de datos.
