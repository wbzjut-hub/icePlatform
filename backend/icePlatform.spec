import platform

system_platform = platform.system()
ffmpeg_binary = 'bin/ffmpeg.exe' if system_platform == 'Windows' else 'bin/ffmpeg'
ffmpeg_target = 'bin/ffmpeg.exe' if system_platform == 'Windows' else 'bin/ffmpeg'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'whisper_models'), # Copy backend/models to dist/whisper_models
        ('.env', '.'), # Ensure .env is included
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
    a.binaries + [(ffmpeg_binary, ffmpeg_target, 'BINARY')], # Dynamic ffmpeg binary
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='icePlatform',
)
