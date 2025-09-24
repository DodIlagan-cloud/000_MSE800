# dodscars.spec — ONE-FILE console build, bundles schema.sql, uses new icon

block_cipher = None

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# __file__ may be undefined in spec context; use CWD as project root
PROJECT_ROOT = Path.cwd()

hidden = []
hidden += collect_submodules('sql_repo')
hidden += collect_submodules('base_repo')        # ABC + Factory module
hidden += collect_submodules('user_repo')
hidden += collect_submodules('admin_repo')
hidden += collect_submodules('customer_repo')
hidden += collect_submodules('car_repo')
hidden += collect_submodules('booking_repo')
hidden += collect_submodules('analytics_repo')
# Add if you have session.py; ignore if not present
try:
    hidden += collect_submodules('session')
except Exception:
    pass

pkg_datas = []  # keep for future package data if needed

a = Analysis(
    ['login_main_menu.py'],
    pathex=[str(PROJECT_ROOT)],                  # deterministic imports
    binaries=[],
    datas=[('schema.sql', '.')],                 # required at runtime
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
    a.datas + pkg_datas,
    name='DodCars',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # console app
    icon=str(PROJECT_ROOT / 'assets' / 'dodcars_icon.png'),  # <- ensure file exists
    # Optional version info (comment out if you don't have the file)
    # version=str(PROJECT_ROOT / 'version_file.txt'),
)
