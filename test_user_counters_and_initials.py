import unittest
import re
import os
import subprocess
from app.helpers import get_initials as py_get_initials


class TestUserCountersAndInitials(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.base_dir, 'frontend', 'users.html'), 'r', encoding='utf-8') as f:
            self.users_html = f.read()
        with open(os.path.join(self.base_dir, 'frontend', 'app.js'), 'r', encoding='utf-8') as f:
            self.app_js = f.read()

    def test_add_user_character_counters_html(self):
        # 1. Check Full Name counter & maxlength
        self.assertIn('id="userFullNameCount"', self.users_html)
        self.assertIn('0/50', self.users_html)
        self.assertTrue(re.search(r'id=["\']wiz_name["\'][^>]*maxlength=["\']50["\']|maxlength=["\']50["\'][^>]*id=["\']wiz_name["\']', self.users_html))

        # 2. Check Username counter & maxlength
        self.assertIn('id="userUsernameCount"', self.users_html)
        self.assertIn('0/30', self.users_html)
        self.assertTrue(re.search(r'id=["\']wiz_username["\'][^>]*maxlength=["\']30["\']|maxlength=["\']30["\'][^>]*id=["\']wiz_username["\']', self.users_html))

        # 3. Check Email counter & maxlength
        self.assertIn('id="userEmailCount"', self.users_html)
        self.assertTrue(re.search(r'id=["\']wiz_email["\'][^>]*maxlength=["\']50["\']|maxlength=["\']50["\'][^>]*id=["\']wiz_email["\']', self.users_html))

        # 4. Check muted sage color styling class
        self.assertIn('text-[#52796f]', self.users_html)

    def test_add_user_char_counter_js_functions(self):
        self.assertIn('function updateUserCharCounters()', self.users_html)
        self.assertIn('function initUserCharCounters()', self.users_html)
        self.assertIn('userFullNameCount', self.users_html)
        self.assertIn('userUsernameCount', self.users_html)
        self.assertIn('userEmailCount', self.users_html)

    def test_python_get_initials(self):
        self.assertEqual(py_get_initials("Juan Cruz"), "JC")
        self.assertEqual(py_get_initials("Maria Clara Santos"), "MS")
        self.assertEqual(py_get_initials("Jose Protacio Rizal Mercado"), "JM")
        self.assertEqual(py_get_initials("Admin"), "AD")
        self.assertEqual(py_get_initials("John"), "JO")
        self.assertEqual(py_get_initials(""), "??")
        self.assertEqual(py_get_initials(None), "??")
        self.assertEqual(py_get_initials("   "), "??")
        self.assertEqual(py_get_initials("  Juan   Dela   Cruz  "), "JC")

    def test_javascript_get_initials_source(self):
        # Verify getInitials function in app.js
        self.assertIn('function getInitials(name)', self.app_js)
        self.assertIn('window.getInitials = getInitials', self.app_js)
        self.assertIn('window.bcInitials = bcInitials', self.app_js)
        
        # Verify getInitials logic structure
        self.assertIn("const words = name.trim().split(/\\s+/).filter(Boolean);", self.app_js)
        self.assertIn("words[0].slice(0, 2).toUpperCase()", self.app_js)
        self.assertIn("words[0].charAt(0).toUpperCase()", self.app_js)
        self.assertIn("words[words.length - 1].charAt(0).toUpperCase()", self.app_js)


if __name__ == '__main__':
    unittest.main()
