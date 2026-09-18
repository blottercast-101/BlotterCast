"""
Unit and integration tests for Census Import Modal UI and handler specifications
"""
import os
import unittest
from app import create_app


class TestCensusImportModalUI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        census_html_path = os.path.join(self.app.static_folder, 'census.html')
        with open(census_html_path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_modal_container_and_header(self):
        # Modal overlay and box ID
        self.assertIn('id="importCensusModal"', self.html)
        self.assertIn('id="importResidentModal"', self.html)

        # Header title: "Import Resident Data", centered, serif font
        self.assertIn('Import Resident Data', self.html)
        self.assertIn('Playfair Display', self.html)
        self.assertIn('font-display', self.html)
        self.assertIn('text-center', self.html)

        # Minimalist close button ✕
        self.assertIn('closeCensusImportModal()', self.html)
        self.assertIn('d="M6 18L18 6M6 6l12 12"', self.html)

    def test_drag_and_drop_upload_container(self):
        # Light mint / soft green background tint
        self.assertIn('bg-[#edf5f0]', self.html)

        # Dashed / broken border line
        self.assertIn('border-dashed', self.html)
        self.assertIn('border-[#a3c9b1]', self.html)
        self.assertIn('rounded-2xl', self.html)

        # Center content: folder-plus icon, primary text, browse files button, hint text
        self.assertIn('Drag &amp; Drop CSV or Excel file (.xlsx, .xls) here or Click to upload', self.html)
        self.assertIn('Browse Files', self.html)
        self.assertIn('Supported types: CSV, Excel (.xlsx, .xls)', self.html)
        self.assertIn('id="censusFileInput"', self.html)

    def test_modal_footer_and_actions(self):
        # Footer container layout: full-width horizontal flex-row with justify-between
        self.assertIn('flex-row', self.html)
        self.assertIn('items-center', self.html)
        self.assertIn('justify-between', self.html)
        self.assertIn('w-full', self.html)

        # Far Left: Download template link
        self.assertIn('/templates/census_resident_template.csv', self.html)
        self.assertIn('Download Resident Census Template (.csv)', self.html)

        # Far Right: Action buttons group in horizontal row
        self.assertIn('id="cancelCensusImportBtn"', self.html)
        self.assertIn('Cancel', self.html)
        self.assertIn('closeCensusImportModal()', self.html)
        self.assertIn('bg-[#edf5f0]', self.html)

        self.assertIn('id="submitCensusImportBtn"', self.html)
        self.assertIn('executeCensusImport()', self.html)
        self.assertIn('bg-[#1e3a2b]', self.html)
        self.assertIn('Import Data', self.html)

    def test_javascript_handlers_present(self):
        # Verify required functions and event bindings exist in census.html
        self.assertIn('function openCensusImportModal', self.html)
        self.assertIn('function closeCensusImportModal', self.html)
        self.assertIn('function handleCensusDragOver', self.html)
        self.assertIn('function handleCensusDragLeave', self.html)
        self.assertIn('function handleCensusDrop', self.html)
        self.assertIn('function handleCensusFileInputChange', self.html)
        self.assertIn('function stageCensusFile', self.html)
        self.assertIn('function executeCensusImport', self.html)
        self.assertIn('function handleCensusFile', self.html)


if __name__ == '__main__':
    unittest.main()
