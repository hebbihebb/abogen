# Repository Guidelines

## Project Structure & Module Organization
- `abogen/` holds the application code: `main.py`/`gui.py` start the PyQt6 app, `tts_backends/` implements Kokoro and F5-TTS engines, and helpers like `voice_formulas.py` manage presets and mixing.
- `abogen/assets/` and `abogen/resources/` contain packaged icons and metadata; keep large binaries and model caches out of git.
- `scripts/` contains backend smoke tests; root-level `test_*.py` files are interactive end-to-end voice cloning/mixing scripts that write audio to `out/`.
- `demo/` and `docs/` provide usage guides and screenshots; utility scripts such as `create_reference.py` and `list_voices.py` demonstrate common workflows.

## Build, Test, and Development Commands
- `python -m pip install -e .` (inside a virtualenv) installs dependencies for local development.
- `abogen` or `python -m abogen.main` launches the GUI; set `HF_HUB_OFFLINE=1` if you want Kokoro to avoid network access.
- `python scripts/test_kokoro_backend.py` runs a lightweight backend smoke test on CPU; `python test_voice_mix_simple.py` exercises the Kokoro -> F5-TTS flow (downloads models, writes to `out/`).
- Packaging check: `python -m build` (after `pip install build`) produces sdist and wheel via Hatchling.

## Coding Style & Naming Conventions
- Format with Black (4-space indents, double quotes commonly used). Functions and methods use `snake_case`, classes use `PascalCase`, and constants use `UPPER_SNAKE_CASE`.
- Prefer pathlib-friendly code paths, explicit imports, and small helpers over sprawling functions. Keep GUI-facing strings and defaults centralized in `constants.py` where possible.

## Testing Guidelines
- Tests are long-running E2E scripts rather than quick unit tests; run only the smallest relevant script to avoid unnecessary model downloads. Clean any `out/` artifacts before committing.
- When adding tests, keep audio snippets short, gate GPU-specific logic behind device flags, and ensure CPU fallback so CI and contributors without GPUs can run them.

## Commit & Pull Request Guidelines
- Commit subjects follow short, imperative phrasing (e.g., `Fix F5-TTS logging`) and should remain tightly scoped.
- PRs should describe the user flow or UI surface touched, any new dependencies/model downloads, and before/after behavior. Link issues when available, attach screenshots for UI changes, and note how you validated your changes (commands run, platform, device).
