-- BlotterCast database backup
-- Generated: 2026-08-20 04:17:41 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:38.578046');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-20 04:17:38.588894');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-20 04:17:39.816631');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-20 04:17:39.818867');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:40.439182');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:40.753751');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-20 04:17:40.761526');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:41.079539');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-20 04:17:41.086397');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-20 04:17:41.093167');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-20 04:17:41.100568');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-20 04:17:41.146271');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-20 04:17:41.148748');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-20 04:17:41.460095');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-20 04:17:41.466997');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260820-041741.sql', '2026-08-20 04:17:41.478560');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260820-041741.sql', '2026-08-20 04:17:41.489273');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-20 04:17:41.495632');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260820-041741.sql', 11722, 'Success', 'system (automatic)', '2026-08-19 03:17:41.482998');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260820-041741.sql', 12183, 'Success', 'system (automatic)', '2026-08-19 15:17:41.497556');

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, '669fc884a5ca89c9dc96616e2f7d635978208a0aea3f2486dfaeec3e96ebfe1a', 'login', '2026-08-20 04:22:38.573964', 0, '2026-08-20 04:17:38.584061', '2026-08-20 04:17:38.575101');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, '4952e9c2d4e2d32afa27f78d1e170a78e7db90543b5b945813dc2eba61fcc3f9', 'login', '2026-08-20 04:22:40.437212', 0, NULL, '2026-08-20 04:17:40.437427');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, 'b75298785b423c2e05a81210a762a470dd4bfdc08c21c771845983dd929c73d4', 'login', '2026-08-20 04:22:40.751558', 0, '2026-08-20 04:17:40.757169', '2026-08-20 04:17:40.751764');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, 'c3df87bf6641d8f6f489cac912f7c96bbc47d0276e161f329875afad69fbb01a', 'login', '2026-08-20 04:22:41.077397', 0, '2026-08-20 04:17:41.082926', '2026-08-20 04:17:41.077607');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '8b9051d7e3f6082d48485921f99e39c197fb534bc21b75b2d4c44d57e4f2346a', 'login', '2026-08-20 04:22:41.457982', 0, '2026-08-20 04:17:41.463437', '2026-08-20 04:17:41.458218');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-20 04:17:35.982916');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-20 04:17:35.983658');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-20 04:17:35.984209');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-20 04:17:35.984761');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-20 04:17:35.986454');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-20 04:17:35.987012');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-20 04:17:35.987550');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-20 04:17:35.988040');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-20 04:17:35.988532');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-20 04:17:35.989073');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-20 04:17:35.989536');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-20 04:17:35.989989');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-20 04:17:35.990534');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-20 04:17:35.991049');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-20 04:17:35.991512');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-20 04:17:35.991948');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-20 04:17:35.992418');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-20 04:17:35.992911');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-20 04:17:35.993418');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-20 04:17:35.993887');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-20 04:17:41.494124');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-20 04:17:35.994931');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$JbVHTUA8aW.JZtqIeUvT2.cvvIx07MxMeYgghOiqOGsaO.EvJJxWC', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', 1, NULL, '2026-08-20 04:17:41.465400', 0, NULL, '2026-08-20 04:17:36.331306', '2026-08-20 04:17:36.331310');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$WIO2azZN.YPlpnemXmhaXue2SoFAN2Om/P0ZXRMkz3wE/zsTZ4lTy', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:36.637648', '2026-08-20 04:17:36.637653');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$HdnFcuFnpZuQMV6Rj/Eebem4K8Ggs3Vx3r7wMBjqK29383xuvfttC', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:36.941237', '2026-08-20 04:17:36.941241');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$uFXR0sQKLC55QunBrk/teOXUkBZYnY1MlA22oE0bQuL4sFy1PnPC2', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', 1, NULL, '2026-08-20 04:17:38.586891', 0, NULL, '2026-08-20 04:17:39.814164', '2026-08-20 04:17:37.245533');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "mfa_enabled", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$g0wzkV78mcsyzLqhdBjlieccX1ZmXOE9s67u2aRE.SowLMV9Ln87y', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', 1, NULL, NULL, 0, NULL, '2026-08-20 04:17:37.552378', '2026-08-20 04:17:37.552383');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Mapulang Lupa Proper (Barangay Hall Area)', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – Mapulang Lupa Elementary School Area', 14.88, 120.9634, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Sitio Bata', 14.8863, 120.9679, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Pandi Village 2', 14.8782, 120.967, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Silangan Corridor (Pandi–Angat Road)', 14.8884, 120.964, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – Pandi Residences 1', 14.8818, 120.9598, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Pandi Encampment One', 14.8854, 120.9613, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – Pandi Residences 3', 14.8806, 120.97, 0.14);
