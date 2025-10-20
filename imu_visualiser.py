# main_app.py
# The main application entry point. This file brings all modules together.

import sys
import time
import json
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QGridLayout,
    QGroupBox,
    QSplitter,
    QStyle,
    QSizePolicy,
)
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSlot

# Import modular components
from stylesheets import DARK_STYLE, LIGHT_STYLE
from serial_worker import SerialWorker
from gl_widget import OpenGLCubeWidget


class IMUVisualiser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.preferences = self.load_preferences()

        self.setWindowTitle("IMU 3D Visualiser")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("icon.png"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.serial_worker = None
        self.is_dark_theme = self.preferences.get("theme", "dark") == "dark"
        self.last_data_time = time.time()
        self.data_update_count = 0

        self._init_ui()
        self.apply_theme()
        self.refresh_ports()

    def _init_ui(self):
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Top Bar (Logo, Controls, Theme) ---
        top_bar_layout = self._create_top_bar()
        main_layout.addLayout(top_bar_layout)

        # --- Main Content Splitter ---
        self.main_splitter = QSplitter(Qt.Horizontal)

        # --- Left Pane (Visualisation with Border) ---
        vis_group = QGroupBox("3D Visualisation")
        vis_group.setObjectName("VisualisationBox")
        vis_layout = QVBoxLayout(vis_group)
        vis_layout.setContentsMargins(5, 15, 5, 5)
        self.gl_widget = OpenGLCubeWidget(self)
        vis_layout.addWidget(self.gl_widget)
        self.main_splitter.addWidget(vis_group)

        # --- Right Pane (Data Display) ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self._create_data_display(right_layout)
        right_layout.addStretch()
        self.main_splitter.addWidget(right_pane)

        # IMPORTANT: Set splitter sizes AFTER widgets have been added
        splitter_sizes = self.preferences.get("splitter_sizes", [750, 450])
        if (
            splitter_sizes
            and len(splitter_sizes) == 2
            and all(s > 0 for s in splitter_sizes)
        ):
            self.main_splitter.setSizes(splitter_sizes)

        main_layout.addWidget(self.main_splitter, 1)

    def _create_top_bar(self):
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        self.logo_label.setPixmap(
            pixmap.scaled(120, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        top_bar_layout.addWidget(self.logo_label)
        top_bar_layout.addSpacing(15)

        # Serial Port Controls
        serial_group = self._create_serial_controls()
        serial_group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        top_bar_layout.addWidget(serial_group)

        top_bar_layout.addStretch()

        # Theme button
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(QSize(45, 40))
        self.theme_button.setToolTip("Toggle light/dark theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        top_bar_layout.addWidget(self.theme_button)

        return top_bar_layout

    def _create_serial_controls(self):
        group = QGroupBox("Serial Connections")
        layout = QHBoxLayout(group)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        layout.addWidget(self.port_combo)

        layout.addSpacing(5)

        layout.addWidget(QLabel("Baud Rate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(
            ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        )
        self.baud_combo.setCurrentText(self.preferences.get("last_baud", "115200"))
        layout.addWidget(self.baud_combo)

        # Refresh Button
        self.refresh_ports_button = QPushButton()
        self.refresh_ports_button.setIconSize(QSize(20, 20))
        self.refresh_ports_button.setFixedWidth(28)
        self.refresh_ports_button.setObjectName("refreshButton")
        self.refresh_ports_button.setToolTip("Refresh available serial ports")
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        layout.addWidget(self.refresh_ports_button)

        # Connect Button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setMinimumWidth(100)
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        # Status "mini box" - now a styled QWidget, not QGroupBox
        status_box = QWidget()
        status_box.setObjectName("statusBox")
        status_layout = QHBoxLayout(status_box)
        status_layout.setContentsMargins(8, 5, 8, 5)
        status_layout.setSpacing(15)

        self.info_label = QLabel("Status: Disconnected")
        self.info_label.setObjectName("infoLabel")
        self.set_info_label("Disconnected", "error")
        status_layout.addWidget(self.info_label)

        self.rate_label = QLabel("Rate: 0.0 Hz")
        self.rate_label.setObjectName("rateLabel")
        status_layout.addWidget(self.rate_label)
        layout.addWidget(status_box)

        return group

    def _create_data_display(self, layout):
        data_row_layout = QHBoxLayout()

        quat_group = QGroupBox("Quaternion Data")
        quat_layout = QVBoxLayout(quat_group)
        self.q0_label = QLabel("q0 (W): N/A")
        self.q1_label = QLabel("q1 (X): N/A")
        self.q2_label = QLabel("q2 (Y): N/A")
        self.q3_label = QLabel("q3 (Z): N/A")
        quat_layout.addWidget(self.q0_label)
        quat_layout.addWidget(self.q1_label)
        quat_layout.addWidget(self.q2_label)
        quat_layout.addWidget(self.q3_label)
        data_row_layout.addWidget(quat_group)

        euler_group = QGroupBox("Euler Angles")
        euler_layout = QVBoxLayout(euler_group)
        self.roll_label = QLabel("Roll: N/A")
        self.pitch_label = QLabel("Pitch: N/A")
        self.yaw_label = QLabel("Yaw: N/A")
        euler_layout.addWidget(self.roll_label)
        euler_layout.addWidget(self.pitch_label)
        euler_layout.addWidget(self.yaw_label)
        data_row_layout.addWidget(euler_group)

        layout.addLayout(data_row_layout)

    def set_info_label(self, text, status_type):
        self.info_label.setText(f"Status: {text}")
        self.info_label.setProperty("status", status_type)
        self.style().unpolish(self.info_label)
        self.style().polish(self.info_label)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = QSerialPortInfo.availablePorts()
        ports.sort(
            key=lambda p: "USB" in p.portName().upper()
            or "ACM" in p.portName().upper(),
            reverse=True,
        )
        port_names = [port.portName() for port in ports]
        self.port_combo.addItems(port_names)
        if port_names:
            self.port_combo.setCurrentIndex(0)

    def toggle_connection(self):
        if self.serial_worker and self.serial_worker.isRunning():
            self.serial_worker.stop()
        else:
            port_name = self.port_combo.currentText()
            if not port_name:
                self.set_info_label("No port selected!", "error")
                return

            baud_rate = int(self.baud_combo.currentText())
            self.connect_button.setText("Disconnect")
            self.set_info_label(f"Connecting...", "connecting")

            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.refresh_ports_button.setEnabled(False)

            self.serial_worker = SerialWorker(port_name, baud_rate)
            self.serial_worker.data_received.connect(self.update_data)
            self.serial_worker.error_occurred.connect(self.handle_serial_error)
            self.serial_worker.finished.connect(self.on_worker_finished)
            self.serial_worker.start()

            self.last_data_time = time.time()
            self.data_update_count = 0

    @pyqtSlot(str)
    def handle_serial_error(self, error_message):
        self.set_info_label(error_message, "error")
        if self.serial_worker and self.serial_worker.isRunning():
            self.serial_worker.stop()

    @pyqtSlot()
    def on_worker_finished(self):
        self.connect_button.setText("Connect")
        if self.info_label.property("status") != "error":
            self.set_info_label("Disconnected", "error")

        self.rate_label.setText("Rate: 0.0 Hz")
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)
        self.refresh_ports_button.setEnabled(True)
        self.serial_worker = None

    @pyqtSlot(str)
    def update_data(self, data):
        try:
            if "Connecting" in self.info_label.text():
                self.set_info_label("Connected", "ok")

            parts = [float(p.strip()) for p in data.split(",")]
            if len(parts) == 4:
                q0, q1, q2, q3 = parts
                norm = np.sqrt(q0**2 + q1**2 + q2**2 + q3**2)
                if norm < 1e-6:
                    return
                q0, q1, q2, q3 = q0 / norm, q1 / norm, q2 / norm, q3 / norm

                self.gl_widget.update_rotation(q0, q1, q2, q3)
                self.q0_label.setText(f"q0 (W): {q0:.4f}")
                self.q1_label.setText(f"q1 (X): {q1:.4f}")
                self.q2_label.setText(f"q2 (Y): {q2:.4f}")
                self.q3_label.setText(f"q3 (Z): {q3:.4f}")
                self.update_euler_angles(q0, q1, q2, q3)
                self.update_refresh_rate()

        except (ValueError, IndexError):
            print(f"Warning: Could not parse serial data: {data}")
            pass

    def update_euler_angles(self, w, x, y, z):
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        sinp = 2 * (w * y - z * x)
        pitch = np.arcsin(sinp) if abs(sinp) < 1 else np.copysign(np.pi / 2, sinp)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        self.roll_label.setText(f"Roll: {np.degrees(roll):.2f}°")
        self.pitch_label.setText(f"Pitch: {np.degrees(pitch):.2f}°")
        self.yaw_label.setText(f"Yaw: {np.degrees(yaw):.2f}°")

    def update_refresh_rate(self):
        self.data_update_count += 1
        current_time = time.time()
        time_diff = current_time - self.last_data_time
        if time_diff >= 1.0:
            rate = self.data_update_count / time_diff
            self.rate_label.setText(f"Rate: {rate:.1f} Hz")
            self.last_data_time = current_time
            self.data_update_count = 0

    def apply_theme(self):
        self.setStyleSheet(DARK_STYLE if self.is_dark_theme else LIGHT_STYLE)
        self.gl_widget.set_theme(self.is_dark_theme)
        self.theme_button.setText("☀️" if self.is_dark_theme else "🌙")

        # Recolor refresh icon to be light/contrasting for the button background
        style = self.style()
        icon = style.standardIcon(QStyle.SP_BrowserReload)
        pixmap = icon.pixmap(QSize(24, 24))

        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        # Use a light color that works on the blue button
        painter.fillRect(pixmap.rect(), QColor("#FFFFFF"))
        painter.end()

        self.refresh_ports_button.setIcon(QIcon(pixmap))

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def load_preferences(self):
        try:
            with open("preferences.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_preferences(self):
        prefs = {
            "theme": "dark" if self.is_dark_theme else "light",
            "last_baud": self.baud_combo.currentText(),
            "splitter_sizes": self.main_splitter.sizes(),
        }
        with open("preferences.json", "w") as f:
            json.dump(prefs, f, indent=4)

    def closeEvent(self, event):
        self.save_preferences()
        if self.serial_worker and self.serial_worker.isRunning():
            self.serial_worker.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IMUVisualiser()
    window.show()
    sys.exit(app.exec_())
