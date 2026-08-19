-- BlotterCast database backup
-- Generated: 2026-08-19 04:12:16 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:12:13.374523');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:12:13.384857');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-19 04:12:14.615526');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-19 04:12:14.617781');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:12:15.240535');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:12:15.555473');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:12:15.561627');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:12:15.879666');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:12:15.885782');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 04:12:15.893260');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-19 04:12:15.900539');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-19 04:12:15.949338');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Logout', 'System', 'User logged out', '2026-08-19 04:12:15.951727');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-19 04:12:16.268812');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-19 04:12:16.274854');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-041216.sql', '2026-08-19 04:12:16.287352');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260819-041216.sql', '2026-08-19 04:12:16.298131');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-19 04:12:16.303311');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260819-041216.sql', 11569, 'Success', 'system (automatic)', '2026-08-18 03:12:16.291873');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260819-041216.sql', 12030, 'Success', 'system (automatic)', '2026-08-18 15:12:16.305194');

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 4, 'ec201f80322be199f8dd584ab45cbc1911a5d4eaa30baa80d57d806b8dce0956', 'login', '2026-08-19 04:17:13.370299', 0, '2026-08-19 04:12:13.381111', '2026-08-19 04:12:13.371427');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 4, 'c6ab1a4fc88e6106c791ccf3acbf8b1d85ac19f0eed01961ebbdd1acae8d566a', 'login', '2026-08-19 04:17:15.238232', 0, NULL, '2026-08-19 04:12:15.238471');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 1, '5c7b10ec3067dd804126029c20f9ecd7fd0d708f69ae915fa75fa1d3e7ba0423', 'login', '2026-08-19 04:17:15.553423', 0, '2026-08-19 04:12:15.559184', '2026-08-19 04:12:15.553615');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 1, 'd54bf68b05c0547a2cd98c023f988f528199981a0a0c75a5e7f27eed1dc46351', 'login', '2026-08-19 04:17:15.877143', 0, '2026-08-19 04:12:15.883290', '2026-08-19 04:12:15.877360');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, 'fbab1aacb2e1eb48894a7a33b18a4b68c8b5509a3f2f73dad5bcd82e553c81d4', 'login', '2026-08-19 04:17:16.266350', 0, '2026-08-19 04:12:16.272461', '2026-08-19 04:12:16.266558');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-19 04:12:10.797459');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-19 04:12:10.798185');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-19 04:12:10.798674');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-19 04:12:10.799171');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-19 04:12:10.799618');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-19 04:12:10.800076');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-19 04:12:10.800502');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-19 04:12:10.800959');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-19 04:12:10.801426');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-19 04:12:10.801881');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-19 04:12:10.802356');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-19 04:12:10.802781');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-19 04:12:10.803218');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-19 04:12:10.803618');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-19 04:12:10.804021');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-19 04:12:10.804454');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-19 04:12:10.804926');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-19 04:12:10.805406');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-19 04:12:10.805847');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-19 04:12:10.806306');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-19 04:12:16.301908');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-19 04:12:10.807317');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$CECM9hwgPO63eUqzunSHce3DKMguikQPhkBadC8UdBcVXqedNJME6', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-19 04:12:16.273257', 0, NULL, '2026-08-19 04:12:11.114808', '2026-08-19 04:12:11.114814');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$OTX9G5.tPchKY.gGu0Qq/O9CLKMQCSSG7mIhnyp1yEpm7rHRH2knO', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-19 04:12:11.421569', '2026-08-19 04:12:11.421575');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$6SNchhWD7sZdhUX8CrWDeOVK47Vn7bh6m1Lw3zaoB7PKh6XjqdcyO', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-19 04:12:11.728970', '2026-08-19 04:12:11.728975');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$VlKYeB.cAZN0M/OZmBRSauUjvwa9ygnV2CR9j7X9PfOaAfeQBn7D.', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, '2026-08-19 04:12:13.382721', 0, NULL, '2026-08-19 04:12:14.612545', '2026-08-19 04:12:12.034307');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$zJIUzVbOk1CnFb0qsfyXzOM9xGtiYagBxev9uFRx4fJJQNqmy6Vnm', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, NULL, 0, NULL, '2026-08-19 04:12:12.340473', '2026-08-19 04:12:12.340478');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
