import os
import unittest
from app import create_app
from app.blueprints.reports import (
    _build_settlement_compliance_pdf,
    _build_incident_summary_pdf,
    _build_blotter_summary_pdf,
    _data_table,
    BC_GREEN_HEADER,
    BC_GREEN_PALE,
)
from app.models import Settlement, BlotterRecord, Incident
from app.extensions import db
from test_mfa_helper import login as mfa_login


class TestReportTableWrapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_css_report_table_styles_exist(self):
        css_path = os.path.join(self.app.root_path, "..", "frontend", "styles.css")
        self.assertTrue(os.path.isfile(css_path), "styles.css must exist")
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn("table.report-table", css)
        self.assertIn("table-layout: fixed !important", css)
        self.assertIn("border-collapse: collapse !important", css)
        self.assertIn("white-space: normal !important", css)
        self.assertIn("word-wrap: break-word !important", css)
        self.assertIn("overflow-wrap: break-word !important", css)
        self.assertIn("word-break: break-word !important", css)
        self.assertIn("vertical-align: top !important", css)
        self.assertIn("padding: 6px 8px !important", css)
        self.assertIn("#1e3a2b", css)
        self.assertIn("#f0f9f2", css)
        self.assertIn("@media print", css)

    def test_frontend_app_js_batch_print_report_table(self):
        js_path = os.path.join(self.app.root_path, "..", "frontend", "app.js")
        self.assertTrue(os.path.isfile(js_path), "app.js must exist")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("table.report-table", js)
        self.assertIn('class="report-table"', js)
        self.assertIn("table-layout: fixed !important", js)
        self.assertIn("word-break: break-word !important", js)
        self.assertIn("white-space: normal !important", js)
        self.assertIn("width: 15%;", js)
        self.assertIn("width: 35%;", js)
        self.assertIn("width: 18%;", js)
        self.assertIn("width: 17%;", js)
        self.assertIn("#1e3a2b", js)
        self.assertIn("#f0f9f2", js)

    def test_pdf_data_table_wraps_in_paragraph(self):
        from reportlab.platypus import Paragraph, Table
        headers = ["Case No.", "Case Title", "Nature", "Date Filed", "Status"]
        rows = [
            ["STL-2026-999", "Legacy Complainant vs Legacy Respondent", "Physical Injury / Property Damage", "2026-01-15", "Complied"]
        ]
        col_widths = [27, 63, 32.4, 30.6, 27]
        t = _data_table(headers, rows, col_widths)
        self.assertIsInstance(t, Table)
        # Verify table_data contains Flowables/Paragraphs, not plain strings
        # In ReportLab Table, _cellvalues holds the rows of cells
        for row in t._cellvalues:
            for cell in row:
                self.assertIsInstance(cell, Paragraph, f"Cell {cell} must be wrapped in a Paragraph for auto-wrapping")

    def test_settlement_compliance_pdf_with_long_case_title(self):
        with self.app.app_context():
            blotter = BlotterRecord.query.first()
            existing = Settlement.query.filter_by(case_no="TEST-STL-WRAP-001").first()
            if not existing and blotter:
                s = Settlement(
                    blotter_id=blotter.id,
                    case_no="TEST-STL-WRAP-001",
                    case_title="Legacy Complainant vs Legacy Respondent with Very Long Extra Descriptive Text That Would Overflow",
                    complaint_title="Test Complaint",
                    nature="Boundary Dispute / Property Damage",
                    status="Ongoing",
                )
                db.session.add(s)
                db.session.commit()

            pdf_bytes = _build_settlement_compliance_pdf()
            self.assertTrue(len(pdf_bytes) > 1000)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_incident_and_blotter_pdf_builders(self):
        with self.app.app_context():
            inc_pdf = _build_incident_summary_pdf("2026-01-01", "2026-08-31", "")
            self.assertTrue(len(inc_pdf) > 1000)
            self.assertTrue(inc_pdf.startswith(b"%PDF"))

            blt_pdf = _build_blotter_summary_pdf("2026-01-01", "2026-08-31", "")
            self.assertTrue(len(blt_pdf) > 1000)
            self.assertTrue(blt_pdf.startswith(b"%PDF"))

    def test_api_generate_and_download_matrix(self):
        mfa_login(self.client, "admin", "admin123")
        reports_to_test = [
            ("Settlement Compliance Report", "pdf"),
            ("Settlement Compliance Report", "excel"),
            ("Blotter Summary Report", "pdf"),
            ("Blotter Summary Report", "excel"),
            ("Incident Summary Report", "pdf"),
        ]
        for rt, fmt in reports_to_test:
            res = self.client.post(
                "/api/reports.php?action=generate",
                json={"type": rt, "from": "2026-01-01", "to": "2026-08-16", "zone": "", "format": fmt}
            )
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertTrue(data.get("file"))

            down_res = self.client.get(f"/api/reports.php?action=download&file={data['file']}")
            self.assertEqual(down_res.status_code, 200)
            self.assertTrue(len(down_res.data) > 0)


if __name__ == "__main__":
    unittest.main()
