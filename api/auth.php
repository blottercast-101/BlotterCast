<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../db.php';

$action = $_GET['action'] ?? $_POST['action'] ?? '';
$action = strtolower(trim($action));

if ($action === 'heartbeat') {
    echo json_encode(['ok' => true, 'online' => false]);
    exit;
}

if ($action === 'auth_config') {
    echo json_encode(['ok' => true, 'google_auth_enabled' => false]);
    exit;
}

echo json_encode(['ok' => true]);
