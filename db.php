<?php
// Safe PHP timezone configuration
date_default_timezone_set('Asia/Manila');

require_once __DIR__ . '/config.php';

try {
    $pdo = new PDO($dsn, $db_user, $db_pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    // Execute timezone safely without killing the script if unsupported
    try {
        $pdo->exec("SET time_zone = '+08:00';");
    } catch (Exception $tzErr) {
        // Silently continue if MySQL server timezone tables are not loaded
    }

    // For PostgreSQL compatibility if connected via pgsql
    try {
        $pdo->exec("SET TIME ZONE 'Asia/Manila';");
    } catch (Exception $tzErr) {
        // Silently continue if unsupported
    }

} catch (PDOException $e) {
    http_response_code(500);
    header('Content-Type: application/json');
    echo json_encode([
        'error' => 'Database connection failed',
        'message' => $e->getMessage()
    ]);
    exit;
}
