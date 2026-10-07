# HƯỚNG DẪN CHẠY KIỂM THỬ TỰ ĐỘNG (RUN_TEST.md)

Tài liệu này hướng dẫn cách thiết lập môi trường và chạy toàn bộ bộ kiểm thử tự động (Automated Testing & Random Testing) cho dự án **AI Translate**.

---

## 1. Điều kiện cần thiết

- **Hệ điều hành**: Windows 10/11, Linux hoặc macOS.
- **Python**: Phiên bản 3.10 trở lên (khuyến nghị Python 3.10 - 3.14).
- **Thư viện chuẩn**: Python built-in module `unittest`, `sqlite3`, `tempfile`, `random`.
- **Thư viện phụ thuộc của ứng dụng**: `PyQt6`, `requests`, `python-dotenv`.

---

## 2. Cách cài đặt dependency phục vụ testing

Toàn bộ các ca kiểm thử sử dụng framework chuẩn `unittest` của Python nên **không yêu cầu cài thêm bất kỳ test runner bên ngoài nào**.

Tuy nhiên, để chạy được môi trường ứng dụng và kiểm thử headless GUI, cần đảm bảo các dependencies chính trong `requirements.txt` đã được cài đặt:

```bash
# Cài đặt các thư viện của project
pip install -r requirements.txt
```

*(Lưu ý: Nếu muốn dùng pytest thay vì unittest chuẩn, có thể cài thêm `pip install pytest`, nhưng mặc định lệnh `python -m unittest` đã chạy hoàn chỉnh).*

---

## 3. Cách chạy project

Để chạy ứng dụng bình thường:

```bash
# 1. Tạo file .env và nhập API Key
# OPENROUTER_API_KEY=your_key_here

# 2. Khởi chạy ứng dụng chính
python main.py
```

Ứng dụng sẽ khởi động và thu nhỏ xuống khay hệ thống (System Tray). Sử dụng phím tắt `Ctrl + Q` khi bôi đen văn bản để dịch.

---

## 4. Cách chạy test

Hệ thống kiểm thử được thiết kế hoàn toàn độc lập:
- Tự động kích hoạt chế độ **Headless / Offscreen Mode** (`QT_QPA_PLATFORM=offscreen`) cho PyQt6, không làm bật cửa sổ đồ họa hay gây gián đoạn màn hình làm việc.
- Sử dụng cơ sở dữ liệu tạm thời (`tempfile`), tự động xóa sau mỗi lần test, không ảnh hưởng đến dữ liệu sổ tay thật (`%APPDATA%/AI_Translate/data.db`).
- Giả lập (Mock) các lệnh gọi mạng và OpenRouter API để test chạy tức thì mà không cần mạng Internet hay API key thật.

---

## 5. Command chính xác để chạy test

Mở terminal tại thư mục gốc của dự án (`F:\SoftWare-Testing-main`) và chạy các lệnh tương ứng:

### A. Chạy toàn bộ test suites (Khuyến nghị)

```bash
python -m unittest discover tests -v
```

Hoặc nếu đang dùng môi trường ảo `venv`:

```bash
.\venv\Scripts\python.exe -m unittest discover tests -v
```

### B. Chạy riêng từng module kiểm thử

1. **Kiểm thử Cơ sở dữ liệu Sổ tay từ vựng (CRUD, Boundary, Injection)**:
```bash
python -m unittest tests/test_notebook_db.py -v
```

2. **Kiểm thử Logic Dịch thuật và Bộ bóc tách UI (Parser, Retry, Mock API)**:
```bash
python -m unittest tests/test_translation_parser.py -v
```

3. **Kiểm thử ngẫu nhiên / Fuzz Testing (Random Seed 42, 100+ mẫu ngẫu nhiên)**:
```bash
python -m unittest tests/test_random_fuzzing.py -v
```

---

## 6. Kết quả mong đợi

Khi chạy lệnh `python -m unittest discover tests -v`, đầu ra hiển thị trạng thái của từng test case:

```text
test_tc_db_01_init_db_creates_table (test_notebook_db.TestNotebookDB.test_tc_db_01_init_db_creates_table) ... ok
test_tc_db_02_add_valid_word_default_tag (test_notebook_db.TestNotebookDB.test_tc_db_02_add_valid_word_default_tag) ... ok
test_tc_db_03_add_word_custom_tag (test_notebook_db.TestNotebookDB.test_tc_db_03_add_word_custom_tag) ... ok
test_tc_db_04_fetch_vocab_all_ordered_by_timestamp_desc (test_notebook_db.TestNotebookDB.test_tc_db_04_fetch_vocab_all_ordered_by_timestamp_desc) ... ok
test_tc_db_05_fetch_vocab_search_by_word (test_notebook_db.TestNotebookDB.test_tc_db_05_fetch_vocab_search_by_word) ... ok
test_tc_db_06_fetch_vocab_search_by_definition (test_notebook_db.TestNotebookDB.test_tc_db_06_fetch_vocab_search_by_definition) ... ok
test_tc_db_07_fetch_vocab_filter_by_tag (test_notebook_db.TestNotebookDB.test_tc_db_07_fetch_vocab_filter_by_tag) ... ok
test_tc_db_08_fetch_vocab_combined_search_and_tag (test_notebook_db.TestNotebookDB.test_tc_db_08_fetch_vocab_combined_search_and_tag) ... ok
test_tc_db_09_fetch_tags_distinct_sorted (test_notebook_db.TestNotebookDB.test_tc_db_09_fetch_tags_distinct_sorted) ... ok
test_tc_db_10_delete_vocab_success (test_notebook_db.TestNotebookDB.test_tc_db_10_delete_vocab_success) ... ok
test_tc_db_11_delete_non_existent_id (test_notebook_db.TestNotebookDB.test_tc_db_11_delete_non_existent_id) ... ok
test_tc_db_12_fetch_vocab_no_match (test_notebook_db.TestNotebookDB.test_tc_db_12_fetch_vocab_no_match) ... ok
test_tc_db_13_fetch_vocab_non_existent_tag (test_notebook_db.TestNotebookDB.test_tc_db_13_fetch_vocab_non_existent_tag) ... ok
test_tc_db_14_add_word_empty_strings (test_notebook_db.TestNotebookDB.test_tc_db_14_add_word_empty_strings) ... ok
test_tc_db_15_add_word_very_large_text (test_notebook_db.TestNotebookDB.test_tc_db_15_add_word_very_large_text) ... ok
test_tc_db_16_sql_injection_resilience (test_notebook_db.TestNotebookDB.test_tc_db_16_sql_injection_resilience) ... ok
test_tc_db_17_unicode_and_vietnamese_diacritics (test_notebook_db.TestNotebookDB.test_tc_db_17_unicode_and_vietnamese_diacritics) ... ok
test_random_01_database_random_vocabulary_insertion_and_integrity (test_random_fuzzing.TestRandomFuzzing.test_random_01_database_random_vocabulary_insertion_and_integrity) ... ok
test_random_02_database_random_search_substrings (test_random_fuzzing.TestRandomFuzzing.test_random_02_database_random_search_substrings) ... ok
test_random_03_classification_word_count_fuzzing (test_random_fuzzing.TestRandomFuzzing.test_random_03_classification_word_count_fuzzing) ... ok
test_random_04_ui_parser_fuzzing_robustness (test_random_fuzzing.TestRandomFuzzing.test_random_04_ui_parser_fuzzing_robustness) ... ok
test_tc_tr_01_translate_empty_and_none (test_translation_parser.TestTranslationAndParser.test_tc_tr_01_translate_empty_and_none) ... ok
test_tc_tr_02_prompt_classification_short_text (test_translation_parser.TestTranslationAndParser.test_tc_tr_02_prompt_classification_short_text) ... ok
test_tc_tr_03_prompt_classification_long_text (test_translation_parser.TestTranslationAndParser.test_tc_tr_03_prompt_classification_long_text) ... ok
test_tc_tr_04_boundary_exact_5_words (test_translation_parser.TestTranslationAndParser.test_tc_tr_04_boundary_exact_5_words) ... ok
test_tc_tr_05_boundary_exact_6_words (test_translation_parser.TestTranslationAndParser.test_tc_tr_05_boundary_exact_6_words) ... ok
test_tc_tr_06_api_error_response_handling (test_translation_parser.TestTranslationAndParser.test_tc_tr_06_api_error_response_handling) ... ok
test_tc_tr_07_network_exception_retry_and_failure (test_translation_parser.TestTranslationAndParser.test_tc_tr_07_network_exception_retry_and_failure) ... ok
test_tc_ui_01_parse_standard_three_part_format (test_translation_parser.TestTranslationAndParser.test_tc_ui_01_parse_standard_three_part_format) ... ok
test_tc_ui_02_parse_plain_sentence_format (test_translation_parser.TestTranslationAndParser.test_tc_ui_02_parse_plain_sentence_format) ... ok
test_tc_ui_03_parse_partial_format_without_example (test_translation_parser.TestTranslationAndParser.test_tc_ui_03_parse_partial_format_without_example) ... ok
test_tc_ui_04_star_button_empty_text_prevents_save (test_translation_parser.TestTranslationAndParser.test_tc_ui_04_star_button_empty_text_prevents_save) ... ok
test_tc_ui_05_star_button_valid_text_emits_save_signal (test_translation_parser.TestTranslationAndParser.test_tc_ui_05_star_button_valid_text_emits_save_signal) ... ok

----------------------------------------------------------------------
Ran 33 tests in 1.712s

OK
```

**Thống kê:**
- **Tổng số ca kiểm thử**: 33
- **Thành công (PASS)**: 33 (100%)
- **Thất bại (FAIL)**: 0
- **Lỗi (ERROR)**: 0
