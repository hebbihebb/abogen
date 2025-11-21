#!/usr/bin/env python3
"""Quick script to list available Kokoro voices."""
from kokoro import KPipeline

kp = KPipeline(lang_code='a')
print('Available Kokoro voices (58 total):')
print()
for voice in sorted(kp.available_voices):
    print(f'  {voice}')
