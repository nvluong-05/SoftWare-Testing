import io
import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from coverage import Coverage


ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
SOURCE_FILES = ["main.py", "translation.py", "ui.py", "utils.py", "history.py"]


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)
        return len(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    # Desktop hooks are always mocked by tests; stubs keep collection offline-safe.
    for module_name in ("keyboard", "pyautogui", "pyperclip"):
        if importlib.util.find_spec(module_name) is None:
            sys.modules[module_name] = MagicMock(name=module_name)
    REPORTS.mkdir(exist_ok=True)
    coverage = Coverage(
        branch=True,
        source=[str(ROOT)],
        omit=[str(ROOT / "tests" / "*"), str(ROOT / "run_tests.py")],
        data_file=str(REPORTS / ".coverage"),
    )
    coverage.start()

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=Tee(sys.stdout, output), verbosity=2).run(suite)

    coverage.stop()
    coverage.save()
    with (REPORTS / "coverage.txt").open("w", encoding="utf-8") as report:
        total = coverage.report(
            morfs=[str(ROOT / file_name) for file_name in SOURCE_FILES],
            file=Tee(sys.stdout, report),
            show_missing=True,
        )
    coverage.xml_report(outfile=str(REPORTS / "coverage.xml"))
    coverage.json_report(outfile=str(REPORTS / "coverage.json"))

    summary = f"\nTests run: {result.testsRun}; failures: {len(result.failures)}; errors: {len(result.errors)}; coverage: {total:.2f}%\n"
    print(summary, end="")
    (REPORTS / "test_results.txt").write_text(output.getvalue() + summary, encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
