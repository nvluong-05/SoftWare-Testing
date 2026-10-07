"""
Unit and Integration Tests for Notebook Database Management (utils.py & history.py)
Covers: Positive, Negative, Boundary, and Security/SQL Injection scenarios.
"""

import os
import sys
import tempfile
import unittest
import sqlite3

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils
import history


class TestNotebookDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_db_path = utils.DB_PATH

    @classmethod
    def tearDownClass(cls):
        utils.DB_PATH = cls.original_db_path

    def setUp(self):
        # Create a fresh temporary database file for each test
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.test_db_path = self.temp_file.name
        utils.DB_PATH = self.test_db_path
        utils.init_db()

    def tearDown(self):
        # Remove temporary database file after test
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    # ==========================================
    # POSITIVE TEST CASES
    # ==========================================

    def test_tc_db_01_init_db_creates_table(self):
        """TC_DB_01: Verify init_db properly creates 'data' table with expected schema."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data';")
        table = cursor.fetchone()
        self.assertIsNotNone(table, "Table 'data' should exist in the database.")
        self.assertEqual(table[0], "data")

        # Verify columns
        cursor.execute("PRAGMA table_info(data);")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ["id", "word", "definition", "phonetics", "tag", "timestamp"]
        for col in expected_columns:
            self.assertIn(col, columns, f"Column '{col}' should exist in table 'data'.")
        conn.close()

    def test_tc_db_02_add_valid_word_default_tag(self):
        """TC_DB_02: Adding a valid word with default tag saves successfully."""
        result = utils.add_to_notebook(
            word="computer",
            definition="máy vi tính",
            phonetics="/kəmˈpjuːtə/"
        )
        self.assertTrue(result, "add_to_notebook should return True on success.")

        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        row = vocab[0]
        self.assertEqual(row[1], "computer")
        self.assertEqual(row[2], "máy vi tính")
        self.assertEqual(row[3], "/kəmˈpjuːtə/")
        self.assertEqual(row[4], "General")  # Default tag

    def test_tc_db_03_add_word_custom_tag(self):
        """TC_DB_03: Adding a word with custom tag saves with specified tag."""
        result = utils.add_to_notebook(
            word="inheritance",
            definition="tính kế thừa",
            phonetics="/ɪnˈher.ɪ.təns/",
            tag="OOP"
        )
        self.assertTrue(result)
        vocab = history.fetch_vocab(tag="OOP")
        self.assertEqual(len(vocab), 1)
        self.assertEqual(vocab[0][1], "inheritance")
        self.assertEqual(vocab[0][4], "OOP")

    def test_tc_db_04_fetch_vocab_all_ordered_by_timestamp_desc(self):
        """TC_DB_04: Fetching all vocab returns records ordered by timestamp DESC."""
        import time
        utils.add_to_notebook("first", "thứ nhất")
        time.sleep(1.05)  # SQLite CURRENT_TIMESTAMP has 1-second resolution
        utils.add_to_notebook("second", "thứ hai")

        vocab = history.fetch_vocab(search="", tag="Tất cả")
        self.assertEqual(len(vocab), 2)
        words = [row[1] for row in vocab]
        self.assertEqual(words, ["second", "first"])

    def test_tc_db_05_fetch_vocab_search_by_word(self):
        """TC_DB_05: Search query matches word substring correctly."""
        utils.add_to_notebook("cat", "con mèo")
        utils.add_to_notebook("caterpillar", "con sâu bướm")
        utils.add_to_notebook("dog", "con chó")

        results = history.fetch_vocab(search="cat")
        self.assertEqual(len(results), 2)
        words = [row[1] for row in results]
        self.assertIn("cat", words)
        self.assertIn("caterpillar", words)
        self.assertNotIn("dog", words)

    def test_tc_db_06_fetch_vocab_search_by_definition(self):
        """TC_DB_06: Search query matches definition substring correctly."""
        utils.add_to_notebook("apple", "quả táo tây")
        utils.add_to_notebook("banana", "quả chuối tiêu")

        results = history.fetch_vocab(search="táo")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "apple")

    def test_tc_db_07_fetch_vocab_filter_by_tag(self):
        """TC_DB_07: Filtering by tag returns only records matching the exact tag."""
        utils.add_to_notebook("docker", "nền tảng container", tag="DevOps")
        utils.add_to_notebook("kubernetes", "hệ thống điều phối", tag="DevOps")
        utils.add_to_notebook("python", "ngôn ngữ lập trình", tag="Language")

        devops_vocab = history.fetch_vocab(tag="DevOps")
        self.assertEqual(len(devops_vocab), 2)
        for row in devops_vocab:
            self.assertEqual(row[4], "DevOps")

    def test_tc_db_08_fetch_vocab_combined_search_and_tag(self):
        """TC_DB_08: Query with both search term and tag filter applies AND logic."""
        utils.add_to_notebook("stack", "ngăn xếp", tag="DataStructure")
        utils.add_to_notebook("queue", "hàng đợi", tag="DataStructure")
        utils.add_to_notebook("stack overflow", "tràn ngăn xếp", tag="Error")

        results = history.fetch_vocab(search="stack", tag="DataStructure")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "stack")
        self.assertEqual(results[0][4], "DataStructure")

    def test_tc_db_09_fetch_tags_distinct_sorted(self):
        """TC_DB_09: fetch_tags returns unique tags sorted alphabetically."""
        utils.add_to_notebook("word1", "def1", tag="Zeta")
        utils.add_to_notebook("word2", "def2", tag="Alpha")
        utils.add_to_notebook("word3", "def3", tag="Alpha")
        utils.add_to_notebook("word4", "def4", tag="Beta")

        tags = history.fetch_tags()
        self.assertEqual(tags, ["Alpha", "Beta", "Zeta"])

    def test_tc_db_10_delete_vocab_success(self):
        """TC_DB_10: Deleting an existing word by ID removes it from database."""
        utils.add_to_notebook("to_delete", "sắp bị xóa")
        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        word_id = vocab[0][0]

        history.delete_vocab(word_id)
        vocab_after = history.fetch_vocab()
        self.assertEqual(len(vocab_after), 0)

    # ==========================================
    # NEGATIVE TEST CASES
    # ==========================================

    def test_tc_db_11_delete_non_existent_id(self):
        """TC_DB_11: Deleting a non-existent ID does not fail or affect other records."""
        utils.add_to_notebook("keep_me", "giữ lại")
        history.delete_vocab(999999)  # ID does not exist
        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        self.assertEqual(vocab[0][1], "keep_me")

    def test_tc_db_12_fetch_vocab_no_match(self):
        """TC_DB_12: Searching for non-existent keyword returns empty list."""
        utils.add_to_notebook("hello", "xin chào")
        results = history.fetch_vocab(search="non_existent_keyword_12345")
        self.assertEqual(results, [])

    def test_tc_db_13_fetch_vocab_non_existent_tag(self):
        """TC_DB_13: Filtering with a tag that does not exist returns empty list."""
        utils.add_to_notebook("hello", "xin chào", tag="General")
        results = history.fetch_vocab(tag="NonExistentTag")
        self.assertEqual(results, [])

    # ==========================================
    # BOUNDARY & EDGE TEST CASES
    # ==========================================

    def test_tc_db_14_add_word_empty_strings(self):
        """TC_DB_14: Boundary test: Empty string inputs are stored without crashing."""
        result = utils.add_to_notebook(word="", definition="", phonetics="", tag="")
        self.assertTrue(result)
        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        self.assertEqual(vocab[0][1], "")
        self.assertEqual(vocab[0][2], "")

    def test_tc_db_15_add_word_very_large_text(self):
        """TC_DB_15: Boundary test: Large text payload (10KB word, 50KB definition)."""
        large_word = "W" * 10000
        large_def = "D" * 50000
        result = utils.add_to_notebook(large_word, large_def)
        self.assertTrue(result)

        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        self.assertEqual(len(vocab[0][1]), 10000)
        self.assertEqual(len(vocab[0][2]), 50000)

    def test_tc_db_16_sql_injection_resilience(self):
        """TC_DB_16: Security/Boundary test: SQL injection payloads in search query."""
        utils.add_to_notebook("secret_token", "giá trị bí mật")

        # Try SQL injection in search parameter
        injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE data; --",
            "\" OR \"1\"=\"1",
            "1' UNION SELECT 1,2,3,4,5,6 --",
        ]
        for payload in injection_payloads:
            results = history.fetch_vocab(search=payload)
            # None of the injection payloads should match "secret_token"
            self.assertEqual(results, [], f"Payload '{payload}' bypassed query parameterization!")

        # Verify table still exists and data is intact
        vocab = history.fetch_vocab()
        self.assertEqual(len(vocab), 1)
        self.assertEqual(vocab[0][1], "secret_token")

    def test_tc_db_17_unicode_and_vietnamese_diacritics(self):
        """TC_DB_17: Boundary test: Full Vietnamese diacritics, emojis, and special chars."""
        word = "Đặc tả yêu cầu & Kiểm thử phần mềm 🎯"
        definition = "Phương pháp kiểm thử hộp đen, hộp trắng và kiểm thử tự động với ký tự: ~!@#$%^&*()_+"
        phonetics = "/ˈspe.sɪ.fɪ.keɪ.ʃən/"
        tag = "Tiếng Việt 🇻🇳"

        result = utils.add_to_notebook(word, definition, phonetics, tag)
        self.assertTrue(result)

        vocab = history.fetch_vocab(search="Kiểm thử")
        self.assertEqual(len(vocab), 1)
        self.assertEqual(vocab[0][1], word)
        self.assertEqual(vocab[0][2], definition)
        self.assertEqual(vocab[0][4], tag)


if __name__ == "__main__":
    unittest.main()
