from __future__ import annotations

import asyncio
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

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
