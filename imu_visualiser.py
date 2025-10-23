# main_app.py
# The main application entry point. This file brings all modules together.

import sys
import time
import json
import struct
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QStackedWidget,
)
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtGui import QIcon, QQuaternion
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal
import os

# Import modular components
from stylesheets import DARK_STYLE, LIGHT_STYLE
from connection_workers import SerialWorker, UdpWorker
from pyvista_widget import PyVistaWidget
from logger_widget import LoggerWidget
from ui_components import (
    ImuVisualiserPanel,
    TopBarWidget,
    FeedbackWidget,
    ImuGridWidget,
)


class IMUVisualiser(QMainWindow):
    # Signal to send log data: (log_line, was_parsed_successfully)
    log_entry_created = pyqtSignal(str, bool)
    # Expected binary format: <Bffff (1 byte IMU ID, 4 floats)
    PACKET_FORMAT = "<Bffff"
    PACKET_SIZE = struct.calcsize(PACKET_FORMAT)

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
        self.last_packet_timestamp = 0

        # Store data for multiple IMUs
        self.vis_widgets = {}  # {imu_id: PyVistaWidget}
        self.vis_panels = {}  # {imu_id: ImuVisualiserPanel}
        self.imu_data = {}  # {imu_id: QQuaternion}
        self.new_data_imu_ids = set()

        # --- Timers ---
        self.connection_timeout_timer = QTimer(self)
        self.connection_timeout_timer.setInterval(1000)  # Check every second
        self.connection_timeout_timer.timeout.connect(self.check_connection_timeout)

        self.render_timer = QTimer(self)
        self.render_timer.setInterval(16)  # Target ~60 FPS
        self.render_timer.timeout.connect(self.update_gl_and_ui)

        self._init_ui()
        self.apply_theme()
        self.refresh_ports()

        # Connect signals
        self.log_entry_created.connect(self.logger_widget.add_log_entry)
        self.connect_ui_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Top Bar (Logo, Controls, Theme) ---
        self.top_bar = TopBarWidget(self)
        main_layout.addWidget(self.top_bar)  # <-- This was the fix from last time

        # --- Main Content Splitter ---
        self.main_splitter = QSplitter(Qt.Horizontal)

        # --- Left Pane (Visualisation Display Stack) ---
        self.display_stack = QStackedWidget()
        self.vis_tab_widget = QTabWidget()
        self.vis_grid_widget = ImuGridWidget()
        self.display_stack.addWidget(self.vis_tab_widget)
        self.display_stack.addWidget(self.vis_grid_widget)
        self.main_splitter.addWidget(self.display_stack)

        # --- Right Pane (Data Display Tabs) ---
        self.right_tab_widget = QTabWidget()
        self.feedback_widget = FeedbackWidget()
        logger_prefs = self.preferences.get("logger", {})
        self.logger_widget = LoggerWidget(logger_prefs)
        self.right_tab_widget.addTab(self.feedback_widget, "Processed Data")
        self.right_tab_widget.addTab(self.logger_widget, "Raw Serial Logs")
        self.main_splitter.addWidget(self.right_tab_widget)

        main_layout.addWidget(self.main_splitter, 1)

    def connect_ui_signals(self):
        """Connect all UI signals to their slots."""
        conn_widget = self.top_bar.connection_widget
        disp_widget = self.top_bar.imu_display_widget

        # Top Bar
        self.top_bar.theme_button.clicked.connect(self.toggle_theme)

        # Connection Widget
        conn_widget.test_mode_check.toggled.connect(self.on_test_mode_toggled)
        conn_widget.refresh_ports_button.clicked.connect(self.refresh_ports)
        conn_widget.connect_button.clicked.connect(self.toggle_connection)

        # Set saved baud rate
        conn_widget.baud_combo.setCurrentText(
            self.preferences.get("last_baud", "115200")
        )

        # IMU Display Widget
        disp_widget.club_tabs_checkbox.toggled.connect(self.on_club_tabs_toggled)

        # Feedback Widget
        self.feedback_widget.imu_select_combo.currentIndexChanged.connect(
            self.update_feedback_display
        )

    def showEvent(self, event):
        """Called when the window is first shown."""
        splitter_sizes = self.preferences.get("splitter_sizes", [750, 450])
        if (
            splitter_sizes
            and len(splitter_sizes) == 2
            and all(s > 0 for s in splitter_sizes)
        ):
            self.main_splitter.setSizes(splitter_sizes)
        super().showEvent(event)

    def set_serial_controls_enabled(self, enabled):
        """Helper to enable/disable serial-specific controls."""
        for widget in self.top_bar.connection_widget.serial_widgets:
            widget.setEnabled(enabled)

    @pyqtSlot(bool)
    def on_test_mode_toggled(self, is_checked):
        """Shows/hides UI elements based on Test Mode state."""
        conn_widget = self.top_bar.connection_widget
        for widget in conn_widget.serial_widgets:
            widget.setVisible(not is_checked)
        conn_widget.test_port_label.setVisible(is_checked)

        if self.connection_worker and self.connection_worker.isRunning():
            self.toggle_connection()

        conn_widget.connect_button.setText("Start Test" if is_checked else "Connect")
        self.set_info_label("Disconnected", "error")

    @pyqtSlot(bool)
    def on_club_tabs_toggled(self, is_checked):
        """
        Switches between the tab view and the grid view,
        moving all PyVista widgets to the correct container.
        """
        if is_checked:
            # Move from TABS to GRID PANELS
            for imu_id in sorted(self.vis_widgets.keys()):
                if imu_id in self.vis_panels:
                    widget = self.vis_widgets[imu_id]
                    panel = self.vis_panels[imu_id]
                    index = self.vis_tab_widget.indexOf(widget)
                    if index != -1:
                        self.vis_tab_widget.removeTab(index)
                    # This automatically detaches from tab widget
                    panel.set_vis_widget(widget)

            self.display_stack.setCurrentWidget(self.vis_grid_widget)
        else:
            # Move from GRID PANELS to TABS
            for imu_id in sorted(self.vis_widgets.keys()):
                if imu_id in self.vis_panels:
                    panel = self.vis_panels[imu_id]
                    widget = panel.clear_vis_widget()  # Detaches from panel
                    if widget:
                        self.vis_tab_widget.addTab(widget, f"IMU {imu_id}")
                        widget.show()

            self.display_stack.setCurrentWidget(self.vis_tab_widget)

    def set_info_label(self, text, status_type):
        conn_widget = self.top_bar.connection_widget
        conn_widget.info_label.setText(text)
        conn_widget.status_indicator.setStatus(status_type)

    def refresh_ports(self):
        port_combo = self.top_bar.connection_widget.port_combo
        port_combo.clear()
        ports = QSerialPortInfo.availablePorts()
        ports.sort(
            key=lambda p: "USB" in p.portName().upper()
            or "ACM" in p.portName().upper(),
            reverse=True,
        )
        port_names = [port.portName() for port in ports]
        port_combo.addItems(port_names)
        if port_names:
            port_combo.setCurrentIndex(0)

    def clear_imu_widgets(self):
        """
        Clears all IMU-related widgets and data.
        """
        # Clear containers first
        self.vis_tab_widget.clear()  # Detaches widgets if in tab view
        self.vis_grid_widget.clear_widgets()  # Detaches panels
        self.feedback_widget.imu_select_combo.clear()
        self.feedback_widget.clear_labels()

        # Delete the panels
        for panel in self.vis_panels.values():
            panel.clear_vis_widget()  # Detach vis_widget if in grid view
            panel.setParent(None)
            panel.deleteLater()
        self.vis_panels.clear()

        # Delete the PyVista widgets
        for widget in self.vis_widgets.values():
            widget.setParent(None)  # Explicitly detach
            widget.deleteLater()  # Ensure proper cleanup

        self.vis_widgets.clear()
        self.imu_data.clear()
        self.new_data_imu_ids.clear()

    def toggle_connection(self):
        conn_widget = self.top_bar.connection_widget
        disp_widget = self.top_bar.imu_display_widget

        if self.connection_worker and self.connection_worker.isRunning():
            # --- DISCONNECT ---
            self.connection_worker.stop()
            self.connection_timeout_timer.stop()
            self.render_timer.stop()
            self.clear_imu_widgets()
        else:
            # --- CONNECT ---
            self.clear_imu_widgets()
            num_imus = disp_widget.imu_count_spinbox.value()
            for i in range(num_imus):
                self.add_new_imu(i)  # This will now correctly populate the current view

            disp_widget.imu_count_spinbox.setEnabled(False)
            is_test_mode = conn_widget.test_mode_check.isChecked()

            if is_test_mode:
                self.connection_worker = UdpWorker(listen_port=12345)
                conn_widget.connect_button.setText("Stop Test")
                self.set_info_label("Listening (UDP)...", "connecting")
            else:
                port_name = conn_widget.port_combo.currentText()
                if not port_name:
                    self.set_info_label("No port selected!", "error")
                    disp_widget.imu_count_spinbox.setEnabled(True)
                    return
                baud_rate = int(conn_widget.baud_combo.currentText())
                self.connection_worker = SerialWorker(port_name, baud_rate)
                conn_widget.connect_button.setText("Disconnect")
                self.set_info_label("Connecting...", "connecting")
                self.set_serial_controls_enabled(False)

            # --- Common Worker Setup ---
            if is_test_mode:
                self.connection_worker.packet_received.connect(
                    self.handle_received_packet
                )
            else:
                self.connection_worker.line_received.connect(self.handle_received_line)
            self.connection_worker.error_occurred.connect(self.handle_serial_error)
            self.connection_worker.finished.connect(self.on_worker_finished)
            self.connection_worker.start()

            self.last_packet_timestamp = time.time()
            self.render_timer.start()

    def check_connection_timeout(self):
        if self.connection_worker and self.connection_worker.isRunning():
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

        conn_widget = self.top_bar.connection_widget
        is_test_mode = conn_widget.test_mode_check.isChecked()
        conn_widget.connect_button.setText("Start Test" if is_test_mode else "Connect")

        if conn_widget.status_indicator._status != "error":
            self.set_info_label("Disconnected", "error")

        self.top_bar.imu_display_widget.imu_count_spinbox.setEnabled(True)
        if not is_test_mode:
            self.set_serial_controls_enabled(True)

        self.connection_worker = None

    def add_new_imu(self, imu_id):
        """
        Creates UI elements and adds them to both views.
        """
        if imu_id in self.vis_widgets:
            return  # Already exists

        print(f"Adding UI for IMU: {imu_id}")
        self.imu_data[imu_id] = QQuaternion(1, 0, 0, 0)

        # 1. Create the PyVista widget
        new_vis_widget = PyVistaWidget(self)
        new_vis_widget.set_theme(self.is_dark_theme)
        self.vis_widgets[imu_id] = new_vis_widget

        # 2. Create the panel for the grid view
        new_panel = ImuVisualiserPanel(imu_id)
        self.vis_panels[imu_id] = new_panel
        # Add the panel to the grid widget
        self.vis_grid_widget.add_widget(new_panel)

        # 3. Add to feedback dropdown
        self.feedback_widget.imu_select_combo.addItem(f"IMU {imu_id}", userData=imu_id)

        # 4. Add the PyVista widget to the *default* container (tabs)
        # (or grid if 'clubbed' is already checked)
        if self.top_bar.imu_display_widget.club_tabs_checkbox.isChecked():
            new_panel.set_vis_widget(new_vis_widget)
        else:
            self.vis_tab_widget.addTab(new_vis_widget, f"IMU {imu_id}")

    @pyqtSlot(bytes)
    def handle_received_packet(self, packet: bytes):
        """Handles raw binary UDP packets."""
        self.last_packet_timestamp = time.time()
        if self.top_bar.connection_widget.status_indicator._status == "connecting":
            self.set_info_label("Connected", "ok")
            self.connection_timeout_timer.start()

        parsed_successfully = False
        decoded_string = ""

        try:
            if len(packet) == self.PACKET_SIZE:
                imu_id, q0, q1, q2, q3 = struct.unpack(self.PACKET_FORMAT, packet)
                decoded_string = f"IMU {imu_id}: W={q0: 9.4f}, X={q1: 9.4f}, Y={q2: 9.4f}, Z={q3: 9.4f}"
                norm = np.sqrt(q0**2 + q1**2 + q2**2 + q3**2)

                if norm > 1e-6:
                    q0, q1, q2, q3 = q0 / norm, q1 / norm, q2 / norm, q3 / norm
                    if imu_id not in self.imu_data:
                        self.add_new_imu(imu_id)  # Dynamically add new IMU

                    # Check if imu_id is still valid (might fail if data for 70 comes in)
                    if imu_id in self.imu_data:
                        self.imu_data[imu_id].setScalar(q0)
                        self.imu_data[imu_id].setX(q1)
                        self.imu_data[imu_id].setY(q2)
                        self.imu_data[imu_id].setZ(q3)
                        self.new_data_imu_ids.add(imu_id)
                        parsed_successfully = True
                    else:
                        decoded_string = f"IMU {imu_id}: ID out of range?"
                else:
                    decoded_string = f"IMU {imu_id}: Zero-norm quaternion"
            else:
                decoded_string = f"Malformed Packet: Got {len(packet)} bytes, expected {self.PACKET_SIZE}"
        except (struct.error, KeyError, Exception) as e:
            decoded_string = f"Packet Unpack/Process Error: {e}"
            pass

        self.log_entry_created.emit(decoded_string, parsed_successfully)

    @pyqtSlot(str)
    def handle_received_line(self, line):
        """Handles ASCII serial lines (legacy support)."""
        imu_id = 0  # Assume all serial data is for IMU 0
        self.last_packet_timestamp = time.time()
        if self.top_bar.connection_widget.status_indicator._status == "connecting":
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
                    if imu_id not in self.imu_data:
                        self.add_new_imu(imu_id)

                    self.imu_data[imu_id].setScalar(q0)
                    self.imu_data[imu_id].setX(q1)
                    self.imu_data[imu_id].setY(q2)
                    self.imu_data[imu_id].setZ(q3)
                    self.new_data_imu_ids.add(imu_id)
                    parsed_successfully = True
        except (ValueError, IndexError):
            pass  # Failed to parse

        self.log_entry_created.emit(
            f"IMU {imu_id} (Serial): {line}", parsed_successfully
        )

    @pyqtSlot()
    def update_gl_and_ui(self):
        """Called by the render_timer to update all UI."""
        for imu_id in self.new_data_imu_ids:
            if imu_id in self.vis_widgets and imu_id in self.imu_data:
                widget = self.vis_widgets[imu_id]
                quat = self.imu_data[imu_id]
                widget.set_rotation_from_quat(quat)
                widget.render()

        selected_imu_id = self.feedback_widget.imu_select_combo.currentData()
        if selected_imu_id in self.new_data_imu_ids:
            if selected_imu_id in self.imu_data:
                self.update_data_labels(self.imu_data[selected_imu_id])

        self.new_data_imu_ids.clear()

    @pyqtSlot()
    def update_feedback_display(self):
        """Updates the data labels based on the dropdown selection."""
        imu_id = self.feedback_widget.imu_select_combo.currentData()
        if imu_id is not None and imu_id in self.imu_data:
            self.update_data_labels(self.imu_data[imu_id])
        else:
            self.feedback_widget.clear_labels()

    def update_data_labels(self, q: QQuaternion):
        """Updates all text labels in the feedback widget."""
        fw = self.feedback_widget
        fw.q0_label.setText(f"q0 (W): {q.scalar():.4f}")
        fw.q1_label.setText(f"q1 (X): {q.x():.4f}")
        fw.q2_label.setText(f"q2 (Y): {q.y():.4f}")
        fw.q3_label.setText(f"q3 (Z): {q.z():.4f}")

        w, x, y, z = q.scalar(), q.x(), q.y(), q.z()
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        sinp = 2 * (w * y - z * x)
        pitch = np.arcsin(sinp) if abs(sinp) < 1 else np.copysign(np.pi / 2, sinp)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        fw.roll_label.setText(f"Roll: {np.degrees(roll):.2f}°")
        fw.pitch_label.setText(f"Pitch: {np.degrees(pitch):.2f}°")
        fw.yaw_label.setText(f"Yaw: {np.degrees(yaw):.2f}°")

    def apply_theme(self):
        self.setStyleSheet(DARK_STYLE if self.is_dark_theme else LIGHT_STYLE)

        for widget in self.vis_widgets.values():
            widget.set_theme(self.is_dark_theme)

        self.top_bar.theme_button.setText("☀️" if self.is_dark_theme else "🌙")
        self.top_bar.connection_widget.set_theme(self.is_dark_theme)

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
            "last_baud": self.top_bar.connection_widget.baud_combo.currentText(),
            "splitter_sizes": self.main_splitter.sizes(),
            "logger": self.logger_widget.get_settings(),
        }
        with open("preferences.json", "w") as f:
            json.dump(prefs, f, indent=4)

    def closeEvent(self, event):
        # Stop timers immediately
        self.render_timer.stop()
        self.connection_timeout_timer.stop()

        # Stop worker thread and wait for it to finish
        if self.connection_worker and self.connection_worker.isRunning():
            self.connection_worker.stop()
            # Wait up to 2 seconds for the thread to finish
            if not self.connection_worker.wait(2000):
                print("Warning: Connection worker thread did not stop gracefully.")

        # Explicitly close all PyVista widgets
        for widget in self.vis_widgets.values():
            widget.close()  # This cleans up the VTK render window

        # Now save preferences
        self.save_preferences()

        # Accept the close event
        event.accept()


if __name__ == "__main__":
    if sys.platform.startswith("linux"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
    os.environ["QT_STYLE_OVERRIDE"] = ""
    app = QApplication(sys.argv)
    window = IMUVisualiser()
    window.show()
    sys.exit(app.exec_())
