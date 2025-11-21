# TTS Engines Guide for Abogen

This guide provides detailed information about the TTS (Text-to-Speech) engines available in Abogen, helping you choose the right one for your use case.

## Table of Contents

- [Overview](#overview)
- [Engine Comparison](#engine-comparison)
- [Kokoro-82M](#kokoro-82m)
- [F5-TTS](#f5-tts)
- [When to Use Which Engine](#when-to-use-which-engine)
- [Troubleshooting](#troubleshooting)
- [Adding New Engines](#adding-new-engines)

---

## Overview

Abogen supports a pluggable TTS backend architecture, allowing you to choose between different synthesis engines based on your needs. Each engine has different strengths:

- **Kokoro-82M**: Fast, lightweight, 58 built-in voices (default)
- **F5-TTS**: High-quality voice cloning from reference audio

You can switch engines via the "TTS Engine" dropdown in the Abogen GUI.

---

## Engine Comparison

### Feature Matrix

| Feature | Kokoro-82M | F5-TTS |
|---------|-----------|---------|
| **Speed** | ⚡⚡⚡ Very Fast | 🐌 Moderate (GPU) / Very Slow (CPU) |
| **Quality** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Voice Options** | 58 built-in | Unlimited (cloning) |
| **Voice Mixing** | ✅ Yes | ❌ No |
| **Languages** | 9 languages | Multi-lingual |
| **GPU Required** | ❌ Optional | ✅ Highly Recommended |
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate |
| **Offline Usage** | ✅ Yes | ✅ Yes (after model download) |
| **Reference Audio Required** | ❌ No | ✅ Yes |

### Performance Benchmarks

Tested on **RTX 2070 8GB** with ~3,000 characters (3.5 minute output):

| Engine | Device | Processing Time | Real-time Factor |
|--------|--------|----------------|------------------|
| Kokoro-82M | CPU | ~15s | ~14x faster |
| Kokoro-82M | GPU (CUDA) | ~8s | ~26x faster |
| F5-TTS | CPU | ~5-10 minutes | ~0.6x slower |
| F5-TTS | GPU (CUDA) | ~45s | ~4.6x faster |

*Real-time factor: 1.0x = generates audio at the same speed as playback duration*

---

## Kokoro-82M

### Overview

Kokoro-82M is the default TTS engine in Abogen. It's a lightweight, fast model with 82 million parameters, optimized for speed without sacrificing quality.

### Key Features

- **58 Built-in Voices**:
  - American English: `af_*`, `am_*`
  - British English: `bf_*`, `bm_*`
  - Spanish: `ef_*`, `em_*`
  - French: `ff_*`, `fm_*`
  - Hindi: `hf_*`, `hm_*`
  - Italian: `if_*`, `im_*`
  - Japanese: `jf_*`, `jm_*`
  - Portuguese: `pf_*`, `pm_*`
  - Chinese: `zf_*`, `zm_*`

- **Voice Mixing**: Create custom voices by blending multiple voices
  - Example: `af_heart*0.5 + am_adam*0.5` (50/50 blend)
  - Save custom blends as profiles for reuse

- **CPU-Friendly**: Runs well on CPU, excellent on GPU

### Installation

Kokoro is installed by default with Abogen:
```bash
pip install abogen  # Includes Kokoro
```

### Usage

1. Select **Kokoro-82M** from the "TTS Engine" dropdown (default)
2. Choose a voice from the 58 built-in options
3. Optionally create custom voice blends via Voice Mixer
4. Start conversion

### Voice Naming Convention

Voice names follow the pattern: `{language}{gender}_{name}`

- **Language codes**: `a` (American), `b` (British), `e` (Spanish), `f` (French), `h` (Hindi), `i` (Italian), `j` (Japanese), `p` (Portuguese), `z` (Chinese)
- **Gender**: `f` (female), `m` (male)
- **Name**: Descriptive identifier (e.g., `heart`, `adam`, `sarah`)

Examples:
- `af_heart`: American English, Female, "Heart" voice
- `bm_lewis`: British English, Male, "Lewis" voice
- `ef_emma`: Spanish, Female, "Emma" voice

### Limitations

- Fixed voice library (no custom voices beyond mixing)
- Quality is good but not state-of-the-art
- Voice mixing only works on CPU (GPU has known issues)

---

## F5-TTS

### Overview

F5-TTS is a state-of-the-art diffusion-based TTS model with zero-shot voice cloning capabilities. It can clone any voice from a short reference audio sample.

### Key Features

- **Zero-Shot Voice Cloning**: Synthesize in any voice from 5-10 seconds of reference audio
- **Exceptional Quality**: Natural prosody, intonation, and voice characteristics
- **Multi-lingual**: Supports multiple languages (English tested)
- **Flexible**: Use any voice you can record or find

### Installation

F5-TTS requires separate installation:

```bash
# Option 1: Install from PyPI
pip install f5-tts

# Option 2: Install from source (latest version)
git clone https://github.com/SWivid/F5-TTS.git
cd F5-TTS
pip install -e .
```

**Note**: F5-TTS will auto-download models (~500MB) on first use.

### Usage

1. **Prepare Reference Audio**:
   - Record or obtain 5-10 seconds of clear speech
   - WAV format recommended (16kHz or higher)
   - No background noise, clear voice
   - Example: "This is a sample of my voice. I'm speaking clearly for voice cloning purposes."

2. **Configure Abogen**:
   - Select **F5-TTS** from "TTS Engine" dropdown
   - Enable **"Use GPU"** option (highly recommended)
   - Provide reference audio path in voice field

3. **Start Conversion**:
   - Process normally - F5-TTS will clone the voice from reference audio
   - First run may be slow (model download + initialization)

### Testing F5-TTS

Test your setup with the included test script:

```bash
# Test F5-TTS with reference audio
python scripts/test_f5_tts_backend.py \
  --ref-audio path/to/my_voice.wav \
  --ref-text "This is my voice sample" \
  --device cuda \
  --output out/test.wav

# Test with custom text
python scripts/test_f5_tts_backend.py \
  --ref-audio voice.wav \
  --text "The quick brown fox jumps over the lazy dog" \
  --device cuda
```

### Reference Audio Guidelines

For best results, your reference audio should:

✅ **Do**:
- Be 5-10 seconds long
- Have clear, consistent voice
- Be in the target language
- Have minimal background noise
- Represent the voice characteristics you want
- Include varied prosody (not monotone)

❌ **Don't**:
- Use audio with music or background noise
- Use phone recordings (low quality)
- Use heavily compressed audio (MP3 < 128kbps)
- Use multi-speaker audio
- Use very short samples (<3 seconds)

### Limitations

- **Speed**: Much slower than Kokoro, especially on CPU
- **GPU Requirement**: Practically requires GPU (CUDA recommended)
- **No Built-in Voices**: Must provide reference audio
- **No Voice Mixing**: Cannot blend F5-TTS voices like Kokoro
- **Memory**: Requires ~4GB VRAM for comfortable use

---

## When to Use Which Engine

### Use Kokoro-82M When:

✅ You need **fast processing** (audiobooks, batch conversions)
✅ You're happy with the **built-in voices**
✅ You want to **mix voices** for custom sounds
✅ You're on **CPU only** or low-end hardware
✅ You need **consistent voice** across multiple projects
✅ You want **simple setup** (works out of the box)

### Use F5-TTS When:

✅ You need **highest quality** synthesis
✅ You want to **clone a specific voice** (narrator, character, etc.)
✅ You have **GPU available** (CUDA recommended)
✅ You can provide **good reference audio**
✅ **Speed is not critical** (willing to wait for quality)
✅ You need a voice **not available in Kokoro**

### Hybrid Approach

You can use both engines in different scenarios:

- **Kokoro**: Quick drafts, testing, batch processing of long books
- **F5-TTS**: Final production, special character voices, narrator cloning

---

## Troubleshooting

### Kokoro Issues

**Problem**: CUDA GPU not detected
```bash
# Solution: Install correct PyTorch version
pip install torch==2.8.0+cu128 --index-url https://download.pytorch.org/whl/cu128
```

**Problem**: Voice mixing gives errors on GPU
```
Solution: Voice mixing is CPU-only in current version. It will auto-fallback to CPU.
```

### F5-TTS Issues

**Problem**: F5-TTS not available in dropdown
```bash
# Solution: Install F5-TTS
pip install f5-tts
# Restart Abogen
```

**Problem**: "Failed to load F5-TTS engine"
```bash
# Check installation
python -c "import f5_tts; print('OK')"

# Reinstall if needed
pip uninstall f5-tts
pip install f5-tts
```

**Problem**: Very slow on CPU
```
This is expected. F5-TTS requires GPU for reasonable speed.
Solutions:
1. Use CUDA: Enable "Use GPU" option
2. Use Kokoro instead for CPU-based synthesis
3. Process smaller chunks of text
```

**Problem**: "Reference audio required" error
```
F5-TTS needs a reference audio file for voice cloning.
Provide a 5-10 second WAV file of the voice you want to clone.
```

**Problem**: Poor quality output with F5-TTS
```
Check your reference audio:
- Should be 5-10 seconds
- Clear, noise-free recording
- In the same language as target text
- Not heavily compressed
```

**Problem**: Out of memory on GPU
```bash
# Reduce batch size or use smaller chunks
# Or use Kokoro instead (more memory-efficient)
```

### General Issues

**Problem**: Engine dropdown not showing
```
This means you're using an older version of Abogen.
Update to the latest version:
pip install --upgrade abogen
```

**Problem**: Config not saving engine selection
```bash
# Clear config and restart
rm ~/.config/abogen/config.json  # Linux/Mac
del %APPDATA%\abogen\config.json  # Windows
```

---

## Adding New Engines

Want to add support for another TTS engine (e.g., ElevenLabs API, OpenAI TTS, Coqui TTS)?

See the [integration plan document](tts_new_backend_plan.md) for architecture details.

Quick overview:

1. **Create backend module**: `abogen/tts_backends/your_engine_backend.py`
2. **Implement TTSBackend protocol**:
   - `__init__(lang_code, device, **kwargs)`
   - `__call__(text, voice, speed) -> Iterator[TTSResult]`
   - `supports_voice_mixing` property
   - `available_voices` property
3. **Register in factory**: Add to `ENGINE_REGISTRY` in `abogen/tts_backends/__init__.py`
4. **Add config**: Update `ENGINE_CONFIGS` in `abogen/constants.py`
5. **Test**: Create test script in `scripts/test_your_engine_backend.py`

Pull requests welcome!

---

## Performance Tips

### For Maximum Speed (Kokoro)
- Use **Kokoro-82M** with **GPU enabled**
- Disable subtitle generation if not needed
- Use simpler output formats (WAV over OPUS)
- Process multiple files via queue mode

### For Maximum Quality (F5-TTS)
- Use **F5-TTS** with **high-quality reference audio**
- Enable **GPU (CUDA)**
- Use **clear reference transcript** (improves results)
- Test reference audio first with test script
- Consider processing in smaller chunks for long texts

### For Balanced Usage
- **Kokoro** for regular conversions
- **F5-TTS** for special cases (narrator cloning, character voices)
- Switch engines per-file in queue mode

---

## FAQ

**Q: Can I use multiple engines in the same project?**
A: Yes! Use queue mode - each queued item can have different engine settings.

**Q: Can I mix Kokoro and F5-TTS voices together?**
A: No, voice mixing only works within Kokoro. F5-TTS voices cannot be blended.

**Q: Which engine is better for audiobooks?**
A: **Kokoro** for speed and consistency. **F5-TTS** if you want to clone a specific narrator's voice.

**Q: Does F5-TTS work offline?**
A: Yes, after initial model download. Set "Disable Kokoro's internet access" doesn't affect F5-TTS.

**Q: Can I use my own voice with Kokoro?**
A: No, Kokoro has fixed voices. Use F5-TTS for custom voice cloning.

**Q: How much VRAM does F5-TTS need?**
A: Minimum ~3GB, comfortable with 4GB+. Works on RTX 2060 and up.

**Q: Can I add OpenAI TTS or ElevenLabs?**
A: Not yet built-in, but the architecture supports it! See "Adding New Engines" section.

---

## Links & Resources

- **Kokoro-82M**: [HuggingFace Model](https://huggingface.co/hexgrad/Kokoro-82M)
- **F5-TTS**: [GitHub Repository](https://github.com/SWivid/F5-TTS)
- **Abogen Issues**: [Report bugs or request features](https://github.com/denizsafak/abogen/issues)

---

**Last Updated**: 2025-01-21
**Abogen Version**: 1.2.4+
