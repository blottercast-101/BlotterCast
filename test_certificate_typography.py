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

                # 1. Must contain cert-line-field
                self.assertIn(
                    "cert-line-field",
                    content,
                    f"Template {tpath} must use the 'cert-line-field' class for semantic underlines"
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


if __name__ == "__main__":
    unittest.main()
