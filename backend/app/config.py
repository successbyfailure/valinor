from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class VersionConfig:
    version: str
    codename: str


@dataclass(frozen=True)
class AppSettings:
    env: str
    cache_backend: str
    cache_url: str
    version_file: Path


def load_version_config(path: Path | str = "config/version.yaml") -> VersionConfig:
    version_path = Path(path)
    with version_path.open(encoding="utf-8") as version_file:
        content: Dict[str, Any] = yaml.safe_load(version_file)
    return VersionConfig(
        version=str(content.get("version", "0.0.0")),
        codename=str(content.get("codename", "sin-nombre")),
    )


def get_settings() -> AppSettings:
    return AppSettings(
        env=os.getenv("APP_ENV", "development"),
        cache_backend=os.getenv("CACHE_BACKEND", "memory"),
        cache_url=os.getenv("CACHE_URL", "redis://redis:6379/0"),
        version_file=Path(os.getenv("VERSION_FILE", "config/version.yaml")),
    )
