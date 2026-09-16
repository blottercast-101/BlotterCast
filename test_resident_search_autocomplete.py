import os
import re
import unittest


class TestResidentSearchAutocomplete(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.templates = [
            os.path.join(self.base_dir, "frontend", "clearance.html"),
            os.path.join(self.base_dir, "frontend", "residency.html"),
            os.path.join(self.base_dir, "frontend", "indigency.html"),
        ]
        self.app_js_path = os.path.join(self.base_dir, "frontend", "app.js")
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")

    def test_dropdown_container_in_html_dom(self):
        """Verify requirement 1: Dropdown container exists directly under #residentSearch in relative w-full container."""
        for tpath in self.templates:
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn('id="residentSearch"', content, f"{tpath} missing #residentSearch")
            if "clearance.html" in tpath:
                self.assertIn('id="residentResultsMenu"', content, f"{tpath} missing #residentResultsMenu")
                self.assertIn('z-[999]', content, f"{tpath} dropdown missing z-[999]")
            else:
                self.assertIn('id="residentDropdownList"', content, f"{tpath} missing #residentDropdownList")
                self.assertIn('z-[70]', content, f"{tpath} dropdown missing z-[70]")

            # Verify relative w-full wrapper
            self.assertIn('relative w-full', content, f"{tpath} missing relative w-full wrapper")
            self.assertIn('border-[#c6dfd4]', content, f"{tpath} dropdown missing border-[#c6dfd4]")

    def test_styles_css_resident_dropdown_z_index(self):
        """Verify styles.css explicitly guarantees high z-index for residentDropdownList."""
        with open(self.styles_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn("#residentDropdownList", css)
        self.assertIn("z-index: 70 !important;", css)

    def test_render_resident_results_functionality(self):
        """Verify requirement 2: renderResidentResults function removes hidden, formats items with palette, and handles empty/deceased."""
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("function renderResidentResults(results)", js)
        self.assertIn("const dropdown = document.getElementById('residentDropdownList')", js)
        self.assertIn("dropdown.classList.remove('hidden')", js)

        # Fallback for no active residents
        self.assertIn("No active residents found", js)
        self.assertIn("#52796f", js)

        # Palette and resident item class
        self.assertIn("resident-item", js)
        self.assertIn("#edf5f0", js)
        self.assertIn("#1e3a2b", js)
        self.assertIn('data-id="${r.id}"', js)

        # Exclusion of deceased residents
        self.assertIn("isDeceased", js)

    def test_event_listeners_and_search_trigger(self):
        """Verify requirement 3: input event triggers filter on val.length > 0, hides dropdown on empty, blocks empty auto-open."""
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("function filterResidents(val)", js)
        self.assertIn("searchInput.addEventListener('input'", js)
        self.assertIn("val.length > 0", js)
        self.assertIn("filterResidents(val)", js)
        self.assertIn("dropdown.classList.add('hidden')", js)

        # Focus guard: does not auto-open on empty input
        self.assertIn("input.value.trim().length > 0", js)


if __name__ == "__main__":
    unittest.main()
