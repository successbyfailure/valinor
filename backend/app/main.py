from __future__ import annotations

import asyncio
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
    return RedirectResponse(url="/docs")


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
        </style>
      </head>
      <body>
        <h1>Fuentes de datos: diagnóstico</h1>
        <p>Resumen rápido de los datos recibidos desde las APIs configuradas.</p>
        {''.join(secciones)}
      </body>
    </html>
    """

    return HTMLResponse(content=html)
