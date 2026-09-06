# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller recipe. Builds a self-contained Hush for the current OS."""

import platform
from PyInstaller.utils.hooks import collect_data_files

system = platform.system()
mac = system == "Darwin"
win = system == "Windows"

# the auto-editor binary for this platform, fetched by fetch_engines.py
if mac:
    engines = [("bin/auto-editor-macos-arm64", "bin"),
               ("bin/auto-editor-macos-x86_64", "bin")]
elif win:
    engines = [("bin/auto-editor-windows-x86_64.exe", "bin")]
else:
    engines = [("bin/auto-editor-linux-x86_64", "bin")]

# tkdnd libraries, otherwise drag and drop is dead in the frozen app
dnd = collect_data_files("tkinterdnd2", include_py_files=False,
                         includes=["**/*"])

a = Analysis(
    ["hush.py"],
    pathex=[],
    binaries=[],
    datas=engines + dnd,
    hiddenimports=["tkinterdnd2"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "PIL", "matplotlib", "pandas", "scipy",
              "PySide6", "PyQt5", "test", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Hush",
    debug=False, strip=False, upx=False, console=False,
    icon="hush.icns" if mac else ("hush.ico" if win else None),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Hush")

if mac:
    app = BUNDLE(
        coll,
        name="Hush.app",
        icon="hush.icns",
        bundle_identifier="com.emptyoverlord.hush",
        info_plist={
            "CFBundleName": "Hush",
            "CFBundleDisplayName": "Hush",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "CFBundleDocumentTypes": [{
                "CFBundleTypeName": "Media",
                "CFBundleTypeRole": "Viewer",
                "LSItemContentTypes": ["public.movie", "public.audio"],
            }],
        },
    )
