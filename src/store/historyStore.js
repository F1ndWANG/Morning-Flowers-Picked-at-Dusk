const STORAGE_KEY = "aigc-creative-history";
const MAX_ITEMS = 8;

function getStorage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function loadHistory() {
  const storage = getStorage();
  if (!storage) {
    return [];
  }

  try {
    const raw = storage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveRun(record) {
  const storage = getStorage();
  if (!storage) {
    return [];
  }

  const history = loadHistory();
  const next = [record, ...history].slice(0, MAX_ITEMS);
  storage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

export function clearHistory() {
  const storage = getStorage();
  if (!storage) {
    return [];
  }
  storage.removeItem(STORAGE_KEY);
  return [];
}

export function createHistoryRecord(form, activeStrategy) {
  return {
    id: `${Date.now()}`,
    createdAt: new Date().toLocaleString("zh-CN", { hour12: false }),
    productName: form.productName,
    brandName: form.brandName,
    experimentMode: form.experimentMode,
    objective: form.objective,
    winnerTitle: activeStrategy.winner.title,
    ctr: activeStrategy.winner.metrics.ctr,
    cvr: activeStrategy.winner.metrics.cvr,
    ecpm: activeStrategy.winner.metrics.ecpm,
    riskLevel: activeStrategy.winner.compliance?.riskLevel ?? "低"
  };
}
