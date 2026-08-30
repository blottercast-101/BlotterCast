import unittest
from datetime import date, datetime
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import BlotterRecord, Settlement, User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class TestSettlementValidation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(username="admin", role="System Admin", full_name="Admin User")
            user.set_password("AdminPass123!")
            db.session.add(user)
            db.session.commit()
        self.user_id = user.id

        # Seed a test BlotterRecord
        self.blotter = BlotterRecord(
            docket_no="BLOT-2026-0001",
            date_filed=date(2026, 8, 20),
            complainant="Juan Dela Cruz",
            respondent="Pedro Penduko",
            nature="Physical Assault",
            case_type="CRIM",
            status="Ongoing"
        )
        db.session.add(self.blotter)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["username"] = "admin"
            sess["role"] = "System Admin"
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_create_and_update_settlement_with_officer_and_status(self):
        self._login()

        # 1. Create settlement with officer and status
        res = self.client.post("/api/records.php?type=settlements", json={
            "blotterId": self.blotter.id,
            "actionTaken": "Mediation (M)",
            "dateConfrontation": "2026-08-22",
            "dateSettlement": "2026-08-25",
            "officer": "Punong Barangay Jose Reyes",
            "mainPoint": "Parties agreed on restitution and mutual respect.",
            "status": "Complied",
            "remarks": "Case closed amicably."
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        stl_id = data["id"]

        # Verify created record in DB
        stl = Settlement.query.get(stl_id)
        self.assertIsNotNone(stl)
        self.assertEqual(stl.officer, "Punong Barangay Jose Reyes")
        self.assertEqual(stl.status, "Complied")
        self.assertEqual(stl.main_point, "Parties agreed on restitution and mutual respect.")

        # Verify dictionary output contains officer
        stl_dict = stl.to_dict()
        self.assertEqual(stl_dict["officer"], "Punong Barangay Jose Reyes")
        self.assertEqual(stl_dict["status"], "Complied")

        # 2. Update settlement
        res_update = self.client.put(f"/api/records.php?type=settlements&id={stl.id}", json={
            "actionTaken": "Conciliation (C)",
            "dateSettlement": "2026-08-26",
            "officer": "Lupon Chairman Santos",
            "mainPoint": "Updated terms agreed upon.",
            "status": "Not Complied",
            "remarks": "Follow-up required."
        })
        self.assertEqual(res_update.status_code, 200)

        stl_refreshed = Settlement.query.get(stl.id)
        self.assertEqual(stl_refreshed.officer, "Lupon Chairman Santos")
        self.assertEqual(stl_refreshed.status, "Not Complied")

        # 3. Update via status endpoint
        res_status = self.client.patch(f"/api/settlements/{stl.id}/status", json={
            "status": "Complied",
            "officer": "Punong Barangay Jose Reyes",
            "mainPoint": "Full compliance reached."
        })
        self.assertEqual(res_status.status_code, 200)
        stl_final = Settlement.query.get(stl.id)
        self.assertEqual(stl_final.status, "Complied")
        self.assertEqual(stl_final.officer, "Punong Barangay Jose Reyes")


if __name__ == "__main__":
    unittest.main()
