"""PySide6 desktop dashboard for visualizing AHRS telemetry."""

from __future__ import annotations

import math
import random
import sys
from collections import deque
from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

BG = "#071018"
PANEL = "#0d1924"
PANEL_2 = "#101f2c"
BORDER = "#233747"
TEXT = "#e8f0f5"
MUTED = "#78909f"
CYAN = "#25d9e8"
BLUE = "#4c8dff"
AMBER = "#ffb547"
GREEN = "#43d19e"


@dataclass(slots=True)
class Telemetry:
    """One display-ready AHRS sample."""

    roll: float
    pitch: float
    heading: float
    accel: tuple[float, float, float]
    gyro: tuple[float, float, float]
    mag: tuple[float, float, float]


class AttitudeView(QWidget):
    """Dependency-light wireframe attitude model drawn with QPainter."""

    vertices = (
        (-1.9, 0.0, 0.0),
        (1.9, 0.0, 0.0),
        (0.0, 0.15, -1.15),
        (0.0, 0.15, 0.85),
        (0.0, -0.22, 0.2),
        (0.0, 0.52, 0.2),
    )
    edges = ((0, 1), (0, 2), (1, 2), (2, 3), (3, 4), (2, 5), (3, 5))

    def __init__(self) -> None:
        super().__init__()
        self.roll = self.pitch = self.heading = 0.0
        self.setMinimumHeight(230)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_attitude(self, roll: float, pitch: float, heading: float) -> None:
        self.roll, self.pitch, self.heading = roll, pitch, heading
        self.update()

    def _rotate(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = point
        roll, pitch, yaw = map(
            math.radians, (self.roll, self.pitch, self.heading)
        )
        cr, sr = math.cos(roll), math.sin(roll)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cy, sy = math.cos(yaw), math.sin(yaw)
        y, z = y * cr - z * sr, y * sr + z * cr
        x, z = x * cp + z * sp, -x * sp + z * cp
        return x * cy - y * sy, x * sy + y * cy, z

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PANEL))
        width, height = self.width(), self.height()
        cx, cy = width / 2, height / 2 + 8
        scale = min(width, height) * 0.18

        painter.setPen(QPen(QColor("#172a38"), 1))
        for radius in (0.25, 0.5, 0.75):
            size = min(width, height) * radius
            painter.drawEllipse(QPointF(cx, cy), size / 2, size / 2)
        grid_pen = QPen(QColor(BORDER), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.drawLine(QPointF(24, cy), QPointF(width - 24, cy))
        painter.drawLine(QPointF(cx, 24), QPointF(cx, height - 24))

        points: list[QPointF] = []
        for point in self.vertices:
            x, y, z = self._rotate(point)
            depth = 1 + y * 0.08
            points.append(QPointF(cx + x * scale * depth, cy - z * scale * depth))

        painter.setPen(QPen(QColor(CYAN), 3))
        for start, end in self.edges:
            painter.drawLine(points[start], points[end])
        painter.setBrush(QColor(TEXT))
        for point in points:
            painter.drawEllipse(point, 3, 3)

        painter.setFont(QFont("Sans Serif", 9, QFont.Weight.Bold))
        painter.setPen(QColor(MUTED))
        painter.drawText(20, 28, "ATTITUDE")
        painter.setPen(QColor(CYAN))
        heading_rect = self.rect().adjusted(20, 12, -20, 0)
        painter.drawText(
            heading_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            f"HDG {self.heading:06.1f}°",
        )


class HistoryPlot(QWidget):
    """Scrolling plot for roll, pitch, and heading."""

    def __init__(self, samples: int = 180) -> None:
        super().__init__()
        self.series = {
            "ROLL": (deque(maxlen=samples), CYAN),
            "PITCH": (deque(maxlen=samples), AMBER),
            "HEADING": (deque(maxlen=samples), BLUE),
        }
        self.setMinimumHeight(220)

    def add(self, roll: float, pitch: float, heading: float) -> None:
        for value, (history, _color) in zip(
            (roll, pitch, heading), self.series.values(), strict=True
        ):
            history.append(value)
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(PANEL))
        width, height = self.width(), self.height()
        left, right, top, bottom = 54, width - 20, 42, height - 28
        if right <= left or bottom <= top:
            return

        painter.setFont(QFont("Monospace", 8))
        for degree in (-180, -90, 0, 90, 180):
            y = bottom - (degree + 180) / 360 * (bottom - top)
            painter.setPen(QColor("#1b2d3b"))
            painter.drawLine(left, int(y), right, int(y))
            painter.setPen(QColor(MUTED))
            painter.drawText(
                4,
                int(y) - 8,
                42,
                16,
                Qt.AlignmentFlag.AlignRight,
                f"{degree}°",
            )
        painter.setPen(QColor("#142633"))
        for fraction in (0.25, 0.5, 0.75, 1.0):
            x = int(left + fraction * (right - left))
            painter.drawLine(x, top, x, bottom)

        legend_x = left
        painter.setFont(QFont("Sans Serif", 8, QFont.Weight.Bold))
        for name, (_history, color) in self.series.items():
            painter.setPen(QPen(QColor(color), 3))
            painter.drawLine(legend_x, 20, legend_x + 18, 20)
            painter.setPen(QColor(TEXT))
            painter.drawText(legend_x + 25, 25, name)
            legend_x += 110

        for history, color in self.series.values():
            if len(history) < 2:
                continue
            polygon = QPolygonF()
            for index, value in enumerate(history):
                x = left + index / (history.maxlen - 1) * (right - left)
                wrapped = (value + 180) % 360 - 180
                y = bottom - (wrapped + 180) / 360 * (bottom - top)
                polygon.append(QPointF(x, y))
            painter.setPen(QPen(QColor(color), 2))
            painter.drawPolyline(polygon)


class SensorCard(QFrame):
    def __init__(self, title: str, unit: str, color: str) -> None:
        super().__init__()
        self.setObjectName("sensorCard")
        layout = QGridLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setHorizontalSpacing(18)
        title_label = QLabel(title.upper())
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label, 0, 0, 1, 2)
        unit_label = QLabel(unit)
        unit_label.setObjectName("unit")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(unit_label, 0, 2)
        self.values: list[QLabel] = []
        for column, axis in enumerate("XYZ"):
            axis_label = QLabel(axis)
            axis_label.setObjectName("axis")
            axis_label.setStyleSheet(f"color: {color};")
            axis_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(axis_label, 1, column)
            value_label = QLabel("+0.000")
            value_label.setObjectName("sensorValue")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(value_label, 2, column)
            self.values.append(value_label)

    def set_values(self, values: tuple[float, float, float]) -> None:
        for label, value in zip(self.values, values, strict=True):
            label.setText(f"{value:+.3f}")


class AHRSWindow(QMainWindow):
    """Main AHRS dashboard window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AHRS Control Center")
        self.resize(1120, 820)
        self.setMinimumSize(880, 680)
        self.connected = False
        self.elapsed = 0.0
        self._build_ui()
        self._apply_style()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(100)

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        shell = QVBoxLayout(root)
        shell.setContentsMargins(24, 22, 24, 22)
        shell.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        eyebrow = QLabel("NAVIGATION / LIVE TELEMETRY")
        eyebrow.setObjectName("eyebrow")
        title = QLabel("AHRS Control Center")
        title.setObjectName("title")
        title_box.addWidget(eyebrow)
        title_box.addWidget(title)
        header.addLayout(title_box)
        header.addStretch()
        self.status_label = QLabel("●  OFFLINE")
        self.status_label.setObjectName("status")
        header.addWidget(self.status_label)
        shell.addLayout(header)

        connection = QFrame()
        connection.setObjectName("panel")
        connection_layout = QHBoxLayout(connection)
        connection_layout.setContentsMargins(18, 14, 18, 14)
        connection_layout.setSpacing(10)
        connection_layout.addWidget(self._caption("PORT"))
        self.port = QLineEdit("/dev/ttyUSB0")
        connection_layout.addWidget(self.port, 1)
        connection_layout.addSpacing(10)
        connection_layout.addWidget(self._caption("BAUD"))
        self.baud = QComboBox()
        self.baud.addItems(("9600", "57600", "115200", "230400"))
        self.baud.setCurrentText("115200")
        connection_layout.addWidget(self.baud)
        connection_layout.addSpacing(10)
        self.connect_button = QPushButton("CONNECT")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self._toggle_connection)
        connection_layout.addWidget(self.connect_button)
        shell.addWidget(connection)

        hero = QHBoxLayout()
        hero.setSpacing(12)
        self.attitude = AttitudeView()
        hero.addWidget(self.attitude, 3)
        readouts = QFrame()
        readouts.setObjectName("panel")
        readout_layout = QVBoxLayout(readouts)
        readout_layout.setContentsMargins(28, 22, 28, 22)
        self.readout_labels: dict[str, QLabel] = {}
        colors = {"Roll": CYAN, "Pitch": AMBER, "Heading": BLUE}
        for name in ("Roll", "Pitch", "Heading"):
            caption = self._caption(name.upper())
            value = QLabel("0.0°")
            value.setObjectName("readout")
            value.setStyleSheet(f"color: {colors[name]};")
            readout_layout.addWidget(caption)
            readout_layout.addWidget(value)
            self.readout_labels[name] = value
        readout_layout.addStretch()
        hero.addWidget(readouts, 2)
        shell.addLayout(hero, 3)

        self.plot = HistoryPlot()
        shell.addWidget(self.plot, 2)

        sensor_layout = QHBoxLayout()
        sensor_layout.setSpacing(12)
        self.sensor_cards = {
            "accel": SensorCard("Accelerometer", "m/s²", CYAN),
            "gyro": SensorCard("Gyroscope", "°/s", AMBER),
            "mag": SensorCard("Magnetometer", "µT", BLUE),
        }
        for card in self.sensor_cards.values():
            sensor_layout.addWidget(card, 1)
        shell.addLayout(sensor_layout)

    @staticmethod
    def _caption(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("caption")
        return label

    def _apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; }}
            QFrame#panel, QFrame#sensorCard {{
                background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px;
            }}
            QFrame#sensorCard {{ background: {PANEL_2}; }}
            QLabel#eyebrow {{ color: {CYAN}; font-size: 10px; font-weight: 700; }}
            QLabel#title {{ color: {TEXT}; font-size: 22px; font-weight: 700; }}
            QLabel#status {{ color: {MUTED}; font-size: 11px; font-weight: 700; }}
            QLabel#caption, QLabel#unit {{ color: {MUTED}; font-size: 10px; }}
            QLabel#cardTitle {{ color: {TEXT}; font-size: 10px; font-weight: 700; }}
            QLabel#axis {{ font-size: 10px; font-weight: 700; margin-top: 8px; }}
            QLabel#sensorValue {{
                font-family: monospace; font-size: 14px; font-weight: 700;
            }}
            QLabel#readout {{
                font-family: monospace; font-size: 27px; font-weight: 700;
            }}
            QLineEdit, QComboBox {{
                background: {PANEL_2}; border: 1px solid {BORDER}; border-radius: 5px;
                color: {TEXT}; padding: 8px 10px; selection-background-color: {BLUE};
            }}
            QComboBox QAbstractItemView {{ background: {PANEL_2}; color: {TEXT}; }}
            QPushButton#connectButton {{
                background: {CYAN}; color: {BG}; border: 0; border-radius: 5px;
                padding: 9px 20px; font-size: 10px; font-weight: 700;
            }}
            QPushButton#connectButton:hover {{ background: #77edf4; }}
            """
        )

    def _toggle_connection(self) -> None:
        self.connected = not self.connected
        if self.connected:
            self.status_label.setText("●  STREAMING")
            self.status_label.setStyleSheet(f"color: {GREEN};")
            self.connect_button.setText("DISCONNECT")
        else:
            self.status_label.setText("●  OFFLINE")
            self.status_label.setStyleSheet(f"color: {MUTED};")
            self.connect_button.setText("CONNECT")

    def update_telemetry(self, sample: Telemetry) -> None:
        """Update every dashboard instrument from one telemetry sample."""
        self.attitude.set_attitude(sample.roll, sample.pitch, sample.heading)
        self.plot.add(sample.roll, sample.pitch, sample.heading)
        orientation = (
            ("Roll", sample.roll),
            ("Pitch", sample.pitch),
            ("Heading", sample.heading),
        )
        for name, value in orientation:
            self.readout_labels[name].setText(f"{value:06.1f}°")
        self.sensor_cards["accel"].set_values(sample.accel)
        self.sensor_cards["gyro"].set_values(sample.gyro)
        self.sensor_cards["mag"].set_values(sample.mag)

    def _tick(self) -> None:
        self.elapsed += 0.1
        if not self.connected:
            return
        roll = 18 * math.sin(self.elapsed * 0.7)
        pitch = 9 * math.sin(self.elapsed * 0.45 - 0.8)
        heading = (242 + self.elapsed * 2.8) % 360

        def noise(amount: float) -> float:
            return random.uniform(-amount, amount)

        self.update_telemetry(
            Telemetry(
                roll,
                pitch,
                heading,
                (noise(0.08), noise(0.08), 9.81 + noise(0.06)),
                (noise(0.7), noise(0.7), 2.8 + noise(0.3)),
                (22.4 + noise(0.5), -4.8 + noise(0.5), 41.1 + noise(0.5)),
            )
        )


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("AHRS Control Center")
    window = AHRSWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
