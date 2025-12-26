#!/usr/bin/env python3
"""
AIMD Backend Build Script

Compiles server.py into a standalone binary using PyInstaller.
Run: python build_backend.py

Output: bin/aimd-server-{platform}-{arch}[.exe]
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform_info() -> tuple[str, str]:
    """Get normalized platform and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Normalize platform
    if system == "darwin":
        plat = "darwin"
    elif system == "windows":
        plat = "win32"
    elif system == "linux":
        plat = "linux"
    else:
        plat = system
    
    # Normalize architecture
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    elif machine in ("i386", "i686"):
        arch = "x86"
    else:
        arch = machine
    
    return plat, arch


def build():
    """Build the backend binary."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    server_py = script_dir / "server.py"
    bin_dir = project_root / "bin"
    
    plat, arch = get_platform_info()
    
    # Output name
    if plat == "win32":
        output_name = f"aimd-server-{plat}-{arch}.exe"
    else:
        output_name = f"aimd-server-{plat}-{arch}"
    
    print(f"[BUILD] Building for: {plat}-{arch}")
    print(f"[BUILD] Output: bin/{output_name}")
    
    # Ensure bin directory exists
    bin_dir.mkdir(exist_ok=True)
    
    # Build with PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable
        "--clean",             # Clean cache
        "--noconfirm",         # Overwrite without asking
        "--name", output_name.replace(".exe", ""),
        "--distpath", str(bin_dir),
        "--workpath", str(script_dir / "build"),
        "--specpath", str(script_dir / "build"),
        str(server_py)
    ]
    
    print(f"[BUILD] Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Build successful: {bin_dir / output_name}")
        
        # Cleanup build artifacts
        build_dir = script_dir / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            print("[OK] Cleaned up build artifacts")
            
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)


if __name__ == "__main__":
    build()
