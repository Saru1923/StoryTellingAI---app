import sys
sys.path.append(".")

from utils.tts_engine import TTSEngine
import os

tts = TTSEngine()
audio_path = tts.synthesize(
    "This is a test of the adventure voice style.",
    voice_style="energetic",
    output_dir="F:\\multimodal_story_generator\\output"
)

print(f"Audio saved to: {audio_path}")

if os.path.exists(audio_path):
    size = os.path.getsize(audio_path)
    print(f"✓ File exists: {audio_path}")
    print(f"✓ File size: {size} bytes")
    if size > 1000:
        print("✓ Audio is valid (has content)")
    else:
        print("✗ File too small — might be silent/empty")
else:
    print("✗ File not found!")

os.startfile(audio_path)