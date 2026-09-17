"""
deepslate.bridge.cli_bridge
CLI execution bridge for BedrockOnLinux commands.
"""

import subprocess
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Callable

CLI_BIN = "bedrock-on-linux"

def is_cli_installed() -> bool:
    """Check if bedrock-on-linux is found in PATH."""
    return shutil.which(CLI_BIN) is not None

def run_cli_command(args: List[str], check: bool = False, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    """Execute a bedrock-on-linux CLI command synchronously and return (code, stdout, stderr)."""
    cmd = [CLI_BIN] + args
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=check
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        return 1, "", str(exc)

def run_cli_streaming(
    args: List[str],
    line_callback: Optional[Callable[[str], None]] = None,
    error_callback: Optional[Callable[[str], None]] = None
) -> subprocess.Popen:
    """Launch a CLI command asynchronously, streaming lines to callbacks."""
    cmd = [CLI_BIN] + args
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return proc
