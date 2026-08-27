"""
Unit and Integration Tests for BlotterCast ML & Geospatial Forecasting Pipeline
"""
import json
import os
import sys
import unittest

from app import create_app
from app.extensions import db
from app.models import Incident, MlRun, User, Zone

from ml.engine import (
    OFFICIAL_ZONES,
    CATEGORIES,
    build_spatiotemporal_panel,
    train_occurrence_model,
    train_type_model,
    train_hotspot_model,
    build_category_probability_cache,
    compute_zone_forecasts,
)


class TestMLPipeline(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_official_zones_definition(self):
        """Ensure official zones are strictly Zone 1 to Zone 7."""
        self.assertEqual(len(OFFICIAL_ZONES), 7)
        self.assertEqual(OFFICIAL_ZONES, ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5', 'Zone 6', 'Zone 7'])

    def test_engine_training_and_dynamic_metrics(self):
        """Verify dynamic scikit-learn metrics calculation on database incidents."""
        import pandas as pd
        incidents = Incident.query.filter_by(archived=False).all()
        self.assertGreater(len(incidents), 10, "Need at least 10 incidents for ML training")

        df = pd.DataFrame([{
            'id': inc.id,
            'date': inc.incident_date,
            'time_reported': inc.time_reported,
            'hour': inc.hour,
            'zone': inc.zone_id,
            'category': inc.category,
            'priority': inc.priority,
            'status': inc.status,
        } for inc in incidents])

        # 1. Panel generation
        panel = build_spatiotemporal_panel(df)
        self.assertFalse(panel.empty)
        self.assertIn('has_incident', panel.columns)
        self.assertIn('days_since_last', panel.columns)

        # 2. Incident Occurrence (Random Forest) -> Test Accuracy & Losses
        occ_metrics, occ_model, occ_cols = train_occurrence_model(panel)
        self.assertIn('accuracy', occ_metrics)
        self.assertIn('f1', occ_metrics)
        self.assertIn('train_loss', occ_metrics)
        self.assertIn('test_loss', occ_metrics)
        self.assertIn('balanced_accuracy', occ_metrics)
        self.assertGreater(occ_metrics['train_samples'], 0)
        self.assertGreater(occ_metrics['test_samples'], 0)
        self.assertGreaterEqual(occ_metrics['accuracy'], 0.0)
        self.assertLessEqual(occ_metrics['accuracy'], 1.0)
        print(f"[TEST] Random Forest Occurrence Accuracy: {occ_metrics['accuracy'] * 100:.1f}%, Train Loss: {occ_metrics['train_loss']}, Test Loss: {occ_metrics['test_loss']}")

        # 3. Incident Type (Gradient Boosting) -> Test Macro F1 & Losses
        type_metrics, type_model, type_cols = train_type_model(df)
        self.assertIn('macroF1', type_metrics)
        self.assertIn('weightedF1', type_metrics)
        self.assertIn('train_loss', type_metrics)
        self.assertIn('test_loss', type_metrics)
        self.assertGreaterEqual(type_metrics['macroF1'], 0.0)
        self.assertLessEqual(type_metrics['macroF1'], 1.0)
        print(f"[TEST] Gradient Boosting Type Macro F1: {type_metrics['macroF1'] * 100:.1f}%, Weighted F1: {type_metrics['weightedF1'] * 100:.1f}%")

        # 4. Hotspot Risk (Gradient Boosting) -> Spatial Accuracy & Losses
        hot_metrics, hot_model, hot_cols = train_hotspot_model(panel)
        self.assertIn('accuracy', hot_metrics)
        self.assertIn('train_loss', hot_metrics)
        self.assertIn('test_loss', hot_metrics)
        self.assertGreaterEqual(hot_metrics['accuracy'], 0.0)
        self.assertLessEqual(hot_metrics['accuracy'], 1.0)
        print(f"[TEST] Gradient Boosting Hotspot Accuracy: {hot_metrics['accuracy'] * 100:.1f}%, Train Loss: {hot_metrics['train_loss']}, Test Loss: {hot_metrics['test_loss']}")

        # 5. Zone forecasts across 7 and 14 days
        cat_cache = build_category_probability_cache(type_model, type_cols)
        forecasts = compute_zone_forecasts(
            panel=panel,
            hotspot_model=hot_model,
            hotspot_cols=hot_cols,
            type_model=type_model,
            type_cols=type_cols,
            cat_cache=cat_cache,
            raw_df=df,
            horizon=14
        )
        self.assertEqual(len(forecasts), 7)
        for zf in forecasts:
            self.assertIn(zf['zone'], OFFICIAL_ZONES)
            self.assertEqual(len(zf['dailyProbs']), 14)
            self.assertEqual(len(zf['forecastDates']), 14)
            self.assertGreaterEqual(zf['expectedCount14d'], zf['expectedCount7d'])

    def test_zone_density_endpoint(self):
        """Test GET /api/analytics/zone-density endpoint."""
        # Login as Desk Officer
        with self.client.session_transaction() as sess:
            user = User.query.filter_by(username="jdelacuz").first()
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["username"] = user.username

        res = self.client.get("/api/analytics/zone-density")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(len(data.get("zones", [])), 7)
        self.assertIn("topRiskZone", data)
        self.assertIn(data["topRiskZone"], OFFICIAL_ZONES)

        for z in data["zones"]:
            self.assertIn(z["zone_id"], OFFICIAL_ZONES)
            self.assertIn("historicalCount", z)
            self.assertIn("predictedOccurrenceProb", z)
            self.assertIn("densityScore", z)
            self.assertIn("tier", z)
            self.assertIn(z["tier"], ["Low", "Medium", "Elevated", "High"])

        print(f"[TEST] Zone Density endpoint returned 7 official zones with top risk zone: {data['topRiskZone']}")


if __name__ == "__main__":
    unittest.main()
