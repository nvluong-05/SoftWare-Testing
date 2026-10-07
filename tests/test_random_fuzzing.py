"""
Random Testing / Fuzz Testing for AI Translate
Technique: Random Testing with fixed Seed (Reproducible)
Generates 100+ random test cases across:
1. Random Vocabulary Data (DB persistence & UTF-8 integrity)
2. Random Search Substring Queries (SQL query resilience)
3. Random Word Count Classification (Partitioning boundary verification)
4. Random Malformed Translation Strings (UI parser robustness/fuzzing)
"""

import os
import sys
import random
import string
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Enable headless Qt before importing PyQt6
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
import utils
import history
from translation import Translator
from ui import TranslationPopup

_app = QApplication.instance() or QApplication([])

# Character sets for random generation
VIETNAMESE_CHARS = "aáàảãạăắằẳẵặâấầẩẫậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđ"
EXTENDED_CHARS = string.ascii_letters + string.digits + " _-+=!@#$%^&*()[]{};:'\",.<>?/\\|~`" + VIETNAMESE_CHARS


def random_string(length: int, pool: str = EXTENDED_CHARS) -> str:
    return "".join(random.choice(pool) for _ in range(length))


class TestRandomFuzzing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_db_path = utils.DB_PATH
        # Set fixed random seed for reproducibility
        cls.seed_value = 42
        random.seed(cls.seed_value)

    @classmethod
    def tearDownClass(cls):
        utils.DB_PATH = cls.original_db_path

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_file.close()
        self.test_db_path = self.temp_file.name
        utils.DB_PATH = self.test_db_path
        utils.init_db()

        self.translator = Translator()
        self.popup = TranslationPopup()

    def tearDown(self):
        self.popup.close()
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                pass

    def test_random_01_database_random_vocabulary_insertion_and_integrity(self):
        """
        Random Test 1: Insert 30 completely random vocabulary entries with varied lengths,
        Vietnamese diacritics, and symbols, then verify database persistence.
        """
        num_samples = 30
        inserted_records = []
        tags_pool = ["General", "Tech", "Language", "Toiec_990", "RandomTag_#1", "Tiếng Việt 🇻🇳", ""]

        for i in range(num_samples):
            w_len = random.randint(3, 40)
            d_len = random.randint(5, 120)
            p_len = random.randint(0, 20)

            word = f"word_{i}_" + random_string(w_len)
            definition = f"def_{i}_" + random_string(d_len)
            phonetics = f"/{random_string(p_len)}/" if p_len > 0 else ""
            tag = random.choice(tags_pool)

            success = utils.add_to_notebook(word=word, definition=definition, phonetics=phonetics, tag=tag)
            self.assertTrue(success, f"Failed to insert random record #{i}: word='{word}'")
            inserted_records.append((word, definition, phonetics, tag))

        # Verify all records stored correctly
        all_vocab = history.fetch_vocab(search="", tag="Tất cả")
        self.assertEqual(len(all_vocab), num_samples, f"Expected {num_samples} records, found {len(all_vocab)}")

        # Verify data integrity of each stored record
        stored_dict = {row[1]: (row[2], row[3], row[4]) for row in all_vocab}
        for word, definition, phonetics, tag in inserted_records:
            self.assertIn(word, stored_dict, f"Word '{word}' was not found in database!")
            actual_def, actual_phon, actual_tag = stored_dict[word]
            self.assertEqual(actual_def, definition)
            self.assertEqual(actual_phon, phonetics)
            self.assertEqual(actual_tag, tag)

    def test_random_02_database_random_search_substrings(self):
        """
        Random Test 2: Perform 25 random substring searches from previously inserted words
        to verify SQL parameterization, substring LIKE search, and ensure no crashes occur.
        """
        num_samples = 25
        created_words = []

        # Populate database with distinct known words
        for i in range(num_samples):
            word = f"randomterm_{i:02d}_" + random_string(8, string.ascii_lowercase)
            definition = f"nghĩa ngẫu nhiên {i:02d} " + random_string(15, VIETNAMESE_CHARS)
            utils.add_to_notebook(word=word, definition=definition)
            created_words.append((word, definition))

        # Query random substrings
        for word, definition in created_words:
            # Pick a random 4-character substring from the word
            start_idx = random.randint(0, len(word) - 4)
            sub = word[start_idx:start_idx + 4]

            # Execute search
            results = history.fetch_vocab(search=sub)
            result_words = [r[1] for r in results]

            self.assertIn(word, result_words,
                          f"Search for substring '{sub}' did not return expected target word '{word}'!")

    @patch("translation.requests.post")
    def test_random_03_classification_word_count_fuzzing(self, mock_post):
        """
        Random Test 3: Generate 30 random sentences of lengths 1 to 20 words.
        Verify that Translator strictly partitions short text (<= 5 words) vs long text (> 5 words).
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "dịch ngẫu nhiên"}}]}
        mock_post.return_value = mock_response

        num_samples = 30
        for _ in range(num_samples):
            word_count = random.randint(1, 20)
            words = [random_string(random.randint(2, 8), string.ascii_lowercase) for _ in range(word_count)]
            text = " ".join(words)

            self.translator.translate_text(text)
            sent_prompt = mock_post.call_args.kwargs["json"]["messages"][0]["content"]

            if word_count <= 5:
                self.assertIn("Dịch từ/cụm từ sau sang tiếng Việt", sent_prompt,
                              f"Expected short-text prompt for word count {word_count}: '{text}'")
                self.assertIn("Phiên âm: [phiên âm IPA]", sent_prompt)
            else:
                self.assertIn("Dịch câu sau sang tiếng Việt", sent_prompt,
                              f"Expected long-sentence prompt for word count {word_count}: '{text}'")
                self.assertIn("Chỉ trả về bản dịch ngắn gọn, sát nghĩa", sent_prompt)

    def test_random_04_ui_parser_fuzzing_robustness(self):
        """
        Random Test 4: Feed 30 randomized, malformed, or unusual strings to _parse_and_display
        to ensure the parser is robust and never throws unhandled exceptions.
        """
        fuzz_patterns = [
            # Missing parts
            "Dịch: chỉ có dịch không có phiên âm hay ví dụ",
            "Phiên âm: /hæv/ | Ví dụ: I have a pen",
            "|||||||||",
            "Dịch: || Phiên âm: || Ví dụ:",
            "Dịch: abc | Phiên âm: def | Ví dụ: ghi | Thêm: thừa | Thừa: nữa",
            "",
            "   \t\n   ",
            "Dịch: " + random_string(500),
            "| Dịch: ngược |",
            "::::",
            "Dịch: 1 | Dịch: 2 | Dịch: 3",
        ]

        # Add 20 randomly synthesized noisy strings
        for _ in range(20):
            pieces = []
            if random.random() > 0.5:
                pieces.append(f"Dịch: {random_string(random.randint(5, 30))}")
            if random.random() > 0.5:
                pieces.append(f"Phiên âm: /{random_string(random.randint(3, 15))}/")
            if random.random() > 0.5:
                pieces.append(f"Ví dụ: {random_string(random.randint(10, 50))}")
            # Insert random delimiters and junk
            junk = random.choice([" | ", " || ", " |?| ", " ; "])
            fuzz_str = junk.join(pieces)
            fuzz_patterns.append(fuzz_str)

        for idx, pattern in enumerate(fuzz_patterns):
            try:
                self.popup._parse_and_display(pattern)
            except Exception as e:
                self.fail(f"Parser crashed on fuzzed input #{idx}: '{pattern}'. Error: {e}")


if __name__ == "__main__":
    unittest.main()
