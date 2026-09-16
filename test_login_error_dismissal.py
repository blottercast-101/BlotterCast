import os
import re
import unittest

class TestLoginErrorDismissal(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.login_html_path = os.path.join(self.base_dir, "frontend", "login.html")
        self.login_js_path = os.path.join(self.base_dir, "frontend", "login.js")
        self.login_public_js_path = os.path.join(self.base_dir, "frontend", "public", "js", "login.js")
        self.styles_path = os.path.join(self.base_dir, "frontend", "styles.css")

        with open(self.login_html_path, "r", encoding="utf-8") as f:
            self.login_html = f.read()

        with open(self.login_js_path, "r", encoding="utf-8") as f:
            self.login_js = f.read()

        with open(self.styles_path, "r", encoding="utf-8") as f:
            self.styles_css = f.read()

    def test_01_error_banner_element_and_styles(self):
        """Verify #loginErrorAlert exists with .auth-error-banner class and CSS rules."""
        self.assertIn('id="loginErrorAlert"', self.login_html, "login.html missing #loginErrorAlert")
        self.assertIn('auth-error-banner', self.login_html, "login.html missing auth-error-banner class")
        self.assertIn('hidden', self.login_html, "login.html error banner should have hidden class initially")

        # Verify styles.css supports auth-error-banner
        self.assertIn('auth-error-banner', self.styles_css)
        self.assertIn('auth-error-banner.show', self.styles_css)
        self.assertIn('auth-error-banner.hidden', self.styles_css)

    def test_02_clear_auth_errors_helper_definition(self):
        """Verify clearAuthErrors function exists in login.js and login.html."""
        for name, code in [("login.html", self.login_html), ("login.js", self.login_js)]:
            self.assertIn("function clearAuthErrors()", code, f"{name} missing function clearAuthErrors()")
            self.assertIn("document.getElementById('loginErrorAlert')", code, f"{name} missing getElementById('loginErrorAlert')")
            self.assertIn("auth-error-banner", code, f"{name} missing querySelector('.auth-error-banner')")
            self.assertIn("errorBanner.classList.add('hidden')", code, f"{name} must add hidden class")
            self.assertIn("errorBanner.style.display = 'none'", code, f"{name} must set style.display = 'none'")
            self.assertIn("errorBanner.textContent = ''", code, f"{name} must clear textContent")

    def test_03_flow_transitions_clear_errors(self):
        """Verify clearAuthErrors is called on step transitions and forgot password."""
        # 1. Forgot password link
        self.assertIn('id="forgotPasswordLink"', self.login_html, "login.html missing id='forgotPasswordLink'")
        self.assertIn("showForgotStep", self.login_html)
        
        # Verify showForgotStep calls clearAuthErrors
        forgot_match = re.search(r'function showForgotStep\([^\)]*\)\s*\{([^}]+)\}', self.login_html)
        self.assertIsNotNone(forgot_match, "showForgotStep function not found")
        self.assertIn("clearAuthErrors()", forgot_match.group(1), "showForgotStep must call clearAuthErrors()")

        # 2. OTP step transition
        otp_match = re.search(r'function showOtpStep\([^\)]*\)\s*\{([^}]+)\}', self.login_html)
        self.assertIsNotNone(otp_match, "showOtpStep function not found")
        self.assertIn("clearAuthErrors()", otp_match.group(1), "showOtpStep must call clearAuthErrors()")

        # 3. Reset OTP step transition
        reset_match = re.search(r'function showResetStep\([^\)]*\)\s*\{([^}]+)\}', self.login_html)
        self.assertIsNotNone(reset_match, "showResetStep function not found")
        self.assertIn("clearAuthErrors()", reset_match.group(1), "showResetStep must call clearAuthErrors()")

        # 4. Set new password step transition
        new_pw_match = re.search(r'function showNewPasswordStep\([^\)]*\)\s*\{([^}]+)\}', self.login_html)
        self.assertIsNotNone(new_pw_match, "showNewPasswordStep function not found")
        self.assertIn("clearAuthErrors()", new_pw_match.group(1), "showNewPasswordStep must call clearAuthErrors()")

        # 5. Back to sign in transition
        back_match = re.search(r'function backToLogin\([^\)]*\)\s*\{([^}]+)\}', self.login_html)
        self.assertIsNotNone(back_match, "backToLogin function not found")
        self.assertIn("clearAuthErrors()", back_match.group(1), "backToLogin must call clearAuthErrors()")

    def test_04_input_and_focus_events_clear_errors(self):
        """Verify typing or focusing in username/password triggers clearAuthErrors."""
        self.assertIn("['username', 'password']", self.login_html)
        self.assertIn("'input'", self.login_html)
        self.assertIn("'focus'", self.login_html)
        self.assertIn("clearAuthErrors()", self.login_html)

    def test_05_login_submission_clears_errors_before_dispatch_and_on_success(self):
        """Verify handleLogin calls clearAuthErrors before API request, preserves hidden on success, reveals on catch."""
        login_fn_match = re.search(r'async function handleLogin\([^\)]*\)\s*\{(.*?)\n  let resendTimer', self.login_html, re.DOTALL)
        self.assertIsNotNone(login_fn_match, "handleLogin function body not found")
        fn_body = login_fn_match.group(1)

        # 1. Calls clearAuthErrors before BCApi.login
        before_api_match = re.search(r'clearAuthErrors\(\);.*?BCApi\.login', fn_body, re.DOTALL)
        self.assertIsNotNone(before_api_match, "clearAuthErrors() must be called immediately before BCApi.login")

        # 2. Clears auth errors on success inside try block
        try_block_match = re.search(r'try\s*\{(.*?)\}\s*catch', fn_body, re.DOTALL)
        self.assertIsNotNone(try_block_match, "try block not found in handleLogin")
        try_body = try_block_match.group(1)
        self.assertIn("clearAuthErrors()", try_body, "try block must ensure banner is cleared on success")
        self.assertNotIn("classList.add('show')", try_body, "try block should never add 'show' on success")

        # 3. Reveals banner inside catch block
        catch_block_match = re.search(r'catch\s*\([^\)]*\)\s*\{(.*?)\}', fn_body, re.DOTALL)
        self.assertIsNotNone(catch_block_match, "catch block not found in handleLogin")
        catch_body = catch_block_match.group(1)
        self.assertIn("errorBanner.classList.remove('hidden')", catch_body)
        self.assertIn("errorBanner.classList.add('show')", catch_body)

if __name__ == "__main__":
    unittest.main()
