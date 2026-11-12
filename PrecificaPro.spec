
# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_DIR = Path(SPECPATH)

a = Analysis(
    [str(PROJECT_DIR / 'app.py')],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=[
        (str(PROJECT_DIR / 'templates'), 'templates'),
        (str(PROJECT_DIR / 'static'), 'static'),
    ],
    hiddenimports=[],
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
    name='PrecificaPro',
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
    icon=str(PROJECT_DIR / 'precifica_pro.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrecificaPro',
)
