from __future__ import annotations

from unicodedata import category, normalize


def join_titles(values: list[str]) -> str:
    return ", ".join(values[:6]) if values else "sin registros"


def normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if category(char) != "Mn")


def payload_text(value: object | None) -> str | None:
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    if isinstance(value, int | float):
        return str(value)
    return None


def compare_int(
    *,
    label: str,
    current: int | None,
    previous: int | None,
    unit: str,
    relevant_delta: int,
) -> list[str]:
    if current is None or previous is None:
        return []
    delta = current - previous
    if abs(delta) < relevant_delta:
        return []
    direction = "subio" if delta > 0 else "bajo"
    return [f"{label} {direction} de {previous} a {current} {unit}."]


def compare_decimal(
    *,
    label: str,
    current: object | None,
    previous: object | None,
    unit: str,
    relevant_delta: float,
) -> list[str]:
    if current is None or previous is None:
        return []
    current_value = float(current)
    previous_value = float(previous)
    delta = current_value - previous_value
    if abs(delta) < relevant_delta:
        return []
    direction = "subio" if delta > 0 else "bajo"
    return [f"{label} {direction} de {previous_value:g} a {current_value:g} {unit}."]
