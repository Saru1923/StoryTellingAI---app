"""
🎬 Multimodal Story Generator with Theme-Controlled Narrative & Voice Modulation
Main Streamlit Application — Luminous Cinematic Edition
"""

import streamlit as st
import tempfile
import time
from pathlib import Path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from utils.input_analyzer import InputAnalyzer
from utils.feature_extractor import FeatureExtractor
from utils.story_generator import StoryGenerator
from utils.emotion_analyzer import EmotionAnalyzer
from utils.tts_engine import TTSEngine
from utils.video_composer import VideoComposer

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🎬 Multimodal Story Generator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Outfit:wght@300;400;500;600;700&display=swap');

  :root {
    --cream:       #fdf8f0;
    --parchment:   #f5ede0;
    --warm-white:  #fffcf7;
    --gold:        #c8922a;
    --gold-light:  #e8b84b;
    --gold-pale:   #f5dea8;
    --copper:      #b5651d;
    --ink:         #2c1f0e;
    --ink-mid:     #4a3520;
    --ink-soft:    #7a6348;
    --ink-muted:   #a08060;
    --ink-faint:   #c8b49a;
    --rose:        #d4607a;
    --teal:        #2a8a7e;
    --lavender:    #7c5cbf;
    --sage:        #4a8a5a;
    --border:      #e0d0bc;
    --border-soft: #ecddc8;
    --shadow:      rgba(44, 31, 14, 0.08);
    --shadow-md:   rgba(44, 31, 14, 0.14);
    --shadow-lg:   rgba(44, 31, 14, 0.22);
  }

  html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    color: var(--ink);
  }

  .stApp {
    background: var(--cream);
    background-image:
      radial-gradient(ellipse 80% 60% at 15% 10%, rgba(232,184,75,0.08) 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 85% 90%, rgba(181,101,29,0.06) 0%, transparent 55%),
      url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E");
  }

  .main .block-container { padding-top: 2rem; max-width: 1100px; }

  /* ── HERO ── */
  .hero-wrap {
    text-align: center;
    padding: 1.5rem 0 0.5rem;
    position: relative;
  }
  .hero-eyebrow {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
  }
  .hero-eyebrow::before, .hero-eyebrow::after {
    content: "";
    display: inline-block;
    width: 36px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-light));
  }
  .hero-eyebrow::after { background: linear-gradient(90deg, var(--gold-light), transparent); }

  .hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(2.6rem, 5.5vw, 4.2rem);
    font-weight: 700;
    font-style: italic;
    line-height: 1.05;
    letter-spacing: -0.01em;
    color: var(--ink);
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 20px rgba(200,146,42,0.15);
  }
  .hero-title span {
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 50%, var(--copper) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Film strip ornament */
  .film-strip {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    margin: 0.8rem auto 0.6rem;
  }
  .film-hole {
    width: 8px; height: 8px;
    border-radius: 2px;
    background: var(--gold-light);
    opacity: 0.55;
  }
  .film-bar {
    height: 2px; width: 40px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
  }

  .subtitle {
    text-align: center;
    color: var(--ink-soft);
    font-size: 0.98rem;
    font-weight: 300;
    letter-spacing: 0.04em;
    margin-bottom: 2rem;
  }

  /* ── SECTION HEADERS ── */
  .section-header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--ink-mid);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 1rem 0 0.8rem;
    letter-spacing: 0.01em;
  }

  /* ── TABS ── */
  .stTabs [data-baseweb="tab-list"] {
    background: var(--parchment);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid var(--border);
    box-shadow: 0 2px 8px var(--shadow);
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    padding: 8px 16px;
    font-weight: 500;
    font-size: 0.88rem;
    color: var(--ink-muted) !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s;
  }
  .stTabs [aria-selected="true"] {
    background: var(--warm-white) !important;
    color: var(--gold) !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 2px 6px var(--shadow) !important;
  }

  /* ── INPUTS ── */
  .stTextArea textarea, .stTextInput input {
    background: var(--warm-white) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.93rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
  }
  .stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px rgba(200,146,42,0.12) !important;
  }
  .stTextArea textarea::placeholder { color: var(--ink-faint) !important; }

  /* ── GENERATE BUTTON ── */
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--gold), var(--copper)) !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.05rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 14px 32px !important;
    letter-spacing: 0.04em !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 20px rgba(200,146,42,0.35) !important;
  }
  .stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(200,146,42,0.5) !important;
  }

  /* ── DOWNLOAD BUTTON ── */
  .stDownloadButton > button {
    background: var(--warm-white) !important;
    color: var(--sage) !important;
    border: 1.5px solid #b8d8be !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
  }
  .stDownloadButton > button:hover {
    background: #f0faf2 !important;
    box-shadow: 0 4px 16px rgba(74,138,90,0.18) !important;
  }

  /* ── INFO BOXES ── */
  .info-note {
    background: linear-gradient(135deg, #fdf5e8, #fef9f0);
    border-left: 3px solid var(--gold-light);
    padding: 10px 15px;
    border-radius: 0 8px 8px 0;
    margin: 8px 0;
    color: var(--ink-soft);
    font-size: 0.86rem;
    box-shadow: 0 2px 8px var(--shadow);
  }
  .status-box {
    background: linear-gradient(135deg, #fdf5e8, #fef9f0);
    border-left: 4px solid var(--gold);
    padding: 10px 16px;
    border-radius: 0 8px 8px 0;
    margin: 6px 0;
    color: var(--ink-mid);
    font-size: 0.88rem;
    font-weight: 500;
    box-shadow: 0 2px 8px var(--shadow);
  }

  /* ── PROGRESS ── */
  .stProgress > div > div > div {
    background: linear-gradient(90deg, var(--gold), var(--copper)) !important;
    border-radius: 4px !important;
  }
  .stProgress > div > div {
    background: var(--border-soft) !important;
    border-radius: 4px !important;
  }

  /* ── RESULTS ── */
  .results-header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2rem;
    font-weight: 700;
    font-style: italic;
    color: var(--ink);
    text-align: center;
    margin: 2rem 0 0.3rem;
    letter-spacing: -0.01em;
  }
  .results-divider {
    width: 60px; height: 2px;
    margin: 0 auto 1.8rem;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
  }

  /* ── VIDEO WRAPPER ── */
  .video-wrapper {
    background: var(--parchment);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 8px 40px var(--shadow-lg);
    margin-bottom: 1rem;
  }

  /* ── DASHBOARD CARDS ── */
  .dash-card {
    background: var(--warm-white);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    margin-bottom: 4px;
    box-shadow: 0 2px 12px var(--shadow);
  }
  .dash-card:hover {
    border-color: var(--gold-pale);
    transform: translateY(-1px);
    box-shadow: 0 6px 24px var(--shadow-md);
  }
  .dash-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, var(--gold));
    border-radius: 12px 12px 0 0;
  }
  .dash-label {
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin-bottom: 7px;
  }
  .dash-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--ink);
    line-height: 1;
  }
  .dash-value-sm {
    font-size: 0.93rem;
    font-weight: 500;
    color: var(--ink-mid);
    line-height: 1.5;
  }
  .divider { border-top: 1px solid var(--border-soft); margin: 9px 0; }

  /* ── EMOTION BARS ── */
  .emo-track {
    background: var(--border-soft);
    border-radius: 3px;
    height: 6px;
    margin-top: 8px;
    overflow: hidden;
  }
  .emo-fill { height: 6px; border-radius: 3px; transition: width 0.5s ease; }

  .emo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 9px; }
  .emo-name { font-size: 0.78rem; color: var(--ink-muted); min-width: 85px; }
  .emo-bg { flex: 1; background: var(--border-soft); border-radius: 3px; height: 7px; overflow: hidden; }
  .emo-fg { height: 7px; border-radius: 3px; }
  .emo-pct { font-size: 0.72rem; color: var(--ink-faint); min-width: 30px; text-align: right; }

  /* ── SCRIPT BOX ── */
  .script-box {
    background: var(--parchment);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 22px;
    color: var(--ink-soft);
    font-size: 0.87rem;
    line-height: 1.85;
    max-height: 240px;
    overflow-y: auto;
    margin-bottom: 12px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) var(--parchment);
    box-shadow: inset 0 2px 8px rgba(44,31,14,0.04);
    font-family: 'Outfit', sans-serif;
  }
  .script-box::-webkit-scrollbar { width: 4px; }
  .script-box::-webkit-scrollbar-track { background: var(--parchment); }
  .script-box::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  /* ── SCENE PILLS ── */
  .scene-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--warm-white);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.78rem;
    color: var(--ink-soft);
    margin: 3px;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 1px 4px var(--shadow);
  }
  .scene-pill:hover { border-color: var(--gold-pale); box-shadow: 0 2px 8px var(--shadow-md); }
  .scene-num {
    background: linear-gradient(135deg, var(--gold), var(--copper));
    color: #fff;
    border-radius: 50%;
    width: 20px; height: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.68rem; font-weight: 700;
  }

  /* ── SECTION TITLE WITH LINE ── */
  .dash-section-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    font-weight: 600;
    font-style: italic;
    color: var(--ink-mid);
    letter-spacing: 0.01em;
    margin: 1.6rem 0 0.8rem;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .dash-section-title::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
  }

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] {
    background: var(--parchment) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 16px var(--shadow) !important;
  }
  [data-testid="stSidebar"] h2 {
    color: var(--ink) !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-style: italic !important;
  }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stSlider label,
  [data-testid="stSidebar"] .stCheckbox label,
  [data-testid="stSidebar"] p {
    color: var(--ink-soft) !important;
    font-size: 0.88rem !important;
  }
  [data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--warm-white) !important;
    border-color: var(--border) !important;
    color: var(--ink) !important;
  }

  .theme-card {
    background: var(--warm-white);
    border-radius: 10px;
    padding: 12px 14px;
    border-left: 3px solid;
    font-size: 0.81rem;
    line-height: 2;
    color: var(--ink-soft);
    box-shadow: 0 2px 10px var(--shadow);
  }
  .theme-card b { color: var(--ink-mid); }

  /* ── STACKED INPUT CARD STYLE ── */
  .input-card {
    background: var(--warm-white);
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 12px var(--shadow);
  }

  hr { border-color: var(--border) !important; }

  /* Selectbox, radio, slider styling fixes */
  .stSlider [data-testid="stSlider"] div > div > div > div {
    background: var(--gold) !important;
  }

  /* Alert styling */
  .stAlert {
    border-radius: 10px !important;
    border: none !important;
  }

  /* Success color */
  .stSuccess { background: #f0faf2 !important; color: var(--sage) !important; }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: var(--parchment) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 10px !important;
  }
  [data-testid="stFileUploader"]:hover {
    border-color: var(--gold-light) !important;
    background: #fdf9f0 !important;
  }

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# THEME CONFIGURATION
# ─────────────────────────────────────────────
THEMES = {
    "🎯 Default": {
        "key": "default", "description": "Standard balanced narration",
        "voice_style": "neutral", "music": "ambient", "color": "#888888",
        "transition": "fade", "font": "Arial",
    },
    "⚔️ Adventure": {
        "key": "adventure", "description": "Fast-paced, thrilling journey",
        "voice_style": "energetic", "music": "epic_orchestral", "color": "#e07040",
        "transition": "wipe", "font": "Impact",
    },
    "💕 Romance": {
        "key": "romance", "description": "Heartfelt emotional storytelling",
        "voice_style": "soft_warm", "music": "soft_piano", "color": "#d4607a",
        "transition": "dissolve", "font": "Georgia",
    },
    "😂 Comedy": {
        "key": "comedy", "description": "Humorous, witty, light-hearted",
        "voice_style": "expressive_lively", "music": "upbeat_quirky", "color": "#c8922a",
        "transition": "bounce", "font": "Comic Sans MS",
    },
    "🔍 Mystery": {
        "key": "mystery", "description": "Suspenseful with hidden clues",
        "voice_style": "calm_suspenseful", "music": "dark_ambient", "color": "#7c5cbf",
        "transition": "iris", "font": "Courier New",
    },
    "🎙️ Documentary": {
        "key": "documentary", "description": "Factual, informative narration",
        "voice_style": "professional_neutral", "music": "minimal_cinematic", "color": "#2a8a7e",
        "transition": "cut", "font": "Helvetica",
    }
}

EMOTION_COLORS = {
    "happy": "#c8922a", "sad": "#6495ED", "dramatic": "#e07040",
    "exciting": "#d4607a", "mysterious": "#7c5cbf",
    "romantic": "#d4607a", "calm": "#2a8a7e", "neutral": "#4a8a9a"
}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎭 Theme Control")
    st.markdown("---")

    selected_theme_name = st.selectbox(
        "Select Narrative Theme", list(THEMES.keys()), index=0,
        help="Theme controls story tone, voice, music, and transitions"
    )
    theme     = THEMES[selected_theme_name]
    theme_key = theme["key"]

    st.markdown(f"""
    <div class="theme-card" style="border-color:{theme['color']};">
        <b>🎨 Voice Style:</b> {theme['voice_style']}<br>
        <b>🎵 Music:</b> {theme['music']}<br>
        <b>✂️ Transition:</b> {theme['transition']}<br>
        <b>🔤 Font:</b> {theme['font']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    max_duration     = st.slider("Max Video Duration (seconds)", 15, 600, 300)
    output_quality   = st.selectbox("Output Quality", ["720p", "1080p", "480p"], index=0)
    include_captions = st.checkbox("Include Captions", value=True)
    include_music    = st.checkbox("Include Background Music", value=True)

    st.markdown("---")
    st.markdown("## 🔑 Groq API Key")
    st.markdown("*Free key — no credit card needed. Get yours at console.groq.com*")

    env_groq_key = os.getenv("GROQ_API_KEY", "")
    groq_key_input = st.text_input(
        "Groq API Key — Free, Required",
        value=env_groq_key if env_groq_key not in ("", "your-groq-api-key-here") else "",
        type="password",
        help="100% free at console.groq.com — powers Llama 4 Vision + Llama 3.3 story generation"
    )
    if groq_key_input:
        os.environ["GROQ_API_KEY"] = groq_key_input
        st.success("✓ Groq key active — Llama 4 Vision + Llama 3.3 70B ready")

    has_groq = bool(os.environ.get("GROQ_API_KEY", ""))
    if not has_groq:
        st.warning("⚠️ No API key — using template stories. Add free Groq key above for AI stories.")

# ─────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
  <div class="hero-eyebrow">✦ AI-Powered Storytelling ✦</div>
  <div class="hero-title">🎬 <span>Multimodal</span> Story Generator</div>
  <div class="film-strip">
    <div class="film-hole"></div><div class="film-hole"></div>
    <div class="film-bar"></div>
    <div class="film-hole"></div><div class="film-hole"></div><div class="film-hole"></div>
    <div class="film-bar"></div>
    <div class="film-hole"></div><div class="film-hole"></div>
  </div>
  <div class="subtitle">Transform images, videos &amp; text into themed cinematic stories</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# INPUT TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📝 Text Input", "🖼️ Image Upload", "🎥 Video Upload", "🔀 Mixed Input"])

inputs = {"text": None, "images": [], "videos": [], "mode": None}

with tab1:
    st.markdown('<div class="section-header">📝 Text Prompt</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-note">
        💡 <b>Text-only input</b> generates a story and returns an <b>audio narration</b>.
        Upload images to get a full video with your images + captions + narration.
    </div>""", unsafe_allow_html=True)
    text_input = st.text_area(
        "Describe your story idea",
        placeholder="e.g. A lone traveler discovers an ancient temple hidden in a dense jungle...",
        height=150, label_visibility="collapsed"
    )
    if text_input:
        inputs["text"] = text_input
        inputs["mode"] = "text"

with tab2:
    st.markdown('<div class="section-header">🖼️ Upload Images</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-note">
        💡 Upload 2–6 images. Each image becomes a scene. The AI reads your images and writes a coherent story around them.
    </div>""", unsafe_allow_html=True)
    uploaded_images = st.file_uploader(
        "Upload images", type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True, label_visibility="collapsed"
    )
    if uploaded_images:
        inputs["images"] = uploaded_images
        inputs["mode"]   = "images"
        cols = st.columns(min(len(uploaded_images), 4))
        for i, img in enumerate(uploaded_images[:4]):
            with cols[i % 4]:
                st.image(img, caption=f"Scene {i+1}", use_column_width=True)
        if len(uploaded_images) > 4:
            st.caption(f"+ {len(uploaded_images) - 4} more image(s)")

with tab3:
    st.markdown('<div class="section-header">🎥 Upload Videos</div>', unsafe_allow_html=True)
    uploaded_videos = st.file_uploader(
        "Upload video clips", type=["mp4", "mov", "avi"],
        accept_multiple_files=True, label_visibility="collapsed"
    )
    if uploaded_videos:
        inputs["videos"] = uploaded_videos
        inputs["mode"]   = "videos"
        for vid in uploaded_videos:
            st.video(vid)

with tab4:
    st.markdown('<div class="section-header">🔀 Mixed Input</div>', unsafe_allow_html=True)
    mix_text   = st.text_area("Add a text description (optional)", height=80)
    mix_images = st.file_uploader("Add images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="mix_img")
    mix_videos = st.file_uploader("Add videos", type=["mp4", "mov"], accept_multiple_files=True, key="mix_vid")
    if mix_text or mix_images or mix_videos:
        inputs["text"]   = mix_text or None
        inputs["images"] = mix_images or []
        inputs["videos"] = mix_videos or []
        inputs["mode"]   = "mixed"

# ─────────────────────────────────────────────
# GENERATE BUTTON
# ─────────────────────────────────────────────
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button(
        f"✨ Generate {selected_theme_name} Story",
        use_container_width=True, type="primary"
    )

# ─────────────────────────────────────────────
# GENERATION PIPELINE
# ─────────────────────────────────────────────
if generate_btn:
    has_input = inputs["text"] or inputs["images"] or inputs["videos"]

    if not has_input:
        st.error("⚠️ Please provide at least one input (text, image, or video)!")
    else:
        progress_bar = st.progress(0)
        status_text  = st.empty()

        try:
            # Step 1
            status_text.markdown('<div class="status-box">🔍 Step 1/6 — Analyzing inputs...</div>', unsafe_allow_html=True)
            progress_bar.progress(10)
            analyzer        = InputAnalyzer()
            analysis_result = analyzer.analyze(inputs)
            is_text_only    = (
                analysis_result.get("input_type") == "text"
                and not analysis_result.get("image_paths")
                and not analysis_result.get("video_paths")
            )
            time.sleep(0.3)

            # Step 2
            status_text.markdown('<div class="status-box">🧠 Step 2/6 — Extracting semantic features...</div>', unsafe_allow_html=True)
            progress_bar.progress(25)
            extractor  = FeatureExtractor()
            embeddings = extractor.extract(analysis_result)
            time.sleep(0.3)

            # Step 3
            ai_note = " (AI reading your images)" if not is_text_only else ""
            status_text.markdown(f'<div class="status-box">✍️ Step 3/6 — Generating {selected_theme_name} story{ai_note}...</div>', unsafe_allow_html=True)
            progress_bar.progress(45)
            story_gen    = StoryGenerator()
            story_result = story_gen.generate(embeddings, theme=theme_key, theme_config=theme)
            time.sleep(0.3)

            # Step 4
            status_text.markdown('<div class="status-box">💭 Step 4/6 — Analyzing emotions for voice modulation...</div>', unsafe_allow_html=True)
            progress_bar.progress(60)
            emotion_analyzer = EmotionAnalyzer()
            emotion_result   = emotion_analyzer.analyze(story_result["script"])
            time.sleep(0.3)

            # Step 5
            status_text.markdown(f'<div class="status-box">🔊 Step 5/6 — Generating {theme["voice_style"]} narration...</div>', unsafe_allow_html=True)
            progress_bar.progress(75)
            tts        = TTSEngine()
            audio_path = tts.synthesize(
                story_result["script"],
                voice_style=theme["voice_style"],
                emotion=emotion_result["dominant_emotion"]
            )
            time.sleep(0.3)

            # Step 6
            compose_msg = "🔊 Step 6/6 — Finalising audio narration..." if is_text_only else \
                          "🎬 Step 6/6 — Composing video with images + captions + narration..."
            status_text.markdown(f'<div class="status-box">{compose_msg}</div>', unsafe_allow_html=True)
            progress_bar.progress(90)

            composer    = VideoComposer()
            output_path = composer.compose(
                inputs={**analysis_result, "input_type": analysis_result.get("input_type", "text")},
                story=story_result,
                audio_path=audio_path,
                theme_config=theme,
                include_captions=include_captions,
                include_music=include_music,
                quality=output_quality,
                max_duration=max_duration
            )

            progress_bar.progress(100)
            status_text.markdown(
                '<div class="status-box" style="border-color:#4a8a5a;color:#3a7a4a;background:linear-gradient(135deg,#f0faf2,#f8fff9);">✅ Story generated successfully!</div>',
                unsafe_allow_html=True
            )

            # ═══════════════════════════════════════════════
            # RESULTS
            # ═══════════════════════════════════════════════
            st.markdown('<div class="results-header">🎉Your Story is Ready</div>', unsafe_allow_html=True)
            st.markdown('<div class="results-divider"></div>', unsafe_allow_html=True)

            # ── 1. VIDEO / AUDIO PLAYER ──────────────────────────
            if is_text_only:
                st.markdown("### 🔊 Audio Narration")
                st.markdown("""
                <div class="info-note">🎙️ Your story has been narrated as audio. Upload images to also get a video!</div>
                """, unsafe_allow_html=True)
                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes)
                    ext = Path(output_path).suffix
                    _, dl_col, _ = st.columns([1, 2, 1])
                    with dl_col:
                        st.download_button(
                            "⬇️ Download Audio", audio_bytes,
                            file_name=f"narration_{theme_key}_{int(time.time())}{ext}",
                            mime="audio/mpeg" if ext == ".mp3" else "audio/wav",
                             use_container_width=True)
            else:
                if os.path.exists(output_path) and output_path.endswith(".mp4"):
                    with open(output_path, "rb") as f:
                        video_bytes = f.read()
                    st.markdown('<div class="video-wrapper">', unsafe_allow_html=True)
                    st.video(video_bytes)
                    st.markdown('</div>', unsafe_allow_html=True)
                    _, dl_col, _ = st.columns([1, 2, 1])
                    with dl_col:
                        st.download_button(
                            "⬇️ Download Video", video_bytes,
                            file_name=f"story_{theme_key}_{int(time.time())}.mp4",
                            mime="video/mp4", use_container_width=True
                        )
                else:
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes)
                        try:
                            import moviepy
                            mv = getattr(moviepy, "__version__", "unknown")
                            st.warning(
                                f"⚠️ Video rendering fell back to audio. MoviePy {mv} is installed — "
                                f"check terminal/logs. Common fixes: (1) Install ImageMagick for captions. "
                                f"(2) Ensure ffmpeg is on your PATH."
                            )
                        except ImportError:
                            st.warning("⚠️ MoviePy not installed. Run: `pip install moviepy` then restart.")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── 3. STORY SCRIPT ──────────────────────────────────
            st.markdown('<div class="dash-section-title">📖 Story Script</div>', unsafe_allow_html=True)
            script_html = story_result["script"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            st.markdown(f'<div class="script-box">{script_html}</div>', unsafe_allow_html=True)

            # ── 4. ANALYSIS DASHBOARD ────────────────────────────
            st.markdown('<div class="dash-section-title">📊 Analysis Dashboard</div>', unsafe_allow_html=True)

            word_count   = len(story_result["script"].split())
            scene_count  = story_result.get("scene_count", 0)
            dom_emotion  = emotion_result.get("dominant_emotion", "neutral")
            emo_label    = dom_emotion.capitalize()
            emo_color    = EMOTION_COLORS.get(dom_emotion, "#4a8a9a")
            emo_conf     = int(emotion_result.get("confidence", 1.0) * 100)
            out_label    = "🔊 Audio" if is_text_only else "🎥 Video"

            # Row A — metrics
            ra1, ra2, ra3 = st.columns(3)
            with ra1:
                st.markdown(f"""
                <div class="dash-card" style="--accent:#c8922a;">
                    <div class="dash-label">📝 Word Count</div>
                    <div class="dash-value">{word_count}</div>
                </div>""", unsafe_allow_html=True)
            with ra2:
                st.markdown(f"""
                <div class="dash-card" style="--accent:#d4607a;">
                    <div class="dash-label">🎬 Scenes</div>
                    <div class="dash-value">{scene_count}</div>
                </div>""", unsafe_allow_html=True)
            with ra3:
                st.markdown(f"""
                <div class="dash-card" style="--accent:#2a8a7e;">
                    <div class="dash-label">📤 Output</div>
                    <div class="dash-value-sm" style="padding-top:6px;font-size:1.1rem;">{out_label}</div>
                </div>""", unsafe_allow_html=True)

            # Row B — theme + emotion
            rb1, rb2 = st.columns(2)
            with rb1:
                st.markdown(f"""
                <div class="dash-card" style="--accent:{theme['color']};">
                    <div class="dash-label">🎭 Theme</div>
                    <div class="dash-value-sm">{selected_theme_name}</div>
                    <div class="divider"></div>
                    <div class="dash-label">🎨 Voice Style</div>
                    <div class="dash-value-sm">{theme['voice_style'].replace('_', ' ').title()}</div>
                </div>""", unsafe_allow_html=True)
            with rb2:
                st.markdown(f"""
                <div class="dash-card" style="--accent:{emo_color};">
                    <div class="dash-label">💭 Dominant Emotion</div>
                    <div class="dash-value-sm" style="color:{emo_color};font-size:1.15rem;">{emo_label}</div>
                    <div class="emo-track">
                        <div class="emo-fill" style="width:{emo_conf}%;background:{emo_color};"></div>
                    </div>
                    <div style="font-size:0.7rem;color:var(--ink-faint);margin-top:5px;">Confidence: {emo_conf}%</div>
                </div>""", unsafe_allow_html=True)

            # Row C — input info + voice modulation
            rc1, rc2 = st.columns(2)
            input_type = analysis_result.get("input_type", "unknown").title()
            tts_params = emotion_result.get("tts_params", {})
            tts_rate   = tts_params.get("rate",   "0%")
            tts_pitch  = tts_params.get("pitch",  "0Hz")
            tts_volume = tts_params.get("volume", "0%")
            img_count  = analysis_result.get("metadata", {}).get("image_count",  0)
            vid_count  = analysis_result.get("metadata", {}).get("video_count",  0)
            txt_len    = analysis_result.get("metadata", {}).get("text_length",  0)

            with rc1:
                st.markdown(f"""
                <div class="dash-card" style="--accent:#2a8a7e;">
                    <div class="dash-label">📂 Input Type</div>
                    <div class="dash-value-sm">{input_type}</div>
                    <div class="divider"></div>
                    <div style="font-size:0.76rem;color:var(--ink-faint);">
                        🖼 Images: <b style="color:var(--ink-soft)">{img_count}</b> &nbsp;·&nbsp;
                        🎥 Videos: <b style="color:var(--ink-soft)">{vid_count}</b> &nbsp;·&nbsp;
                        📝 Text: <b style="color:var(--ink-soft)">{txt_len} chars</b>
                    </div>
                </div>""", unsafe_allow_html=True)
            with rc2:
                st.markdown(f"""
                <div class="dash-card" style="--accent:#7c5cbf;">
                    <div class="dash-label">🔊 Voice Modulation</div>
                    <div style="font-size:0.8rem;color:var(--ink-soft);margin-top:8px;line-height:2.2;">
                        <span style="color:var(--gold);">⏱ Rate</span>&nbsp;&nbsp;&nbsp;{tts_rate}<br>
                        <span style="color:var(--rose);">🎵 Pitch</span>&nbsp;&nbsp;{tts_pitch}<br>
                        <span style="color:var(--copper);">🔉 Volume</span>&nbsp;{tts_volume}
                    </div>
                </div>""", unsafe_allow_html=True)

            # ── 5. EMOTION BREAKDOWN ─────────────────────────────
            emotion_scores = emotion_result.get("scores", {})
            if emotion_scores and len(emotion_scores) > 1:
                st.markdown('<div class="dash-section-title">📈 Emotion Breakdown</div>', unsafe_allow_html=True)
                emo_html = ""
                for emo, score in sorted(emotion_scores.items(), key=lambda x: -x[1]):
                    pct = int(score * 100)
                    col = EMOTION_COLORS.get(emo, "#4a8a9a")
                    emo_html += f"""
                    <div class="emo-row">
                        <span class="emo-name">{emo.capitalize()}</span>
                        <div class="emo-bg"><div class="emo-fg" style="width:{pct}%;background:{col};"></div></div>
                        <span class="emo-pct">{pct}%</span>
                    </div>"""
                st.markdown(
                    f'<div class="dash-card" style="--accent:var(--gold);padding:18px 20px;">{emo_html}</div>',
                    unsafe_allow_html=True
                )

            # ── 6. SCENE CAPTIONS ────────────────────────────────
            if story_result.get("captions") and not is_text_only:
                st.markdown('<div class="dash-section-title">🎞 Scene Captions</div>', unsafe_allow_html=True)
                pills = ""
                for i, cap in enumerate(story_result["captions"]):
                    safe_cap = cap.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    pills += f"""<span class="scene-pill"><span class="scene-num">{i+1}</span>{safe_cap}</span>"""
                st.markdown(f'<div style="margin-bottom:24px;">{pills}</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Generation failed: {str(e)}")
            st.exception(e)