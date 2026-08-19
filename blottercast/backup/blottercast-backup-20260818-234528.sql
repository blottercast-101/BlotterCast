-- BlotterCast database backup
-- Generated: 2026-08-18 23:45:28 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:25.561122');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:45:25.571725');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-18 23:45:26.818203');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-18 23:45:26.820737');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:27.448241');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:27.763062');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:45:27.769272');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:28.088164');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:45:28.094548');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 23:45:28.102438');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 23:45:28.109929');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-18 23:45:28.158093');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-18 23:45:28.160747');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:45:28.474821');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:45:28.481035');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-234528.sql', '2026-08-18 23:45:28.493173');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-234528.sql', '2026-08-18 23:45:28.504357');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-18 23:45:28.509629');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260818-234528.sql', 11569, 'Success', 'system (automatic)', '2026-08-17 22:45:28.498047');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260818-234528.sql', 12030, 'Success', 'system (automatic)', '2026-08-18 10:45:28.511500');

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, 'e58b774782a6ebc2dc5abd6046a910cfea9eba158f9dc67f8b08488a66534e56', 'login', '2026-08-18 23:50:25.556772', 0, '2026-08-18 23:45:25.567768', '2026-08-18 23:45:25.558001');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, 'f263948d9a0ad39ecaaa4f18271bb86c9dd6b06186ea525b3f94e6ca3ab2af2f', 'login', '2026-08-18 23:50:27.446180', 0, NULL, '2026-08-18 23:45:27.446424');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, '6b816ff3e556a87b496e760fa1b32c2a14595e63f71c3a79d494f502c59f3972', 'login', '2026-08-18 23:50:27.760475', 0, '2026-08-18 23:45:27.766834', '2026-08-18 23:45:27.760727');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, 'a90061b43a670928dc08b3157cb9b03eaa09dbfd0cd2dbf56fd7cbe757f40a3e', 'login', '2026-08-18 23:50:28.085617', 0, '2026-08-18 23:45:28.091929', '2026-08-18 23:45:28.085860');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, 'c6952e302c1cc0db85f1c046035d9f1809ee4761952817e8468615054cb1c2e3', 'login', '2026-08-18 23:50:28.472201', 0, '2026-08-18 23:45:28.478596', '2026-08-18 23:45:28.472446');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-18 23:45:22.879865');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-18 23:45:22.880600');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-18 23:45:22.881193');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-18 23:45:22.881787');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-18 23:45:22.882319');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-18 23:45:22.882837');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-18 23:45:22.883319');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-18 23:45:22.883816');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-18 23:45:22.884349');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-18 23:45:22.884847');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-18 23:45:22.885415');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-18 23:45:22.886002');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-18 23:45:22.886489');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-18 23:45:22.886993');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-18 23:45:22.887481');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-18 23:45:22.888015');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-18 23:45:22.888486');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-18 23:45:22.888985');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-18 23:45:22.889475');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-18 23:45:22.889959');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-18 23:45:28.508310');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-18 23:45:22.891073');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$E/CdCiQdqaUUE93E8o1UkOjMj6ASZd35ydiaiYhJFV1VgYtscw2PW', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-18 23:45:28.479392', 0, NULL, '2026-08-18 23:45:23.204885', '2026-08-18 23:45:23.204891');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$MzIzVmY4j72dXZyKY3gfIuYztT1NIihVLmDljokp8AcNL6VtBuCNu', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:23.514406', '2026-08-18 23:45:23.514414');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$psAvbYg48J0P9kOGMOl4y.2P1ANFTm5bPRtu7gCvj68bj7h968cfe', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:23.826884', '2026-08-18 23:45:23.826890');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$EJUGTzKHPeV3BlXkS9j9P.y78ut1bIR2xyRz4B9X51xRM4QZSNp5G', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, '2026-08-18 23:45:25.569405', 0, NULL, '2026-08-18 23:45:26.814323', '2026-08-18 23:45:24.135150');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$1074uanHAYk5l8ttizwEk.sxzzOSL7hwNtK7DnBIFCmoe6Cyip7Di', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:45:24.441667', '2026-08-18 23:45:24.441673');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
