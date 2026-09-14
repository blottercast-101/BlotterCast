import os
import unittest


class TestCertificateResponsiveScaling(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")
        with open(self.styles_path, "r", encoding="utf-8") as f:
            self.styles_css = f.read()

        self.js_path = os.path.join(self.base_dir, "frontend", "public", "js", "certificates.js")
        with open(self.js_path, "r", encoding="utf-8") as f:
            self.js_content = f.read()

        self.templates = {
            "clearance": os.path.join(self.base_dir, "frontend", "clearance.html"),
            "residency": os.path.join(self.base_dir, "frontend", "residency.html"),
            "non_residency": os.path.join(self.base_dir, "frontend", "non_residency.html"),
            "indigency": os.path.join(self.base_dir, "frontend", "indigency.html"),
        }

    def test_01_all_four_templates_have_responsive_viewport_wrapper(self):
        """Verify all 4 certificate templates include .certificate-preview-viewport and .certificate-paper."""
        for name, path in self.templates.items():
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            self.assertIn("certificate-preview-viewport", html, f"{name}.html missing certificate-preview-viewport class")
            self.assertIn("certificate-paper", html, f"{name}.html missing certificate-paper class")
            self.assertIn('data-base-width="794"', html, f"{name}.html missing data-base-width attribute")
            self.assertIn('id="certPrint"', html, f"{name}.html missing id='certPrint'")
            self.assertIn('id="printableCertificate"', html, f"{name}.html missing id='printableCertificate'")
            self.assertIn("overflow-hidden", html, f"{name}.html missing overflow-hidden on preview container")
            self.assertIn("transition-transform", html, f"{name}.html missing transition-transform on sheet")

    def test_02_stylesheet_contains_screen_and_print_rules(self):
        """Verify frontend/styles.css contains .certificate-preview-viewport and .certificate-paper in screen and print."""
        self.assertIn(".certificate-preview-viewport", self.styles_css)
        self.assertIn(".certificate-paper", self.styles_css)

        # Print media fidelity
        self.assertIn("@media print", self.styles_css)
        self.assertIn("transform: none !important;", self.styles_css)

        # Ensure .certificate-preview-viewport in print has overflow: visible and height: auto
        self.assertIn(".certificate-preview-viewport", self.styles_css)
        self.assertIn("overflow: visible !important;", self.styles_css)

    def test_03_certificates_js_contains_auto_scaling_and_observers(self):
        """Verify certificates.js defines fitCertificatePreview with resize and ResizeObserver bindings."""
        self.assertIn("function fitCertificatePreview()", self.js_content)
        self.assertIn("document.querySelectorAll('.certificate-preview-viewport')", self.js_content)
        self.assertIn("scale = availableWidth / baseWidth", self.js_content)
        self.assertIn("sheet.style.transform = `scale(${scale})`", self.js_content)
        self.assertIn("sheet.style.transformOrigin = 'top center'", self.js_content)
        self.assertIn("window.addEventListener('resize', fitCertificatePreview)", self.js_content)
        self.assertIn("ResizeObserver", self.js_content)
        self.assertIn("window.fitCertificatePreview = fitCertificatePreview", self.js_content)
        self.assertIn("fitCertificatePreview,", self.js_content)


if __name__ == "__main__":
    unittest.main()
