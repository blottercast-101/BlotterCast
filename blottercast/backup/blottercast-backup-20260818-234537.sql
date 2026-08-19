-- BlotterCast database backup
-- Generated: 2026-08-18 23:45:37 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:37.395542');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:45:37.406268');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Created', 'Census', 'New resident recorded: Juan Cruz', '2026-08-18 23:45:37.418716');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Created', 'Users', 'New account created: testuser1 (Desk Officer)', '2026-08-18 23:45:37.900016');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-18 23:45:37.911653');

-- Table: backups

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records
INSERT INTO "blotter_records" ("id", "docket_no", "date_filed", "complainant", "complainant_id", "complainant_addr", "respondent", "respondent_id", "respondent_addr", "nature", "case_type", "status", "zone_id", "archived", "created_at", "updated_at") VALUES (1, 'BLT-2026-001', '2026-08-18', 'Juan Cruz', 1, '', 'Pedro Reyes', NULL, '', 'Noise complaint', 'CIVIL', 'Pending', NULL, 0, '2026-08-18 23:45:37.449554', '2026-08-18 23:45:37.449557');

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Cruz', 'Juan', '', '1990-05-01', 'Male', 'Single', 'Filipino', NULL, '123 Rizal St', 'HH-01', '', 'Not Registered', '', 'Active', '2026-08-18 23:45:37.417189', '2026-08-18 23:45:37.417193');

-- Table: generated_reports
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (1, 'Incident Summary Report', 'System Administrator', '2026-01-01', '2026-12-31', 'PDF', 'incident-summary-report-20260818-234537.pdf', '2026-08-18 23:45:37.537863');
INSERT INTO "generated_reports" ("id", "report_type", "generated_by", "period_from", "period_to", "format", "file_path", "created_at") VALUES (2, 'Settlement Compliance Report', 'System Administrator', '2026-08-01', '2026-08-18', 'Excel', 'settlement-compliance-report-20260818-234537.csv', '2026-08-18 23:45:37.543680');

-- Table: incidents
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (1, 'INC-2026-0001', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 0', 14.883198, 120.965377, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-18 23:45:37.428635', '2026-08-18 23:45:37.428639');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (2, 'INC-2026-0002', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 1', 14.883426, 120.965895, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-18 23:45:37.436012', '2026-08-18 23:45:37.436017');
INSERT INTO "incidents" ("id", "report_no", "incident_date", "time_reported", "hour", "zone_id", "location", "lat", "lng", "category", "description", "reporter", "officer", "priority", "status", "created_at", "updated_at") VALUES (3, 'INC-2026-0003', '2026-08-10', '14:30:00.000000', 14, 'Zone 1', 'Test location 2', 14.884051, 120.965727, 'Theft', '', '', '', 'High', 'Under Investigation', '2026-08-18 23:45:37.440667', '2026-08-18 23:45:37.440670');

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '79fe6f63c5d565c97b215921cc596b23d3596bab5dd43f2168ec339ef8b06acb', 'login', '2026-08-18 23:50:37.391070', 0, '2026-08-18 23:45:37.402396', '2026-08-18 23:45:37.392285');

-- Table: settlements
INSERT INTO "settlements" ("id", "blotter_id", "case_no", "case_title", "complaint_title", "nature", "date_filed", "date_confrontation", "action_taken", "date_settlement", "date_execution", "main_point", "status", "remarks", "created_at", "updated_at") VALUES (1, 1, 'STL-2026-001', 'Juan Cruz vs. Pedro Reyes', 'Noise complaint', 'Civil', '2026-08-18', NULL, '', NULL, NULL, '', 'Pending', '', '2026-08-18 23:45:37.458804', '2026-08-18 23:45:37.458807');

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Test Updated', '2026-08-18 23:45:37.910278');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-18 23:45:34.770905');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-18 23:45:34.771393');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-18 23:45:34.771888');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-18 23:45:34.772328');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-18 23:45:34.772781');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-18 23:45:34.773210');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-18 23:45:34.773664');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-18 23:45:34.774111');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-18 23:45:34.774515');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-18 23:45:34.774988');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-18 23:45:34.775433');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-18 23:45:34.775889');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-18 23:45:34.776312');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-18 23:45:34.776744');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-18 23:45:34.777182');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-18 23:45:34.777725');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-18 23:45:34.778224');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-18 23:45:34.778669');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-18 23:45:34.779130');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-18 23:45:34.779539');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-18 23:45:34.780129');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$YK0p9Y6kjrI3nOEget.YR.es2.Rqo1nFco8uF/RsgTV8k2GabXRW.', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-18 23:45:37.404105', 0, NULL, '2026-08-18 23:45:35.088895', '2026-08-18 23:45:35.088901');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$jwT9WlzBxl2UXGFEM4Wwte.1Qv9nVgMMNhdvxn8JNFO1y3cqgkxqK', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:35.397870', '2026-08-18 23:45:35.397876');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$rRkYst/nYv5AuuGbxse4suO22Zm97mq95OGXntL3wSVhrlE81WxHy', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:35.708133', '2026-08-18 23:45:35.708139');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$IzRrzHoZ2DBU60BiRbEOUeuxsZhDfFWzAC4wNgFQ1vB2bHrTlqxCa', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:36.022157', '2026-08-18 23:45:36.022166');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$3mjb/8.2U0tMDc.ofAziV.1gSiSQN0eqwv9lFdWg682auFupzkEGC', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:36.333455', '2026-08-18 23:45:36.333462');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (6, 'testuser1', '$2b$12$ZY3nHQ1qttbbbSCDqkYAPuSVw38xbGyrBiF65dvRoIwFO/tvw0GkO', 'Test User', 'testuser1@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:37.896082', '2026-08-18 23:45:37.897308');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
