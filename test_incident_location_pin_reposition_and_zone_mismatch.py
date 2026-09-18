"""
Unit and integration tests for Incident Location Detail Pin Auto-Repositioning and Zone Mismatch Warning
"""
import os
import unittest
from app import create_app


class TestIncidentLocationPinAndZoneMismatch(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        incident_html_path = os.path.join(self.app.static_folder, 'incident.html')
        with open(incident_html_path, 'r', encoding='utf-8') as f:
            self.html = f.read()

    def test_location_coordinates_lookup_and_resolver_exist(self):
        """Verify LOCATION_COORDINATES_LOOKUP and resolveLocationCoordinates are defined."""
        self.assertIn("var LOCATION_COORDINATES_LOOKUP =", self.html)
        self.assertIn("function resolveLocationCoordinates(", self.html)
        
        # Verify Mitay 1 is present with Zone 4 coordinates
        self.assertIn("'Mitay 1'", self.html)
        self.assertIn("14.887000", self.html)
        self.assertIn("120.963500", self.html)

    def test_on_location_detail_input_auto_repositions_pin_without_changing_zone_dropdown(self):
        """Verify onLocationDetailInput resolves coordinates, repositions pin, and preserves zone dropdown."""
        self.assertIn("async function onLocationDetailInput()", self.html)
        self.assertIn("const resolved = resolveLocationCoordinates(locText);", self.html)
        
        # Must pass autoUpdateZone=false so zone dropdown is NOT automatically replaced
        self.assertIn("setPickerCoordinates(resolved.lat, resolved.lng, true, false);", self.html)

    def test_set_picker_coordinates_respects_auto_update_zone_flag(self):
        """Verify setPickerCoordinates accepts autoUpdateZone flag and guards zone dropdown update."""
        self.assertIn("function setPickerCoordinates(lat, lng, pan = true, autoUpdateZone = true)", self.html)
        self.assertIn("if (autoUpdateZone) {", self.html)

    def test_check_zone_location_conflict_detects_placed_pin_zone_mismatch(self):
        """Verify checkZoneLocationConflict compares placed pin coordinates against selectedZone."""
        self.assertIn("function checkZoneLocationConflict()", self.html)
        self.assertIn("pinDetectedZone = detectZoneFromCoordinates(Number(latVal), Number(lngVal));", self.html)
        self.assertIn("if (pinDetectedZone && pinDetectedZone.zone && pinDetectedZone.zone !== selectedZone)", self.html)
        self.assertIn("Placed pin is located inside", self.html)
        self.assertIn("Switch to ${pinDetectedZone.zone}", self.html)

    def test_edit_incident_preserves_saved_record_zone(self):
        """Verify editIncident modal loads coordinates without overwriting the record's zone."""
        self.assertIn("setPickerCoordinates(r.lat, r.lng, true, false);", self.html)

    def test_location_detail_input_has_input_and_change_handlers(self):
        """Verify if_location input tag has both oninput and onchange handlers."""
        self.assertIn('id="if_location"', self.html)
        self.assertIn('oninput="onLocationDetailInput()"', self.html)
        self.assertIn('onchange="onLocationDetailInput()"', self.html)


if __name__ == '__main__':
    unittest.main()
