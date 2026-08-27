import unittest
import uuid
from datetime import date, time
from app import create_app
from app.extensions import db
from app.models import (
    AuditLog,
    BarangayClearance,
    BarangayNonResidency,
    BarangayResidency,
    BlotterRecord,
    CensusRecord,
    Incident,
    IndigencyCertificate,
    Notification,
    User,
    Zone,
)


class TestResidentsBatchDelete(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Ensure a test zone exists
        if not db.session.get(Zone, 'Zone 1'):
            db.session.add(Zone(zone_id='Zone 1', label='Zone 1', description='Test Zone'))
            db.session.commit()

        # Create test users if not existing
        self.admin_user = User.query.filter_by(username='test_admin_census').first()
        if not self.admin_user:
            self.admin_user = User(username='test_admin_census', password='AdminPass123!', full_name='Admin User', role='System Admin', status='Active')
            db.session.add(self.admin_user)
            db.session.commit()

        self.desk_user = User.query.filter_by(username='test_desk_census').first()
        if not self.desk_user:
            self.desk_user = User(username='test_desk_census', password='DeskPass123!', full_name='Desk Officer User', role='Desk Officer', status='Active')
            db.session.add(self.desk_user)
            db.session.commit()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def _login(self, username, role):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 9999
            sess['username'] = username
            sess['role'] = role
            sess['full_name'] = f"{role} User"

    def _uid(self):
        return uuid.uuid4().hex[:6]

    def test_batch_archive_and_restore_residents(self):
        """Test batch archiving active residents and then batch restoring them."""
        self._login('test_admin_census', 'System Admin')
        uid = self._uid()

        # Create two test residents
        r1 = CensusRecord(resident_no=f'RES-{uid}1', last_name='Batumbakal', first_name='Juan', zone_id='Zone 1', status='Active', archived=False)
        r2 = CensusRecord(resident_no=f'RES-{uid}2', last_name='Dalisay', first_name='Cardo', zone_id='Zone 1', status='Active', archived=False)
        db.session.add_all([r1, r2])
        db.session.commit()

        # 1. Batch Archive
        res = self.client.post('/api/records.php?type=census&action=batch_archive', json={'ids': [r1.id, r2.id]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['count'], 2)

        # Verify archived status in DB
        db.session.refresh(r1)
        db.session.refresh(r2)
        self.assertTrue(r1.archived)
        self.assertTrue(r2.archived)

        # 2. Batch Restore
        res_restore = self.client.post('/api/records.php?type=census&action=batch_restore', json={'ids': [r1.id, r2.id]})
        self.assertEqual(res_restore.status_code, 200)
        data_restore = res_restore.get_json()
        self.assertTrue(data_restore['ok'])
        self.assertEqual(data_restore['count'], 2)

        db.session.refresh(r1)
        db.session.refresh(r2)
        self.assertFalse(r1.archived)
        self.assertFalse(r2.archived)

    def test_permanent_delete_rejects_unarchived_residents(self):
        """Active (unarchived) residents must NOT be permanently deleted directly."""
        self._login('test_admin_census', 'System Admin')
        uid = self._uid()

        r = CensusRecord(resident_no=f'RES-{uid}', last_name='ActiveResident', first_name='Test', zone_id='Zone 1', status='Active', archived=False)
        db.session.add(r)
        db.session.commit()

        # Try single permanent delete
        res_single = self.client.delete(f'/api/documents.php?type=census&id={r.id}&permanent=1')
        self.assertEqual(res_single.status_code, 400)
        self.assertIn('Only archived records can be permanently deleted', res_single.get_json()['error'])

        # Try batch permanent delete
        res_batch = self.client.post('/api/records.php?type=census&action=batch_permanent_delete&permanent=1', json={'ids': [r.id]})
        self.assertEqual(res_batch.status_code, 400)
        self.assertIn('Only archived records can be permanently deleted', res_batch.get_json()['error'])

    def test_batch_permanent_delete_cascade_and_set_null_integrity(self):
        """
        Verify relational integrity upon permanent delete of archived residents:
        - Incidents: reporter_resident_id, complainant_resident_id set to NULL (incident report retained)
        - Blotter records: complainant_id, respondent_id set to NULL (blotter record retained)
        - Certificates: BarangayClearance, Residency, NonResidency, Indigency cascade deleted
        - Notifications: deleted
        - Census records: deleted
        """
        self._login('test_admin_census', 'System Admin')
        uid = self._uid()

        r1 = CensusRecord(resident_no=f'RES-{uid}A', last_name='ComplainantRes', first_name='Alice', zone_id='Zone 1', status='Active', archived=True)
        r2 = CensusRecord(resident_no=f'RES-{uid}B', last_name='RespondentRes', first_name='Bob', zone_id='Zone 1', status='Active', archived=True)
        db.session.add_all([r1, r2])
        db.session.commit()

        # Create linked Incident
        inc = Incident(
            report_no=f'INC-{uid}',
            incident_date=date(2026, 8, 1),
            time_reported=time(10, 0),
            hour=10,
            zone_id='Zone 1',
            category='Theft',
            reporter='Alice ComplainantRes',
            reporter_resident_id=r1.id,
            complainant='Alice ComplainantRes',
            complainant_resident_id=r1.id,
        )
        # Create linked Blotter Record
        blt = BlotterRecord(
            docket_no=f'BLT-{uid}',
            date_filed=date(2026, 8, 1),
            complainant='Alice ComplainantRes',
            complainant_id=r1.id,
            respondent='Bob RespondentRes',
            respondent_id=r2.id,
            nature='Theft',
            case_type='CRIM',
        )
        # Create Certificates linked to r1 & r2
        clr = BarangayClearance(resident_id=r1.id, ctrl_no=f'CLR-{uid}', full_name='Alice ComplainantRes', date_issued=date(2026, 8, 1))
        res_cert = BarangayResidency(resident_id=r1.id, ctrl_no=f'RES-C-{uid}', full_name='Alice ComplainantRes', date_issued=date(2026, 8, 1))
        non_res = BarangayNonResidency(resident_id=r2.id, ctrl_no=f'NON-C-{uid}', full_name='Bob RespondentRes', date_issued=date(2026, 8, 1))
        ind = IndigencyCertificate(resident_id=r1.id, ctrl_no=f'IND-C-{uid}', full_name='Alice ComplainantRes', date_issued=date(2026, 8, 1))

        # Create Notification
        notif = Notification(type='census', title='Test Census Notif', body='Test Body', ref_table='census', ref_id=r1.id)

        db.session.add_all([inc, blt, clr, res_cert, non_res, ind, notif])
        db.session.commit()

        inc_id = inc.id
        blt_id = blt.id
        clr_id = clr.id
        res_cert_id = res_cert.id
        non_res_id = non_res.id
        ind_id = ind.id
        notif_id = notif.id
        r1_id = r1.id
        r2_id = r2.id

        # Batch permanent delete r1 and r2
        res = self.client.post('/api/records.php?type=census&action=batch_permanent_delete&permanent=1', json={'ids': [r1_id, r2_id]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['count'], 2)

        # 1. Census records are removed
        self.assertIsNone(db.session.get(CensusRecord, r1_id))
        self.assertIsNone(db.session.get(CensusRecord, r2_id))

        # 2. Incident report remains, foreign keys set to NULL
        inc_fresh = db.session.get(Incident, inc_id)
        self.assertIsNotNone(inc_fresh)
        self.assertIsNone(inc_fresh.reporter_resident_id)
        self.assertIsNone(inc_fresh.complainant_resident_id)
        self.assertEqual(inc_fresh.reporter, 'Alice ComplainantRes')

        # 3. Blotter record remains, foreign keys set to NULL
        blt_fresh = db.session.get(BlotterRecord, blt_id)
        self.assertIsNotNone(blt_fresh)
        self.assertIsNone(blt_fresh.complainant_id)
        self.assertIsNone(blt_fresh.respondent_id)
        self.assertEqual(blt_fresh.complainant, 'Alice ComplainantRes')
        self.assertEqual(blt_fresh.respondent, 'Bob RespondentRes')

        # 4. Certificates are cascade deleted
        self.assertIsNone(db.session.get(BarangayClearance, clr_id))
        self.assertIsNone(db.session.get(BarangayResidency, res_cert_id))
        self.assertIsNone(db.session.get(BarangayNonResidency, non_res_id))
        self.assertIsNone(db.session.get(IndigencyCertificate, ind_id))

        # 5. Notification is deleted
        self.assertIsNone(db.session.get(Notification, notif_id))

        # 6. AuditLog is created
        audit = AuditLog.query.filter_by(action='BATCH_PERMANENT_DELETE', module='census').order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(audit)
        self.assertIn('Batch permanently deleted 2 records', audit.details)

    def test_single_permanent_delete(self):
        """Test single permanent delete via DELETE /api/documents.php?type=census&id=<id>&permanent=1."""
        self._login('test_admin_census', 'System Admin')
        uid = self._uid()

        r = CensusRecord(resident_no=f'RES-{uid}', last_name='SoloDelete', first_name='Mark', zone_id='Zone 1', status='Active', archived=True)
        db.session.add(r)
        db.session.commit()
        rid = r.id

        res = self.client.delete(f'/api/documents.php?type=census&id={rid}&permanent=1')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['ok'])
        self.assertTrue(res.get_json()['deleted'])

        self.assertIsNone(db.session.get(CensusRecord, rid))

        audit = AuditLog.query.filter_by(action='PERMANENT_DELETE', module='Census').order_by(AuditLog.id.desc()).first()
        self.assertIsNotNone(audit)
        self.assertIn(f'Resident record #{rid}', audit.details)

    def test_rbac_restrictions_on_permanent_delete(self):
        """Desk Officer (or non-admin) must be denied permission to permanently delete."""
        self._login('test_desk_census', 'Desk Officer')
        uid = self._uid()

        r = CensusRecord(resident_no=f'RES-{uid}', last_name='ProtectedRes', first_name='Jane', zone_id='Zone 1', status='Active', archived=True)
        db.session.add(r)
        db.session.commit()
        rid = r.id

        # Desk Officer tries single permanent delete
        res_single = self.client.delete(f'/api/documents.php?type=census&id={rid}&permanent=1')
        self.assertEqual(res_single.status_code, 403)

        # Desk Officer tries batch permanent delete
        res_batch = self.client.post('/api/records.php?type=census&action=batch_permanent_delete&permanent=1', json={'ids': [rid]})
        self.assertEqual(res_batch.status_code, 403)

        # Verify record was NOT deleted
        self.assertIsNotNone(db.session.get(CensusRecord, rid))


if __name__ == '__main__':
    unittest.main()
