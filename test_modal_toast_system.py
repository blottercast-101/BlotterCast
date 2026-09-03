import unittest
import re
import os

class TestModalAndToastReliability(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.styles_path = os.path.join(self.base_dir, 'frontend', 'styles.css')
        self.app_js_path = os.path.join(self.base_dir, 'frontend', 'app.js')
        self.api_js_path = os.path.join(self.base_dir, 'frontend', 'api.js')
        
        with open(self.styles_path, 'r', encoding='utf-8') as f:
            self.styles_css = f.read()
        with open(self.app_js_path, 'r', encoding='utf-8') as f:
            self.app_js = f.read()
        with open(self.api_js_path, 'r', encoding='utf-8') as f:
            self.api_js = f.read()

    def test_01_z_index_hierarchy_scale(self):
        """Verify CSS contains the complete standardized z-index scale"""
        self.assertIn('--z-dropdown: 1000;', self.styles_css)
        self.assertIn('--z-sticky-nav: 1020;', self.styles_css)
        self.assertIn('--z-drawer-sidebar: 1040;', self.styles_css)
        self.assertIn('--z-form-modal: 1050;', self.styles_css)
        self.assertIn('--z-confirm-modal: 1060;', self.styles_css)
        self.assertIn('--z-toast-notification: 9999;', self.styles_css)

    def test_02_modal_and_confirm_layering(self):
        """Verify modals and confirmation dialogs use fixed positioning and appropriate z-index variables"""
        self.assertIn('z-index: var(--z-form-modal) !important;', self.styles_css)
        self.assertIn('z-index: var(--z-confirm-modal) !important;', self.styles_css)
        self.assertIn('.modal-backdrop-overlay', self.styles_css)
        self.assertIn('.modal-overlay', self.styles_css)
        self.assertIn('#bcDialogOverlay', self.styles_css)
        self.assertIn('#bcPermDeleteOverlay', self.styles_css)
        self.assertIn('#elevateConfirmModal', self.styles_css)

    def test_03_toast_container_styling(self):
        """Verify toast container and items styling with pointer-events and z-index"""
        self.assertIn('.toast-container', self.styles_css)
        self.assertIn('#toast-container', self.styles_css)
        self.assertIn('#toast-portal', self.styles_css)
        self.assertIn('z-index: var(--z-toast-notification) !important;', self.styles_css)
        self.assertIn('top: 1.25rem !important;', self.styles_css)
        self.assertIn('right: 1.25rem !important;', self.styles_css)
        self.assertIn('pointer-events: none !important;', self.styles_css)
        self.assertIn('pointer-events: auto !important;', self.styles_css)

    def test_04_modal_body_teleportation(self):
        """Verify app.js implements DOM teleportation to document.body"""
        self.assertIn('function teleportModalsToBody()', self.app_js)
        self.assertIn('MutationObserver', self.app_js)
        self.assertIn('function openModal(id)', self.app_js)
        self.assertIn('document.body.appendChild(el)', self.app_js)

    def test_05_centralized_toast_manager(self):
        """Verify app.js provides centralized multi-toast store and polymorphic showToast"""
        self.assertIn('class ToastManager', self.app_js)
        self.assertIn('window.toastStore = _toastStoreInstance', self.app_js)
        self.assertIn('function showToast(', self.app_js)
        self.assertIn('window.showToast = showToast', self.app_js)
        self.assertIn('window.toast = {', self.app_js)
        self.assertIn('toast-close-btn', self.app_js)
        self.assertIn('toast-progress-bar', self.app_js)
        self.assertIn('executePrint', self.app_js)

    def test_06_api_error_interceptor_and_fail_safe(self):
        """Verify api.js captures network errors and 4xx/5xx responses with error toasts"""
        self.assertIn('Network connection failed', self.api_js)
        self.assertIn('window.showToast', self.api_js)
        self.assertIn('window.addEventListener(\'unhandledrejection\'', self.api_js)

if __name__ == '__main__':
    unittest.main()
