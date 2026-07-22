# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\dashboard\\registration_app.py'],
    pathex=['C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend', 'C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\dashboard'],
    binaries=[],
    datas=[
        ('C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\dashboard\\static', 'static'),
        ('C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\dashboard\\templates', 'templates'),
        ('C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\dashboard\\credentials.json', '.'),
        ('C:\\Users\\admin\\Desktop\\projects\\BANKONGSETON\\backend\\sheets_adapter.py', '.'),
    ],
    hiddenimports=['engineio', 'socketio', 'engineio.async_drivers.threading', 'simple_websocket', 'dashboard_core', 'offline_queue', 'sheets_adapter', 'notifications'],
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
    name='registration_app',
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
    name='registration_app',
)
