import math
import re


TOKEN_PATTERN = r"[\s,\n.;:!?，。；：！？、]+"


def clamp(value: float, lower: float, upper: float) -> float:
  return max(lower, min(upper, value))


def tokenize(text: str) -> set[str]:
  return {token.strip().lower() for token in re.split(TOKEN_PATTERN, str(text or "")) if token.strip()}


def token_list(text: str) -> list[str]:
  return [token.strip().lower() for token in re.split(TOKEN_PATTERN, str(text or "")) if token.strip()]


def overlap_ratio(source: str, target: str) -> float:
  source_tokens = tokenize(source)
  target_tokens = tokenize(target)
  if not source_tokens or not target_tokens:
    return 0
  return len(source_tokens & target_tokens) / len(source_tokens)


def jaccard_text(a: str, b: str) -> float:
  left = tokenize(a)
  right = tokenize(b)
  union = left | right
  return len(left & right) / len(union) if union else 0


def saturation(value: float, scale: float) -> float:
  if scale <= 0:
    return 0
  return clamp(1 - math.exp(-value / scale), 0, 1)
