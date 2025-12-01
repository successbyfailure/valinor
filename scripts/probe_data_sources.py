from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))

from app.cache import MemoryCache  # noqa: E402
from app.datasources import DataSourceProbe  # noqa: E402


def main() -> None:
    cache = MemoryCache(ttl_seconds=120)
    probe = DataSourceProbe(cache)
    results = probe.probe_all(limit=3)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
