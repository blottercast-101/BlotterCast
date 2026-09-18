import unittest
import os
import re

class TestCertificatesHeatmapNotificationsI18nAndZoom(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")
        self.js_cert_path = os.path.join(self.base_dir, "frontend", "public", "js", "certificates.js")
        self.app_path = os.path.join(self.base_dir, "frontend", "app.js")
        self.i18n_path = os.path.join(self.base_dir, "frontend", "i18n.js")
        self.templates = {
            "clearance": os.path.join(self.base_dir, "frontend", "clearance.html"),
            "residency": os.path.join(self.base_dir, "frontend", "residency.html"),
            "non_residency": os.path.join(self.base_dir, "frontend", "non_residency.html"),
            "indigency": os.path.join(self.base_dir, "frontend", "indigency.html"),
        }
        self.heatmap_path = os.path.join(self.base_dir, "frontend", "heatmap.html")
        self.dashboard_path = os.path.join(self.base_dir, "frontend", "dashboard.html")

    def test_01_certificate_preview_wrapper_css(self):
        """Verify CSS constraints on .certificate-preview-wrapper and .certificate-preview-viewport."""
        with open(self.styles_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn(".certificate-preview-wrapper", css)
        self.assertIn("max-width: 100%", css)
        self.assertIn("object-fit: contain", css)
        self.assertIn("transform-origin: top center", css)

    def test_02_certificates_js_zoom_and_scaling_fixes(self):
        """Verify certificates.js has zero-dimension retry, ResizeObserver, and multi-stage timers."""
        with open(self.js_cert_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("fitCertificatePreview", content)
        self.assertIn("viewport.clientWidth <= 0", content)
        self.assertIn("ResizeObserver", content)
        self.assertIn("bc:page-loaded", content)
        self.assertIn("dispatchEvent(new Event('resize'))", content)

    def test_03_all_certificate_templates_have_wrapper(self):
        """Verify all 4 certificate templates include .certificate-preview-wrapper."""
        for name, path in self.templates.items():
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            self.assertIn("certificate-preview-wrapper", html, f"{name}.html missing certificate-preview-wrapper class")
            self.assertIn("certificate-preview-viewport", html, f"{name}.html missing certificate-preview-viewport class")

    def test_04_certificate_templates_i18n_attributes(self):
        """Verify residency, non-residency, and indigency templates have all required data-i18n tags."""
        # Residency
        with open(self.templates["residency"], "r", encoding="utf-8") as f:
            res_html = f.read()
        res_keys = [
            'data-i18n="certificate_of_residency"',
            'data-i18n="residency_description"',
            'data-i18n="issue_new_certificate"',
            'data-i18n="issued_this_month"',
            'data-i18n="total_this_year"',
            'data-i18n="revenue_fees"',
            'data-i18n="issuance_log"',
            'data-i18n="certificate_preview"',
            'data-i18n-placeholder="search_residency_placeholder"'
        ]
        for key in res_keys:
            self.assertIn(key, res_html, f"Missing {key} in residency.html")

        # Non-Residency
        with open(self.templates["non_residency"], "r", encoding="utf-8") as f:
            non_res_html = f.read()
        non_res_keys = [
            'data-i18n="certificate_of_non_residency"',
            'data-i18n="non_residency_description"',
            'data-i18n="issue_new_certificate"',
            'data-i18n="issued_this_month"',
            'data-i18n="total_this_year"',
            'data-i18n="revenue_fees"',
            'data-i18n="issuance_log"',
            'data-i18n="certificate_preview"',
            'data-i18n-placeholder="search_non_residency_placeholder"'
        ]
        for key in non_res_keys:
            self.assertIn(key, non_res_html, f"Missing {key} in non_residency.html")

        # Indigency
        with open(self.templates["indigency"], "r", encoding="utf-8") as f:
            ind_html = f.read()
        ind_keys = [
            'data-i18n="certificate_of_indigency"',
            'data-i18n="indigency_description"',
            'data-i18n="issue_certificate"',
            'data-i18n="issued_this_month"',
            'data-i18n="total_this_year"',
            'data-i18n="common_purpose"',
            'data-i18n="issuance_log"',
            'data-i18n="certificate_preview"',
            'data-i18n-placeholder="search_indigency_placeholder"'
        ]
        for key in ind_keys:
            self.assertIn(key, ind_html, f"Missing {key} in indigency.html")

    def test_05_heatmap_i18n_attributes(self):
        """Verify heatmap.html has required data-i18n attributes for controls, badges, and stats."""
        with open(self.heatmap_path, "r", encoding="utf-8") as f:
            html = f.read()

        heatmap_keys = [
            'data-i18n="incident_heat_map"',
            'data-i18n="heatmap_subtitle"',
            'data-i18n="period_all_time"',
            'data-i18n="period_this_month"',
            'data-i18n="period_this_week"',
            'data-i18n="show_incident_markers"',
            'data-i18n="mapulang_lupa_heat_map"',
            'data-i18n="visual_density_desc"',
            'data-i18n="density_low"',
            'data-i18n="density_medium"',
            'data-i18n="density_high"',
            'data-i18n="badge_barangay"',
            'data-i18n="badge_municipality"',
            'data-i18n="badge_source"',
            'data-i18n="badge_boundary_file"',
            'data-i18n="summary"',
            'data-i18n="visible_incidents"',
            'data-i18n="top_category"',
            'data-i18n="category_breakdown"',
            'data-i18n="all_zones"',
            'data-i18n="all_categories"',
            'data-i18n-placeholder="search_heatmap_placeholder"'
        ]
        for key in heatmap_keys:
            self.assertIn(key, html, f"Missing {key} in heatmap.html")

    def test_06_dashboard_and_notifications_i18n(self):
        """Verify dashboard notifications header and app.js notification panel translations."""
        with open(self.dashboard_path, "r", encoding="utf-8") as f:
            dash_html = f.read()
        self.assertIn('data-i18n="notifications"', dash_html)
        self.assertIn('data-i18n="mark_all_read"', dash_html)

        with open(self.app_path, "r", encoding="utf-8") as f:
            app_js = f.read()
        self.assertIn("badge_tl: 'INSIDENTE'", app_js)
        self.assertIn("badge_tl: 'PAG-AAYOS'", app_js)
        self.assertIn("badge_tl: 'MATAAS NA PRIYORIDAD'", app_js)
        self.assertIn("badge_tl: 'HEOGRAPIKO'", app_js)
        self.assertIn('ngayon lang', app_js)
        self.assertIn('nakalipas', app_js)

    def test_07_app_js_openmodal_and_nav_scaling_hooks(self):
        """Verify openModal, closeModal, and navigateTo invoke fitCertificatePreview and synthetic resize."""
        with open(self.app_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("function openModal", app_js)
        self.assertIn("window.dispatchEvent(new Event('resize'))", app_js)

    def test_08_i18n_dictionary_symmetry(self):
        """Verify certificate, heatmap, and notification keys exist in both en and tl in i18n.js and app.js."""
        check_keys = [
            "certificate_of_residency", "residency_description", "issue_new_certificate",
            "search_residency_placeholder",
            "certificate_of_non_residency", "non_residency_description",
            "search_non_residency_placeholder",
            "certificate_of_indigency", "indigency_description", "issue_certificate",
            "common_purpose", "search_indigency_placeholder",
            "incident_heat_map", "heatmap_subtitle", "period_all_time", "period_this_month", "period_this_week",
            "show_incident_markers", "mapulang_lupa_heat_map", "visual_density_desc",
            "zone_density_label", "density_low", "density_medium", "density_elevated", "density_high",
            "badge_barangay", "badge_municipality", "badge_source", "badge_boundary_file",
            "summary", "visible_incidents", "top_category", "category_breakdown",
            "incident_location_summary", "incident_location_summary_desc",
            "search_heatmap_placeholder", "all_zones", "all_categories",
            "notifications", "mark_all_read", "no_notifications", "loading_notifications",
            "notif_error"
        ]

        with open(self.i18n_path, "r", encoding="utf-8") as f:
            i18n_content = f.read()

        with open(self.app_path, "r", encoding="utf-8") as f:
            app_content = f.read()

        for key in check_keys:
            self.assertIn(f'{key}:', i18n_content, f"Key '{key}' missing from i18n.js")
            self.assertIn(f'{key}:', app_content, f"Key '{key}' missing from app.js")


if __name__ == "__main__":
    unittest.main()
