import unittest
import os
import re

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))

class TestExportButtonAndReportsI18n(unittest.TestCase):
    def setUp(self):
        self.app_js_path = os.path.join(REPO_ROOT, "frontend", "app.js")
        self.i18n_js_path = os.path.join(REPO_ROOT, "frontend", "i18n.js")
        self.reports_html_path = os.path.join(REPO_ROOT, "frontend", "reports.html")
        self.blotter_html_path = os.path.join(REPO_ROOT, "frontend", "blotter.html")
        self.settlement_html_path = os.path.join(REPO_ROOT, "frontend", "settlement.html")
        self.incident_html_path = os.path.join(REPO_ROOT, "frontend", "incident.html")
        self.census_html_path = os.path.join(REPO_ROOT, "frontend", "census.html")
        self.users_html_path = os.path.join(REPO_ROOT, "frontend", "users.html")

        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

        with open(self.i18n_js_path, "r", encoding="utf-8") as f:
            self.i18n_js = f.read()

        with open(self.reports_html_path, "r", encoding="utf-8") as f:
            self.reports_html = f.read()

        with open(self.blotter_html_path, "r", encoding="utf-8") as f:
            self.blotter_html = f.read()

        with open(self.settlement_html_path, "r", encoding="utf-8") as f:
            self.settlement_html = f.read()

    def test_export_button_visual_styling_in_blotter(self):
        """Export to Excel button in blotter.html must have soft green background, forest green text/icon, rounded-xl, px-4 py-2.5"""
        btn_match = re.search(r'<button[^>]*id="exportExcelBtn"[^>]*>', self.blotter_html)
        self.assertIsNotNone(btn_match, "exportExcelBtn not found in blotter.html")
        btn_tag = btn_match.group(0)
        self.assertIn("bg-[#edf5f0]", btn_tag)
        self.assertIn("hover:bg-[#e2efe7]", btn_tag)
        self.assertIn("text-[#1e3a2b]", btn_tag)
        self.assertIn("px-4 py-2.5", btn_tag)
        self.assertIn("rounded-xl", btn_tag)
        self.assertIn("text-xs font-semibold", btn_tag)

        # SVG color
        export_btn_block = self.blotter_html[btn_match.start():self.blotter_html.find('</button>', btn_match.start())]
        self.assertIn("text-[#1e3a2b]", export_btn_block)

        # Adjacent import button should match
        import_btn_match = re.search(r'<button[^>]*openModal\([\'"]importModal[\'"][^>]*class="([^"]+)"', self.blotter_html)
        self.assertIsNotNone(import_btn_match)
        import_classes = import_btn_match.group(1)
        self.assertIn("px-4 py-2.5", import_classes)
        self.assertIn("bg-[#edf5f0]", import_classes)
        self.assertIn("rounded-xl", import_classes)

    def test_export_button_visual_styling_in_settlement(self):
        """Export button in settlement.html must also have soft green background, forest green text/icon, rounded-xl, px-4 py-2.5"""
        export_btn_match = re.search(r'<button[^>]*openExportFilter\([^\)]*action=settlement_monitoring[^\)]*\)[^>]*class="([^"]+)"', self.settlement_html)
        self.assertIsNotNone(export_btn_match)
        classes = export_btn_match.group(1)
        self.assertIn("bg-[#edf5f0]", classes)
        self.assertIn("hover:bg-[#e2efe7]", classes)
        self.assertIn("text-[#1e3a2b]", classes)
        self.assertIn("px-4 py-2.5", classes)
        self.assertIn("rounded-xl", classes)
        self.assertIn("text-xs font-semibold", classes)

    def test_i18n_dictionary_symmetry_and_reports_keys(self):
        """i18n.js must contain symmetrical keys for reports, scheduled reports, badges, and controls"""
        required_keys = [
            "scheduled_reports_title",
            "recent_generated_reports_title",
            "generate_report_title",
            "badge_pdf_only",
            "report_card_incident_summary_title",
            "report_card_incident_summary_desc",
            "report_card_predictive_risk_title",
            "report_card_predictive_risk_desc",
            "report_card_patrol_deployment_title",
            "report_card_patrol_deployment_desc",
            "report_card_trend_analysis_title",
            "report_card_trend_analysis_desc",
            "report_card_settlement_compliance_title",
            "report_card_settlement_compliance_desc",
            "report_card_comparative_period_title",
            "report_card_comparative_period_desc",
            "th_report",
            "th_frequency",
            "th_next_run",
            "th_recipients",
            "th_format",
            "th_enabled",
            "all_statuses",
            "view_archived",
            "view_active",
            "prev_label",
            "next_label",
        ]

        for k in required_keys:
            self.assertIn(f"{k}:", self.i18n_js, f"Missing key '{k}' in i18n.js")

        # Check Tagalog translations
        self.assertIn('scheduled_reports_title: "Naka-iskedyul na mga Ulat"', self.i18n_js)
        self.assertIn('badge_pdf_only: "PDF LAMANG"', self.i18n_js)
        self.assertIn('all_statuses: "Lahat ng Status"', self.i18n_js)
        self.assertIn('view_archived: "Tignan ang Naka-arkibo"', self.i18n_js)
        self.assertIn('prev_label: "‹ Nakalipas"', self.i18n_js)
        self.assertIn('next_label: "Susunod ›"', self.i18n_js)

    def test_bc_translations_reports_and_schedules(self):
        """BC_TRANSLATIONS.fil in app.js must have reports, schedules, and pagination entries"""
        self.assertIn('"Generate Report": "Gumawa ng Ulat"', self.app_js)
        self.assertIn('"Scheduled Reports": "Naka-iskedyul na mga Ulat"', self.app_js)
        self.assertIn('"Incident Summary Report": "Ulat sa Buod ng Insidente"', self.app_js)
        self.assertIn('"Predictive Risk Assessment": "Pagtatasa ng Inaasahang Panganib"', self.app_js)
        self.assertIn('"Patrol Deployment Plan": "Plano ng Pagpapakalat ng Patrolya"', self.app_js)
        self.assertIn('"Trend Analysis Report": "Ulat sa Pagsusuri ng Trend"', self.app_js)
        self.assertIn('"Settlement Compliance Report": "Ulat sa Pagtupad sa Kasunduan"', self.app_js)
        self.assertIn('"Comparative Period Report": "Ulat sa Paghahambing ng Panahon"', self.app_js)
        self.assertIn('"Next Monday": "Susunod na Lunes"', self.app_js)
        self.assertIn('"1st of month": "Unang araw ng buwan"', self.app_js)
        self.assertIn('"PDF Only": "PDF LAMANG"', self.app_js)
        self.assertIn('"‹ Prev": "‹ Nakalipas"', self.app_js)
        self.assertIn('"Next ›": "Susunod ›"', self.app_js)

    def test_proper_noun_exception_for_recipients(self):
        """Usernames like kapitan and admin in scheduled recipients must be protected in isProperNounOrName"""
        self.assertIn("kapitan", self.app_js)
        self.assertIn("admin", self.app_js)
        # Check regex in isProperNounOrName
        self.assertIn(r"/^(kapitan|admin)(,\s*(kapitan|admin))*$/i", self.app_js)

    def test_reports_html_data_i18n_attributes(self):
        """reports.html elements must have proper data-i18n attributes for all cards, headers, and badges"""
        self.assertIn('data-i18n="generate_report_title"', self.reports_html)
        self.assertIn('data-i18n="scheduled_reports_title"', self.reports_html)
        self.assertIn('data-i18n="recent_generated_reports_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_incident_summary_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_incident_summary_desc"', self.reports_html)
        self.assertIn('data-i18n="report_card_predictive_risk_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_predictive_risk_desc"', self.reports_html)
        self.assertIn('data-i18n="badge_pdf_only"', self.reports_html)
        self.assertIn('data-i18n="report_card_patrol_deployment_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_trend_analysis_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_settlement_compliance_title"', self.reports_html)
        self.assertIn('data-i18n="report_card_comparative_period_title"', self.reports_html)
        self.assertIn('data-i18n="th_report"', self.reports_html)
        self.assertIn('data-i18n="th_frequency"', self.reports_html)
        self.assertIn('data-i18n="th_next_run"', self.reports_html)
        self.assertIn('data-i18n="th_recipients"', self.reports_html)

    def test_scheduled_reports_recipients_preserved(self):
        """renderScheduledReports must preserve s.recipients untouched without translating kapitan or admin"""
        render_sched = re.search(r'function renderScheduledReports\(\)\s*\{(.*?)\n\}', self.reports_html, re.DOTALL)
        self.assertIsNotNone(render_sched)
        body = render_sched.group(1)
        self.assertIn('${s.recipients}', body)

    def test_pagination_and_record_count_formatters(self):
        """bcFormatRecordCount, bcFormatPaginationInfo, and bcRenderPagination must be defined and exported in app.js"""
        self.assertIn("function bcFormatRecordCount", self.app_js)
        self.assertIn("window.bcFormatRecordCount = bcFormatRecordCount", self.app_js)
        self.assertIn("function bcFormatPaginationInfo", self.app_js)
        self.assertIn("window.bcFormatPaginationInfo = bcFormatPaginationInfo", self.app_js)
        self.assertIn("window.bcRenderPagination = bcRenderPagination", self.app_js)
        self.assertIn("‹ Nakalipas", self.app_js)
        self.assertIn("Susunod ›", self.app_js)
        self.assertIn("mga tala", self.app_js)
        self.assertIn("Ipinapakita ang", self.app_js)

if __name__ == "__main__":
    unittest.main()
