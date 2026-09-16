import unittest
import os


class TestModalHierarchyAndAutocomplete(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")
        self.app_js_path = os.path.join(self.base_dir, "frontend", "app.js")

    def test_css_stacking_hierarchy_tokens(self):
        with open(self.styles_path, "r", encoding="utf-8") as f:
            css = f.read()

        # Scope 1 CSS z-index stacking tokens
        self.assertIn(".modal-form-backdrop", css)
        self.assertIn("z-index: 60 !important;", css)
        self.assertIn(".modal-form-card", css)
        self.assertIn("z-index: 61 !important;", css)
        self.assertIn(".confirm-modal-backdrop", css)
        self.assertIn("z-index: 9998 !important;", css)
        self.assertIn(".confirm-modal-card", css)
        self.assertIn("z-index: 9999 !important;", css)
        self.assertIn(".global-toast", css)
        self.assertIn("z-index: 10000 !important;", css)

    def test_app_js_modal_lifecycle_and_freeze_prevention(self):
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # dismissModal implementation
        self.assertIn("function dismissModal(modalEl, backdropEl)", js)
        self.assertIn("document.body.classList.remove('overflow-hidden', 'modal-open')", js)
        self.assertIn("document.body.style.overflow = ''", js)
        self.assertIn("document.body.style.pointerEvents = 'auto'", js)
        self.assertIn("window.dismissModal = dismissModal", js)

        # Confirm dialog DOM placement
        self.assertIn("confirm-modal-backdrop", js)
        self.assertIn("confirm-modal-card", js)
        self.assertIn("document.body.appendChild(el)", js)

    def test_autocomplete_dropdown_premature_expansion_prevention(self):
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Focus listener restriction: must check input value length > 0
        self.assertIn("input.value.trim().length > 0", js)

        # Query guard in _bcFilterResidents
        self.assertIn("if (q.length === 0)", js)
        self.assertIn("list.classList.add('hidden')", js)
        self.assertIn("list.innerHTML = ''", js)

        # Clear existing options on reset
        self.assertIn("bcResidentPickerClear", js)


if __name__ == "__main__":
    unittest.main()
