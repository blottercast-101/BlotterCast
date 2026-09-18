"""
Tests for Census CSV Template Download and Import Modal Markup Integration
"""
import os
import unittest
from app import create_app


class TestCensusCsvTemplateDownload(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_census_csv_template_file_exists(self):
        template_path = os.path.join(self.app.static_folder, 'templates', 'census_resident_template.csv')
        self.assertTrue(os.path.exists(template_path), f"File not found at {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
            self.assertIn("LAST NAME", header)
            self.assertIn("FIRST NAME", header)
            self.assertIn("ZONE", header)

    def test_census_csv_template_download_endpoint(self):
        res = self.client.get('/templates/census_resident_template.csv')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            'text/csv' in res.content_type or 'application/vnd.ms-excel' in res.content_type,
            f"Unexpected content type: {res.content_type}"
        )
        data = res.get_data(as_text=True)
        self.assertTrue(data.startswith("LAST NAME,FIRST NAME"))
        self.assertIn("Dela Cruz,Juan", data)

    def test_census_modal_html_contains_template_download_banner(self):
        census_html_path = os.path.join(self.app.static_folder, 'census.html')
        with open(census_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Verify #importResidentModal exists
        self.assertIn('id="importResidentModal"', content)

        # Verify exact required banner structure
        self.assertIn('/templates/census_resident_template.csv', content)
        self.assertIn('Resident Census Template (.csv)', content)
        self.assertIn('bg-[#edf5f0]', content)
        self.assertIn('border-[#d8e8dd]', content)
        self.assertIn('text-[#1e3a2b]', content)


if __name__ == '__main__':
    unittest.main()
