# dodscars.spec
# Builds a ONE-FILE console app "DodCars" and bundles schema.sql next to the exe at runtime

block_cipher = None

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

PROJECT_ROOT = Path.cwd()

hidden = []
hidden += collect_submodules('sql_repo')
hidden += collect_submodules('base_repo')       # <-- added (ABC + Factory module)
hidden += collect_submodules('user_repo')
hidden += collect_submodules('admin_repo')
hidden += collect_submodules('customer_repo')
hidden += collect_submodules('car_repo')
hidden += collect_submodules('booking_repo')
hidden += collect_submodules('analytics_repo')
# If a session singleton module exists and is imported indirectly:
try:
    hidden += collect_submodules('session')     # <-- add if session.py exists
except Exception:
    pass

# (Optional) collect data files from packages if you ever add any
pkg_datas = []
# pkg_datas += collect_data_files('some_package')

a = Analysis(
    ['login_main_menu.py'],
    pathex=[PROJECT_ROOT],                      # <-- make imports deterministic
    binaries=[],
    datas=[
        ('schema.sql', '.'),                    # <-- required at runtime
    ],
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

# ONE-FILE build: include binaries/zipfiles/datas right here, no COLLECT()
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
    icon=os.path.join(PROJECT_ROOT, 'assets', 'dodscars_icon.png'),  # <-- new icon
    # (Optional) Windows version info file; create version_file.txt beside this spec if you want it.
    # version=os.path.join(PROJECT_ROOT, 'version_file.txt'),
)
