"""
Video Composition Module
Composes final themed story video using MoviePy.
- Text-only input  → returns audio file only (no video)
- Image input      → images + captions + audio narration + theme music → MP4
- Video input      → video clips + captions + audio + theme music → MP4

Fixes applied:
1. MoviePy v1.x AND v2.x compatibility (auto-detects version)
2. Video duration auto-matches the narration audio length
3. Each uploaded music file is mapped to the correct theme key
4. Music is resolved relative to the project root (static/music/)
5. Proper error reporting instead of silent fallback
"""

import os
import shutil
import tempfile
import time
from typing import Any, cast, Dict, List, Optional, Tuple
from pathlib import Path


def _ac(obj: Any) -> Any:
    """
    Cast any MoviePy clip/audio object to Any so Pyright stops resolving
    it as the base Clip/AudioClip stub, which is missing most attributes.
    All MoviePy methods (with_audio, set_audio, .audio, .duration, etc.)
    are available at runtime — this cast is purely for the type checker.
    """
    return cast(Any, obj)


# ─── CAPTION COLORS PER THEME ────────────────────────────────────────────────
CAPTION_COLORS: Dict[str, str] = {
    "default":      "white",
    "adventure":    "#FF6B35",
    "romance":      "#FFB6C1",
    "comedy":       "#FFD700",
    "mystery":      "#DDA0DD",
    "documentary":  "#90EE90",
}

# ─── MUSIC: theme music_key → actual filename in static/music/ ───────────────
MUSIC_FILES: Dict[str, str] = {
    "ambient":           "the_mountain-ambient-487008.mp3",
    "epic_orchestral":   "alexgrohl-upbeat-fun-cheerful-478798.mp3",
    "soft_piano":        "prettyjohn1-romantics-love-valentines-day_39sec-483360.mp3",
    "upbeat_quirky":     "Happiness In Music - Comedy.mp3",           # spaces
    "dark_ambient":      "Universfield - Dark 80s Sci-Fi Atmosphere.mp3",  # spaces
    "minimal_cinematic": "paulyudin-piano-music-piano-485929.mp3",
}

MUSIC_VOLUME: float = 0.18

# ─── PIL CAPTION BAR COLOURS PER THEME ───────────────────────────────────────
CAPTION_BAR_RGBA: Dict[str, Tuple[int, int, int, int]] = {
    "default":     (0,   0,   0,   185),
    "adventure":   (130, 40,  5,   210),
    "romance":     (100, 10,  50,  200),
    "comedy":      (90,  80,  0,   210),
    "mystery":     (15,  0,   45,  210),
    "documentary": (0,   45,  18,  200),
}
CAPTION_TEXT_RGB: Dict[str, Tuple[int, int, int]] = {
    "default":     (255, 255, 255),
    "adventure":   (255, 165,  80),
    "romance":     (255, 182, 193),
    "comedy":      (255, 230,  60),
    "mystery":     (210, 180, 255),
    "documentary": (150, 255, 160),
}


def _find_font(size: int, bold: bool = False) -> Any:
    """
    Return a PIL ImageFont.  Tries multiple Windows + Linux paths.
    Falls back to PIL's built-in default so it NEVER raises.
    Avoids the 'cannot open resource' error on systems where Arial
    is not at the exact path MoviePy expects.
    """
    try:
        from PIL import ImageFont  # type: ignore[import]
    except ImportError:
        return None

    suffix_b = "bd" if bold else ""
    candidates = [
        # Windows — multiple possible paths
        rf"C:\Windows\Fonts\arial{suffix_b}.ttf",
        rf"C:\Windows\Fonts\Arial{suffix_b}.ttf",
        rf"C:\Windows\Fonts\ARIAL{suffix_b.upper()}.TTF",
        # Windows — common fallbacks
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\verdana.ttf",
        r"C:\Windows\Fonts\trebuc.ttf",
        # Linux / WSL / Mac
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/freefont/Free{'SansBold' if bold else 'Sans'}.ttf",
        f"/usr/share/fonts/truetype/crosextra/Carlito-{'Bold' if bold else 'Regular'}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
        # Mac
        f"/System/Library/Fonts/Helvetica.ttc",
        f"/Library/Fonts/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    # Absolute last resort — PIL's bitmap default (always works)
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10
    except Exception:
        pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _find_font_path(bold: bool = False) -> str:
    """
    Return a valid font FILE PATH string for MoviePy TextClip's font= param.
    MoviePy needs a real file path, not a PIL font object.
    Returns empty string if nothing found (TextClip will use its own default).
    """
    suffix_b = "bd" if bold else ""
    candidates = [
        # Windows
        rf"C:\Windows\Fonts\arial{suffix_b}.ttf",
        rf"C:\Windows\Fonts\Arial{suffix_b}.ttf",
        rf"C:\Windows\Fonts\arial.ttf",
        rf"C:\Windows\Fonts\Arial.ttf",
        rf"C:\Windows\Fonts\calibri.ttf",
        rf"C:\Windows\Fonts\segoeui.ttf",
        rf"C:\Windows\Fonts\tahoma.ttf",
        rf"C:\Windows\Fonts\verdana.ttf",
        # Linux
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/crosextra/Carlito-{'Bold' if bold else 'Regular'}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf",
        # Mac
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    import os as _os
    for path in candidates:
        if _os.path.exists(path):
            return path
    return ""


def _bake_caption_onto_image(
    img_path: str,
    story_caption: str,
    image_caption: str,
    theme_key: str,
    target_w: int,
    target_h: int,
) -> str:
    """
    Resize the image and bake TWO caption lines onto the bottom using PIL only.
      Line 1 (small, light):  what is IN the image       (image_caption)
      Line 2 (large, bright): story narrative caption    (story_caption)

    Returns path to a temp JPEG — or the original path if PIL fails.
    Never raises; the pipeline always continues even if baking fails.

    Note: PIL.Image.LANCZOS is accessed via getattr() to avoid the Pyright
    false-positive 'LANCZOS is not a known attribute of module PIL.Image'.
    """
    try:
        from PIL import Image, ImageDraw  # type: ignore[import]

        _LANCZOS = getattr(Image, "LANCZOS", None) or getattr(Image, "ANTIALIAS", None)  # type: ignore[attr-defined]

        img: Any = Image.open(img_path).convert("RGBA")
        img = img.resize((target_w, target_h), _LANCZOS) if _LANCZOS else img.resize((target_w, target_h))

        def _wrap(text: str, max_chars: int) -> str:
            words = text.split()
            lines: List[str] = []
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 <= max_chars:
                    cur = (cur + " " + w).strip()
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            return "\n".join(lines) if lines else text

        story_font = _find_font(28, bold=True)
        image_font = _find_font(20, bold=False)

        story_text = _wrap(story_caption[:80],  52)
        image_text = _wrap(image_caption[:100], 64)

        # Measure text heights
        story_h, image_h = 36, 24
        try:
            from PIL import Image as _I, ImageDraw as _ID  # type: ignore[import]
            td: Any = _ID.Draw(_I.new("RGBA", (10, 10)))
            if story_font and hasattr(td, "multiline_textbbox"):
                s_bb    = td.multiline_textbbox((0, 0), story_text, font=story_font, spacing=4)
                i_bb    = td.multiline_textbbox((0, 0), image_text, font=image_font, spacing=3)
                story_h = int(s_bb[3] - s_bb[1])
                image_h = int(i_bb[3] - i_bb[1])
        except Exception:
            pass

        padding   = 12
        bar_h     = story_h + image_h + padding * 3 + 6
        bar_y     = target_h - bar_h
        bar_color = CAPTION_BAR_RGBA.get(theme_key, (0, 0, 0, 185))
        txt_color = CAPTION_TEXT_RGB.get(theme_key, (255, 255, 255))
        muted: Tuple[int, int, int] = (
            min(255, txt_color[0] + 55),
            min(255, txt_color[1] + 55),
            min(255, txt_color[2] + 55),
        )

        overlay: Any = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rectangle([(0, bar_y), (target_w, target_h)], fill=bar_color)
        img = Image.alpha_composite(img, overlay)

        draw: Any = ImageDraw.Draw(img)
        draw.multiline_text((padding, bar_y + padding),image_text, font=image_font, fill=muted + (210,), spacing=3)
        draw.multiline_text((padding, bar_y + padding + image_h + 6),story_text, font=story_font, fill=txt_color + (255,), spacing=4)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.convert("RGB").save(tmp.name, "JPEG", quality=93)
        tmp.close()
        return tmp.name

    except Exception as exc:
        print(f"PIL caption bake failed ({exc}) — using original image without caption")
        return img_path


def _detect_moviepy_version() -> Tuple[int, Any]:
    """
    Returns (major_version, moviepy_module_or_None).
    Tries v2.x API first, then v1.x, then gives up.
    """
    # Try MoviePy v2.x
    try:
        import moviepy as mp2
        version_str = getattr(mp2, "__version__", "2.0.0")
        major = int(version_str.split(".")[0])
        if major >= 2:
            return major, mp2
    except Exception:
        pass

    # Try MoviePy v1.x via moviepy.editor
    try:
        import moviepy.editor as mp1  # noqa: F401
        return 1, None  # We'll import directly in methods
    except Exception:
        pass

    return 0, None


class VideoComposer:

    QUALITY_MAP: Dict[str, tuple] = {
        "480p":  (854,  480),
        "720p":  (1280, 720),
        "1080p": (1920, 1080),
    }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────
    def compose(
        self,
        inputs: Dict[str, Any],
        story: Dict[str, Any],
        audio_path: str,
        theme_config: Dict[str, Any],
        include_captions: bool = True,
        include_music: bool = True,
        quality: str = "720p",
        max_duration: int = 180,
        output_dir: Optional[str] = None,
    ) -> str:
        input_type:  str       = inputs.get("input_type", "text")
        image_paths: List[str] = inputs.get("image_paths", []) or []
        video_paths: List[str] = inputs.get("video_paths", []) or []

        if input_type == "text" and not image_paths and not video_paths:
            print("Text-only → returning audio only.")
            return audio_path

        moviepy_version, _ = _detect_moviepy_version()
        print(f"MoviePy version detected: {moviepy_version}.x")

        if moviepy_version == 0:
            print("⚠️  MoviePy not available. Install with: pip install moviepy")
            return self._ffmpeg_fallback(image_paths, audio_path, output_dir, theme_config)

        try:
            if moviepy_version >= 2:
                return self._compose_v2(
                    inputs, story, audio_path, theme_config,
                    include_captions, include_music, quality, max_duration, output_dir,
                )
            else:
                return self._compose_v1(
                    inputs, story, audio_path, theme_config,
                    include_captions, include_music, quality, max_duration, output_dir,
                )
        except Exception as exc:
            print(f"❌ MoviePy v{moviepy_version} composition failed: {exc}")
            import traceback
            traceback.print_exc()
            print("Trying ffmpeg fallback...")
            return self._ffmpeg_fallback(image_paths, audio_path, output_dir, theme_config)

    # ─────────────────────────────────────────────────────────────────────────
    # MOVIEPY v2.x PIPELINE  (moviepy >= 2.0)
    # ─────────────────────────────────────────────────────────────────────────
    def _compose_v2(
        self,
        inputs: Dict[str, Any],
        story: Dict[str, Any],
        audio_path: str,
        theme_config: Dict[str, Any],
        include_captions: bool,
        include_music: bool,
        quality: str,
        max_duration: int,
        output_dir: Optional[str],
    ) -> str:
        from moviepy import (
            AudioFileClip, ColorClip, CompositeVideoClip,
            ImageClip, VideoFileClip, concatenate_videoclips,
        )

        resolution     = self.QUALITY_MAP.get(quality, self.QUALITY_MAP["720p"])
        theme_key      = theme_config.get("key", "default")
        captions       = story.get("captions", [])
        image_captions = story.get("image_captions", captions)  # what's IN each image
        caption_color  = CAPTION_COLORS.get(theme_key, "white")
        image_paths    = inputs.get("image_paths", []) or []
        video_paths    = inputs.get("video_paths", []) or []

        # ── Measure narration duration ────────────────────────────────────────
        narration_clip, narration_duration = self._load_audio_v2(audio_path, AudioFileClip)

        # ── Clamp total video duration to narration length ────────────────────
        # The video must last EXACTLY as long as the narration so nothing is
        # cut off and there is no silent black tail.
        total_video_dur = narration_duration if narration_duration > 0 else 10.0
        if total_video_dur > max_duration:
            total_video_dur = float(max_duration)

        n_images = len(image_paths)
        n_videos = len(video_paths)
        n_sources = max(n_images + n_videos, 1)

        # Each image gets an equal share of the full narration duration so that
        # all images together fill the entire audio — no short clips, no gap.
        img_dur = max(4.0, total_video_dur / n_sources)
        print(f"⏱  Per-image duration: {img_dur:.1f}s ({n_sources} sources, {total_video_dur:.1f}s audio)")

        source_clips: List[Any] = []
        pil_temps:    List[str] = []   # temp files created by PIL baking

        # ── Build image clips — each holds for its full share of the audio ────
        # PIL baking draws captions directly onto the image — no TextClip,
        # no Arial font dependency, no MoviePy font errors.
        for i, img_path in enumerate(image_paths):
            try:
                if not os.path.exists(img_path):
                    continue
                story_cap = captions[i]       if i < len(captions)       else f"Scene {i + 1}"
                img_cap   = image_captions[i] if i < len(image_captions) else story_cap
                if include_captions:
                    baked = _bake_caption_onto_image(
                        img_path, story_cap, img_cap, theme_key,
                        resolution[0], resolution[1],
                    )
                    pil_temps.append(baked)
                    clip: Any = _ac(ImageClip(baked, duration=img_dur))
                else:
                    clip = _ac(ImageClip(img_path, duration=img_dur)).resized(resolution)
                source_clips.append(clip)
                print(f"✓ Image {i + 1}: {os.path.basename(img_path)}  |  {img_cap[:55]}")
            except Exception as exc:
                print(f"Could not load image {img_path}: {exc}")

        # ── Build video clips — loop/trim each to its share of the audio ──────
        for i, vid_path in enumerate(video_paths):
            try:
                if not os.path.exists(vid_path):
                    continue
                offset      = len(source_clips)
                vclip: Any  = _ac(VideoFileClip(vid_path)).resized(resolution)
                vdur: float = float(vclip.duration or 0.0)
                # Loop short videos until they fill their allocated duration
                if vdur > 0 and vdur < img_dur:
                    times   = int(img_dur / vdur) + 1
                    vclip   = _ac(concatenate_videoclips([vclip] * times, method="compose"))
                # Trim to allocated duration
                vclip = vclip.subclipped(0, img_dur)
                vclip = vclip.with_audio(None)
                story_cap = captions[offset]       if offset < len(captions)       else f"Scene {offset + 1}"
                img_cap   = image_captions[offset] if offset < len(image_captions) else story_cap
                if include_captions:
                    label = f"{img_cap} — {story_cap}" if img_cap != story_cap else story_cap
                    vclip = self._add_caption_v2(vclip, label, caption_color, theme_key)
                source_clips.append(vclip)
                print(f"✓ Video {i + 1}: {os.path.basename(vid_path)}  |  {img_cap[:55]}")
            except Exception as exc:
                print(f"Could not load video {vid_path}: {exc}")

        if not source_clips:
            source_clips = self._create_text_slides_v2(
                story.get("script", ""), theme_config, resolution, captions,
                ColorClip, CompositeVideoClip, total_duration=total_video_dur
            )
        if not source_clips:
            source_clips = [_ac(ColorClip(resolution, color=(20, 20, 40), duration=total_video_dur))]

        source_clips = self._apply_transitions_v2(source_clips)
        final_clip: Any = _ac(concatenate_videoclips(source_clips, method="compose"))

        # ── Final trim/extend so video duration == narration duration exactly ──
        final_dur: float = float(final_clip.duration or 0.0)
        if final_dur < total_video_dur - 0.1:
            # Extend by freezing the last frame for the remaining duration
            extra     = total_video_dur - final_dur
            last_src  = source_clips[-1]
            last_src_dur = float(last_src.duration or 1.0)
            freeze: Any  = _ac(last_src.to_ImageClip(t=max(0.0, last_src_dur - 0.05))).with_duration(extra)
            if include_captions and captions:
                freeze = self._add_caption_v2(freeze, captions[-1], caption_color, theme_key)
            final_clip = _ac(concatenate_videoclips([final_clip, freeze], method="compose"))
        elif final_dur > total_video_dur + 0.1:
            final_clip = final_clip.subclipped(0, total_video_dur)

        if float(final_clip.duration or 0.0) > max_duration:
            final_clip = final_clip.subclipped(0, max_duration)

        # Attach narration
        if narration_clip is not None:
            try:
                nc: Any       = _ac(narration_clip)
                nc_dur: float = float(nc.duration or 0.0)
                fd2: float    = float(final_clip.duration or 0.0)
                if nc_dur > fd2 and fd2 > 0:
                    nc = nc.subclipped(0, fd2)
                final_clip = final_clip.with_audio(nc)
            except Exception as exc:
                print(f"Narration attach failed: {exc}")

        if include_music:
            final_clip = self._add_background_music_v2(final_clip, theme_config)

        output_path = self._get_output_path(output_dir, theme_key)
        # Unique temp audio per render — prevents WinError 32 on Windows
        temp_audio_path = os.path.join(
            os.path.dirname(output_path), f"temp_audio_{int(time.time())}.m4a"
        )
        old_temp = os.path.join(os.path.dirname(output_path), "temp_audio.m4a")
        try:
            if os.path.exists(old_temp):
                os.remove(old_temp)
        except Exception:
            pass

        print(f"🎬 Rendering → {output_path}")
        try:
            final_clip.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None,
                temp_audiofile=temp_audio_path,
                remove_temp=True,
            )
        finally:
            try:
                final_clip.close()
            except Exception:
                pass
            for p in [temp_audio_path, old_temp]:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            # Clean up PIL-baked temp images
            for tf in pil_temps:
                try:
                    if tf and os.path.exists(tf):
                        os.remove(tf)
                except Exception:
                    pass

        print(f"✓ Video saved: {output_path}")
        return output_path

    def _load_audio_v2(self, audio_path: str, AudioFileClip: Any) -> tuple:
        """Load audio clip. Returns (Any-typed clip, duration). Safe for v2."""
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 500:
            try:
                clip: Any  = _ac(AudioFileClip(audio_path))
                dur: float = float(clip.duration or 0.0)
                print(f"✓ Narration: {dur:.1f}s")
                return clip, dur
            except Exception as exc:
                print(f"Could not read narration: {exc}")
        return None, 0.0

    def _add_caption_v2(self, clip: Any, text: str, color: str, theme_key: str = "default") -> Any:
        """
        v2 caption overlay — uses PIL baking (no Arial/TextClip dependency).
        Extracts the first frame, bakes the caption bar onto it as an overlay,
        then composites it as a static ImageClip over the video.
        Falls back gracefully — never crashes the pipeline.
        """
        try:
            from moviepy import ImageClip, CompositeVideoClip
            import numpy as np

            if len(text) > 80:
                text = text[:77] + "…"

            clip_w: int   = int(clip.w or 1280)
            clip_h: int   = int(clip.h or 720)
            clip_dur: float = float(clip.duration or 5.0)

            # Build a caption-bar image using PIL
            from PIL import Image as PilImage, ImageDraw as PilDraw

            bar_h   = 72
            bar_img = PilImage.new("RGBA", (clip_w, bar_h), (0, 0, 0, 0))
            bar_color = CAPTION_BAR_RGBA.get(theme_key, (0, 0, 0, 185))
            txt_color = CAPTION_TEXT_RGB.get(theme_key, (255, 255, 255))
            PilDraw.Draw(bar_img).rectangle([(0, 0), (clip_w, bar_h)], fill=bar_color)

            font = _find_font(26, bold=True)
            draw = PilDraw.Draw(bar_img)
            if font:
                draw.text((14, 14), text, font=font, fill=txt_color + (255,))
            else:
                draw.text((14, 14), text, fill=txt_color + (255,))

            # Convert PIL bar to numpy array for MoviePy
            bar_np = np.array(bar_img.convert("RGBA"))

            # Create a transparent full-frame overlay
            overlay_np = np.zeros((clip_h, clip_w, 4), dtype=np.uint8)
            y_start    = clip_h - bar_h
            overlay_np[y_start:y_start + bar_h, :, :] = bar_np

            # Make an RGBA ImageClip from the overlay and composite on the video
            overlay_clip: Any = _ac(
                ImageClip(overlay_np, is_mask=False).with_duration(clip_dur)
            )
            return _ac(CompositeVideoClip([clip, overlay_clip], use_bgclip=True))

        except Exception as exc:
            print(f"Caption skipped (v2): {exc}")
            return clip

    def _apply_transitions_v2(self, clips: List[Any]) -> List[Any]:
        """Fade in/out using MoviePy v2 effects API."""
        try:
            from moviepy.video.fx import FadeIn, FadeOut
            result = []
            for clip in clips:
                cdur: float = float(clip.duration or 0.0)
                if cdur > 1.2:
                    clip = clip.with_effects([FadeIn(0.5), FadeOut(0.5)])
                result.append(clip)
            return result
        except Exception:
            return clips

    def _create_text_slides_v2(
        self, script: str, theme_config: Dict[str, Any],
        resolution: tuple, captions: List[str],
        ColorClip: Any, CompositeVideoClip: Any,
        total_duration: float = 0.0,
    ) -> List[Any]:
        """Create text slides using PIL-baked captions — no TextClip/Arial dependency."""
        from moviepy import ImageClip
        import numpy as np

        theme_key = theme_config.get("key", "default")
        bg_colors = {
            "default": (245, 240, 230), "adventure": (80, 35, 15),
            "romance":  (60, 15, 35),   "comedy":    (255, 245, 200),
            "mystery":  (15,  8,  30),  "documentary": (20, 40, 30),
        }
        bg_color  = bg_colors.get(theme_key, (245, 240, 230))
        sentences = [s.strip() for s in script.replace("\n", " ").split(". ") if len(s.strip()) > 10]
        if not sentences:
            sentences = [script[:200]] if script else ["Your story begins here."]

        # Distribute full narration duration evenly across ALL sentences —
        # no slide-count cap, no fixed 5-second default.
        n_slides   = len(sentences)
        slide_dur  = max(4.0, total_duration / n_slides) if total_duration > 0 else 5.0

        slides = []
        for sentence in sentences:
            slide_np = self._make_text_slide_np(sentence[:160], bg_color, resolution, theme_key)
            try:
                slide: Any = _ac(ImageClip(slide_np, duration=slide_dur))
                slides.append(slide)
            except Exception as exc:
                print(f"Text slide failed: {exc}")
                slides.append(_ac(ColorClip(resolution, color=bg_color, duration=slide_dur)))
        return slides

    def _add_background_music_v2(self, clip: Any, theme_config: Dict[str, Any]) -> Any:
        music_key  = theme_config.get("music", "ambient")
        music_path = self._resolve_music_path(music_key)
        if music_path is None:
            return clip
        print(f"🎵 Mixing music: {os.path.basename(music_path)}")
        try:
            from moviepy import AudioFileClip, CompositeAudioClip
            from moviepy.audio.fx import AudioLoop
            music: Any    = _ac(AudioFileClip(music_path)).with_volume_scaled(MUSIC_VOLUME)
            clip_ac: Any  = _ac(clip)
            clip_dur      = float(clip_ac.duration or 0.0)
            music_dur     = float(music.duration or 0.0)
            if music_dur < clip_dur:
                music = music.with_effects([AudioLoop(duration=clip_dur)])
            else:
                music = music.subclipped(0, clip_dur)
            existing: Any = clip_ac.audio
            if existing is not None:
                combined: Any = _ac(CompositeAudioClip([existing, music]))
                return clip_ac.with_audio(combined)
            return clip_ac.with_audio(music)
        except Exception as exc:
            print(f"Background music failed (v2): {exc}")
            return clip

    # ─────────────────────────────────────────────────────────────────────────
    # MOVIEPY v1.x PIPELINE  (moviepy < 2.0)
    # ─────────────────────────────────────────────────────────────────────────
    def _compose_v1(
        self,
        inputs: Dict[str, Any],
        story: Dict[str, Any],
        audio_path: str,
        theme_config: Dict[str, Any],
        include_captions: bool,
        include_music: bool,
        quality: str,
        max_duration: int,
        output_dir: Optional[str],
    ) -> str:
        from moviepy.editor import (
            AudioFileClip, ColorClip, CompositeVideoClip,
            ImageClip, VideoFileClip, concatenate_videoclips,
        )

        resolution     = self.QUALITY_MAP.get(quality, self.QUALITY_MAP["720p"])
        theme_key      = theme_config.get("key", "default")
        captions       = story.get("captions", [])
        image_captions = story.get("image_captions", captions)
        caption_color  = CAPTION_COLORS.get(theme_key, "white")
        image_paths    = inputs.get("image_paths", []) or []
        video_paths    = inputs.get("video_paths", []) or []

        narration_clip: Any = None
        narration_duration  = 0.0
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 500:
            try:
                narration_clip     = _ac(AudioFileClip(audio_path))
                narration_duration = float(narration_clip.duration or 0.0)
                print(f"✓ Narration: {narration_duration:.1f}s")
            except Exception as exc:
                print(f"Could not read narration: {exc}")

        n_sources = max(len(image_paths) + len(video_paths), 1)
        # No upper cap — each image gets an equal share of the full narration so
        # the video always covers the complete story script, however long it is.
        img_dur = max(4.0, narration_duration / n_sources) if narration_duration > 0 else 6.0
        print(f"⏱  Per-image duration: {img_dur:.1f}s ({n_sources} sources, {narration_duration:.1f}s audio)")

        source_clips:  List[Any] = []
        pil_temps_v1:  List[str] = []

        # PIL caption baking — no Arial/TextClip dependency
        for i, img_path in enumerate(image_paths):
            try:
                if not os.path.exists(img_path):
                    continue
                story_cap = captions[i]       if i < len(captions)       else f"Scene {i + 1}"
                img_cap   = image_captions[i] if i < len(image_captions) else story_cap
                if include_captions:
                    baked = _bake_caption_onto_image(
                        img_path, story_cap, img_cap, theme_key,
                        resolution[0], resolution[1],
                    )
                    pil_temps_v1.append(baked)
                    clip: Any = _ac(ImageClip(baked)).set_duration(img_dur)
                else:
                    clip = _ac(ImageClip(img_path)).set_duration(img_dur).resize(resolution)
                source_clips.append(clip)
                print(f"✓ Image {i + 1}: {os.path.basename(img_path)}  |  {img_cap[:55]}")
            except Exception as exc:
                print(f"Could not load image {img_path}: {exc}")

        for i, vid_path in enumerate(video_paths):
            try:
                if not os.path.exists(vid_path):
                    continue
                offset       = len(source_clips)
                vclip: Any   = _ac(VideoFileClip(vid_path)).resize(resolution)
                vdur_v1: float = float(vclip.duration or 0.0)
                if vdur_v1 > 15:
                    vclip = vclip.subclip(0, 15)
                vclip = vclip.set_audio(None)
                story_cap = captions[offset]       if offset < len(captions)       else f"Scene {offset + 1}"
                img_cap   = image_captions[offset] if offset < len(image_captions) else story_cap
                if include_captions:
                    label = f"{img_cap} — {story_cap}" if img_cap != story_cap else story_cap
                    vclip = self._add_caption_v1(vclip, label, caption_color, theme_key)
                source_clips.append(vclip)
                print(f"✓ Video {i + 1}: {os.path.basename(vid_path)}  |  {img_cap[:55]}")
            except Exception as exc:
                print(f"Could not load video {vid_path}: {exc}")

        if not source_clips:
            source_clips = self._create_text_slides_v1(
                story.get("script", ""), theme_config, resolution, captions,
                total_duration=narration_duration
            )
        if not source_clips:
            source_clips = [_ac(ColorClip(resolution, color=(20, 20, 40), duration=6))]

        source_clips   = self._apply_transitions_v1(source_clips)
        final_clip: Any = _ac(concatenate_videoclips(source_clips, method="compose"))

        if narration_clip is not None and narration_duration > 0:
            final_dur_v1: float = float(final_clip.duration or 0.0)
            if narration_duration > final_dur_v1:
                extra           = narration_duration - final_dur_v1
                last_src_v1     = source_clips[-1]
                last_src_v1_dur = float(last_src_v1.duration or 1.0)
                last: Any       = _ac(last_src_v1.to_ImageClip(t=max(0.0, last_src_v1_dur - 0.05))).set_duration(extra)
                if include_captions and captions:
                    last = self._add_caption_v1(last, captions[-1], caption_color, theme_key)
                final_clip = _ac(concatenate_videoclips([final_clip, last], method="compose"))
            elif float(final_clip.duration or 0.0) > narration_duration + 0.5:
                final_clip = final_clip.subclip(0, narration_duration)

        if float(final_clip.duration or 0.0) > max_duration:
            final_clip = final_clip.subclip(0, max_duration)

        if narration_clip is not None:
            try:
                nc: Any        = _ac(narration_clip)
                nc_dur_v1: float   = float(nc.duration or 0.0)
                final_dur_v1b: float = float(final_clip.duration or 0.0)
                if nc_dur_v1 > final_dur_v1b and final_dur_v1b > 0:
                    nc = nc.subclip(0, final_dur_v1b)
                final_clip = final_clip.set_audio(nc)
                print("✓ Narration audio attached.")
            except Exception as exc:
                print(f"Narration attach failed: {exc}")

        if include_music:
            final_clip = self._add_background_music_v1(final_clip, theme_config)

        output_path = self._get_output_path(output_dir, theme_key)
        temp_audio_path = os.path.join(
            os.path.dirname(output_path), f"temp_audio_{int(time.time())}.m4a"
        )
        old_temp = os.path.join(os.path.dirname(output_path), "temp_audio.m4a")
        try:
            if os.path.exists(old_temp):
                os.remove(old_temp)
        except Exception:
            pass

        print(f"🎬 Rendering → {output_path}")
        try:
            final_clip.write_videofile(
                output_path, fps=24, codec="libx264", audio_codec="aac",
                logger=None,
                temp_audiofile=temp_audio_path,
                remove_temp=True,
            )
        finally:
            try:
                final_clip.close()
            except Exception:
                pass
            for p in [temp_audio_path, old_temp]:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            for tf in pil_temps_v1:
                try:
                    if tf and os.path.exists(tf):
                        os.remove(tf)
                except Exception:
                    pass

        print(f"✓ Video saved: {output_path}")
        return output_path

    def _add_caption_v1(self, clip: Any, text: str, color: str, theme_key: str = "default") -> Any:
        """
        v1 caption overlay — uses PIL baking (no Arial/TextClip dependency).
        Same approach as v2: numpy overlay composited over the video clip.
        """
        try:
            from moviepy.editor import ImageClip, CompositeVideoClip
            import numpy as np

            if len(text) > 80:
                text = text[:77] + "…"

            clip_w: int    = int(clip.w or 1280)
            clip_h: int    = int(clip.h or 720)
            clip_dur: float = float(clip.duration or 5.0)

            from PIL import Image as PilImage, ImageDraw as PilDraw

            bar_h     = 72
            bar_img   = PilImage.new("RGBA", (clip_w, bar_h), (0, 0, 0, 0))
            bar_color = CAPTION_BAR_RGBA.get(theme_key, (0, 0, 0, 185))
            txt_color = CAPTION_TEXT_RGB.get(theme_key, (255, 255, 255))
            PilDraw.Draw(bar_img).rectangle([(0, 0), (clip_w, bar_h)], fill=bar_color)

            font = _find_font(26, bold=True)
            draw = PilDraw.Draw(bar_img)
            if font:
                draw.text((14, 14), text, font=font, fill=txt_color + (255,))
            else:
                draw.text((14, 14), text, fill=txt_color + (255,))

            bar_np     = np.array(bar_img.convert("RGBA"))
            overlay_np = np.zeros((clip_h, clip_w, 4), dtype=np.uint8)
            y_start    = clip_h - bar_h
            overlay_np[y_start:y_start + bar_h, :, :] = bar_np

            overlay_clip: Any = _ac(
                ImageClip(overlay_np, ismask=False).set_duration(clip_dur)
            )
            return _ac(CompositeVideoClip([clip, overlay_clip]))

        except Exception as exc:
            print(f"Caption skipped (v1): {exc}")
            return clip

    def _apply_transitions_v1(self, clips: List[Any]) -> List[Any]:
        try:
            from moviepy.video.fx.all import fadein, fadeout
            result = []
            for clip in clips:
                cdur_v1: float = float(clip.duration or 0.0)
                if cdur_v1 > 1.2:
                    clip = fadein(fadeout(clip, 0.5), 0.5)
                result.append(clip)
            return result
        except Exception:
            return clips

    def _create_text_slides_v1(
        self, script: str, theme_config: Dict[str, Any],
        resolution: tuple, captions: List[str],
        total_duration: float = 0.0,
    ) -> List[Any]:
        """Create text slides using PIL-baked frames — no TextClip/Arial dependency."""
        from moviepy.editor import ImageClip, ColorClip
        import numpy as np

        theme_key = theme_config.get("key", "default")
        bg_colors = {
            "default": (245, 240, 230), "adventure": (80, 35, 15),
            "romance":  (60, 15, 35),   "comedy":    (255, 245, 200),
            "mystery":  (15,  8,  30),  "documentary": (20, 40, 30),
        }
        bg_color  = bg_colors.get(theme_key, (245, 240, 230))
        sentences = [s.strip() for s in script.replace("\n", " ").split(". ") if len(s.strip()) > 10]
        if not sentences:
            sentences = [script[:200]] if script else ["Your story begins here."]

        # Distribute full narration duration evenly across ALL sentences.
        n_slides  = len(sentences)
        slide_dur = max(4.0, total_duration / n_slides) if total_duration > 0 else 5.0

        slides = []
        for sentence in sentences:
            slide_np = self._make_text_slide_np(sentence[:160], bg_color, resolution, theme_key)
            try:
                slide: Any = _ac(ImageClip(slide_np).set_duration(slide_dur))
                slides.append(slide)
            except Exception as exc:
                print(f"Text slide failed: {exc}")
                slides.append(_ac(ColorClip(resolution, color=bg_color, duration=slide_dur)))
        return slides

    def _add_background_music_v1(self, clip: Any, theme_config: Dict[str, Any]) -> Any:
        music_key  = theme_config.get("music", "ambient")
        music_path = self._resolve_music_path(music_key)
        if music_path is None:
            return clip
        print(f"🎵 Mixing music: {os.path.basename(music_path)}")
        try:
            from moviepy.audio.fx.all import audio_loop
            from moviepy.editor import AudioFileClip, CompositeAudioClip
            clip_ac: Any  = _ac(clip)
            music: Any    = _ac(AudioFileClip(music_path)).volumex(MUSIC_VOLUME)
            clip_dur      = float(clip_ac.duration or 0.0)
            music_dur     = float(music.duration or 0.0)
            if music_dur < clip_dur:
                music = audio_loop(music, duration=clip_dur)
            else:
                music = music.subclip(0, clip_dur)
            existing: Any = clip_ac.audio
            if existing is not None:
                combined: Any = _ac(CompositeAudioClip([existing, music]))
                return clip_ac.set_audio(combined)
            return clip_ac.set_audio(music)
        except Exception as exc:
            print(f"Background music failed (v1): {exc}")
            return clip

    def _make_text_slide_np(
        self,
        text: str,
        bg_color: tuple,
        resolution: tuple,
        theme_key: str = "default",
    ):
        """
        Create a numpy RGB frame (H, W, 3) with text centered on a background.
        Uses PIL only — no ImageMagick, no Arial dependency.
        """
        import numpy as np
        from PIL import Image as PilImage, ImageDraw as PilDraw

        w, h   = resolution
        txt_color = CAPTION_TEXT_RGB.get(theme_key, (255, 255, 255))

        img  = PilImage.new("RGB", (w, h), color=bg_color)
        draw = PilDraw.Draw(img)

        # Word-wrap
        max_chars = 52
        words     = text.split()
        lines: List[str] = []
        cur = ""
        for word in words:
            if len(cur) + len(word) + 1 <= max_chars:
                cur = (cur + " " + word).strip()
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        wrapped = "\n".join(lines) if lines else text

        font      = _find_font(36, bold=True)
        line_h    = 50
        text_h    = len(lines) * line_h
        y_start   = (h - text_h) // 2

        try:
            if font and hasattr(draw, "multiline_textbbox"):
                bb     = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
                text_w = bb[2] - bb[0]
                x      = max(20, (w - text_w) // 2)
                draw.multiline_text((x, y_start), wrapped, font=font,
                                    fill=txt_color, spacing=8, align="center")
            elif font:
                draw.text((w // 2, h // 2), wrapped, font=font, fill=txt_color)
            else:
                draw.text((40, h // 2 - 20), wrapped, fill=txt_color)
        except Exception:
            draw.text((40, h // 2 - 20), text[:120], fill=txt_color)

        return np.array(img)

    # ─────────────────────────────────────────────────────────────────────────
    # MUSIC PATH RESOLVER
    # ─────────────────────────────────────────────────────────────────────────
    def _resolve_music_path(self, music_key: str) -> Optional[str]:
        filename = MUSIC_FILES.get(music_key)
        if not filename:
            return None

        # Build candidate root directories to search, from most to least specific:
        #   1. Up from __file__ (utils/ → project root)
        #   2. os.getcwd() and its parent  (handles Streamlit CWD variations)
        #   3. Walk up from CWD looking for a "static/music" folder
        this_dir     = os.path.dirname(os.path.abspath(__file__))
        file_root    = os.path.dirname(this_dir)          # utils/ → project root
        cwd          = os.path.abspath(os.getcwd())
        cwd_parent   = os.path.dirname(cwd)

        # Collect all unique "static/music" candidates
        candidate_roots = [file_root, cwd, cwd_parent, this_dir]
        # Also walk up from CWD up to 4 levels to find static/music
        walk = cwd
        for _ in range(4):
            parent = os.path.dirname(walk)
            if parent == walk:
                break
            candidate_roots.append(parent)
            walk = parent

        seen_music_dirs: list = []
        for root in candidate_roots:
            md = os.path.join(root, "static", "music")
            if md not in seen_music_dirs:
                seen_music_dirs.append(md)

        # Name variants: exact, underscores↔spaces
        variants = [filename, filename.replace(" ", "_"), filename.replace("_", " ")]

        # 1. Try exact / near-exact name in every music dir AND the roots themselves
        search_dirs = seen_music_dirs + candidate_roots
        for search_dir in search_dirs:
            for v in variants:
                candidate = os.path.join(search_dir, v)
                if os.path.exists(candidate):
                    print(f"🎵 Music resolved: {candidate}")
                    return candidate

        # 2. Fuzzy stem match inside any existing music dir
        stem = Path(filename).stem.lower().replace("_", " ")
        for music_dir in seen_music_dirs:
            if os.path.isdir(music_dir):
                for f in os.listdir(music_dir):
                    f_norm = f.lower().replace("_", " ")
                    # Match on first 12 chars of stem OR the music_key itself
                    if stem[:12] in f_norm or music_key.replace("_", " ") in f_norm:
                        found = os.path.join(music_dir, f)
                        print(f"🎵 Music fuzzy-matched: {found}")
                        return found

        print(f"⚠️  Music not found for key='{music_key}' ({filename})")
        print(f"   Searched music dirs: {seen_music_dirs}")
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # FFMPEG FALLBACK
    # ─────────────────────────────────────────────────────────────────────────
    def _ffmpeg_fallback(
        self,
        image_paths: List[str],
        audio_path: str,
        output_dir: Optional[str],
        theme_config: Dict[str, Any],
    ) -> str:
        import subprocess
        theme_key   = theme_config.get("key", "story")
        output_path = self._get_output_path(output_dir, theme_key)

        if not image_paths:
            try:
                subprocess.run(
                    ["ffmpeg", "-y",
                     "-f", "lavfi", "-i", "color=c=navy:size=1280x720:duration=10",
                     "-i", audio_path,
                     "-shortest", "-c:v", "libx264", "-c:a", "aac", output_path],
                    capture_output=True, check=True,
                )
                return output_path
            except Exception as exc:
                print(f"ffmpeg fallback: {exc}")
                return audio_path

        try:
            tmpdir = tempfile.mkdtemp()
            for i, src in enumerate(image_paths):
                shutil.copy(src, os.path.join(tmpdir, f"img{i:04d}.jpg"))
            audio_dur = 10.0
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries",
                     "format=duration", "-of",
                     "default=noprint_wrappers=1:nokey=1", audio_path],
                    capture_output=True, text=True,
                )
                audio_dur = float(r.stdout.strip())
            except Exception:
                pass
            per_img = max(4.0, audio_dur / max(len(image_paths), 1))
            subprocess.run(
                ["ffmpeg", "-y",
                 "-framerate", f"1/{per_img:.2f}",
                 "-i", os.path.join(tmpdir, "img%04d.jpg"),
                 "-i", audio_path,
                 "-c:v", "libx264", "-c:a", "aac",
                 "-pix_fmt", "yuv420p", "-shortest", output_path],
                capture_output=True, check=True,
            )
            shutil.rmtree(tmpdir, ignore_errors=True)
            print(f"✓ ffmpeg video: {output_path}")
            return output_path
        except Exception as exc:
            print(f"ffmpeg fallback failed: {exc}")
            return audio_path

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _get_output_path(self, output_dir: Optional[str], theme_key: str) -> str:
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output"
            )
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, f"story_{theme_key}_{int(time.time())}.mp4")