import unittest
from unittest.mock import Mock, patch

from translation import API_URL, Translator


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.translator = Translator()

    def response(self, data):
        response = Mock()
        response.json.return_value = data
        return response

    @patch.dict("translation.os.environ", {}, clear=True)
    def test_req02_default_model_uses_active_model(self):
        translator = Translator()
        self.assertEqual(translator.model, "google/gemini-3.5-flash-lite")

    @patch.dict("translation.os.environ", {"OPENROUTER_MODEL": "google/gemini-3.5-flash-lite"})
    def test_req02_model_can_be_configured_from_environment(self):
        translator = Translator()
        self.assertEqual(translator.model, "google/gemini-3.5-flash-lite")

    @patch("translation.requests.post")
    def test_req02_empty_and_whitespace_input_returns_none(self, post):
        self.assertIsNone(self.translator.translate_text(""))
        self.assertIsNone(self.translator.translate_text("   \t"))
        post.assert_not_called()

    @patch("translation.requests.post")
    def test_req02_short_input_boundaries_use_structured_prompt(self, post):
        post.return_value = self.response({"choices": [{"message": {"content": "ok"}}]})
        for count in (1, 4, 5):
            with self.subTest(count=count):
                text = " ".join(["word"] * count)
                self.assertEqual(self.translator.translate_text(text), "ok")
                prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
                self.assertIn("Phiên âm", prompt)

    @patch("translation.requests.post")
    def test_req02_six_words_use_plain_translation_prompt(self, post):
        post.return_value = self.response({"choices": [{"message": {"content": " bản dịch "}}]})
        result = self.translator.translate_text("one two three four five six")
        self.assertEqual(result, "bản dịch")
        prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
        self.assertIn("Dịch câu", prompt)
        self.assertNotIn("Phiên âm", prompt)

    @patch("translation.requests.post")
    def test_req02_success_posts_expected_request(self, post):
        post.return_value = self.response({"choices": [{"message": {"content": "xin chào"}}]})
        self.assertEqual(self.translator.translate_text("hello world here today now again"), "xin chào")
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], API_URL)
        self.assertEqual(post.call_args.kwargs["timeout"], 15)
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 150)

    @patch("translation.time.sleep")
    @patch("translation.requests.post")
    def test_req03_exception_then_success_retries_once(self, post, sleep):
        post.side_effect = [TimeoutError("slow"), self.response({"choices": [{"message": {"content": "ok"}}]})]
        self.assertEqual(self.translator.translate_text("hello"), "ok")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(3)

    @patch("translation.time.sleep")
    @patch("translation.requests.post")
    def test_req03_three_connection_failures_return_error(self, post, sleep):
        post.side_effect = ConnectionError("offline")
        self.assertEqual(self.translator.translate_text("hello"), "Lỗi kết nối: offline")
        self.assertEqual(post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("translation.time.sleep")
    @patch("translation.requests.post")
    def test_req03_malformed_response_retries_three_times(self, post, sleep):
        post.return_value = self.response({"unexpected": True})
        result = self.translator.translate_text("hello")
        self.assertTrue(result.startswith("Lỗi kết nối:"))
        self.assertEqual(post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("translation.requests.post")
    def test_req03_api_error_returns_immediately_without_retry(self, post):
        post.return_value = self.response({"error": {"message": "invalid key"}})
        self.assertEqual(self.translator.translate_text("hello"), "Lỗi dịch thuật: invalid key")
        post.assert_called_once()

    @patch("translation.requests.post")
    def test_req03_api_error_without_message_uses_fallback(self, post):
        post.return_value = self.response({"error": {}})
        self.assertEqual(self.translator.translate_text("hello"), "Lỗi dịch thuật: Unknown error")


if __name__ == "__main__":
    unittest.main()
