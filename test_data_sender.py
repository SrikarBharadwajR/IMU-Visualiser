# test_data_sender.py
# Sends simulated IMU data (quaternions) over UDP to the main application.
# Now sends binary data for a configurable number of IMUs.

import socket
import time
import numpy as np
import struct
import random

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 12345
SEND_RATE_HZ = 50  # Send data 50 times per second
SLEEP_DURATION = 1.0 / SEND_RATE_HZ

# --- TEST CONFIG ---
# Change this to "random" to send random data
TEST_MODE = "sync"  # "sync" or "random"
NUM_IMUS = 4
# ---------------------

# Packet format: <Bffff (1 byte IMU ID, 4 floats)
PACKET_FORMAT = "<Bffff"

print(f"--- IMU Test Data Sender ---")
print(f"Starting UDP data sender...")
print(f"Targeting:   {TARGET_HOST}:{TARGET_PORT}")
print(f"Send Rate: {SEND_RATE_HZ} Hz")
print(f"Mode:      {TEST_MODE} for {NUM_IMUS} IMUs (Ctrl+C to stop)")


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# --- State for 'sync' mode (generalized for N IMUs) ---

# Base axes to cycle through
base_axes = [
    np.array([1.0, 0.0, 0.0]),  # X
    np.array([0.0, 1.0, 0.0]),  # Y
    np.array([0.0, 0.0, 1.0]),  # Z
    np.array([0.707, 0.707, 0.0]),  # XY
    np.array([0.0, 0.707, 0.707]),  # YZ
    np.array([0.707, 0.0, 0.707]),  # XZ
]

imu_angles = [0.0] * NUM_IMUS
imu_rot_speeds = []
imu_axes = []

base_speed = 20.0
for i in range(NUM_IMUS):
    # Assign a unique rotation speed, alternating direction
    speed = base_speed + (i * 15.0)
    if i % 2 == 1:
        speed *= -1  # Make every other one rotate backward
    imu_rot_speeds.append(speed)

    # Assign a unique axis, cycling through the base axes
    axis = base_axes[i % len(base_axes)].copy()
    # Add a small random tilt to make them more distinct
    tilt = (np.random.rand(3) - 0.5) * 0.1
    axis = axis + tilt
    axis = axis / np.linalg.norm(axis)  # Re-normalize
    imu_axes.append(axis)

# ----------------------------------------------------


def get_random_quaternion():
    """Generates a random unit quaternion."""
    u = np.random.rand(3)
    w = np.sqrt(1 - u[0]) * np.sin(2 * np.pi * u[1])
    x = np.sqrt(1 - u[0]) * np.cos(2 * np.pi * u[1])
    y = np.sqrt(u[0]) * np.sin(2 * np.pi * u[2])
    z = np.sqrt(u[0]) * np.cos(2 * np.pi * u[2])
    return w, x, y, z


try:
    while True:
        if TEST_MODE == "sync":
            # --- Iterate through all N IMUs and send sync'd data ---
            for i in range(NUM_IMUS):
                # Update angle for this IMU
                imu_angles[i] = (
                    imu_angles[i] + imu_rot_speeds[i] * SLEEP_DURATION
                ) % 360.0

                # Calculate quaternion
                rad = np.radians(imu_angles[i] / 2.0)
                w = np.cos(rad)
                x = np.sin(rad) * imu_axes[i][0]
                y = np.sin(rad) * imu_axes[i][1]
                z = np.sin(rad) * imu_axes[i][2]

                # Pack and send the message with IMU ID 'i'
                msg = struct.pack(PACKET_FORMAT, i, w, x, y, z)
                sock.sendto(msg, (TARGET_HOST, TARGET_PORT))

        elif TEST_MODE == "random":
            # --- Iterate and send random data ---
            for i in range(NUM_IMUS):
                w, x, y, z = get_random_quaternion()
                msg = struct.pack(PACKET_FORMAT, i, w, x, y, z)
                sock.sendto(msg, (TARGET_HOST, TARGET_PORT))

        # Wait for the next frame
        time.sleep(SLEEP_DURATION)

except KeyboardInterrupt:
    print("\nStopping sender.")
finally:
    sock.close()
