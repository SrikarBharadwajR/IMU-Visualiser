# serial_worker.py
# This module contains the QThread worker for handling serial port communication.
# This version uses a polling-based loop and emits signals for data and errors.

from PyQt5.QtCore import QThread, pyqtSignal, QIODevice
from PyQt5.QtSerialPort import QSerialPort


class SerialWorker(QThread):
    """
    Handles serial port communication in a separate thread to prevent UI freezing.
    Uses a polling loop with waitForReadyRead() and emits signals for data and errors.
    """

    line_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port_name, baud_rate):
        super().__init__()
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.serial_port = None
        self._is_running = False

    def run(self):
        """The main logic of the thread."""
        self.serial_port = QSerialPort()
        self.serial_port.setPortName(self.port_name)
        self.serial_port.setBaudRate(self.baud_rate)

        if not self.serial_port.open(QIODevice.ReadOnly):
            error_str = self.serial_port.errorString()
            self.error_occurred.emit(f"Failed to open port: {error_str}")
            return

        self._is_running = True

        while self._is_running:
            # Check if the port is still open. If not, the device was likely unplugged.
            if not self.serial_port.isOpen():
                self.error_occurred.emit("Device disconnected.")
                break

            # Wait up to 100ms for new data to arrive
            if self.serial_port.waitForReadyRead(100):
                # Read all available lines
                while self.serial_port.canReadLine():
                    if not self._is_running:
                        break

                    # Read one line, decode safely, and strip whitespace
                    data = (
                        self.serial_port.readLine()
                        .data()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )
                    # Emit every line, even if it's empty after stripping
                    self.line_received.emit(data)

        if self.serial_port and self.serial_port.isOpen():
            self.serial_port.close()

        self.serial_port = None
        print("Serial worker thread has finished.")

    def stop(self):
        """Stops the thread gracefully."""
        if self.isRunning():
            self._is_running = False
            self.wait(500)  # Wait a bit for the thread to finish
