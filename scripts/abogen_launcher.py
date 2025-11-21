"""
Temporary GUI launcher for Abogen.

Usage:
    # Run from repo root
    python scripts/abogen_launcher.py

This opens a small Tk window with a Launch button. By default it starts Abogen
in the existing conda env at /mnt/Games/conda_envs/abogen and forces
QT_QPA_PLATFORM=offscreen to avoid display issues. You can toggle offscreen or
set a custom DISPLAY before launching.
"""

import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk


CONDA_PREFIX = "/mnt/Games/conda_envs/abogen"


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Abogen Launcher")
        self.geometry("520x360")

        self.proc: subprocess.Popen | None = None

        # Controls
        self.offscreen_var = tk.BooleanVar(value=True)
        self.display_var = tk.StringVar(value=os.environ.get("DISPLAY", ":0"))

        ttk.Label(self, text="DISPLAY").pack(anchor="w", padx=10, pady=(10, 0))
        ttk.Entry(self, textvariable=self.display_var).pack(
            fill="x", padx=10, pady=2
        )

        ttk.Checkbutton(
            self,
            text="Force QT_QPA_PLATFORM=offscreen",
            variable=self.offscreen_var,
        ).pack(anchor="w", padx=10, pady=4)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=6)
        self.launch_btn = ttk.Button(btns, text="Launch Abogen", command=self.launch)
        self.launch_btn.pack(side="left")
        self.stop_btn = ttk.Button(btns, text="Terminate", state="disabled", command=self.stop)
        self.stop_btn.pack(side="left", padx=6)

        # Output area
        self.output = tk.Text(self, height=14, wrap="word", state="disabled")
        self.output.pack(fill="both", expand=True, padx=10, pady=8)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, line: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", line + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def launch(self) -> None:
        if self.proc:
            self.log("Process already running.")
            return

        env = os.environ.copy()
        env["DISPLAY"] = self.display_var.get().strip()
        if self.offscreen_var.get():
            env["QT_QPA_PLATFORM"] = "offscreen"

        cmd = [
            "conda",
            "run",
            "-p",
            CONDA_PREFIX,
            "abogen",
        ]

        self.log(f"Launching: {' '.join(cmd)}")
        self.log(f"DISPLAY={env.get('DISPLAY', '')}")
        if self.offscreen_var.get():
            self.log("QT_QPA_PLATFORM=offscreen")

        try:
            self.proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
        except Exception as exc:  # pragma: no cover - manual use only
            self.log(f"Failed to start: {exc}")
            self.proc = None
            return

        self.launch_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._pump_output, daemon=True).start()

    def _pump_output(self) -> None:
        assert self.proc is not None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break
            self.log(line.rstrip())

        rc = self.proc.wait()
        self.log(f"Process exited with code {rc}")
        self.proc = None
        self.after(0, self._reset_buttons)

    def stop(self) -> None:
        if not self.proc:
            return
        self.proc.terminate()
        self.log("Termination requested...")  # racing is fine here

    def _reset_buttons(self) -> None:
        self.launch_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def on_close(self) -> None:
        self.stop()
        self.destroy()


if __name__ == "__main__":
    Launcher().mainloop()
