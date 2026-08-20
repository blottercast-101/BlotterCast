-- BlotterCast database backup
-- Generated: 2026-08-20 04:17:50 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:50.237839');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-20 04:17:50.249403');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-20 04:17:50.262908');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Created', 'Users', 'New account created: testuser1 (Desk Officer)', '2026-08-20 04:17:50.754880');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-20 04:17:50.766892');

-- Table: backups

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (1, 'BLT-2026-001', '2026-08-20', 'Juan Cruz', 1, '', 'Pedro Reyes', NULL, '', 'Noise complaint', 'CIVIL', 'Pending', NULL, 0, '2026-08-20 04:17:50.298050', '2026-08-20 04:17:50.298057');

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Cruz', 'Juan', '', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '', 'Not Registered', '', 'Active', '2026-08-20 04:17:50.260697', '2026-08-20 04:17:50.260767');

-- Table: generated_reports
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (1, 'Incident Summary Report', 'System Administrator', '2026-01-01', '2026-12-31', 'PDF', 'incident-summary-report-20260820-041750.pdf', '2026-08-20 04:17:50.393528');
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (2, 'Settlement Compliance Report', 'System Administrator', '2026-08-01', '2026-08-20', 'Excel', 'settlement-compliance-report-20260820-041750.csv', '2026-08-20 04:17:50.399813');

-- Table: incidents
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (1, 'INC-2026-0001', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 0', 14.883284, 120.966049, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-20 04:17:50.276157', '2026-08-20 04:17:50.276162');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (2, 'INC-2026-0002', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 1', 14.883278, 120.965909, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-20 04:17:50.282785', '2026-08-20 04:17:50.282788');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (3, 'INC-2026-0003', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 2', 14.884014, 120.965136, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-20 04:17:50.287835', '2026-08-20 04:17:50.287845');

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '6807681d6ed6853051c226648fca5a5c2485faa758e70bed4d99364bf24b406d', 'login', '2026-08-20 04:22:50.233196', 0, '2026-08-20 04:17:50.244324', '2026-08-20 04:17:50.234500');

-- Table: settlements
INSERT INTO "settlements" ("id", "blotter_id", "case_no", "case_title", "complaint_title", "nature", "date_filed", "date_confrontation", "action_taken", "date_settlement", "date_execution", "main_point", "status", "remarks", "created_at", "updated_at") VALUES (1, 1, 'STL-2026-001', 'Juan Cruz vs. Pedro Reyes', 'Noise complaint', 'Civil', '2026-08-20', NULL, '', NULL, NULL, '', 'Pending', '', '2026-08-20 04:17:50.309588', '2026-08-20 04:17:50.309596');

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Test Updated', '2026-08-20 04:17:50.765592');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-20 04:17:47.635870');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-20 04:17:47.636389');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-20 04:17:47.636907');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-20 04:17:47.637392');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-20 04:17:47.637845');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-20 04:17:47.638327');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-20 04:17:47.638782');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-20 04:17:47.639273');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-20 04:17:47.639695');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-20 04:17:47.640162');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-20 04:17:47.640620');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-20 04:17:47.641134');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-20 04:17:47.641627');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-20 04:17:47.642243');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-20 04:17:47.642724');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-20 04:17:47.643188');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-20 04:17:47.643620');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-20 04:17:47.644144');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-20 04:17:47.644615');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-20 04:17:47.645261');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-20 04:17:47.645969');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$5BzCyJbTIYVqR8esXEHEpOElccs1C//aRsf7Y7fNgITrTLwJnBa7q', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-20 04:17:50.247334', 0, NULL, '2026-08-20 04:17:47.951374', '2026-08-20 04:17:47.951378');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$MFh5Zqy9saYmmuHEMArLQOopWTiLS9Trniravwq5oCvRgt7AT9P4q', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:48.258815', '2026-08-20 04:17:48.258834');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$igvGCPlfbWopqaOHndODF.yRfv4TDH9kge5RK8ik6TN.EtEanlu/a', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:48.567371', '2026-08-20 04:17:48.567377');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$a9qhyQqHea8fmL7sdRv0Dunu1ikD26tSjBFX1sqFkWxM/ws3CpAY2', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:48.872539', '2026-08-20 04:17:48.872544');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$0e/jwqqHKXRuLTBm2YH/teWZ/XOsLjaZrdJOxxWccoyhCjCPnDQwS', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:49.177978', '2026-08-20 04:17:49.177984');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (6, 'testuser1', '$2b$12$88.iMe6Zt8NXXVTOS0wtF.ct2o6dkF07ayAwadQ/XGV7x7K824U0a', 'Test User', 'testuser1@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:50.751608', '2026-08-20 04:17:50.752733');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – Mapulang Lupa Elementary School Area', 14.88, 120.9634, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Sitio Bata', 14.8863, 120.9679, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Pandi Village 2', 14.8782, 120.967, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Silangan Corridor (Pandi–Angat Road)', 14.8884, 120.964, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – Pandi Residences 1', 14.8818, 120.9598, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Pandi Encampment One', 14.8854, 120.9613, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – Pandi Residences 3', 14.8806, 120.97, 0.14);
