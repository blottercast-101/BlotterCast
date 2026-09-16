import os
import re
import unittest


class TestClearanceResidentAutocomplete(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.clearance_html = os.path.join(self.base_dir, "frontend", "clearance.html")
        self.clearance_js = os.path.join(self.base_dir, "frontend", "clearance.js")
        self.styles_css = os.path.join(self.base_dir, "frontend", "styles.css")

    def test_dom_structure_clearance_modal(self):
        """Verify requirement 1: exact DOM structure in clearance.html for residentSearchContainer and residentResultsMenu."""
        with open(self.clearance_html, "r", encoding="utf-8") as f:
            content = f.read()

        # Check container
        self.assertIn('id="residentSearchContainer"', content)
        self.assertIn('class="relative w-full mb-3"', content)

        # Check label
        self.assertIn('class="block text-xs font-semibold text-[#1e3a2b] mb-1">Resident *</label>', content)

        # Check input #residentSearch
        self.assertIn('id="residentSearch"', content)
        self.assertIn('autocomplete="off"', content)
        self.assertIn('placeholder="Type a name to search..."', content)
        self.assertIn('class="w-full bg-[#edf5f0] border border-[#c6dfd4] rounded-xl px-4 py-2.5 text-sm text-[#52796f] placeholder-[#52796f] focus:outline-none focus:ring-1 focus:ring-[#1e3a2b]"', content)

        # Check paragraph
        self.assertIn('class="text-[11px] text-[#52796f] mt-1"', content)

        # Check results menu container
        self.assertIn('id="residentResultsMenu"', content)
        self.assertIn('class="hidden absolute left-0 right-0 top-[65px] bg-white border border-[#c6dfd4] rounded-xl shadow-xl max-h-56 overflow-y-auto z-[999]"', content)

        # Check script inclusion
        self.assertIn('<script src="clearance.js"></script>', content)

    def test_js_logic_clearance_js(self):
        """Verify requirement 2: clean, crash-proof JS logic in clearance.js."""
        with open(self.clearance_js, "r", encoding="utf-8") as f:
            js = f.read()

        # Check elements query
        self.assertIn("document.getElementById('residentSearch')", js)
        self.assertIn("document.getElementById('residentResultsMenu')", js)

        # Check renderResidentsList function
        self.assertIn("function renderResidentsList(", js)
        self.assertIn("window.censusResidents", js)
        self.assertIn("status === 'deceased'", js)
        self.assertIn("No matching residents found", js)
        self.assertIn("resident-option", js)
        self.assertIn("TRANSFERRED", js)
        self.assertIn("opacity-40 cursor-not-allowed bg-gray-50", js)
        self.assertIn("cursor-pointer hover:bg-[#edf5f0] text-[#1e3a2b]", js)
        self.assertIn("resultsMenu.classList.remove('hidden')", js)

        # Check event listeners
        self.assertIn("residentInput.addEventListener('input'", js)
        self.assertIn("val.length > 0", js)
        self.assertIn("resultsMenu.classList.add('hidden')", js)
        self.assertIn("residentInput.addEventListener('focus'", js)
        self.assertIn("residentInput.value.trim().length > 0", js)

        # Check click selection and delegation
        self.assertIn("selectResidentForClearance", js)
        self.assertIn("resultsMenu.addEventListener('click'", js)
        self.assertIn("option.dataset.transferred === 'true'", js)

    def test_modal_body_overflow_not_hidden(self):
        """Verify requirement 3: parent modal body has overflow-y: auto and not overflow: hidden."""
        with open(self.clearance_html, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the modal body containing residentSearch
        match = re.search(r'<div class="([^"]*modal-body[^"]*)">.*?id="residentSearchContainer"', content, re.DOTALL)
        self.assertIsNotNone(match, "Could not find modal-body wrapping residentSearchContainer")
        modal_body_classes = match.group(1)

        self.assertIn("overflow-y-auto", modal_body_classes)
        self.assertNotIn("overflow-hidden", modal_body_classes)

    def test_css_z_index_resident_results_menu(self):
        """Verify CSS specifies z-index 999 for residentResultsMenu."""
        with open(self.styles_css, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn("#residentResultsMenu", css)
        self.assertIn("z-index: 999 !important;", css)


if __name__ == "__main__":
    unittest.main()
