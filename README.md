# Valinor

Dashboard para explorar variables económicas procedentes de Eurostat, Banco de España y el INE. El objetivo es comparar series en el tiempo, cruzarlas entre sí y ofrecer filtros por tipo de serie y frecuencia.

## Estado del proyecto
- **Versión**: 0.0.1
- **Nombre en clave**: "Hola mundo"
- **Servicios**: API FastAPI + Redis opcional para caché.

## Estructura
- `backend/`: API en FastAPI con un punto de exploración de fuentes.
- `config/version.yaml`: configuración de versión y nombre en clave.
- `infra/`: espacio reservado para artefactos de infraestructura adicionales.
- `scripts/`: utilidades de línea de comandos (por ejemplo, `probe_data_sources.py`).

## Ejecución con Docker Compose
1. Copia las variables de ejemplo: `cp .env.example .env`.
2. Arranca los servicios: `docker compose up --build`.
3. La API quedará disponible en `http://localhost:8000` con los endpoints:
   - `GET /health`
   - `GET /version`
   - `GET /sources/probe` para sondear fuentes y validar caché.

## Ejecución local de las pruebas de datos
Instala dependencias de backend y ejecuta el script de sondeo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/probe_data_sources.py
```

El script devuelve un resumen con el estado de Eurostat, Banco de España e INE, mostrando muestras de datos cuando están disponibles.

## Caché
- Por defecto se usa un caché en memoria con TTL.
- Define `CACHE_BACKEND=redis` y `CACHE_URL=redis://redis:6379/0` en `.env` para activar Redis a través de Docker Compose.

## Próximos pasos sugeridos
- Incorporar frontend del dashboard y vistas comparativas.
- Añadir persistencia de series seleccionadas y filtros de frecuencia.
- Automatizar la ingesta recurrente con workers y programaciones.
