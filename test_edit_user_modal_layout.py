import re
import unittest

class TestEditUserModalLayout(unittest.TestCase):
    def test_edit_user_modal_layout(self):
        with open("frontend/users.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Find edit_wiz_view_step_1 container
        step1_match = re.search(r'<div id="edit_wiz_view_step_1"[^>]*>(.*?)</div>\s*<!-- STEP 2: Roles -->', html, re.DOTALL)
        self.assertIsNotNone(step1_match, "Could not find #edit_wiz_view_step_1 in users.html")
        step1_html = step1_match.group(1)

        # Check section header in Edit User modal has (Read-Only)
        self.assertIn('Personal Information', step1_html)
        self.assertIn('(Read-Only)', step1_html)
        self.assertTrue(re.search(r'<span[^>]*class="[^"]*text-\[#52796f\][^"]*"[^>]*>\(Read-Only\)</span>', step1_html))

        # Check the grid container
        grid_match = re.search(r'<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">(.*?)</div>\s*<div class="flex items-center justify-end', step1_html, re.DOTALL)
        self.assertIsNotNone(grid_match, "Could not find grid container in #edit_wiz_view_step_1")
        grid_html = grid_match.group(1)

        # Check order of fields:
        # 1. Full Name
        # 2. Username
        # 3. Email
        # 4. Contact No.
        pos_fullname = grid_html.find('id="uf_name"')
        pos_username = grid_html.find('id="uf_username"')
        pos_email = grid_html.find('id="uf_email"')
        pos_contact = grid_html.find('id="uf_contact"')

        self.assertNotEqual(pos_fullname, -1, "uf_name not found in step 1 grid")
        self.assertNotEqual(pos_username, -1, "uf_username not found in step 1 grid")
        self.assertNotEqual(pos_email, -1, "uf_email not found in step 1 grid")
        self.assertNotEqual(pos_contact, -1, "uf_contact not found in step 1 grid")

        self.assertLess(pos_fullname, pos_username, f"Full Name ({pos_fullname}) should be before Username ({pos_username})")
        self.assertLess(pos_username, pos_email, f"Username ({pos_username}) should be before Email ({pos_email})")
        self.assertLess(pos_email, pos_contact, f"Email ({pos_email}) should be before Contact No. ({pos_contact})")

        # Split into the 4 position containers
        # Position 1: Full Name container
        p1_idx = grid_html.find('Position 1')
        p2_idx = grid_html.find('Position 2')
        p3_idx = grid_html.find('Position 3')
        p4_idx = grid_html.find('Position 4')

        self.assertTrue(p1_idx < p2_idx < p3_idx < p4_idx, "Containers must be in order: Position 1 -> Position 2 -> Position 3 -> Position 4")

        c1 = grid_html[p1_idx:p2_idx]
        c2 = grid_html[p2_idx:p3_idx]
        c3 = grid_html[p3_idx:p4_idx]
        c4 = grid_html[p4_idx:]

        # Position 1 (Top Left): Full Name with user icon
        self.assertIn('Full Name', c1)
        self.assertIn('data-icon="user"', c1)
        self.assertIn('id="uf_name"', c1)
        self.assertIn('name="full_name"', c1)
        self.assertIn('readonly', c1)

        # Position 2 (Top Right): Username with idCard icon
        self.assertIn('Username', c2)
        self.assertIn('data-icon="idCard"', c2)
        self.assertIn('id="uf_username"', c2)
        self.assertIn('name="username"', c2)
        self.assertIn('readonly', c2)

        # Position 3 (Bottom Left): Email with mail icon
        self.assertIn('Email', c3)
        self.assertIn('data-icon="mail"', c3)
        self.assertIn('id="uf_email"', c3)
        self.assertIn('name="email"', c3)
        self.assertIn('readonly', c3)

        # Position 4 (Bottom Right): Contact No. with phone icon and +63 prefix
        self.assertIn('Contact No.', c4)
        self.assertIn('data-icon="phone"', c4)
        self.assertIn('+63', c4)
        self.assertIn('id="uf_contact"', c4)
        self.assertIn('name="contact_no"', c4)
        self.assertIn('readonly', c4)

        # Check classes for readonly indicator: cursor-not-allowed, select-none, bg-[#edf5f0]/80, opacity-90
        for input_id in ['uf_name', 'uf_username', 'uf_email']:
            input_tag = re.search(rf'<input[^>]*id="{input_id}"[^>]*>', grid_html).group(0)
            self.assertIn('cursor-not-allowed', input_tag, f"{input_id} missing cursor-not-allowed")
            self.assertIn('select-none', input_tag, f"{input_id} missing select-none")
            self.assertIn('opacity-90', input_tag, f"{input_id} missing opacity-90")
            self.assertIn('bg-[#edf5f0]/80', input_tag, f"{input_id} missing bg-[#edf5f0]/80")
            self.assertIn('focus:ring-0', input_tag, f"{input_id} missing focus:ring-0")
            self.assertIn('focus:outline-none', input_tag, f"{input_id} missing focus:outline-none")

        # For contact, both wrapper and input reflect read-only styles
        contact_input_tag = re.search(r'<input[^>]*id="uf_contact"[^>]*>', grid_html).group(0)
        self.assertIn('cursor-not-allowed', contact_input_tag, "uf_contact missing cursor-not-allowed" )
        self.assertIn('select-none', contact_input_tag, "uf_contact missing select-none")

        # Ensure no character counter spans exist in step 1 of Edit User
        self.assertNotIn('Count', step1_html, "Dynamic character counter spans should not exist in Edit User step 1")
        self.assertFalse(re.search(r'>\s*\d+/\d+\s*<', step1_html), "Character counter display (e.g. >0/50<) should not exist in Edit User step 1")

        # Ensure buttons are right-aligned
        self.assertIn('justify-end', step1_html, "Buttons in step 1 should be right-aligned")
        self.assertIn('Cancel', step1_html, "Cancel button should exist in step 1")
        self.assertIn('Next', step1_html, "Next button should exist in step 1")

    def test_add_user_modal_remains_editable(self):
        with open("frontend/users.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Find addUserWizardModal
        add_modal_match = re.search(r'<div class="modal-overlay" id="addUserWizardModal">(.*?)</div>\s*<!-- Edit User Modal', html, re.DOTALL)
        self.assertIsNotNone(add_modal_match, "Could not find #addUserWizardModal in users.html")
        add_modal_html = add_modal_match.group(1)

        # Ensure Add User section header does NOT say (Read-Only)
        self.assertNotIn('(Read-Only)', add_modal_html)

        # Ensure wiz_name, wiz_username, wiz_email, wiz_contact are NOT readonly or disabled
        for input_id in ['wiz_name', 'wiz_username', 'wiz_email', 'wiz_contact']:
            input_tag = re.search(rf'<input[^>]*id="{input_id}"[^>]*>', add_modal_html).group(0)
            self.assertNotIn('readonly', input_tag.lower(), f"{input_id} in Add User should NOT be readonly")
            self.assertNotIn('disabled', input_tag.lower(), f"{input_id} in Add User should NOT be disabled")

        # Ensure character counters still exist in Add User modal
        self.assertIn('userFullNameCount', add_modal_html)
        self.assertIn('userUsernameCount', add_modal_html)
        self.assertIn('userEmailCount', add_modal_html)

    def test_edit_user_js_logic(self):
        with open("frontend/users.html", "r", encoding="utf-8") as f:
            html = f.read()

        # In editUser(id), check that readOnly is set on all 4 fields
        edit_user_match = re.search(r'function editUser\(id\)\s*{(.*?)\n}', html, re.DOTALL)
        self.assertIsNotNone(edit_user_match, "Could not find editUser function")
        edit_user_code = edit_user_match.group(1)

        self.assertIn('nameEl.readOnly = true', edit_user_code)
        self.assertIn('usernameEl.readOnly = true', edit_user_code)
        self.assertIn('emailEl.readOnly = true', edit_user_code)
        self.assertIn('contactEl.readOnly = true', edit_user_code)

        # In saveUser(), check that values are extracted
        save_user_match = re.search(r'async function saveUser\(\)\s*{(.*?)\n}', html, re.DOTALL)
        self.assertIsNotNone(save_user_match, "Could not find saveUser function")
        save_user_code = save_user_match.group(1)

        self.assertIn('uf_name', save_user_code)
        self.assertIn('uf_username', save_user_code)
        self.assertIn('uf_email', save_user_code)
        self.assertIn('getEditNormalizedContact()', save_user_code)

        # In getEditNormalizedContact(), check that uf_contact is read
        contact_norm_match = re.search(r'function getEditNormalizedContact\(\)\s*{(.*?)\n}', html, re.DOTALL)
        self.assertIsNotNone(contact_norm_match, "Could not find getEditNormalizedContact function")
        self.assertIn('uf_contact', contact_norm_match.group(1))

    def test_table_action_button_view_and_edit(self):
        with open("frontend/users.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Find renderUsers function
        render_users_match = re.search(r'function renderUsers\(\)\s*{(.*?)\n}', html, re.DOTALL)
        self.assertIsNotNone(render_users_match, "Could not find renderUsers function")
        code = render_users_match.group(1)

        # Check that the button has View & Edit, editUser(${u.id}), data-icon="edit"
        self.assertIn('View & Edit', code)
        self.assertIn('editUser(${u.id})', code)
        self.assertIn('data-icon="edit"', code)
        self.assertIn('btn-edit', code)

        # Check that openEditUserModal alias exists
        self.assertIn('window.openEditUserModal = editUser;', html)

if __name__ == "__main__":
    unittest.main()
