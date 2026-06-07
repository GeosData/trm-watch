from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from .analytics import Summary, summarize
from .brief import narrate
from .client import TrmClient

app = typer.Typer(add_completion=False, help="Watch de la TRM (peso/dólar) en Colombia.")
console = Console()


@app.command()
def brief(
    since: str = typer.Option(None, help="Desde esta fecha (YYYY-MM-DD)."),
    until: str = typer.Option(None, help="Hasta esta fecha (YYYY-MM-DD)."),
    limit: int = typer.Option(365, help="Máximo de lecturas a traer."),
) -> None:
    """Trae la serie de TRM, calcula tendencia y narra una lectura cambiaria."""
    scope = _scope(since, until, limit)
    rates = TrmClient().fetch(since, until, limit)
    summary = summarize(rates)
    _render_table(summary)
    console.rule("Lectura")
    console.print(narrate(summary, scope))


@app.command()
def latest() -> None:
    """Muestra la TRM vigente y su cambio frente a la lectura anterior."""
    rates = TrmClient().fetch(limit=2)
    if not rates:
        console.print("Sin datos de TRM.")
        raise typer.Exit()
    summary = summarize(rates)
    fecha = summary.latest_fecha.isoformat() if summary.latest_fecha else "—"
    console.print(f"TRM {summary.latest:,.2f} COP/USD (al {fecha})")
    console.print(f"Cambio vs anterior: {summary.change_abs:+,.2f} ({summary.change_pct:+.2f}%)")


def _scope(since: str | None, until: str | None, limit: int) -> str:
    parts = []
    if since:
        parts.append(f"desde={since}")
    if until:
        parts.append(f"hasta={until}")
    if not parts:
        parts.append(f"últimas {limit} lecturas")
    return ", ".join(parts)


def _render_table(summary: Summary) -> None:
    table = Table(title="Resumen TRM")
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")
    table.add_row("Lecturas", str(summary.count))
    table.add_row("TRM actual", f"{summary.latest:,.2f}")
    table.add_row("Cambio en ventana", f"{summary.change_abs:+,.2f} ({summary.change_pct:+.2f}%)")
    table.add_row("Máximo / mínimo", f"{summary.high:,.2f} / {summary.low:,.2f}")
    table.add_row("Promedio", f"{summary.mean:,.2f}")
    table.add_row("Volatilidad", f"{summary.volatility:,.2f}")
    table.add_row("Racha", f"{summary.streak_dir} ({summary.streak_len})")
    table.add_row("Movimientos fuertes", str(len(summary.big_moves)))
    console.print(table)


if __name__ == "__main__":
    app()
