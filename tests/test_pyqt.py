import sys

from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AHRS Layout Prototype")
        self.resize(600, 520)
        self._build_ui()
        self._connect_actions()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        layout.addWidget(self._create_connection_section())
        layout.addWidget(self._create_data_section())
        layout.addWidget(self._create_log_section())

    def _create_connection_section(self) -> QWidget:
        section = QWidget()
        section.setLayout(QGridLayout())
        section.layout().setContentsMargins(10, 10, 10, 10)
        section.layout().setHorizontalSpacing(12)
        section.layout().setVerticalSpacing(8)

        section.layout().addWidget(QLabel("Connection"), 0, 0, 1, 2)
        section.layout().addWidget(QLabel("Port:"), 1, 0)
        self.port_input = QLineEdit("/dev/ttyUSB0")
        section.layout().addWidget(self.port_input, 1, 1)
        section.layout().addWidget(QLabel("Baud:"), 2, 0)
        self.baud_input = QLineEdit("115200")
        section.layout().addWidget(self.baud_input, 2, 1)
        self.connect_button = QPushButton("Connect")
        section.layout().addWidget(self.connect_button, 3, 0, 1, 2)
        return section

    def _create_data_section(self) -> QWidget:
        section = QWidget()
        section.setLayout(QGridLayout())
        section.layout().setContentsMargins(10, 10, 10, 10)
        section.layout().setHorizontalSpacing(12)
        section.layout().setVerticalSpacing(8)

        section.layout().addWidget(QLabel("Data Display"), 0, 0, 1, 2)
        self.roll_label = QLabel("Roll: 0.00°")
        self.pitch_label = QLabel("Pitch: 0.00°")
        self.heading_label = QLabel("Heading: 0.00°")
        self.accel_label = QLabel("Accel: 0.00, 0.00, 0.00")
        section.layout().addWidget(self.roll_label, 1, 0)
        section.layout().addWidget(self.pitch_label, 1, 1)
        section.layout().addWidget(self.heading_label, 2, 0)
        section.layout().addWidget(self.accel_label, 2, 1)
        return section

    def _create_log_section(self) -> QWidget:
        section = QWidget()
        section.setLayout(QVBoxLayout())
        section.layout().setContentsMargins(10, 10, 10, 10)
        section.layout().setSpacing(8)

        section.layout().addWidget(QLabel("Event Log"))
        self.log_view = QListWidget()
        self.log_view.addItems(["Ready."])
        section.layout().addWidget(self.log_view)
        return section

    def _connect_actions(self) -> None:
        self.connect_button.clicked.connect(self._toggle_connection)

    def _toggle_connection(self) -> None:
        if self.connect_button.text() == "Connect":
            self.connect_button.setText("Disconnect")
            self.log_view.addItem("Connected to sensor.")
        else:
            self.connect_button.setText("Connect")
            self.log_view.addItem("Disconnected.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
