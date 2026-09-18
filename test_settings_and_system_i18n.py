import unittest
import os
import re

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


class TestSettingsAndSystemI18n(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(FRONTEND_DIR, "i18n.js"), "r", encoding="utf-8") as f:
            self.i18n_js = f.read()
        with open(os.path.join(FRONTEND_DIR, "app.js"), "r", encoding="utf-8") as f:
            self.app_js = f.read()
        with open(os.path.join(FRONTEND_DIR, "settings.html"), "r", encoding="utf-8") as f:
            self.settings_html = f.read()

    def test_key_symmetry_in_i18n_js(self):
        """Verify 100% key symmetry between en and tl in frontend/i18n.js."""
        en_match = re.search(r"en:\s*\{(.*?)\},\s*tl:\s*\{", self.i18n_js, re.DOTALL)
        self.assertIsNotNone(en_match, "Could not find 'en' block in i18n.js")
        en_block = en_match.group(1)

        tl_match = re.search(r"tl:\s*\{(.*?)\}\s*\n\};", self.i18n_js, re.DOTALL)
        self.assertIsNotNone(tl_match, "Could not find 'tl' block in i18n.js")
        tl_block = tl_match.group(1)

        en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", en_block, re.MULTILINE))
        tl_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", tl_block, re.MULTILINE))

        missing_in_tl = en_keys - tl_keys
        missing_in_en = tl_keys - en_keys

        self.assertEqual(missing_in_tl, set(), f"Keys in en missing in tl in i18n.js: {missing_in_tl}")
        self.assertEqual(missing_in_en, set(), f"Keys in tl missing in en in i18n.js: {missing_in_en}")

    def test_key_symmetry_in_app_js(self):
        """Verify 100% key symmetry between en and tl in frontend/app.js."""
        en_match = re.search(r"en:\s*\{(.*?)\},\s*tl:\s*\{", self.app_js, re.DOTALL)
        self.assertIsNotNone(en_match, "Could not find 'en' block in app.js")
        en_block = en_match.group(1)

        tl_match = re.search(r"tl:\s*\{(.*?)\}\s*\n\};", self.app_js, re.DOTALL)
        self.assertIsNotNone(tl_match, "Could not find 'tl' block in app.js")
        tl_block = tl_match.group(1)

        en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", en_block, re.MULTILINE))
        tl_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", tl_block, re.MULTILINE))

        missing_in_tl = en_keys - tl_keys
        missing_in_en = tl_keys - en_keys

        self.assertEqual(missing_in_tl, set(), f"Keys in en missing in tl in app.js: {missing_in_tl}")
        self.assertEqual(missing_in_en, set(), f"Keys in tl missing in en in app.js: {missing_in_en}")

    def test_data_management_and_export_dictionary(self):
        """Verify [DATA MANAGEMENT & EXPORT] translations in i18n.js and app.js."""
        expected = {
            "data_management": "Pamamahala ng Data",
            "data_management_desc": "Ang lahat ng tala ay nakaimbak sa PostgreSQL blottercast database. Ang mga talang idinadagdag sa mga pahina ng Blotter at Incident ay awtomatikong nagpapakain sa Heat Map, Trends, at Python ML Predictions module.",
            "reset_demo_dataset": "I-reset ang Sample na Data",
            "export_records_json": "I-export ang mga Tala (JSON)"
        }
        for key, val in expected.items():
            self.assertIn(f'{key}: "{val}"', self.i18n_js)
            self.assertIn(f'{key}: "{val}"', self.app_js)

        # Also verify settings.html tags
        self.assertIn('data-i18n="data_management"', self.settings_html)
        self.assertIn('data-i18n="data_management_desc"', self.settings_html)
        self.assertIn('data-i18n="reset_demo_dataset"', self.settings_html)
        self.assertIn('data-i18n="export_records_json"', self.settings_html)

    def test_alerts_and_notifications_dictionary(self):
        """Verify [ALERTS & NOTIFICATIONS] translations."""
        expected = {
            "trigger_alert_risk_desc": "Magpadala ng babala kapag ang inaasahang panganib ay lumampas sa halagang ito.",
            "alert_spike_desc": "Magpadala ng babala kapag ang mga bagong insidente ay lumampas sa bilang na ito sa loob ng 24 oras.",
            "in_app_notifications": "Mga Notification sa App",
            "show_alerts_desc": "Ipakita ang mga babala sa notification center",
            "model_retraining_alerts": "Mga Babala sa Muling Pagsasanay ng Modelo",
            "notify_retrain_desc": "Magbigay-alam kapag natapos ang muling pagsasanay ng ML model"
        }
        for key, val in expected.items():
            self.assertIn(f'{key}: "{val}"', self.i18n_js)
            self.assertIn(f'{key}: "{val}"', self.app_js)
            self.assertIn(f'data-i18n="{key}"', self.settings_html)

    def test_security_and_password_rules_dictionary(self):
        """Verify [SECURITY & PASSWORD RULES] translations."""
        expected = {
            "password_must_contain": "ANG PASSWORD AY DAPAT NAGLALAMAN NG:",
            "rule_len": "Hindi bababa sa 6 na character",
            "rule_upper": "Hindi bababa sa 1 malaking titik (A–Z)",
            "rule_lower": "Hindi bababa sa 1 maliit na titik (a–z)",
            "rule_num": "Hindi bababa sa 1 numero (0–9)",
            "rule_special": "Hindi bababa sa 1 espesyal na karakter (hal. !@#$%^&*)",
            "security_tip": "Tip sa Seguridad",
            "security_tip_desc": "HUWAG KAILANMAN GAMITIN ANG PAREHONG PASSWORD SA IBANG SYSTEM"
        }
        for key, val in expected.items():
            self.assertIn(f'{key}: "{val}"', self.i18n_js)
            self.assertIn(f'{key}: "{val}"', self.app_js)
            self.assertIn(f'data-i18n="{key}"', self.settings_html)

    def test_display_and_authentication_settings_dictionary(self):
        """Verify [DISPLAY & AUTHENTICATION SETTINGS] translations."""
        expected = {
            "display_preferences": "Mga Kagustuhan sa Display",
            "system_time_format": "Format ng Oras ng System",
            "time_format_12h": "12-Oras (hh:mm A) (hal. 01:45 PM)",
            "security_and_authentication": "Seguridad at Pagpapatunay",
            "admin_master_control": "Pangunahing Kontrol ng Admin",
            "enforce_2fa_all_accounts": "Ipatupad ang 2FA sa Lahat ng Account",
            "require_2fa_desc": "Hilingin ang Two-Factor Authentication sa lahat ng papel sa pag-login.",
            "session_inactivity_auto_logout": "Awtomatikong Pag-logout kapag Walang Gawain (2 Oras)",
            "auto_logout_desc": "Awtomatikong nilog-out ang mga user na walang activity pagkaraan ng 120 minuto.",
            "policy_thresholds_password_rules": "Mga Patakaran at Tuntunin sa Password",
            "inactivity_timeout_duration": "Tagal bago i-Logout kapag walang Gawain (minuto)",
            "default_timeout_desc": "Default: 120 minuto (2 oras).",
            "max_failed_logins": "Pinakamataas na Subok ng Maling Login",
            "min_password_length": "Pinakamaikling Haba ng Password",
            "password_expiry_days": "Pagpasa ng Password (araw)",
            "data_privacy": "Privacy ng Data",
            "audit_trail_logging": "Pagtatala ng Audit Trail",
            "log_data_changes_desc": "Itala ang lahat ng pagbabago sa data, pag-login, at pag-export ng ulat",
            "data_subject_rights_module": "Module para sa Karapatan sa Data Privacy",
            "data_subject_rights_desc": "Payagan ang kahilingan sa pag-access o pagwawasto ng data mula sa mga indibidwal"
        }
        for key, val in expected.items():
            self.assertIn(f'{key}: "{val}"', self.i18n_js)
            self.assertIn(f'{key}: "{val}"', self.app_js)
            self.assertIn(f'data-i18n="{key}"', self.settings_html)

    def test_backup_and_recovery_dictionary(self):
        """Verify [BACKUP & RECOVERY] translations."""
        expected = {
            "automated_backup": "Awtomatikong Backup",
            "backup_frequency": "Dalas ng Backup",
            "backup_time": "Oras ng Backup",
            "backup_destination": "Pupuntahan ng Backup",
            "retain_backups_days": "Itabi ang Backup ng (mga araw)",
            "backups_scheduled_desc": "Ang mga backup ay naka-iskedyul at awtomatikong isinasagawa ng backend server worker batay sa Asia/Manila standard time (UTC+8).",
            "perform_backup_now": "Magsagawa ng Backup Ngayon",
            "recovery_objectives": "Mga Layunin sa Pagbawi (Recovery)",
            "recovery_time_objective": "Target na Oras ng Pagbawi (RTO)",
            "rto_desc": "Pinakamatagal na katanggap-tanggap na pagtigil ng system pagkatapos ng pagkasira.",
            "recovery_point_objective": "Target na Halaga ng Nawalang Data (RPO)",
            "rpo_desc": "Pinakamataas na katanggap-tanggap na saklaw ng nawalang data.",
            "backup_history": "Kasaysayan ng Backup"
        }
        for key, val in expected.items():
            self.assertIn(f'{key}: "{val}"', self.i18n_js)
            self.assertIn(f'{key}: "{val}"', self.app_js)
            self.assertIn(f'data-i18n="{key}"', self.settings_html)

    def test_modals_and_dialogs_dictionary_and_handlers(self):
        """Verify [MODALS & DIALOGS] translations and logic."""
        # 1. Dictionary keys
        self.assertIn('log_out: "Mag-log Out"', self.i18n_js)
        self.assertIn('confirm_logout_message: "Sigurado ka bang gusto mong mag-log out?"', self.i18n_js)
        self.assertIn('cancel: "Kanselahin"', self.i18n_js)

        # 2. app.js BC_TRANSLATIONS.fil
        self.assertIn('"Log Out": "Mag-log Out"', self.app_js)
        self.assertIn('"Are you sure you want to log out?": "Sigurado ka bang gusto mong mag-log out?"', self.app_js)
        self.assertIn('"Cancel": "Kanselahin"', self.app_js)

        # 3. doLogout() prompt & options
        self.assertIn("Sigurado ka bang gusto mong mag-log out?", self.app_js)
        self.assertIn("const cancelLabel = isTl ? 'Kanselahin' : 'Cancel';", self.app_js)

        # 4. _bcOpenDialog default cancel label
        self.assertIn("cancelBtn.textContent = cancelLabel || (isDialogTl ? 'Kanselahin' : 'Cancel');", self.app_js)

        # 5. resetDemoData() dialog
        self.assertIn("I-reset ang Sample na Data", self.settings_html)
        self.assertIn("const cancelLabel = isTl ? 'Kanselahin' : 'Cancel';", self.settings_html)


if __name__ == "__main__":
    unittest.main()
