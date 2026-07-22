# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\cashier_app\\app.py'],
    pathex=['C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend', 'C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\cashier_app'],
    binaries=[],
    datas=[],
    hiddenimports=['engineio', 'socketio', 'engineio.async_drivers.threading', 'simple_websocket', 'cashier_routes'],
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
    name='cashier_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='cashier_app',
)
