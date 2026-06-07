from trm_watch.client import TrmClient


def test_where_empty_when_no_filters():
    assert TrmClient._build_where(None, None) == ""


def test_where_since_only():
    assert TrmClient._build_where("2026-01-01", None) == "vigenciadesde >= '2026-01-01'"


def test_where_combines_since_and_until():
    where = TrmClient._build_where("2026-01-01", "2026-06-01")
    assert "vigenciadesde >= '2026-01-01'" in where
    assert "vigenciadesde <= '2026-06-01'" in where
    assert " AND " in where


def test_escape_doubles_quotes():
    assert "''" in TrmClient._build_where("2026'01", None)
