# test_data_sender.py
# Sends simulated IMU data (quaternions) over UDP to the main application.
# Run this file in a separate terminal to test the visualiser.

import socket
import time
import numpy as np

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 12345
SEND_RATE_HZ = 50  # Send data 50 times per second
SLEEP_DURATION = 1.0 / SEND_RATE_HZ

print(f"--- IMU Test Data Sender ---")
print(f"Starting UDP data sender...")
print(f"Targeting:   {TARGET_HOST}:{TARGET_PORT}")
print(f"Send Rate: {SEND_RATE_HZ} Hz (Ctrl+C to stop)")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Simulate a smooth rotation
angle = 0.0
rotation_speed_deg_s = 30.0  # degrees per second

try:
    while True:
        # Calculate rotation for this frame
        angle += rotation_speed_deg_s * SLEEP_DURATION
        if angle > 360.0:
            angle -= 360.0

        # Create a quaternion for rotation around a tilted axis (e.g., Y and Z)
        rad = np.radians(angle / 2.0)
        axis = np.array([0.0, 0.707, 0.707])  # Tilted axis
        axis = axis / np.linalg.norm(axis)  # Normalize axis

        w = np.cos(rad)
        x = np.sin(rad) * axis[0]
        y = np.sin(rad) * axis[1]
        z = np.sin(rad) * axis[2]

        # Format as "w, x, y, z" string
        # This matches the format the main app expects
        message = f"{w:.6f}, {x:.6f}, {y:.6f}, {z:.6f}"

        # Send the data
        sock.sendto(message.encode("utf-8"), (TARGET_HOST, TARGET_PORT))

        # Wait for the next frame
        time.sleep(SLEEP_DURATION)

except KeyboardInterrupt:
    print("\nStopping sender.")
finally:
    sock.close()
