"""
Unit and Integration Tests for Census CSV Import Parsing and Backend Ingestion
"""
import unittest
from app import create_app
from app.extensions import db
from app.models import CensusRecord, User, Zone


class TestCensusCsvImport(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Ensure Zone 1 exists
        if not db.session.get(Zone, 'Zone 1'):
            db.session.add(Zone(zone_id='Zone 1', label='Zone 1', description='Test Zone'))
            db.session.commit()

        # Ensure admin user
        self.admin = User.query.filter_by(username='test_admin_csv').first()
        if not self.admin:
            self.admin = User(username='test_admin_csv', password='AdminPass123!', full_name='Admin CSV', role='System Admin', status='Active')
            db.session.add(self.admin)
            db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin.id
            sess['username'] = self.admin.username
            sess['role'] = self.admin.role
            sess['full_name'] = self.admin.full_name

    def test_backend_flexible_synonym_ingestion(self):
        """Test that backend POST /api/documents.php?type=census accepts synonym keys and normalizes fields."""
        self._login()
        import uuid
        uid = uuid.uuid4().hex[:6]

        payload = {
            'surname': f'Rizal_{uid}',
            'given_name': f'Jose_{uid}',
            'middle_name': 'Protacio',
            'birth_date': '1990-06-19',
            'gender': 'Male',
            'marital_status': 'Single',
            'citizenship': 'Filipino',
            'purok': '1',
            'street_address': 'Calamba St, Mapulang Lupa',
            'household_no': 'HH-999',
            'mobile': '09171234567',
            'voter_status': 'Registered Voter',
            'job': 'Doctor',
            'status': 'Active',
        }

        res = self.client.post('/api/documents.php?type=census', json=payload, headers={'X-Bulk-Import': '1'})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['ok'])
        rec_id = data['id']

        rec = db.session.get(CensusRecord, rec_id)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.last_name, f'Rizal_{uid}')
        self.assertEqual(rec.first_name, f'Jose_{uid}')
        self.assertEqual(rec.middle_name, 'Protacio')
        self.assertEqual(rec.sex, 'Male')
        self.assertEqual(rec.zone_id, 'Zone 1')
        self.assertEqual(rec.civil_status, 'Single')
        self.assertEqual(rec.occupation, 'Doctor')


if __name__ == '__main__':
    unittest.main()
