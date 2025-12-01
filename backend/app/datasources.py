from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

import requests

from .cache import CacheBackend

logger = logging.getLogger(__name__)

INE_OPERATIONS_URL = "https://servicios.ine.es/wstempus/js/ES/OPERACIONES_DISPONIBLES"
EUROSTAT_TOC_URL = "https://ec.europa.eu/eurostat/api/discover/toc"
BANCO_ESPANA_SERIES_URL = "https://api.bde.es/datos/series/SEC/SEC/O1_13_240500"


class DataSourceProbe:
    def __init__(self, cache: CacheBackend, timeout_seconds: int = 20) -> None:
        self.cache = cache
        self.timeout_seconds = timeout_seconds

    def probe_all(self, limit: int = 5) -> Dict[str, Any]:
        return {
            "ine": self.fetch_ine_operations(limit=limit),
            "eurostat": self.fetch_eurostat_catalog(limit=limit),
            "banco_de_espana": self.fetch_bde_sample(),
        }

    def fetch_ine_operations(self, limit: int = 5) -> Dict[str, Any]:
        cache_key = f"ine:operations:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            response = requests.get(
                INE_OPERATIONS_URL,
                params={"clase": "IND"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            operations: List[Dict[str, Any]] = data[:limit]
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "count": len(data),
                "sample": [
                    {"codigo": op.get("Codigo"), "nombre": op.get("Nombre")}
                    for op in operations
                ],
            }
            self.cache.set(cache_key, summary)
            return summary
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo en petición al INE: %s", exc)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": None,
                "error": str(exc),
                "sample": [],
            }

    def fetch_eurostat_catalog(self, limit: int = 5) -> Dict[str, Any]:
        cache_key = f"eurostat:toc:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            response = requests.get(
                EUROSTAT_TOC_URL, params={"limit": str(limit)}, timeout=self.timeout_seconds
            )
            response.raise_for_status()
            payload = response.json()
            entries: List[Dict[str, Any]] = payload.get("datasets", [])[:limit]
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "count": len(payload.get("datasets", [])),
                "sample": entries,
            }
            self.cache.set(cache_key, summary)
            return summary
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo en petición a Eurostat: %s", exc)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": None,
                "error": str(exc),
                "sample": [],
            }

    def fetch_bde_sample(self) -> Dict[str, Any]:
        cache_key = "bde:sample"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            response = requests.get(BANCO_ESPANA_SERIES_URL, params={"type": "JSON"}, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload: Dict[str, Any] = response.json()
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": response.status_code,
                "keys": list(payload.keys())[:5],
            }
            self.cache.set(cache_key, summary)
            return summary
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo en petición al Banco de España: %s", exc)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status_code": None,
                "error": str(exc),
                "sample": [],
            }
