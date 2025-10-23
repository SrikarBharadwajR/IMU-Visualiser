# connection_workers.py
# This module contains QThread workers for handling data connections.
# Includes SerialWorker (for real hardware) and UdpWorker (for testing).

import socket
from PyQt5.QtCore import QThread, pyqtSignal, QIODevice
from PyQt5.QtSerialPort import QSerialPort


class SerialWorker(QThread):
    """
    Handles serial port communication in a separate thread to prevent UI freezing.
    Uses a polling loop with waitForReadyRead() and emits signals for data and errors.
    """

    # This will eventually be updated to emit bytes too
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
                    if data:
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


class UdpWorker(QThread):
    """
    Listens for UDP packets on a specific port and emits them as raw bytes.
    Used for the "Test Mode" feature.
    """

    packet_received = pyqtSignal(bytes)  # Changed from line_received
    error_occurred = pyqtSignal(str)

    def __init__(self, listen_port=12345):
        super().__init__()
        self.listen_port = listen_port
        self.listen_host = "127.0.0.1"  # Listen on localhost only
        self.sock = None
        self._is_running = False

    def run(self):
        """The main logic of the thread."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.listen_host, self.listen_port))
            # Set a timeout so the loop can check _is_running
            self.sock.settimeout(1.0)
        except Exception as e:
            self.error_occurred.emit(f"Failed to open UDP socket: {e}")
            return

        self._is_running = True
        print(f"UDP worker started, listening on {self.listen_host}:{self.listen_port}")

        while self._is_running:
            try:
                # Wait for data
                data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
                if data:
                    self.packet_received.emit(data)  # Emit raw bytes
            except socket.timeout:
                # This is expected, just loop again to check self._is_running
                continue
            except Exception as e:
                if self._is_running:
                    # Log other errors but don't crash
                    print(f"UDP worker error: {e}")

        if self.sock:
            self.sock.close()

        self.sock = None
        print("UDP worker thread has finished.")

    def stop(self):
        """Stops the thread gracefully."""
        if self.isRunning():
            self._is_running = False
            # Wait for the socket timeout to expire
            self.wait(1500)
