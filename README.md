# Shadow Slave – Production Notes

## 📖 Project Overview
This repository contains the dramatized audiobook adaptation of *Shadow Slave* (Volume 1).  
Scripts, voices, raw audio, mixes, SFX, and exports are organized for clarity and long-term production.

## 📂 Directory Structure
- **script/**
  - `01_chapter1_master.json` → Final supervised script (Chapter 1)
  - `02_chapter2_master.json` → Final supervised script (Chapter 2)
  - `cast_master.json` → Cumulative cast sheet (all chapters)
  - `sfx_cues.txt` → Sound effect log across all chapters
- **voices/** → Subfolders for each character’s raw recordings
- **audio_raw/** → Chapter-by-chapter raw WAV files
- **audio_final/** → Chapter final mixes (WAV/MP3)
- **music_sfx/** → Ambient/music/SFX assets
- **export/** → Full audiobook exports (MP3/M4B)
- **README_production_notes.md** → This file

## 🎙️ Supervising Editor Rules (Global)
1. **Consistency**: Character names & voice notes unified across chapters.
2. **Pacing**: Pauses only at beat shifts or heavy punctuation.
3. **SFX Hygiene**: Max 0–2 cues per scene; never clutter narration.
4. **Intelligibility**: Narrator lines always clear above SFX/music.
5. **Dialogue Flow**: Trim filler unless faithful to source text.
6. **QC Warnings**: Any invented or out-of-scope additions flagged.

## 📋 Current Assets
- Chapters scripted: **01, 02**
- Cast locked: Narrator, Sunny (Sunless), Tired Officer, Gray-Haired Policeman, PA/Officers, Nightmare Spell System, Broad-Shouldered Slave, Shifty Slave, Gentle Slave, Young Soldier, Older Soldier
- SFX cues logged: Chapters 1–2

## 🛠️ Workflow Notes
- Each new chapter adds a `NN_chapter_master.json` script.
- `cast_master.json` grows cumulatively (no duplicates).
- `sfx_cues.txt` is a full log across all chapters (append-only).
- Optional `scene_index.txt` may be added for one-line beat summaries.
- Audio workflow: voices → audio_raw → audio_final → export.

## ✅ QC Log
- [Ch3] Added Head Soldier; renamed Gentle Slave → Gentle Slave (Scholar). Inner lore intact, pacing trimmed.
- [Ch4] Added Mountain King’s Larva (creature voice). Preserved tyrant hierarchy lore. Pacing tightened for combat.
- [Ch5] Preserved Young Soldier intervention and key scene. Inner sarcasm (“poser”) retained. Bonfire logic faithful.

- [Ch1] Removed redundant SFX (multiple gulps, extra ambient layers).
- [Ch1] Unified Sunny/Sunless as same character.
- [Ch2] Flagged sarcastic “male lead” remark as inner thought (not fact).
- [Ch2] No fabricated lore added.

---
*Maintained automatically by supervising editor guidelines.*

## 📊 Chapter Progress Tracker
| Chapter | Script | Audio Raw | Audio Final | Status Notes |
|---------|--------|-----------|-------------|--------------|
| Ch1: S1 Park – outside police station | ✅ Scripted | ⏳ Pending | ❌ Not Mixed | 6 scene(s) scripted |
| Ch2: S1 Dream mountain vision | ✅ Scripted | ⏳ Pending | ❌ Not Mixed | 3 scene(s) scripted |
| Ch3: S1 Caravan march | ✅ Scripted | ⏳ Pending | ❌ Not Mixed | 4 scene(s) scripted |
| Ch4: S1 Avalanche attack | ✅ Scripted | ⏳ Pending | ❌ Not Mixed | 7 scene(s) scripted |
| Ch5: S1 Aftermath | ✅ Scripted | ⏳ Pending | ❌ Not Mixed | 6 scene(s) scripted |
