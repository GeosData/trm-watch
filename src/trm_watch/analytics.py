from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date

from .models import Rate


@dataclass
class DayMove:
    fecha: date | None
    valor: float
    delta: float  # change vs the previous reading in the window


@dataclass
class Summary:
    count: int
    latest: float
    latest_fecha: date | None
    oldest_fecha: date | None
    change_abs: float  # latest - oldest in window
    change_pct: float
    high: float
    low: float
    mean: float
    volatility: float  # population stdev of the values
    streak_dir: str  # "alza", "baja" or "plano"
    streak_len: int  # consecutive readings moving that direction
    big_moves: list[DayMove] = field(default_factory=list)


def _empty() -> Summary:
    return Summary(0, 0.0, None, None, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "plano", 0)


def summarize(rates: list[Rate], outlier_z: float = 2.0) -> Summary:
    series = _ascending(rates)
    if not series:
        return _empty()
    valores = [r.valor for r in series]
    oldest, latest = series[0], series[-1]
    change_abs = latest.valor - oldest.valor
    change_pct = (change_abs / oldest.valor * 100) if oldest.valor else 0.0
    direction, length = _streak(series)
    return Summary(
        count=len(series),
        latest=latest.valor,
        latest_fecha=latest.fecha,
        oldest_fecha=oldest.fecha,
        change_abs=change_abs,
        change_pct=change_pct,
        high=max(valores),
        low=min(valores),
        mean=statistics.mean(valores),
        volatility=statistics.pstdev(valores) if len(valores) > 1 else 0.0,
        streak_dir=direction,
        streak_len=length,
        big_moves=big_moves(series, outlier_z),
    )


def big_moves(rates: list[Rate], z: float = 2.0) -> list[DayMove]:
    """Readings whose day-over-day change is an outlier vs the window's typical move."""
    series = _ascending(rates)
    deltas = _deltas(series)
    if len(deltas) < 2:
        return []
    std = statistics.pstdev([d.delta for d in deltas])
    if std == 0:
        return []
    threshold = z * std
    flagged = [d for d in deltas if abs(d.delta) > threshold]
    flagged.sort(key=lambda d: abs(d.delta), reverse=True)
    return flagged


def _streak(series: list[Rate]) -> tuple[str, int]:
    """Length of the current run of same-direction moves, counting back from latest."""
    if len(series) < 2:
        return "plano", 0
    moves = [b.valor - a.valor for a, b in zip(series, series[1:])]
    last = moves[-1]
    if last == 0:
        return "plano", 0
    direction = "alza" if last > 0 else "baja"
    length = 1
    for move in reversed(moves[:-1]):
        if (move > 0) == (last > 0) and move != 0:
            length += 1
        else:
            break
    return direction, length


def _deltas(series: list[Rate]) -> list[DayMove]:
    return [
        DayMove(fecha=b.fecha, valor=b.valor, delta=b.valor - a.valor)
        for a, b in zip(series, series[1:])
    ]


def _ascending(rates: list[Rate]) -> list[Rate]:
    """Sort by date ascending; rows without a date sort last and keep input order."""
    return sorted(rates, key=lambda r: (r.fecha is None, r.fecha or date.min))
