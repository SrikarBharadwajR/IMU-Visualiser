# logger_widget.py
# This module contains the widget for logging and saving raw serial data.

import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QLabel,
    QPlainTextEdit,
    QLineEdit,
    QSpinBox,
    QFileDialog,
    QApplication,
    QStyle,
    QGroupBox,
)
from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal


class ClickableLineEdit(QLineEdit):
    """A QLineEdit that emits a 'clicked' signal when pressed."""

    clicked = pyqtSignal()  # Define a new signal

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)  # Make it behave more like a label

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()  # Emit the signal on left-click
        super().mousePressEvent(event)  # Call the base class implementation


class LoggerWidget(QWidget):
    """
    A widget for displaying, controlling, and saving raw serial logs.
    """

    def __init__(self, preferences, parent=None):
        super().__init__(parent)
        self.log_file_path = ""
        self.log_line_count = 0
        self.last_rate_update_time = time.time()
        self._init_ui()
        self._load_settings(preferences)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 10, 5, 5)
        main_layout.setSpacing(10)

        # --- Top controls ---
        controls_group = QGroupBox("Log Controls")
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setSpacing(10)

        self.show_parsed_checkbox = QCheckBox("Show Parsed Only")
        self.show_parsed_checkbox.setToolTip(
            "Only display lines that were successfully parsed as quaternion data."
        )
        controls_layout.addWidget(self.show_parsed_checkbox)

        self.timestamps_checkbox = QCheckBox("Timestamps")
        self.timestamps_checkbox.setToolTip("Prepend a timestamp to each log entry.")
        controls_layout.addWidget(self.timestamps_checkbox)

        self.autoscroll_checkbox = QCheckBox("Autoscroll")
        self.autoscroll_checkbox.setChecked(True)
        controls_layout.addWidget(self.autoscroll_checkbox)

        controls_layout.addStretch()

        controls_layout.addWidget(QLabel("Buffer:"))
        self.buffer_spinbox = QSpinBox()
        self.buffer_spinbox.setToolTip("Maximum number of lines to keep in the log.")
        self.buffer_spinbox.setRange(100, 100000)
        self.buffer_spinbox.setValue(5000)
        self.buffer_spinbox.setSingleStep(100)
        controls_layout.addWidget(self.buffer_spinbox)

        main_layout.addWidget(controls_group)

        # --- Log display ---
        self.log_display = QPlainTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setWordWrapMode(False)
        font = self.log_display.font()
        font.setFamily("Consolas, Courier New, monospace")
        self.log_display.setFont(font)
        main_layout.addWidget(self.log_display, 1)  # Give it stretch factor

        # --- Bottom controls ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.clear_button = QPushButton()
        self.clear_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_button.setToolTip("Clear the log display.")
        self.clear_button.clicked.connect(self.clear_logs)
        bottom_layout.addWidget(self.clear_button)

        self.log_path_display = ClickableLineEdit()
        self.log_path_display.setPlaceholderText("Click to select log file path...")
        self.log_path_display.setToolTip("Click to browse for a file to save the log.")
        self.log_path_display.setMinimumWidth(150)
        self.log_path_display.clicked.connect(self.browse_log_file)
        bottom_layout.addWidget(self.log_path_display)

        self.save_button = QPushButton()
        self.save_button.setToolTip("Save the Logs")
        self.save_button.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.save_button.clicked.connect(self.save_logs)
        bottom_layout.addWidget(self.save_button)

        self.rate_label = QLabel("Print Rate: 0.0 Hz")
        bottom_layout.addWidget(self.rate_label)

        main_layout.addLayout(bottom_layout)

    @pyqtSlot(str, bool)
    def add_log_entry(self, line, is_parsed):
        """Adds a new line to the log display, respecting control settings."""
        if self.show_parsed_checkbox.isChecked() and not is_parsed:
            return

        if self.timestamps_checkbox.isChecked():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            line = f"[{timestamp}] {line}"

        # Handle buffer limit
        if self.log_display.blockCount() > self.buffer_spinbox.value():
            cursor = self.log_display.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.LineUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # remove the newline

        # Append text and handle autoscroll
        self.log_display.appendPlainText(line)
        if self.autoscroll_checkbox.isChecked():
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

        self._update_rate()

    def _update_rate(self):
        self.log_line_count += 1
        current_time = time.time()
        time_diff = current_time - self.last_rate_update_time
        if time_diff >= 1.0:
            rate = self.log_line_count / time_diff
            self.rate_label.setText(f"Print Rate: {rate:.1f} Hz")
            self.last_rate_update_time = current_time
            self.log_line_count = 0

    @pyqtSlot()
    def clear_logs(self):
        self.log_display.clear()

    @pyqtSlot()
    def browse_log_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log File",
            "",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)",
        )
        if path:
            self.log_file_path = path
            self.log_path_display.setText(path)

    @pyqtSlot()
    def save_logs(self):
        if not self.log_file_path:
            self.browse_log_file()
        if self.log_file_path:
            try:
                with open(self.log_file_path, "w") as f:
                    f.write(self.log_display.toPlainText())
            except Exception as e:
                # In a real app, show a message box
                print(f"Error saving log file: {e}")

    def _load_settings(self, settings):
        """Loads settings from a dictionary."""
        self.show_parsed_checkbox.setChecked(settings.get("show_parsed_only", False))
        self.timestamps_checkbox.setChecked(settings.get("add_timestamps", False))
        self.autoscroll_checkbox.setChecked(settings.get("autoscroll", True))
        self.buffer_spinbox.setValue(settings.get("buffer_size", 5000))
        self.log_file_path = settings.get("log_file_path", "")
        if self.log_file_path:
            self.log_path_display.setText(self.log_file_path)

    def get_settings(self):
        """Returns the current settings as a dictionary."""
        return {
            "show_parsed_only": self.show_parsed_checkbox.isChecked(),
            "add_timestamps": self.timestamps_checkbox.isChecked(),
            "autoscroll": self.autoscroll_checkbox.isChecked(),
            "buffer_size": self.buffer_spinbox.value(),
            "log_file_path": self.log_file_path,
        }
