import unittest
import os
import re

class TestTrendsPredictionsPaginationI18n(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.app_path = os.path.join(self.base_dir, "frontend", "app.js")
        self.i18n_path = os.path.join(self.base_dir, "frontend", "i18n.js")
        self.heatmap_path = os.path.join(self.base_dir, "frontend", "heatmap.html")
        self.trends_path = os.path.join(self.base_dir, "frontend", "trends.html")
        self.predictions_path = os.path.join(self.base_dir, "frontend", "predictions.html")
        self.users_path = os.path.join(self.base_dir, "frontend", "users.html")
        self.reports_path = os.path.join(self.base_dir, "frontend", "reports.html")

    def test_01_pagination_formatting_incidents(self):
        """Verify bcFormatPaginationInfo handles unit='incidents' in app.js and is called in heatmap.html."""
        with open(self.app_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        # Check function supports incidents unit
        self.assertIn("function bcFormatPaginationInfo", app_js)
        self.assertIn("normalizedUnit === 'incidents'", app_js)
        self.assertIn("Ipinapakita ang ${from} hanggang ${to} sa ${tot} na insidente", app_js)
        self.assertIn("Showing ${from} to ${to} of ${tot} incident", app_js)

        # Check heatmap.html renders pagination with unit 'incidents'
        with open(self.heatmap_path, "r", encoding="utf-8") as f:
            heatmap_html = f.read()

        self.assertIn('data-i18n="showing_zero_incidents"', heatmap_html)
        self.assertIn("bcFormatPaginationInfo(start + 1, Math.min(start + TABLE_PAGE_SIZE, total), total, 'incidents')", heatmap_html)

    def test_02_trends_html_data_i18n_and_scripts(self):
        """Verify trends.html has data-i18n attributes and localized dynamic rendering."""
        with open(self.trends_path, "r", encoding="utf-8") as f:
            trends_html = f.read()

        required_keys = [
            'data-i18n="trends_comparative_analytics"',
            'data-i18n="trends_subtitle"',
            'data-i18n="total_incidents_metric"',
            'data-i18n="peak_month"',
            'data-i18n="settlement_rate"',
            'data-i18n="elevated_to_blotter"',
            'data-i18n="monthly_comparative_pipeline"',
            'data-i18n="monthly_pipeline_desc"',
            'data-i18n="category_severity"',
            'data-i18n="category_distribution"',
            'data-i18n="zonal_matrix_title"',
            'data-i18n="zonal_matrix_subtitle"',
            'data-i18n="th_zone_substation"',
            'data-i18n="th_total_incidents"',
            'data-i18n="th_elevated_to_blotter"',
            'data-i18n="th_elevation_rate"',
            'data-i18n="th_resolved_cases"',
            'data-i18n="th_status_col"',
            'data-i18n="incidents_by_day_of_week"',
            'data-i18n="weekly_occurrence_distribution"',
            'data-i18n="top_incident_categories"',
            'data-i18n="ranked_by_volume"',
        ]
        for key in required_keys:
            self.assertIn(key, trends_html, f"Missing {key} in trends.html")

        # Script checks
        self.assertIn("isFilipino", trends_html)
        self.assertIn("MONTHS_TL", trends_html)
        self.assertIn("DAYS_TL", trends_html)
        self.assertIn("CATEGORY_TL", trends_html)
        self.assertIn("MATAAS NA PAG-AAKYAT", trends_html)
        self.assertIn("MAAYOS NA KONTROL", trends_html)
        self.assertIn("Tirahan", trends_html)
        self.assertIn("bc:language-changed", trends_html)

    def test_03_predictions_html_data_i18n_and_scripts(self):
        """Verify predictions.html has data-i18n attributes and dynamic localization."""
        with open(self.predictions_path, "r", encoding="utf-8") as f:
            pred_html = f.read()

        required_keys = [
            'data-i18n="predictive_insights"',
            'data-i18n="predictive_insights_desc"',
            'data-i18n="loading_latest_insights"',
            'data-i18n="retrain_model_btn"',
            'data-i18n="high_risk_zones"',
            'data-i18n="moderate_risk_zones"',
            'data-i18n="low_risk_zones"',
            'data-i18n="all_zones_1_7"',
            'data-i18n="next_7_days"',
            'data-i18n="next_14_days"',
            'data-i18n="patrol_recommendations"',
            'data-i18n="category_forecast_by_zone"',
            'data-i18n="category_forecast_desc"',
            'data-i18n="predicted_risk_by_zone"',
            'data-i18n="th_pred_zone"',
            'data-i18n="th_pred_hotspot"',
            'data-i18n="th_pred_risk"',
            'data-i18n="th_pred_top_cat"',
            'data-i18n="th_pred_peak_time"',
        ]
        for key in required_keys:
            self.assertIn(key, pred_html, f"Missing {key} in predictions.html")

        # Script checks
        self.assertIn("isFilipino", pred_html)
        self.assertIn("Pagkakaroon ng Insidente", pred_html)
        self.assertIn("Uri ng Insidente", pred_html)
        self.assertIn("Panganib sa Hotspot", pred_html)
        self.assertIn("Katumpakan", pred_html)
        self.assertIn("F1 Score", pred_html)
        self.assertIn("Kritikal", pred_html)
        self.assertIn("Tumataas", pred_html)
        self.assertIn("Bumababa", pred_html)
        self.assertIn("Matatag", pred_html)
        self.assertIn("bc:language-changed", pred_html)

    def test_04_system_and_audit_settings_i18n(self):
        """Verify users.html and reports.html have requested data-i18n tags."""
        with open(self.users_path, "r", encoding="utf-8") as f:
            users_html = f.read()
        self.assertIn('data-i18n="manage_personnel_accounts"', users_html)
        self.assertIn('data-i18n="recent_audit_log"', users_html)

        with open(self.reports_path, "r", encoding="utf-8") as f:
            reports_html = f.read()
        self.assertIn('data-i18n="generate_reports_subtitle"', reports_html)

    def test_05_i18n_dictionary_symmetry(self):
        """Verify that all new keys exist in both en and tl in i18n.js and app.js."""
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            i18n_content = f.read()
        with open(self.app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        test_keys = [
            "showing_zero_incidents",
            "trends_comparative_analytics",
            "trends_subtitle",
            "total_incidents_metric",
            "peak_month",
            "settlement_rate",
            "elevated_to_blotter",
            "monthly_comparative_pipeline",
            "monthly_pipeline_desc",
            "category_severity",
            "category_distribution",
            "zonal_matrix_title",
            "zonal_matrix_subtitle",
            "th_zone_substation",
            "th_total_incidents",
            "th_elevated_to_blotter",
            "th_elevation_rate",
            "th_resolved_cases",
            "th_status_col",
            "incidents_by_day_of_week",
            "weekly_occurrence_distribution",
            "top_incident_categories",
            "ranked_by_volume",
            "predictive_insights",
            "predictive_insights_desc",
            "loading_latest_insights",
            "retrain_model_btn",
            "high_risk_zones",
            "moderate_risk_zones",
            "low_risk_zones",
            "all_zones_1_7",
            "next_7_days",
            "next_14_days",
            "patrol_recommendations",
            "category_forecast_by_zone",
            "category_forecast_desc",
            "predicted_risk_by_zone",
            "th_pred_zone",
            "th_pred_hotspot",
            "th_pred_expected",
            "th_pred_risk",
            "th_pred_top_cat",
            "th_pred_peak_time",
            "th_pred_trend",
            "manage_personnel_accounts",
            "recent_audit_log",
            "generate_reports_subtitle"
        ]

        for k in test_keys:
            # Check pattern: k: or "k":
            pattern = rf'(?:["\']?{k}["\']?\s*:)'
            self.assertTrue(bool(re.search(pattern, i18n_content)), f"Key {k} missing in i18n.js")
            self.assertTrue(bool(re.search(pattern, app_content)), f"Key {k} missing in app.js")

if __name__ == "__main__":
    unittest.main()
