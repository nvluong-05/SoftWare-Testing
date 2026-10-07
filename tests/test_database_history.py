import os
import unittest
import uuid
from unittest.mock import patch

import history
import utils
from tests.qt_support import get_app


class DatabaseHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        temp_root = os.path.join(os.getcwd(), "reports")
        os.makedirs(temp_root, exist_ok=True)
        self.db_path = os.path.join(temp_root, f"test-{uuid.uuid4().hex}.db")
        self.db_patch = patch.object(utils, "DB_PATH", self.db_path)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def add_samples(self):
        self.assertTrue(utils.add_to_notebook("hello", "Dịch: xin chào", "həˈləʊ", "General"))
        self.assertTrue(utils.add_to_notebook("don't", "Dịch: đừng", "", "Grammar"))
        self.assertTrue(utils.add_to_notebook("100%", "Dịch: toàn bộ", "", "General"))

    def test_req06_init_db_creates_parent_and_schema_idempotently(self):
        utils.init_db()
        utils.init_db()
        self.assertTrue(os.path.isfile(self.db_path))
        self.assertEqual(history.fetch_vocab(), [])

    def test_req05_add_to_notebook_success_and_defaults(self):
        self.assertTrue(utils.add_to_notebook("book", "Dịch: sách"))
        row = history.fetch_vocab()[0]
        self.assertEqual(row[1:5], ("book", "Dịch: sách", "", "General"))

    @patch("utils.sqlite3.connect", side_effect=OSError("disk full"))
    def test_req05_add_to_notebook_database_error_returns_false(self, _connect):
        self.assertFalse(utils.add_to_notebook("book", "sách"))

    def test_req07_empty_and_populated_notebook(self):
        self.assertEqual(history.fetch_vocab(), [])
        self.add_samples()
        self.assertEqual(len(history.fetch_vocab()), 3)

    def test_req08_search_word_meaning_vietnamese_and_apostrophe(self):
        self.add_samples()
        self.assertEqual([r[1] for r in history.fetch_vocab("hello")], ["hello"])
        self.assertEqual([r[1] for r in history.fetch_vocab("đừng")], ["don't"])
        self.assertEqual([r[1] for r in history.fetch_vocab("don't")], ["don't"])
        self.assertEqual(history.fetch_vocab("không tồn tại"), [])

    def test_req08_percent_and_underscore_are_literal_search_text(self):
        self.add_samples()
        self.assertEqual([r[1] for r in history.fetch_vocab("%")], ["100%"])
        self.assertEqual(history.fetch_vocab("_"), [])

    def test_req09_fetch_tags_and_filter_combinations(self):
        self.add_samples()
        self.assertEqual(history.fetch_tags(), ["General", "Grammar"])
        self.assertEqual(len(history.fetch_vocab(tag="Tất cả")), 3)
        self.assertEqual([r[1] for r in history.fetch_vocab(tag="Grammar")], ["don't"])
        self.assertEqual([r[1] for r in history.fetch_vocab("đừng", "Grammar")], ["don't"])
        self.assertEqual(history.fetch_vocab("hello", "Grammar"), [])

    def test_req10_integration_save_read_search_delete(self):
        self.assertTrue(utils.add_to_notebook("persistence", "Dịch: sự kiên trì", "pəˈsɪstəns", "Study"))
        saved = history.fetch_vocab("kiên trì", "Study")
        self.assertEqual(len(saved), 1)
        history.delete_vocab(saved[0][0])
        self.assertEqual(history.fetch_vocab(), [])


if __name__ == "__main__":
    unittest.main()
