-- BlotterCast database backup
-- Generated: 2026-08-18 23:07:19 UTC
-- Engine: sqlite

-- Table: audit_logs
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (1, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:14.629577');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (2, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:14.641010');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (3, 'admin', 'Created', 'Census', 'New resident recorded: Maria Dela Cruz', '2026-08-18 23:07:14.653656');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (4, 'admin', 'Logout', 'System', 'User logged out', '2026-08-18 23:07:14.665307');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (5, 'pencoder', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:14.980072');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (6, 'pencoder', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:14.986965');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (7, 'pencoder', 'Created', 'Census', 'New resident recorded: Ana Reyes', '2026-08-18 23:07:14.995274');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (8, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:16.103947');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (9, 'msantos', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:16.118177');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (10, 'msantos', 'Updated', 'System', 'Password changed', '2026-08-18 23:07:17.360911');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (11, 'msantos', 'Logout', 'System', 'User logged out', '2026-08-18 23:07:17.363603');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (12, 'msantos', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:17.989270');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (13, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:18.303049');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (14, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:18.311962');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (15, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:18.628647');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (16, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:18.635460');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (17, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 23:07:18.644885');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (18, 'admin', 'Updated', 'Users', 'Signature uploaded for kapitan', '2026-08-18 23:07:18.652527');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (19, 'admin', 'Updated', 'Users', 'Signature removed for kapitan', '2026-08-18 23:07:18.703485');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (20, 'admin', 'Logout', 'System', 'User logged out', '2026-08-18 23:07:18.707107');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (21, 'admin', 'Login', 'System', 'Password verified, MFA code sent', '2026-08-18 23:07:19.019887');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (22, 'admin', 'Login', 'System', 'Successful login (MFA verified)', '2026-08-18 23:07:19.026240');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (23, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-230719.sql', '2026-08-18 23:07:19.039295');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (24, 'system (automatic)', 'Exported', 'Backup', 'Database backup created: blottercast-backup-20260818-230719.sql', '2026-08-18 23:07:19.050920');
INSERT INTO "audit_logs" ("id", "username", "action", "module", "details", "created_at") VALUES (25, 'admin', 'Updated', 'Settings', 'System settings saved', '2026-08-18 23:07:19.056184');

-- Table: backups
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (1, 'blottercast-backup-20260818-230719.sql', 14537, 'Success', 'system (automatic)', '2026-08-17 22:07:19.044089');
INSERT INTO "backups" ("id", "file_name", "size_bytes", "status", "created_by", "created_at") VALUES (2, 'blottercast-backup-20260818-230719.sql', 14998, 'Success', 'system (automatic)', '2026-08-18 10:07:19.058226');

-- Table: barangay_clearance

-- Table: barangay_non_residency

-- Table: barangay_residency

-- Table: blotter_records

-- Table: census_records
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (1, 'RES-0001', 'Dela Cruz', 'Maria', '', '1985-03-10', 'Female', 'Single', 'Filipino', NULL, '45 Mabini St', 'HH-09', '', 'Not Registered', '', 'Active', '2026-08-18 23:07:14.652162', '2026-08-18 23:07:14.652166');
INSERT INTO "census_records" ("id", "resident_no", "last_name", "first_name", "middle_name", "date_of_birth", "sex", "civil_status", "nationality", "zone_id", "address", "household_no", "contact_no", "voter_status", "occupation", "status", "created_at", "updated_at") VALUES (2, 'RES-0002', 'Reyes', 'Ana', '', '2000-01-01', 'Female', 'Single', 'Filipino', NULL, '', '', '', 'Not Registered', '', 'Active', '2026-08-18 23:07:14.993830', '2026-08-18 23:07:14.993834');

-- Table: generated_reports

-- Table: incidents

-- Table: indigency_certificates

-- Table: ml_runs

-- Table: notification_reads

-- Table: notifications

-- Table: otp_codes
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (1, 1, '1a2757dbc2b6869c470983768b063ba7ad858205ba325fb62ef1543b4eaf2338', 'login', '2026-08-18 23:12:14.623381', 0, '2026-08-18 23:07:14.636630', '2026-08-18 23:07:14.624524');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (2, 5, '1c69aa458c619d772e47e3803b2d334447b27ff24ceb243c6ec8d577b2106dc2', 'login', '2026-08-18 23:12:14.977283', 0, '2026-08-18 23:07:14.984159', '2026-08-18 23:07:14.977522');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (3, 4, '320a08cd96e1f7f3821f0e6b8c569071df384d14418e066a17769058a728d24c', 'login', '2026-08-18 23:12:16.098481', 0, '2026-08-18 23:07:16.113128', '2026-08-18 23:07:16.099704');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (4, 4, '5ce7ba66d84ad75a9fb6f088893e0286d249f1073bf91e2e3959ded0c8a2bd0c', 'login', '2026-08-18 23:12:17.986916', 0, NULL, '2026-08-18 23:07:17.987153');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (5, 1, '8f2e7ee8de4dae851bf3170c65318b808de3fbfc3348dc8ad95729440cfbd7f8', 'login', '2026-08-18 23:12:18.300398', 0, '2026-08-18 23:07:18.306870', '2026-08-18 23:07:18.300621');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (6, 1, '03b134b8ba0867d7069cb0a0128ece2439c83e4693353267b8c6c8decb273ca9', 'login', '2026-08-18 23:12:18.625368', 0, '2026-08-18 23:07:18.632619', '2026-08-18 23:07:18.625592');
INSERT INTO "otp_codes" ("id", "user_id", "code_hash", "purpose", "expires_at", "attempts", "consumed_at", "created_at") VALUES (7, 1, 'fe61f666c2f60236cc3f8c943c012ef2060ff410e8aca592b7af3c0b6636a861', 'login', '2026-08-18 23:12:19.017247', 0, '2026-08-18 23:07:19.023631', '2026-08-18 23:07:19.017470');

-- Table: settlements

-- Table: system_settings
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('barangay_name', 'Barangay Mapulang Lupa', '2026-08-18 23:07:11.985423');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('municipality', 'Pandi, Bulacan', '2026-08-18 23:07:11.986242');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('region', 'Region III – Central Luzon', '2026-08-18 23:07:11.986902');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('captain_name', 'Kapitan Jose Reyes', '2026-08-18 23:07:11.987379');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('contact_no', '0917-000-0000', '2026-08-18 23:07:11.987842');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('email', 'mapulanglupa@pandi.gov.ph', '2026-08-18 23:07:11.988297');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('date_format', 'MM/DD/YYYY', '2026-08-18 23:07:11.988800');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('time_format', '12-Hour (AM/PM)', '2026-08-18 23:07:11.989242');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('records_per_page', '6', '2026-08-18 23:07:11.989694');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('default_language', 'English', '2026-08-18 23:07:11.990167');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('risk_threshold', '75', '2026-08-18 23:07:11.990637');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('spike_threshold', '5', '2026-08-18 23:07:11.991092');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_inapp', '1', '2026-08-18 23:07:11.991516');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('notif_retrain', '1', '2026-08-18 23:07:11.992040');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('lockout_enabled', '1', '2026-08-18 23:07:11.992583');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('session_timeout', '30', '2026-08-18 23:07:11.993083');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('max_failed_logins', '5', '2026-08-18 23:07:11.993617');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('min_password_length', '8', '2026-08-18 23:07:11.994146');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('password_expiry_days', '90', '2026-08-18 23:07:11.994698');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('audit_trail', '1', '2026-08-18 23:07:11.995181');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_frequency', 'Every 12 hours', '2026-08-18 23:07:19.054867');
INSERT INTO "system_settings" ("setting_key", "setting_value", "updated_at") VALUES ('backup_time', '02:00', '2026-08-18 23:07:11.996302');

-- Table: users
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (1, 'admin', '$2b$12$D4B9L3parmPd9a5l6HVESeftDpKX/xp6/iW.l03mdOR8kGhQgaTJ.', 'System Administrator', 'fileyourname@gmail.com', NULL, 'System Admin', 'Active', NULL, '2026-08-18 23:07:19.024406', 0, NULL, '2026-08-18 23:07:12.309258', '2026-08-18 23:07:12.309264');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (2, 'kapitan', '$2b$12$OydTSHNEvUKu7XpvEhAsOuPPkSG2U7ad76Xp8UTMC45j.pDkcALQm', 'Barangay Captain', 'kapitan@blottercast.local', NULL, 'Barangay Captain', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:07:12.629079', '2026-08-18 23:07:12.629086');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (3, 'jdelacuz', '$2b$12$.CKnOr2RIBekVO80xrmaruGJ54FZp.UJEPf3.o8AEoMmnYaM33mRq', 'J. Dela Cruz', 'jdelacuz@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, NULL, 0, NULL, '2026-08-18 23:07:12.939433', '2026-08-18 23:07:12.939439');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (4, 'msantos', '$2b$12$dsgqOWAExFBaS.EuOYOu4ej93IEGfK43aEWjt6NGZNkfJX85LzMXS', 'M. Santos', 'msantos@blottercast.local', NULL, 'Desk Officer', 'Active', NULL, '2026-08-18 23:07:16.114874', 0, NULL, '2026-08-18 23:07:17.357395', '2026-08-18 23:07:13.250547');
INSERT INTO "users" ("id", "username", "password", "full_name", "email", "contact_no", "role", "status", "signature_path", "last_login", "failed_attempts", "locked_until", "password_changed_at", "created_at") VALUES (5, 'pencoder', '$2b$12$vB0EXmrgnYclQmMve/6i7usE8NXRidG8Hs584123j4HwsXihk/Ohi', 'P. Encoder', 'pencoder@blottercast.local', NULL, 'Data Encoder', 'Active', NULL, '2026-08-18 23:07:14.984942', 0, NULL, '2026-08-18 23:07:13.560724', '2026-08-18 23:07:13.560730');

-- Table: zones
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 1', 'Zone 1 – Barangay Hall Area', 14.8836, 120.9655, 0.2);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 2', 'Zone 2 – South Central', 14.8824, 120.9648, 0.11);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 3', 'Zone 3 – Market Area', 14.8845, 120.9663, 0.18);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 4', 'Zone 4 – Southeast Residential', 14.8818, 120.966, 0.06);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 5', 'Zone 5 – Northern Cluster', 14.8852, 120.965, 0.1);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 6', 'Zone 6 – West Interior', 14.883, 120.9636, 0.05);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 7', 'Zone 7 – Basketball Court Area', 14.8842, 120.9641, 0.16);
INSERT INTO "zones" ("zone_id", "label", "lat", "lng", "weight") VALUES ('Zone 8', 'Zone 8 – East Road Junction', 14.8826, 120.967, 0.14);
