import pytest
from unittest.mock import patch, MagicMock
from translation import Translator

@pytest.fixture
def translator():
    return Translator()

def test_translate_text_empty(translator):
    assert translator.translate_text("") is None

@patch('translation.requests.post')
def test_translate_text_short(mock_post, translator):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Dịch: Kiên trì | Phiên âm: /pərˈsɪstəns/ | Ví dụ: He showed great persistence."}}]
    }
    mock_post.return_value = mock_response

    result = translator.translate_text("Persistence")
    assert "Kiên trì" in result
    called_prompt = mock_post.call_args[1]['json']['messages'][0]['content']
    assert "1-3 nghĩa ngắn" in called_prompt

@patch('translation.requests.post')
def test_translate_text_long(mock_post, translator):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Đây là một câu dài cần dịch."}}]
    }
    mock_post.return_value = mock_response

    result = translator.translate_text("This is a very long sentence to translate.")
    assert "Đây là một câu dài" in result
    called_prompt = mock_post.call_args[1]['json']['messages'][0]['content']
    assert "bản dịch ngắn gọn" in called_prompt

@patch('translation.requests.post')
def test_translate_text_api_error(mock_post, translator):
    mock_response = MagicMock()
    mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
    mock_post.return_value = mock_response

    result = translator.translate_text("Hello")
    assert "Lỗi dịch thuật: Invalid API key" in result

@patch('translation.requests.post')
def test_translate_text_connection_error(mock_post, translator):
    mock_post.side_effect = Exception("Connection timed out")
    with patch('translation.time.sleep'):
        result = translator.translate_text("Hello")
    
    assert "Lỗi kết nối: Connection timed out" in result