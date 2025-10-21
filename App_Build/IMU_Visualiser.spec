# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['imu_visualiser.py'],
    pathex=[],
    binaries=[],
    datas=[('/home/srikar/.local/lib/python3.13/site-packages/PyQt5/Qt5/plugins/imageformats', 'PyQt5/Qt5/plugins/imageformats'), ('logo.jpeg', '.'), ('icon.jpeg', '.')],
    hiddenimports=['OpenGL.platform.egl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='IMU_Visualiser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
