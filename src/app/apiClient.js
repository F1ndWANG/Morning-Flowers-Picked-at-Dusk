const DEFAULT_API_BASE = "http://127.0.0.1:8000";


function buildUrl(base, path) {
  return `${base.replace(/\/$/, "")}${path}`;
}


export function createApiClient(baseUrl = DEFAULT_API_BASE) {
  async function request(path, options = {}) {
    const response = await fetch(buildUrl(baseUrl, path), {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
      ...options,
    });

    if (!response.ok) {
      let detail = "";
      try {
        const payload = await response.json();
        detail = payload.detail || payload.message || JSON.stringify(payload);
      } catch {
        detail = await response.text();
      }
      throw new Error(detail ? `API request failed: ${response.status} - ${detail}` : `API request failed: ${response.status}`);
    }

    return response.json();
  }

  return {
    baseUrl,
    checkHealth() {
      return request("/health");
    },
    getCatalog() {
      return request("/api/v1/catalog");
    },
    getSamples() {
      return request("/api/v1/samples");
    },
    getIntegrations() {
      return request("/api/v1/integrations");
    },
    getModelRuntime() {
      return request("/api/v1/models/runtime");
    },
    getModelHealth() {
      return request("/api/v1/models/health");
    },
    getModelRegistry() {
      return request("/api/v1/models/registry");
    },
    activateModel(modelId) {
      return request("/api/v1/models/activate", {
        method: "POST",
        body: JSON.stringify({ modelId }),
      });
    },
    getOfflineBenchmark() {
      return request("/api/v1/benchmarks/offline");
    },
    getHistory() {
      return request("/api/v1/experiments/history");
    },
    saveHistory(form) {
      return request("/api/v1/experiments/history", {
        method: "POST",
        body: JSON.stringify(form),
      });
    },
    clearHistory() {
      return request("/api/v1/experiments/history", {
        method: "DELETE",
      });
    },
    runPipeline(form) {
      return request("/api/v1/pipeline/run", {
        method: "POST",
        body: JSON.stringify(form),
      });
    },
    createSnapshot(form) {
      return request("/api/v1/experiments/snapshot", {
        method: "POST",
        body: JSON.stringify(form),
      });
    },
  };
}
