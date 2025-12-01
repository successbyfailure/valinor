from __future__ import annotations

import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from .cache import build_cache
from .config import get_settings, load_version_config
from .datasources import DataSourceProbe

settings = get_settings()
version_config = load_version_config(settings.version_file)
cache_backend = build_cache(settings.cache_backend, settings.cache_url)
probe = DataSourceProbe(cache_backend)

app = FastAPI(
    title="Valinor Dashboard API",
    version=version_config.version,
    description="API para el dashboard de variables económicas",
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "entorno": settings.env}


@app.get("/version")
async def version() -> dict[str, str]:
    return {"version": version_config.version, "codename": version_config.codename}


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/sources/probe")
async def sources_probe(limit: int = 5) -> dict:
    return await asyncio.to_thread(probe.probe_all, limit)


def _render_sample_items(items: list[dict] | list[str]) -> str:
    if not items:
        return "<li>Sin muestras disponibles</li>"

    rendered = []
    for item in items:
        if isinstance(item, dict):
            pairs = [f"<strong>{key}</strong>: {value}" for key, value in item.items()]
            rendered.append("<li>" + " | ".join(pairs) + "</li>")
        else:
            rendered.append(f"<li>{item}</li>")
    return "".join(rendered)


def _render_source_section(name: str, payload: dict) -> str:
    status = payload.get("status_code") or "Sin código"
    timestamp = payload.get("timestamp", "-")
    error = payload.get("error")
    count = payload.get("count")
    keys = payload.get("keys", [])
    sample = payload.get("sample", [])

    extra_rows = ""
    if count is not None:
        extra_rows += f"<tr><td>Total</td><td>{count}</td></tr>"
    if keys:
        extra_rows += "<tr><td>Claves</td><td><ul>" + _render_sample_items(keys) + "</ul></td></tr>"
    if sample:
        extra_rows += "<tr><td>Muestra</td><td><ul>" + _render_sample_items(sample) + "</ul></td></tr>"
    if error:
        extra_rows += f"<tr><td>Error</td><td>{error}</td></tr>"

    return f"""
    <section>
      <h2>{name}</h2>
      <table>
        <tr><td>Última actualización</td><td>{timestamp}</td></tr>
        <tr><td>Código de estado</td><td>{status}</td></tr>
        {extra_rows}
      </table>
    </section>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(limit: int = 5) -> HTMLResponse:
    resultados = await asyncio.to_thread(probe.probe_all, limit)

    serie_meta = resultados.get("ine_series", {})
    operaciones = serie_meta.get("operations", [])
    histograma_periodicidad = serie_meta.get("periodicity_histogram", {})

    operaciones_labels = [op.get("codigo") or f"Operación {op.get('id')}" for op in operaciones]
    operaciones_valores = [op.get("series_count", 0) for op in operaciones]
    histo_labels = list(histograma_periodicidad.keys())
    histo_valores = list(histograma_periodicidad.values())

    secciones = [
        _render_source_section("INE", resultados.get("ine", {})),
        _render_source_section("Eurostat", resultados.get("eurostat", {})),
        _render_source_section("Banco de España", resultados.get("banco_de_espana", {})),
    ]

    html = f"""
    <html lang=\"es\">
      <head>
        <meta charset=\"UTF-8\" />
        <title>Dashboard de fuentes</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 1.5rem; background: #f8fafc; }}
          h1 {{ color: #0f172a; }}
          section {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
          table {{ width: 100%; border-collapse: collapse; }}
          td {{ padding: 0.4rem 0.6rem; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
          ul {{ margin: 0; padding-left: 1.2rem; }}
          .chart-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
          .chart-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08); }}
          .chart-card h3 {{ margin-top: 0; color: #0f172a; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
      </head>
      <body>
        <h1>Fuentes de datos: diagnóstico</h1>
        <p>Resumen rápido de los datos recibidos desde las APIs configuradas.</p>
        <section>
          <h2>Gráficas rápidas (INE)</h2>
          <p>Datos de prueba construidos a partir de las operaciones disponibles en la API del INE.</p>
          <div class="chart-container">
            <div class="chart-card">
              <h3>Series por operación</h3>
              <canvas id="chartSeries"></canvas>
            </div>
            <div class="chart-card">
              <h3>Distribución por periodicidad</h3>
              <canvas id="chartPeriodicity"></canvas>
            </div>
          </div>
        </section>
        {''.join(secciones)}
        <script>
          const serieLabels = {json.dumps(operaciones_labels)};
          const serieValores = {json.dumps(operaciones_valores)};
          const periodicidadLabels = {json.dumps(histo_labels)};
          const periodicidadValores = {json.dumps(histo_valores)};

          if (serieLabels.length && serieValores.length) {{
            new Chart(document.getElementById('chartSeries'), {{
              type: 'bar',
              data: {{
                labels: serieLabels,
                datasets: [{{
                  label: 'Número de series',
                  data: serieValores,
                  backgroundColor: '#0ea5e9',
                  borderColor: '#0284c7',
                  borderWidth: 1,
                }}],
              }},
              options: {{
                plugins: {{ legend: {{ display: false }} }},
                scales: {{ y: {{ beginAtZero: true }} }},
              }},
            }});
          }}

          if (periodicidadLabels.length && periodicidadValores.length) {{
            new Chart(document.getElementById('chartPeriodicity'), {{
              type: 'doughnut',
              data: {{
                labels: periodicidadLabels,
                datasets: [{{
                  label: 'Series contabilizadas',
                  data: periodicidadValores,
                  backgroundColor: ['#22c55e', '#f59e0b', '#6366f1', '#06b6d4', '#ef4444'],
                }}],
              }},
              options: {{
                plugins: {{ legend: {{ position: 'bottom' }} }},
              }},
            }});
          }}
        </script>
      </body>
    </html>
    """

    return HTMLResponse(content=html)
