# dodscars_seeder.spec — one-file console EXE for the seeder

block_cipher = None

import os
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = os.path.abspath(os.getcwd())

hidden = []
hidden += collect_submodules('sql_repo')
hidden += collect_submodules('user_repo')
hidden += collect_submodules('car_repo')
hidden += collect_submodules('booking_repo')
hidden += collect_submodules('analytics_repo')  # harmless if unused at runtime

a = Analysis(
    ['seed_from_csv.py'],                     # entry script for the seeder
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[('schema.sql', '.')],         # make schema available inside the exe
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='DodCarsSeeder',
    console=True,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                              # <— disable UPX
    icon=None,                              # <— TEMP: rule out a bad .ico; restore later
)

