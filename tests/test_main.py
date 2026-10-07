import unittest
from unittest.mock import Mock, call, patch

from PyQt6.QtWidgets import QMessageBox, QSystemTrayIcon

from main import AppController, HotkeyBridge
from tests.qt_support import get_app


class HotkeyBridgeTests(unittest.TestCase):
    @patch("main.time.sleep")
    @patch("main.pyperclip")
    @patch("main.keyboard.press_and_release")
    @patch("main.pyautogui.position", return_value=(120, 240))
    def test_req01_hotkey_copies_strips_and_emits(self, _position, press, clipboard, sleep):
        clipboard.paste.return_value = "  selected text  "
        bridge = HotkeyBridge()
        emitted = []
        bridge.translate_triggered.connect(lambda text, x, y: emitted.append((text, x, y)))
        bridge._on_hotkey()
        clipboard.copy.assert_called_once_with("")
        press.assert_called_once_with("ctrl+c")
        sleep.assert_called_once_with(0.5)
        self.assertEqual(emitted, [("selected text", 120, 240)])

    @patch("main.time.sleep")
    @patch("main.pyperclip")
    @patch("main.keyboard.press_and_release")
    @patch("main.pyautogui.position", return_value=(1, 2))
    def test_req01_hotkey_does_not_emit_for_empty_selection(self, _position, _press, clipboard, _sleep):
        clipboard.paste.return_value = "   "
        bridge = HotkeyBridge()
        emitted = Mock()
        bridge.translate_triggered.connect(emitted)
        bridge._on_hotkey()
        emitted.assert_not_called()


class AppControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def controller(self):
        controller = AppController.__new__(AppController)
        controller.translator = Mock()
        controller.popup = Mock()
        controller.tray = Mock()
        controller.history_window = Mock()
        return controller

    def test_req02_translate_success_displays_popup(self):
        controller = self.controller()
        controller.translator.translate_text.return_value = "xin chào"
        controller.on_translate_triggered("hello", 10, 20)
        controller.popup.show_translation_at.assert_called_once_with("hello", "xin chào", 10, 20)

    def test_req03_translate_none_does_not_display_popup(self):
        controller = self.controller()
        controller.translator.translate_text.return_value = None
        controller.on_translate_triggered("", 10, 20)
        controller.popup.show_translation_at.assert_not_called()

    @patch("main.utils.add_to_notebook", return_value=True)
    def test_req05_save_success_extracts_phonetics_and_refreshes_visible_history(self, add):
        controller = self.controller()
        controller.history_window.isVisible.return_value = True
        text = "Dịch: sách | Phiên âm: /bʊk/ | Ví dụ: Read a book."
        controller.on_save_vocab("book", text)
        add.assert_called_once_with(word="book", definition=text, phonetics="/bʊk/", tag="General")
        controller.popup.set_save_result.assert_called_once_with(True)
        controller.tray.showMessage.assert_called_once()
        controller.history_window.load_data.assert_called_once()

    @patch("main.utils.add_to_notebook", return_value=False)
    def test_req05_save_failure_updates_popup_without_success_notification(self, _add):
        controller = self.controller()
        controller.on_save_vocab("book", "Dịch: sách")
        controller.popup.set_save_result.assert_called_once_with(False)
        controller.tray.showMessage.assert_not_called()
        controller.history_window.load_data.assert_not_called()

    def test_req07_open_history_refreshes_and_switches_windows(self):
        controller = self.controller()
        controller.open_history()
        controller.history_window.load_data.assert_called_once()
        controller.popup.hide.assert_called_once()
        controller.history_window.show.assert_called_once()
        controller.history_window.activateWindow.assert_called_once()

    def test_req11_tray_double_click_opens_popup_only_for_double_click(self):
        controller = self.controller()
        controller.on_tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
        controller.popup.show.assert_not_called()
        controller.on_tray_activated(QSystemTrayIcon.ActivationReason.DoubleClick)
        controller.popup.show.assert_called_once()
        controller.popup.activateWindow.assert_called_once()

    @patch("main.QMessageBox")
    def test_req11_popup_close_minimize_hides_and_keeps_running(self, message_box):
        controller = self.controller()
        event = Mock()
        msg = message_box.return_value
        minimize, quit_button = object(), object()
        msg.addButton.side_effect = [minimize, quit_button, object()]
        msg.clickedButton.return_value = minimize
        controller.on_popup_close(event)
        event.ignore.assert_called_once()
        controller.popup.hide.assert_called_once()
        controller.tray.showMessage.assert_called_once()

    @patch("main.QMessageBox")
    def test_req11_popup_close_quit_calls_quit_app(self, message_box):
        controller = self.controller()
        controller.quit_app = Mock()
        msg = message_box.return_value
        minimize, quit_button = object(), object()
        msg.addButton.side_effect = [minimize, quit_button, object()]
        msg.clickedButton.return_value = quit_button
        controller.on_popup_close(Mock())
        controller.quit_app.assert_called_once()

    @patch("main.QMessageBox")
    def test_req11_popup_close_cancel_ignores_event(self, message_box):
        controller = self.controller()
        event = Mock()
        msg = message_box.return_value
        msg.addButton.side_effect = [object(), object(), object()]
        msg.clickedButton.return_value = object()
        controller.on_popup_close(event)
        event.ignore.assert_called_once()
        controller.popup.hide.assert_not_called()


if __name__ == "__main__":
    unittest.main()
