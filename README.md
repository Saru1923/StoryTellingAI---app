# 🎬 Multimodal Story Generator with Theme-Controlled Narrative & Voice Modulation

## Complete Step-by-Step Documentation  
### From Installation to Full Development

---

## 📑 Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Installation Guide](#4-installation-guide)
5. [Project Structure](#5-project-structure)
6. [Module-by-Module Explanation](#6-module-by-module-explanation)
7. [Theme System Deep Dive](#7-theme-system-deep-dive)
8. [Running the Application](#8-running-the-application)
9. [API Keys & Configuration](#9-api-keys--configuration)
10. [Testing the Pipeline](#10-testing-the-pipeline)
11. [Common Errors & Fixes](#11-common-errors--fixes)
12. [Viva Preparation](#12-viva-preparation)

---

## 1. Project Overview

This system converts multimodal inputs (text, images, videos, or any combination) into a fully narrated, themed story video. The key innovation is the **Theme Switching System** which influences every stage of the pipeline:

| Input | Processing | Output |
|-------|-----------|--------|
| Text prompts | Feature extraction | MP4 video |
| Images | GMM clustering | Voice narration |
| Videos | LLM story generation | Themed captions |
| Mixed | Emotion analysis | Background music |

### 🎭 Supported Themes

| Theme | Voice Style | Music | Use Case |
|-------|------------|-------|----------|
| Default | Standard neutral | Ambient | General purpose |
| ⚔️ Adventure | Energetic, dynamic | Epic orchestral | Action/journey content |
| 💕 Romance | Soft, warm | Soft piano | Emotional/love stories |
| 😂 Comedy | Expressive, lively | Upbeat quirky | Funny content |
| 🔍 Mystery | Calm, suspenseful | Dark ambient | Thriller/detective |
| 🎙️ Documentary | Professional neutral | Minimal cinematic | Educational content |

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────┐
│                    USER LAYER                          │
│    Text / Images / Videos Upload + Theme Selection     │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│              FRONTEND LAYER (Streamlit)                │
│  • File Upload Widget                                  │
│  • Theme Dropdown (Adventure/Romance/Comedy/etc.)      │
│  • Progress Display                                    │
│  • Video Preview + Download                            │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│              AI PROCESSING LAYER                       │
│                                                        │
│  ① Input Analyzer  →  Detect type (text/image/video)  │
│                    ↓                                   │
│  ② Feature Extractor → CLIP + Sentence-Transformers   │
│                    ↓                                   │
│  ③ GMM Clustering  →  Group related scenes            │
│                    ↓                                   │
│  ④ Theme-Aware LLM  →  LangChain + themed prompts     │
│                    ↓                                   │
│  ⑤ Emotion Analyzer → Detect story mood               │
│                    ↓                                   │
│  ⑥ TTS Engine     →  Neural voice with style          │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│           VIDEO COMPOSITION LAYER (MoviePy)            │
│  • Scene ordering by cluster                           │
│  • Theme-specific transitions (fade/wipe/dissolve)     │
│  • Themed caption overlay                              │
│  • Narration audio synchronization                     │
│  • Background music at 15% volume                      │
│  • Final MP4 export                                    │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────┐
│               OUTPUT: Narrated Themed Story Video      │
│               (720p MP4 with captions + music)         │
└────────────────────────────────────────────────────────┘
```

---

## 3. Prerequisites

### Required Software
- **Python**: 3.9 or 3.10 (recommended)  
- **pip**: Package manager (comes with Python)  
- **FFmpeg**: Required for video rendering

### Install FFmpeg

**Windows:**
```bash
# Using winget (Windows 10/11)
winget install ffmpeg

# Or download from https://ffmpeg.org/download.html
# Add to PATH after extracting
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian Linux:**
```bash
sudo apt update
sudo apt install ffmpeg -y
```

**Verify FFmpeg installation:**
```bash
ffmpeg -version
```

---

## 4. Installation Guide

### Step 1: Clone or Download the Project

```bash
# If using git:
git clone https://github.com/your-username/multimodal-story-generator.git
cd multimodal-story-generator

# Or just extract the zip folder and cd into it
cd multimodal_story_generator
```

### Step 2: Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

### Step 3: Install Core Dependencies

```bash
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

> ⚠️ **Note**: `torch` installation can be slow (1-2GB download). Be patient.

### Step 4: Install TTS Engine (Choose One)

**Option A: gTTS (Google TTS) — Easiest, requires internet**
```bash
pip install gTTS
```

**Option B: edge-tts (Microsoft Neural — Best Quality)**
```bash
pip install edge-tts
```

**Option C: pyttsx3 (Offline, no internet needed)**
```bash
pip install pyttsx3
```

### Step 5: Configure Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings (optional - defaults work fine)
# Only needed if using OpenAI API
```

### Step 6: Create Required Directories

```bash
mkdir -p output static/music temp
```

### Step 7: (Optional) Add Background Music

Place royalty-free MP3 files in `static/music/`:
- `ambient.mp3`
- `epic_orchestral.mp3`
- `soft_piano.mp3`
- `upbeat_quirky.mp3`
- `dark_ambient.mp3`
- `minimal_cinematic.mp3`

> Free music sources: [Pixabay](https://pixabay.com/music/), [Free Music Archive](https://freemusicarchive.org/)

---

## 5. Project Structure

```
multimodal_story_generator/
│
├── app/
│   └── main.py                  ← Streamlit UI (entry point)
│
├── utils/
│   ├── __init__.py
│   ├── input_analyzer.py        ← Detect & preprocess input types
│   ├── feature_extractor.py     ← CLIP + Sentence-Transformer embeddings
│   ├── story_generator.py       ← Theme-aware LLM story generation
│   ├── emotion_analyzer.py      ← Emotion detection for voice modulation
│   ├── tts_engine.py            ← Multi-backend TTS with voice styles
│   └── video_composer.py        ← MoviePy video composition
│
├── static/
│   └── music/                   ← Background music files (MP3)
│
├── output/                      ← Generated videos saved here
├── temp/                        ← Temporary processing files
├── requirements.txt
├── .env.example
└── README.md                    ← This file
```

---

## 6. Module-by-Module Explanation

### Module 1: Input Analyzer (`input_analyzer.py`)

**Purpose**: Identifies what type of input the user provided and preprocesses it.

**How it works:**
1. Checks if text, images, and/or videos are provided
2. Classifies as: `text`, `images`, `videos`, or `mixed`
3. Saves uploaded files to temporary paths for processing
4. Returns structured metadata dictionary

**Key method:**
```python
result = analyzer.analyze(inputs)
# Returns: {input_type, text, image_paths, video_paths, metadata}
```

---

### Module 2: Feature Extractor (`feature_extractor.py`)

**Purpose**: Converts raw inputs into numerical semantic embeddings for AI processing.

**Models Used:**
| Input Type | Model | Output |
|-----------|-------|--------|
| Images | `openai/clip-vit-base-patch32` | 512-dim vector |
| Videos | CLIP on sampled frames (8 frames) | 512-dim vector |
| Text | `all-MiniLM-L6-v2` | 384-dim vector |

**Clustering Algorithm: Gaussian Mixture Model (GMM)**
- Groups similar scenes together
- Improves narrative coherence
- Better than K-Means because it handles overlapping clusters

```python
embeddings_result = extractor.extract(analysis_result)
# Returns: {embeddings, descriptions, cluster_labels, scene_count}
```

---

### Module 3: Story Generator (`story_generator.py`)

**Purpose**: Core innovation — generates a themed narrative using LangChain + LLM.

**Theme Prompt Engineering:**

Each theme has 4 components:
1. **System prompt**: Sets the AI's persona
2. **Instruction**: What to generate
3. **Style guide**: How to write it
4. **Scene connector**: Transition phrase between scenes

**Example for Mystery theme:**
```python
system = "You are a suspenseful mystery writer who builds tension through careful revelation."
instruction = "Generate a suspenseful mystery story with hidden clues and rising tension..."
style_guide = "Use atmospheric language, hint at hidden truths, build tension gradually..."
```

**LLM Provider Priority:**
1. HuggingFace local model (GPT-2) — free, offline
2. OpenAI GPT-3.5 — if API key provided
3. Ollama local LLMs — if installed
4. Template fallback — always works

---

### Module 4: Emotion Analyzer (`emotion_analyzer.py`)

**Purpose**: Detects emotional tone of the generated story to guide voice modulation.

**Method**: Keyword frequency scoring across 8 emotion categories:
- Happy, Sad, Dramatic, Exciting, Mysterious, Romantic, Calm, Neutral

**Output feeds into TTS parameters:**
| Emotion | Speaking Rate | Pitch | Volume |
|---------|--------------|-------|--------|
| Exciting | +20% | +8Hz | +10% |
| Mysterious | -15% | -5Hz | -8% |
| Romantic | -10% | +3Hz | -3% |
| Neutral | 0% | 0Hz | 0% |

---

### Module 5: TTS Engine (`tts_engine.py`)

**Purpose**: Converts the generated script to speech with theme-appropriate voice style.

**Backend Priority:**
1. `edge-tts` (Microsoft Neural — best quality)
2. `gTTS` (Google — good, needs internet)
3. `pyttsx3` (offline fallback)
4. Silent audio (last resort)

**Voice Style Mapping:**
| Theme Voice Style | edge-tts Voice | gTTS Accent |
|-----------------|----------------|-------------|
| energetic | en-US-DavisNeural | Australian |
| soft_warm | en-GB-SoniaNeural | British (slow) |
| expressive_lively | en-US-AriaNeural | Indian English |
| calm_suspenseful | en-US-GuyNeural | British (slow) |
| professional_neutral | en-US-ChristopherNeural | US English |

---

### Module 6: Video Composer (`video_composer.py`)

**Purpose**: Assembles all components into the final themed MP4 video.

**Pipeline:**
1. Load images/videos as MoviePy clips
2. Resize all clips to target resolution (720p/1080p)
3. Apply theme-specific transitions
4. Overlay caption text with themed fonts/colors
5. Add narration audio (synchronized)
6. Mix in background music at 15% volume
7. Export as MP4 with H.264 + AAC

**Fallback**: If no visual media is provided (text-only input), it creates animated text slides from the story script.

---

## 7. Theme System Deep Dive

### Data Flow with Theme

```
User selects "Mystery" theme
        ↓
theme_key = "mystery"
theme_config = {
    voice_style: "calm_suspenseful",
    music: "dark_ambient",
    transition: "fade",
    font: "Courier New",
    color: "#9B59B6"
}
        ↓
StoryGenerator receives theme_config
  → Builds mystery-specific prompt
  → LLM generates suspenseful narrative
        ↓
TTSEngine receives voice_style="calm_suspenseful"
  → Uses en-US-GuyNeural (or British slow gTTS)
        ↓
VideoComposer receives theme_config
  → Adds dark purple captions
  → Uses fade transitions
  → Mixes dark ambient music
        ↓
Output: Suspenseful mystery video with moody narration
```

### Adding a Custom Theme

To add a new theme (e.g., "Horror"):

**1. In `main.py`**, add to THEMES dict:
```python
"👻 Horror": {
    "key": "horror",
    "description": "Dark, terrifying storytelling",
    "voice_style": "calm_suspenseful",
    "music": "dark_ambient",
    "color": "#8B0000",
    "transition": "fade",
    "font": "Courier New",
    "prompt_prefix": "Generate a terrifying horror story..."
}
```

**2. In `story_generator.py`**, add to THEME_PROMPTS:
```python
"horror": {
    "system": "You are a master horror author...",
    "instruction": "Generate a chilling horror story...",
    "style_guide": "Use dread, suspense, and shocking imagery...",
    "scene_connector": "In the darkness, something stirred..."
}
```

**3. In `video_composer.py`**, add to CAPTION_COLORS:
```python
"horror": "#8B0000"  # Dark red
```

---

## 8. Running the Application

### Start the Streamlit App

```bash
# Make sure venv is activated
# Navigate to project root
cd multimodal_story_generator

# Run the app
streamlit run app/main.py
```

The app will open at: **http://localhost:8501**

### Usage Walkthrough

1. **Open the app** in your browser
2. **Select a theme** from the sidebar dropdown
3. **Adjust settings** (quality, duration, captions toggle)
4. **Choose input tab**:
   - Text: Type your story idea
   - Images: Upload JPG/PNG photos
   - Videos: Upload MP4/MOV clips
   - Mixed: Combine all three
5. **Click "Generate Story"**
6. **Wait for pipeline** (30 seconds – 5 minutes depending on input size)
7. **Download** the generated MP4 video

---

## 9. API Keys & Configuration

### Free Usage (No API Keys Needed)

The system works completely free using:
- HuggingFace local models (GPT-2 for story generation)
- gTTS or pyttsx3 for TTS
- Open CLIP model (downloaded automatically)

### For Better LLM Quality (Optional)

**Using OpenAI (GPT-3.5/4):**
```bash
# In your .env file:
OPENAI_API_KEY=sk-your-key-here

# Install:
pip install langchain-openai openai
```

**Using Ollama (Local LLMs, best quality + free):**
```bash
# Install Ollama: https://ollama.ai
ollama pull llama2
# or
ollama pull mistral

# No API key needed - runs locally
```

**Using HuggingFace Inference API:**
```bash
HUGGINGFACE_TOKEN=hf_your_token_here
```

---

## 10. Testing the Pipeline

### Quick Smoke Test

```python
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
```

Run with:
```bash
python test_pipeline.py
```

### Test TTS

```python
from utils.tts_engine import TTSEngine

tts = TTSEngine()
audio_path = tts.synthesize(
    "This is a test of the adventure voice style.",
    voice_style="energetic"
)
print(f"Audio saved to: {audio_path}")
```

---

## 11. Common Errors & Fixes

### Error: `ModuleNotFoundError: No module named 'moviepy'`
```bash
pip install moviepy
```

### Error: `OSError: MoviePy depends on ffmpeg`
```bash
# Install ffmpeg system-wide
# Ubuntu: sudo apt install ffmpeg
# macOS: brew install ffmpeg
# Windows: winget install ffmpeg
```

### Error: `torch` installation fails on Windows
```bash
# Install CPU-only version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Error: `TextClip` fails with ImageMagick error
```bash
# Install ImageMagick
# Ubuntu: sudo apt install imagemagick
# macOS: brew install imagemagick
# Windows: https://imagemagick.org/script/download.php

# Then fix ImageMagick policy (Linux):
sudo nano /etc/ImageMagick-6/policy.xml
# Change: <policy domain="path" rights="none" pattern="@*"/>
# To:     <policy domain="path" rights="read|write" pattern="@*"/>
```

### Error: `gTTS connection failed`
```bash
# gTTS requires internet. Use pyttsx3 for offline:
pip install pyttsx3
# It will auto-fallback to pyttsx3 if gTTS fails
```

### Warning: `HuggingFace model too slow`
```bash
# Install lighter model support
pip install accelerate
# Or use OpenAI/Ollama for faster generation
```

### Error: Streamlit app won't start
```bash
# Check Python version
python --version  # Must be 3.9 or 3.10

# Try explicit port
streamlit run app/main.py --server.port 8502
```

---

## 12. Viva Preparation

### Key Questions & Answers

**Q: What is the architecture of your system?**  
A: Our system has 5 layers: User Layer → Frontend (Streamlit) → AI Processing → Video Composition → Output. The AI layer has 6 modules: Input Analyzer, Feature Extractor, Story Generator, Emotion Analyzer, TTS Engine, and Video Composer.

**Q: How does the Theme Switching work?**  
A: The theme is passed as a parameter through all AI modules. It modifies the LLM system prompt and instruction (prompt engineering), the TTS voice selection, the caption color and font, the video transition style, and the background music type.

**Q: What is GMM Clustering and why use it?**  
A: Gaussian Mixture Model groups semantically similar scenes together using probabilistic clustering. We use it over K-Means because GMM allows overlapping clusters (soft assignment), which better represents scenes that could belong to multiple narrative groups.

**Q: What is CLIP and why use it for images?**  
A: CLIP (Contrastive Language-Image Pretraining) from OpenAI converts images into semantic embedding vectors that share the same space as text embeddings. This allows us to compare and cluster visual and textual content together.

**Q: What is LangChain's role?**  
A: LangChain is a framework for building LLM applications. We use it to structure prompts (system + user messages), manage model providers (OpenAI, HuggingFace, Ollama), and handle the generation pipeline.

**Q: How does emotion affect voice modulation?**  
A: The emotion analyzer detects the dominant emotion in the script using keyword frequency analysis. This emotion maps to TTS parameters: speaking rate (speed), pitch (tone), and volume. For example, "exciting" content gets +20% rate and +8Hz pitch.

**Q: What happens if the user only provides text (no images)?**  
A: The text is embedded using Sentence-Transformers, fed to the story generator, and the video composer creates animated text slides from the story script instead of visual scenes.

**Q: How is audio synchronized with video?**  
A: MoviePy's `set_audio()` method attaches the TTS narration to the video clip. The shorter of video/audio is trimmed to match the longer one, ensuring perfect synchronization.

**Q: Why use Streamlit over React/Flask?**  
A: For a student project, Streamlit allows rapid prototyping with Python only — no JavaScript, HTML, or separate frontend server needed. It handles file uploads, progress bars, and video display natively.

---

## 📎 Dependencies Summary

| Library | Version | Purpose |
|---------|---------|---------|
| streamlit | ≥1.32 | Web UI |
| transformers | ≥4.38 | CLIP, emotion models |
| torch | ≥2.0 | Deep learning backend |
| sentence-transformers | ≥2.6 | Text embeddings |
| langchain | ≥0.1 | LLM orchestration |
| opencv-python | ≥4.9 | Video frame extraction |
| scikit-learn | ≥1.4 | GMM clustering |
| moviepy | ≥1.0.3 | Video composition |
| gTTS / edge-tts | latest | Text-to-speech |
| Pillow | ≥10.0 | Image processing |

---

*Generated for: Multimodal Story Generator with Theme-Controlled Narrative & Voice Modulation*  
*Version: 1.0.0*