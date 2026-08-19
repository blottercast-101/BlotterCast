-- BlotterCast database backup
-- Generated: 2026-08-19 04:28:31 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:28:28.966421');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:28:28.977802');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-19 04:28:30.213467');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-19 04:28:30.215788');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:28:30.838330');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:28:31.153747');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:28:31.161516');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:28:31.479485');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:28:31.487109');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 04:28:31.494216');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 04:28:31.502844');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-19 04:28:31.553730');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-19 04:28:31.556491');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:28:31.872391');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:28:31.879760');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-042831.sql', '2026-08-19 04:28:31.891920');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-042831.sql', '2026-08-19 04:28:31.903011');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-19 04:28:31.909831');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260819-042831.sql', 11659, 'Success', 'system (automatic)', '2026-08-18 03:28:31.896581');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260819-042831.sql', 12120, 'Success', 'system (automatic)', '2026-08-18 15:28:31.911729');

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, '28d512082c183aa58c368c6dbe50f57c611fd192c9264b1049c0d966f9178f8c', 'login', '2026-08-19 04:33:28.962145', 0, '2026-08-19 04:28:28.972956', '2026-08-19 04:28:28.963288');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, '32c77e618402495f09d4344b71eb8f5144aca6cd0288326d99ab05e111fa7bd3', 'login', '2026-08-19 04:33:30.836122', 0, NULL, '2026-08-19 04:28:30.836348');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, 'a0397ac301d1a2db3cc550db0645b103dab318068601f292fd30c0ef8caf4762', 'login', '2026-08-19 04:33:31.150917', 0, '2026-08-19 04:28:31.157607', '2026-08-19 04:28:31.151154');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, '85f8e07fccef5bd444ded311006e83018f81057d79d08ac70b43d0ef4391a78c', 'login', '2026-08-19 04:33:31.477022', 0, '2026-08-19 04:28:31.483451', '2026-08-19 04:28:31.477249');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '3f8be88019a324201ab961bb93ac190c167cc621d63e9ec38a0ba5d71a889468', 'login', '2026-08-19 04:33:31.870066', 0, '2026-08-19 04:28:31.876206', '2026-08-19 04:28:31.870296');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-19 04:28:26.310138');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-19 04:28:26.310873');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-19 04:28:26.311365');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-19 04:28:26.311837');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-19 04:28:26.312291');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-19 04:28:26.312716');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-19 04:28:26.313184');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-19 04:28:26.313596');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-19 04:28:26.314102');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-19 04:28:26.314554');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-19 04:28:26.315007');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-19 04:28:26.315453');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-19 04:28:26.315882');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-19 04:28:26.316296');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-19 04:28:26.316691');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-19 04:28:26.317122');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-19 04:28:26.317555');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-19 04:28:26.318052');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-19 04:28:26.318503');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-19 04:28:26.318980');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-19 04:28:31.908281');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-19 04:28:26.320060');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$PrRFxtZkN0a34NRv79FDWeg3vB0/cC4YZKh95Uy8GuHM14y76C82C', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-19 04:28:31.878210', 0, NULL, '2026-08-19 04:28:26.637923', '2026-08-19 04:28:26.637928');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$cJMfFMVi1izM7DT9ZHipB.bIEUGOn8Sj3XuYnDi8HvPHjmLQ/KvwG', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 04:28:26.948371', '2026-08-19 04:28:26.948377');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$AesWcbJJ/DOXG7R9JahQweiLE5UUdQC2kTyV48dgzLINeQhMvMv.a', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 04:28:27.255589', '2026-08-19 04:28:27.255595');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$c2md7CeIGehJtQ0bjVNTjuwhn4VC68UmRiWrDnDZ8mrdu0Qz/IYNC', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, '2026-08-19 04:28:28.975791', 0, NULL, '2026-08-19 04:28:30.210377', '2026-08-19 04:28:27.562673');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$4JpRRm4zPp1hRTVYikIhLePvx.IiNtbsFR3obb7dOVfAthcZvv6ry', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 04:28:27.870314', '2026-08-19 04:28:27.870320');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
