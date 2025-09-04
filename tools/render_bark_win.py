#!/usr/bin/env python3
# Windows-friendly Bark renderer for My_Audiobook_Project
# - Reads voices/<Speaker>/*.txt
# - Uses voices_map.json to map Speaker -> Bark voice preset
# - Chunks long text for Bark stability, concatenates to a single WAV
# - Saves to audio_raw/<chapter>_<speaker>.wav
# - Resumes by default (skip existing) unless --overwrite

import argparse
import json
import re
from pathlib import Path
from typing import List

import numpy as np
import soundfile as sf

# Bark
from bark import generate_audio, preload_models

# ---------- Config defaults ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOICES_DIR   = PROJECT_ROOT / "voices"
AUDIO_RAW    = PROJECT_ROOT / "audio_raw"
VOICE_MAP    = PROJECT_ROOT / "voices_map.json"

SAMPLE_RATE  = 24000          # Bark output SR
MAX_CHARS    = 550            # conservative per-chunk size (Bark is happier under ~700)
SENTENCE_END = re.compile(r'([.!?…]+["\')\]]?\s+)', flags=re.MULTILINE)

# ------------------------------------

def load_voice_map() -> dict:
    if not VOICE_MAP.exists():
        raise FileNotFoundError(f"voices_map.json not found at: {VOICE_MAP}")
    return json.loads(VOICE_MAP.read_text(encoding="utf-8"))

def sentence_chunk(text: str, max_chars: int) -> List[str]:
    """
    Split text into sentence-like chunks under max_chars.
    We first split by sentence punctuation, then glue back respecting max_chars.
    """
    text = re.sub(r'\s+', ' ', text.strip())
    if not text:
        return []

    parts = []
    start = 0
    for m in SENTENCE_END.finditer(text + " "):  # extra space to catch last segment
        end = m.end()
        parts.append(text[start:end])
        start = end
    if start < len(text):
        parts.append(text[start:])

    # Re-glue under max_chars
    chunks = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) <= max_chars:
            cur += p
        else:
            if cur.strip():
                chunks.append(cur.strip())
            cur = p
    if cur.strip():
        chunks.append(cur.strip())
    return chunks

def render_text_to_audio(text: str, history_prompt: str) -> np.ndarray:
    """
    Generate a single audio array with Bark, catching occasional hiccups.
    """
    audio = generate_audio(text, history_prompt=history_prompt)
    # Ensure float32 for saving
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    return audio

def render_file(txt_path: Path, speaker_display: str, voice_id: str, out_path: Path,
                overwrite: bool, max_chars: int) -> None:
    if out_path.exists() and not overwrite:
        print(f"[skip] {out_path.name} (exists)")
        return

    raw = txt_path.read_text(encoding="utf-8").strip()
    if not raw:
        print(f"[warn] Empty text: {txt_path}")
        return

    chunks = sentence_chunk(raw, max_chars=max_chars)
    if not chunks:
        print(f"[warn] No chunks after split: {txt_path}")
        return

    print(f"[render] {out_path.name} — speaker={speaker_display} voice={voice_id} chunks={len(chunks)}")

    # Generate and concatenate with a small silence pad between chunks
    silence = np.zeros(int(0.20 * SAMPLE_RATE), dtype=np.float32)  # 200ms pad
    rendered = []
    for i, ck in enumerate(chunks, 1):
        try:
            audio = render_text_to_audio(ck, history_prompt=voice_id)
        except Exception as e:
            print(f"[error] chunk {i}/{len(chunks)} failed: {e}")
            continue
        rendered.append(audio)
        if i < len(chunks):
            rendered.append(silence)

    if not rendered:
        print(f"[error] Nothing rendered for {txt_path}")
        return

    full = np.concatenate(rendered)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, full, SAMPLE_RATE)
    print(f"[done]  {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Render Bark TTS for My_Audiobook_Project")
    parser.add_argument("--speaker", nargs="*", default=None,
                        help="Restrict to one or more speakers (folder names, e.g., Narrator Sunny_(Sunless))")
    parser.add_argument("--chapter", nargs="*", default=None,
                        help="Restrict to one or more chapter stems (e.g., 01_chapter1 05_chapter5)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing WAV files")
    parser.add_argument("--max-chars", type=int, default=MAX_CHARS, help="Max characters per chunk")
    args = parser.parse_args()

    if not VOICES_DIR.exists():
        raise FileNotFoundError(f"voices directory not found: {VOICES_DIR}")
    AUDIO_RAW.mkdir(exist_ok=True)

    # Preload Bark once (faster subsequent renders)
    print("[init] Preloading Bark models…")
    preload_models()

    voice_map = load_voice_map()

    # Normalize filters
    speakers_filter = set(args.speaker) if args.speaker else None
    chapters_filter = set(args.chapter) if args.chapter else None

    total = 0
    for speaker_dir in sorted([p for p in VOICES_DIR.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        if speakers_filter and speaker_dir.name not in speakers_filter:
            continue

        # Bark voice ID from map; default to en_speaker_0 if missing
        speaker_display = speaker_dir.name.replace("_", " ")
        voice_id = voice_map.get(speaker_display, "v2/en_speaker_0")

        for txt_file in sorted(speaker_dir.glob("*.txt"), key=lambda p: p.name.lower()):
            chapter_stem = txt_file.stem          # e.g., 05_chapter5
            if chapters_filter and chapter_stem not in chapters_filter:
                continue

            out_file = AUDIO_RAW / f"{chapter_stem}_{speaker_dir.name}.wav"
            render_file(txt_file, speaker_display, voice_id, out_file, args.overwrite, args.max_chars)
            total += 1

    print(f"[summary] processed files: {total}")

if __name__ == "__main__":
    main()
