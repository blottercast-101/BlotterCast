-- BlotterCast database backup
-- Generated: 2026-08-18 08:08:07 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:02.563573');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:02.577439');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Created', 'Census', 'New resident recorded: Maria Dela Cruz', '2026-08-18 08:08:02.591193');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Logout', 'System', 'User logged out', '2026-08-18 08:08:02.602769');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'pencoder', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:02.921091');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'pencoder', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:02.927455');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'pencoder', 'Created', 'Census', 'New resident recorded: Ana Reyes', '2026-08-18 08:08:02.935423');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:04.076472');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:04.088516');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-18 08:08:05.344029');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-18 08:08:05.346851');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:05.975361');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:06.291615');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:06.298127');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:06.613810');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:06.620219');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 08:08:06.627629');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 08:08:06.635092');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (19, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-18 08:08:06.656222');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (20, 'admin', 'Logout', 'System', 'User logged out', '2026-08-18 08:08:06.658856');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (21, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 08:08:06.970354');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (22, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 08:08:06.976536');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (23, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-080806.sql', '2026-08-18 08:08:06.988576');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (24, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-080806.sql', '2026-08-18 08:08:07.000082');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (25, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-18 08:08:07.005287');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260818-080806.sql', 14537, 'Success', 'system (automatic)', '2026-08-17 07:08:06.993317');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260818-080806.sql', 14998, 'Success', 'system (automatic)', '2026-08-17 19:08:07.007221');

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Dela Cruz', 'Maria', '', '1985-03-10', 'Female', 'Single', 'Filipino', NULL, '45 Mabini St', 'HH-09', '', 'Not Registered', '', 'Active', '2026-08-18 08:08:02.589031', '2026-08-18 08:08:02.589036');
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (2, 'RES-0002', 'Reyes', 'Ana', '', '2000-01-01', 'Female', 'Single', 'Filipino', NULL, '', '', '', 'Not Registered', '', 'Active', '2026-08-18 08:08:02.934054', '2026-08-18 08:08:02.934058');

-- Table: generated_reports

-- Table: incidents

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '1a2d310f8739b18ec14f8c36415da586552020d02fce8532350f9541586a3aa4', 'login', '2026-08-18 08:13:02.558974', 0, '2026-08-18 08:08:02.570422', '2026-08-18 08:08:02.560176');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 5, '32d655a99d228e9f375fa44079011025cfef1733f52c9c3a4debccb978e84080', 'login', '2026-08-18 08:13:02.918609', 0, '2026-08-18 08:08:02.924799', '2026-08-18 08:08:02.918844');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 4, 'fbddedb13019081c87781b91fba9435e44fb99c90aaa20cb81e003ea1ef2ee84', 'login', '2026-08-18 08:13:04.071236', 0, '2026-08-18 08:08:04.083886', '2026-08-18 08:08:04.072638');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 4, '5e005bc844727922b9e4149d9fc8088a85d27630e36ebfa5de7e40881b8d15e6', 'login', '2026-08-18 08:13:05.972951', 0, NULL, '2026-08-18 08:08:05.973213');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '9bfbdda7bb1096a07b45a1fc69dffc7be1c26a42a57329c018c08abbef2a5818', 'login', '2026-08-18 08:13:06.289119', 0, '2026-08-18 08:08:06.295420', '2026-08-18 08:08:06.289357');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (6, 1, '32fb9c97f8aaf683ca19171401679aaa703c92e2f7a8b35f0b4f2ecc93a2e230', 'login', '2026-08-18 08:13:06.611341', 0, '2026-08-18 08:08:06.617547', '2026-08-18 08:08:06.611590');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (7, 1, '6bda92d1030cfd829499039beaac2eb140f87021ad71070c64fea246baa68549', 'login', '2026-08-18 08:13:06.967924', 0, '2026-08-18 08:08:06.974104', '2026-08-18 08:08:06.968142');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-18 08:07:59.901700');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-18 08:07:59.902541');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-18 08:07:59.903131');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-18 08:07:59.903886');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-18 08:07:59.904784');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-18 08:07:59.905653');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-18 08:07:59.906532');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-18 08:07:59.907093');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-18 08:07:59.907656');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-18 08:07:59.908134');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-18 08:07:59.908721');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-18 08:07:59.909229');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-18 08:07:59.909739');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-18 08:07:59.910310');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-18 08:07:59.911116');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-18 08:07:59.911731');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-18 08:07:59.912217');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-18 08:07:59.912849');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-18 08:07:59.913436');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-18 08:07:59.913917');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-18 08:08:07.003884');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-18 08:07:59.915011');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$SFsuzJTR1/39FTuvfUhgA.EKhxORxZjvR4xHarLDD0B0of8Taz60G', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-18 08:08:06.974870', 0, NULL, '2026-08-18 08:08:00.227192', '2026-08-18 08:08:00.227197');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$7.992qOFM0E/Ofs3rcwSM.XUr/ZFp8yXMorAQfQ6WVHprCl89rnH.', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-18 08:08:00.539766', '2026-08-18 08:08:00.539772');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$e1wayZiuq8hXtl3BOcFEbucjvflTTqUaHkUPzgp/nwKyoMl0vNsQO', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 08:08:00.850781', '2026-08-18 08:08:00.850787');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$51KVQ5T.GeS8YK/i0Ptb1OT2.l4Gg74WB8w17HqC4mZ4zJQcHBFie', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, '2026-08-18 08:08:04.085743', 0, NULL, '2026-08-18 08:08:05.339793', '2026-08-18 08:08:01.160859');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$lC1laXX721DNpgCT06si5.wT4j7MtD8x.V6TRdfPeevv4JNF.XNmS', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, '2026-08-18 08:08:02.925600', 0, NULL, '2026-08-18 08:08:01.474817', '2026-08-18 08:08:01.474825');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
