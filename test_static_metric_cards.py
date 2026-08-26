import unittest


class TestStaticMetricCards(unittest.TestCase):
    def test_css_guards_present(self):
        css_files = ["frontend/styles.css", "frontend/public/css/style.css"]
        for cpath in css_files:
            with open(cpath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("cursor: default !important;", content)
                self.assertIn(".stat-card:not([role=\"button\"]):not(a):not(.clickable-card)", content)
                self.assertIn("transform: none !important;", content)

    def test_dashboard_heatmap_trends_cards_static(self):
        templates = [
            "frontend/dashboard.html",
            "frontend/heatmap.html",
            "frontend/trends.html",
        ]
        for tpath in templates:
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("cursor-default", content)
                # Ensure no hover scale or hover elevation classes on metric cards
                self.assertNotIn("hover:scale-", content)
                self.assertNotIn("hover:-translate-y-", content)

    def test_heatmap_metadata_badges_inside_container(self):
        with open("frontend/heatmap.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("heatmapBadgeBarangay", content)
            self.assertIn("heatmapBadgeMunicipality", content)
            self.assertIn("Mapulang Lupa", content)
            self.assertIn("Pandi", content)
            self.assertIn("Source: <span class=\"font-medium text-[#064e3b]\">Incident Report</span>", content)
            self.assertIn("mapulang-lupa.geojson", content)


if __name__ == "__main__":
    unittest.main()
