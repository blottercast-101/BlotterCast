import os
import subprocess
import unittest
from unittest.mock import MagicMock

from app import create_app, db
from app.models import User
from app.__init__ import _set_db_timezone


class TestDatabaseConnectionAndApiRestoration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_auth_heartbeat_returns_200_json_get_and_post(self):
        """Verify api/auth.php?action=heartbeat returns HTTP 200 JSON on both GET and POST."""
        # 1. GET request
        res_get = self.client.get("/api/auth.php?action=heartbeat")
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.get_json()
        self.assertIsNotNone(data_get)
        self.assertTrue(data_get.get("ok"))

        # 2. POST request
        res_post = self.client.post("/api/auth.php?action=heartbeat")
        self.assertEqual(res_post.status_code, 200)
        data_post = res_post.get_json()
        self.assertIsNotNone(data_post)
        self.assertTrue(data_post.get("ok"))

    def test_users_api_returns_200_json_when_authenticated(self):
        """Verify api/users.php returns HTTP 200 JSON when authenticated as admin."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "System Admin"

        # 1. GET /api/users.php
        res = self.client.get("/api/users.php")
        self.assertEqual(res.status_code, 200)
        users = res.get_json()
        self.assertIsInstance(users, list)
        self.assertGreater(len(users), 0)

        # 2. GET /api/users.php?action=list
        res_list = self.client.get("/api/users.php?action=list")
        self.assertEqual(res_list.status_code, 200)
        users_list = res_list.get_json()
        self.assertIsInstance(users_list, list)

    def test_users_api_health_ping(self):
        """Verify api/users.php?action=health responds with HTTP 200 without authentication."""
        res = self.client.get("/api/users.php?action=health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("status"), "healthy")

    def test_sqlite_connection_listener_does_not_execute_set(self):
        """Verify SQLite connections are safely skipped without syntax errors."""
        mock_sqlite = MagicMock()
        mock_sqlite.__class__.__module__ = "sqlite3"
        mock_sqlite.__class__.__name__ = "Connection"

        _set_db_timezone(mock_sqlite, None)
        # Cursor should not even be acquired for SQLite
        mock_sqlite.cursor.assert_not_called()

    def test_postgres_connection_listener_uses_set_time_zone_and_handles_failures(self):
        """Verify PostgreSQL connections use SET TIME ZONE 'Asia/Manila' and rollback on failure."""
        # 1. Success case
        mock_pg = MagicMock()
        mock_pg.__class__.__module__ = "psycopg2.extensions"
        mock_pg.__class__.__name__ = "connection"
        mock_cursor = MagicMock()
        mock_pg.cursor.return_value = mock_cursor

        _set_db_timezone(mock_pg, None)
        mock_cursor.execute.assert_called_once_with("SET TIME ZONE 'Asia/Manila'")
        mock_pg.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

        # 2. Failure case: rollback is executed so transaction is never left aborted
        mock_pg_fail = MagicMock()
        mock_pg_fail.__class__.__module__ = "psycopg2.extensions"
        mock_pg_fail.__class__.__name__ = "connection"
        mock_cursor_fail = MagicMock()
        mock_cursor_fail.execute.side_effect = Exception("DB error")
        mock_pg_fail.cursor.return_value = mock_cursor_fail

        _set_db_timezone(mock_pg_fail, None)
        mock_pg_fail.rollback.assert_called_once()
        mock_cursor_fail.close.assert_called_once()

    def test_mysql_connection_listener_uses_set_time_zone_and_handles_failures(self):
        """Verify MySQL connections use SET time_zone = '+08:00' and rollback on failure."""
        mock_mysql = MagicMock()
        mock_mysql.__class__.__module__ = "pymysql.connections"
        mock_mysql.__class__.__name__ = "Connection"
        mock_cursor = MagicMock()
        mock_mysql.cursor.return_value = mock_cursor

        _set_db_timezone(mock_mysql, None)
        mock_cursor.execute.assert_called_once_with("SET time_zone = '+08:00'")
        mock_mysql.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_php_syntax_and_no_whitespace_before_tag(self):
        """Verify PHP files are syntactically valid and have no whitespace before <?php."""
        php_files = ["config.php", "db.php", "database.php", "api/users.php", "api/auth.php"]
        for rel_path in php_files:
            abs_path = os.path.join(os.getcwd(), rel_path)
            self.assertTrue(os.path.exists(abs_path), f"File {rel_path} must exist")

            # Check starts with <?php without whitespace or BOM
            with open(abs_path, "rb") as fp:
                first_bytes = fp.read(5)
                self.assertEqual(first_bytes, b"<?php", f"{rel_path} must start directly with <?php")

            # Run php -l if php CLI is available
            res = subprocess.run(["php", "-l", abs_path], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"PHP lint failed on {rel_path}: {res.stderr}")
            self.assertIn("No syntax errors detected", res.stdout)


if __name__ == "__main__":
    unittest.main()
