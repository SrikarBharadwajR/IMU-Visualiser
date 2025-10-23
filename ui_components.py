# ui_components.py
# Contains all custom QWidget classes for the IMU Visualiser UI.

import math
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QGroupBox,
    QSplitter,
    QStyle,
    QSizePolicy,
    QFrame,
    QTabWidget,
    QCheckBox,
    QSpinBox,
    QStackedWidget,
    QGridLayout,
)
from PyQt5.QtGui import QPainter, QColor, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSlot

from stylesheets import DARK_GREEN, DARK_RED, LIGHT_GREEN, LIGHT_RED


class ImuVisualiserPanel(QFrame):
    """A container widget that holds a PyVistaWidget and a title label."""

    def __init__(self, imu_id: int, parent=None):
        super().__init__(parent)

        # Style the frame
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self_layout = QVBoxLayout(self)
        self_layout.setContentsMargins(5, 5, 5, 5)
        self_layout.setSpacing(5)

        # 1. Title Label
        self.title_label = QLabel(f"<b>IMU {imu_id}</b>")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("ImuGridTitleLabel")
        self_layout.addWidget(self.title_label)

        # 2. Add a placeholder layout for the PyVista widget
        self.vis_widget_layout = QVBoxLayout()
        self.vis_widget_layout.setContentsMargins(0, 0, 0, 0)
        self_layout.addLayout(self.vis_widget_layout, 1)  # Give it stretch

    def set_vis_widget(self, widget: QWidget):
        """Adds the PyVista widget to the panel."""
        self.clear_vis_widget()
        widget.setParent(self)
        self.vis_widget_layout.addWidget(widget)
        widget.show()

    def clear_vis_widget(self) -> QWidget | None:
        """Removes the PyVista widget from the panel and returns it."""
        if self.vis_widget_layout.count() > 0:
            item = self.vis_widget_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.setParent(None)  # Detach it
                return widget
        return None

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


class ConnectionWidget(QGroupBox):
    """Encapsulates all connection controls into one widget."""

    def __init__(self, parent=None):
        super().__init__("Connections", parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        # --- Test Mode Checkbox ---
        self.test_mode_check = QCheckBox("Test Mode")
        self.test_mode_check.setToolTip(
            "Bypass serial and listen for UDP test data on 127.0.0.1:12345"
        )
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
        # Preferences should be set by the main window
        layout.addWidget(self.baud_combo)

        # Refresh Button
        self.refresh_ports_button = QPushButton()
        self.refresh_ports_button.setIconSize(QSize(20, 20))
        self.refresh_ports_button.setFixedWidth(28)
        self.refresh_ports_button.setObjectName("refreshButton")
        self.refresh_ports_button.setToolTip("Refresh available serial ports")
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
        layout.addWidget(self.connect_button)

        layout.addSpacing(15)

        # --- Status Indicator and Labels ---
        self.status_indicator = StatusIndicator()
        layout.addWidget(self.status_indicator)

        self.info_label = QLabel()
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)

    def set_theme(self, is_dark):
        """Updates theme-dependent elements like icons."""
        self.status_indicator.set_theme(is_dark)

        # Recolor refresh icon
        style = self.style()
        icon = style.standardIcon(QStyle.SP_BrowserReload)
        pixmap = icon.pixmap(QSize(24, 24))

        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#FFFFFF"))
        painter.end()

        self.refresh_ports_button.setIcon(QIcon(pixmap))


class ImuDisplayWidget(QGroupBox):
    """Encapsulates IMU count and display options."""

    def __init__(self, parent=None):
        super().__init__("IMU Display", parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("IMU Count:"))
        self.imu_count_spinbox = QSpinBox()
        self.imu_count_spinbox.setRange(1, 64)
        self.imu_count_spinbox.setValue(2)
        self.imu_count_spinbox.setToolTip("Set the expected number of IMUs")
        layout.addWidget(self.imu_count_spinbox)

        layout.addSpacing(15)

        self.club_tabs_checkbox = QCheckBox("Club Tabs")
        self.club_tabs_checkbox.setToolTip("Show all IMU visualisers in a single grid")
        layout.addWidget(self.club_tabs_checkbox)


class TopBarWidget(QWidget):
    """Encapsulates the entire top bar (logo, controls, theme button)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        top_bar_layout = QHBoxLayout(self)
        top_bar_layout.setContentsMargins(0, 10, 0, 0)

        # Logo
        self.logo_label = QLabel()
        pixmap = QPixmap("logo.png")
        self.logo_label.setPixmap(
            pixmap.scaled(120, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        top_bar_layout.addWidget(self.logo_label)
        top_bar_layout.addSpacing(50)

        # Connection Controls
        self.connection_widget = ConnectionWidget()
        top_bar_layout.addWidget(self.connection_widget)

        # IMU Display Controls
        self.imu_display_widget = ImuDisplayWidget()
        top_bar_layout.addWidget(self.imu_display_widget)

        top_bar_layout.addStretch()

        # Theme button
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(QSize(45, 40))
        self.theme_button.setToolTip("Toggle light/dark theme")
        top_bar_layout.addWidget(self.theme_button)


class FeedbackWidget(QWidget):
    """Encapsulates the 'Processed Data' tab's UI."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        processed_layout = QVBoxLayout(self)
        processed_layout.setAlignment(Qt.AlignTop)

        # --- IMU Selection Dropdown ---
        feedback_select_layout = QHBoxLayout()
        feedback_select_layout.addWidget(QLabel("Show Feedback for IMU:"))
        self.imu_select_combo = QComboBox()
        feedback_select_layout.addWidget(self.imu_select_combo)
        feedback_select_layout.addStretch()
        processed_layout.addLayout(feedback_select_layout)

        # --- Data Labels ---
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

    def clear_labels(self):
        """Resets all data labels to 'N/A'."""
        self.q0_label.setText("q0 (W): N/A")
        self.q1_label.setText("q1 (X): N/A")
        self.q2_label.setText("q2 (Y): N/A")
        self.q3_label.setText("q3 (Z): N/A")
        self.roll_label.setText("Roll: N/A")
        self.pitch_label.setText("Pitch: N/A")
        self.yaw_label.setText("Yaw: N/A")


class ImuGridWidget(QWidget):
    """A widget that displays multiple IMU widgets in a grid."""

    # Set of prime numbers up to 64
    _PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(5)
        self.widgets = []
        self.dummy_widget = None

    def add_widget(self, widget: QWidget):
        """Adds a widget to the grid and updates the layout."""
        if widget not in self.widgets:
            self.widgets.append(widget)
            self.update_grid()

    def clear_widgets(self):
        """Removes all widgets from the grid."""
        for widget in self.widgets:
            if isinstance(widget, ImuVisualiserPanel):
                widget.clear_vis_widget()
            widget.setParent(None)
        self.widgets.clear()

        if self.dummy_widget:
            self.dummy_widget.setParent(None)
            self.dummy_widget = None

        self.update_grid()

    def update_grid(self):
        """Clears and rebuilds the entire grid layout."""
        # Clear existing layout
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        self.dummy_widget = None
        num_widgets = len(self.widgets)
        if num_widgets == 0:
            return

        # Handle prime number case by adding 1 for a dummy
        display_count = num_widgets
        if num_widgets > 1 and num_widgets in self._PRIMES:
            display_count += 1

        # Calculate grid size
        cols = int(math.ceil(math.sqrt(display_count)))
        rows = int(math.ceil(display_count / cols))

        # Re-add widgets
        current_col = 0
        current_row = 0
        for widget in self.widgets:
            self.grid_layout.addWidget(widget, current_row, current_col)
            current_col += 1
            if current_col == cols:
                current_col = 0
                current_row += 1

        # Add dummy widget if needed
        if display_count > num_widgets:
            self.dummy_widget = QFrame()
            self.dummy_widget.setObjectName("dummyImuPanel")
            self.dummy_widget.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
            self.grid_layout.addWidget(self.dummy_widget, current_row, current_col)
