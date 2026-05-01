"""
Feature Extraction Module
Extracts semantic embeddings from text, images, and video frames.
Uses CLIP for vision and sentence-transformers for text.

Fix: All embeddings are padded/projected to 512-dim before clustering
     so mixed text(384) + image(512) inputs don't crash GMM.
"""

import os
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

# Target unified embedding dimension for clustering
UNIFIED_DIM = 512


class FeatureExtractor:
    """
    Extracts semantic feature embeddings from multimodal inputs.

    Models used:
    - Vision: openai/clip-vit-base-patch32  → 512-dim
    - Text:   sentence-transformers/all-MiniLM-L6-v2 → 384-dim (padded to 512)
    """

    def __init__(self) -> None:
        self._clip_model: Any = None
        self._clip_processor: Any = None
        self._text_model: Any = None

    def _load_clip(self) -> None:
        """Lazy-load CLIP model."""
        if self._clip_model is not None:
            return
        try:
            from transformers import CLIPProcessor, CLIPModel  # type: ignore
            print("Loading CLIP model...")
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        except ImportError:
            print("transformers not installed. Using mock embeddings.")
        except Exception as e:
            print(f"CLIP model load failed: {e}. Using mock embeddings.")

    def _load_text_model(self) -> None:
        """Lazy-load sentence transformer."""
        if self._text_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            print("Loading sentence transformer...")
            self._text_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            print("sentence-transformers not installed. Using mock embeddings.")
        except Exception as e:
            print(f"Text model load failed: {e}. Using mock embeddings.")

    def _tensor_to_numpy(self, tensor: Any) -> np.ndarray:
        """Safely convert PyTorch tensor to numpy (PyTorch 2.x compatible)."""
        try:
            arr: np.ndarray = tensor.squeeze().detach().cpu().numpy()
            return arr
        except Exception:
            try:
                arr2: np.ndarray = tensor.squeeze().numpy()
                return arr2
            except Exception:
                return np.random.rand(512).astype(np.float32)

    def _normalize_to_unified_dim(self, embedding: np.ndarray) -> np.ndarray:
        """
        Pad or truncate any embedding to UNIFIED_DIM (512).
        ✅ Fixes: text(384-dim) + image(512-dim) shape mismatch in GMM clustering.
        """
        current_dim = embedding.shape[0]
        if current_dim == UNIFIED_DIM:
            return embedding
        elif current_dim < UNIFIED_DIM:
            # Zero-pad to 512
            padded = np.zeros(UNIFIED_DIM, dtype=np.float32)
            padded[:current_dim] = embedding
            return padded
        else:
            # Truncate to 512
            return embedding[:UNIFIED_DIM]

    def extract_image_embedding(self, image_path: str) -> np.ndarray:
        """Extract 512-dim CLIP embedding from an image file."""
        self._load_clip()

        if self._clip_model is None or self._clip_processor is None:
            return np.random.rand(512).astype(np.float32)

        try:
            import torch  # type: ignore
            from PIL import Image  # type: ignore

            image = Image.open(image_path).convert("RGB")
            inputs: Dict[str, Any] = self._clip_processor(
                images=image,
                return_tensors="pt"
            )
            with torch.no_grad():
                features: Any = self._clip_model.get_image_features(**inputs)

            return self._tensor_to_numpy(features)

        except Exception as e:
            print(f"Image embedding failed for '{image_path}': {e}")
            return np.random.rand(512).astype(np.float32)

    def extract_video_embedding(
        self, video_path: str, num_frames: int = 8
    ) -> np.ndarray:
        """Extract mean 512-dim CLIP embedding from uniformly sampled video frames."""
        self._load_clip()

        try:
            import cv2  # type: ignore
            import torch  # type: ignore
            from PIL import Image  # type: ignore

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                cap.release()
                return np.random.rand(512).astype(np.float32)

            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
            frame_embeddings: List[np.ndarray] = []

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if not ret:
                    continue

                pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if self._clip_model is not None and self._clip_processor is not None:
                    inputs: Dict[str, Any] = self._clip_processor(
                        images=pil_image,
                        return_tensors="pt"
                    )
                    with torch.no_grad():
                        feat: Any = self._clip_model.get_image_features(**inputs)
                    frame_embeddings.append(self._tensor_to_numpy(feat))
                else:
                    frame_embeddings.append(np.random.rand(512).astype(np.float32))

            cap.release()

            if frame_embeddings:
                result: np.ndarray = np.mean(np.stack(frame_embeddings, axis=0), axis=0)
                return result

            return np.random.rand(512).astype(np.float32)

        except Exception as e:
            print(f"Video embedding failed for '{video_path}': {e}")
            return np.random.rand(512).astype(np.float32)

    def extract_text_embedding(self, text: str) -> np.ndarray:
        """Extract 384-dim sentence-transformer embedding from text."""
        self._load_text_model()

        if self._text_model is None:
            return np.random.rand(384).astype(np.float32)

        try:
            result: np.ndarray = self._text_model.encode(text)
            return result
        except Exception as e:
            print(f"Text embedding failed: {e}")
            return np.random.rand(384).astype(np.float32)

    def cluster_embeddings(
        self,
        embeddings: List[np.ndarray],
        n_components: int = 3
    ) -> List[int]:
        """
        Cluster embeddings using Gaussian Mixture Model (GMM).
        ✅ All embeddings normalized to UNIFIED_DIM (512) before stacking
           to handle mixed text(384) + image/video(512) inputs.
        """
        if len(embeddings) <= 1:
            return [0] * len(embeddings)

        try:
            from sklearn.mixture import GaussianMixture  # type: ignore

            # ✅ Key fix: unify dimensions before stacking
            unified = [self._normalize_to_unified_dim(e) for e in embeddings]

            emb_matrix = np.stack([e / (np.linalg.norm(e) + 1e-8) for e in unified],axis=0)
            n_clusters = min(n_components, len(embeddings))
            gmm = GaussianMixture(n_components=n_clusters, random_state=42)
            labels: np.ndarray = gmm.fit_predict(emb_matrix)
            return labels.tolist()

        except Exception as e:
            print(f"Clustering failed: {e}. Using sequential labels.")
            return list(range(len(embeddings)))

    def extract(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction pipeline.
        Returns embeddings, descriptions, cluster labels, and metadata.
        """
        embeddings: List[np.ndarray] = []
        descriptions: List[str] = []

        # ── Text embedding ───────────────────────────────────────
        raw_text: Optional[str] = analysis_result.get("text")
        if raw_text:
            text_emb = self.extract_text_embedding(raw_text)
            embeddings.append(text_emb)
            descriptions.append(f"Text: {raw_text[:100]}")

        # ── Image embeddings ─────────────────────────────────────
        for img_path in analysis_result.get("image_paths", []):
            img_emb = self.extract_image_embedding(img_path)
            embeddings.append(img_emb)
            descriptions.append(f"Image: {Path(img_path).name}")

        # ── Video embeddings ─────────────────────────────────────
        for vid_path in analysis_result.get("video_paths", []):
            vid_emb = self.extract_video_embedding(vid_path)
            embeddings.append(vid_emb)
            descriptions.append(f"Video: {Path(vid_path).name}")

        # ── GMM Clustering ───────────────────────────────────────
        cluster_labels = self.cluster_embeddings(embeddings) if embeddings else []

        return {
            "embeddings": embeddings,
            "descriptions": descriptions,
            "cluster_labels": cluster_labels,
            "scene_count": len(embeddings),
            "input_type": analysis_result.get("input_type", "text"),
            "raw_text": raw_text,
            "image_paths": analysis_result.get("image_paths", []),
            "video_paths": analysis_result.get("video_paths", []),
        }