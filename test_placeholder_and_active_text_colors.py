import unittest
import os
import re


class TestPlaceholderAndActiveTextColors(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.base_dir, 'frontend', 'styles.css'), 'r', encoding='utf-8') as f:
            self.styles_css = f.read()

    def test_global_placeholder_css_rules(self):
        # 1. Global placeholder rule exists with #52796f and 0.75 opacity
        self.assertIn('#52796f', self.styles_css)
        self.assertTrue(
            'color: #52796f !important;' in self.styles_css,
            "Placeholder color #52796f !important should be present in styles.css"
        )
        self.assertTrue(
            'opacity: 0.75 !important;' in self.styles_css,
            "Placeholder opacity 0.75 !important should be present in styles.css"
        )

    def test_active_typing_text_color_css_rules(self):
        # 2. Input/textarea/select active text color is #1e3a2b
        self.assertIn('color: #1e3a2b !important;', self.styles_css)
        
        # Check input, textarea, select rules
        self.assertTrue(
            re.search(r'input,\s*textarea,\s*select', self.styles_css),
            "input, textarea, select grouping rule should be in styles.css"
        )
        self.assertTrue(
            re.search(r'input:focus,\s*textarea:focus,\s*select:focus', self.styles_css),
            "input:focus, textarea:focus, select:focus rule should be in styles.css"
        )

    def test_select_placeholder_and_option_rules(self):
        # 3. Select invalid/placeholder and option styling
        self.assertIn('select:invalid', self.styles_css)
        self.assertIn('select option', self.styles_css)
        self.assertIn('.bc-select-value.bc-select-placeholder', self.styles_css)
        self.assertIn('.bc-select-trigger', self.styles_css)

    def test_filter_and_search_inputs_styling(self):
        # 4. Filter and search input classes are covered
        self.assertIn('.filter-input::placeholder', self.styles_css)
        self.assertIn('.search-input::placeholder', self.styles_css)
        self.assertIn('.form-input::placeholder', self.styles_css)


if __name__ == '__main__':
    unittest.main()
