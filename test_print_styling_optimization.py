import os
import re
import unittest


class TestPrintStylingOptimization(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")
        with open(self.styles_path, "r", encoding="utf-8") as f:
            self.styles_css = f.read()

        self.templates = {
            "clearance": os.path.join(self.base_dir, "frontend", "clearance.html"),
            "residency": os.path.join(self.base_dir, "frontend", "residency.html"),
            "non_residency": os.path.join(self.base_dir, "frontend", "non_residency.html"),
            "indigency": os.path.join(self.base_dir, "frontend", "indigency.html"),
        }

    def test_01_global_print_rules_in_stylesheet(self):
        """Verify @media print block enforces zero-margin full-bleed rules, chrome hiding, and isolation."""
        self.assertIn("@media print", self.styles_css)

        # 1. Page size and zero margin full-bleed boundaries
        self.assertIn("size: A4 portrait", self.styles_css)
        self.assertIn("margin: 0 !important;", self.styles_css)

        # 2. Hide entire application chrome
        self.assertIn("body *", self.styles_css)
        self.assertIn("visibility: hidden", self.styles_css)

        # 3. Suppress all chrome elements
        for selector in [
            "aside", "header", "nav", "#mainSidebar", "#sidebar",
            "#globalSidebarToggle", ".sidebar", ".no-print",
            ".modal-backdrop", ".modal-header", ".modal-footer",
            "button", ".action-buttons"
        ]:
            self.assertIn(selector, self.styles_css, f"Missing chrome suppression selector: {selector}")

        # 4. Certificate isolation & full-bleed viewport bounds
        self.assertIn("#printableCertificate", self.styles_css)
        self.assertIn(".certificate-container", self.styles_css)
        self.assertIn(".printable-document", self.styles_css)
        self.assertIn("position: fixed !important;", self.styles_css)
        self.assertIn("width: 100vw !important;", self.styles_css)
        self.assertIn("height: 100vh !important;", self.styles_css)

        # 5. Header and footer full-bleed bars & internal padding
        self.assertIn(".certificate-header-bar", self.styles_css)
        self.assertIn(".certificate-footer-bar", self.styles_css)
        self.assertIn(".certificate-body-content", self.styles_css)
        self.assertIn("padding-left: 20mm !important;", self.styles_css)
        self.assertIn("padding-right: 20mm !important;", self.styles_css)

        # 6. html, body overflow hidden for single page enforcement
        self.assertIn("overflow: hidden !important;", self.styles_css)

        # 7. break-inside avoid on signature / certificate blocks
        self.assertIn("break-inside: avoid !important;", self.styles_css)
        self.assertIn("page-break-inside: avoid !important;", self.styles_css)

    def test_02_all_four_certificate_templates_contain_printable_identifiers(self):
        """Verify all 4 certificate templates include #printableCertificate, certificate-container, and printable-document."""
        for name, path in self.templates.items():
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            self.assertIn('id="printableCertificate"', html, f"{name}.html must have id='printableCertificate'")
            self.assertIn("certificate-container", html, f"{name}.html must have 'certificate-container' class")
            self.assertIn("printable-document", html, f"{name}.html must have 'printable-document' class")
            self.assertIn("cert-sheet", html, f"{name}.html must retain 'cert-sheet' class")

    def test_03_all_four_certificate_templates_retain_letterheads_and_signature_blocks(self):
        """Verify letterheads, dynamic fields, and Captain signature blocks remain intact across all 4 templates."""
        for name, path in self.templates.items():
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            # Letterhead image
            self.assertIn("cert-bg", html, f"{name}.html missing letterhead image")

            # Signatory block & captain name binding
            self.assertIn("captain-signatory-block", html, f"{name}.html missing captain-signatory-block")
            self.assertIn("cert-captain-name", html, f"{name}.html missing cert-captain-name")
            self.assertIn("captain-e-signature", html, f"{name}.html missing captain-e-signature")

            # Semantic line fields and body paragraphs
            self.assertIn("cert-line-field", html, f"{name}.html missing cert-line-field")
            self.assertIn("cert-body-paragraph", html, f"{name}.html missing cert-body-paragraph")

    def test_04_fixed_aspect_ratio_a4_paper_container(self):
        """Verify immutable A4 paper architecture, responsive scaling for tablets, and print resets."""
        # 1. Stylesheet rules for .a4-sheet
        self.assertIn(".a4-sheet", self.styles_css)
        self.assertIn("width: 210mm;", self.styles_css)
        self.assertIn("height: 297mm;", self.styles_css)
        self.assertIn(".certificate-viewport-container", self.styles_css)

        # 2. Responsive scaling for tablet/mobile viewports
        self.assertIn("@media screen and (max-width: 1024px)", self.styles_css)
        self.assertIn("transform: scale(0.85);", self.styles_css)
        self.assertIn("@media screen and (max-width: 800px)", self.styles_css)
        self.assertIn("transform: scale(0.72);", self.styles_css)

        # 3. Print reset
        self.assertIn("transform: none !important;", self.styles_css)

        # 4. Template wrappers
        for name, path in self.templates.items():
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            self.assertIn("certificate-viewport-container", html, f"{name}.html must have 'certificate-viewport-container' class")
            self.assertIn("a4-sheet", html, f"{name}.html must have 'a4-sheet' class")


if __name__ == "__main__":
    unittest.main()
