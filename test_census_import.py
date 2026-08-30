import json
import unittest
from datetime import date

from app import create_app
from app.extensions import db
from app.models import CensusRecord, User


class TestCensusImportAddressResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "System Admin"

        # Clean any test residents
        CensusRecord.query.filter(CensusRecord.last_name.in_(["Aguinaldo", "Bonifacio", "Rizal", "Mabini", "Silang"])).delete(synchronize_session=False)
        db.session.commit()

    def tearDown(self):
        self.ctx.pop()

    def test_census_create_with_various_address_keys(self):
        """Verify that address is reliably extracted from varied incoming keys."""
        test_payloads = [
            {
                "lastName": "Aguinaldo",
                "firstName": "Emilio",
                "street_address": "Pasong Kalabaw St., Phase 1",
                "dob": "1990-05-15",
                "sex": "Male",
                "zone": "Zone 2",
            },
            {
                "lastName": "Bonifacio",
                "firstName": "Andres",
                "location": "Sitio Gubat Near Chapel",
                "dob": "1988-11-30",
                "sex": "Male",
            },
            {
                "lastName": "Rizal",
                "firstName": "Jose",
                "complete_address": "Atlantica Subdivision Blk 5 Lot 12",
                "dob": "1992-06-19",
                "sex": "Male",
            },
            {
                "fullName": "Mabini, Apolinario",
                "tirahan": "Calle Bangko, Purok 6",
                "dob": "1985-07-23",
                "sex": "Male",
            },
            {
                "lastName": "Silang",
                "firstName": "Gabriela",
                "zone": "Zone 7",
                "dob": "1995-03-19",
                "sex": "Female",
            },
        ]

        for payload in test_payloads:
            res = self.client.post(
                "/api/documents.php?type=census",
                data=json.dumps(payload),
                content_type="application/json",
                headers={"X-Bulk-Import": "1"}
            )
            self.assertEqual(res.status_code, 201, f"Failed to insert resident: {res.get_json()}")
            res_id = res.get_json()["id"]

            record = CensusRecord.query.get(res_id)
            self.assertIsNotNone(record)
            self.assertTrue(len(record.address or "") > 0, f"Address was left blank for {record.first_name} {record.last_name}")
            self.assertTrue(record.zone_id in [f"Zone {i}" for i in range(1, 8)], f"Zone was not properly resolved for {record.first_name}: {record.zone_id}")

        # Check specific resolved addresses & zones
        bonifacio = CensusRecord.query.filter_by(first_name="Andres", last_name="Bonifacio").first()
        self.assertEqual(bonifacio.zone_id, "Zone 5")
        self.assertEqual(bonifacio.address, "Sitio Gubat Near Chapel")

        rizal = CensusRecord.query.filter_by(first_name="Jose", last_name="Rizal").first()
        self.assertEqual(rizal.zone_id, "Zone 3")
        self.assertEqual(rizal.address, "Atlantica Subdivision Blk 5 Lot 12")

        mabini = CensusRecord.query.filter_by(first_name="Apolinario", last_name="Mabini").first()
        self.assertEqual(mabini.zone_id, "Zone 6")
        self.assertEqual(mabini.address, "Calle Bangko, Purok 6")


if __name__ == "__main__":
    unittest.main()
