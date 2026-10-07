import unittest
from unittest.mock import Mock, patch

from PyQt6.QtCore import QPoint

from tests.qt_support import get_app
from ui import TranslationPopup


class TranslationPopupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.popup = TranslationPopup()

    def tearDown(self):
        self.popup.close()

    def test_req04_parse_complete_structured_translation(self):
        self.popup._parse_and_display("Dịch: bền bỉ | Phiên âm: /pəˈsɪstəns/ | Ví dụ: Keep trying.")
        self.assertEqual(self.popup.txt_translated.toPlainText(), "bền bỉ")
        self.assertEqual(self.popup.lbl_phonetics.text(), "🔊 /pəˈsɪstəns/")
        self.assertEqual(self.popup.lbl_example.text(), "Keep trying.")
        self.assertTrue(self.popup.lbl_phonetics.isVisibleTo(self.popup))

    def test_req04_parse_structured_translation_with_missing_parts(self):
        self.popup._parse_and_display("Dịch: sách | Phiên âm:  | Ví dụ: ")
        self.assertEqual(self.popup.txt_translated.toPlainText(), "sách")
        self.assertFalse(self.popup.lbl_phonetics.isVisible())
        self.assertFalse(self.popup.lbl_example.isVisible())

    def test_req04_plain_translation_clears_stale_metadata_regression(self):
        self.popup._parse_and_display("Dịch: sách | Phiên âm: /bʊk/ | Ví dụ: Read a book.")
        self.popup._parse_and_display("Đây là một câu dịch thông thường.")
        self.assertEqual(self.popup.lbl_phonetics.text(), "")
        self.assertEqual(self.popup.lbl_example.text(), "")
        self.popup.txt_original.setText("a long sentence")
        captured = []
        self.popup.save_vocab_signal.connect(lambda original, translated: captured.append((original, translated)))
        self.popup.on_star_clicked()
        self.assertEqual(captured, [("a long sentence", "Dịch: Đây là một câu dịch thông thường.")])

    def test_req05_star_rejects_missing_original_or_translation(self):
        emitted = Mock()
        self.popup.save_vocab_signal.connect(emitted)
        for original, translated in (("", "dịch"), ("word", "")):
            with self.subTest(original=original, translated=translated):
                self.popup.txt_original.setText(original)
                self.popup.txt_translated.setText(translated)
                self.popup.on_star_clicked()
                self.assertEqual(self.popup.btn_star.toolTip(), "Không thể lưu!")
        emitted.assert_not_called()

    def test_req05_star_waits_for_storage_result_regression(self):
        captured = []
        self.popup.txt_original.setText("book")
        self.popup._parse_and_display("Dịch: sách | Phiên âm: /bʊk/ | Ví dụ: Read a book.")
        self.popup.save_vocab_signal.connect(lambda original, translated: captured.append((original, translated)))
        self.popup.on_star_clicked()
        self.assertFalse(self.popup.btn_star.isEnabled())
        self.assertEqual(self.popup.btn_star.toolTip(), "Đang lưu...")
        self.assertEqual(captured, [("book", "Dịch: sách | Phiên âm: /bʊk/ | Ví dụ: Read a book.")])

    def test_req05_set_save_result_success_and_failure(self):
        self.popup.btn_star.setEnabled(False)
        self.popup.set_save_result(True)
        self.assertTrue(self.popup.btn_star.isEnabled())
        self.assertIn("Đã lưu", self.popup.btn_star.toolTip())
        with patch("ui.QTimer.singleShot") as timer:
            self.popup.set_save_result(False)
        self.assertEqual(self.popup.btn_star.toolTip(), "Lưu thất bại!")
        timer.assert_called_once()

    @patch("ui.QApplication.primaryScreen")
    def test_req04_show_translation_repositions_inside_screen(self, primary_screen):
        screen = Mock()
        screen.geometry.return_value.width.return_value = 800
        primary_screen.return_value = screen
        with patch.object(self.popup, "show"), patch.object(self.popup, "activateWindow"):
            self.popup.show_translation_at("word", "dịch", 790, 5)
        self.assertLess(self.popup.pos().x(), 790)
        self.assertGreaterEqual(self.popup.pos().y(), 0)

    def test_req11_wheel_moves_popup_up_and_down(self):
        self.popup.move(100, 100)
        up = Mock()
        up.angleDelta.return_value = QPoint(0, 120)
        self.popup.wheelEvent(up)
        self.assertEqual(self.popup.pos().y(), 40)
        down = Mock()
        down.angleDelta.return_value = QPoint(0, -120)
        self.popup.wheelEvent(down)
        self.assertEqual(self.popup.pos().y(), 100)


if __name__ == "__main__":
    unittest.main()
