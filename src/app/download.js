export function downloadReport(content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "aigc-creative-report.md";
  link.click();
  URL.revokeObjectURL(url);
}
