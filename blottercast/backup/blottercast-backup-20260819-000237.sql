-- BlotterCast database backup
-- Generated: 2026-08-19 00:02:37 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 00:02:34.291627');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 00:02:34.302027');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-19 00:02:35.536734');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-19 00:02:35.539238');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 00:02:36.162267');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 00:02:36.476780');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 00:02:36.483274');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 00:02:36.801034');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 00:02:36.807223');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 00:02:36.814398');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 00:02:36.821818');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-19 00:02:36.863534');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-19 00:02:36.866150');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 00:02:37.182149');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 00:02:37.188436');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-000237.sql', '2026-08-19 00:02:37.200604');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-000237.sql', '2026-08-19 00:02:37.211479');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-19 00:02:37.216483');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260819-000237.sql', 11569, 'Success', 'system (automatic)', '2026-08-17 23:02:37.205188');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260819-000237.sql', 12030, 'Success', 'system (automatic)', '2026-08-18 11:02:37.218301');

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records

-- Table: census_records

-- Table: generated_reports

-- Table: incidents

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, 'c127b283b2233018e4fd22caf1764cbfdad1cadcce328ff753312a268d081366', 'login', '2026-08-19 00:07:34.287094', 0, '2026-08-19 00:02:34.298169', '2026-08-19 00:02:34.288277');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, 'eb11a6f86abd144cd1a382d2e1948d84d2ab90c25b80dd744ce442768026cc83', 'login', '2026-08-19 00:07:36.160020', 0, NULL, '2026-08-19 00:02:36.160252');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, '448e3edc51302815d96b2b52dae8071591877bab192f360c7c8deee675655600', 'login', '2026-08-19 00:07:36.473305', 0, '2026-08-19 00:02:36.480691', '2026-08-19 00:02:36.473535');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, 'e427b96fb96293503bbb38f3da99ffa020eb0575a2957b1bbc6f4f9cec638ba6', 'login', '2026-08-19 00:07:36.798561', 0, '2026-08-19 00:02:36.804668', '2026-08-19 00:02:36.798782');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '28c67a74e3b93ad2e55ccfe7c2e6b26df1b991731bb9d0d9d350e4a2d468cd45', 'login', '2026-08-19 00:07:37.179788', 0, '2026-08-19 00:02:37.185894', '2026-08-19 00:02:37.180051');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-19 00:02:31.691698');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-19 00:02:31.692438');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-19 00:02:31.694350');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-19 00:02:31.694952');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-19 00:02:31.695496');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-19 00:02:31.695977');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-19 00:02:31.696442');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-19 00:02:31.696874');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-19 00:02:31.697354');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-19 00:02:31.697812');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-19 00:02:31.698298');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-19 00:02:31.698727');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-19 00:02:31.699224');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-19 00:02:31.699657');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-19 00:02:31.700094');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-19 00:02:31.700513');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-19 00:02:31.700985');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-19 00:02:31.701438');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-19 00:02:31.701864');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-19 00:02:31.702321');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-19 00:02:37.215217');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-19 00:02:31.703366');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$kyWOfegF4iSD.A78lwJhM.QxDaldn.ziGl.Sf6hFKCp1PTA3v01xy', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-19 00:02:37.186644', 0, NULL, '2026-08-19 00:02:32.011165', '2026-08-19 00:02:32.011171');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$T8XD5dydThbVfpEvTZS6JOCWeFK8pNRLB0ccOlKM2p9keF/Qksg6y', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-19 00:02:32.317901', '2026-08-19 00:02:32.317907');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$tdjS/weljgEiUxDaZt6RouOi8UaHEmNZpH0xP3ULSIolau2BF8Uou', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-19 00:02:32.622907', '2026-08-19 00:02:32.622912');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$lNp13tobI9NUDMquqNpCRedUgfjOKIWBAO6Dofk1D8E1Wa8.zjw7q', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, '2026-08-19 00:02:34.299858', 0, NULL, '2026-08-19 00:02:35.533288', '2026-08-19 00:02:32.930292');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$6wIEc9pGpFWLgUJ9LE9YrOcaTxASG/apbJZNHV7q04qkAx.dmzUFK', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, NULL, 0, NULL, '2026-08-19 00:02:33.236525', '2026-08-19 00:02:33.236532');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
