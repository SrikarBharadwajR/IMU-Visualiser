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
    QFrame,
    QTabWidget,
    QCheckBox,
)
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QQuaternion
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QTimer, pyqtSignal
import os

# Import modular components
from stylesheets import (
    DARK_STYLE,
    LIGHT_STYLE,
    DARK_GREEN,
    DARK_RED,
    LIGHT_GREEN,
    LIGHT_RED,
)
from connection_workers import SerialWorker, UdpWorker
from pyvista_widget import PyVistaWidget
from logger_widget import LoggerWidget


class StatusIndicator(QWidget):
    """A custom widget to display a colored status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self._status = "error"
        self._is_dark = True

        # Define colors for both themes
        self.dark_colors = {
            "ok": QColor(DARK_GREEN),
            "error": QColor(DARK_RED),
            "connecting": QColor("#F9E2AF"),  # Yellow
        }
        self.light_colors = {
            "ok": QColor(LIGHT_GREEN),
            "error": QColor(LIGHT_RED),
            "connecting": QColor("#EE9928"),  # Orange
        }
        self.current_colors = self.dark_colors

    def set_theme(self, is_dark):
        """Updates the color palette based on the theme."""
        self._is_dark = is_dark
        self.current_colors = self.dark_colors if is_dark else self.light_colors
        self.update()  # Trigger a repaint with the new colors

    def setStatus(self, status):
        """Sets the status and triggers a repaint."""
        if status in self.current_colors:
            self._status = status
            self.update()  # Schedule a repaint

    def paintEvent(self, event):
        """Paints the status circle."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.current_colors.get(self._status, QColor("#808080"))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        # Draw a circle in the center of the widget, with a small margin
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawEllipse(rect)


class IMUVisualiser(QMainWindow):
    # Signal to send log data: (log_line, was_parsed_successfully)
    log_entry_created = pyqtSignal(str, bool)

    def __init__(self):
        super().__init__()

        self.preferences = self.load_preferences()

        self.setWindowTitle("IMU 3D Visualiser")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("icon.png"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.connection_worker = None
        self.is_dark_theme = self.preferences.get("theme", "dark") == "dark"
        self.last_data_time = time.time()
        self.data_update_count = 0
        self.last_packet_timestamp = 0

        # Store the latest quaternion data here
        self.current_quaternion = QQuaternion(1, 0, 0, 0)
        self.new_data_available = False

        # --- Connection Timeout Timer ---
        self.connection_timeout_timer = QTimer(self)
        self.connection_timeout_timer.setInterval(1000)  # Check every second
        self.connection_timeout_timer.timeout.connect(self.check_connection_timeout)

        # --- Render Timer ---
        self.render_timer = QTimer(self)
        self.render_timer.setInterval(16)  # Target ~60 FPS for rendering
        self.render_timer.timeout.connect(self.update_gl_and_ui)

        self._init_ui()
        self.apply_theme()
        self.refresh_ports()

        # Connect the logger signal
        self.log_entry_created.connect(self.logger_widget.add_log_entry)

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
        # Use the new PyVistaWidget
        self.gl_widget = PyVistaWidget(self)
        vis_layout.addWidget(self.gl_widget)
        self.main_splitter.addWidget(vis_group)

        # --- Right Pane (Data Display Tabs) ---
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self._create_data_display_tabs(right_layout)
        self.main_splitter.addWidget(right_pane)

        main_layout.addWidget(self.main_splitter, 1)

    def showEvent(self, event):
        """Called when the window is first shown."""
        # Apply splitter sizes *after* the window is shown and has geometry
        splitter_sizes = self.preferences.get("splitter_sizes", [750, 450])
        if (
            splitter_sizes
            and len(splitter_sizes) == 2
            and all(s > 0 for s in splitter_sizes)
        ):
            self.main_splitter.setSizes(splitter_sizes)

        # Call the base class implementation
        super().showEvent(event)

    def _create_top_bar(self):
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 10, 0, 0)

        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        self.logo_label.setPixmap(
            pixmap.scaled(120, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        top_bar_layout.addWidget(self.logo_label)
        top_bar_layout.addSpacing(50)

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
        group = QGroupBox("Connections")
        layout = QHBoxLayout(group)
        layout.setSpacing(10)

        # --- Test Mode Checkbox ---
        self.test_mode_check = QCheckBox("Test Mode")
        self.test_mode_check.setToolTip(
            "Bypass serial and listen for UDP test data on 127.0.0.1:12345"
        )
        self.test_mode_check.toggled.connect(self.on_test_mode_toggled)
        layout.addWidget(self.test_mode_check)
        layout.addSpacing(10)

        # --- Serial Port Widgets ---
        self.serial_port_label = QLabel("Port:")
        layout.addWidget(self.serial_port_label)
        self.port_combo = QComboBox()
        layout.addWidget(self.port_combo)

        layout.addSpacing(5)

        self.serial_baud_label = QLabel("Baud Rate:")
        layout.addWidget(self.serial_baud_label)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(
            [
                "9600",
                "19200",
                "38400",
                "57600",
                "115200",
                "230400",
                "460800",
                "921600",
                "1000000",
            ]
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

        # Store serial-only widgets
        self.serial_widgets = [
            self.serial_port_label,
            self.port_combo,
            self.serial_baud_label,
            self.baud_combo,
            self.refresh_ports_button,
        ]

        # --- Test Mode Widgets ---
        self.test_port_label = QLabel("Listening on: 127.0.0.1:12345 (UDP)")
        layout.addWidget(self.test_port_label)
        self.test_port_label.setVisible(False)  # Hide by default

        # Connect Button
        self.connect_button = QPushButton("Connect")
        self.connect_button.setMinimumWidth(100)
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        layout.addSpacing(15)

        # --- Status Indicator and Labels ---
        self.status_indicator = StatusIndicator()
        layout.addWidget(self.status_indicator)

        self.info_label = QLabel()
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)

        # Set initial values
        self.set_info_label("Disconnected", "error")

        return group

    def _create_data_display_tabs(self, parent_layout):
        tab_widget = QTabWidget()

        # --- Processed Data Tab ---
        processed_tab = QWidget()
        processed_layout = QVBoxLayout(processed_tab)
        processed_layout.setAlignment(Qt.AlignTop)

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

        processed_layout.addLayout(data_row_layout)
        tab_widget.addTab(processed_tab, "Processed Data")

        # --- Raw Serial Log Tab ---
        logger_prefs = self.preferences.get("logger", {})
        self.logger_widget = LoggerWidget(logger_prefs)
        tab_widget.addTab(self.logger_widget, "Raw Serial Logs")

        parent_layout.addWidget(tab_widget)

    def set_serial_controls_enabled(self, enabled):
        """Helper to enable/disable serial-specific controls."""
        for widget in self.serial_widgets:
            widget.setEnabled(enabled)

    @pyqtSlot(bool)
    def on_test_mode_toggled(self, is_checked):
        """Shows/hides UI elements based on Test Mode state."""
        # Show/hide serial vs test widgets
        for widget in self.serial_widgets:
            widget.setVisible(not is_checked)
        self.test_port_label.setVisible(is_checked)

        # If a connection is active, toggle it off
        if self.connection_worker and self.connection_worker.isRunning():
            self.toggle_connection()

        # Update connect button text
        self.connect_button.setText("Start Test" if is_checked else "Connect")
        self.set_info_label("Disconnected", "error")

    def set_info_label(self, text, status_type):
        self.info_label.setText(text)
        self.status_indicator.setStatus(status_type)

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
        if self.connection_worker and self.connection_worker.isRunning():
            self.connection_worker.stop()
            self.connection_timeout_timer.stop()
            self.render_timer.stop()
        else:
            is_test_mode = self.test_mode_check.isChecked()

            if is_test_mode:
                # --- Start Test (UDP) Worker ---
                self.connect_button.setText("Stop Test")
                self.set_info_label("Listening (UDP)...", "connecting")
                self.connection_worker = UdpWorker(listen_port=12345)

            else:
                # --- Start Serial Worker ---
                port_name = self.port_combo.currentText()
                if not port_name:
                    self.set_info_label("No port selected!", "error")
                    return

                baud_rate = int(self.baud_combo.currentText())
                self.connect_button.setText("Disconnect")
                self.set_info_label("Connecting...", "connecting")
                self.set_serial_controls_enabled(False)

                self.connection_worker = SerialWorker(port_name, baud_rate)

            # --- Common Worker Setup ---
            self.connection_worker.line_received.connect(self.handle_received_line)
            self.connection_worker.error_occurred.connect(self.handle_serial_error)
            self.connection_worker.finished.connect(self.on_worker_finished)
            self.connection_worker.start()

            self.last_data_time = time.time()
            self.data_update_count = 0
            self.render_timer.start()

    def check_connection_timeout(self):
        """Called by QTimer to check for stale data."""
        if self.connection_worker and self.connection_worker.isRunning():
            # Check if more than 2 seconds have passed since the last packet
            if time.time() - self.last_packet_timestamp > 2.0:
                self.render_timer.stop()
                self.handle_serial_error("Connection timed out")

    @pyqtSlot(str)
    def handle_serial_error(self, error_message):
        self.connection_timeout_timer.stop()
        self.render_timer.stop()
        self.set_info_label(error_message, "error")
        if self.connection_worker and self.connection_worker.isRunning():
            self.connection_worker.stop()

    @pyqtSlot()
    def on_worker_finished(self):
        self.connection_timeout_timer.stop()
        self.render_timer.stop()

        # Update button text based on mode
        is_test_mode = self.test_mode_check.isChecked()
        self.connect_button.setText("Start Test" if is_test_mode else "Connect")

        # Only change status if it wasn't already set to an error
        if self.status_indicator._status != "error":
            self.set_info_label("Disconnected", "error")

        if not is_test_mode:
            self.set_serial_controls_enabled(True)

        self.connection_worker = None

    @pyqtSlot(str)
    def handle_received_line(self, line):
        # Update timestamp on every packet to reset the timeout
        self.last_packet_timestamp = time.time()

        # If this is the first packet, change status and start the timeout timer
        if self.status_indicator._status == "connecting":
            self.set_info_label("Connected", "ok")
            self.connection_timeout_timer.start()

        parsed_successfully = False
        try:
            parts = [float(p.strip()) for p in line.split(",")]
            if len(parts) == 4:
                q0, q1, q2, q3 = parts
                norm = np.sqrt(q0**2 + q1**2 + q2**2 + q3**2)
                if norm > 1e-6:
                    q0, q1, q2, q3 = q0 / norm, q1 / norm, q2 / norm, q3 / norm

                    self.current_quaternion.setScalar(q0)
                    self.current_quaternion.setX(q1)
                    self.current_quaternion.setY(q2)
                    self.current_quaternion.setZ(q3)
                    self.new_data_available = True

                    self.data_update_count += 1
                    parsed_successfully = True

        except (ValueError, IndexError):
            # This line could not be parsed as quaternion data
            pass

        # Emit the log entry signal for the logger widget regardless of parse success
        self.log_entry_created.emit(line, parsed_successfully)

    @pyqtSlot()
    def update_gl_and_ui(self):
        """
        This slot is called by the render_timer and handles ALL UI updates.
        """
        if self.new_data_available:
            self.gl_widget.set_rotation_from_quat(self.current_quaternion)
            # PyVista's QtInteractor needs render() to be called
            self.gl_widget.render()
            self.update_data_labels(self.current_quaternion)
            self.new_data_available = False

        # self.update_refresh_rate()

    def update_data_labels(self, q: QQuaternion):
        """Updates all text labels based on the quaternion."""
        self.q0_label.setText(f"q0 (W): {q.scalar():.4f}")
        self.q1_label.setText(f"q1 (X): {q.x():.4f}")
        self.q2_label.setText(f"q2 (Y): {q.y():.4f}")
        self.q3_label.setText(f"q3 (Z): {q.z():.4f}")

        # Calculate and update Euler angles
        w, x, y, z = q.scalar(), q.x(), q.y(), q.z()
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

    def apply_theme(self):
        self.setStyleSheet(DARK_STYLE if self.is_dark_theme else LIGHT_STYLE)
        self.gl_widget.set_theme(self.is_dark_theme)
        self.theme_button.setText("☀️" if self.is_dark_theme else "🌙")

        # Update status indicator theme if it has been created
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_theme(self.is_dark_theme)

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
            "logger": self.logger_widget.get_settings(),
        }
        with open("preferences.json", "w") as f:
            json.dump(prefs, f, indent=4)

    def closeEvent(self, event):
        self.save_preferences()
        if self.connection_worker and self.connection_worker.isRunning():
            self.connection_worker.stop()
        event.accept()


if __name__ == "__main__":
    if sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # PyVista/VTK can have issues with styling, setting this env var can help
    os.environ["QT_STYLE_OVERRIDE"] = ""

    # Must construct QApplication *before* PyVista widget
    app = QApplication(sys.argv)
    window = IMUVisualiser()
    window.show()
    sys.exit(app.exec_())
