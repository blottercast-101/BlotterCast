/**
 * BlotterCast Report Preview & Tab Management Helpers
 * Handles browser tab name, system/PDF document icon, and MIME types.
 */

const BC_REPORT_FAVICON = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%231e3a2b'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM14 9V3.5L18.5 8H14z'/></svg>";

/**
 * METHOD A: Generates a named, branded print/preview browser tab via window.open.
 * Explicitly injects title, system favicon, viewport meta, and styles before document.close().
 *
 * @param {string} htmlContent - Body/table HTML markup
 * @param {string} [reportTitle='Settlement Compliance Report'] - Tab title
 * @param {boolean} [autoPrint=false] - Whether to invoke print dialog on load
 * @returns {Window|null}
 */
function openReportPrintTab(htmlContent, reportTitle = 'Settlement Compliance Report', autoPrint = false) {
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    if (typeof showToast === 'function') {
      showToast('Please allow popups to preview report.', 'error');
    }
    return null;
  }

  printWindow.document.write(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${reportTitle}</title>
      <!-- Sets the PDF / App Icon in browser tab -->
      <link rel="icon" type="image/svg+xml" href="${BC_REPORT_FAVICON}">
      <style>
        /* Report base styling */
        @page { size: letter portrait; margin: 0.5in; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          padding: 24px;
          color: #1e293b;
          background: #ffffff;
        }
        .header {
          text-align: center;
          border-bottom: 2px solid #0f172a;
          padding-bottom: 12px;
          margin-bottom: 18px;
        }
        .header h2 {
          margin: 0 0 4px;
          font-size: 18px;
          color: #1e3a2b;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }
        .header p {
          margin: 0;
          font-size: 13px;
          color: #64748b;
        }
        
        /* Enforce responsive, non-overlapping table cells */
        table.report-table {
          width: 100% !important;
          table-layout: fixed !important;
          border-collapse: collapse !important;
          font-size: 11px;
          margin-top: 12px;
        }
        table.report-table th,
        table.report-table td {
          white-space: normal !important;
          word-wrap: break-word !important;
          overflow-wrap: break-word !important;
          word-break: break-word !important;
          vertical-align: top !important;
          padding: 6px 8px !important;
        }
        table.report-table th {
          background: #1e3a2b !important;
          color: #ffffff !important;
          font-weight: 600;
          border: 1px solid #1e3a2b;
          text-align: left;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
        table.report-table td {
          border: 1px solid #cbd5e1;
          color: #1e293b;
        }
        table.report-table tbody tr:nth-child(even) {
          background: #f0f9f2 !important;
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
        .footer {
          margin-top: 24px;
          font-size: 11px;
          color: #94a3b8;
          text-align: right;
        }
        @media print {
          body { padding: 0; }
          @page { margin: 1.5cm; }
          table.report-table th {
            background-color: #1e3a2b !important;
            color: #ffffff !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          table.report-table tbody tr:nth-child(even) {
            background-color: #f0f9f2 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
        }
      </style>
    </head>
    <body>
      ${htmlContent}
      ${autoPrint ? '<script>window.onload = function() { window.print(); };</script>' : ''}
    </body>
    </html>
  `);

  printWindow.document.close();
  printWindow.document.title = reportTitle; // Guarantees title reflects on tab bar
  return printWindow;
}

/**
 * METHOD B: Previews a generated PDF Blob or jsPDF instance in a new tab with
 * strict application/pdf MIME type and document title properties.
 *
 * @param {Object|Blob} pdfOrBlob - jsPDF instance or raw Blob
 * @param {string} [reportTitle='Settlement_Compliance_Report'] - PDF document title
 * @returns {string} blobUrl
 */
function previewPdfBlob(pdfOrBlob, reportTitle = 'Settlement_Compliance_Report') {
  if (pdfOrBlob && typeof pdfOrBlob.setProperties === 'function') {
    pdfOrBlob.setProperties({
      title: reportTitle,
      subject: 'Barangay Official Report'
    });
  }

  const blob = (pdfOrBlob && typeof pdfOrBlob.output === 'function')
    ? pdfOrBlob.output('blob')
    : (pdfOrBlob instanceof Blob ? pdfOrBlob : new Blob([pdfOrBlob], { type: 'application/pdf' }));

  const blobUrl = URL.createObjectURL(blob);
  const previewTab = window.open(blobUrl, '_blank');
  if (previewTab) {
    previewTab.document.title = reportTitle;
  }
  return blobUrl;
}

if (typeof window !== 'undefined') {
  window.BC_REPORT_FAVICON = BC_REPORT_FAVICON;
  window.openReportPrintTab = openReportPrintTab;
  window.previewPdfBlob = previewPdfBlob;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    BC_REPORT_FAVICON,
    openReportPrintTab,
    previewPdfBlob
  };
}
