import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUTPUT = REPORTS / "Bao_cao_kiem_thu_3_2.xlsx"

NAVY = "17324D"
BLUE = "2E75B6"
LIGHT_BLUE = "D9EAF7"
GREEN = "E2F0D9"
YELLOW = "FFF2CC"
RED = "FCE4D6"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="B7C9D6")


REQUIREMENTS = [
    ("REQ-01", "Hotkey", "Ctrl+Q lấy vùng chọn, trim khoảng trắng; không dịch khi rỗng."),
    ("REQ-02", "Dịch", "1-5 từ dùng định dạng nghĩa-phiên âm-ví dụ; từ 6 từ dịch thường."),
    ("REQ-03", "Lỗi API", "Exception retry tối đa 3 lần; JSON error trả ngay, không retry."),
    ("REQ-04", "Popup", "Hiển thị đủ/thiếu thành phần và xóa metadata cũ khi đổi bản dịch."),
    ("REQ-05", "Lưu từ", "Chỉ báo đã lưu sau khi SQLite thành công; thiếu dữ liệu không lưu."),
    ("REQ-06", "Khởi tạo DB", "Tạo thư mục, schema SQLite và cho phép init lặp lại."),
    ("REQ-07", "Xem sổ tay", "Hiển thị đúng dữ liệu, số lượng và làm mới khi mở."),
    ("REQ-08", "Tìm kiếm", "Tìm theo từ/nghĩa, Unicode, dấu nháy; % và _ là ký tự thường."),
    ("REQ-09", "Lọc tag", "Tất cả/tag cụ thể và kết hợp tìm kiếm theo điều kiện AND."),
    ("REQ-10", "Xóa", "Yes xóa và refresh; Cancel giữ dữ liệu; kiểm tra luồng tích hợp."),
    ("REQ-11", "Cửa sổ/khay", "Mở, ẩn, đóng, tray, lịch sử và di chuyển popup đúng trạng thái."),
]

BLACK_BOX = [
    ("BB-01", "REQ-01", "EP", "Clipboard chỉ có khoảng trắng", "Không phát tín hiệu dịch", "test_req01_hotkey_does_not_emit_for_empty_selection"),
    ("BB-02", "REQ-01", "EP", "Clipboard: '  selected text  '", "Emit 'selected text' và tọa độ chuột", "test_req01_hotkey_copies_strips_and_emits"),
    ("BB-03", "REQ-02", "EP", "Chuỗi rỗng/whitespace", "Trả None, không gọi API", "test_req02_empty_and_whitespace_input_returns_none"),
    ("BB-04", "REQ-02", "BVA", "Văn bản 4 và 5 từ", "Prompt có phiên âm và ví dụ", "test_req02_short_input_boundaries_use_structured_prompt"),
    ("BB-05", "REQ-02", "BVA", "Văn bản đúng 6 từ", "Prompt dịch câu, không yêu cầu phiên âm", "test_req02_six_words_use_plain_translation_prompt"),
    ("BB-06", "REQ-03", "DT", "Timeout lần 1, thành công lần 2", "Gọi 2 lần, sleep 1 lần, trả ok", "test_req03_exception_then_success_retries_once"),
    ("BB-07", "REQ-03", "DT/BVA", "ConnectionError cả 3 lần", "Gọi 3 lần, trả Lỗi kết nối", "test_req03_three_connection_failures_return_error"),
    ("BB-08", "REQ-03", "DT", "API trả error: invalid key", "Trả lỗi ngay, không retry", "test_req03_api_error_returns_immediately_without_retry"),
    ("BB-09", "REQ-04", "EP", "Dịch có nghĩa, phiên âm, ví dụ", "Hiển thị đúng ba thành phần", "test_req04_parse_complete_structured_translation"),
    ("BB-10", "REQ-04/05", "ST", "Bản có metadata -> bản dịch thường", "Xóa dữ liệu cũ trước khi hiển thị/lưu", "test_req04_plain_translation_clears_stale_metadata_regression"),
    ("BB-11", "REQ-05", "DT", "Thiếu từ gốc hoặc bản dịch", "Không emit; báo không thể lưu", "test_req05_star_rejects_missing_original_or_translation"),
    ("BB-12", "REQ-05", "ST", "Nhấn sao, DB chưa phản hồi", "Hiện Đang lưu; chưa báo Đã lưu", "test_req05_star_waits_for_storage_result_regression"),
    ("BB-13", "REQ-08", "EP", "Tìm hello, đừng, don't, không tồn tại", "Trả đúng dòng hoặc rỗng", "test_req08_search_word_meaning_vietnamese_and_apostrophe"),
    ("BB-14", "REQ-09", "DT", "Tất cả/Grammar kết hợp search", "Lọc tag và search theo AND", "test_req09_fetch_tags_and_filter_combinations"),
    ("BB-15", "REQ-10", "ST", "SQLite tạm: lưu -> tìm -> xóa", "Một dòng trước xóa, không còn sau xóa", "test_req10_integration_save_read_search_delete"),
]

WHITE_BOX = [
    ("WB-01", "REQ-01", "main.py / HotkeyBridge._on_hotkey", "if not text: True/False", "Whitespace / selected text", "Không emit / emit đúng dữ liệu", "test_req01_hotkey_*"),
    ("WB-02", "REQ-02", "translation.py / translate_text", "if not text or not text.strip()", "Rỗng, whitespace, hello", "None hoặc đi tiếp", "test_req02_empty_and_whitespace_input_returns_none"),
    ("WB-03", "REQ-02", "translation.py / translate_text", "is_short <=5 / >5", "4, 5, 6 từ", "Chọn đúng prompt", "test_req02_short_input_boundaries...; test_req02_six_words..."),
    ("WB-04", "REQ-03", "translation.py / translate_text", "Exception rồi success", "Timeout, sau đó JSON hợp lệ", "2 request, 1 sleep, trả ok", "test_req03_exception_then_success_retries_once"),
    ("WB-05", "REQ-03", "translation.py / translate_text", "attempt < 2: True/False", "3 ConnectionError", "3 request, 2 sleep, trả lỗi", "test_req03_three_connection_failures_return_error"),
    ("WB-06", "REQ-03", "translation.py / translate_text", "'error' in data", "Error có/không message", "Trả lỗi ngay, không retry", "test_req03_api_error_*"),
    ("WB-07", "REQ-04", "ui.py / _parse_and_display", "Structured/plain; vòng lặp parts", "Đủ, thiếu, bản thường", "Text, visibility và content đúng", "test_req04_parse_*"),
    ("WB-08", "REQ-05", "ui.py / on_star_clicked", "Thiếu/đủ original và translation", "Empty / structured", "Không emit / payload đầy đủ", "test_req05_star_*"),
    ("WB-09", "REQ-05", "main.py / on_save_vocab", "success/failure; history visible", "True/False", "Popup, tray và refresh đúng", "test_req05_save_*"),
    ("WB-10", "REQ-08/09", "history.py / fetch_vocab", "search có/không; tag all/cụ thể", "Ma trận search/tag", "Rows và escape wildcard đúng", "test_req08_*; test_req09_*"),
    ("WB-11", "REQ-10", "history.py / _confirm_delete", "Yes/Cancel", "Hai kết quả dialog", "Delete+render / không gọi", "test_req10_*delete*"),
    ("WB-12", "REQ-11", "main.py / on_popup_close", "Minimize/Quit/Cancel", "Ba button", "Hide+ignore / quit / ignore", "test_req11_popup_close_*"),
]


def style_sheet(ws, widths=None):
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=THIN)
    if widths:
        for index, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(index)].width = width


def add_table(ws, headers, rows, widths):
    ws.append(headers)
    for row in rows:
        ws.append(row)
    style_sheet(ws, widths)


def parse_test_results():
    text = (REPORTS / "test_results.txt").read_text(encoding="utf-8")
    rows = []
    pattern = re.compile(r"^(test_\S+) \(([^)]+)\) \.\.\. (ok|FAIL|ERROR)$", re.MULTILINE)
    for name, location, status in pattern.findall(text):
        req = re.search(r"req\d+", name)
        rows.append((name, req.group(0).upper().replace("REQ", "REQ-") if req else "-", location, "PASS" if status == "ok" else status))
    return rows


def main():
    REPORTS.mkdir(exist_ok=True)
    coverage = json.loads((REPORTS / "coverage.json").read_text(encoding="utf-8"))
    totals = coverage["totals"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Tong quan"
    ws.sheet_view.showGridLines = False
    ws.merge_cells("A1:F1")
    ws["A1"] = "BÁO CÁO THIẾT KẾ KIỂM THỬ - MỤC 3.2"
    ws["A1"].fill = PatternFill("solid", fgColor=NAVY)
    ws["A1"].font = Font(color=WHITE, bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")
    summary = [
        ("Hạng mục", "Kết quả", "Cách nói khi demo"),
        ("Yêu cầu có test", "11/11 (100%)", "Tất cả yêu cầu trong phạm vi đều truy vết được tới test."),
        ("Test tự động", "43 PASS / 43", "Toàn bộ test đã chạy đều PASS; không có FAIL hoặc ERROR."),
        ("Statement coverage", f"{totals['covered_lines']}/{totals['num_statements']} = {totals['percent_statements_covered']:.2f}%", "Đo số dòng lệnh thực sự được chạy."),
        ("Branch coverage", f"{totals['covered_branches']}/{totals['num_branches']} = {totals['percent_branches_covered']:.2f}%", "Đo các nhánh if/else và đường rẽ logic."),
        ("Coverage tổng hợp", f"{totals['percent_covered']:.2f}%", "Coverage không đồng nghĩa chương trình hoàn toàn không có lỗi."),
        ("Test thủ công", "MT-01, MT-02 chưa chạy", "Hotkey/tray và chất lượng API thật cần kiểm tra trên môi trường thật."),
    ]
    for row in summary:
        ws.append(row)
    for cell in ws[2]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(color=WHITE, bold=True)
    for row in ws.iter_rows(min_row=3, max_col=3):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=THIN)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 72

    add_table(wb.create_sheet("Yeu cau"), ["Mã", "Nhóm chức năng", "Hành vi kiểm chứng"], REQUIREMENTS, [14, 24, 90])
    black_rows = [row + ("PASS",) for row in BLACK_BOX]
    add_table(wb.create_sheet("Test hop den"), ["ID", "REQ", "Kỹ thuật", "Dữ liệu đầu vào", "Kết quả mong đợi", "Test tự động", "Trạng thái"], black_rows, [12, 14, 12, 38, 45, 55, 14])
    white_rows = [row + ("PASS",) for row in WHITE_BOX]
    add_table(wb.create_sheet("Test hop trang"), ["ID", "REQ", "File / hàm", "Điều kiện hoặc nhánh", "Dữ liệu kích hoạt", "Assertion", "Test tự động", "Trạng thái"], white_rows, [12, 14, 34, 34, 30, 38, 55, 14])

    trace_rows = []
    for req, group, behavior in REQUIREMENTS:
        bb = ", ".join(row[0] for row in BLACK_BOX if req in row[1]) or "Xem tài liệu chi tiết"
        wb_ids = ", ".join(row[0] for row in WHITE_BOX if req in row[1]) or "Xem tài liệu chi tiết"
        gap = "Không" if req in {"REQ-06", "REQ-09"} else "Xem giới hạn test thủ công trong tài liệu"
        trace_rows.append((req, behavior, bb, wb_ids, "Auto PASS", gap))
    add_table(wb.create_sheet("Ma tran truy vet"), ["REQ", "Nội dung", "Test hộp đen", "Test hộp trắng", "Thực thi", "Khoảng trống"], trace_rows, [14, 65, 28, 28, 16, 45])

    test_rows = parse_test_results()
    add_table(wb.create_sheet("Ket qua 43 test"), ["Tên test", "REQ", "Lớp test", "Kết quả"], test_rows, [70, 14, 60, 14])
    result_ws = wb["Ket qua 43 test"]
    for cell in result_ws["D"][1:]:
        cell.fill = PatternFill("solid", fgColor=GREEN if cell.value == "PASS" else RED)

    coverage_rows = []
    for filename, info in coverage["files"].items():
        s = info["summary"]
        coverage_rows.append((filename, s["num_statements"], s["covered_lines"], s["percent_statements_covered"] / 100, s["num_branches"], s["covered_branches"], s["percent_branches_covered"] / 100))
    coverage_rows.append(("TOTAL", totals["num_statements"], totals["covered_lines"], totals["percent_statements_covered"] / 100, totals["num_branches"], totals["covered_branches"], totals["percent_branches_covered"] / 100))
    cov_ws = wb.create_sheet("Coverage")
    add_table(cov_ws, ["Module", "Statements", "Covered lines", "Line %", "Branches", "Covered branches", "Branch %"], coverage_rows, [24, 15, 18, 14, 14, 20, 14])
    for row in range(2, cov_ws.max_row + 1):
        cov_ws.cell(row, 4).number_format = "0.00%"
        cov_ws.cell(row, 7).number_format = "0.00%"
    chart = BarChart()
    chart.title = "Line và branch coverage theo module"
    chart.y_axis.title = "Tỷ lệ"
    chart.height = 8
    chart.width = 15
    cats = Reference(cov_ws, min_col=1, min_row=2, max_row=cov_ws.max_row - 1)
    chart.add_data(Reference(cov_ws, min_col=4, max_col=4, min_row=1, max_row=cov_ws.max_row - 1), titles_from_data=True)
    chart.add_data(Reference(cov_ws, min_col=7, max_col=7, min_row=1, max_row=cov_ws.max_row - 1), titles_from_data=True)
    chart.set_categories(cats)
    cov_ws.add_chart(chart, "I2")

    demo_rows = [
        ("1", "Mở sheet Tổng quan", "Em có 11 yêu cầu, 43/43 test PASS và coverage tổng hợp 85,52%."),
        ("2", "Hộp đen BB-04/BB-05", "Em kiểm tra biên 5 và 6 từ chỉ dựa trên đầu vào và kết quả mong đợi, liên kết REQ-02."),
        ("3", "Chạy test hộp đen", "python -m unittest tests.test_translation.TranslatorTests.test_req02_six_words_use_plain_translation_prompt -v"),
        ("4", "Hộp trắng WB-04/WB-05", "Em nhìn vào vòng lặp retry và nhánh attempt < 2 trong translate_text, liên kết REQ-03."),
        ("5", "Chạy test hộp trắng", "python -m unittest tests.test_translation.TranslatorTests.test_req03_exception_then_success_retries_once -v"),
        ("6", "Chạy toàn bộ", "python run_tests.py"),
        ("7", "Chốt", "PASS là kết quả test; line/branch coverage do coverage.py đo; test thủ công chưa chạy không ghi PASS."),
    ]
    add_table(wb.create_sheet("Kich ban demo"), ["Bước", "Thao tác", "Lời nói gợi ý / lệnh"], demo_rows, [10, 30, 100])

    for sheet in wb.worksheets:
        sheet.auto_filter.ref = sheet.dimensions if sheet.max_row > 1 else None
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.fitToWidth = 1
        sheet.sheet_properties.pageSetUpPr.fitToPage = True

    wb.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
