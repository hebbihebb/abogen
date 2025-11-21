#!/usr/bin/env python3
"""Generate a reference audio file with Kokoro for F5-TTS cloning."""
from pathlib import Path
import numpy as np
import soundfile as sf
from abogen.tts_backends import create_tts_engine

# Reference text - good phonetic variety
ref_text = (
    "The quick brown fox jumps over the lazy dog, "
    "demonstrating clear pronunciation and natural vocal characteristics for voice cloning."
)

# Choose your voice here
voice_name = "af_bella"  # Change to: af_nicole, af_sarah, am_adam, am_michael, etc.

print(f"Generating reference audio with voice: {voice_name}")
print(f"Text: {ref_text}\n")

# Create Kokoro engine
engine = create_tts_engine("kokoro", lang_code="en-us", device="cpu")

# Generate audio
audio_chunks = []
sample_rate = None

for result in engine(ref_text, voice=voice_name):
    audio_chunks.append(result.audio)
    sample_rate = result.sample_rate

# Save
audio = np.concatenate(audio_chunks)
output_file = f"out/reference_{voice_name}.wav"
Path("out").mkdir(exist_ok=True)
sf.write(output_file, audio, sample_rate)

duration = len(audio) / sample_rate
print(f"[OK] Reference created: {output_file}")
print(f"    Duration: {duration:.2f}s")
print(f"    Sample rate: {sample_rate}Hz")
print(f"\nYou can now use this file with F5-TTS!")
