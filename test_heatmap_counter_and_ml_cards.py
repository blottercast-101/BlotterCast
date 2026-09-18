import unittest
import os
import re

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


class TestHeatmapCounterAndMlCards(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FRONTEND_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.app_js = f.read()
        with open(os.path.join(FRONTEND_DIR, "i18n.js"), "r", encoding="utf-8") as f:
            self.i18n_js = f.read()
        with open(os.path.join(FRONTEND_DIR, "heatmap.html"), "r", encoding="utf-8") as f:
            self.heatmap_html = f.read()
        with open(os.path.join(FRONTEND_DIR, "predictions.html"), "r", encoding="utf-8") as f:
            self.predictions_html = f.read()

    def test_bc_format_pagination_info_pattern(self):
        """Verify bcFormatPaginationInfo outputs 'Ipinapakita ang {from} hanggang {to} sa {total} na insidente'."""
        self.assertIn("function bcFormatPaginationInfo", self.app_js)
        self.assertIn("Ipinapakita ang ${from} hanggang ${to} sa ${tot} na insidente", self.app_js)
        self.assertIn("Showing ${from} to ${to} of ${tot} incident", self.app_js)
        self.assertIn("function bcInterpolatePagination", self.app_js)

    def test_apply_language_translation_pagination_safeguard(self):
        """Verify applyLanguageTranslation does not overwrite non-zero pagination numbers with 0/O."""
        self.assertIn("key === 'showing_zero_incidents'", self.app_js)
        self.assertIn("numMatch && Number(numMatch[3]) > 0", self.app_js)
        self.assertIn("Ipinapakita ang ${from} hanggang ${to} sa ${total} na insidente", self.app_js)

    def test_heatmap_table_pagination_listeners(self):
        """Verify heatmap.html listens to language changes and dynamically formats pagination."""
        self.assertIn("bc:language-changed", self.heatmap_html)
        self.assertIn("bc-language-changed", self.heatmap_html)
        self.assertIn("bcFormatPaginationInfo", self.heatmap_html)

    def test_ml_prediction_card_titles_and_submetrics(self):
        """Verify ML Prediction Metric Cards use official Tagalog terms in predictions.html."""
        # 1. Card Titles
        self.assertIn("Pagkakaroon ng Insidente", self.predictions_html)
        self.assertIn("Uri ng Insidente", self.predictions_html)
        self.assertIn("Panganib sa Hotspot", self.predictions_html)

        # 2. Card Sub-metrics
        self.assertIn("Katumpakan", self.predictions_html)
        self.assertIn("F1 Score", self.predictions_html)

        # 3. Dynamic language change listener
        self.assertIn("bc:language-changed", self.predictions_html)
        self.assertIn("bc-language-changed", self.predictions_html)

    def test_dictionary_and_translations_in_i18n_and_app(self):
        """Verify exact terms in i18n.js and app.js."""
        # i18n.js tl block
        self.assertIn('incident_occurrence_task: "Pagkakaroon ng Insidente"', self.i18n_js)
        self.assertIn('incident_type_task: "Uri ng Insidente"', self.i18n_js)
        self.assertIn('hotspot_risk_task: "Panganib sa Hotspot"', self.i18n_js)
        self.assertIn('accuracy_metric: "Katumpakan"', self.i18n_js)
        self.assertIn('f1_score_metric: "F1 Score"', self.i18n_js)
        self.assertIn('showing_zero_incidents: "Ipinapakita ang 0 hanggang 0 sa 0 na insidente"', self.i18n_js)

        # app.js tl block
        self.assertIn('incident_occurrence_task: "Pagkakaroon ng Insidente"', self.app_js)
        self.assertIn('incident_type_task: "Uri ng Insidente"', self.app_js)
        self.assertIn('hotspot_risk_task: "Panganib sa Hotspot"', self.app_js)
        self.assertIn('accuracy_metric: "Katumpakan"', self.app_js)
        self.assertIn('f1_score_metric: "F1 Score"', self.app_js)
        self.assertIn('showing_zero_incidents: "Ipinapakita ang 0 hanggang 0 sa 0 na insidente"', self.app_js)

        # app.js BC_TRANSLATIONS.fil
        self.assertIn('"INCIDENT OCCURRENCE": "Pagkakaroon ng Insidente"', self.app_js)
        self.assertIn('"INCIDENT TYPE": "Uri ng Insidente"', self.app_js)
        self.assertIn('"HOTSPOT RISK": "Panganib sa Hotspot"', self.app_js)
        self.assertIn('"Accuracy": "Katumpakan"', self.app_js)
        self.assertIn('"F1 Score": "F1 Score"', self.app_js)

    def test_i18n_key_symmetry(self):
        """Verify 100% key symmetry between en and tl in i18n.js and app.js."""
        for name, content in [("i18n.js", self.i18n_js), ("app.js", self.app_js)]:
            en_match = re.search(r"en:\s*\{(.*?)\},\s*tl:\s*\{", content, re.DOTALL)
            self.assertIsNotNone(en_match, f"Could not find 'en' block in {name}")
            en_block = en_match.group(1)

            tl_match = re.search(r"tl:\s*\{(.*?)\}\s*\n\};", content, re.DOTALL)
            self.assertIsNotNone(tl_match, f"Could not find 'tl' block in {name}")
            tl_block = tl_match.group(1)

            en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", en_block, re.MULTILINE))
            tl_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", tl_block, re.MULTILINE))

            self.assertEqual(en_keys - tl_keys, set(), f"Missing in tl for {name}: {en_keys - tl_keys}")
            self.assertEqual(tl_keys - en_keys, set(), f"Missing in en for {name}: {tl_keys - en_keys}")


if __name__ == "__main__":
    unittest.main()
