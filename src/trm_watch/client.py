from __future__ import annotations

import httpx

from .config import settings
from .models import Rate


class TrmClient:
    """Thin SODA (Socrata) query client for the official TRM (USD/COP) dataset.

    Builds a SoQL query over the effective-date column and returns typed Rate rows.
    The API is public; an app token only raises the rate limit, so it is optional.
    """

    def __init__(self, token: str | None = None, timeout: float = 30.0) -> None:
        self._url = settings.dataset_url
        self._token = token or settings.app_token
        self._timeout = timeout

    def _headers(self) -> dict:
        if self._token:
            return {"X-App-Token": self._token}
        return {}

    def fetch(
        self,
        since: str | None = None,
        until: str | None = None,
        limit: int = 365,
    ) -> list[Rate]:
        where = self._build_where(since, until)
        params = {"$limit": str(limit), "$order": "vigenciadesde DESC"}
        if where:
            params["$where"] = where
        resp = httpx.get(self._url, params=params, headers=self._headers(), timeout=self._timeout)
        resp.raise_for_status()
        return [Rate.from_record(row) for row in resp.json()]

    @staticmethod
    def _build_where(since: str | None, until: str | None) -> str:
        clauses: list[str] = []
        if since:
            clauses.append(f"vigenciadesde >= '{_escape(since)}'")
        if until:
            clauses.append(f"vigenciadesde <= '{_escape(until)}'")
        return " AND ".join(clauses)


def _escape(value: str) -> str:
    return value.replace("'", "''")
