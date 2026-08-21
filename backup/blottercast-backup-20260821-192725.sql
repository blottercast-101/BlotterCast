-- BlotterCast database backup
-- Generated: 2026-08-21 19:27:25 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'active_oauth_user', 'Login', 'System', 'Successful login via Google OAuth', '2026-08-21 19:27:03.039154');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'inactive_oauth_user', 'Login Failed', 'System', 'Google login rejected: account is Inactive', '2026-08-21 19:27:03.048862');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'system', 'Login Failed', 'System', 'Google login rejected: unregistered email random.unregistered.person@gmail.com', '2026-08-21 19:27:03.055542');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:08.780621');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:08.982622');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:09.020560');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-21 19:27:09.045331');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Created', 'Clearance', 'Clearance issued: BC-2026-001 for Cruz, Juan Santos', '2026-08-21 19:27:09.086893');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Logout', 'System', 'User logged out', '2026-08-21 19:27:09.098782');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:21.550727');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:21.588432');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Logout', 'System', 'User logged out', '2026-08-21 19:27:21.595826');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:21.799245');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:21.836724');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Logout', 'System', 'User logged out', '2026-08-21 19:27:21.844005');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:22.033654');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:22.310784');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:22.594153');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (19, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:22.655553');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (20, 'admin', 'Logout', 'System', 'User logged out', '2026-08-21 19:27:22.662048');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (21, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:23.147129');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (22, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:23.180848');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (23, 'admin', 'Logout', 'System', 'User logged out', '2026-08-21 19:27:23.187480');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (24, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-21 19:27:24.701783');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (25, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-21 19:27:24.732426');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (26, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-21 19:27:24.752622');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (27, 'admin', 'Created', 'Users', 'New account created: testuser1 (Desk Officer)', '2026-08-21 19:27:25.512471');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (28, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-21 19:27:25.531578');

-- Table: backups

-- Table: barangay_clearance
INSERT INTO "barangay_clearance" ("id", "resident_id", "ctrl_no", "full_name", "age", "civil_status", "address", "voter_status", "purpose", "or_no", "fee", "date_issued", "issued_by", "created_at") VALUES (1, 1, 'BC-2026-001', 'Cruz, Juan Santos', 36, 'Single', '123 Rizal St', 'Registered Voter', 'Employment', 'OR-2026-001', 20, '2026-08-21', 'System Administrator', '2026-08-21 19:27:09.080258');

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (1, 'BLT-2026-001', '2026-08-21', 'Juan Cruz', 1, '', 'Pedro Reyes', NULL, 'outside barangay', 'Noise complaint', 'CIVIL', 'Pending', 'Zone 1', 0, '2026-08-21 19:27:09.060508', '2026-08-21 19:27:09.060510');
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (2, 'BLT-2026-002', '2026-08-21', 'Juan Cruz', 2, '', 'Pedro Reyes', NULL, '', 'Noise complaint', 'CIVIL', 'Pending', NULL, 0, '2026-08-21 19:27:24.800410', '2026-08-21 19:27:24.800415');

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Cruz', 'Juan', 'Santos', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '0917-123-4567', 'Registered Voter', 'Farmer', 'Active', '2026-08-21 19:27:09.036792', '2026-08-21 19:27:09.036797');
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (2, 'RES-0002', 'Cruz', 'Juan', '', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '', 'Not Registered', '', 'Active', '2026-08-21 19:27:24.748563', '2026-08-21 19:27:24.748568');

-- Table: generated_reports
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (1, 'Incident Summary Report', 'System Administrator', '2026-01-01', '2026-12-31', 'PDF', 'incident-summary-report-20260822-032724.pdf', '2026-08-21 19:27:24.871690');
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (2, 'Settlement Compliance Report', 'System Administrator', '2026-08-01', '2026-08-21', 'Excel', 'settlement-compliance-report-20260822-032724.csv', '2026-08-21 19:27:24.901297');

-- Table: incidents
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (1, 'INC-2026-0001', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 0', 14.883836, 120.965325, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-21 19:27:24.765375', '2026-08-21 19:27:24.765379');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (2, 'INC-2026-0002', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 1', 14.883848, 120.965217, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-21 19:27:24.777775', '2026-08-21 19:27:24.777777');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (3, 'INC-2026-0003', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 2', 14.884051, 120.96579, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-21 19:27:24.785925', '2026-08-21 19:27:24.785928');

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '40d7b241a689ce3ce054d29736f8544ced21e669c8d3ebc85494de74c097cb68', 'login', '2026-08-21 19:32:08.772407', 0, '2026-08-21 19:27:08.969209', '2026-08-21 19:27:08.773871');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 1, 'ab6018c2eed1d6f2ef209cb62d0fa83cd0a88578e66edbf9c73a8dc3de88bcdf', 'login', '2026-08-21 19:32:08.972318', 0, '2026-08-21 19:27:09.011325', '2026-08-21 19:27:08.972562');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, '2917cb8e03675fd1fa5c2c0c2183471b42d314e87c83ea48f21c585808d03da9', 'login', '2026-08-21 19:32:21.526923', 0, '2026-08-21 19:27:21.577444', '2026-08-21 19:27:21.527717');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, '5673647d338408973cc8f79829feca2f2295fd419cdcf820e9ba1dd4b3a23519', 'login', '2026-08-21 19:32:21.793929', 1, '2026-08-21 19:27:21.827750', '2026-08-21 19:27:21.794157');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '6860d57e6a36510bd98dcf3229487dd79fd9ef040b1642398be5ceeb574c91ca', 'login', '2026-08-21 19:32:22.028069', 5, '2026-08-21 19:27:22.287482', '2026-08-21 19:27:22.028241');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (6, 1, '4a19d69d938070d5a395dc6484510b096c7ae5b1e5ae9f435ac4ee9bc712d779', 'login', '2026-08-21 19:27:21.317107', 0, '2026-08-21 19:27:22.564114', '2026-08-21 19:27:22.305615');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (7, 1, 'ea2360e585ad2b46800a0cce5dc56a299ed736d1fa47653ea7b26dda99ff6af6', 'login', '2026-08-21 19:32:22.583432', 0, '2026-08-21 19:27:22.618412', '2026-08-21 19:26:51.608782');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (8, 1, '037d6bb4efb562b0a6ab87254b5adeaeeb8e047be235d233c52fe96ed694bef3', 'login', '2026-08-21 19:32:22.620100', 0, '2026-08-21 19:27:22.645380', '2026-08-21 19:27:22.620437');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (9, 1, '72670bf6661aca567371dc4818ff13c125bb43bf0038d7c7e3f171aa1566e1a3', 'login', '2026-08-21 19:32:23.139136', 0, '2026-08-21 19:27:23.170361', '2026-08-21 19:27:23.139335');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (10, 1, '569608b1d73747ae604b11a66ca8bde58c243929c5be8e0d8e3344ce69029aeb', 'login', '2026-08-21 19:32:24.674264', 0, '2026-08-21 19:27:24.721712', '2026-08-21 19:27:24.676265');

-- Table: settlements
INSERT INTO "settlements" ("id", "blotter_id", "case_no", "case_title", "complaint_title", "nature", "date_filed", "date_confrontation", "action_taken", "date_settlement", "date_execution", "main_point", "status", "remarks", "created_at", "updated_at") VALUES (1, 2, 'STL-2026-001', 'Juan Cruz vs. Pedro Reyes', 'Noise complaint', 'Civil', '2026-08-21', NULL, '', NULL, NULL, '', 'Pending', '', '2026-08-21 19:27:24.814239', '2026-08-21 19:27:24.814244');

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Test Updated', '2026-08-21 19:27:25.526114');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-21 19:26:55.012892');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-21 19:26:55.013331');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-21 19:26:55.013759');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-21 19:26:55.014192');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-21 19:26:55.014615');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-21 19:26:55.015056');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-21 19:26:55.015477');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-21 19:26:55.015921');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-21 19:26:55.016382');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-21 19:26:55.016900');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-21 19:26:55.017457');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-21 19:26:55.017900');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-21 19:26:55.018316');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-21 19:26:55.018774');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-21 19:26:55.019457');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-21 19:26:55.019926');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-21 19:26:55.020382');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-21 19:26:55.021046');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-21 19:26:55.021731');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-21 19:26:55.022412');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-21 19:26:55.023320');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$dLi6HTdXs8gzcqNa4CPAdOQHXq/.ChhMoIU2cr8Zll3H17PqCnpE.', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, 'local', NULL, '2026-08-21 19:27:24.727377', 0, NULL, '2026-08-21 19:26:55.236205', '2026-08-21 19:26:55.236208');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$t5d5aU4oqe2fcUKGsJpLCuSyCMr2TRTXCy3zzCb13VHZwFu.fy1fm', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:26:55.430132', '2026-08-21 19:26:55.430136');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$SnvTSkAna6K8x9oM16M5RerJcJw5l2Jx6ZyFGp.nixwxRTtlEDR1q', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:26:55.620042', '2026-08-21 19:26:55.620045');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$UNpwDp0NPAj/B57XNCacleKZdL0CG/VD//6xy/5wVPwPOOD1ljwky', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:26:55.833048', '2026-08-21 19:26:55.833052');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$TU7JyFYyEsMs1QTZPI4xUOEK8pI9VBbnuPF0CM/8iSEtHTsg56MBu', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:26:56.053215', '2026-08-21 19:26:56.053218');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (6, 'active_oauth_user', 'hashed_pw_test', 'Active Test User', 'active.oauth@mapulanglupa.gov.ph', NULL, 'Desk Officer', 'Active', 1, 'google-uid-999888', 'google', NULL, '2026-08-21 19:27:03.033863', 0, NULL, '2026-08-21 19:27:03.014620', '2026-08-21 19:27:03.014624');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (7, 'inactive_oauth_user', 'hashed_pw_test', 'Inactive Test User', 'inactive.oauth@mapulanglupa.gov.ph', NULL, 'Desk Officer', 'Inactive', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:27:03.014627', '2026-08-21 19:27:03.014628');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "google_id", "auth_provider", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (8, 'testuser1', '$2b$12$5kyLa3bAznftBhNGKB1otuXBiAw/.fWgVH0VE5OJX4EKYZOnoSLhm', 'Test User', 'testuser1@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, 'local', NULL, NULL, 0, NULL, '2026-08-21 19:27:25.505259', '2026-08-21 19:27:25.505867');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – Mapulang Lupa Elementary School Area', 14.88, 120.9634, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Sitio Bata', 14.8863, 120.9679, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Pandi Village 2', 14.8782, 120.967, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Silangan Corridor (Pandi–Angat Road)', 14.8884, 120.964, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – Pandi Residences 1', 14.8818, 120.9598, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Pandi Encampment One', 14.8854, 120.9613, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – Pandi Residences 3', 14.8806, 120.97, 0.14);
