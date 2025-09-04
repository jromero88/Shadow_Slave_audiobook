import os, json
from pathlib import Path
import numpy as np
import soundfile as sf
from bark import generate_audio, preload_models

# Preload models once (saves time)
preload_models()

# Load mapping
voice_map = json.load(open("voices_map.json"))

VOICES_DIR = Path("voices")
AUDIO_RAW = Path("audio_raw")
AUDIO_RAW.mkdir(exist_ok=True)

# Iterate speakers
for speaker_dir in VOICES_DIR.iterdir():
    if not speaker_dir.is_dir():
        continue
    speaker_name = speaker_dir.name.replace("_", " ")
    voice_id = voice_map.get(speaker_name, "v2/en_speaker_0")

    for txt_file in speaker_dir.glob("*.txt"):
        chapter = txt_file.stem  # e.g., 01_chapter1
        out_file = AUDIO_RAW / f"{chapter}_{speaker_dir.name}.wav"

        text = txt_file.read_text(encoding="utf-8").strip()
        if not text:
            continue

        print(f"Rendering {out_file} with voice {voice_id}…")

        # Generate audio with Bark
        audio_array = generate_audio(text, history_prompt=voice_id)

        # Save to WAV
        sf.write(out_file, audio_array, 24000)  # Bark outputs 24kHz
