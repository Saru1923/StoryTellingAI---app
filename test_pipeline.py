# test_pipeline.py
import sys
sys.path.append(".")

from utils.input_analyzer import InputAnalyzer
from utils.feature_extractor import FeatureExtractor
from utils.story_generator import StoryGenerator
from utils.emotion_analyzer import EmotionAnalyzer

# Test with text only
inputs = {
    "text": "A brave knight discovers a dragon who only wants to paint sunsets.",
    "images": [],
    "videos": [],
    "mode": "text"
}

print("Testing Input Analyzer...")
analyzer = InputAnalyzer()
result = analyzer.analyze(inputs)
print(f"✓ Input type: {result['input_type']}")

print("Testing Feature Extractor...")
extractor = FeatureExtractor()
embeddings = extractor.extract(result)
print(f"✓ Scene count: {embeddings['scene_count']}")

print("Testing Story Generator (Adventure theme)...")
gen = StoryGenerator()
story = gen.generate(embeddings, theme="adventure")
print(f"✓ Story generated: {len(story['script'])} chars")
print(f"  Preview: {story['script'][:100]}...")

print("Testing Emotion Analyzer...")
emotion = EmotionAnalyzer()
emotions = emotion.analyze(story["script"])
print(f"✓ Dominant emotion: {emotions['dominant_emotion']}")

print("\n🎉 All modules working correctly!")