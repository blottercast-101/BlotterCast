"""
Test suite for Barangay Captain and System Administrator user management business logic,
lifecycle permissions, and Add/Edit role options.
"""
import os
import unittest
from app import create_app
from app.extensions import db
from app.models import User, SystemSetting


class TestUserRolesCaptainAndAdminLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Ensure System Admin exists
        self.admin = User.query.filter_by(role="System Admin").first()
        if not self.admin:
            self.admin = User(
                username="test_admin",
                password="AdminPassword123!",
                full_name="System Admin Test",
                email="admin_test@test.gov",
                role="System Admin",
                status="Active"
            )
            db.session.add(self.admin)
            db.session.commit()

        # Ensure Barangay Captain exists
        self.captain = User.query.filter_by(role="Barangay Captain").first()
        if not self.captain:
            self.captain = User(
                username="test_captain",
                password="CaptainPassword123!",
                full_name="Kapitan Test",
                email="captain_test@test.gov",
                role="Barangay Captain",
                status="Active"
            )
            db.session.add(self.captain)
            db.session.commit()

        # Ensure regular Desk Officer exists for edit tests
        self.officer = User.query.filter_by(username="test_officer_sample").first()
        if not self.officer:
            self.officer = User(
                username="test_officer_sample",
                password="OfficerPassword123!",
                full_name="Desk Officer Sample",
                email="officer_sample@test.gov",
                role="Desk Officer",
                status="Inactive"
            )
            db.session.add(self.officer)
            db.session.commit()

        self._login_as_admin()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    def _login_as_admin(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["username"] = self.admin.username
            sess["role"] = self.admin.role
            sess["full_name"] = self.admin.full_name

    def test_01_single_active_captain_blocked_when_one_exists(self):
        """Bawal mag-add ng bagong Barangay Captain account hangga't may umiiral at aktibong Barangay Captain."""
        res = self.client.post("/api/users.php?action=create", json={
            "name": "Second Captain",
            "username": "second_captain",
            "email": "second_capt@test.gov",
            "role": "Barangay Captain",
            "contact": "09171112233"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("ok", True))
        expected_msg = "Only one active Barangay Captain is allowed. Please delete the current Barangay Captain account first."
        self.assertIn(expected_msg, data.get("error", ""))

    def test_02_no_suspend_rule_for_barangay_captain(self):
        """Panatilihin o i-enforce ang restriction na hindi ito puwedeng i-suspend."""
        # Test toggle_status endpoint
        res = self.client.post(f"/api/users.php?action=toggle_status&id={self.captain.id}")
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("cannot be suspended", data.get("error", ""))

        # Test update endpoint attempting to suspend
        res_up = self.client.put(f"/api/users.php?action=update&id={self.captain.id}", json={
            "name": self.captain.full_name,
            "email": self.captain.email,
            "status": "Suspended"
        })
        self.assertEqual(res_up.status_code, 400)
        data_up = res_up.get_json()
        self.assertIn("cannot be suspended", data_up.get("error", ""))

    def test_03_delete_barangay_captain_and_recreate_new_one(self):
        """Hindi na ito protected role: puwede na itong i-delete, at pagka-delete ay puwede nang mag-add ng bago."""
        capt_id = self.captain.id

        # 1. Delete the existing Barangay Captain
        res_del = self.client.delete(f"/api/users.php?action=delete&id={capt_id}")
        self.assertEqual(res_del.status_code, 200)
        data_del = res_del.get_json()
        self.assertTrue(data_del.get("ok"))

        # Verify captain is deleted from database
        check_capt = db.session.get(User, capt_id)
        self.assertIsNone(check_capt)

        # 2. Now add a new Barangay Captain
        res_create = self.client.post("/api/users.php?action=create", json={
            "name": "Kapitan Bagong Halal",
            "username": "kapitan_bago",
            "email": "kapitan_bago@test.gov",
            "role": "Barangay Captain",
            "contact": "09189998877"
        })
        self.assertEqual(res_create.status_code, 201)
        data_create = res_create.get_json()
        self.assertTrue(data_create.get("ok"))
        new_id = data_create["id"]

        new_capt = db.session.get(User, new_id)
        self.assertIsNotNone(new_capt)
        self.assertEqual(new_capt.role, "Barangay Captain")
        self.assertEqual(new_capt.full_name, "Kapitan Bagong Halal")

        # Verify settings synchronization
        setting_row = SystemSetting.query.get("barangay_captain")
        self.assertEqual(setting_row.setting_value, "Kapitan Bagong Halal")

    def test_04_system_administrator_cannot_be_assigned_in_edit(self):
        """Sa Edit User, bawal ilipat o i-assign ang System Administrator role."""
        res = self.client.put(f"/api/users.php?action=update&id={self.officer.id}", json={
            "name": self.officer.full_name,
            "email": self.officer.email,
            "role": "System Admin"
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("Assigning System Administrator role is not allowed", data.get("error", ""))

        res_full = self.client.put(f"/api/users.php?action=update&id={self.officer.id}", json={
            "name": self.officer.full_name,
            "email": self.officer.email,
            "role": "System Administrator"
        })
        self.assertEqual(res_full.status_code, 400)

    def test_05_system_administrator_cannot_be_created_via_add_user(self):
        """System Admin cannot be created via user management endpoint."""
        res = self.client.post("/api/users.php?action=create", json={
            "name": "Hacked Admin",
            "username": "hacked_admin",
            "email": "hacked@test.gov",
            "role": "System Admin"
        })
        self.assertEqual(res.status_code, 403)

    def test_06_system_administrator_cannot_be_suspended_or_deleted(self):
        """System Administrator remains protected against delete and suspend."""
        # Create or fetch a second admin to test non-self-delete
        other_admin = User.query.filter_by(username="other_admin_test").first()
        if not other_admin:
            other_admin = User(
                username="other_admin_test",
                password="OtherPassword123!",
                full_name="Other Admin Test",
                email="other_admin@test.gov",
                role="System Admin",
                status="Active"
            )
            db.session.add(other_admin)
            db.session.commit()

        # Suspend attempt on other admin
        res_tog = self.client.post(f"/api/users.php?action=toggle_status&id={other_admin.id}")
        self.assertEqual(res_tog.status_code, 400)
        self.assertIn("protected and cannot be suspended", res_tog.get_json().get("error", ""))

        # Delete attempt on other admin
        res_del = self.client.delete(f"/api/users.php?action=delete&id={other_admin.id}")
        self.assertEqual(res_del.status_code, 400)
        self.assertIn("protected and cannot be deleted", res_del.get_json().get("error", ""))

    def test_07_frontend_markup_verification(self):
        """Verify frontend/users.html has correct cards, hidden admin, and row action logic."""
        users_html_path = os.path.join(self.app.static_folder, "users.html")
        with open(users_html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Add User wizard role selector includes Barangay Captain
        self.assertIn('name="wiz_role_radio" value="Barangay Captain"', content)

        # 2. Edit User modal role options hide System Administrator
        self.assertIn('id="editRoleCardAdmin" class="hidden', content)

        # 3. Single active captain validation message present in scripts
        self.assertIn("Only one active Barangay Captain is allowed. Please delete the current Barangay Captain account first.", content)

        # 4. Table actions: Barangay Captain has delete button and no suspend toggle button
        self.assertIn("u.role === 'Barangay Captain'", content)
        self.assertIn("Barangay Captain accounts cannot be suspended.", content)

        # 5. Barangay Captain row action buttons: View & Edit and Delete
        self.assertIn("openEditUserModal('${u.id}')", content)
        self.assertIn("confirmDeleteUser('${u.id}', '${u.role}')", content)
        self.assertIn('data-i18n="view_edit"', content)
        self.assertIn('data-i18n="delete"', content)
        self.assertIn('d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"', content)
        self.assertIn('d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"', content)
        self.assertIn("window.renderUserTable = renderUsers;", content)
        self.assertIn("window.confirmDeleteUser = confirmDeleteUser;", content)


if __name__ == "__main__":
    unittest.main()
