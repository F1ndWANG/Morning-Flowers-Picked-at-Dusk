export function renderRuntimeStatus(dom, status) {
  dom.runtimeMode.textContent = status.modeLabel;
  dom.runtimeBackend.textContent = status.backendLabel;
  dom.runtimeHint.textContent = status.hint;
}
