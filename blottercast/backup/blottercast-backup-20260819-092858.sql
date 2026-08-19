-- BlotterCast database backup
-- Generated: 2026-08-19 09:28:58 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:28:57.517834');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 09:28:57.530378');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-19 09:28:57.542625');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Created', 'Users', 'New account created: testuser1 (Desk Officer)', '2026-08-19 09:28:58.027931');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-19 09:28:58.040857');

-- Table: backups

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (1, 'BLT-2026-001', '2026-08-19', 'Juan Cruz', 1, '', 'Pedro Reyes', NULL, '', 'Noise complaint', 'CIVIL', 'Pending', NULL, 0, '2026-08-19 09:28:57.571966', '2026-08-19 09:28:57.571969');

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Cruz', 'Juan', '', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '', 'Not Registered', '', 'Active', '2026-08-19 09:28:57.541112', '2026-08-19 09:28:57.541116');

-- Table: generated_reports
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (1, 'Incident Summary Report', 'System Administrator', '2026-01-01', '2026-12-31', 'PDF', 'incident-summary-report-20260819-092857.pdf', '2026-08-19 09:28:57.659194');
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (2, 'Settlement Compliance Report', 'System Administrator', '2026-08-01', '2026-08-19', 'Excel', 'settlement-compliance-report-20260819-092857.csv', '2026-08-19 09:28:57.665049');

-- Table: incidents
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (1, 'INC-2026-0001', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 0', 14.883385, 120.966024, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-19 09:28:57.553074', '2026-08-19 09:28:57.553082');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (2, 'INC-2026-0002', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 1', 14.884138, 120.965481, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-19 09:28:57.559100', '2026-08-19 09:28:57.559103');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (3, 'INC-2026-0003', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 2', 14.883333, 120.965034, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-19 09:28:57.563695', '2026-08-19 09:28:57.563698');

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '098e74b5a9ee8473839888a6897d608d977bfecff4491d9ca8043893c64c0a94', 'login', '2026-08-19 09:33:57.513032', 0, '2026-08-19 09:28:57.525027', '2026-08-19 09:28:57.514244');

-- Table: settlements
INSERT INTO "settlements" ("id", "blotter_id", "case_no", "case_title", "complaint_title", "nature", "date_filed", "date_confrontation", "action_taken", "date_settlement", "date_execution", "main_point", "status", "remarks", "created_at", "updated_at") VALUES (1, 1, 'STL-2026-001', 'Juan Cruz vs. Pedro Reyes', 'Noise complaint', 'Civil', '2026-08-19', NULL, '', NULL, NULL, '', 'Pending', '', '2026-08-19 09:28:57.580657', '2026-08-19 09:28:57.580669');

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Test Updated', '2026-08-19 09:28:58.039377');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-19 09:28:54.912776');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-19 09:28:54.913357');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-19 09:28:54.913971');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-19 09:28:54.914472');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-19 09:28:54.914975');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-19 09:28:54.915435');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-19 09:28:54.915868');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-19 09:28:54.916342');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-19 09:28:54.916814');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-19 09:28:54.917278');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-19 09:28:54.917713');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-19 09:28:54.918189');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-19 09:28:54.918634');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-19 09:28:54.919133');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-19 09:28:54.919633');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-19 09:28:54.920090');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-19 09:28:54.920554');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-19 09:28:54.920985');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-19 09:28:54.921465');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-19 09:28:54.921919');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-19 09:28:54.922495');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$mQL1v0r.I7h9i.4LBDm.IuPBYrmy2r2QVUcLfGNcR4DRqP22Gr7Di', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-19 09:28:57.528085', 0, NULL, '2026-08-19 09:28:55.235962', '2026-08-19 09:28:55.235967');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$/9vgC6.ZiAiY4g4VXwbpGeks2Rwp9Hf.GAVW8N/XbZPdEStuUwda.', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:28:55.543088', '2026-08-19 09:28:55.543094');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$H854LfEN/NbhZV58cSn76.d7A2xBCDZRrYOMmOS6E16HoRorD5jdq', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:28:55.850217', '2026-08-19 09:28:55.850224');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$7pgMpc8WTC0piHQ./M8hPevKuBjPvFY33EqrVPwe0iqyTpB734l/a', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:28:56.159076', '2026-08-19 09:28:56.159082');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$vEFFhlbjKT0Uo2jEFGXa5eroNNkMCM86nImqizi6BZ51h.UEdhFj.', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:28:56.464138', '2026-08-19 09:28:56.464143');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (6, 'testuser1', '$2b$12$wf7kB36kgenZFBB8kafzQODPey54t2VUCZ61qCG3lmipbTGYO0.Be', 'Test User', 'testuser1@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:28:58.024412', '2026-08-19 09:28:58.025575');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
