import unittest
import os
import re

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


class TestDashboardAndPermissionsI18n(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FRONTEND_DIR, "dashboard.html"), "r", encoding="utf-8") as f:
            self.dashboard_html = f.read()
        with open(os.path.join(FRONTEND_DIR, "blotter.html"), "r", encoding="utf-8") as f:
            self.blotter_html = f.read()
        with open(os.path.join(FRONTEND_DIR, "users.html"), "r", encoding="utf-8") as f:
            self.users_html = f.read()
        with open(os.path.join(FRONTEND_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.app_js = f.read()
        with open(os.path.join(FRONTEND_DIR, "i18n.js"), "r", encoding="utf-8") as f:
            self.i18n_js = f.read()

    def test_search_placeholders_and_header_i18n(self):
        """Verify search inputs and header greetings have appropriate data-i18n attributes."""
        # Dashboard search input
        self.assertIn('id="dashboardGlobalSearch"', self.dashboard_html)
        self.assertIn('data-i18n-placeholder="search_records_placeholder"', self.dashboard_html)

        # Users search input
        self.assertIn('id="userSearch"', self.users_html)
        self.assertIn('data-i18n-placeholder="search_users_placeholder"', self.users_html)

        # Dashboard greeting
        self.assertIn('id="dashboardGreeting"', self.dashboard_html)
        self.assertIn('data-i18n="welcome_overview"', self.dashboard_html)

    def test_date_formatting_and_helpers_in_app_js(self):
        """Verify bcFormatDateLocale, bcFormatUserGreeting, and counter helpers in app.js."""
        self.assertIn("function bcFormatDateLocale", self.app_js)
        self.assertIn("'tl-PH'", self.app_js)
        self.assertIn("function bcFormatUserGreeting", self.app_js)
        self.assertIn("Maligayang pagbabalik", self.app_js)
        self.assertIn("function bcFormatThisWeekCount", self.app_js)
        self.assertIn("ngayong linggo", self.app_js)
        self.assertIn("function bcFormatResolutionRate", self.app_js)
        self.assertIn("antas ng pagresolba", self.app_js)

    def test_dashboard_card_metrics_and_sublabels(self):
        """Verify dashboard card metrics and sub-labels have data-i18n tags."""
        self.assertIn('data-i18n="total_blotters"', self.dashboard_html)
        self.assertIn('data-i18n="blotter_entries_on_file"', self.dashboard_html)
        self.assertIn('data-i18n="incident_reports"', self.dashboard_html)
        self.assertIn('data-i18n="pending_settlement"', self.dashboard_html)
        self.assertIn('data-i18n="awaiting_settlement"', self.dashboard_html)
        self.assertIn('data-i18n="resolved_cases"', self.dashboard_html)
        self.assertIn('data-i18n="resolved_lowercase"', self.dashboard_html)
        self.assertIn('data-i18n="new_this_week"', self.dashboard_html)
        self.assertIn('data-i18n="awaiting_settlement_cap"', self.dashboard_html)

        # Risk forecast card
        self.assertIn('data-i18n="risk_forecast"', self.dashboard_html)
        self.assertIn('data-i18n="risk_rankings_title"', self.dashboard_html)
        self.assertIn('data-i18n="risk_hotspots_desc"', self.dashboard_html)

    def test_blotter_card_metrics_and_subtitles(self):
        """Verify blotter.html has data-i18n tags for cards and subtitle."""
        self.assertIn('data-i18n="manage_blotter_records"', self.blotter_html)
        self.assertIn('data-i18n="total_blotters"', self.blotter_html)
        self.assertIn('data-i18n="blotter_entries_on_file"', self.blotter_html)
        self.assertIn('data-i18n="incident_reports"', self.blotter_html)
        self.assertIn('data-i18n="pending_settlement"', self.blotter_html)
        self.assertIn('data-i18n="awaiting_settlement"', self.blotter_html)
        self.assertIn('data-i18n="resolved_cases"', self.blotter_html)

    def test_quick_actions_and_section_headers(self):
        """Verify quick action tiles and section headers in dashboard.html."""
        self.assertIn('data-i18n="recent_blotter_entries"', self.dashboard_html)
        self.assertIn('data-i18n="view_all_arrow"', self.dashboard_html)
        self.assertIn('data-i18n="resolution_rate"', self.dashboard_html)
        self.assertIn('data-i18n="quick_actions"', self.dashboard_html)

        # Quick action tiles
        self.assertIn('data-i18n="quick_blotter_records"', self.dashboard_html)
        self.assertIn('data-i18n="quick_new_incident"', self.dashboard_html)
        self.assertIn('data-i18n="quick_monitor_settlement"', self.dashboard_html)
        self.assertIn('data-i18n="quick_generate_report"', self.dashboard_html)
        self.assertIn('data-i18n="quick_import_census"', self.dashboard_html)
        self.assertIn('data-i18n="quick_users_roles"', self.dashboard_html)

    def test_role_permission_matrix_and_badges_in_users(self):
        """Verify role permission matrix headers, action rows, system users, and protected badge."""
        self.assertIn('data-i18n="role_permission_matrix"', self.users_html)
        self.assertIn('data-i18n="th_permission"', self.users_html)
        self.assertIn('data-i18n="role_col_admin"', self.users_html)
        self.assertIn('data-i18n="role_col_captain"', self.users_html)
        self.assertIn('data-i18n="role_col_officer"', self.users_html)
        self.assertIn('data-i18n="role_col_encoder"', self.users_html)
        self.assertIn('data-i18n="system_users"', self.users_html)
        self.assertIn('data-i18n="protected"', self.users_html)

        # Check renderPermMatrix function exists
        self.assertIn("function renderPermMatrix", self.users_html)
        self.assertIn("perm_view_all_records", self.users_html)
        self.assertIn("perm_add_blotter_entry", self.users_html)
        self.assertIn("perm_edit_any_record", self.users_html)
        self.assertIn("perm_delete_records", self.users_html)
        self.assertIn("perm_archive_records", self.users_html)
        self.assertIn("perm_generate_reports", self.users_html)
        self.assertIn("perm_view_analytics", self.users_html)
        self.assertIn("perm_manage_users", self.users_html)
        self.assertIn("perm_retrain_ml_model", self.users_html)
        self.assertIn("perm_import_csv_excel", self.users_html)
        self.assertIn("perm_system_settings", self.users_html)

    def test_i18n_dictionary_symmetry_and_values(self):
        """Verify all new keys are present and symmetric between en and tl."""
        expected_keys = [
            "search_records_placeholder",
            "search_users_placeholder",
            "welcome_overview",
            "total_blotters",
            "blotter_entries_on_file",
            "incident_reports",
            "new_this_week",
            "pending_settlement",
            "awaiting_settlement",
            "resolved_cases",
            "resolved_lowercase",
            "risk_forecast",
            "risk_rankings_title",
            "risk_hotspots_desc",
            "manage_blotter_records",
            "recent_blotter_entries",
            "resolution_rate",
            "view_all_arrow",
            "quick_actions",
            "quick_blotter_records",
            "quick_new_incident",
            "quick_monitor_settlement",
            "quick_generate_report",
            "quick_import_census",
            "quick_users_roles",
            "role_permission_matrix",
            "th_permission",
            "role_col_admin",
            "role_col_captain",
            "role_col_officer",
            "role_col_encoder",
            "perm_view_all_records",
            "perm_add_blotter_entry",
            "perm_edit_any_record",
            "perm_delete_records",
            "perm_archive_records",
            "perm_generate_reports",
            "perm_view_analytics",
            "perm_manage_users",
            "perm_retrain_ml_model",
            "perm_import_csv_excel",
            "perm_system_settings",
            "protected",
            "system_users",
        ]

        en_match = re.search(r"en:\s*\{(.*?)\},\s*tl:\s*\{", self.app_js, re.DOTALL)
        self.assertIsNotNone(en_match)
        en_block = en_match.group(1)

        tl_match = re.search(r"tl:\s*\{(.*?)\}\s*\n\};", self.app_js, re.DOTALL)
        self.assertIsNotNone(tl_match)
        tl_block = tl_match.group(1)

        en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", en_block, re.MULTILINE))
        tl_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", tl_block, re.MULTILINE))

        for k in expected_keys:
            self.assertIn(k, en_keys, f"Missing key {k} in en dictionary")
            self.assertIn(k, tl_keys, f"Missing key {k} in tl dictionary")


if __name__ == "__main__":
    unittest.main()
