-- BlotterCast database backup
-- Generated: 2026-08-19 09:46:56 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:46:53.730086');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 09:46:53.742081');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-19 09:46:54.990746');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-19 09:46:54.993102');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:46:55.618571');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:46:55.930836');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 09:46:55.939048');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:46:56.253980');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 09:46:56.261282');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 09:46:56.268335');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 09:46:56.275844');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-19 09:46:56.317451');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-19 09:46:56.319922');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 09:46:56.632014');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 09:46:56.638988');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-094656.sql', '2026-08-19 09:46:56.651040');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-094656.sql', '2026-08-19 09:46:56.661669');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-19 09:46:56.667933');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260819-094656.sql', 11722, 'Success', 'system (automatic)', '2026-08-18 08:46:56.655422');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260819-094656.sql', 12183, 'Success', 'system (automatic)', '2026-08-18 20:46:56.669833');

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, 'daa335b432d01f79b977a3fe067fb220085974ff91d4421952c5fc168adbf7dd', 'login', '2026-08-19 09:51:53.725274', 0, '2026-08-19 09:46:53.736870', '2026-08-19 09:46:53.726410');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, 'b4a8cdda3a1868995d527b16242c95bfa918b38bec3070875f185815509359e0', 'login', '2026-08-19 09:51:55.616551', 0, NULL, '2026-08-19 09:46:55.616797');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, 'c15bc880f81772a496593be39f0a29ce7c63aa7f37b9dd08a2f8360e4eaf7355', 'login', '2026-08-19 09:51:55.928740', 0, '2026-08-19 09:46:55.934474', '2026-08-19 09:46:55.928977');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, '69c034fd965a081942d519aaaf7d6f0a52f3ffe5563a2c54210c1ec7ebebf4ba', 'login', '2026-08-19 09:51:56.251669', 0, '2026-08-19 09:46:56.257857', '2026-08-19 09:46:56.251894');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, 'f638b1c516b55e54ce3b83fd3c362fdd917bb5e478ff8fd564aecd6bcf748316', 'login', '2026-08-19 09:51:56.629875', 0, '2026-08-19 09:46:56.635299', '2026-08-19 09:46:56.630063');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-19 09:46:51.089312');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-19 09:46:51.090051');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-19 09:46:51.090550');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-19 09:46:51.091120');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-19 09:46:51.091598');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-19 09:46:51.092160');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-19 09:46:51.092604');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-19 09:46:51.093070');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-19 09:46:51.093566');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-19 09:46:51.094046');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-19 09:46:51.094566');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-19 09:46:51.095323');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-19 09:46:51.095942');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-19 09:46:51.096429');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-19 09:46:51.096908');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-19 09:46:51.097358');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-19 09:46:51.097838');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-19 09:46:51.098278');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-19 09:46:51.098740');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-19 09:46:51.099273');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-19 09:46:56.666536');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-19 09:46:51.100395');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$/ceu9j0ZH0X/ls1pdpO0l.v/4JlfMBq2PHRHUfyXBozG/3s7sh9vG', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-19 09:46:56.637328', 0, NULL, '2026-08-19 09:46:51.419687', '2026-08-19 09:46:51.419693');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$66JBpphw/GyMmGpuhCw90..1LuQfi43vfBdcvN1NLxi37pJWRhM3K', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:46:51.732485', '2026-08-19 09:46:51.732491');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$YACjEmgWUHP4q9JTt8Z4k.So1nNqTrtzeL6bJWUR9mO1.CqN2RCnS', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:46:52.042968', '2026-08-19 09:46:52.042974');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$h0nXODcb7mUslS//iTBzpexFYa3vBR2d2Lqy1MIpX3LSNSg3ncVK.', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, '2026-08-19 09:46:53.739940', 0, NULL, '2026-08-19 09:46:54.987713', '2026-08-19 09:46:52.352511');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$bOPYjIu1c4qLZREriKqwUuOcaRo/iUuFXeOgeFgzVylfymm/phNGK', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-19 09:46:52.661410', '2026-08-19 09:46:52.661417');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – Mapulang Lupa Elementary School Area', 14.88, 120.9634, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Sitio Bata', 14.8863, 120.9679, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Pandi Village 2', 14.8782, 120.967, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Silangan Corridor (Pandi–Angat Road)', 14.8884, 120.964, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – Pandi Residences 1', 14.8818, 120.9598, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Pandi Encampment One', 14.8854, 120.9613, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – Pandi Residences 3', 14.8806, 120.97, 0.14);
