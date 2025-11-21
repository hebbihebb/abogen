from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Path to the conda environment that has Abogen + F5-TTS installed.
ENV_DIR = Path("/mnt/Games/conda_envs/abogen")
ABOGEN_BIN = ENV_DIR / "bin" / "abogen"


def main() -> None:
    if not ABOGEN_BIN.exists():
        sys.stderr.write(
            f"Abogen launch script not found at {ABOGEN_BIN}.\n"
            "Make sure the conda environment is installed and adjust ENV_DIR if needed.\n"
        )
        sys.exit(1)

    env = os.environ.copy()
    env.setdefault(
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        str(ENV_DIR / "lib" / "python3.12" / "site-packages" / "PyQt6" / "Qt6" / "plugins" / "platforms"),
    )

    try:
        subprocess.run([str(ABOGEN_BIN)], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"Abogen exited with code {exc.returncode}\n")
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
