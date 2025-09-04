import os, json
from pathlib import Path
import soundfile as sf
from openai import OpenAI

client = OpenAI()

# Load voice map
voice_map = json.load(open("voices_map.json"))

VOICES_DIR = Path("voices")
AUDIO_RAW = Path("audio_raw")
AUDIO_RAW.mkdir(exist_ok=True)

# Iterate speakers
for speaker_dir in VOICES_DIR.iterdir():
    if not speaker_dir.is_dir():
        continue
    speaker_name = speaker_dir.name.replace("_", " ")
    voice_id = voice_map.get(speaker_name, "alloy")

    for txt_file in speaker_dir.glob("*.txt"):
        chapter = txt_file.stem  # e.g., 01_chapter1
        out_file = AUDIO_RAW / f"{chapter}_{speaker_dir.name}.wav"

        # Read lines
        lines = txt_file.read_text(encoding="utf-8").splitlines()
        text = " ".join(lines).strip()
        if not text:
            continue

        print(f"Rendering {out_file} with voice {voice_id}…")

        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice_id,
            input=text,
            format="wav"
        )

        # Save
        with open(out_file, "wb") as f:
            f.write(response.read())
