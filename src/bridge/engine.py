"""
deepslate.bridge.engine
Unified Engine controller for Deepslate Launcher.
Interacts directly with the `bol` backend with graceful CLI fallbacks.
"""

from __future__ import annotations

import os
import sys
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

# Ensure bol is available in sys.path
from .backend_loader import ensure_backend
ensure_backend()

from bol.config import (
    DATA, GAMES, LOGS, SETTINGS, VERSION as BOL_VERSION, PRETTY
)
from bol.auth import (
    NativeAuth, msa_logout, msa_signed_in, msa_gamertag
)
from bol.games import (
    installed_builds, list_editions, list_versions, remove_build, use_game_dir
)
from bol.gamesetup import do_setup
from bol.launch import direct_launch_readiness, launch
from bol.doctor import doctor, acknowledge_gpu_crash, gpu_crash_acknowledgement_status
from bol.prefix import _mc_running, kill_wine, reset_prefix
from bol.profiles import (
    list_profiles, current_profile_name, create_profile, delete_profile,
    rename_profile, write_play_shortcut, write_profile_shortcut
)
from bol.content import import_content
from bol.util import load_settings as bol_load_settings, save_settings as bol_save_settings
from .cli_bridge import run_cli_command


class Engine:
    """Singleton-like controller managing state, game lifecycle, and backend operations."""
    
    def __init__(self):
        self.settings: Dict[str, Any] = self.load_settings()
        self.game_process: Optional[threading.Thread] = None
        self._running = False
        self._log_listeners: List[Callable[[str], None]] = []
        
    # --------------------------------------------------------------------------
    # Settings
    # --------------------------------------------------------------------------
    def load_settings(self) -> Dict[str, Any]:
        """Load user settings from ~/.local/share/bedrock-on-linux/settings.json."""
        try:
            self.settings = bol_load_settings()
        except Exception:
            self.settings = {}
        return self.settings

    def save_settings(self, updates: Optional[Dict[str, Any]] = None) -> None:
        """Update and persist settings."""
        if updates:
            self.settings.update(updates)
        bol_save_settings(self.settings)

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value
        bol_save_settings(self.settings)

    # --------------------------------------------------------------------------
    # Versions & Builds
    # --------------------------------------------------------------------------
    def get_installed_builds(self) -> List[Dict[str, Any]]:
        """Return list of all locally installed Minecraft Bedrock builds."""
        try:
            return installed_builds(with_size=True)
        except Exception as exc:
            print(f"[Deepslate] Error fetching installed builds: {exc}", file=sys.stderr)
            return []

    def get_available_versions(self, edition: str = "release", beta: bool = False, refresh: bool = False) -> List[str]:
        """Fetch available remote builds from Microsoft Store/Xbox index."""
        try:
            return list_versions(edition_id=edition, beta=beta, refresh=refresh)
        except Exception as exc:
            print(f"[Deepslate] Error fetching remote versions: {exc}", file=sys.stderr)
            return []

    def remove_version(self, target_path_or_version: str, edition_id: Optional[str] = None) -> int:
        """Delete an installed build and return freed bytes."""
        builds = self.get_installed_builds()
        match = None
        for b in builds:
            if str(b.get("path")) == target_path_or_version or b.get("version") == target_path_or_version:
                match = b
                break
        if match:
            return remove_build(Path(match["path"]))
        return 0

    def install_build(
        self,
        edition: str,
        version: Optional[str] = None,
        force: bool = False,
        progress_cb: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """Download and install a Bedrock build with real-time progress callbacks."""
        return do_setup(
            mc_edition=edition,
            mc_version=version,
            force=force,
            progress=progress_cb
        )

    # --------------------------------------------------------------------------
    # Account & Authentication
    # --------------------------------------------------------------------------
    def is_signed_in(self) -> bool:
        """Check if user has an active Microsoft / Xbox session."""
        try:
            return msa_signed_in()
        except Exception:
            return False

    def get_account_gamertag(self) -> Optional[str]:
        """Return user's Xbox Gamertag if signed in."""
        try:
            return msa_gamertag()
        except Exception:
            return None

    def is_store_account_linked(self) -> bool:
        """Check if Microsoft Store account is linked via Xodus."""
        xodus_keyring = DATA / "xodus-home" / ".xodus-keyring.ron"
        return xodus_keyring.is_file()

    def sign_out(self) -> None:
        """Log out from Microsoft account."""
        try:
            msa_logout()
        except Exception as exc:
            print(f"[Deepslate] Logout error: {exc}", file=sys.stderr)

    # --------------------------------------------------------------------------
    # Game Launch & Process Lifecycle
    # --------------------------------------------------------------------------
    def is_game_running(self) -> bool:
        """Check if Minecraft Bedrock is currently running in Wine/Proton."""
        try:
            return _mc_running()
        except Exception:
            return False

    def check_launch_readiness(self) -> Tuple[bool, Optional[str]]:
        """Validate if game is ready to launch or if safety gates/remedies are required."""
        try:
            ready, msg = direct_launch_readiness()
            return ready, msg
        except Exception as exc:
            return True, None

    def kill_game(self) -> None:
        """Terminate running Minecraft and Wine prefix processes."""
        try:
            kill_wine()
        except Exception as exc:
            print(f"[Deepslate] Error killing Wine: {exc}", file=sys.stderr)

    def launch_game_async(
        self,
        log_callback: Optional[Callable[[str], None]] = None,
        exit_callback: Optional[Callable[[int], None]] = None
    ) -> threading.Thread:
        """Launch Minecraft in a background thread while streaming log output."""
        def _runner():
            from bol import log as bol_log
            
            # Hook the log sink to intercept log lines
            old_sink = bol_log._LOG_SINK
            if log_callback:
                bol_log._LOG_SINK = log_callback
                
            code = 0
            try:
                launch()
            except Exception as exc:
                code = 1
                if log_callback:
                    log_callback(f"[Deepslate Error] Launch failed: {exc}\n")
            finally:
                bol_log._LOG_SINK = old_sink
                if exit_callback:
                    exit_callback(code)

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        self.game_process = thread
        return thread

    # --------------------------------------------------------------------------
    # Profiles
    # --------------------------------------------------------------------------
    def get_profiles(self) -> List[str]:
        try:
            return list_profiles()
        except Exception:
            return ["Default"]

    def get_current_profile(self) -> str:
        try:
            return current_profile_name()
        except Exception:
            return "Default"

    def create_new_profile(self, name: str) -> None:
        create_profile(name)

    def remove_profile(self, name: str) -> None:
        delete_profile(name)

    def make_desktop_shortcut(self, profile: Optional[str] = None) -> Path:
        if profile and profile != "Default":
            return write_profile_shortcut(profile)
        return write_play_shortcut()

    # --------------------------------------------------------------------------
    # Diagnostics & Tools
    # --------------------------------------------------------------------------
    def run_system_doctor(self) -> Tuple[int, str]:
        """Run system health check."""
        code, out, err = run_cli_command(["doctor"])
        return code, out or err

    def run_network_doctor(self) -> Tuple[int, str]:
        """Run network diagnostics."""
        code, out, err = run_cli_command(["doctor", "--network"])
        return code, out or err

    def reset_wine_prefix(self) -> None:
        """Reset the Wine prefix."""
        reset_prefix()

    def import_game_content(self, file_paths: List[str]) -> Tuple[int, List[str]]:
        """Import .mcpack / .mcaddon / .mcworld / .mcskin files."""
        return import_content(file_paths)

    def ack_gpu_crash(self) -> None:
        """Clear the interrupted-launch GPU safety marker."""
        acknowledge_gpu_crash()

    def has_gpu_crash_marker(self) -> bool:
        """Check if GPU safety barrier is active."""
        try:
            status = gpu_crash_acknowledgement_status()
            return bool(getattr(status, "can_acknowledge", False) or getattr(status, "marker_present", False))
        except Exception:
            return False

    # --------------------------------------------------------------------------
    # Playtime Tracking & User Folders
    # --------------------------------------------------------------------------
    def start_session(self) -> None:
        import time
        self.session_start_time = time.time()

    def end_session(self) -> None:
        import time
        if hasattr(self, "session_start_time") and self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            cur = int(self.get_setting("playtime_seconds", 0))
            self.set_setting("playtime_seconds", cur + elapsed)
            self.session_start_time = None

    def get_total_playtime_formatted(self) -> str:
        sec = int(self.get_setting("playtime_seconds", 0))
        h = sec // 3600
        m = (sec % 3600) // 60
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    def get_session_playtime_formatted(self) -> str:
        import time
        if hasattr(self, "session_start_time") and self.session_start_time:
            sec = int(time.time() - self.session_start_time)
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            if h > 0:
                return f"{h}h {m}m"
            return f"{m}m {s}s"
        return "0m"

    def get_mojang_dir(self) -> Optional[Path]:
        """Find the com.mojang data folder inside the active Wine prefix."""
        base = DATA / "compatdata" / "pfx" / "drive_c" / "users" / "steamuser" / "AppData" / "Roaming" / "Minecraft Bedrock" / "Users"
        if base.is_dir():
            matches = list(base.glob("*/games/com.mojang"))
            # Prefer non-Shared if exists
            for m in matches:
                if m.is_dir() and "Shared" not in str(m):
                    return m
            if matches and matches[0].is_dir():
                return matches[0]
        return None

    def open_mojang_subfolder(self, subfolder: str = "minecraftWorlds") -> bool:
        import subprocess
        mojang = self.get_mojang_dir()
        if mojang:
            target = mojang / subfolder
            target.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(["xdg-open", str(target)])
            return True
        return False

    def backup_worlds(self, dest_dir: Optional[Path] = None) -> Optional[Path]:
        """Create a .zip archive backup of the user's minecraftWorlds directory."""
        import zipfile
        import time
        mojang = self.get_mojang_dir()
        if not mojang:
            return None
        worlds_dir = mojang / "minecraftWorlds"
        if not worlds_dir.is_dir():
            return None

        out_dir = dest_dir or Path.home()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        out_zip = out_dir / f"Minecraft_Bedrock_Worlds_{timestamp}.zip"

        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(worlds_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(worlds_dir)
                    zf.write(file_path, arcname)

        return out_zip


# Singleton instance
engine = Engine()

