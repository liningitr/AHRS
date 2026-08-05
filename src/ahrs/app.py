"""Application entrypoint for the AHRS dashboard."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from ahrs.ahrs_ui import AHRSWindow


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("AHRS Control Center")
    window = AHRSWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
