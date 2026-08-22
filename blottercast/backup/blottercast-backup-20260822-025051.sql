-- BlotterCast database backup
-- Generated: 2026-08-22 02:50:51 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:44:36.956671');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:44:37.205201');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:44:37.267917');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-22 02:44:37.324978');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'admin', 'Created', 'Clearance', 'Clearance issued: BC-2026-001 for Cruz, Juan Santos', '2026-08-22 02:44:37.384773');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Logout', 'System', 'User logged out', '2026-08-22 02:44:37.407297');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:45.798555');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:46.074054');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:46.152940');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:47.500135');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:47.552260');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Logout', 'System', 'User logged out', '2026-08-22 02:50:47.563369');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:47.800028');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:47.866252');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Logout', 'System', 'User logged out', '2026-08-22 02:50:47.881981');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:48.098335');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:48.386979');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:48.631671');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (19, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:48.712117');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (20, 'admin', 'Logout', 'System', 'User logged out', '2026-08-22 02:50:48.720353');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (21, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:49.163036');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (22, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:49.233978');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (23, 'admin', 'Logout', 'System', 'User logged out', '2026-08-22 02:50:49.251471');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (24, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-22 02:50:50.665398');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (25, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-22 02:50:50.734556');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (26, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-22 02:50:50.775415');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (27, 'admin', 'Created', 'Users', 'New account created: testuser1 (Desk Officer)', '2026-08-22 02:50:51.368200');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (28, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-22 02:50:51.398841');

-- Table: backups

-- Table: barangay_clearance
INSERT INTO "barangay_clearance" ("id", "resident_id", "ctrl_no", "full_name", "age", "civil_status", "address", "voter_status", "purpose", "or_no", "fee", "date_issued", "issued_by", "created_at") VALUES (1, 1, 'BC-2026-001', 'Cruz, Juan Santos', 36, 'Single', '123 Rizal St', 'Registered Voter', 'Employment', 'OR-2026-001', 20, '2026-08-22', 'System Administrator', '2026-08-22 02:44:37.374883');

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (1, 'BLT-2026-001', '2026-08-22', 'Juan Cruz', 1, '', 'Pedro Reyes', NULL, 'outside barangay', 'Noise complaint', 'CIVIL', 'Pending', 'Zone 1', 0, '2026-08-22 02:44:37.350375', '2026-08-22 02:44:37.350378');
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (2, 'BLT-2026-002', '2026-08-22', 'Juan Cruz', 2, '', 'Pedro Reyes', NULL, '', 'Noise complaint', 'CIVIL', 'Pending', NULL, 0, '2026-08-22 02:50:50.875956', '2026-08-22 02:50:50.875960');

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Cruz', 'Juan', 'Santos', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '0917-123-4567', 'Registered Voter', 'Farmer', 'Active', '2026-08-22 02:44:37.303810', '2026-08-22 02:44:37.303815');
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (2, 'RES-0002', 'Cruz', 'Juan', '', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '', 'Not Registered', '', 'Active', '2026-08-22 02:50:50.761552', '2026-08-22 02:50:50.761559');

-- Table: generated_reports
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (1, 'Incident Summary Report', 'System Administrator', '2026-01-01', '2026-12-31', 'PDF', 'incident-summary-report-20260822-105050.pdf', '2026-08-22 02:50:50.969191');
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (2, 'Settlement Compliance Report', 'System Administrator', '2026-08-01', '2026-08-22', 'Excel', 'settlement-compliance-report-20260822-105050.csv', '2026-08-22 02:50:51.001570');

-- Table: incidents
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (1, 'INC-2026-0001', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 0', 14.883096, 120.965595, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-22 02:50:50.807151', '2026-08-22 02:50:50.807156');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (2, 'INC-2026-0002', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 1', 14.883574, 120.96602, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-22 02:50:50.825301', '2026-08-22 02:50:50.825306');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (3, 'INC-2026-0003', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 2', 14.884091, 120.965496, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-22 02:50:50.842034', '2026-08-22 02:50:50.842039');

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, 'ce56c0ac42e7d9a540d3d214f4eb3c21325afb6936780b2771b5ba96d0a2a26b', 'login', '2026-08-22 02:49:36.930877', 0, '2026-08-22 02:44:37.170613', '2026-08-22 02:44:36.932064');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 1, '24611aee8ecffdea2b0fe1bb3770a1adc8a4b945002c74ac35a525306507f150', 'login', '2026-08-22 02:49:37.191065', 0, '2026-08-22 02:44:37.249180', '2026-08-22 02:44:37.191360');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, '96d898e885be6de6f38cde8b4a2333d803fd17ae04db2fee8997e453f7bed1fd', 'login', '2026-08-22 02:55:45.777738', 0, '2026-08-22 02:50:46.045067', '2026-08-22 02:50:45.779582');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, 'ee954bc879f2eb982803285597034a652042abb9efb98dd97e94cde67c9e6e93', 'login', '2026-08-22 02:55:46.062906', 0, '2026-08-22 02:50:46.122104', '2026-08-22 02:50:46.063305');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '98defba68a826ea17af8b20ae0818875da7742f62eca402a317b86e174ca4455', 'login', '2026-08-22 02:55:47.485494', 0, '2026-08-22 02:50:47.535505', '2026-08-22 02:50:47.486255');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (6, 1, '100b9ae41a83e882e81810d12ab053717caf02f3cc1934f2626720337a4ee2fd', 'login', '2026-08-22 02:55:47.789747', 1, '2026-08-22 02:50:47.846264', '2026-08-22 02:50:47.789905');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (7, 1, '779a5684487e6b3b5ad0738a20685c6b402a77d430d6b6f032a3eccbc68595b3', 'login', '2026-08-22 02:55:48.088029', 5, '2026-08-22 02:50:48.373101', '2026-08-22 02:50:48.088257');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (8, 1, '1c53ffd0c8c5e22a825ff23b6670c8172f0b45a1ac898ed6f3f83155378e8cd5', 'login', '2026-08-22 02:50:47.400281', 0, '2026-08-22 02:50:48.623824', '2026-08-22 02:50:48.376541');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (9, 1, '18a58a0534e4ae412b5ec0c598ce33622119f0765d0267901d36e4f3efc80bff', 'login', '2026-08-22 02:55:48.624851', 0, '2026-08-22 02:50:48.655610', '2026-08-22 02:50:17.641892');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (10, 1, 'ce979eb05459554f9a9854904e4c85971e04605097fe1ca76d4fc1d27817e27e', 'login', '2026-08-22 02:55:48.657464', 0, '2026-08-22 02:50:48.691995', '2026-08-22 02:50:48.657656');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (11, 1, '5bd45fbd1b183d23ab79c7f545d1349fa00229563f5039e1b2acb3be76b03b0c', 'login', '2026-08-22 02:55:49.148303', 0, '2026-08-22 02:50:49.190170', '2026-08-22 02:50:49.148459');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (12, 1, 'ac3dadc605ad73298b5925594e4a32e2c99631f60707c10a99205b1c3c5afac0', 'login', '2026-08-22 02:55:50.619247', 0, '2026-08-22 02:50:50.710571', '2026-08-22 02:50:50.621639');

-- Table: settlements
INSERT INTO "settlements" ("id", "blotter_id", "case_no", "case_title", "complaint_title", "nature", "date_filed", "date_confrontation", "action_taken", "date_settlement", "date_execution", "main_point", "status", "remarks", "created_at", "updated_at") VALUES (1, 2, 'STL-2026-001', 'Juan Cruz vs. Pedro Reyes', 'Noise complaint', 'Civil', '2026-08-22', NULL, '', NULL, NULL, '', 'Pending', '', '2026-08-22 02:50:50.912961', '2026-08-22 02:50:50.912969');

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Test Updated', '2026-08-22 02:50:51.385709');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-22 02:44:28.373423');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-22 02:44:28.373833');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-22 02:44:28.374177');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-22 02:44:28.374461');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-22 02:44:28.374899');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-22 02:44:28.375397');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-22 02:44:28.375916');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-22 02:44:28.376590');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-22 02:44:28.377513');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-22 02:44:28.378489');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-22 02:44:28.379085');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-22 02:44:28.379577');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-22 02:44:28.380061');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-22 02:44:28.380514');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-22 02:44:28.380965');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-22 02:44:28.381481');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-22 02:44:28.382042');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-22 02:44:28.382539');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-22 02:44:28.382956');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-22 02:44:28.383416');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-22 02:44:28.384116');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (1, 'admin', '$2b$12$ijfRE7.7zQt27r0iBl99neWTr6N10Qs1Gcfq4Wnd5yzcY98cbUjki', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-22 02:50:50.722298', 0, NULL, '2026-08-22 02:44:28.574929', '2026-08-22 02:44:28.574932', NULL, NULL);
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (2, 'kapitan', '$2b$12$J4/A8ttbUC6ycAUmpTVXceuJfR5WTAPsK9uk2.meGtxABBZIelufi', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-22 02:44:28.801113', '2026-08-22 02:44:28.801118', NULL, NULL);
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (3, 'jdelacuz', '$2b$12$ndXk.XbK4t.CaeQ2yAfFkuezww/kf050.5xRG2fbNZNWL2Fr.X0C.', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-22 02:44:28.994240', '2026-08-22 02:44:28.994244', NULL, NULL);
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (4, 'msantos', '$2b$12$UjZsZlLzE2XiigtgWsZ/j.Q0QGW59X7MKhRO9tRhfSZckxuGpu/lO', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-22 02:44:29.186526', '2026-08-22 02:44:29.186529', NULL, NULL);
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (5, 'pencoder', '$2b$12$HCKPq6xW09SkJorhmd7cIOKvb./YHt5UKAE3ZetHDG3nHgJpAAGP.', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-22 02:44:29.379958', '2026-08-22 02:44:29.379962', NULL, NULL);
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at", "google_id", "google_email") VALUES (6, 'testuser1', '$2b$12$6WfILyIeZvQJlyoeJw6B7ukglxNtxD1G4Op1AzxLBVhka3WVC9ATC', 'Test User', 'testuser1@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-22 02:50:51.360331', '2026-08-22 02:50:51.361408', NULL, NULL);

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – Mapulang Lupa Elementary School Area', 14.88, 120.9634, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Sitio Bata', 14.8863, 120.9679, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Pandi Village 2', 14.8782, 120.967, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Silangan Corridor (Pandi–Angat Road)', 14.8884, 120.964, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – Pandi Residences 1', 14.8818, 120.9598, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Pandi Encampment One', 14.8854, 120.9613, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – Pandi Residences 3', 14.8806, 120.97, 0.14);
