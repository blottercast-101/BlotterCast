import os
import re
import unittest

class TestIncidentElevatedStatusAndBanner(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.incident_html_path = os.path.join(self.base_dir, "frontend", "incident.html")
        self.incidents_js_path = os.path.join(self.base_dir, "frontend", "incidents.js")
        self.public_incidents_js_path = os.path.join(self.base_dir, "frontend", "public", "js", "incidents.js")
        self.app_js_path = os.path.join(self.base_dir, "frontend", "app.js")
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")

        with open(self.incident_html_path, "r", encoding="utf-8") as f:
            self.incident_html = f.read()

        with open(self.incidents_js_path, "r", encoding="utf-8") as f:
            self.incidents_js = f.read()

        with open(self.public_incidents_js_path, "r", encoding="utf-8") as f:
            self.public_incidents_js = f.read()

        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

        with open(self.styles_path, "r", encoding="utf-8") as f:
            self.styles_css = f.read()

    def test_01_get_status_badge_helper(self):
        """Verify getStatusBadge function exists and maps statuses correctly in incidents.js, incident.html, and app.js."""
        for name, code in [
            ("incidents.js", self.incidents_js),
            ("public/js/incidents.js", self.public_incidents_js),
            ("incident.html", self.incident_html),
            ("app.js", self.app_js)
        ]:
            self.assertIn("function getStatusBadge(status)", code, f"{name} must define function getStatusBadge(status)")
            self.assertIn("case 'UNDER INVESTIGATION':", code, f"{name} missing UNDER INVESTIGATION case")
            self.assertIn("'bg-amber-100 text-amber-800 border border-amber-300'", code, f"{name} wrong amber styling")
            self.assertIn("case 'ELEVATED':", code, f"{name} missing ELEVATED case")
            self.assertIn("'bg-red-100 text-red-700 border border-red-200'", code, f"{name} wrong soft red styling for ELEVATED")
            self.assertIn("case 'SETTLED':", code, f"{name} missing SETTLED case")
            self.assertIn("case 'RESOLVED':", code, f"{name} missing RESOLVED case")
            self.assertIn("'bg-emerald-100 text-emerald-800 border border-emerald-300'", code, f"{name} wrong green styling")
            self.assertIn("'bg-gray-100 text-gray-700 border border-gray-200'", code, f"{name} wrong default styling")

    def test_02_incident_table_row_renders_elevated_in_soft_red(self):
        """Verify Incident Reports table row renders ELEVATED badge consistently with getStatusBadge."""
        # Check script tag included
        self.assertIn('<script src="incidents.js"></script>', self.incident_html)

        # Check table row rendering calls getStatusBadge
        table_row_match = re.search(
            r'<td><span class="badge \$\{getStatusBadge\(\(r\.is_blotter \|\| r\.status === [^\)]+\) \? \'ELEVATED\' : r\.status\)\}" style="white-space:nowrap">\$\{\(r\.is_blotter \|\| r\.status === [^\)]+\) \? \'ELEVATED\' : r\.status\}</span></td>',
            self.incident_html
        )
        self.assertIsNotNone(table_row_match, "incident.html table row must evaluate elevated status via getStatusBadge")

        # Verify no hardcoded green/mint class overriding ELEVATED in table rows
        bad_elevated_check = re.search(r'ELEVATED.*?(badge-resolved|status-resolved|bg-emerald)', self.incident_html)
        self.assertIsNone(bad_elevated_check, "Found hardcoded green/mint class associated with ELEVATED in incident.html")

    def test_03_warning_banner_text_only_and_no_lock_icon(self):
        """Verify warning banner in view and edit modals has no lock icon and has clean text-only amber alert box."""
        # 1. Check view modal banner
        self.assertIn('bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs leading-relaxed', self.incident_html)
        self.assertIn('id="bltRefCode"', self.incident_html)
        self.assertIn('This incident is locked because it has been elevated to Blotter Records', self.incident_html)

        # Ensure no lock icon preceding the message in the view modal lockBanner
        view_banner_match = re.search(
            r'const lockBanner = isElevated\s*\?\s*`<div class="mb-4 p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-900 text-xs leading-relaxed">\s*<p>This incident is locked because it has been elevated to Blotter Records \(<span class="font-semibold" id="bltRefCode">',
            self.incident_html
        )
        self.assertIsNotNone(view_banner_match, "view modal lockBanner should match clean text-only structure without lock icon")
        self.assertNotIn('🔒</span>\n          <span>This incident is locked', self.incident_html)

        # 2. Check edit modal banner (if_elevatedLockBanner)
        self.assertIn('id="if_elevatedLockBanner"', self.incident_html)
        banner_div = re.search(r'<div id="if_elevatedLockBanner"[^>]+>', self.incident_html).group(0)
        self.assertIn('bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 leading-relaxed', banner_div)

    def test_04_styles_css_support(self):
        """Verify styles.css supports .status-elevated, .badge-elevated, and .badge.bg-red-100."""
        self.assertIn('.status-elevated', self.styles_css)
        self.assertIn('.badge-elevated', self.styles_css)
        self.assertIn('.badge.bg-red-100', self.styles_css)
        self.assertIn('#fee2e2', self.styles_css)
        self.assertIn('#b91c1c', self.styles_css)
        self.assertIn('#fecaca', self.styles_css)

if __name__ == "__main__":
    unittest.main()
