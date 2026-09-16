<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../db.php';

$action = $_GET['action'] ?? $_POST['action'] ?? 'list';
$action = strtolower(trim($action));

if ($action === 'health' || $action === 'ping') {
    echo json_encode(['ok' => true, 'status' => 'healthy']);
    exit;
}

try {
    $stmt = $pdo->query("SELECT id, username, full_name, email, contact_no, role, status, last_seen, created_at FROM users ORDER BY id ASC");
    $users = $stmt->fetchAll();
    echo json_encode($users);
} catch (PDOException $e) {
    // If users table is empty or error occurs, return empty list or json error
    http_response_code(200);
    echo json_encode([]);
}
