from __future__ import annotations

from pathlib import Path

from .analytics import Summary
from .config import settings

_DEFAULT_PROMPT = Path(__file__).parent / "prompts" / "brief_es.txt"


def load_prompt() -> str:
    """Read the brief prompt from disk so it is editable without touching code."""
    path = Path(settings.brief_prompt_path) if settings.brief_prompt_path else _DEFAULT_PROMPT
    return path.read_text(encoding="utf-8").strip()


def stats_block(summary: Summary, scope: str) -> str:
    """Deterministic facts the narrator may use, and nothing else."""
    latest_fecha = summary.latest_fecha.isoformat() if summary.latest_fecha else "—"
    oldest_fecha = summary.oldest_fecha.isoformat() if summary.oldest_fecha else "—"
    lines = [
        f"Ventana: {scope}",
        f"Lecturas: {summary.count}",
        f"TRM actual: {summary.latest:,.2f} (al {latest_fecha})",
        f"Cambio en ventana: {summary.change_abs:+,.2f} ({summary.change_pct:+.2f}%) desde {oldest_fecha}",
        f"Máximo / mínimo: {summary.high:,.2f} / {summary.low:,.2f}",
        f"Promedio: {summary.mean:,.2f}",
        f"Volatilidad (desv. est.): {summary.volatility:,.2f}",
        f"Racha actual: {summary.streak_dir} de {summary.streak_len} lecturas",
    ]
    if summary.big_moves:
        top = summary.big_moves[0]
        fecha = top.fecha.isoformat() if top.fecha else "—"
        lines.append(f"Movimientos fuertes: {len(summary.big_moves)} (mayor: {top.delta:+,.2f} el {fecha})")
    return "\n".join(lines)


def narrate(summary: Summary, scope: str) -> str:
    facts = stats_block(summary, scope)
    if not settings.openai_api_key:
        return _fallback(facts)
    return _llm(facts)


def _llm(facts: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.judge_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": load_prompt()},
            {"role": "user", "content": facts},
        ],
    )
    return resp.choices[0].message.content or facts


def _fallback(facts: str) -> str:
    head = "Lectura (plantilla, sin LLM — exporta OPENAI_API_KEY para narrativa):"
    return f"{head}\n{facts}"
