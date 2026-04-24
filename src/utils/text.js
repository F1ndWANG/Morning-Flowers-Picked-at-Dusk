export function tokenize(text) {
  return new Set(
    text
      .toLowerCase()
      .split(/[\s，。、“”‘’：:；;,.!?！？|/]+/)
      .map((item) => item.trim())
      .filter(Boolean)
  );
}

export function jaccardSimilarity(a, b) {
  const intersection = [...a].filter((item) => b.has(item)).length;
  const union = new Set([...a, ...b]).size;
  return union === 0 ? 0 : intersection / union;
}
