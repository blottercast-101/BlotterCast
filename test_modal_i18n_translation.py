import unittest
import os
import re
import json

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")


class TestModalI18nTranslation(unittest.TestCase):
    def setUp(self):
        self.app_js_path = os.path.join(FRONTEND_DIR, "app.js")
        with open(self.app_js_path, "r", encoding="utf-8") as f:
            self.app_js = f.read()

    def test_i18n_dictionary_exists_and_has_en_and_tl(self):
        """Verify window.i18n is exposed and has en and tl definitions."""
        self.assertIn("window.i18n = i18n;", self.app_js)
        self.assertIn("window.applyLanguageTranslation = applyLanguageTranslation;", self.app_js)
        
        # Check that const i18n = { en: { ... }, tl: { ... } }; is present
        self.assertIn("const i18n = {", self.app_js)
        self.assertIn("en: {", self.app_js)
        self.assertIn("tl: {", self.app_js)

    def test_i18n_key_symmetry(self):
        """Extract en and tl key dictionaries from app.js and check key symmetry."""
        en_match = re.search(r"en:\s*\{(.*?)\},\s*tl:\s*\{", self.app_js, re.DOTALL)
        self.assertIsNotNone(en_match, "Could not locate 'en' block in i18n")
        en_block = en_match.group(1)

        tl_match = re.search(r"tl:\s*\{(.*?)\}\s*\n\};", self.app_js, re.DOTALL)
        self.assertIsNotNone(tl_match, "Could not locate 'tl' block in i18n")
        tl_block = tl_match.group(1)

        # Match top-level keys starting at the beginning of the line (ignoring whitespace)
        en_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", en_block, re.MULTILINE))
        tl_keys = set(re.findall(r"^\s*([a-zA-Z0-9_]+)\s*:\s*[\"']", tl_block, re.MULTILINE))

        # Test essential modal keys
        required_keys = [
            "import_resident_title",
            "export_blotter_title",
            "period_label",
            "year_label",
            "month_label",
            "period_all",
            "period_year",
            "period_month",
            "download",
            "drag_drop_text",
            "browse_files",
            "upload_import",
            "cancel",
            "close",
            "add_resident_title",
            "edit_resident_title",
            "import_blotter_title",
            "new_blotter_entry",
            "edit_blotter_entry",
            "new_incident_report",
            "edit_incident_report",
            "issue_clearance_title",
            "issue_residency_title",
            "issue_non_residency_title",
            "issue_indigency_title",
            "new_settlement_title",
            "edit_settlement_title",
            "add_new_user_title",
            "edit_user_title",
            "permanently_delete_user",
            "generate_report_title",
            "full_name",
            "address",
            "save",
            "export_excel",
            "view_edit",
            "delete",
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
        ]
        for k in required_keys:
            self.assertIn(k, en_keys, f"Missing {k} in en dictionary")
            self.assertIn(k, tl_keys, f"Missing {k} in tl dictionary")

        # Check key symmetry
        missing_in_tl = en_keys - tl_keys
        missing_in_en = tl_keys - en_keys
        self.assertEqual(missing_in_tl, set(), f"Keys in en but missing in tl: {missing_in_tl}")
        self.assertEqual(missing_in_en, set(), f"Keys in tl but missing in en: {missing_in_en}")

    def test_apply_language_translation_function(self):
        """Verify applyLanguageTranslation implementation details."""
        # Querying data-i18n, data-i18n-placeholder, and data-i18n-title
        self.assertIn("document.querySelectorAll('[data-i18n]')", self.app_js)
        self.assertIn("document.querySelectorAll('[data-i18n-placeholder]')", self.app_js)
        self.assertIn("document.querySelectorAll('[data-i18n-title]')", self.app_js)

        # Icon preservation check
        self.assertIn("el.querySelector('svg, [data-icon], i')", self.app_js)

        # Open modal hook
        self.assertIn("applyLanguageTranslation();", self.app_js)

        # Storage listener sync
        self.assertIn("localStorage.getItem('app_language')", self.app_js)
        self.assertIn("localStorage.getItem('bc_language')", self.app_js)

    def test_settings_page_language_handler(self):
        """Verify settings.html synchronizes app_language and triggers applyLanguageTranslation."""
        settings_path = os.path.join(FRONTEND_DIR, "settings.html")
        with open(settings_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("app_language", content)
        self.assertIn("applyLanguageTranslation", content)

    def test_census_html_modals_i18n(self):
        """Verify census.html has data-i18n attributes on residentModal, importModal, and censusViewModal."""
        census_path = os.path.join(FRONTEND_DIR, "census.html")
        with open(census_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check modal title attributes
        self.assertIn('data-i18n="import_resident_title"', content)
        self.assertIn('data-i18n="drag_drop_text"', content)
        self.assertIn('data-i18n="add_resident_title"', content)
        self.assertIn('data-i18n="resident_profile_details"', content)

        # Check button IDs preserved
        self.assertIn('id="cancelCensusImportBtn"', content)
        self.assertIn('id="submitCensusImportBtn"', content)

        # Check template download link preserved
        self.assertIn('/templates/census_resident_template.csv', content)

        # Check reset function dynamically pulls from window.i18n
        self.assertIn('window.i18n[isFil ? \'tl\' : \'en\']', content)

    def test_blotter_html_modals_i18n(self):
        """Verify blotter.html has data-i18n attributes on blotterModal, importModal, and viewModal."""
        blotter_path = os.path.join(FRONTEND_DIR, "blotter.html")
        with open(blotter_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('data-i18n="import_blotter_title"', content)
        self.assertIn('data-i18n="new_blotter_entry"', content)
        self.assertIn('data-i18n="blotter_record_details"', content)
        self.assertIn('data-i18n-placeholder="search_census_ph"', content)
        self.assertIn('id="exportExcelBtn"', content)
        self.assertIn('data-i18n="export_excel"', content)
        self.assertIn('onclick="toggleExportMenu()"', content)

    def test_incident_html_modals_i18n(self):
        """Verify incident.html has data-i18n attributes on incidentModal, incViewModal, and elevateConfirmModal."""
        incident_path = os.path.join(FRONTEND_DIR, "incident.html")
        with open(incident_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('data-i18n="new_incident_report"', content)
        self.assertIn('data-i18n="incident_report_details"', content)
        self.assertIn('data-i18n="elevate_confirm_title"', content)
        self.assertIn('data-i18n="elevate_confirm_body"', content)
        self.assertIn('data-i18n-placeholder="location_detail_ph"', content)

    def test_clearance_residency_indigency_modals_i18n(self):
        """Verify document issuance modals have data-i18n attributes."""
        for filename, title_key in [
            ("clearance.html", "issue_clearance_title"),
            ("residency.html", "issue_residency_title"),
            ("non_residency.html", "issue_non_residency_title"),
            ("indigency.html", "issue_indigency_title"),
        ]:
            filepath = os.path.join(FRONTEND_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(f'data-i18n="{title_key}"', content, f"Missing {title_key} in {filename}")
            self.assertIn('data-i18n="cancel"', content, f"Missing cancel in {filename}")

    def test_settlement_html_modals_i18n(self):
        """Verify settlement.html has data-i18n attributes on settlementModal and stlViewModal."""
        stl_path = os.path.join(FRONTEND_DIR, "settlement.html")
        with open(stl_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('data-i18n="new_settlement_title"', content)
        self.assertIn('data-i18n="settlement_hearing_details"', content)
        self.assertIn('data-i18n="link_blotter_case"', content)
        self.assertIn('data-i18n="save_record"', content)
        self.assertIn('data-i18n-placeholder="search_blotter_ph"', content)

    def test_users_html_modals_i18n(self):
        """Verify users.html has data-i18n attributes on addUserWizardModal, userModal, and deleteUserModal."""
        users_path = os.path.join(FRONTEND_DIR, "users.html")
        with open(users_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('data-i18n="add_new_user_title"', content)
        self.assertIn('data-i18n="edit_user_title"', content)
        self.assertIn('data-i18n="permanently_delete_user"', content)
        self.assertIn('data-i18n="temporary_password"', content)
        self.assertIn('data-i18n="e_signature"', content)
        self.assertIn('data-i18n-placeholder="type_delete_confirm"', content)

    def test_reports_html_modal_i18n(self):
        """Verify reports.html has data-i18n attributes on generateModal."""
        reports_path = os.path.join(FRONTEND_DIR, "reports.html")
        with open(reports_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('data-i18n="generate_report_title"', content)
        self.assertIn('data-i18n="date_from"', content)
        self.assertIn('data-i18n="date_to"', content)
        self.assertIn('data-i18n="zone_filter"', content)
        self.assertIn('data-i18n="export_format"', content)

    def test_blotter_export_excel_button_structure_and_translation(self):
        """Verify blotter.html export button matches specifications and dictionary contains accurate translations."""
        blotter_path = os.path.join(FRONTEND_DIR, "blotter.html")
        with open(blotter_path, "r", encoding="utf-8") as f:
            blotter_html = f.read()

        # Check export button attributes
        self.assertIn('id="exportExcelBtn"', blotter_html)
        self.assertIn('onclick="toggleExportMenu()"', blotter_html)
        self.assertIn('data-i18n="export_excel"', blotter_html)

        # Check SVG icon
        self.assertIn('<svg class="w-4 h-4 text-[#1e3a2b]"', blotter_html)
        self.assertIn('d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"', blotter_html)

        # Check span with data-i18n
        self.assertIn('<span data-i18n="export_excel">Export to Excel</span>', blotter_html)

        # Check dictionary translations in app.js
        self.assertIn('export_excel: "Export to Excel"', self.app_js)
        self.assertIn('export_excel: "I-export sa Excel"', self.app_js)
        self.assertIn('"Export to Excel": "I-export sa Excel"', self.app_js)

    def test_export_filter_modal_i18n_attributes(self):
        """Verify _ensureExportFilterModal provides data-i18n attributes on title, labels, options, and actions."""
        self.assertIn('id="bcExportFilterTitle" data-i18n="export_blotter_title"', self.app_js)
        self.assertIn('data-i18n="period_label"', self.app_js)
        self.assertIn('data-i18n="year_label"', self.app_js)
        self.assertIn('data-i18n="month_label"', self.app_js)
        self.assertIn('data-i18n="period_all"', self.app_js)
        self.assertIn('data-i18n="period_year"', self.app_js)
        self.assertIn('data-i18n="period_month"', self.app_js)
        self.assertIn('data-i18n="month_jan"', self.app_js)
        self.assertIn('data-i18n="month_feb"', self.app_js)
        self.assertIn('data-i18n="month_dec"', self.app_js)
        self.assertIn('data-i18n="download"', self.app_js)

    def test_i18n_standalone_file_content_and_exact_translations(self):
        """Verify frontend/i18n.js contains exact required Tagalog translations."""
        i18n_path = os.path.join(FRONTEND_DIR, "i18n.js")
        self.assertTrue(os.path.exists(i18n_path), "frontend/i18n.js must exist")
        with open(i18n_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('window.i18n = i18n;', content)
        self.assertIn('cancel: "Kanselahin"', content)
        self.assertTrue('import_data: "Mag-import"' in content or 'import_data: "I-import ang Datos"' in content)
        self.assertIn('export_excel: "I-export sa Excel"', content)
        self.assertIn('download: "I-download"', content)
        self.assertIn('view_edit: "Tignan at Baguhin"', content)
        self.assertIn('delete: "Burahin"', content)
        self.assertIn('import_resident_title: "Mag-import ng Datos ng Residente"', content)
        self.assertIn('export_blotter_title: "I-export ang Tala ng Blotter"', content)
        self.assertIn('period_label: "Panahon"', content)
        self.assertIn('year_label: "Taon"', content)
        self.assertIn('month_label: "Buwan"', content)
        self.assertIn('period_all: "Lahat ng Tala"', content)
        self.assertIn('period_year: "Tiyak na Taon"', content)
        self.assertIn('period_month: "Tiyak na Buwan"', content)
        self.assertIn('jan: "Enero"', content)
        self.assertIn('feb: "Pebreo"', content)
        self.assertIn('mar: "Marso"', content)
        self.assertIn('apr: "Abril"', content)
        self.assertIn('may: "Mayo"', content)
        self.assertIn('jun: "Hunyo"', content)
        self.assertIn('jul: "Hulyo"', content)
        self.assertIn('aug: "Agosto"', content)
        self.assertIn('sep: "Setyembre"', content)
        self.assertIn('oct: "Oktubre"', content)
        self.assertIn('nov: "Nobyembre"', content)
        self.assertIn('dec: "Disyembre"', content)

    def test_proper_noun_preservation_and_system_translation_coverage(self):
        """Verify isProperNounOrName and bcApplyLanguage cover table headers, badges, and option lists."""
        self.assertIn("function isProperNounOrName(text)", self.app_js)
        self.assertIn("/^Zone\\s+\\d+$/i", self.app_js)
        self.assertIn("BlotterCast", self.app_js)
        # Verify table header query in bcApplyLanguage
        self.assertIn("document.querySelectorAll('table th')", self.app_js)
        # Verify badge query in bcApplyLanguage
        self.assertIn("document.querySelectorAll('.badge, span[class*=\"badge\"], .status-badge')", self.app_js)
        # Verify select options query in bcApplyLanguage
        self.assertIn("sel.querySelectorAll('option')", self.app_js)


if __name__ == "__main__":
    unittest.main()


