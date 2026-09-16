import io
import os
import unittest
from app import create_app
from app.blueprints.reports import (
    _build_settlement_compliance_pdf,
    _build_incident_summary_pdf,
    _build_blotter_summary_pdf,
)
from test_mfa_helper import login as mfa_login


class TestReportPreviewTabAndMime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_method_a_js_helpers_exist_and_inject_metadata(self):
        """Method A: Verifies openReportPrintTab injects title, SVG favicon, and tab title guarantee."""
        for path_suffix in ["reports.js", "app.js", "public/js/reports.js"]:
            js_path = os.path.join(self.app.root_path, "..", "frontend", *path_suffix.split("/"))
            self.assertTrue(os.path.isfile(js_path), f"{path_suffix} must exist")
            with open(js_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("openReportPrintTab", content)
            self.assertIn("<title>", content)
            self.assertIn("link rel=\"icon\"", content)
            self.assertIn("image/svg+xml", content)
            self.assertIn("viewBox='0 0 24 24'", content)
            self.assertIn("%231e3a2b", content)
            self.assertIn("@page { size: letter portrait; margin: 0.5in; }", content)
            self.assertIn("document.close()", content)
            self.assertIn("document.title = reportTitle", content)

    def test_method_a_table_structure_and_widths_retained(self):
        """Method A: Verifies wrapped table column widths and styles in app.js and reports.js."""
        for path_suffix in ["reports.js", "app.js"]:
            js_path = os.path.join(self.app.root_path, "..", "frontend", path_suffix)
            with open(js_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("table.report-table", content)
            self.assertIn("table-layout: fixed !important", content)
            self.assertIn("word-break: break-word !important", content)
            self.assertIn("white-space: normal !important", content)
            self.assertIn("#1e3a2b", content)
            self.assertIn("#f0f9f2", content)

        # In app.js, check column widths for settlement and batch tables
        app_js_path = os.path.join(self.app.root_path, "..", "frontend", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("width: 15%;", app_js)
        self.assertIn("width: 35%;", app_js)
        self.assertIn("width: 18%;", app_js)
        self.assertIn("width: 17%;", app_js)
        self.assertIn("Settlement_Compliance_Report", app_js)
        self.assertIn("Blotter_Report", app_js)
        self.assertIn("Incident_Summary_Report", app_js)
        self.assertIn("Census_Registry_Report", app_js)
        self.assertIn("${entityType}_${dateStr}", app_js)

    def test_method_b_js_preview_blob_helper(self):
        """Method B: Verifies previewPdfBlob helper sets title properties and MIME type."""
        for path_suffix in ["reports.js", "public/js/reports.js"]:
            js_path = os.path.join(self.app.root_path, "..", "frontend", *path_suffix.split("/"))
            with open(js_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("previewPdfBlob", content)
            self.assertIn("setProperties", content)
            self.assertIn("title: reportTitle", content)
            self.assertIn("subject: 'Barangay Official Report'", content)
            self.assertIn("type: 'application/pdf'", content)

    def test_method_b_pdf_binary_metadata(self):
        """Method B: Verifies ReportLab embeds Title and Subject metadata in the PDF stream."""
        with self.app.app_context():
            pdf_bytes = _build_settlement_compliance_pdf()
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))
            self.assertIn(b"/Title", pdf_bytes, "PDF must include /Title metadata for browser PDF viewer tab title")
            self.assertIn(b"/Subject", pdf_bytes, "PDF must include /Subject metadata")
            self.assertIn(b"Barangay Official Report", pdf_bytes)

            blt_bytes = _build_blotter_summary_pdf("2026-01-01", "2026-08-31", "")
            self.assertIn(b"/Title", blt_bytes)
            self.assertIn(b"/Subject", blt_bytes)

            inc_bytes = _build_incident_summary_pdf("2026-01-01", "2026-08-31", "")
            self.assertIn(b"/Title", inc_bytes)
            self.assertIn(b"/Subject", inc_bytes)

    def test_method_b_backend_preview_and_download_headers(self):
        """Method B: Verifies Content-Type and inline vs attachment Content-Disposition."""
        mfa_login(self.client, "admin", "admin123")

        # 1. Generate a PDF report
        res = self.client.post(
            "/api/reports.php?action=generate",
            json={"type": "Settlement Compliance Report", "from": "2026-01-01", "to": "2026-08-16", "zone": "", "format": "pdf"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        filename = data["file"]
        self.assertTrue(filename.endswith(".pdf"))
        self.assertIn("preview_url", data)

        # 2. Test Preview action -> inline Content-Disposition and application/pdf Content-Type
        preview_res = self.client.get(f"/api/reports.php?action=preview&file={filename}")
        self.assertEqual(preview_res.status_code, 200)
        self.assertEqual(preview_res.headers.get("Content-Type"), "application/pdf")
        self.assertIn("inline", preview_res.headers.get("Content-Disposition", ""))
        self.assertIn(filename, preview_res.headers.get("Content-Disposition", ""))
        self.assertTrue(preview_res.data.startswith(b"%PDF"))

        # 3. Test Download action -> attachment Content-Disposition
        download_res = self.client.get(f"/api/reports.php?action=download&file={filename}")
        self.assertEqual(download_res.status_code, 200)
        self.assertIn("attachment", download_res.headers.get("Content-Disposition", ""))
        self.assertIn(filename, download_res.headers.get("Content-Disposition", ""))

    def test_reports_html_includes_preview_script_and_controls(self):
        """Verifies reports.html loads reports.js, has Preview button and inline link."""
        html_path = os.path.join(self.app.root_path, "..", "frontend", "reports.html")
        self.assertTrue(os.path.isfile(html_path))
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('src="reports.js"', html)
        self.assertIn('action=preview', html)
        self.assertIn('id="prevBtn"', html)
        self.assertIn('simulateGenerate(true)', html)


if __name__ == "__main__":
    unittest.main()
