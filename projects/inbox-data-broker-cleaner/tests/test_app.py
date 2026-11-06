import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as inbox_app


class InboxCleanerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        inbox_app.app.config.update(TESTING=True, DATABASE=str(Path(self.temp.name) / "test.sqlite3"))
        inbox_app.GMAIL_CREDENTIALS = None
        inbox_app.init_db()
        self.client = inbox_app.app.test_client()

    def tearDown(self):
        inbox_app.GMAIL_CREDENTIALS = None
        self.temp.cleanup()

    def token(self):
        self.client.get("/")
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def test_home_page_loads_without_connecting_mail(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No inbox data saved", response.data)

    def test_headers_aggregate_sender_and_do_not_store_subject_or_unsubscribe_url(self):
        rows = inbox_app.normalize_sender_rows([
            {"From": "News Team <updates@example.com>", "List-Unsubscribe": "<https://example.invalid/private-token>"},
            {"From": "News Team <updates@example.com>", "List-Unsubscribe": ""},
        ], "Gmail", "me@example.com")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["message_count"], 2)
        self.assertTrue(rows[0]["has_unsubscribe"])
        self.assertNotIn("subject", rows[0])
        self.assertNotIn("unsubscribe_url", rows[0])

    def test_icloud_password_is_not_saved(self):
        with patch.object(inbox_app, "scan_icloud_headers", return_value=[]):
            response = self.client.post("/connect/icloud", data={
                "csrf_token": self.token(), "mailbox": "me@icloud.com", "app_password": "private-example",
            }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with inbox_app.database() as connection:
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(senders)")}
        self.assertNotIn("app_password", columns)
        self.assertNotIn(b"private-example", response.data)

    def test_post_without_csrf_token_is_rejected(self):
        self.assertEqual(self.client.post("/clear").status_code, 400)


if __name__ == "__main__":
    unittest.main()

