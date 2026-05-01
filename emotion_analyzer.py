"""
Emotion Analysis Module
Detects emotional tone from story text to guide TTS voice modulation.
"""

from typing import Dict, Any, List


# Emotion keywords mapping
EMOTION_KEYWORDS = {
    "happy": ["joy", "happy", "delight", "laugh", "smile", "bright", "celebrate", "wonderful", "amazing", "cheerful", "fun", "excited"],
    "sad": ["sad", "tears", "grief", "loss", "sorrow", "alone", "lonely", "miss", "regret", "pain", "hurt", "cry"],
    "dramatic": ["suddenly", "gasped", "shocking", "revelation", "dramatic", "intense", "desperate", "crisis", "moment", "powerful"],
    "exciting": ["adventure", "thrilling", "rush", "racing", "danger", "escape", "battle", "victory", "chase", "explosive"],
    "mysterious": ["shadow", "secret", "hidden", "clue", "strange", "whisper", "unknown", "dark", "mysterious", "suspicious"],
    "romantic": ["love", "heart", "embrace", "gentle", "tender", "beautiful", "together", "warmth", "passion", "connection"],
    "calm": ["peaceful", "quiet", "serene", "gentle", "soft", "still", "relaxed", "breathe", "slow", "tranquil"],
    "neutral": []
}

# Theme to expected emotion mapping
THEME_EMOTION_MAP = {
    "adventure": "exciting",
    "romance": "romantic",
    "comedy": "happy",
    "mystery": "mysterious",
    "documentary": "neutral",
    "default": "neutral"
}


class EmotionAnalyzer:
    """
    Analyzes emotional content in text using keyword matching + optional transformer model.
    """

    def __init__(self, use_transformer: bool = False):
        self.use_transformer = use_transformer
        self._classifier = None

    def _load_classifier(self):
        """Load transformer-based emotion classifier."""
        if self._classifier is None:
            try:
                from transformers import pipeline
                self._classifier = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    top_k=None
                )
            except Exception as e:
                print(f"Could not load emotion classifier: {e}")
                self._classifier = None

    def _keyword_analysis(self, text: str) -> Dict[str, float]:
        """Simple keyword-based emotion scoring."""
        text_lower = text.lower()
        scores = {}
        
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if emotion == "neutral":
                continue
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[emotion] = score

        total = sum(scores.values())
        if total == 0:
            return {"neutral": 1.0}
        
        return {k: v / total for k, v in scores.items() if v > 0}

    def _transformer_analysis(self, text: str) -> Dict[str, float]:
        """Transformer-based emotion analysis."""
        self._load_classifier()
        if self._classifier is None:
            return self._keyword_analysis(text)

        try:
            # Use first 512 chars for speed
            results = self._classifier(text[:512])
            if results and isinstance(results[0], list):
                return {r["label"].lower(): r["score"] for r in results[0]}
            return self._keyword_analysis(text)
        except Exception:
            return self._keyword_analysis(text)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotion in text.
        
        Args:
            text: Story script text
            
        Returns:
            Dict with dominant_emotion, scores, voice_rate, pitch
        """
        if self.use_transformer:
            scores = self._transformer_analysis(text)
        else:
            scores = self._keyword_analysis(text)

        if not scores:
            dominant_emotion = "neutral"
            confidence = 1.0
        else:
            dominant_emotion = max(scores, key=scores.get)
            confidence = scores[dominant_emotion]

        # Map emotion to TTS parameters
        tts_params = self._get_tts_params(dominant_emotion)

        return {
            "dominant_emotion": dominant_emotion,
            "confidence": round(confidence, 3),
            "scores": scores,
            "tts_params": tts_params
        }

    def _get_tts_params(self, emotion: str) -> Dict[str, Any]:
        """Get TTS speaking parameters for an emotion."""
        params_map = {
            "happy": {"rate": "+15%", "pitch": "+5Hz", "volume": "+5%"},
            "sad": {"rate": "-20%", "pitch": "-3Hz", "volume": "-5%"},
            "dramatic": {"rate": "-5%", "pitch": "+2Hz", "volume": "+8%"},
            "exciting": {"rate": "+20%", "pitch": "+8Hz", "volume": "+10%"},
            "mysterious": {"rate": "-15%", "pitch": "-5Hz", "volume": "-8%"},
            "romantic": {"rate": "-10%", "pitch": "+3Hz", "volume": "-3%"},
            "calm": {"rate": "-20%", "pitch": "-2Hz", "volume": "-5%"},
            "neutral": {"rate": "0%", "pitch": "0Hz", "volume": "0%"}
        }
        return params_map.get(emotion, params_map["neutral"])