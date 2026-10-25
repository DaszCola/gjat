# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        ('bin/deno.exe', 'bin'),
        ('bin/ffmpeg.exe', 'bin'),
        ('bin/ffprobe.exe', 'bin')
    ],
    datas=[('app_icon.png', '.'), ('app_icon.ico', '.'), ('version.json', '.')],

    hiddenimports=['PIL', 'yt_dlp', 'PyQt6', 'curl_cffi', 'cffi', 'pycparser'],
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
    name='GjatDownloader',
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
    icon=['app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GjatDownloader',
)
