# 3.2. Thiết kế kiểm thử

## 1. Phạm vi, môi trường và nguyên tắc

Tài liệu này được lập từ `README.md` và mã nguồn tại ngày 03/10/2026. Phạm vi gồm lấy
văn bản bằng hotkey, dịch, popup, lưu SQLite, xem/tìm/lọc/xóa sổ tay và vòng đời cửa
sổ/khay hệ thống. API, bàn phím, clipboard, chuột, sleep và hộp thoại được mock; SQLite
tích hợp dùng file riêng trong `reports/`, không dùng sổ tay thật.

- Framework: `unittest`, `unittest.mock`, `coverage.py 7.16.2`.
- Môi trường đã chạy: Windows PowerShell, Python 3.14.0, PyQt6 6.11.0, Qt offscreen.
- Lệnh: `python -m pip install -r requirements-test.txt`, sau đó `python run_tests.py`.
- Báo cáo tái tạo: `reports/test_results.txt`, `reports/coverage.txt`,
  `reports/coverage.xml`, `reports/coverage.json`.
- Quy ước: PASS chỉ áp dụng cho test đã chạy. Test thủ công giữ trạng thái "Chưa chạy".

## 2. Yêu cầu có thể kiểm chứng

| Mã | Nhóm | Hành vi mong muốn | Nguồn |
|---|---|---|---|
| REQ-01 | Hotkey | `Ctrl+Q` sao chép vùng chọn, bỏ khoảng trắng đầu/cuối, không phát yêu cầu nếu rỗng; nếu có dữ liệu thì phát text và tọa độ chuột. | README + `HotkeyBridge` |
| REQ-02 | Dịch | Input rỗng/whitespace không gọi API; 1-5 từ dùng prompt có nghĩa-phiên âm-ví dụ, từ 6 từ dùng prompt dịch thường; kết quả hợp lệ được trim và trả về. | README + quy tắc `<= 5` trong code |
| REQ-03 | Lỗi API | Exception được thử tối đa 3 lần, nghỉ giữa lần thử; lỗi hai lần rồi thành công phải trả kết quả; lỗi đủ ba lần trả lỗi kết nối. Phản hồi có trường `error` trả ngay, không retry. | `Translator.translate_text` |
| REQ-04 | Popup | Popup phân tích đủ/thiếu các phần có cấu trúc, hiển thị dịch thường, xóa metadata cũ, đặt vị trí tránh cạnh trên/phải màn hình. | README + `TranslationPopup` |
| REQ-05 | Lưu từ | Không lưu khi thiếu từ gốc/bản dịch; lưu đúng definition và phiên âm; chỉ báo "Đã lưu" sau khi SQLite thành công, báo thất bại khi ghi lỗi. | README; hành vi mong muốn sửa từ lỗi hiện trạng |
| REQ-06 | Khởi tạo DB | Tạo thư mục và bảng `data` đúng schema; gọi lặp lại an toàn. | `utils.init_db` |
| REQ-07 | Xem/làm mới | Sổ tay rỗng/có dữ liệu hiển thị đúng số hàng; mở sổ tay phải refresh và chuyển cửa sổ. | README + `HistoryWindow` |
| REQ-08 | Tìm kiếm | Tìm trong từ hoặc nghĩa, hỗ trợ Unicode và dấu nháy; không có kết quả trả rỗng; `%` và `_` được hiểu là ký tự thường, không phải wildcard. | README; giả định an toàn đã hiện thực hóa |
| REQ-09 | Lọc tag | "Tất cả" không giới hạn tag; tag cụ thể lọc chính xác; kết hợp search và tag dùng điều kiện AND. | `history.fetch_vocab` |
| REQ-10 | Xóa | Chỉ xóa sau xác nhận Yes và refresh; Cancel giữ dữ liệu; luồng lưu → đọc/tìm → xóa chạy trên SQLite thật tạm thời. | README + `HistoryWindow._confirm_delete` |
| REQ-11 | Cửa sổ/khay | Double-click khay mở popup; đóng có ba trạng thái thu nhỏ, thoát, hủy; đóng sổ tay mở lại popup; lăn chuột dịch popup. | `main.py`, `ui.py`, `history.py` |

Giả định cần xác nhận với chủ sản phẩm: từ trùng hiện được phép lưu thành nhiều dòng vì
schema không có unique constraint; tìm kiếm không phân biệt hoa/thường theo cách SQLite
LIKE mặc định với ASCII; chuỗi whitespace được coi là không có nội dung; ký tự wildcard
được tìm theo nghĩa literal. Các test không biến lỗi hiện trạng thành kết quả mong đợi.

## 3. Thiết kế hộp đen

Kỹ thuật dùng: phân vùng tương đương (EP), giá trị biên (BVA), bảng quyết định (DT) và
chuyển trạng thái (ST). Các bước tự động đều là chạy `python run_tests.py`; tên test ở cột
"Cách chạy" cho phép truy lại chính xác. Kết quả thực tế dưới đây lấy từ lần chạy gần nhất.

| ID | REQ | Chức năng | Kỹ thuật | Tiền điều kiện / dữ liệu | Bước thực hiện | Kết quả mong đợi | Cách chạy | Thực tế | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|
| BB-01 | REQ-01 | Lấy vùng chọn | EP | Clipboard trả `"   "` | Kích hoạt hotkey | Không phát tín hiệu dịch | `test_req01_hotkey_does_not_emit_for_empty_selection` | Đúng mong đợi | PASS |
| BB-02 | REQ-01 | Lấy vùng chọn | EP | Chuột `(120,240)`, clipboard `"  selected text  "` | Kích hoạt hotkey | Copy bằng Ctrl+C, phát `selected text,120,240` | `test_req01_hotkey_copies_strips_and_emits` | Đúng mong đợi | PASS |
| BB-03 | REQ-02 | Input dịch | EP | `""`, `"   \t"` | Gọi dịch | Trả `None`, API không được gọi | `test_req02_empty_and_whitespace_input_returns_none` | Đúng mong đợi | PASS |
| BB-04 | REQ-02 | Phân loại độ dài | BVA | 4 và 5 từ | Gọi dịch | Prompt có nghĩa-phiên âm-ví dụ | `test_req02_short_input_boundaries_use_structured_prompt` | Đúng mong đợi | PASS |
| BB-05 | REQ-02 | Phân loại độ dài | BVA | 6 từ | Gọi dịch | Prompt dịch câu thường, không yêu cầu phiên âm | `test_req02_six_words_use_plain_translation_prompt` | Đúng mong đợi | PASS |
| BB-06 | REQ-03 | API | DT | API thành công ngay, content có khoảng trắng | Gọi dịch | Một request, content được trim | `test_req02_success_posts_expected_request` | Đúng mong đợi | PASS |
| BB-07 | REQ-03 | Retry | DT | Timeout rồi thành công | Gọi dịch | 2 request, sleep một lần, trả `ok` | `test_req03_exception_then_success_retries_once` | Đúng mong đợi | PASS |
| BB-08 | REQ-03 | Retry | DT/BVA | ConnectionError cả 3 lần | Gọi dịch | 3 request, 2 sleep, trả `Lỗi kết nối` | `test_req03_three_connection_failures_return_error` | Đúng mong đợi | PASS |
| BB-09 | REQ-03 | Lỗi nghiệp vụ API | DT | JSON `error.message=invalid key` | Gọi dịch | Trả lỗi dịch thuật ngay, không retry | `test_req03_api_error_returns_immediately_without_retry` | Đúng mong đợi | PASS |
| BB-10 | REQ-03 | JSON sai cấu trúc | EP | JSON không có `choices` | Gọi dịch | Thử đủ 3 lần rồi trả lỗi kết nối | `test_req03_malformed_response_retries_three_times` | Đúng mong đợi | PASS |
| BB-11 | REQ-04 | Popup cấu trúc | EP | `Dịch: bền bỉ | Phiên âm: ... | Ví dụ: ...` | Hiển thị | Ba thành phần đúng và hiện | `test_req04_parse_complete_structured_translation` | Đúng mong đợi | PASS |
| BB-12 | REQ-04 | Popup thiếu phần | EP | Phiên âm/ví dụ rỗng | Hiển thị | Nghĩa hiện; nhãn thiếu được ẩn | `test_req04_parse_structured_translation_with_missing_parts` | Đúng mong đợi | PASS |
| BB-13 | REQ-04/05 | Chuyển bản dịch | ST | Hiển thị bản có metadata rồi bản thường | Hiển thị và nhấn lưu | Metadata cũ bị xóa, definition chỉ chứa bản mới | `test_req04_plain_translation_clears_stale_metadata_regression` | Đúng mong đợi | PASS |
| BB-14 | REQ-05 | Thiếu dữ liệu lưu | DT | Thiếu original hoặc translation | Nhấn sao | Không emit; tooltip báo không thể lưu | `test_req05_star_rejects_missing_original_or_translation` | Đúng mong đợi | PASS |
| BB-15 | REQ-05 | Trạng thái lưu | ST | Dữ liệu hợp lệ, DB chưa phản hồi | Nhấn sao | Nút disable, chỉ báo `Đang lưu...` | `test_req05_star_waits_for_storage_result_regression` | Đúng mong đợi | PASS |
| BB-16 | REQ-05 | Kết quả lưu | DT | DB success / failure | Controller nhận kết quả | Success mới báo đã lưu; failure không phát thông báo thành công | `test_req05_save_success...`, `test_req05_save_failure...` | Đúng mong đợi | PASS |
| BB-17 | REQ-06/07 | DB/sổ tay | ST | DB chưa tồn tại; sau đó thêm 3 dòng | Init, đọc trước/sau thêm | Tạo schema; 0 rồi 3 dòng | `test_req06_init_db...`, `test_req07_empty_and_populated_notebook` | Đúng mong đợi | PASS |
| BB-18 | REQ-08 | Tìm từ/nghĩa | EP | `hello`, `đừng`, `don't`, chuỗi không tồn tại | Tìm từng giá trị | Đúng dòng tương ứng hoặc rỗng | `test_req08_search_word_meaning_vietnamese_and_apostrophe` | Đúng mong đợi | PASS |
| BB-19 | REQ-08 | Wildcard | EP | Dữ liệu `100%`; tìm `%` và `_` | Tìm kiếm | `%` chỉ khớp `100%`; `_` không khớp tùy ý | `test_req08_percent_and_underscore_are_literal_search_text` | Đúng mong đợi | PASS |
| BB-20 | REQ-09 | Lọc/kết hợp | DT | General, Grammar; search `đừng`/`hello` | Chọn Tất cả/tag và kết hợp search | Tất cả=3; Grammar đúng 1; điều kiện AND chính xác | `test_req09_fetch_tags_and_filter_combinations` | Đúng mong đợi | PASS |
| BB-21 | REQ-10 | Xác nhận xóa | DT | ID 7; Yes / Cancel | Chọn hai nhánh hộp thoại | Yes xóa+refresh; Cancel không đổi | `test_req10_confirm_delete_yes_deletes_and_refreshes`, `test_req10_cancel_delete_keeps_data` | Đúng mong đợi | PASS |
| BB-22 | REQ-10 | Luồng tích hợp | ST | SQLite tạm, từ `persistence` | Lưu → tìm nghĩa/tag → xóa → đọc | Có 1 dòng trước xóa, 0 sau xóa | `test_req10_integration_save_read_search_delete` | Đúng mong đợi | PASS |
| BB-23 | REQ-11 | Đóng popup | DT | Chọn thu nhỏ / thoát / hủy | Gọi close | Ẩn+tray message / quit / ignore | 3 test `test_req11_popup_close_*` | Đúng mong đợi | PASS |
| BB-24 | REQ-11 | Hotkey/khay thực | ST | Cài đủ dependency, app chạy trên Windows | Chọn text ở app khác, Ctrl+Q; thao tác icon khay | Popup thực ở gần chuột; quyền hotkey và tray hoạt động | Thủ công MT-01 | Chưa chạy | Chưa chạy |
| BB-25 | REQ-03 | API thật | EP | API key hợp lệ và mạng thật | Dịch từ và câu | OpenRouter trả nội dung phù hợp | Thủ công MT-02 | Chưa chạy | Chưa chạy |

Phạm vi hộp đen chọn theo các lớp dữ liệu và quyết định có khác biệt hành vi, không đặt số
lượng tùy ý. Biên 4/5/6 được bao phủ; một từ nằm trong cùng lớp 1-5 và cũng được chạy
trong subtest. Timeout và connection error cùng đi qua nhánh exception/retry; khác biệt môi
trường thật được giữ lại ở MT-02.

## 4. Thiết kế hộp trắng

| ID | REQ | File/hàm | Điều kiện/nhánh | Dữ liệu kích hoạt | Assertion | Test tự động |
|---|---|---|---|---|---|---|
| WB-01 | REQ-01 | `main.HotkeyBridge._on_hotkey` | `if not text` true/false | whitespace / selected text | Không emit / emit text+tọa độ | `test_req01_hotkey_*` |
| WB-02 | REQ-02 | `translation.translate_text` | empty true/false | `""`, whitespace, `hello` | None không gọi API / đi tiếp | `test_req02_empty_and_whitespace_input_returns_none` |
| WB-03 | REQ-02 | `translation.translate_text` | `is_short` true/false | 4,5,6 từ | Chọn đúng prompt | `test_req02_short_input_boundaries...`, `test_req02_six_words...` |
| WB-04 | REQ-03 | `translation.translate_text` | thành công lần 1 | JSON choices đúng | Một request, trim content | `test_req02_success_posts_expected_request` |
| WB-05 | REQ-03 | `translation.translate_text` | exception rồi success | timeout, JSON đúng | Retry đúng 1 lần | `test_req03_exception_then_success_retries_once` |
| WB-06 | REQ-03 | `translation.translate_text` | `attempt < 2` true/false | 3 ConnectionError | 3 call, 2 sleep, lỗi kết nối | `test_req03_three_connection_failures_return_error` |
| WB-07 | REQ-03 | `translation.translate_text` | trường `error` có/không message | `invalid key` / `{}` | Nội dung thật / `Unknown error`, không retry | 2 test `test_req03_api_error_*` |
| WB-08 | REQ-04 | `ui._parse_and_display` | structured/plain; vòng lặp 3 phần | đủ, thiếu, plain | Text/visible/content đúng | 3 test `test_req04_parse_*` |
| WB-09 | REQ-04 | `ui.show_translation_at` | `pos_y < 0`; tràn cạnh phải | `(790,5)` trên màn 800px | Tọa độ được điều chỉnh | `test_req04_show_translation_repositions_inside_screen` |
| WB-10 | REQ-05 | `ui.on_star_clicked` | thiếu/đủ dữ liệu; phonetic/example có/không | empty; structured; plain | Không emit / full payload; trạng thái pending | `test_req05_star_*`, regression metadata |
| WB-11 | REQ-05 | `ui.set_save_result` | success/failure | True/False | Tooltip, enable, timer đúng | `test_req05_set_save_result_success_and_failure` |
| WB-12 | REQ-02/03 | `main.on_translate_triggered` | result truthy/falsy | `xin chào` / None | Show popup / không show | `test_req02_translate_success...`, `test_req03_translate_none...` |
| WB-13 | REQ-05 | `main.on_save_vocab` | có/không phiên âm; success/failure; history visible | structured/plain, True/False | Tham số DB, trạng thái popup, refresh/message | 2 test `test_req05_save_*` |
| WB-14 | REQ-06 | `utils.init_db` | DB/thư mục chưa có, gọi lặp | path test mới | File/schema tồn tại, không lỗi | `test_req06_init_db_creates_parent_and_schema_idempotently` |
| WB-15 | REQ-05 | `utils.add_to_notebook` | try/except | SQLite thật / connect disk full | True và row đúng / False | 2 test `test_req05_add_to_notebook_*` |
| WB-16 | REQ-08/09 | `history.fetch_vocab` | search có/không; tag all/cụ thể | search/tag ma trận | Rows đúng, wildcard escape | 3 test `test_req08_*`, `test_req09_*` |
| WB-17 | REQ-09 | `history.fetch_tags` | vòng lặp rows | General/Grammar | Danh sách distinct, có thứ tự | `test_req09_fetch_tags_and_filter_combinations` |
| WB-18 | REQ-10 | `history.delete_vocab` | xóa ID | SQLite tạm | Dòng biến mất | `test_req10_integration_save_read_search_delete` |
| WB-19 | REQ-10 | `HistoryWindow._confirm_delete` | Yes/Cancel | hai kết quả dialog | Gọi delete+render / không gọi | 2 test `test_req10_*delete*` |
| WB-20 | REQ-11 | `main.on_popup_close` | minimize/quit/cancel | ba clicked button | hide+ignore / quit / ignore | 3 test `test_req11_popup_close_*` |
| WB-21 | REQ-11 | tray/history/wheel | double click/khác; popup có/không; delta +/- | enum, mock popup, ±120 | Mở đúng; close accept; Y ±60 | `test_req11_tray_*`, `test_req11_history_*`, `test_req11_wheel_*` |

## 5. Ma trận truy vết yêu cầu

| REQ | Nội dung rút gọn | Test hộp đen | Test hộp trắng | Test tự động / thủ công | Thực thi | Khoảng trống |
|---|---|---|---|---|---|---|
| REQ-01 | Hotkey lấy vùng chọn | BB-01, BB-02, BB-24 | WB-01 | `test_req01_hotkey_*`; MT-01 | Auto PASS; manual chưa chạy | Quyền hotkey/clipboard liên ứng dụng thật |
| REQ-02 | Phân loại và dịch | BB-03..BB-06 | WB-02, WB-03, WB-12 | `test_req02_*` | PASS | Chất lượng ngôn ngữ API thật |
| REQ-03 | Lỗi/retry API | BB-07..BB-10, BB-25 | WB-04..WB-07, WB-12 | `test_req03_*`; MT-02 | Auto PASS; manual chưa chạy | Mạng và OpenRouter thật |
| REQ-04 | Hiển thị popup | BB-11..BB-13 | WB-08, WB-09 | `test_req04_*` | PASS | Hình thức trên nhiều DPI/màn hình |
| REQ-05 | Lưu từ | BB-13..BB-16 | WB-10, WB-11, WB-13, WB-15 | `test_req05_*` | PASS | Hành vi từ trùng cần chủ sản phẩm xác nhận |
| REQ-06 | Init DB | BB-17 | WB-14 | `test_req06_*` | PASS | Không |
| REQ-07 | Xem/làm mới | BB-17 | WB-13, WB-21 | `test_req07_*` | PASS | Cảm nhận UI với dữ liệu rất lớn |
| REQ-08 | Tìm kiếm | BB-18, BB-19 | WB-16 | `test_req08_*` | PASS | Unicode case-fold ngoài ASCII phụ thuộc SQLite |
| REQ-09 | Lọc tag | BB-20 | WB-16, WB-17 | `test_req09_*` | PASS | Không |
| REQ-10 | Xóa | BB-21, BB-22 | WB-18, WB-19 | `test_req10_*` | PASS | Kiểm tra trực quan dialog thật |
| REQ-11 | Cửa sổ/khay | BB-23, BB-24 | WB-20, WB-21 | `test_req11_*`; MT-01 | Auto PASS; manual chưa chạy | Tray, Esc và window manager thật |

- Bao phủ thiết kế yêu cầu: 11/11 = 100% yêu cầu có ít nhất một test phù hợp.
- Điều này không đồng nghĩa 11/11 đã được xác minh hoàn toàn: MT-01 và MT-02 chưa chạy.
- Test tự động: 43 chạy, 43 PASS, 0 FAIL, 0 ERROR; tỷ lệ PASS test đã chạy = 100%.
- Line/statement coverage: 431/500 line thực thi, statement coverage 86.20%.
- Branch coverage: 65/80 = 81.25%.
- Chỉ số kết hợp do coverage.py hiển thị: 85.52% (làm tròn cột TOTAL: 86%).
- Phần thiếu tập trung ở khởi tạo/tray thật, main entry point, phím Esc và vài nhánh bố trí
  GUI; không suy ra coverage từ số lượng test.

## 6. Lỗi phát hiện và sửa hồi quy

1. `TranslationPopup.on_star_clicked` trước đây đặt tooltip "Đã lưu" trước khi callback ghi
   SQLite trả kết quả. Sửa thành trạng thái `Đang lưu...`, controller gọi
   `set_save_result(success)`, chỉ success mới báo đã lưu. Khóa bởi BB-15, BB-16/WB-10,
   WB-11, WB-13.
2. Khi chuyển từ bản dịch có phiên âm/ví dụ sang bản dịch thường, label bị ẩn nhưng nội
   dung cũ vẫn còn và được ghép lại lúc lưu. Sửa bằng cách clear hai label ở nhánh plain.
   Khóa bởi BB-13.
3. Chuỗi chỉ có whitespace trước đây vẫn có thể gọi API trực tiếp. Sửa bằng `text.strip()`
   và trả `None`; khóa bởi BB-03.
4. Tìm `%` hoặc `_` trước đây dùng wildcard LIKE ngoài ý muốn. Sửa escape literal; khóa
   bởi BB-19.
5. Việc tạo thư mục DB xảy ra lúc import, gây tác dụng phụ và khó cô lập. Chuyển tạo thư
   mục vào `init_db`; `add_to_notebook` tự bảo đảm schema tồn tại. Khóa bởi BB-17/WB-14.

## 7. Kiểm thử thủ công và giới hạn mock

### MT-01 - Tích hợp desktop Windows (Chưa chạy)

1. Cài dependency, chạy `python main.py` bằng quyền phù hợp.
2. Bôi đen text trong Notepad và trình duyệt, nhấn `Ctrl+Q`.
3. Kiểm tra popup nằm gần chuột, không vượt màn hình; thử không chọn text.
4. Double-click tray, mở sổ tay, đóng/thu nhỏ/hủy/thoát, nhấn Esc.
5. Ghi bằng chứng màn hình và trạng thái. Mock không chứng minh quyền global keyboard,
   clipboard giữa process, tray shell, focus và DPI/window manager thật.

### MT-02 - API thật (Chưa chạy)

1. Đặt `OPENROUTER_API_KEY`, bảo đảm có Internet.
2. Dịch một từ và một câu 6 từ trở lên.
3. Kiểm tra cấu trúc, độ chính xác ngôn ngữ, timeout và thông báo khi key sai.
4. Test tự động không gọi mạng nên chỉ chứng minh request/prompt, parse và retry, không
   chứng minh SLA hay chất lượng mô hình bên ngoài.

## 8. Kịch bản demo ngắn

1. Chạy `python run_tests.py`; chỉ ra 43 PASS và `reports/coverage.txt`.
2. Hộp đen: trình bày BB-05 (biên 5/6 từ), dữ liệu/đầu ra nhìn từ bên ngoài và liên kết
   REQ-02.
3. Hộp trắng: trình bày WB-06, nhánh `attempt < 2`, ba exception và assertion 3 call/2
   sleep, liên kết REQ-03.
4. Mở ma trận ở mục 5 để chỉ BB-05 và WB-06 truy vết về yêu cầu, rồi phân biệt thiết kế
   coverage, trạng thái chạy và line/branch coverage.
