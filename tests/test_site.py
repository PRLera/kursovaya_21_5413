"""Тесты запросов без JavaScript с использованием тестового клиента Flask."""
import unittest
from app import app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def send(self, action, **data):
        return self.client.post("/", data={"action": action, **data}, follow_redirects=True)

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Визуализация связных списков".encode(), response.data)

    def test_insert_middle(self):
        self.send("add_at", value="77", index="1")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["values"], [10, 77, 20, 30])

    def test_remove_first(self):
        self.send("remove_front")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["values"], [20, 30])

    def test_circular_cursor_wrap(self):
        self.send("previous")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["cursor"], 2)

    def test_rotate(self):
        self.send("rotate", steps="1")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["values"], [20, 30, 10])

    def test_change_type_preserves_values(self):
        self.send("choose_type", kind="singly")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["kind"], "singly")
            self.assertEqual(sess["values"], [10, 20, 30])

    def test_reject_invalid_index(self):
        response = self.send("remove_at", index="99")
        self.assertIn("Индекс вне диапазона".encode(), response.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("values", sess)  # Ошибка не сохраняет изменения.

    def test_empty_list(self):
        self.send("clear")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["values"], [])
            self.assertIsNone(sess["cursor"])


if __name__ == "__main__":
    unittest.main()
