from backend.app.core.catalog import OBJECTIVE_LABELS, PLATFORM_LABELS


def objective_text(key: str) -> str:
  return OBJECTIVE_LABELS.get(key, key)


def platform_text(key: str) -> str:
  return PLATFORM_LABELS.get(key, key)


def format_percent(value: float) -> str:
  return f"{value * 100:.2f}%"


def format_lift(top: float, base: float) -> str:
  if not base:
    return "+0.0%"
  lift = ((top - base) / base) * 100
  return f"{'+' if lift >= 0 else ''}{lift:.1f}%"
