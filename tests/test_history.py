import pytest
import sqlite3
import history
import utils

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_data.db"
    monkeypatch.setattr(utils, 'DB_PATH', str(db_file))
    utils.init_db()
    
    conn = sqlite3.connect(utils.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO data (word, definition, phonetics, tag) VALUES ('cat', 'con mèo', '', 'Animal')")
    cursor.execute("INSERT INTO data (word, definition, phonetics, tag) VALUES ('dog', 'con chó', '', 'Animal')")
    cursor.execute("INSERT INTO data (word, definition, phonetics, tag) VALUES ('apple', 'quả táo', '', 'Food')")
    conn.commit()
    conn.close()

def test_fetch_vocab_all():
    rows = history.fetch_vocab()
    assert len(rows) == 3
def test_fetch_vocab_search():
    rows = history.fetch_vocab(search="cat")
    assert len(rows) == 1
    assert rows[0][1] == "cat" 
def test_fetch_vocab_filter_tag():
    rows = history.fetch_vocab(tag="Food")
    assert len(rows) == 1
    assert rows[0][1] == "apple"

def test_fetch_tags():
    tags = history.fetch_tags()
    assert set(tags) == {"Animal", "Food"}

def test_delete_vocab():
    rows = history.fetch_vocab(search="dog")
    dog_id = rows[0][0]
    
    history.delete_vocab(dog_id)
    rows_after = history.fetch_vocab()
    assert len(rows_after) == 2