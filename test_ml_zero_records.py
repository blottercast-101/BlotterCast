"""
Unit and Integration Tests for ML Zero-Record & Insufficient Data Handling
"""
import json
import os
import sys
import unittest
import pandas as pd
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import Incident, MlRun, User, Zone

from ml.engine import (
    OFFICIAL_ZONES,
    train_occurrence_model,
    train_type_model,
    train_hotspot_model,
    compute_zone_forecasts,
    predict_top_category,
)
import ml.service as ml_service


class TestMLZeroRecords(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.ml_client = ml_service.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_engine_metrics_on_empty_and_insufficient_data(self):
        """Ensure ML engine metrics return None/null instead of hardcoded 100% or synthetic values."""
        empty_df = pd.DataFrame()
        empty_panel = pd.DataFrame()

        # 1. Type model on empty df
        metrics, model, cols = train_type_model(empty_df)
        self.assertIsNone(metrics['accuracy'])
        self.assertIsNone(metrics['macroF1'])
        self.assertIsNone(metrics['incident_type_f1'])
        self.assertEqual(len(cols), 0)

        # 2. Type model on 1 category only (e.g. 3 records of Public Disturbance)
        single_cat_df = pd.DataFrame([
            {'date': '2026-08-01', 'zone': 'Zone 1', 'category': 'Public Disturbance', 'hour': 10},
            {'date': '2026-08-02', 'zone': 'Zone 1', 'category': 'Public Disturbance', 'hour': 14},
            {'date': '2026-08-03', 'zone': 'Zone 2', 'category': 'Public Disturbance', 'hour': 18},
        ])
        metrics_single, _, _ = train_type_model(single_cat_df)
        self.assertIsNone(metrics_single['accuracy'], "Should not be hardcoded 1.0 or 100%")
        self.assertIsNone(metrics_single['incident_type_f1'], "Should not be hardcoded 100%")
        self.assertIsNone(metrics_single['macroF1'])

        # 3. Hotspot model on empty panel
        hot_metrics, _, _ = train_hotspot_model(empty_panel)
        self.assertIsNone(hot_metrics['accuracy'])
        self.assertIsNone(hot_metrics['f1'])

        # 4. Predict top category on uninitialized model
        top_cat, top_p = predict_top_category(model, cols, 'Zone 1', 2, 14)
        self.assertIsNone(top_cat)
        self.assertIsNone(top_p)

        # 5. Compute zone forecasts on empty panel
        forecasts = compute_zone_forecasts(
            panel=empty_panel,
            hotspot_model=None,
            hotspot_cols=[],
            type_model=None,
            type_cols=[],
            cat_cache={},
            raw_df=empty_df,
        )
        self.assertEqual(forecasts, [])

    def test_ml_service_zero_records_endpoints(self):
        """Test ML service endpoints (/latest, /train, /predict) when DB has 0 records."""
        with patch.object(ml_service, 'get_active_incident_count', return_value=0), \
             patch.object(ml_service, 'load_incidents', return_value=pd.DataFrame()):
            
            # 1. GET /latest with 0 records
            res_latest = self.ml_client.get('/latest')
            self.assertEqual(res_latest.status_code, 200)
            data_latest = res_latest.get_json()
            self.assertFalse(data_latest['ok'])
            self.assertEqual(data_latest['status'], 'insufficient_data')
            self.assertEqual(data_latest['record_count'], 0)
            self.assertIn('Not enough incident records', data_latest['message'])
            self.assertNotIn('zoneRisk', data_latest)

            # 2. POST /train with 0 records
            res_train = self.ml_client.post('/train', json={})
            self.assertEqual(res_train.status_code, 200)
            data_train = res_train.get_json()
            self.assertFalse(data_train['ok'])
            self.assertEqual(data_train['status'], 'insufficient_data')
            self.assertEqual(data_train['record_count'], 0)
            self.assertIn('Not enough incident records', data_train['message'])

            # 3. POST /predict with 0 records
            res_pred = self.ml_client.post('/predict', json={'zone': 'Zone 1', 'hour': 12})
            self.assertEqual(res_pred.status_code, 200)
            data_pred = res_pred.get_json()
            self.assertFalse(data_pred['ok'])
            self.assertEqual(data_pred['status'], 'insufficient_data')
            self.assertEqual(data_pred['record_count'], 0)

    def test_ml_service_below_threshold_endpoints(self):
        """Test ML service endpoints when record count is below minimum threshold (< 10 records)."""
        mock_df = pd.DataFrame([
            {'id': i, 'date': '2026-08-01', 'time_reported': '10:00', 'zone': 'Zone 1', 'hour': 10, 'category': 'Theft', 'priority': 'Low', 'status': 'Pending'}
            for i in range(5)
        ])

        with patch.object(ml_service, 'get_active_incident_count', return_value=5), \
             patch.object(ml_service, 'load_incidents', return_value=mock_df):
            
            # 1. GET /latest with 5 records
            res_latest = self.ml_client.get('/latest')
            data_latest = res_latest.get_json()
            self.assertFalse(data_latest['ok'])
            self.assertEqual(data_latest['status'], 'insufficient_data')
            self.assertEqual(data_latest['record_count'], 5)

            # 2. POST /train with 5 records
            res_train = self.ml_client.post('/train', json={})
            data_train = res_train.get_json()
            self.assertFalse(data_train['ok'])
            self.assertEqual(data_train['status'], 'insufficient_data')
            self.assertEqual(data_train['record_count'], 5)

            # 3. POST /predict with 5 records
            res_pred = self.ml_client.post('/predict', json={'zone': 'Zone 1', 'hour': 12})
            data_pred = res_pred.get_json()
            self.assertFalse(data_pred['ok'])
            self.assertEqual(data_pred['status'], 'insufficient_data')
            self.assertEqual(data_pred['record_count'], 5)


if __name__ == '__main__':
    unittest.main()
