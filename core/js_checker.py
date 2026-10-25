import os
import sys
import shutil
from pathlib import Path
from typing import Optional

def get_deno_dir() -> Optional[str]:
    """Finds the directory containing deno.exe."""
    # 1. Next to the running executable or script
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).resolve().parent.parent

    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    user_home = Path.home()

    search_dirs = [
        exe_dir / "bin",
        exe_dir,
        exe_dir / "_internal" / "bin",
        exe_dir / "_internal",
        user_home / ".gjat_downloader" / "bin",
        user_home / ".deno" / "bin",
        local_app_data / "Programs" / "GjatDownloader" / "bin",
        local_app_data / "Programs" / "GjatDownloader",
        local_app_data / "Programs" / "GjatDownloader" / "_internal" / "bin",
        local_app_data / "Programs" / "GjatDownloader" / "_internal",
        local_app_data / "Microsoft" / "WinGet" / "Packages" / "DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe",
    ]

    for d in search_dirs:
        if (d / "deno.exe").exists() or (d / "deno.EXE").exists():
            return str(d)

    # 2. Check system PATH
    sys_deno = shutil.which("deno")
    if sys_deno:
        return str(Path(sys_deno).parent)

    # 3. Search winget packages folder for any deno installation
    winget_pkg_dir = local_app_data / "Microsoft" / "WinGet" / "Packages"
    if winget_pkg_dir.exists():
        for sub in winget_pkg_dir.iterdir():
            if "deno" in sub.name.lower() and (sub / "deno.exe").exists():
                return str(sub)

    return None

def setup_js_runtime():
    """Ensures Deno / JS runtime is present in PATH for yt-dlp."""
    deno_dir = get_deno_dir()
    if deno_dir:
        cur_path = os.environ.get("PATH", "")
        if deno_dir not in cur_path:
            os.environ["PATH"] = deno_dir + os.pathsep + cur_path
        return deno_dir
    return None
