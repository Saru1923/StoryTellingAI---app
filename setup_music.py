"""
setup_music.py
Run this ONCE from the project root to copy your uploaded music files
into the correct static/music/ directory that VideoComposer reads from.

Usage:
    cd F:/multimodal_story_generator
    python setup_music.py
"""

import os
import shutil

# By default, looks for MP3s in the same folder as this script (project root).
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR   = os.path.join(SOURCE_DIR, "static", "music")

MUSIC_FILES = [
    "the_mountain-ambient-487008.mp3",
    "alexgrohl-upbeat-fun-cheerful-478798.mp3",
    "prettyjohn1-romantics-love-valentines-day_39sec-483360.mp3",
    "Happiness In Music - Comedy.mp3",
    "Universfield - Dark 80s Sci-Fi Atmosphere.mp3",
    "paulyudin-piano-music-piano-485929.mp3",
]

os.makedirs(DEST_DIR, exist_ok=True)
print("Destination: " + DEST_DIR)
print("")

copied  = 0
missing = 0

for fname in MUSIC_FILES:
    src = os.path.join(SOURCE_DIR, fname)
    dst = os.path.join(DEST_DIR,   fname)

    if os.path.exists(dst):
        print("  Already present: " + fname)
        copied += 1
        continue

    if os.path.exists(src):
        shutil.copy2(src, dst)
        print("  Copied: " + fname)
        copied += 1
    else:
        print("  NOT FOUND - place this file in: " + SOURCE_DIR)
        print("  Missing: " + fname)
        missing += 1

print("")
print("=" * 50)
print("Done: " + str(copied) + " copied/present, " + str(missing) + " missing.")

if missing == 0:
    print("All music files ready! Run: streamlit run app/main.py")
else:
    print("Copy the missing MP3 files to the project root first, then re-run.")