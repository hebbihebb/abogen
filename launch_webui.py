from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Paths
ROOT = Path(__file__).parent
ENV_DIR = Path("/mnt/Games/conda_envs/abogen")
BACKEND_DIR = ROOT / "webui" / "backend"
FRONTEND_DIR = ROOT / "webui" / "frontend"


def main() -> None:
    # Prefer any existing frontend build; otherwise run dev server.
    dist_dir = FRONTEND_DIR / "dist"
    backend_cmd = [
        str(ENV_DIR / "bin" / "python"),
        str(BACKEND_DIR / "main.py"),
    ]

    env = os.environ.copy()
    # Ensure Qt plugins resolve if the GUI is ever launched from this env too
    env.setdefault(
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        str(ENV_DIR / "lib" / "python3.12" / "site-packages" / "PyQt6" / "Qt6" / "plugins" / "platforms"),
    )

    if not dist_dir.exists():
        sys.stderr.write(
            "Frontend build not found at webui/frontend/dist.\n"
            "Open another terminal and run:\n"
            "  cd webui/frontend && npm install && npm run build\n"
            "Or run the dev server (npm run dev) separately and ignore this warning.\n"
        )

    try:
        subprocess.run(
            backend_cmd,
            cwd=BACKEND_DIR,
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"Web UI backend exited with code {exc.returncode}\n")
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
