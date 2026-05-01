"""
Theme-Aware Story Generator Module
Uses Groq API (FREE, no credit card) for vision + story generation.
Supports: Default, Adventure, Romance, Comedy, Mystery, Documentary

Models used:
- Vision (images + video frames): meta-llama/llama-4-scout-17b-16e-instruct
- Story generation (text):        llama-3.3-70b-versatile
- Fallback:                       Smart creative templates (no API key needed)

Setup:
    pip install groq
    Get FREE key at: console.groq.com  (no credit card required)

Groq Free Tier limits (resets daily):
    - 14,400 requests/day  on Llama 4 Scout (vision)
    - 14,400 requests/day  on Llama 3.3 70B (story text)
"""

import os
import re
import base64
from dotenv import load_dotenv  # type: ignore
from typing import Any, Dict, List, Optional

load_dotenv()

# ─── GROQ MODELS ──────────────────────────────────────────────────────────────
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_TEXT_MODEL   = "llama-3.3-70b-versatile"

# ─── THEME PROMPT TEMPLATES ───────────────────────────────────────────────────
THEME_PROMPTS: Dict[str, Dict[str, str]] = {
    "default": {
        "system": (
            "You are a skilled, highly creative storyteller who crafts detailed, "
            "emotionally engaging narratives directly inspired by visual scenes. "
            "Every sentence must feel like it was written specifically for the images provided."
        ),
        "style_guide": "Use clear, vivid language. Build real characters with names, emotions, and motivations. Make each scene feel alive and connected.",
        "scene_connector": "As the story unfolded,",
    },
    "adventure": {
        "system": (
            "You are an epic adventure storyteller who crafts thrilling, cinematic tales of "
            "courage, danger, and discovery. Your stories feel like blockbuster films — each "
            "scene is described with urgency, sensory detail, and rising stakes."
        ),
        "style_guide": "Use vivid action verbs, urgent pacing, and dramatic tension. Name your hero. Build danger and discovery from what is literally visible in each image.",
        "scene_connector": "With heart pounding,",
    },
    "romance": {
        "system": (
            "You are a romantic storyteller who crafts heartfelt, emotionally rich tales of "
            "love, longing, and connection. Your stories feel like beloved novels — intimate, "
            "sensory, and deeply human."
        ),
        "style_guide": "Use sensory-rich, emotionally resonant language. Name your characters. Focus on feelings, meaningful looks, small gestures. Each image suggests a chapter of their love story.",
        "scene_connector": "In that tender moment,",
    },
    "comedy": {
        "system": (
            "You are a witty comedian-storyteller who finds rich, absurd humor in everyday "
            "situations. Your stories have comic timing, unexpected twists, and a playful voice "
            "that makes readers laugh out loud."
        ),
        "style_guide": "Use irony, comic exaggeration, and unexpected reversals. Name your characters and give them absurd but believable motivations. Build comedic momentum across every scene.",
        "scene_connector": "And then, predictably but somehow still shocking,",
    },
    "mystery": {
        "system": (
            "You are a masterful mystery writer who builds tension and intrigue from visual "
            "clues. Your stories feel like psychological thrillers — atmospheric, unsettling, "
            "and full of hidden meanings."
        ),
        "style_guide": "Use atmospheric language, hint at hidden truths. Name your detective or protagonist. Every image contains a clue that the reader and character must interpret. Build dread gradually.",
        "scene_connector": "Something was deeply wrong.",
    },
    "documentary": {
        "system": (
            "You are an award-winning documentary narrator in the style of David Attenborough "
            "and Ken Burns — engaging, precise, and deeply informative. You find the profound "
            "story hidden in everyday visual moments."
        ),
        "style_guide": "Use measured, authoritative language. Present observations as fascinating discoveries. Build understanding progressively and end with the larger significance of what was witnessed.",
        "scene_connector": "As careful observation reveals,",
    }
}

# ─── CREATIVE STORY OPENERS PER THEME ────────────────────────────────────────
STORY_OPENERS: Dict[str, List[str]] = {
    "adventure": [
        "Nobody had warned {protagonist} that {scene}. But here they were.",
        "The mission was supposed to be simple. Then {protagonist} saw {scene}, and everything changed.",
        "{scene} — that was the moment {protagonist} knew there was no turning back.",
        "Three things {protagonist} had not expected today: {scene}. And yet.",
    ],
    "romance": [
        "It began, as the best things do, without warning. {scene}, and {protagonist} felt something shift.",
        "{protagonist} had given up believing in this kind of moment. Then came {scene}.",
        "There are days that change everything. For {protagonist}, it started with {scene}.",
        "She had always thought such moments only happened in films. Then {scene}, and she understood.",
    ],
    "comedy": [
        "In hindsight, {protagonist} would admit that {scene} was not the most dignified beginning.",
        "{scene}. This was, {protagonist} would later insist, entirely someone else's fault.",
        "The plan had been perfect. Then {scene}, and 'perfect' took an unexpected holiday.",
        "If anyone had told {protagonist} that {scene} would define their Tuesday, they'd have laughed.",
    ],
    "mystery": [
        "The first clue was {scene}. {protagonist} almost missed it entirely.",
        "{protagonist} had seen a lot of strange things in this city. But {scene} was something else.",
        "It was {scene} that first made {protagonist} suspect the truth was far darker than it appeared.",
        "Twenty years on the force, and {protagonist} had never seen {scene} mean anything good.",
    ],
    "documentary": [
        "What we are witnessing here — {scene} — is rarer than most people realize.",
        "To the untrained eye, {scene} might appear unremarkable. It is anything but.",
        "Researchers have spent decades looking for exactly this: {scene}.",
        "In all recorded observations of this phenomenon, {scene} stands out as extraordinary.",
    ],
    "default": [
        "It started with {scene} — quietly, almost unnoticeably, the way the most important things often do.",
        "{protagonist} had no way of knowing that {scene} would become the moment everything changed.",
        "Some stories announce themselves dramatically. This one began with {scene}.",
        "The day was ordinary until {scene} made it anything but.",
    ],
}

PROTAGONISTS: Dict[str, str] = {
    "adventure":   "Maya",
    "romance":     "Elena",
    "comedy":      "Oliver",
    "mystery":     "Detective Rivers",
    "documentary": "the subject",
    "default":     "Alex",
}


class StoryGenerator:
    """
    Generates long, coherent, image-aware themed narrative scripts.

    Primary:     Groq API (FREE) via GROQ_API_KEY
                 - Vision:  Llama 4 Scout  (image + video frame description)
                 - Story:   Llama 3.3 70B  (themed narrative generation)
    Last resort: Smart creative templates (no API key required)
    """

    def __init__(self, llm_provider: str = "groq") -> None:
        self.llm_provider: str = llm_provider
        self._groq_client: Any = None

    # ─────────────────────────────────────────────────────────────────────────
    # LLM LOADING
    # ─────────────────────────────────────────────────────────────────────────
    def _load_llm(self) -> None:
        """Load Groq client using GROQ_API_KEY from environment."""
        live_key: Optional[str] = os.environ.get("GROQ_API_KEY", "").strip() or None

        if self._groq_client is not None and live_key:
            return

        self._groq_client = None

        if not live_key:
            print("No GROQ_API_KEY found — using smart creative template story generation.")
            print("Get a FREE key at: console.groq.com (no credit card required)")
            return

        try:
            from groq import Groq  # type: ignore[import]
            print(f"Loading Groq client...")
            print(f"  Vision model : {GROQ_VISION_MODEL}")
            print(f"  Story model  : {GROQ_TEXT_MODEL}")
            self._groq_client = Groq(api_key=live_key)
            print("✓ Groq client loaded successfully.")
        except ImportError:
            print("groq package not installed. Run: pip install groq")
        except Exception as e:
            print(f"Groq client load failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # IMAGE DESCRIPTION VIA GROQ VISION (Llama 4 Scout)
    # ─────────────────────────────────────────────────────────────────────────
    def _describe_images_with_groq(
        self, image_paths: List[str], theme: str = "default"
    ) -> List[str]:
        """
        Use Llama 4 Scout on Groq to describe images with theme-specific focus.
        Uses OpenAI-compatible image_url format with base64 data URLs.
        """
        if self._groq_client is None:
            return [f"Image {i+1}: a visual scene" for i in range(len(image_paths))]

        focus_map: Dict[str, str] = {
            "adventure":   "Focus on action, movement, danger, scale of environment, and any sense of journey.",
            "romance":     "Focus on people, facial expressions, physical closeness, warm colors, emotions of longing or love.",
            "comedy":      "Focus on absurd or funny details, awkward situations, and anything unexpectedly silly.",
            "mystery":     "Focus on shadows, partially hidden elements, unusual objects, and anything that feels suspicious.",
            "documentary": "Focus on factual details, setting context, any visible text/signage, and what this scene represents.",
            "default":     "Focus on the main subject, their action, the setting, mood, and the story the image tells.",
        }
        theme_focus = focus_map.get(theme, focus_map["default"])
        prompt_text = (
            f"Describe this image in vivid, concrete detail for a storyteller. {theme_focus} "
            "Be VERY specific: mention actual colors, exact objects, number of people and what they "
            "look like, precise location, lighting, time of day if visible, any text/signs, facial "
            "expressions, body language, and overall mood. "
            "Write 4-5 concrete sentences. Do NOT be vague — say exactly what you see."
        )

        mime_map: Dict[str, str] = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".webp": "image/webp",
            ".gif": "image/gif",  ".bmp":  "image/jpeg",
        }

        descriptions: List[str] = []
        for i, img_path in enumerate(image_paths):
            try:
                with open(img_path, "rb") as f:
                    raw_bytes = f.read()
                b64_data   = base64.b64encode(raw_bytes).decode("utf-8")
                ext        = os.path.splitext(img_path)[1].lower()
                media_type = mime_map.get(ext, "image/jpeg")

                response = self._groq_client.chat.completions.create(
                    model=GROQ_VISION_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{media_type};base64,{b64_data}",
                                    },
                                },
                                {"type": "text", "text": prompt_text},
                            ],
                        }
                    ],
                    max_tokens=500,
                    temperature=0.4,
                )
                desc = response.choices[0].message.content.strip()
                descriptions.append(desc)
                print(f"✓ Image {i+1} described (Groq Llama 4 Vision): {desc[:80]}...")

            except Exception as e:
                print(f"Groq vision failed for image {i+1}: {e}")
                descriptions.append(f"Image {i+1}: a visual scene")

        return descriptions

    # ─────────────────────────────────────────────────────────────────────────
    # TEXT STORY GENERATION VIA GROQ (Llama 3.3 70B)
    # ─────────────────────────────────────────────────────────────────────────
    def _generate_with_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Generate story text using Llama 3.3 70B on Groq."""
        if self._groq_client is None:
            return ""
        try:
            response = self._groq_client.chat.completions.create(
                model=GROQ_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=2000,
                temperature=0.85,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq text generation failed: {e}")
            return ""

    # ─────────────────────────────────────────────────────────────────────────
    # PROMPT BUILDING
    # ─────────────────────────────────────────────────────────────────────────
    def _build_prompt(
        self,
        scene_descriptions: List[str],
        theme: str,
        raw_text: Optional[str] = None,
        image_count: int = 0,
    ) -> str:
        theme_config: Dict[str, str] = THEME_PROMPTS.get(theme, THEME_PROMPTS["default"])
        protagonist  = PROTAGONISTS.get(theme, "Alex")

        scene_text = ""
        for i, desc in enumerate(scene_descriptions, 1):
            scene_text += f"\n--- Scene {i} ---\n{desc}\n"

        context = ""
        if raw_text:
            context = (
                f'\nUser\'s core concept or context:\n"{raw_text}"\n'
                f'Use this to guide the story\'s central premise.\n'
            )

        word_target = max(350, image_count * 130) if image_count > 0 else 350

        return (
            f"You are writing a vivid, immersive {theme} story directly inspired by these visual scenes.\n\n"
            f"{context}\n"
            f"Visual Scenes (describe EXACTLY what is in each image):\n{scene_text}\n\n"
            f"Story Style: {theme_config['style_guide']}\n"
            f"Protagonist name (use this): {protagonist}\n\n"
            f"STRICT REQUIREMENTS:\n"
            f"- Write {word_target}-{word_target + 200} words\n"
            f"- EVERY scene must be clearly reflected in the story\n"
            f"- Make the story flow cinematically from scene to scene\n"
            f"- Give {protagonist} a clear goal, obstacle, and emotional arc\n"
            f"- Use sensory details pulled from the visual descriptions above\n"
            f"- Create a satisfying beginning, escalating middle, and resonant ending\n"
            f"- Write ONLY the story — no headings, no meta-commentary\n\n"
            f"After the story, write exactly:\n"
            f"CAPTIONS:\n"
            f"Then one punchy caption per scene (max 8 words, present tense), numbered:\n"
            f"1. [scene 1 caption]\n"
            f"2. [scene 2 caption]\n\n"
            f"Begin the story now:"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SMART CREATIVE TEMPLATE (fallback — no API key required)
    # ─────────────────────────────────────────────────────────────────────────
    def _smart_template_story(
        self,
        scene_descriptions: List[str],
        theme: str,
        raw_text: Optional[str] = None,
    ) -> str:
        protagonist = PROTAGONISTS.get(theme, "Alex")
        connector   = THEME_PROMPTS.get(theme, THEME_PROMPTS["default"])["scene_connector"]
        openers     = STORY_OPENERS.get(theme, STORY_OPENERS["default"])

        clean_scenes: List[str] = []
        for desc in scene_descriptions:
            cleaned = desc
            for prefix in ["Text: ", "Image: ", "Video: "]:
                if desc.startswith(prefix):
                    cleaned = desc[len(prefix):]
                    break
            clean_scenes.append(cleaned.strip().rstrip(".").lower())

        story_parts: List[str] = []
        for i, (desc, clean) in enumerate(zip(scene_descriptions, clean_scenes)):
            scene_sentence = self._extract_scene_sentence(desc, clean)
            short_name = protagonist.split()[0] if ' ' in protagonist else protagonist

            if i == 0:
                opener = openers[i % len(openers)].format(
                    protagonist=protagonist, scene=scene_sentence
                )
                story_parts.append(
                    f"{opener} {short_name} stood before {scene_sentence}, "
                    f"mind racing with what it meant. "
                    f"This was not at all how the day was supposed to go."
                )
            elif i == len(scene_descriptions) - 1:
                story_parts.append(
                    f"And then, at last, came {scene_sentence}. "
                    f"{short_name} understood now why every step of this journey had been necessary. "
                    f"The world looked different from here — sharper, realer, more worth the struggle. "
                    f"Some things, once truly seen, cannot be unseen. This was one of them."
                )
            else:
                story_parts.append(
                    f"{connector} {scene_sentence} changed everything again. "
                    f"{short_name} paused, taking it in — the colors, the weight of the moment, "
                    f"the strange feeling that this had been waiting for them all along. "
                    f"There was no going back now, only forward."
                )

        if raw_text:
            insert = (
                f" The whole thing had started because of one simple truth: "
                f"{raw_text.strip().rstrip('.')}. "
                f"Everything since had been a consequence of that."
            )
            story_parts.insert(1, insert) if len(story_parts) > 1 else story_parts.append(insert)

        captions_text = "\nCAPTIONS:\n"
        for i, clean in enumerate(clean_scenes, 1):
            caption = " ".join(clean.split()[:8]).rstrip(",").rstrip(".")
            captions_text += f"{i}. {caption.capitalize()}\n"

        return " ".join(story_parts) + captions_text

    def _extract_scene_sentence(self, full_desc: str, clean: str) -> str:
        if len(full_desc) > 80 and not full_desc.startswith(("Image ", "Video ", "Text ")):
            first = full_desc.split(".")[0].strip()
            if len(first.split()) > 4:
                return " ".join(first.split()[:14]).lower().rstrip(",")
        words = clean.split()
        return " ".join(words[:12]) if len(words) > 12 else (clean or "the scene before them")

    # ─────────────────────────────────────────────────────────────────────────
    # OUTPUT PARSING
    # ─────────────────────────────────────────────────────────────────────────
    def _parse_llm_output(self, raw_output: str, scene_count: int) -> Dict[str, Any]:
        script: str       = raw_output
        captions: List[str] = []

        if "CAPTIONS:" in raw_output:
            parts   = raw_output.split("CAPTIONS:")
            script  = parts[0].strip()
            cap_txt = parts[1].strip() if len(parts) > 1 else ""
            for line in cap_txt.split("\n"):
                line = line.strip()
                if line:
                    caption = re.sub(r'^[\d]+[.):\-\s]+', '', line).strip()
                    if caption and len(caption) > 2:
                        captions.append(caption)

        for kw in ["Style Guide:", "Requirements:", "Core concept:", "INSTRUCTIONS:", "STRICT REQUIREMENTS:"]:
            if kw in script:
                script = script.split(kw)[0].strip()

        while len(captions) < scene_count:
            captions.append(f"Scene {len(captions) + 1}")

        return {
            "script":   script[:4500] if script.strip() else "Story generation in progress.",
            "captions": captions[:scene_count],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # VIDEO FRAME DESCRIPTION (3-frame sampling → Groq Vision)
    # ─────────────────────────────────────────────────────────────────────────
    def _describe_video_with_vision(self, video_path: str, theme: str = "default") -> str:
        """
        Extracts 3 evenly-spaced frames (25%, 50%, 75%) from the video,
        describes each with Groq Vision (Llama 4 Scout), then combines
        them into a single coherent scene description for story generation.
        """
        try:
            import cv2      # type: ignore
            import tempfile

            cap   = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 0:
                cap.release()
                return "A video scene"

            sample_positions = [total // 4, total // 2, (total * 3) // 4]
            frame_paths: List[str] = []

            for pos in sample_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ret, frame = cap.read()
                if not ret:
                    continue
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                cv2.imwrite(tmp.name, frame)
                tmp.close()
                frame_paths.append(tmp.name)

            cap.release()

            if not frame_paths:
                return "A dynamic video scene with rich visual content"

            # Describe all sampled frames via Groq Vision
            frame_descs: List[str] = []
            if self._groq_client is not None:
                frame_descs = self._describe_images_with_groq(frame_paths, theme=theme)
            else:
                frame_descs = ["A video frame scene"] * len(frame_paths)

            # Clean up temp frame files
            for fp in frame_paths:
                try:
                    os.remove(fp)
                except Exception:
                    pass

            # Combine descriptions into one cohesive video scene summary
            if not frame_descs:
                return "A dynamic video scene with rich visual content"
            if len(frame_descs) == 1:
                return frame_descs[0]

            combined = (
                f"Opening: {frame_descs[0]}  "
                f"Middle: {frame_descs[1] if len(frame_descs) > 1 else ''}  "
                f"End: {frame_descs[-1]}"
            )
            return combined[:800]

        except Exception as e:
            print(f"Video frame description failed: {e}")
            return "A video scene with movement and action"

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN GENERATE
    # ─────────────────────────────────────────────────────────────────────────
    def generate(
        self,
        embeddings_result: Dict[str, Any],
        theme: str = "default",
        theme_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full pipeline:
        1. Describe images   via Groq Vision (Llama 4 Scout)
        2. Describe videos   via Groq Vision (3-frame sampling)
        3. Generate story    via Groq (Llama 3.3 70B)
           → smart template fallback if no key
        """
        self._load_llm()

        descriptions: List[str]     = list(embeddings_result.get("descriptions", []))
        raw_text:     Optional[str] = embeddings_result.get("raw_text")
        image_paths:  List[str]     = embeddings_result.get("image_paths", [])
        video_paths:  List[str]     = embeddings_result.get("video_paths", [])
        scene_count:  int           = max(len(descriptions), 1)

        visual_descs: Optional[List[str]] = None

        # ── Step 1a: Images → Groq Vision ─────────────────────────
        if image_paths and self._groq_client is not None:
            print(f"Using Groq Vision (Llama 4 Scout) for {len(image_paths)} images...")
            visual_descs = self._describe_images_with_groq(image_paths, theme=theme)
            if visual_descs:
                new_descs: List[str] = []
                img_idx = 0
                for desc in descriptions:
                    if desc.startswith("Image: ") and img_idx < len(visual_descs):
                        new_descs.append(visual_descs[img_idx])
                        img_idx += 1
                    else:
                        new_descs.append(desc)
                descriptions = new_descs

        # ── Step 1b: Videos → Groq Vision (3-frame sampling) ──────
        video_descs: List[str] = []
        if video_paths:
            for vid_path in video_paths:
                print(f"Analysing video: {os.path.basename(vid_path)} (3-frame sampling)...")
                video_descs.append(self._describe_video_with_vision(vid_path, theme=theme))
            vid_idx = 0
            new_descs2: List[str] = []
            for desc in descriptions:
                if desc.startswith("Video: ") and vid_idx < len(video_descs):
                    new_descs2.append(video_descs[vid_idx])
                    vid_idx += 1
                else:
                    new_descs2.append(desc)
            descriptions = new_descs2

        if not descriptions and raw_text:
            descriptions = [raw_text]

        # ── Step 2: Build prompt ───────────────────────────────────
        prompt       = self._build_prompt(descriptions, theme, raw_text, image_count=len(image_paths))
        theme_system = THEME_PROMPTS.get(theme, THEME_PROMPTS["default"])["system"]

        # ── Step 3: Generate story via Groq ───────────────────────
        raw_story: str = ""
        if self._groq_client is not None:
            print(f"Generating story via Groq ({GROQ_TEXT_MODEL})...")
            raw_story = self._generate_with_groq(theme_system, prompt)
            if raw_story:
                print(f"✓ Story via Groq ({GROQ_TEXT_MODEL}): {len(raw_story)} chars")

        if not raw_story:
            print("Using smart creative template story generation...")
            raw_story = self._smart_template_story(descriptions, theme, raw_text)

        parsed = self._parse_llm_output(raw_story, scene_count)

        image_content_captions: List[str] = []
        all_visual = (visual_descs or []) + video_descs
        for vd in all_visual:
            first = vd.split(".")[0].strip()
            words = first.split()[:10]
            short = " ".join(words) + ("..." if len(first.split()) > 10 else "")
            image_content_captions.append(short)

        while len(image_content_captions) < scene_count:
            idx = len(image_content_captions)
            image_content_captions.append(
                parsed["captions"][idx] if idx < len(parsed["captions"]) else f"Scene {idx + 1}"
            )

        return {
            "script":              parsed["script"],
            "captions":            parsed["captions"],
            "image_captions":      image_content_captions,
            "scene_descriptions":  descriptions,
            "vision_descriptions": all_visual,
            "scene_count":         scene_count,
            "theme":               theme,
            "prompt_used":         prompt[:500],
        }