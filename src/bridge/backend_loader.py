"""
deepslate.bridge.backend_loader
Dynamic loader for BedrockOnLinux backend (`bol`).

Attempts to load `bol` from:
1. Existing sys.path / Python environment
2. Installed AppImage (/opt/bedrock-on-linux-bin/*.AppImage), extracting `usr/bin/bol` into cache
3. Local development fallback directories
"""

import os
import sys
import glob
import shutil
import subprocess
from pathlib import Path
from typing import Optional

CACHE_DIR = Path.home() / ".cache" / "deepslate"
EXTRACTED_BOL_DIR = CACHE_DIR / "bol_runtime"
VERSION_MARKER = CACHE_DIR / "bol_version.txt"

def find_installed_appimage() -> Optional[Path]:
    """Look for bedrock-on-linux AppImage installed from AUR or elsewhere."""
    candidates = [
        "/opt/bedrock-on-linux-bin",
        "/opt/bedrock-on-linux",
        str(Path.home() / "Applications"),
        str(Path.home() / ".local" / "bin"),
    ]
    for directory in candidates:
        if os.path.isdir(directory):
            matches = glob.glob(os.path.join(directory, "*Bedrock*.AppImage")) + \
                      glob.glob(os.path.join(directory, "*bedrock*.AppImage"))
            if matches:
                return Path(matches[0])
    # Also check /usr/bin/bedrock-on-linux if it is a symlink to an AppImage
    usr_bin = Path("/usr/bin/bedrock-on-linux")
    if usr_bin.is_symlink():
        target = usr_bin.resolve()
        if target.is_file() and "AppImage" in target.name:
            return target
    return None

def extract_bol_from_appimage(appimage_path: Path) -> bool:
    """Extract usr/bin/bol from the AppImage into ~/.cache/deepslate/bol_runtime."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        mtime = str(appimage_path.stat().st_mtime)
        
        # If cache already valid for this exact AppImage mtime, skip extraction
        if VERSION_MARKER.is_file() and EXTRACTED_BOL_DIR.is_dir():
            if VERSION_MARKER.read_text().strip() == f"{appimage_path}:{mtime}":
                if (EXTRACTED_BOL_DIR / "bol" / "__init__.py").is_file():
                    return True
        
        # Run AppImage extraction for usr/bin/bol/*
        cmd = [str(appimage_path), "--appimage-extract", "usr/bin/bol/*"]
        result = subprocess.run(cmd, cwd=str(CACHE_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        extracted_source = CACHE_DIR / "squashfs-root" / "usr" / "bin" / "bol"
        if extracted_source.is_dir():
            if EXTRACTED_BOL_DIR.exists():
                shutil.rmtree(EXTRACTED_BOL_DIR, ignore_errors=True)
            EXTRACTED_BOL_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copytree(extracted_source, EXTRACTED_BOL_DIR / "bol", dirs_exist_ok=True)
            shutil.rmtree(CACHE_DIR / "squashfs-root", ignore_errors=True)
            VERSION_MARKER.write_text(f"{appimage_path}:{mtime}")
            return True
            
        if (CACHE_DIR / "squashfs-root").exists():
            shutil.rmtree(CACHE_DIR / "squashfs-root", ignore_errors=True)
            
    except Exception as exc:
        print(f"[Deepslate] Warning: Failed to extract bol from AppImage: {exc}", file=sys.stderr)
    return False

def ensure_backend() -> bool:
    """Ensure `bol` is importable, configuring sys.path as necessary."""
    try:
        import bol
        return True
    except ImportError:
        pass

    # 1. Try AppImage extraction
    appimage = find_installed_appimage()
    if appimage and extract_bol_from_appimage(appimage):
        if str(EXTRACTED_BOL_DIR) not in sys.path:
            sys.path.insert(0, str(EXTRACTED_BOL_DIR))
        try:
            import bol
            return True
        except ImportError:
            pass

    # 2. Try development fallbacks (e.g. /tmp/bedrock_research, ~/Projects/BedrockOnLinux)
    fallbacks = [
        "/tmp/bedrock_research",
        str(Path.home() / "Projects" / "BedrockOnLinux"),
        str(Path.home() / "caelestia-dots-kde" / "bedrock"),
    ]
    for fb in fallbacks:
        if os.path.isdir(os.path.join(fb, "bol")):
            if fb not in sys.path:
                sys.path.insert(0, fb)
            try:
                import bol
                return True
            except ImportError:
                pass

    return False

# Initialize backend on module import
BACKEND_AVAILABLE = ensure_backend()
