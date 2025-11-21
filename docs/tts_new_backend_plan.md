# TTS Backend Integration Plan: F5-TTS Support for Abogen

## Executive Summary

This document outlines the plan to extend Abogen with a pluggable TTS backend architecture, starting with F5-TTS integration. The goal is to enable users to choose between different TTS engines (Kokoro, F5-TTS, and future engines) while maintaining backward compatibility and code quality.

## Current Architecture Analysis

### Existing TTS Integration (Kokoro-82M)

**Key Components:**
- **Engine**: Kokoro-82M from HuggingFace (hexgrad/Kokoro-82M)
- **Location**: `abogen/utils.py:349-353` (loader), `abogen/conversion.py:831` (instantiation)
- **Pattern**: Direct dependency injection - `KPipeline` class passed to `ConversionThread`
- **Interface**: No formal abstraction - Kokoro methods called directly

**Pipeline Flow:**
1. GUI loads KPipeline in background thread (`gui.py:2130`)
2. ConversionThread receives KPipeline class (`conversion.py:622`)
3. TTS instantiated with lang_code, repo_id, device (`conversion.py:831`)
4. Chapter loop calls `tts(text, voice, speed, split_pattern)` (`conversion.py:1337-1342`)
5. Results yield audio segments incrementally

**Kokoro-Specific Features Used:**
- `tts(text, voice, speed, split_pattern)` - Generator yielding audio segments
- `tts.load_single_voice(voice_name)` - Voice tensor loading for mixing
- Result format: `result.audio`, `result.graphemes`, `result.tokens`
- Voice formulas: Weighted blending of voice embeddings

### Limitations for Multi-Engine Support

❌ **No abstraction layer** - Direct coupling to Kokoro API
❌ **Hard-coded result expectations** - Assumes Kokoro's result format
❌ **No engine selection UI** - Only Kokoro is available
❌ **Voice system tied to Kokoro** - 58 internal voices are Kokoro-specific

---

## Proposed Architecture: Pluggable TTS Backends

### Design Principles

1. **Protocol-based abstraction** - Use Python `Protocol` for engine interface
2. **Backward compatibility** - Kokoro remains default, existing configs work
3. **Isolation** - Engine-specific code in separate modules
4. **Factory pattern** - Central registry for engine selection
5. **Graceful degradation** - Clear errors if engine unavailable

### New Directory Structure

```
abogen/
├── tts_backends/              # New package for TTS engines
│   ├── __init__.py            # Factory & engine registry
│   ├── base.py                # TTSBackend Protocol definition
│   ├── kokoro_backend.py      # Kokoro wrapper (refactored)
│   └── f5_tts_backend.py      # F5-TTS implementation
├── conversion.py              # Modified to use backend abstraction
├── gui.py                     # Add engine selection dropdown
├── constants.py               # Add ENGINE_CONFIGS
└── utils.py                   # Keep backward-compatible loaders
```

### Core Abstraction: TTSBackend Protocol

**File**: `abogen/tts_backends/base.py`

```python
from typing import Protocol, Iterator, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class TTSResult:
    """Normalized result format across all TTS engines."""
    audio: np.ndarray      # Audio samples (mono or stereo)
    sample_rate: int       # Sample rate (e.g., 24000)
    graphemes: list[str]   # Optional: Phoneme/grapheme breakdown
    tokens: list          # Optional: Token representation

class TTSBackend(Protocol):
    """Protocol for TTS engine implementations."""

    def __init__(
        self,
        lang_code: str,
        device: str = "cpu",
        **engine_specific_kwargs
    ):
        """Initialize the TTS engine."""
        ...

    def __call__(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        split_pattern: Optional[str] = None,
    ) -> Iterator[TTSResult]:
        """
        Synthesize text to audio, yielding segments incrementally.

        Args:
            text: Input text to synthesize
            voice: Voice identifier (engine-specific format)
            speed: Speech speed multiplier (1.0 = normal)
            split_pattern: Regex pattern for text splitting (optional)

        Yields:
            TTSResult objects with audio segments
        """
        ...

    def load_single_voice(self, voice_name: str) -> any:
        """
        Load a voice embedding/model for blending (optional).
        Only needed if engine supports voice mixing.
        """
        raise NotImplementedError("Voice mixing not supported")

    @property
    def supports_voice_mixing(self) -> bool:
        """Whether this engine supports voice formula blending."""
        return False

    @property
    def available_voices(self) -> list[str]:
        """List of voice identifiers supported by this engine."""
        return []
```

### Engine Factory

**File**: `abogen/tts_backends/__init__.py`

```python
from typing import Type, Optional
from .base import TTSBackend
from .kokoro_backend import KokoroBackend
from .f5_tts_backend import F5TTSBackend

ENGINE_REGISTRY = {
    "kokoro": KokoroBackend,
    "f5_tts": F5TTSBackend,
}

def create_tts_engine(
    engine_name: str,
    lang_code: str,
    device: str = "cpu",
    **kwargs
) -> TTSBackend:
    """
    Factory function to create TTS engine instances.

    Args:
        engine_name: "kokoro", "f5_tts", etc.
        lang_code: Language code (e.g., "a" for American English)
        device: "cpu", "cuda", or "mps"
        **kwargs: Engine-specific parameters

    Returns:
        Initialized TTS backend instance

    Raises:
        ValueError: If engine_name not recognized
        ImportError: If engine dependencies not installed
    """
    if engine_name not in ENGINE_REGISTRY:
        available = ", ".join(ENGINE_REGISTRY.keys())
        raise ValueError(
            f"Unknown TTS engine '{engine_name}'. "
            f"Available engines: {available}"
        )

    engine_class = ENGINE_REGISTRY[engine_name]

    try:
        return engine_class(lang_code=lang_code, device=device, **kwargs)
    except ImportError as e:
        raise ImportError(
            f"Failed to load '{engine_name}' engine. "
            f"Missing dependencies: {e}. "
            f"Install with: pip install abogen[{engine_name}]"
        )

def get_available_engines() -> list[str]:
    """Return list of engine names that can be loaded."""
    available = []
    for name, engine_class in ENGINE_REGISTRY.items():
        try:
            # Check if dependencies are available
            engine_class._check_dependencies()
            available.append(name)
        except ImportError:
            pass
    return available
```

---

## F5-TTS Integration Details

### F5-TTS Overview

**Repository**: https://github.com/SWivid/F5-TTS
**Model Type**: Diffusion-based TTS with flow matching
**Key Features**:
- Zero-shot voice cloning from reference audio
- High-quality multi-lingual synthesis
- Controllable speed and prosody

**Challenges**:
- Requires reference audio for voice (no built-in voice library like Kokoro)
- Longer inference time than Kokoro
- May need phoneme preprocessing for some languages

### Implementation: F5TTSBackend

**File**: `abogen/tts_backends/f5_tts_backend.py`

```python
import re
import numpy as np
from pathlib import Path
from typing import Iterator, Optional
from dataclasses import dataclass
import logging

from .base import TTSResult, TTSBackend

logger = logging.getLogger(__name__)

class F5TTSBackend:
    """
    F5-TTS backend for Abogen.

    Provides TTS synthesis using F5-TTS diffusion model with
    reference voice cloning capabilities.
    """

    def __init__(
        self,
        lang_code: str,
        device: str = "cpu",
        model_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize F5-TTS backend.

        Args:
            lang_code: Language code (currently only 'a' for English supported)
            device: "cpu", "cuda", or "mps"
            model_path: Path to F5-TTS checkpoint (auto-downloads if None)
            vocab_path: Path to vocab file (auto-downloads if None)
            reference_audio: Path to reference voice audio (WAV, ~5-10s)
            reference_text: Transcript of reference audio
        """
        self.lang_code = lang_code
        self.device = device
        self.model_path = model_path
        self.reference_audio = reference_audio
        self.reference_text = reference_text

        logger.info(f"Initializing F5-TTS backend on {device}...")

        try:
            from f5_tts.infer.utils_infer import load_model, infer_process
            self._load_model = load_model
            self._infer_process = infer_process
        except ImportError:
            raise ImportError(
                "F5-TTS not installed. Install with: "
                "pip install git+https://github.com/SWivid/F5-TTS.git"
            )

        # Load model (auto-download if needed)
        self.model = self._load_model(
            model_path=model_path,
            vocab_path=vocab_path,
            device=device
        )

        logger.info("F5-TTS model loaded successfully")

    @staticmethod
    def _check_dependencies():
        """Check if F5-TTS is installed."""
        import f5_tts

    def __call__(
        self,
        text: str,
        voice: str,
        speed: float = 1.0,
        split_pattern: Optional[str] = None,
    ) -> Iterator[TTSResult]:
        """
        Synthesize text using F5-TTS.

        For F5-TTS, 'voice' parameter is interpreted as:
        - Path to reference audio file, OR
        - Name of a bundled reference voice (if we provide some)

        Args:
            text: Input text to synthesize
            voice: Reference audio path or voice name
            speed: Speech speed multiplier (1.0 = normal)
            split_pattern: Regex pattern for splitting text into chunks

        Yields:
            TTSResult objects with audio segments
        """
        # Use provided voice or fall back to initialization reference
        ref_audio = voice if Path(voice).exists() else self.reference_audio
        ref_text = self.reference_text  # May need per-voice mapping

        if not ref_audio:
            raise ValueError(
                "F5-TTS requires reference audio. "
                "Provide via 'voice' parameter or 'reference_audio' config."
            )

        # Split text into manageable chunks
        chunks = self._split_text(text, split_pattern)

        logger.info(f"Synthesizing {len(chunks)} text chunks with F5-TTS...")

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

            # Run inference
            audio, sample_rate = self._infer_process(
                model=self.model,
                ref_audio=ref_audio,
                ref_text=ref_text,
                gen_text=chunk,
                speed=speed,
                device=self.device
            )

            # Convert to numpy array if needed
            if not isinstance(audio, np.ndarray):
                audio = np.array(audio)

            yield TTSResult(
                audio=audio,
                sample_rate=sample_rate,
                graphemes=[],  # F5-TTS doesn't expose graphemes
                tokens=[]
            )

        logger.info("F5-TTS synthesis complete")

    def _split_text(self, text: str, split_pattern: Optional[str]) -> list[str]:
        """Split text into chunks for processing."""
        if split_pattern:
            chunks = re.split(split_pattern, text)
        else:
            # Default: split on sentence boundaries, max ~200 words per chunk
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current = []
            current_len = 0

            for sent in sentences:
                words = sent.split()
                if current_len + len(words) > 200 and current:
                    chunks.append(" ".join(current))
                    current = [sent]
                    current_len = len(words)
                else:
                    current.append(sent)
                    current_len += len(words)

            if current:
                chunks.append(" ".join(current))

        return [c.strip() for c in chunks if c.strip()]

    @property
    def supports_voice_mixing(self) -> bool:
        """F5-TTS doesn't support Kokoro-style voice formula mixing."""
        return False

    @property
    def available_voices(self) -> list[str]:
        """
        F5-TTS uses reference audio, so "voices" are user-provided.
        We could bundle some default reference voices in the future.
        """
        return []  # Empty for now, user provides reference audio
```

### Configuration Changes

**File**: `abogen/constants.py`

```python
# Add engine configuration section

ENGINE_CONFIGS = {
    "kokoro": {
        "display_name": "Kokoro-82M (Local)",
        "description": "Fast, 58 built-in voices, multi-language support",
        "requires_gpu": False,
        "supports_voice_mixing": True,
        "default_params": {
            "repo_id": "hexgrad/Kokoro-82M",
        }
    },
    "f5_tts": {
        "display_name": "F5-TTS (Local)",
        "description": "High-quality, voice cloning, requires reference audio",
        "requires_gpu": True,  # Very slow on CPU
        "supports_voice_mixing": False,
        "default_params": {
            "model_path": None,  # Auto-download
            "vocab_path": None,
            "reference_audio": None,  # User must provide
            "reference_text": None,
        }
    },
}

DEFAULT_ENGINE = "kokoro"
```

---

## Files to Modify

### 1. `abogen/conversion.py`

**Changes:**
- Replace `self.KPipeline` with `self.tts_engine` (backend instance)
- Update `__init__` to accept engine name + config instead of KPipeline class
- Remove Kokoro-specific assumptions
- Handle engines without voice mixing support

**Key modifications:**

```python
# Line 622 - ConversionThread.__init__
def __init__(
    self,
    # ... existing params ...
    engine_name: str = "kokoro",  # NEW
    engine_config: dict = None,   # NEW
    kpipeline_class=None,  # DEPRECATED but kept for compatibility
):
    # ... existing init code ...

    # NEW: Initialize TTS backend
    from abogen.tts_backends import create_tts_engine

    if kpipeline_class:  # Backward compatibility
        # Wrap legacy Kokoro usage
        self.tts_engine = KokoroBackend(
            lang_code=self.lang_code,
            device=device,
            kpipeline_class=kpipeline_class
        )
    else:
        self.tts_engine = create_tts_engine(
            engine_name=engine_name,
            lang_code=self.lang_code,
            device=device,
            **(engine_config or {})
        )

# Line 831 - Remove direct KPipeline instantiation
# OLD: tts = self.KPipeline(lang_code=..., repo_id=..., device=...)
# NEW: tts = self.tts_engine (already instantiated)

# Line 1337-1342 - TTS call remains the same (uses Protocol)
for result in tts(
    chapter_text,
    voice=loaded_voice,
    speed=self.speed,
    split_pattern=self.split_pattern,
):
    # Process result.audio, result.sample_rate, etc.
```

### 2. `abogen/gui.py`

**Changes:**
- Add engine selection dropdown in settings area
- Load engine-specific config panel
- Pass engine selection to ConversionThread
- Update voice list based on selected engine
- Disable voice mixing UI if engine doesn't support it

**New UI elements:**

```python
# Around line 920 - Add engine selection
self.engine_label = QLabel("TTS Engine:")
self.engine_combo = QComboBox()
self.engine_combo.addItems([
    cfg["display_name"] for cfg in ENGINE_CONFIGS.values()
])
self.engine_combo.currentTextChanged.connect(self._on_engine_changed)

# Add to layout
settings_layout.addWidget(self.engine_label)
settings_layout.addWidget(self.engine_combo)

# Line 2061 - Update ConversionThread instantiation
self.conversion_thread = ConversionThread(
    # ... existing params ...
    engine_name=self.selected_engine,  # NEW
    engine_config=self.engine_config,   # NEW
)

# NEW: Handler for engine selection
def _on_engine_changed(self, engine_display_name):
    """Update UI when user changes TTS engine."""
    # Map display name back to engine key
    for key, cfg in ENGINE_CONFIGS.items():
        if cfg["display_name"] == engine_display_name:
            self.selected_engine = key
            break

    # Load engine-specific voices
    self._update_voice_list()

    # Show/hide voice mixing controls
    supports_mixing = ENGINE_CONFIGS[self.selected_engine]["supports_voice_mixing"]
    self.voice_formula_widgets.setVisible(supports_mixing)

    # Load engine config panel
    self._load_engine_config_panel(self.selected_engine)
```

### 3. `abogen/voice_formulas.py`

**Changes:**
- Check if engine supports voice mixing before attempting
- Gracefully handle engines without `load_single_voice` method

```python
def get_new_voice(pipeline, voice_formula: str, use_gpu: bool):
    """Parse and blend voice formula, if supported by engine."""

    # Check if engine supports mixing
    if not getattr(pipeline, 'supports_voice_mixing', False):
        logger.warning(
            f"Current TTS engine doesn't support voice mixing. "
            f"Using first voice from formula: {voice_formula}"
        )
        # Extract first voice name from formula
        first_voice = voice_formula.split('*')[0].strip()
        return first_voice

    # Existing voice mixing logic...
```

---

## Implementation Phases

### Phase 1: Abstraction Layer (Days 1-2)
1. ✅ Create `abogen/tts_backends/` package
2. ✅ Implement `base.py` with TTSBackend Protocol and TTSResult
3. ✅ Implement `kokoro_backend.py` wrapping existing Kokoro usage
4. ✅ Implement factory in `__init__.py`
5. ✅ Add ENGINE_CONFIGS to `constants.py`

### Phase 2: Refactor Existing Code (Day 2)
6. ✅ Modify `conversion.py` to use backend abstraction
7. ✅ Update `voice_formulas.py` for engine compatibility
8. ✅ Test that Kokoro still works via new abstraction (backward compatibility)

### Phase 3: F5-TTS Implementation (Days 3-4)
9. ✅ Research F5-TTS API and installation
10. ✅ Implement `f5_tts_backend.py`
11. ✅ Test basic synthesis with sample text
12. ✅ Handle reference audio loading and voice selection

### Phase 4: GUI Integration (Day 4-5)
13. ✅ Add engine selection dropdown
14. ✅ Add F5-TTS config panel (reference audio picker)
15. ✅ Update voice list loading per engine
16. ✅ Save/load engine preference in config.json

### Phase 5: Testing & Documentation (Days 5-6)
17. ✅ Create `scripts/test_f5_tts_backend.py`
18. ✅ Test full chapter synthesis with both engines
19. ✅ Update README.md with installation instructions
20. ✅ Create `docs/tts_engines.md` comparison guide

---

## Risk Mitigation

### Risk: F5-TTS too slow on CPU
**Mitigation**: Add clear GPU requirement in docs, show speed estimate in GUI

### Risk: F5-TTS reference audio format issues
**Mitigation**: Provide sample reference voices, validate audio format on load

### Risk: Breaking existing Kokoro users
**Mitigation**: Keep Kokoro as default, maintain backward compatibility with `kpipeline_class` parameter

### Risk: F5-TTS dependency conflicts
**Mitigation**: Make F5-TTS an optional dependency via `pip install abogen[f5_tts]`

---

## Testing Strategy

### Unit Tests
- `test_tts_backends.py`: Test each backend's Protocol compliance
- `test_engine_factory.py`: Test engine selection and error handling

### Integration Tests
- `test_kokoro_backward_compat.py`: Ensure Kokoro still works
- `test_f5_synthesis.py`: Full chapter synthesis with F5-TTS

### Manual Test Script
```python
# scripts/test_f5_tts_backend.py
from abogen.tts_backends import create_tts_engine
from pathlib import Path

def test_f5_synthesis():
    """Test F5-TTS backend with sample text."""

    engine = create_tts_engine(
        engine_name="f5_tts",
        lang_code="a",
        device="cuda",  # or "cpu" for slower inference
        reference_audio="path/to/reference.wav",
        reference_text="This is the reference transcript."
    )

    test_text = "Hello world! This is a test of F5-TTS integration with Abogen."

    output_path = Path("out/test_f5_tts.wav")
    output_path.parent.mkdir(exist_ok=True)

    print("Synthesizing...")
    for i, result in enumerate(engine(test_text, voice="", speed=1.0)):
        print(f"Chunk {i}: {len(result.audio)} samples @ {result.sample_rate}Hz")

    # Save final result
    import soundfile as sf
    sf.write(output_path, result.audio, result.sample_rate)
    print(f"✓ Saved to {output_path}")

if __name__ == "__main__":
    test_f5_synthesis()
```

---

## Future Enhancements

1. **More engines**: OpenAI TTS, ElevenLabs, Azure Cognitive Services
2. **Voice library for F5-TTS**: Bundle quality reference voices
3. **Speed optimizations**: Batch processing, model quantization
4. **Voice conversion**: Convert Kokoro voices to F5-TTS style
5. **Hybrid mode**: Use Kokoro for speed, F5-TTS for quality on select chapters

---

## Success Criteria

✅ Users can select F5-TTS from dropdown
✅ F5-TTS synthesizes full chapter successfully
✅ Kokoro still works (backward compatibility)
✅ Clear error messages if F5-TTS not installed
✅ Documentation explains installation and usage
✅ Test script validates F5-TTS functionality
✅ No performance regression for Kokoro users

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Author**: Claude (Sonnet 4.5)
