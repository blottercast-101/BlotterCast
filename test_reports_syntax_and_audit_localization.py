import unittest
import os
import re

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")

class TestReportsSyntaxAndAuditLocalization(unittest.TestCase):
    def setUp(self):
        self.reports_js_path = os.path.join(FRONTEND_DIR, "reports.js")
        self.public_reports_js_path = os.path.join(FRONTEND_DIR, "public", "js", "reports.js")
        self.app_js_path = os.path.join(FRONTEND_DIR, "app.js")
        self.i18n_js_path = os.path.join(FRONTEND_DIR, "i18n.js")
        self.users_html_path = os.path.join(FRONTEND_DIR, "users.html")
        self.census_html_path = os.path.join(FRONTEND_DIR, "census.html")
        self.blotter_html_path = os.path.join(FRONTEND_DIR, "blotter.html")

        with open(self.reports_js_path, "r", encoding="utf-8") as f:
            self.reports_js = f.read()

        with open(self.public_reports_js_path, "r", encoding="utf-8") as f:
            self.public_reports_js = f.read()

        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

        with open(self.i18n_js_path, "r", encoding="utf-8") as f:
            self.i18n_js = f.read()

        with open(self.users_html_path, "r", encoding="utf-8") as f:
            self.users_html = f.read()

        with open(self.census_html_path, "r", encoding="utf-8") as f:
            self.census_html = f.read()

        with open(self.blotter_html_path, "r", encoding="utf-8") as f:
            self.blotter_html = f.read()

    def test_no_top_level_const_bc_report_favicon_collision(self):
        """reports.js and app.js must not declare top-level const BC_REPORT_FAVICON that causes SyntaxError collision."""
        self.assertNotIn("const BC_REPORT_FAVICON =", self.reports_js)
        self.assertNotIn("const BC_REPORT_FAVICON =", self.public_reports_js)
        self.assertNotIn("const BC_REPORT_FAVICON =", self.app_js)

        # Scoped to window
        self.assertIn("typeof window.BC_REPORT_FAVICON === 'undefined'", self.reports_js)
        self.assertIn("window.BC_REPORT_FAVICON =", self.reports_js)
        self.assertIn("typeof window.BC_REPORT_FAVICON === 'undefined'", self.app_js)

    def test_import_button_styling_and_attributes_census(self):
        """census.html import button must have soft green style, folder SVG icon, and data-i18n="import_data"."""
        btn_match = re.search(r'<button[^>]*id="importBtn"[^>]*>(.*?)</button>', self.census_html, re.DOTALL)
        self.assertIsNotNone(btn_match, "id='importBtn' not found in census.html")
        btn_content = btn_match.group(0)
        self.assertIn("bg-[#edf5f0]", btn_content)
        self.assertIn("text-[#1e3a2b]", btn_content)
        self.assertIn("px-4 py-2.5", btn_content)
        self.assertIn("rounded-xl", btn_content)
        self.assertIn("text-xs font-semibold", btn_content)
        self.assertIn('d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"', btn_content)
        self.assertIn('data-i18n="import_data"', btn_content)

    def test_import_button_styling_and_attributes_blotter(self):
        """blotter.html import button must have soft green style, folder SVG icon, and data-i18n="import_data"."""
        btn_match = re.search(r'<button[^>]*openModal\([\'"]importModal[\'"][^>]*>(.*?)</button>', self.blotter_html, re.DOTALL)
        self.assertIsNotNone(btn_match, "Import modal button not found in blotter.html")
        btn_content = btn_match.group(0)
        self.assertIn("bg-[#edf5f0]", btn_content)
        self.assertIn("text-[#1e3a2b]", btn_content)
        self.assertIn("px-4 py-2.5", btn_content)
        self.assertIn("rounded-xl", btn_content)
        self.assertIn('d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"', btn_content)
        self.assertIn('data-i18n="import_data"', btn_content)

    def test_action_table_header_data_i18n(self):
        """users.html table headers must have data-i18n="action" for the Action column."""
        self.assertIn('<th data-i18n="action">Action</th>', self.users_html)
        self.assertIn('<th data-i18n="actions">Actions</th>', self.users_html)

        # Dictionary translations
        self.assertIn('action: "KILOS"', self.i18n_js)
        self.assertIn('"Action": "KILOS"', self.app_js)
        self.assertIn('"ACTION": "KILOS"', self.app_js)

    def test_audit_action_badges_mapping(self):
        """app.js must implement bcTranslateAuditAction mapping CREATED, DELETED, UPDATED, LOGIN to Tagalog."""
        self.assertIn("function bcTranslateAuditAction(action)", self.app_js)
        self.assertIn("window.bcTranslateAuditAction = bcTranslateAuditAction", self.app_js)
        self.assertIn("'GINAWA'", self.app_js)
        self.assertIn("'BINURA'", self.app_js)
        self.assertIn("'INUPDATE'", self.app_js)
        self.assertIn("'NAG-LOGIN'", self.app_js)

    def test_audit_log_details_template_translation(self):
        """app.js must implement bcTranslateAuditDetails matching templates while preserving usernames untouched."""
        self.assertIn("function bcTranslateAuditDetails(details)", self.app_js)
        self.assertIn("window.bcTranslateAuditDetails = bcTranslateAuditDetails", self.app_js)
        self.assertIn("Nakalikha ng account:", self.app_js)
        self.assertIn("Nabura ang account:", self.app_js)
        self.assertIn("Matagumpay na pag-login (Naka-", self.app_js)
        self.assertIn("Inupdate ang sariling detalye ng account", self.app_js)
        self.assertIn("Naisave ang mga setting ng sistema", self.app_js)

    def test_load_audit_log_uses_translation_helpers(self):
        """loadAuditLog in users.html must invoke bcTranslateAuditAction and bcTranslateAuditDetails."""
        self.assertIn("bcTranslateAuditAction(r.action)", self.users_html)
        self.assertIn("bcTranslateAuditDetails(r.details)", self.users_html)

if __name__ == "__main__":
    unittest.main()
