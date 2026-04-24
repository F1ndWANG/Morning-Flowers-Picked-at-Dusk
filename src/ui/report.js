export function renderReport(dom, report) {
  dom.reportOutput.value = report;
}

export function bindReportDownload(dom, onDownload) {
  dom.reportBtn.onclick = onDownload;
}
