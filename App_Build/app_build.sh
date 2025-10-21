#!/bin/bash
rm -rf build/ dist/
# Replace the path in the first --add-data line with your own!
PLUGIN_PATH="/home/srikar/.local/lib/python3.13/site-packages/PyQt5/Qt5/plugins/imageformats"

pyinstaller --name="IMU_Visualiser" --onefile --windowed \
--add-data="$PLUGIN_PATH:PyQt5/Qt5/plugins/imageformats" \
--add-data="logo.jpeg:." \
--add-data="icon.jpeg:." \
--hidden-import="OpenGL.platform.egl" \
imu_visualiser.py