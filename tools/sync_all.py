#!/usr/bin/env python3
"""
tools/sync_all.py

Rebuilds:
  - script/cast_master.json   (cumulative cast, preserves existing voice notes)
  - script/sfx_cues.txt       (SFX cues across all chapters)
  - scene_index.txt           (one-line scene beat summaries)

Exports per-speaker lines:
  - voices/<Speaker>/<NN_chapterX>.txt
  - voices/<Speaker>/<NN_chapterX>.ssml
  - voices/<Speaker>/_ALL.txt
  - voices/<Speaker>/_ALL.ssml

Also updates README:
  - Adds/updates a '📊 Chapter Progress Tracker' table with one row per chapter.

Run from project root:
  python3 tools/sync_all.py
"""
from pathlib import Path
import json, re, sys, html

# --- Paths (project-root aware) ---
ROOT        = Path(__file__).resolve().parents[1]
SCRIPT_DIR  = ROOT / "script"
CAST_PATH   = SCRIPT_DIR / "cast_master.json"
SFX_PATH    = SCRIPT_DIR / "sfx_cues.txt"
SCENE_IDX   = ROOT / "scene_index.txt"
VOICES_DIR  = ROOT / "voices"
README_PATH = ROOT / "README_production_notes.md"

CHAP_RE     = re.compile(r"^(?P<prefix>\d{2})_chapter(?P<num>\d+)_master\.json$", re.IGNORECASE)
REQUIRED    = {"index","scene","speaker","line","emotion","sfx","timing","notes"}

def safe_speaker_name(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in (" ","-","_")).strip()
    return safe.replace(" ", "_") or "Unknown"

def load_chapters():
    if not SCRIPT_DIR.exists():
        print(f"ERROR: script directory not found: {SCRIPT_DIR}", file=sys.stderr)
        sys.exit(1)
    chapters = []
    for p in SCRIPT_DIR.iterdir():
        if p.is_file():
            m = CHAP_RE.match(p.name)
            if m:
                chapters.append((p, m.group("prefix"), m.group("num")))
    chapters.sort(key=lambda t: t[1])  # by leading NN prefix
    return chapters

def ensure_rows(rows, src_name):
    for row in rows:
        missing = REQUIRED - set(row.keys())
        if missing:
            raise ValueError(f"{src_name}: Missing keys in row {row.get('index')}: {missing}")

def rebuild_cast(chapters):
    speakers = set()
    for path, _prefix, _num in chapters:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path.name}: expected top-level JSON array")
        ensure_rows(data, path.name)
        for r in data:
            sp = (r.get("speaker") or "").strip()
            if sp:
                speakers.add(sp)

    old = []
    if CAST_PATH.exists():
        try: old = json.loads(CAST_PATH.read_text(encoding="utf-8"))
        except Exception: old = []
    voice_map = {c.get("name"): c.get("voice_note") for c in old if isinstance(c, dict)}

    merged = [{"name": name, "voice_note": voice_map.get(name, "")}
              for name in sorted(speakers, key=lambda s: s.lower())]
    CAST_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(merged)

def rebuild_sfx(chapters):
    lines = []
    for path, _prefix, _num in chapters:
        data = json.loads(path.read_text(encoding="utf-8"))
        ensure_rows(data, path.name)
        bucket = [f"{r['index']}. {r['scene']} — {r['sfx'].strip()}"
                  for r in data if (r.get("sfx") or "").strip()]
        if bucket:
            lines.append(f"=== {path.stem.replace('_master','')} ===")
            lines.extend(bucket)
            lines.append("")
    SFX_PATH.write_text("\n".join(lines).rstrip() + ("\n" if lines else ""), encoding="utf-8")
    return sum(1 for _ in lines if _ and not _.startswith("==="))

def rebuild_scene_index(chapters):
    out = []
    for path, prefix, _num in chapters:
        data = json.loads(path.read_text(encoding="utf-8"))
        ensure_rows(data, path.name)

        seen = set()
        beats = []
        for r in data:
            sc = r["scene"]
            if sc not in seen:
                seen.add(sc)
                narr = next((x for x in data if x["scene"] == sc and (x["speaker"] or "").lower() == "narrator"), None)
                beat = narr["line"] if narr else r["line"]
                if len(beat) > 140:
                    beat = beat[:137].rstrip() + "…"
                beats.append((sc, beat))

        if beats:
            out.append(f"=== {path.stem.replace('_master','')} ===")
            for sc, beat in beats:
                out.append(f"{sc} — {beat}")
            out.append("")
    SCENE_IDX.write_text("\n".join(out).rstrip() + ("\n" if out else ""), encoding="utf-8")
    return len(out)

def export_per_speaker(chapters):
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    agg = {}  # safe_speaker -> {"display": original, "items": [(prefix, chapter_stem, index, line, timing)]}

    for path, prefix, _num in chapters:
        chapter_stem = path.stem.replace("_master", "")  # e.g., 01_chapter1
        data = json.loads(path.read_text(encoding="utf-8"))
        ensure_rows(data, path.name)

        by_speaker = {}
        for r in data:
            by_speaker.setdefault(r["speaker"], []).append(r)

        for speaker, rows in by_speaker.items():
            safe = safe_speaker_name(speaker)
            speaker_dir = VOICES_DIR / safe
            speaker_dir.mkdir(parents=True, exist_ok=True)

            txt_path  = speaker_dir / f"{chapter_stem}.txt"
            ssml_path = speaker_dir / f"{chapter_stem}.ssml"

            with txt_path.open("w", encoding="utf-8") as f:
                for r in sorted(rows, key=lambda x: int(x["index"])):
                    f.write(f"{r['line']}\n")

            with ssml_path.open("w", encoding="utf-8") as f:
                f.write("<speak>\n")
                f.write(f'  <voice name="{html.escape(speaker)}">\n')
                for r in sorted(rows, key=lambda x: int(x["index"])):
                    line = html.escape(str(r["line"]))
                    f.write(f'    <prosody rate="medium">{line}</prosody>\n')
                    timing = r.get("timing")
                    if timing:
                        f.write(f'    <break time="{html.escape(str(timing))}"/>\n')
                f.write("  </voice>\n</speak>\n")

            bucket = agg.setdefault(safe, {"display": speaker, "items": []})
            for r in rows:
                bucket["items"].append((prefix, chapter_stem, int(r["index"]), str(r["line"]), str(r.get("timing") or "")))

    for safe, payload in agg.items():
        speaker_display = payload["display"]
        items = sorted(payload["items"], key=lambda t: (t[0], t[2]))
        speaker_dir = VOICES_DIR / safe
        all_txt  = speaker_dir / "_ALL.txt"
        all_ssml = speaker_dir / "_ALL.ssml"

        with all_txt.open("w", encoding="utf-8") as f:
            last_prefix = None
            for prefix, chapter_stem, idx, line, timing in items:
                if prefix != last_prefix:
                    f.write(f"\n=== {chapter_stem} ===\n")
                    last_prefix = prefix
                f.write(f"{line}\n")

        with all_ssml.open("w", encoding="utf-8") as f:
            f.write("<speak>\n")
            f.write(f'  <voice name="{html.escape(speaker_display)}">\n')
            last_prefix = None
            for prefix, chapter_stem, idx, line, timing in items:
                if prefix != last_prefix:
                    if last_prefix is not None:
                        f.write('    <break time="300ms"/>\n')
                    last_prefix = prefix
                f.write(f'    <prosody rate="medium">{html.escape(line)}</prosody>\n')
                if timing:
                    f.write(f'    <break time="{html.escape(str(timing))}"/>\n')
            f.write("  </voice>\n</speak>\n")

def _readme_insert_or_replace_block(text: str, header: str, block: str) -> str:
    """Insert or replace a markdown section starting with a specific header line."""
    if header in text:
        # replace section: header until next "## " or end
        start = text.index(header)
        tail = text[start+len(header):]
        next_idx = tail.find("\n## ")
        if next_idx != -1:
            return text[:start] + header + block + tail[next_idx+1:]
        else:
            return text[:start] + header + block
    else:
        # append at end with spacing
        return (text.rstrip() + "\n\n" + header + block + "\n")

def update_readme_progress(chapters):
    # Build rows based on chapter files: derive human title from filename part after 'chapter'
    rows = []
    for path, prefix, num in chapters:
        # filename example: 05_chapter5_master.json  -> title "Chapter 5"
        # You may choose to store richer titles in the JSON; for now, use a simple heuristic.
        title = f"Ch{int(num)}: "  # we’ll try to read first scene to seed a short label
        data = json.loads(path.read_text(encoding="utf-8"))
        ensure_rows(data, path.name)
        # Try to derive a short label from first Narrator line or first line
        first_scene = data[0].get("scene", "")
        # Friendly label from scene; fallback to 'Chapter <num>'
        label_map = {
            # You can keep extending this mapping if you want explicit names
        }
        label = label_map.get(prefix, first_scene) or f"Chapter {int(num)}"
        # Trim long labels
        if len(label) > 40:
            label = label[:37].rstrip() + "…"
        title += label

        scene_count = len({r["scene"] for r in data})
        status_notes = f"{scene_count} scene(s) scripted"

        rows.append((int(num), title, "✅ Scripted", "⏳ Pending", "❌ Not Mixed", status_notes))

    rows.sort(key=lambda x: x[0])

    # Build markdown table
    table_lines = [
        "## 📊 Chapter Progress Tracker",
        "| Chapter | Script | Audio Raw | Audio Final | Status Notes |",
        "|---------|--------|-----------|-------------|--------------|",
    ]
    for _n, title, script_s, raw_s, final_s, notes in rows:
        table_lines.append(f"| {title} | {script_s} | {raw_s} | {final_s} | {notes} |")
    table = "\n".join(table_lines) + "\n"

    # Read existing README (create if missing)
    text = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else "# My_Audiobook_Project – Production Notes\n"
    updated = _readme_insert_or_replace_block(text, "## 📊 Chapter Progress Tracker", "\n" + "\n".join(table_lines[1:]) + "\n")
    README_PATH.write_text(updated, encoding="utf-8")

def main():
    chapters = load_chapters()
    if not chapters:
        print(f"No chapter master files found in {SCRIPT_DIR}")
        return

    cast_count = rebuild_cast(chapters)
    sfx_count  = rebuild_sfx(chapters)
    scene_lines = rebuild_scene_index(chapters)
    export_per_speaker(chapters)
    update_readme_progress(chapters)

    print(f"Rebuilt cast_master.json — {cast_count} speakers")
    print(f"Rebuilt sfx_cues.txt     — {sfx_count} cue lines")
    print(f"Rebuilt scene_index.txt  — {scene_lines} lines (incl. headers)")
    print(f"Exported per-speaker files in {VOICES_DIR} (per-chapter + aggregates)")
    print(f"Updated README progress tracker with {len(chapters)} chapter(s)")

if __name__ == "__main__":
    main()
