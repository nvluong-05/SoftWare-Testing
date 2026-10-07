import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


def get_app():
    return QApplication.instance() or QApplication(sys.argv[:1])
