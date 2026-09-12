import unittest
import re

class TestWizardButtonsAndPlaceholders(unittest.TestCase):
    def setUp(self):
        with open("frontend/users.html", "r", encoding="utf-8") as f:
            self.users_html = f.read()
        with open("frontend/styles.css", "r", encoding="utf-8") as f:
            self.styles_css = f.read()

    def test_email_placeholders_updated(self):
        self.assertNotIn("email@barangay.gov", self.users_html)
        self.assertIn('id="wiz_email"', self.users_html)
        self.assertIn('placeholder="yourname@gmail.com"', self.users_html)
        self.assertIn('id="uf_email"', self.users_html)

    def test_wizard_footer_buttons_right_aligned(self):
        # Add User Wizard Step 1: Cancel + Next
        step1_match = re.search(
            r'id="wiz_view_step_1".*?<div class="flex items-center justify-end gap-3 pt-4 border-t border-forest-100/80 mt-6">\s*<button[^>]*>Cancel</button>\s*<button[^>]*>.*?Next.*?</div>',
            self.users_html,
            re.DOTALL
        )
        self.assertIsNotNone(step1_match, "Step 1 buttons must be right-aligned with Cancel and Next grouped")

        # Add User Wizard Step 2: Back + Next
        step2_match = re.search(
            r'id="wiz_view_step_2".*?<div class="flex items-center justify-end gap-3 pt-4 border-t border-forest-100/80 mt-6">\s*<button[^>]*>.*?Back.*?</button>\s*<button[^>]*>.*?Next.*?</div>',
            self.users_html,
            re.DOTALL
        )
        self.assertIsNotNone(step2_match, "Step 2 buttons must be right-aligned with Back and Next grouped")

        # Add User Wizard Step 3: Back + Save User
        step3_match = re.search(
            r'id="wiz_view_step_3".*?<div class="flex items-center justify-end gap-3 pt-4 border-t border-forest-100/80 mt-6">\s*<button[^>]*>.*?Back.*?</button>\s*<button[^>]*id="btnSaveWizardUser"[^>]*>.*?Save User.*?</div>',
            self.users_html,
            re.DOTALL
        )
        self.assertIsNotNone(step3_match, "Step 3 buttons must be right-aligned with Back and Save User grouped")

    def test_button_color_classes(self):
        # Secondary action button classes
        self.assertIn("bg-[#eef6f2]", self.users_html)
        self.assertIn("border-[#c6dfd4]", self.users_html)
        self.assertIn("text-[#2d5a43]", self.users_html)
        # Primary action button classes
        self.assertIn("bg-[#1e4d36]", self.users_html)
        self.assertIn("hover:bg-[#163c29]", self.users_html)

    def test_global_placeholder_css(self):
        self.assertIn("::placeholder", self.styles_css)
        self.assertIn("input::placeholder", self.styles_css)
        self.assertIn("textarea::placeholder", self.styles_css)
        self.assertIn("#52796f", self.styles_css)
        self.assertRegex(self.styles_css, r'color:\s*#52796f\s*!important')
        self.assertRegex(self.styles_css, r'opacity:\s*0\.7\s*!important')

if __name__ == "__main__":
    unittest.main()
