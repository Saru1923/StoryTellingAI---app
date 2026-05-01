"""
Text-to-Speech (TTS) Engine Module
Supports neural TTS with voice style modulation per theme.
Primary: gTTS (Google TTS) - easy, free, online
Optional: pyttsx3 (offline), edge-tts (Microsoft Neural)
"""

import os
import tempfile
from typing import Dict, Any, Optional


# Voice style settings per theme
VOICE_STYLE_MAP = {
    "neutral": {
        "lang": "en",
        "tld": "com",          # US English
        "slow": False,
        "description": "Standard neutral voice"
    },
    "energetic": {
        "lang": "en",
        "tld": "com.au",       # Australian accent - energetic
        "slow": False,
        "description": "Energetic, dynamic voice for adventure"
    },
    "soft_warm": {
        "lang": "en",
        "tld": "co.uk",        # British - softer tone
        "slow": True,
        "description": "Soft, warm voice for romance"
    },
    "expressive_lively": {
        "lang": "en",
        "tld": "co.in",        # Indian English - expressive
        "slow": False,
        "description": "Expressive, lively voice for comedy"
    },
    "calm_suspenseful": {
        "lang": "en",
        "tld": "co.uk",
        "slow": True,
        "description": "Calm, measured voice for mystery"
    },
    "professional_neutral": {
        "lang": "en",
        "tld": "com",
        "slow": False,
        "description": "Clear, professional voice for documentaries"
    }
}

# Edge TTS voice map (Microsoft Neural - best quality, requires edge-tts)
EDGE_TTS_VOICES = {
    "neutral": "en-US-JennyNeural",
    "energetic": "en-US-DavisNeural",
    "soft_warm": "en-GB-SoniaNeural",
    "expressive_lively": "en-US-AriaNeural",
    "calm_suspenseful": "en-US-GuyNeural",
    "professional_neutral": "en-US-ChristopherNeural"
}


class TTSEngine:
    """
    Multi-backend TTS engine with voice style modulation.
    Tries: gTTS → pyttsx3
    """

    def __init__(self):
        self._backend = None

    def _detect_backend(self) -> str:
        """Detect best available TTS backend."""
        try:
            import gtts
            return "gtts"
        except ImportError:
            pass
        try:
            import pyttsx3
            return "pyttsx3"
        except ImportError:
            pass
        return "silent"  

    def _synthesize_edge_tts(self, text: str, voice: str, output_path: str) -> str:
        """Use Microsoft Edge TTS (best quality, free)."""
        import asyncio
        import edge_tts

        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)

        asyncio.run(_generate())
        return output_path

    def _synthesize_gtts(self, text: str, voice_config: Dict, output_path: str) -> str:
        """Use Google TTS."""
        from gtts import gTTS
        tts = gTTS(
            text=text,
            lang=voice_config.get("lang", "en"),
            tld=voice_config.get("tld", "com"),
            slow=voice_config.get("slow", False)
        )
        tts.save(output_path)
        return output_path

    def _synthesize_pyttsx3(self, text: str, output_path: str) -> str:
        """Use pyttsx3 (offline TTS)."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return output_path

    def _create_silent_audio(self, output_path: str, duration: float = 5.0) -> str:
        """Create silent audio file as last resort fallback."""
        try:
            import numpy as np
            import wave
            import struct
            
            sample_rate = 22050
            num_samples = int(sample_rate * duration)
            
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                data = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
                wav_file.writeframes(data)
            return output_path
        except Exception:
            # Create empty file
            with open(output_path, 'w') as f:
                f.write("")
            return output_path

    def synthesize(
        self,
        text: str,
        voice_style: str = "neutral",
        emotion: str = "neutral",
        output_dir: Optional[str] = None
    ) -> str:
        """
        Synthesize speech from text with voice style modulation.
        
        Args:
            text: Story narration text
            voice_style: Voice style key from VOICE_STYLE_MAP
            emotion: Detected emotion (may further modulate voice)
            output_dir: Directory to save audio file
            
        Returns:
            Path to generated audio file (MP3 or WAV)
        """
        backend = self._detect_backend()
        print(f"TTS Backend: {backend}, Voice Style: {voice_style}")

        # Prepare output path
        ext = ".mp3" if backend in ["edge_tts", "gtts"] else ".wav"
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"narration_{voice_style}{ext}")
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            output_path = tmp.name
            tmp.close()

        # Clean text for TTS
        clean_text = self._clean_text(text)

        try:
            if backend == "gtts":
                voice_config = VOICE_STYLE_MAP.get(voice_style, VOICE_STYLE_MAP["neutral"])
                return self._synthesize_gtts(clean_text, voice_config, output_path)
            
            elif backend == "pyttsx3":
                return self._synthesize_pyttsx3(clean_text, output_path)
            
            else:
                print("No TTS backend available. Creating silent audio.")
                output_path = output_path.replace(".mp3", ".wav")
                return self._create_silent_audio(output_path, duration=10.0)

        except Exception as e:
            print(f"TTS synthesis failed: {e}. Creating silent audio.")
            output_path = output_path.replace(".mp3", ".wav")
            return self._create_silent_audio(output_path, duration=10.0)

    def _clean_text(self, text: str) -> str:
        """Clean text for TTS (remove markdown, special chars)."""
        import re
        # Remove markdown formatting
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        # Remove CAPTIONS section if present
        if "CAPTIONS:" in text:
            text = text.split("CAPTIONS:")[0]
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Limit length (most TTS have character limits)
        return text[:3000]