"""
Input Analyzer Module
Detects and classifies input types (text, image, video, mixed)
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any


class InputAnalyzer:
    """Analyzes and preprocesses multimodal inputs."""

    SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    SUPPORTED_VIDEO_TYPES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

    def analyze(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze input data and return structured analysis result.

        Args:
            inputs: Dict with keys: text, images, videos, mode

        Returns:
            Dict with analyzed and preprocessed data
        """
        result = {
            "input_type": "unknown",
            "text": None,
            "image_paths": [],
            "video_paths": [],
            "metadata": {}
        }

        has_text = bool(inputs.get("text"))
        has_images = bool(inputs.get("images"))
        has_videos = bool(inputs.get("videos"))

        # Determine input type
        count = sum([has_text, has_images, has_videos])
        if count > 1:
            result["input_type"] = "mixed"
        elif has_text:
            result["input_type"] = "text"
        elif has_images:
            result["input_type"] = "images"
        elif has_videos:
            result["input_type"] = "videos"

        
        if has_text:
            result["text"] = inputs["text"].strip()

        
        if has_images:
            for uploaded_file in inputs["images"]:
                suffix = Path(uploaded_file.name).suffix.lower()
                if suffix in self.SUPPORTED_IMAGE_TYPES:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    tmp.write(uploaded_file.read())
                    tmp.close()
                    result["image_paths"].append(tmp.name)

        # Save uploaded videos to temp files
        if has_videos:
            for uploaded_file in inputs["videos"]:
                suffix = Path(uploaded_file.name).suffix.lower()
                if suffix in self.SUPPORTED_VIDEO_TYPES:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    tmp.write(uploaded_file.read())
                    tmp.close()
                    result["video_paths"].append(tmp.name)

        # Metadata
        result["metadata"] = {
            "image_count": len(result["image_paths"]),
            "video_count": len(result["video_paths"]),
            "has_text": has_text,
            "text_length": len(result["text"]) if result["text"] else 0
        }

        return result