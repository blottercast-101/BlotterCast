import re
import unittest


class TestCertificateTypography(unittest.TestCase):
    def test_templates_use_cert_line_field_and_no_raw_underscores(self):
        templates = [
            "frontend/clearance.html",
            "frontend/residency.html",
            "frontend/indigency.html",
            "frontend/non_residency.html",
        ]
        for tpath in templates:
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()

                # 1. Must contain cert-line-field, cert-line, and cert-underlined
                self.assertIn(
                    "cert-line-field",
                    content,
                    f"Template {tpath} must use the 'cert-line-field' class for semantic underlines"
                )
                self.assertIn(
                    "cert-line",
                    content,
                    f"Template {tpath} must use the 'cert-line' class for single-wrapper underlines"
                )
                self.assertIn(
                    "cert-underlined",
                    content,
                    f"Template {tpath} must use the 'cert-underlined' class for signature-style centered alignment"
                )

                # 2. Must contain cert-body-paragraph
                self.assertIn(
                    "cert-body-paragraph",
                    content,
                    f"Template {tpath} must use 'cert-body-paragraph' for standardized typography"
                )

                # 3. Must not have raw long underscore placeholders (e.g. 5+ underscores) in HTML body
                # Extract cert body block
                body_match = re.search(r'<div class="cert-ov[^"]*body">(.*?)</div>', content, re.DOTALL)
                if body_match:
                    body_html = body_match.group(1)
                    underscores = re.findall(r'_{4,}', body_html)
                    self.assertEqual(
                        len(underscores),
                        0,
                        f"Template {tpath} still contains raw underscore strings: {underscores}"
                    )


    def test_cert_field_centered_css_rules(self):
        with open("frontend/styles.css", "r", encoding="utf-8") as f:
            styles = f.read()

        self.assertIn(".cert-line", styles)
        self.assertIn(".cert-field", styles)
        self.assertIn(".cert-underlined", styles)
        self.assertIn(".cert-line-field", styles)
        self.assertIn("display: inline !important;", styles)
        self.assertIn("border-bottom: 1.5px solid #111827 !important;", styles)
        self.assertIn("padding: 0 2px !important;", styles)
        self.assertIn("display: inline-block !important;", styles)
        self.assertIn("vertical-align: -2px !important;", styles)
        self.assertIn("height: 1em !important;", styles)
        self.assertIn("line-height: 1 !important;", styles)
        self.assertIn("min-width: 140px !important;", styles)
        self.assertIn("min-width: 35px !important;", styles)

    def test_templates_punctuation_and_no_surrounding_underscores(self):
        templates = [
            "frontend/clearance.html",
            "frontend/residency.html",
            "frontend/indigency.html",
            "frontend/non_residency.html",
        ]
        for tpath in templates:
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()

            body_match = re.search(r'<div class="cert-ov[^"]*body[^"]*">(.*?)</div>', content, re.DOTALL)
            self.assertIsNotNone(body_match, f"Could not find certificate body in {tpath}")
            body_html = body_match.group(1)

            # Check that there are no underscores before or inside spans
            self.assertFalse(re.search(r'_+<span', body_html), f"Found underscore before span in {tpath}")
            self.assertFalse(re.search(r'<span[^>]*>[^<]*_+', body_html), f"Found underscore inside span in {tpath}")
            # Check there is no space before commas attached to closing tags
            self.assertFalse(re.search(r'</span>\s+,', body_html), f"Found space before comma after span in {tpath}")


    def test_enforce_centered_fields_runtime_enforcer(self):
        with open("frontend/public/js/certificates.js", "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("function enforceCenteredFields", js)
        self.assertIn("window.enforceCenteredFields", js)
        self.assertIn("enforceCenteredFields", js)
        self.assertIn("el.removeAttribute('style')", js)
        self.assertIn("style.setProperty('display', 'inline', 'important')", js)
        self.assertIn("style.setProperty('padding', '0 2px', 'important')", js)
        self.assertIn("style.setProperty('display', 'inline-block', 'important')", js)
        self.assertIn("style.setProperty('border-bottom', '1.5px solid #111827', 'important')", js)
        self.assertIn("style.setProperty('vertical-align', '-2px', 'important')", js)
        self.assertIn("style.setProperty('height', '1em', 'important')", js)
        self.assertIn("style.setProperty('line-height', '1', 'important')", js)


if __name__ == "__main__":
    unittest.main()
