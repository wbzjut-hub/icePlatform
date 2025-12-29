# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'whisper_models'), # Copy backend/models to dist/whisper_models
    ],
    hiddenimports=['whisper'],
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
    name='icePlatform',
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
    a.binaries + [('bin/ffmpeg', 'bin/ffmpeg', 'BINARY')], # Use local bin/ffmpeg, put in bin/ folder
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='icePlatform',
)
