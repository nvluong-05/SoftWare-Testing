"""
Unit and Integration Tests for Translation Logic and UI Popup Parser
(translation.py & ui.py)
Covers: Prompt categorization, API response handling, Network retries,
UI string parsing, and Star button validation.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Enable headless Qt before importing PyQt6
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from translation import Translator
from ui import TranslationPopup


# Ensure a single QApplication instance exists for GUI tests
_app = QApplication.instance() or QApplication([])


class TestTranslationAndParser(unittest.TestCase):
    def setUp(self):
        self.translator = Translator()
        self.popup = TranslationPopup()

    def tearDown(self):
        self.popup.close()

    # ==========================================
    # TRANSLATION LOGIC TEST CASES
    # ==========================================

    def test_tc_tr_01_translate_empty_and_none(self):
        """TC_TR_01: translate_text returns None immediately on empty or None input."""
        self.assertIsNone(self.translator.translate_text(""))
        self.assertIsNone(self.translator.translate_text(None))

    @patch("translation.requests.post")
    def test_tc_tr_02_prompt_classification_short_text(self, mock_post):
        """TC_TR_02: Short text (<= 5 words) generates vocabulary/phonetics prompt."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Dịch: sách | Phiên âm: /bʊk/ | Ví dụ: A good book."}}]
        }
        mock_post.return_value = mock_response

        result = self.translator.translate_text("open book")
        self.assertIn("Dịch: sách", result)

        # Inspect prompt passed to requests.post
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        sent_prompt = payload["messages"][0]["content"]
        self.assertIn("Dịch từ/cụm từ sau sang tiếng Việt", sent_prompt)
        self.assertIn("Phiên âm: [phiên âm IPA]", sent_prompt)

    @patch("translation.requests.post")
    def test_tc_tr_03_prompt_classification_long_text(self, mock_post):
        """TC_TR_03: Long text (> 5 words) generates sentence translation prompt."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Kiểm thử phần mềm là một môn học quan trọng."}}]
        }
        mock_post.return_value = mock_response

        text = "Software testing is a very important course in computer science"
        result = self.translator.translate_text(text)
        self.assertEqual(result, "Kiểm thử phần mềm là một môn học quan trọng.")

        # Inspect prompt passed to requests.post
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        sent_prompt = payload["messages"][0]["content"]
        self.assertIn("Dịch câu sau sang tiếng Việt", sent_prompt)
        self.assertIn("Chỉ trả về bản dịch ngắn gọn, sát nghĩa", sent_prompt)

    @patch("translation.requests.post")
    def test_tc_tr_04_boundary_exact_5_words(self, mock_post):
        """TC_TR_04: Boundary: Exactly 5 words is classified as short text."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "dummy"}}]}
        mock_post.return_value = mock_response

        self.translator.translate_text("one two three four five")
        sent_prompt = mock_post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("Dịch từ/cụm từ sau sang tiếng Việt", sent_prompt)

    @patch("translation.requests.post")
    def test_tc_tr_05_boundary_exact_6_words(self, mock_post):
        """TC_TR_05: Boundary: Exactly 6 words is classified as sentence (long text)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "dummy"}}]}
        mock_post.return_value = mock_response

        self.translator.translate_text("one two three four five six")
        sent_prompt = mock_post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("Dịch câu sau sang tiếng Việt", sent_prompt)

    @patch("translation.requests.post")
    def test_tc_tr_06_api_error_response_handling(self, mock_post):
        """TC_TR_06: API error in JSON response returns formatted error string."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": {"message": "Invalid API key provided."}
        }
        mock_post.return_value = mock_response

        result = self.translator.translate_text("test")
        self.assertEqual(result, "Lỗi dịch thuật: Invalid API key provided.")

    @patch("translation.time.sleep", return_value=None)
    @patch("translation.requests.post")
    def test_tc_tr_07_network_exception_retry_and_failure(self, mock_post, mock_sleep):
        """TC_TR_07: Network exception retries 3 times then returns connection error."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        result = self.translator.translate_text("network test")
        self.assertEqual(mock_post.call_count, 3)
        self.assertIn("Lỗi kết nối: Network unreachable", result)

    # ==========================================
    # UI PARSER & INTERACTION TEST CASES
    # ==========================================

    def test_tc_ui_01_parse_standard_three_part_format(self):
        """TC_UI_01: Standard format parses meaning, phonetics, and example accurately."""
        input_text = "Dịch: máy tính, máy vi tính | Phiên âm: /kəmˈpjuː.tər/ | Ví dụ: I use a computer."
        self.popup._parse_and_display(input_text)

        self.assertEqual(self.popup.txt_translated.toPlainText(), "máy tính, máy vi tính")
        self.assertEqual(self.popup.lbl_phonetics.text(), "🔊 /kəmˈpjuː.tər/")
        self.assertFalse(self.popup.lbl_phonetics.isHidden())
        self.assertEqual(self.popup.lbl_example.text(), "I use a computer.")
        self.assertFalse(self.popup.lbl_example.isHidden())
        self.assertFalse(self.popup.lbl_example_title.isHidden())

    def test_tc_ui_02_parse_plain_sentence_format(self):
        """TC_UI_02: Plain sentence format displays directly and hides phonetics/example."""
        input_text = "Hệ thống kiểm thử tự động đang thực thi các ca kiểm thử."
        self.popup._parse_and_display(input_text)

        self.assertEqual(self.popup.txt_translated.toPlainText(), input_text)
        self.assertTrue(self.popup.lbl_phonetics.isHidden())
        self.assertTrue(self.popup.lbl_example.isHidden())
        self.assertTrue(self.popup.lbl_example_title.isHidden())

    def test_tc_ui_03_parse_partial_format_without_example(self):
        """TC_UI_03: Partial format (only translation and phonetics) handled gracefully."""
        input_text = "Dịch: xin chào | Phiên âm: /həˈləʊ/"
        self.popup._parse_and_display(input_text)

        self.assertEqual(self.popup.txt_translated.toPlainText(), "xin chào")
        self.assertEqual(self.popup.lbl_phonetics.text(), "🔊 /həˈləʊ/")
        self.assertFalse(self.popup.lbl_phonetics.isHidden())
        self.assertTrue(self.popup.lbl_example.isHidden())

    def test_tc_ui_04_star_button_empty_text_prevents_save(self):
        """TC_UI_04: Clicking star button when translation or original is empty does not emit save."""
        self.popup.txt_original.setText("")
        self.popup.txt_translated.setText("")

        emitted_signals = []
        self.popup.save_vocab_signal.connect(lambda orig, trans: emitted_signals.append((orig, trans)))

        self.popup.on_star_clicked()
        self.assertEqual(len(emitted_signals), 0, "Signal should NOT be emitted when fields are empty.")
        self.assertEqual(self.popup.btn_star.toolTip(), "Không thể lưu!")

    def test_tc_ui_05_star_button_valid_text_emits_save_signal(self):
        """TC_UI_05: Clicking star button with valid data emits save_vocab_signal properly."""
        self.popup.txt_original.setText("keyboard")
        self.popup.txt_translated.setText("bàn phím")
        self.popup.lbl_phonetics.setText("🔊 /ˈkiː.bɔːd/")
        self.popup.lbl_example.setText("mechanical keyboard")

        emitted_signals = []
        self.popup.save_vocab_signal.connect(lambda orig, trans: emitted_signals.append((orig, trans)))

        self.popup.on_star_clicked()
        self.assertEqual(len(emitted_signals), 1)
        orig, full_trans = emitted_signals[0]
        self.assertEqual(orig, "keyboard")
        self.assertIn("Dịch: bàn phím", full_trans)
        self.assertIn("Phiên âm: /ˈkiː.bɔːd/", full_trans)
        self.assertIn("Ví dụ: mechanical keyboard", full_trans)

        # The UI only marks the item as saved after storage confirms success.
        self.assertNotEqual(self.popup.btn_star.property("class"), "saved")
        self.popup.set_save_result(True)
        self.assertEqual(self.popup.btn_star.property("class"), "saved")
        self.assertEqual(self.popup.btn_star.toolTip(), "Đã lưu vào sổ tay ✓")


if __name__ == "__main__":
    unittest.main()
