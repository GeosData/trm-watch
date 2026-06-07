from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, field_validator


def _to_float(value: str | float | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _to_date(value: str | None) -> date | None:
    if not value:
        return None
    # SODA serves timestamps like "2026-06-06T00:00:00.000"; keep only the date.
    return datetime.fromisoformat(value).date()


class Rate(BaseModel):
    """One TRM reading: the official USD/COP value effective from a given date.

    The TRM is published per business day; on weekends one value carries to the next
    business day. We key everything off `vigenciadesde` (the date it takes effect).
    """

    fecha: date | None = None
    valor: float = 0.0

    @field_validator("valor", mode="before")
    @classmethod
    def _coerce_valor(cls, v: object) -> float:
        return _to_float(v)  # type: ignore[arg-type]

    @classmethod
    def from_record(cls, row: dict) -> Rate:
        return cls(
            fecha=_to_date(row.get("vigenciadesde")),
            valor=row.get("valor", "0"),
        )
