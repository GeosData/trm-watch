from datetime import date

from trm_watch.analytics import big_moves, summarize
from trm_watch.models import Rate


def make_rate(day: int, valor: float) -> Rate:
    return Rate(fecha=date(2026, 6, day), valor=valor)


def test_empty_is_zeroed():
    s = summarize([])
    assert s.count == 0
    assert s.latest == 0.0
    assert s.streak_dir == "plano"
    assert s.big_moves == []


def test_change_uses_oldest_and_latest_regardless_of_input_order():
    # input out of order; summarize sorts ascending by date
    rates = [make_rate(3, 3600), make_rate(1, 3500), make_rate(2, 3550)]
    s = summarize(rates)
    assert s.latest == 3600
    assert s.latest_fecha == date(2026, 6, 3)
    assert s.change_abs == 100
    assert round(s.change_pct, 4) == round(100 / 3500 * 100, 4)


def test_high_low_and_mean():
    rates = [make_rate(1, 3500), make_rate(2, 3700), make_rate(3, 3600)]
    s = summarize(rates)
    assert s.high == 3700
    assert s.low == 3500
    assert s.mean == 3600


def test_streak_counts_consecutive_rises():
    rates = [make_rate(1, 3500), make_rate(2, 3520), make_rate(3, 3540), make_rate(4, 3560)]
    s = summarize(rates)
    assert s.streak_dir == "alza"
    assert s.streak_len == 3


def test_streak_breaks_on_direction_change():
    rates = [make_rate(1, 3500), make_rate(2, 3600), make_rate(3, 3550), make_rate(4, 3540)]
    s = summarize(rates)
    assert s.streak_dir == "baja"
    assert s.streak_len == 2


def test_big_moves_flags_extreme_daily_change():
    rates = [make_rate(d, 3500 + d) for d in range(1, 10)] + [make_rate(10, 3900)]
    moves = big_moves(rates, z=2.0)
    assert len(moves) == 1
    assert moves[0].fecha == date(2026, 6, 10)


def test_no_big_moves_when_uniform_steps():
    rates = [make_rate(d, 3500 + 10 * d) for d in range(1, 6)]
    assert big_moves(rates) == []


def test_valor_coercion_handles_blank():
    assert Rate.from_record({"valor": ""}).valor == 0.0
    assert Rate.from_record({"valor": "3588.09"}).valor == 3588.09


def test_from_record_parses_timestamp_date():
    r = Rate.from_record({"vigenciadesde": "2026-06-06T00:00:00.000", "valor": "3588.09"})
    assert r.fecha == date(2026, 6, 6)
