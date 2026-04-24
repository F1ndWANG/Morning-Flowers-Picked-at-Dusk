export function renderPrompts(dom, prompts) {
  dom.textSystemPrompt.textContent = prompts.textSystemPrompt;
  dom.textUserPrompt.textContent = prompts.textUserPrompt;
  dom.imagePrompt.textContent = prompts.imagePrompt;
  dom.promptMarkers.innerHTML = prompts.apiMarkers.map((item) => `<span>${item}</span>`).join("");
}
