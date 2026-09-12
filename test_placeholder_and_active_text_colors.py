import unittest
import os
import re


class TestPlaceholderAndActiveTextColors(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.base_dir, 'frontend', 'styles.css'), 'r', encoding='utf-8') as f:
            self.styles_css = f.read()

    def test_global_placeholder_css_rules(self):
        # 1. Global placeholder rule exists with #52796f and opacity 1
        self.assertIn('#52796f', self.styles_css)
        self.assertTrue(
            'color: #52796f !important;' in self.styles_css,
            "Placeholder color #52796f !important should be present in styles.css"
        )
        self.assertTrue(
            'opacity: 1 !important;' in self.styles_css,
            "Placeholder opacity 1 !important should be present in styles.css"
        )

    def test_active_typing_text_color_css_rules(self):
        # 2. Input/textarea/search-input active text color is #52796f
        self.assertIn('color: #52796f !important;', self.styles_css)
        self.assertTrue(
            re.search(r'input,\s*textarea,\s*\.search-input', self.styles_css),
            "input, textarea, .search-input rule should be in styles.css"
        )
        self.assertTrue(
            re.search(r'input:focus,\s*textarea:focus', self.styles_css),
            "input:focus, textarea:focus rule should be in styles.css"
        )

    def test_select_typography_and_ghost_overlay_guards(self):
        # 3. Select invalid/placeholder and option styling in #52796f
        self.assertIn('select option', self.styles_css)
        self.assertIn('.bc-select-value.bc-select-placeholder', self.styles_css)
        self.assertIn('.bc-select-trigger', self.styles_css)
        self.assertIn('.bc-select-native', self.styles_css)
        self.assertIn('select::-ms-expand', self.styles_css)

    def test_filter_and_search_inputs_styling(self):
        # 4. Filter and search input classes are covered
        self.assertIn('.filter-input::placeholder', self.styles_css)
        self.assertIn('.search-input::placeholder', self.styles_css)
        self.assertIn('.form-input::placeholder', self.styles_css)


if __name__ == '__main__':
    unittest.main()

