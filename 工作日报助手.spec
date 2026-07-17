# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['UI\\main_fluent.py'],
    pathex=[],
    binaries=[],
    datas=[('UI/styles.qss', 'UI'), ('UI/main_window.ui', 'UI')],
    hiddenimports=['PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui', 'qfluentwidgets', 'cv2', 'numpy', 'mss', 'ollama', 'csv', 'json', 'base64'],
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
    [],
    exclude_binaries=True,
    name='工作日报助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='工作日报助手',
)
