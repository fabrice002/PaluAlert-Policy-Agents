"""The surveillance agent's tools: the malaria early-warning system (palualert_app).

If AI4G_MEWS_API_URL is set, calls go over HTTP to a running palualert_app
(`python serve_all.py`). Otherwise palualert_app is loaded in-process through
FastAPI's TestClient against a throwaway SQLite database, so a scenario run
never touches real data and needs no server.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile
from pathlib import Path

from palualert_agents.settings import APP_DIR, settings


class MewsClient:
    def __init__(self, base_url: str = settings.mews_api_url):
        self.base_url = base_url.rstrip("/")
        self._client = None

    def _http(self):
        if self._client is not None:
            return self._client
        if self.base_url:
            import httpx
            self._client = httpx.Client(base_url=self.base_url, timeout=120)
        else:
            db = Path(tempfile.mkdtemp(prefix="mews_agents_")) / "mews.db"
            os.environ.setdefault("MEWS_DATABASE_URL", "sqlite:///" + str(db).replace("\\", "/"))
            os.environ.setdefault("MEWS_SCHEDULER_ENABLED", "false")
            if str(APP_DIR) not in sys.path:
                sys.path.insert(0, str(APP_DIR))
            from fastapi.testclient import TestClient
            from app.main import app            # palualert_app's FastAPI application
            self._client = TestClient(app)
            self._client.__enter__()            # runs the lifespan: loads the bundle
        return self._client

    @property
    def mode(self) -> str:
        return f"http:{self.base_url}" if self.base_url else "in-process"

    def health(self) -> dict:
        return self._http().get("/api/v1/health").json()

    def district(self, name: str) -> dict:
        r = self._http().get(f"/api/v1/districts/{name}")
        r.raise_for_status()
        return r.json()

    def predict(self, readings: list[dict]) -> dict:
        r = self._http().post("/api/v1/predict", json={"readings": readings})
        r.raise_for_status()
        return r.json()

    def shap(self, prediction_id: int, model_kind: str = "regressor") -> dict:
        r = self._http().get(f"/api/v1/prediction/{prediction_id}/shap",
                             params={"model_kind": model_kind})
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        if self._client is not None and not self.base_url:
            self._client.__exit__(None, None, None)
        self._client = None


# ── sensor correction (the method of sensor_validation) ────────────────────
def _svp(t_c: float) -> float:
    """Saturation vapour pressure, hPa (Magnus, over water)."""
    return 6.112 * math.exp(17.62 * t_c / (243.12 + t_c))


def dew_point(t_c: float, rh: float) -> float:
    g = math.log(max(rh, 1e-3) / 100) + 17.62 * t_c / (243.12 + t_c)
    return 243.12 * g / (17.62 - g)


def correct_siting_offset(t_c: float, rh: float, offset_c: float) -> tuple[float, float]:
    """Remove a warm siting bias at constant moisture: subtract the offset from
    temperature and recompute relative humidity at the sensor's own dew point."""
    td = dew_point(t_c, rh)
    t_new = t_c - offset_c
    rh_new = min(100.0, 100 * _svp(td) / _svp(t_new))
    return round(t_new, 2), round(rh_new, 1)
