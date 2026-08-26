import unittest
import json
import os


class TestDynamicDensityBreaks(unittest.TestCase):
    def test_heatmap_js_contains_dynamic_breaks_and_colors(self):
        js_path = "frontend/public/js/heatmap.js"
        self.assertTrue(os.path.exists(js_path))
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("function computeDensityBreaks", content)
            self.assertIn("function getDynamicZoneColor", content)
            self.assertIn("function updateDynamicLegendUI", content)
            self.assertIn("function getDynamicZoneStyle", content)
            self.assertIn("lowMax", content)
            self.assertIn("medMax", content)
            self.assertIn("elevMax", content)
            self.assertIn("#EF4444", content) # High Red
            self.assertIn("#F97316", content) # Elevated Orange
            self.assertIn("#F59E0B", content) # Medium Yellow
            self.assertIn("#10B981", content) # Low Green

    def test_heatmap_html_includes_script_and_dynamic_tiers(self):
        html_path = "frontend/heatmap.html"
        self.assertTrue(os.path.exists(html_path))
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn('<script src="public/js/heatmap.js"></script>', content)
            self.assertIn("computeDynamicDensityTiers", content)
            self.assertIn("updateLegendUI", content)


if __name__ == "__main__":
    unittest.main()
