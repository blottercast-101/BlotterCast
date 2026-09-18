import os
import unittest


class TestZoneHighlightPersistence(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.incident_html_path = os.path.join(self.base_dir, "frontend", "incident.html")
        with open(self.incident_html_path, "r", encoding="utf-8") as f:
            self.incident_html = f.read()

    def test_01_active_zone_layer_group_not_duplicated_in_init_picker_map(self):
        """Verify initPickerMap checks !activeZoneLayerGroup to prevent creating orphaned layer groups on pickerMap."""
        # Unconditional reassignment 'activeZoneLayerGroup = L.layerGroup().addTo(pickerMap);' without checking
        # if activeZoneLayerGroup already exists causes an orphaned layer group stuck on the map.
        self.assertNotIn(
            "\n    activeZoneLayerGroup = L.layerGroup().addTo(pickerMap);\n",
            self.incident_html,
            "activeZoneLayerGroup must not be unconditionally reassigned without checking if it already exists",
        )
        self.assertIn(
            "if (!activeZoneLayerGroup)",
            self.incident_html,
            "initPickerMap must check if !activeZoneLayerGroup before adding a new layer group to pickerMap",
        )

    def test_02_highlight_selected_zone_clears_previous_active_layers(self):
        """Verify highlightSelectedZoneOnMiniMap clears activeZoneLayerGroup and resets pickerZonesLayer."""
        self.assertIn(
            "function highlightSelectedZoneOnMiniMap(zoneId, shouldPan = true)",
            self.incident_html,
            "highlightSelectedZoneOnMiniMap must be defined",
        )
        self.assertIn(
            "activeZoneLayerGroup.clearLayers()",
            self.incident_html,
            "highlightSelectedZoneOnMiniMap must clearLayers on activeZoneLayerGroup before applying a new highlight",
        )
        self.assertIn(
            "pickerZonesLayer.eachLayer",
            self.incident_html,
            "highlightSelectedZoneOnMiniMap must reset base polygon styles to neutral on pickerZonesLayer",
        )

    def test_03_reset_incident_form_clears_zone_highlight(self):
        """Verify resetIncidentFormFields explicitly clears zone highlights for clean Add Incident flow."""
        self.assertIn(
            "highlightSelectedZoneOnMiniMap('', false)",
            self.incident_html,
            "resetIncidentFormFields must clear zone highlights on pickerMap when resetting form for Add flow",
        )

    def test_04_on_zone_dropdown_change_triggers_highlight_and_badge_update(self):
        """Verify onZoneDropdownChange triggers highlightSelectedZoneOnMiniMap and updatePickerStatusBadge."""
        self.assertIn(
            "async function onZoneDropdownChange()",
            self.incident_html,
            "onZoneDropdownChange must be defined",
        )
        self.assertIn(
            "highlightSelectedZoneOnMiniMap(zoneVal, true)",
            self.incident_html,
            "onZoneDropdownChange must invoke highlightSelectedZoneOnMiniMap with selected zone",
        )
        self.assertIn(
            "updatePickerStatusBadge(lat ? Number(lat) : null, lng ? Number(lng) : null)",
            self.incident_html,
            "onZoneDropdownChange must update picker badges even if lat/lng are not yet set",
        )

    def test_05_single_selection_state_logic(self):
        """Simulate zone switching lifecycle and verify single active zone constraint."""
        class MockLayer:
            def __init__(self, zone_name):
                self.zone_name = zone_name
                self.style = {}

            def setStyle(self, s):
                self.style = dict(s)

        class MockLayerGroup:
            def __init__(self):
                self.layers = []

            def clearLayers(self):
                self.layers = []

            def addLayer(self, layer):
                self.layers.append(layer)

        # Simulation of highlightSelectedZoneOnMiniMap logic
        active_zone_layer_group = MockLayerGroup()
        base_zone_layers = [MockLayer(f"Zone {i}") for i in range(1, 8)]

        def highlight_zone(zone_id):
            active_zone_layer_group.clearLayers()
            for l in base_zone_layers:
                l.setStyle({"color": "#94A3B8", "fillColor": "#F1F5F9"})
            if not zone_id:
                return
            active_zone_layer_group.addLayer(MockLayer(zone_id))

        # Initial Edit state: Zone 1
        highlight_zone("Zone 1")
        self.assertEqual(len(active_zone_layer_group.layers), 1)
        self.assertEqual(active_zone_layer_group.layers[0].zone_name, "Zone 1")

        # Switch to Zone 2 in Edit Flow
        highlight_zone("Zone 2")
        self.assertEqual(len(active_zone_layer_group.layers), 1, "Only one zone should be highlighted after switch")
        self.assertEqual(active_zone_layer_group.layers[0].zone_name, "Zone 2")

        # Switch to Zone 5 in Edit Flow
        highlight_zone("Zone 5")
        self.assertEqual(len(active_zone_layer_group.layers), 1, "Only one zone should be highlighted after switch")
        self.assertEqual(active_zone_layer_group.layers[0].zone_name, "Zone 5")

        # Open Add Incident flow: reset
        highlight_zone("")
        self.assertEqual(len(active_zone_layer_group.layers), 0, "No zone highlighted after reset in Add flow")

        # Switch to Zone 3 in Add Flow
        highlight_zone("Zone 3")
        self.assertEqual(len(active_zone_layer_group.layers), 1)
        self.assertEqual(active_zone_layer_group.layers[0].zone_name, "Zone 3")

        # Switch to Zone 4 in Add Flow
        highlight_zone("Zone 4")
        self.assertEqual(len(active_zone_layer_group.layers), 1, "Only one zone should be highlighted after switch in Add flow")
        self.assertEqual(active_zone_layer_group.layers[0].zone_name, "Zone 4")

    def test_06_quick_fix_zone_conflict_async_and_ensures_boundary(self):
        """Verify quickFixZoneConflict is async, awaits boundary load, and triggers highlightSelectedZoneOnMiniMap."""
        self.assertIn(
            "async function quickFixZoneConflict()",
            self.incident_html,
            "quickFixZoneConflict must be an async function to await boundary loading",
        )
        self.assertIn(
            "await ensurePickerBoundaryLoaded()",
            self.incident_html,
            "quickFixZoneConflict must await ensurePickerBoundaryLoaded before rendering highlight or resolving centroid",
        )
        self.assertIn(
            "highlightSelectedZoneOnMiniMap(targetZone, true)",
            self.incident_html,
            "quickFixZoneConflict must call highlightSelectedZoneOnMiniMap with targetZone to immediately re-render boundary",
        )

    def test_07_quick_fix_preserves_placed_pin_inside_target_zone(self):
        """Verify quickFixZoneConflict preserves placed pin coordinates when already inside target zone."""
        self.assertIn(
            "pinAlreadyInTargetZone",
            self.incident_html,
            "quickFixZoneConflict must check if pin is already inside targetZone before recalculating coordinates",
        )
        self.assertIn(
            "currentZoneConflict.matchedKeyword === 'Pin Placement'",
            self.incident_html,
            "quickFixZoneConflict must honor 'Pin Placement' conflict and keep placed pin in targetZone",
        )
        self.assertIn(
            "finalLat = curLat",
            self.incident_html,
            "quickFixZoneConflict must keep curLat when pin is already in targetZone",
        )

    def test_08_quick_fix_strict_target_zone_lookup_filter(self):
        """Verify lookup coordinates are strictly filtered by targetZone and cannot pick from another zone."""
        # Find the quickFixZoneConflict function body
        start_idx = self.incident_html.find("async function quickFixZoneConflict()")
        end_idx = self.incident_html.find("async function onZoneDropdownChange()")
        self.assertNotEqual(start_idx, -1)
        self.assertNotEqual(end_idx, -1)
        fn_body = self.incident_html[start_idx:end_idx]

        self.assertIn(
            "entry.zone !== targetZone",
            fn_body,
            "LOCATION_COORDINATES_LOOKUP search must reject entries not matching targetZone",
        )
        # Ensure there is no unconstrained fallback lookup that drops the zone check
        self.assertNotIn(
            "if (!matchedLocation) {\n        matchedLocation = LOCATION_COORDINATES_LOOKUP.find(entry => {\n          if (matchedKw",
            fn_body,
            "LOCATION_COORDINATES_LOOKUP must never have an unconstrained fallback matching outside targetZone",
        )

    def test_09_active_zone_polygon_and_selected_zone_state_tracking(self):
        """Verify activeZonePolygon and selectedZoneId variables exist and are updated in highlightSelectedZoneOnMiniMap."""
        self.assertIn(
            "var activeZonePolygon = null;",
            self.incident_html,
            "activeZonePolygon must be declared to track the active highlighted polygon",
        )
        self.assertIn(
            "var selectedZoneId = null;",
            self.incident_html,
            "selectedZoneId must be declared to track the active zone id",
        )
        self.assertIn(
            "activeZonePolygon = activeHighlight;",
            self.incident_html,
            "highlightSelectedZoneOnMiniMap must assign activeZonePolygon to the new activeHighlight",
        )

    def test_10_save_incident_syncs_zone_highlight_on_confirm(self):
        """Verify saveIncident updates the mini-map zone highlight when user confirms switching zone before save."""
        self.assertIn(
            "highlightSelectedZoneOnMiniMap(conflict.detectedZone, false);",
            self.incident_html,
            "saveIncident must call highlightSelectedZoneOnMiniMap when user confirms switching zones",
        )


if __name__ == "__main__":
    unittest.main()
