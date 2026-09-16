<?php
// Safe PHP timezone configuration
date_default_timezone_set('Asia/Manila');

// Database configuration defaults with environment variable overrides
$db_host = getenv('DB_HOST') ?: '127.0.0.1';
$db_port = getenv('DB_PORT') ?: '3306';
$db_name = getenv('DB_NAME') ?: 'blottercast';
$db_user = getenv('DB_USER') ?: 'root';
$db_pass = getenv('DB_PASS') ?: '';
$database_url = getenv('DATABASE_URL');

if ($database_url) {
    $dbparts = parse_url($database_url);
    if (!empty($dbparts['scheme'])) {
        $scheme = strtolower($dbparts['scheme']);
        if ($scheme === 'postgres' || $scheme === 'postgresql') {
            $driver = 'pgsql';
            $port = $dbparts['port'] ?? 5432;
        } else {
            $driver = 'mysql';
            $port = $dbparts['port'] ?? 3306;
        }
        $host = $dbparts['host'] ?? '127.0.0.1';
        $user = $dbparts['user'] ?? '';
        $pass = $dbparts['pass'] ?? '';
        $dbname = ltrim($dbparts['path'] ?? '', '/');
        $dsn = "{$driver}:host={$host};port={$port};dbname={$dbname}";
        $db_user = $user;
        $db_pass = $pass;
    } else {
        $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
    }
} else {
    $dsn = "mysql:host={$db_host};port={$db_port};dbname={$db_name};charset=utf8mb4";
}
