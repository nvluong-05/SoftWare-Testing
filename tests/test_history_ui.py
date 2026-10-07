import unittest
from unittest.mock import Mock, patch

from PyQt6.QtWidgets import QMessageBox

from history import HistoryWindow
from tests.qt_support import get_app


class HistoryWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def make_window(self):
        with patch("history.HistoryWindow.load_data"):
            return HistoryWindow()

    @patch("history.fetch_vocab")
    def test_req07_render_empty_and_populated_table(self, fetch):
        window = self.make_window()
        self.addCleanup(window.close)
        fetch.return_value = []
        window._render_table()
        self.assertEqual(window.table.rowCount(), 0)
        self.assertEqual(window.lbl_count.text(), "0 từ")
        fetch.return_value = [(1, "book", "Dịch: sách | Ví dụ: Read.", "/bʊk/", "General", "2026")]
        window._render_table()
        self.assertEqual(window.table.rowCount(), 1)
        self.assertEqual(window.table.item(0, 2).text(), "sách")
        self.assertEqual(window.lbl_count.text(), "1 từ")

    @patch("history.fetch_vocab", return_value=[])
    def test_req08_render_passes_trimmed_search_and_tag(self, fetch):
        window = self.make_window()
        self.addCleanup(window.close)
        window.tag_filter.addItems(["Tất cả", "Study"])
        window.tag_filter.setCurrentText("Study")
        window.search_box.setText("  sách  ")
        window._render_table()
        fetch.assert_called_with("sách", "Study")

    @patch("history.delete_vocab")
    @patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes)
    def test_req10_confirm_delete_yes_deletes_and_refreshes(self, _exec, delete):
        window = self.make_window()
        self.addCleanup(window.close)
        window._render_table = Mock()
        window._confirm_delete(7, "book")
        delete.assert_called_once_with(7)
        window._render_table.assert_called_once()

    @patch("history.delete_vocab")
    @patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Cancel)
    def test_req10_cancel_delete_keeps_data(self, _exec, delete):
        window = self.make_window()
        self.addCleanup(window.close)
        window._render_table = Mock()
        window._confirm_delete(7, "book")
        delete.assert_not_called()
        window._render_table.assert_not_called()

    def test_req11_history_close_reopens_popup(self):
        popup = Mock()
        with patch("history.HistoryWindow.load_data"):
            window = HistoryWindow(popup=popup)
        self.addCleanup(window.close)
        event = Mock()
        window.closeEvent(event)
        popup.show.assert_called_once()
        popup.activateWindow.assert_called_once()
        event.accept.assert_called_once()


if __name__ == "__main__":
    unittest.main()
