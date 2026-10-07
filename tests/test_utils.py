import pytest
import sqlite3
import os
from unittest.mock import patch
import utils

@pytest.fixture(autouse=True)
def mock_db_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test_data.db"
    monkeypatch.setattr(utils, 'DB_PATH', str(db_file))

def test_init_db():
    utils.init_db()
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data'")
    table = cursor.fetchone()
    conn.close()
    assert table is not None

def test_add_to_notebook_success():
    utils.init_db()
    result = utils.add_to_notebook("Hello", "Xin chào", "/heˈloʊ/", "Basic")
    assert result is True
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT word, definition, phonetics, tag FROM data")
    row = cursor.fetchone()
    conn.close()
    
    assert row == ("Hello", "Xin chào", "/heˈloʊ/", "Basic")

@patch('utils.sqlite3.connect')
def test_add_to_notebook_exception(mock_connect):
    mock_connect.side_effect = Exception("DB Locked")
    
    result = utils.add_to_notebook("Error", "Lỗi")
    assert result is False

@patch('utils.mouse.position')
def test_get_mouse_position(mock_pos):
    mock_pos.return_value = (100, 200)
    pos = utils.get_mouse_position()
    assert pos == (100, 200)