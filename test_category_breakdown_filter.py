import unittest
import pandas as pd
from ml.engine import EXCLUDED_CATEGORIES, train_type_model, predict_top_category


class TestCategoryBreakdownFilter(unittest.TestCase):
    def test_heatmap_category_exclusion_script(self):
        with open("frontend/heatmap.html", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("EXCLUDED_HEATMAP_CATEGORIES", content)
            self.assertIn("'civil'", content)
            self.assertIn("'crim'", content)
            self.assertIn("'neighborhood dispute'", content)
            self.assertIn("'other'", content)

    def test_ml_engine_category_exclusion(self):
        self.assertIn('civil', EXCLUDED_CATEGORIES)
        self.assertIn('crim', EXCLUDED_CATEGORIES)
        self.assertIn('neighborhood dispute', EXCLUDED_CATEGORIES)
        self.assertIn('other', EXCLUDED_CATEGORIES)

        # Ensure multi-class model training excludes these categories
        data = [
            {'date': '2025-01-01', 'zone': 'Zone 1', 'hour': 10, 'category': 'CIVIL'},
            {'date': '2025-01-02', 'zone': 'Zone 1', 'hour': 11, 'category': 'CRIM'},
            {'date': '2025-01-03', 'zone': 'Zone 1', 'hour': 12, 'category': 'Neighborhood Dispute'},
            {'date': '2025-01-04', 'zone': 'Zone 1', 'hour': 13, 'category': 'Other'},
            {'date': '2025-01-05', 'zone': 'Zone 1', 'hour': 14, 'category': 'Theft'},
            {'date': '2025-01-06', 'zone': 'Zone 1', 'hour': 15, 'category': 'Theft'},
            {'date': '2025-01-07', 'zone': 'Zone 1', 'hour': 16, 'category': 'Physical Assault'},
            {'date': '2025-01-08', 'zone': 'Zone 1', 'hour': 17, 'category': 'Physical Assault'},
        ]
        df = pd.DataFrame(data)
        metrics, model, cols = train_type_model(df)
        if hasattr(model, 'classes_') and len(model.classes_) > 0:
            for cls_name in model.classes_:
                self.assertNotIn(str(cls_name).lower(), EXCLUDED_CATEGORIES)

        # Test predict_top_category never predicts excluded category
        top_cat, prob = predict_top_category(model, cols, 'Zone 1', 1, 14)
        self.assertNotIn(top_cat.lower(), EXCLUDED_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
