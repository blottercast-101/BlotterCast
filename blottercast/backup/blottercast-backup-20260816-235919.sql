-- BlotterCast database backup
-- Generated: 2026-08-16 23:59:19 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-16 23:58:37.362721');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-16 23:59:17.001437');

-- Table: backups

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
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '5bd7923a783ce3b66e93095b793a9f0e4607fa15796e67773863e90516587e33', 'login', '2026-08-17 00:03:32.362530', 0, '2026-08-16 23:59:16.962420', '2026-08-16 23:58:32.364532');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-16 23:48:49.163857');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-16 23:48:49.165858');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-16 23:48:49.166859');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-16 23:48:49.167853');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-16 23:48:49.168862');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-16 23:48:49.169845');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-16 23:48:49.170843');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-16 23:48:49.172846');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-16 23:48:49.174808');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-16 23:48:49.175801');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-16 23:48:49.176804');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-16 23:48:49.178805');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-16 23:48:49.179804');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-16 23:48:49.180803');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-16 23:48:49.181802');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-16 23:48:49.182802');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-16 23:48:49.183802');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-16 23:48:49.184802');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-16 23:48:49.185801');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-16 23:48:49.186802');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Daily', '2026-08-16 23:48:49.187801');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-16 23:48:49.188802');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$spGh7S32hoVFEL5z1nOQRe6WHyEfH/qyuP4W0bIeGDHHjd0NZ7qk6', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-16 23:59:16.982384', 0, NULL, '2026-08-16 23:48:49.564850', '2026-08-16 23:48:49.564850');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$ctgMFwgzX38tWNpNBCoZ7OYLdqyD.BLZ855sGe7BPxSnWHxnI55/q', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-16 23:48:50.041857', '2026-08-16 23:48:50.041857');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$CU/gvOFLWrtELyvHeBx9OueHGtjf5fpFS2TkYIF4IRKiayM8e.kuC', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-16 23:48:50.419983', '2026-08-16 23:48:50.419983');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$OHMnPCZ1FBLc5sgTiLsVuOyNvMV7B7EZVqU759IGazqQZ.rVLPi.i', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-16 23:48:50.810703', '2026-08-16 23:48:50.810703');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$fwqfZ8mnreATRZE8cNpkrOpy1ftxD6BASxRycFYx1QeuuGx5Io8oO', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, NULL, 0, NULL, '2026-08-16 23:48:51.163716', '2026-08-16 23:48:51.163716');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
