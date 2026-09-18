import unittest
import os
import re

class TestCensusIncidentSettlementClearanceI18n(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.census_path = os.path.join(self.base_dir, 'frontend', 'census.html')
        self.incident_path = os.path.join(self.base_dir, 'frontend', 'incident.html')
        self.settlement_path = os.path.join(self.base_dir, 'frontend', 'settlement.html')
        self.clearance_path = os.path.join(self.base_dir, 'frontend', 'clearance.html')
        self.i18n_path = os.path.join(self.base_dir, 'frontend', 'i18n.js')
        self.app_path = os.path.join(self.base_dir, 'frontend', 'app.js')

    def test_census_header_layout_and_alignment(self):
        """Test census header is flex with justify-between and buttons container has ml-auto"""
        with open(self.census_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check header classes
        self.assertIn('justify-between', content)
        self.assertIn('w-full', content)
        
        # Check action button group has ml-auto
        btn_container_pattern = r'<div class="[^"]*ml-auto[^"]*">\s*<button[^>]*openCensusImportModal'
        self.assertRegex(content, btn_container_pattern)

    def test_census_i18n_attributes(self):
        """Test census.html has all required data-i18n and placeholder attributes"""
        with open(self.census_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_keys = [
            'data-i18n="barangay_census"',
            'data-i18n="census_description"',
            'data-i18n="add_resident"',
            'data-i18n="total_residents"',
            'data-i18n="registered_in_barangay"',
            'data-i18n="total_households"',
            'data-i18n="indexed_residences"',
            'data-i18n="registered_voters"',
            'data-i18n="active_precinct_voters"',
            'data-i18n="senior_citizens"',
            'data-i18n="senior_care_sub"',
            'data-i18n="resident_records"',
            'data-i18n-placeholder="search_name_address_placeholder"'
        ]
        for key in required_keys:
            self.assertIn(key, content, f"Missing {key} in census.html")

    def test_incident_i18n_attributes(self):
        """Test incident.html has all required data-i18n and placeholder attributes"""
        with open(self.incident_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_keys = [
            'data-i18n="incident_reports"',
            'data-i18n="incident_description"',
            'data-i18n="new_incident_report"',
            'data-i18n="total_reports"',
            'data-i18n="incident_logs_on_record"',
            'data-i18n="high_priority"',
            'data-i18n="urgent_attention_required"',
            'data-i18n="under_investigation"',
            'data-i18n="in_progress_by_officers"',
            'data-i18n="referred_status"',
            'data-i18n="referred_to_blotter_lupon"',
            'data-i18n-placeholder="search_incident_placeholder"'
        ]
        for key in required_keys:
            self.assertIn(key, content, f"Missing {key} in incident.html")

    def test_settlement_i18n_attributes(self):
        """Test settlement.html has all required data-i18n and placeholder attributes"""
        with open(self.settlement_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_keys = [
            'data-i18n="settlement_monitoring_title"',
            'data-i18n="settlement_monitoring_desc"',
            'data-i18n="add_settlement_record"',
            'data-i18n="total_cases"',
            'data-i18n="status_pending"',
            'data-i18n="status_complied"',
            'data-i18n="status_not_complied"',
            'data-i18n="settlement_records"',
            'data-i18n-placeholder="search_settlement_placeholder"'
        ]
        for key in required_keys:
            self.assertIn(key, content, f"Missing {key} in settlement.html")

    def test_clearance_i18n_attributes(self):
        """Test clearance.html has all required data-i18n and placeholder attributes"""
        with open(self.clearance_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_keys = [
            'data-i18n="barangay_clearance"',
            'data-i18n="clearance_description"',
            'data-i18n="issue_new_clearance"',
            'data-i18n="issued_this_month"',
            'data-i18n="total_this_year"',
            'data-i18n="revenue_fees"',
            'data-i18n="issuance_log"',
            'data-i18n="certificate_preview"',
            'data-i18n="print"',
            'data-i18n-placeholder="search_clearance_placeholder"'
        ]
        for key in required_keys:
            self.assertIn(key, content, f"Missing {key} in clearance.html")

    def test_dictionary_key_symmetry_in_i18n_js(self):
        """Test all new keys exist in both en and tl sections in i18n.js"""
        with open(self.i18n_path, 'r', encoding='utf-8') as f:
            content = f.read()

        test_keys = [
            'barangay_census', 'census_description', 'add_resident', 'total_residents',
            'registered_in_barangay', 'total_households', 'indexed_residences',
            'registered_voters', 'active_precinct_voters', 'senior_citizens',
            'senior_care_sub', 'resident_records', 'search_name_address_placeholder',
            'incident_description', 'total_reports', 'incident_logs_on_record',
            'high_priority', 'urgent_attention_required', 'under_investigation',
            'in_progress_by_officers', 'referred_status', 'referred_to_blon_record',
            'referred_to_blotter_lupon', 'search_incident_placeholder',
            'settlement_monitoring_title', 'settlement_monitoring_desc',
            'total_cases', 'status_pending', 'status_complied', 'status_not_complied',
            'add_settlement_record', 'settlement_records', 'search_settlement_placeholder',
            'barangay_clearance', 'clearance_description', 'issue_new_clearance',
            'issued_this_month', 'total_this_year', 'revenue_fees', 'issuance_log',
            'certificate_preview', 'print', 'search_clearance_placeholder'
        ]

        # Extract en and tl blocks
        en_match = re.search(r'en:\s*\{(.*?)\n\s*\},?\s*tl:\s*\{', content, re.DOTALL)
        tl_match = re.search(r'tl:\s*\{(.*?)\n\s*\};?\s*(?:window|$)', content, re.DOTALL)

        self.assertIsNotNone(en_match, "en dictionary not found in i18n.js")
        self.assertIsNotNone(tl_match, "tl dictionary not found in i18n.js")

        en_text = en_match.group(1)
        tl_text = tl_match.group(1)

        for k in test_keys:
            if k == 'referred_to_blon_record': continue
            self.assertIn(f'{k}:', en_text, f"Key {k} missing in en of i18n.js")
            self.assertIn(f'{k}:', tl_text, f"Key {k} missing in tl of i18n.js")

    def test_dictionary_key_symmetry_in_app_js(self):
        """Test all new keys exist in both en and tl sections in app.js"""
        with open(self.app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        test_keys = [
            'barangay_census', 'census_description', 'add_resident', 'total_residents',
            'registered_in_barangay', 'total_households', 'indexed_residences',
            'registered_voters', 'active_precinct_voters', 'senior_citizens',
            'senior_care_sub', 'resident_records', 'search_name_address_placeholder',
            'incident_description', 'total_reports', 'incident_logs_on_record',
            'high_priority', 'urgent_attention_required', 'under_investigation',
            'in_progress_by_officers', 'referred_status',
            'referred_to_blotter_lupon', 'search_incident_placeholder',
            'settlement_monitoring_title', 'settlement_monitoring_desc',
            'total_cases', 'status_pending', 'status_complied', 'status_not_complied',
            'add_settlement_record', 'settlement_records', 'search_settlement_placeholder',
            'barangay_clearance', 'clearance_description', 'issue_new_clearance',
            'issued_this_month', 'total_this_year', 'revenue_fees', 'issuance_log',
            'certificate_preview', 'print', 'search_clearance_placeholder'
        ]

        en_match = re.search(r'(?:const\s+i18n\s*=\s*|window\.i18n\s*=\s*)\{\s*en:\s*\{(.*?)\n\s*\},?\s*tl:\s*\{', content, re.DOTALL)
        tl_match = re.search(r'tl:\s*\{(.*?)\n\s*\};?\s*(?:function|const|let|var|window|$)', content, re.DOTALL)

        self.assertIsNotNone(en_match, "window.i18n.en not found in app.js")
        self.assertIsNotNone(tl_match, "window.i18n.tl not found in app.js")

        en_text = en_match.group(1)
        tl_text = tl_match.group(1)

        for k in test_keys:
            self.assertIn(f'{k}:', en_text, f"Key {k} missing in en of app.js")
            self.assertIn(f'{k}:', tl_text, f"Key {k} missing in tl of app.js")

if __name__ == '__main__':
    unittest.main()
