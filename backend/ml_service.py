"""
ml_service.py
Bertanggung jawab atas:
  - Load model EfficientNet-B3 dari artifacts/
  - Preprocessing gambar (sesuai pipeline training)
  - Inference & return top-N prediksi + probabilitas
"""

import json
import logging
from pathlib import Path
from typing import Optional

import torch
import torch.nn.functional as F
from torchvision import transforms
from torchvision.models import efficientnet_b3, EfficientNet_B3_Weights
from PIL import Image
import io

logger = logging.getLogger(__name__)

# ─── Path Artifacts ──────────────────────────────────────────────────────────
ARTIFACTS_DIR   = Path(__file__).parent / "artifacts"
MODEL_PATH      = ARTIFACTS_DIR / "insect_classifier_traced.pt"
FALLBACK_PATH   = ARTIFACTS_DIR / "insect_classifier.pth"
METADATA_PATH   = ARTIFACTS_DIR / "model_metadata.json"


class MLService:
    """
    Singleton-style service untuk load model sekali dan reuse di tiap request.
    Urutan load:
      1. TorchScript traced (.pt)  — lebih cepat, tidak butuh definisi class
      2. state_dict (.pth)         — fallback jika traced tidak ada
    """

    def __init__(self):
        self.model      = None
        self.metadata   = None
        self.transform  = None
        self.device     = torch.device("cpu")   # Backend pakai CPU (sesuai FAQ modul)
        self._loaded    = False

    # ── Load ─────────────────────────────────────────────────────────────────
    def load(self) -> None:
        """Load model + metadata dari artifacts/. Dipanggil sekali saat startup."""
        if self._loaded:
            return

        # 1. Baca metadata
        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                f"model_metadata.json tidak ditemukan di {METADATA_PATH}. "
                "Salin hasil training ke backend/artifacts/ terlebih dahulu."
            )
        with open(METADATA_PATH, "r") as f:
            self.metadata = json.load(f)

        img_size = self.metadata["img_size"]           # e.g. 300
        mean     = self.metadata["imagenet_mean"]      # [0.485, 0.456, 0.406]
        std      = self.metadata["imagenet_std"]       # [0.229, 0.224, 0.225]

        # 2. Load model (TorchScript → fallback state_dict)
        if MODEL_PATH.exists():
            logger.info(f"Memuat TorchScript model dari {MODEL_PATH}")
            self.model = torch.jit.load(str(MODEL_PATH), map_location=self.device)
        elif FALLBACK_PATH.exists():
            logger.info(f"TorchScript tidak ada, memuat state_dict dari {FALLBACK_PATH}")
            self.model = self._build_model_from_state_dict(FALLBACK_PATH)
        else:
            raise FileNotFoundError(
                f"File model tidak ditemukan. "
                f"Pastikan '{MODEL_PATH.name}' atau '{FALLBACK_PATH.name}' ada di artifacts/."
            )

        self.model.to(self.device)
        self.model.eval()

        # 3. Transform (sama persis dengan eval_transforms saat training)
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])

        self._loaded = True
        logger.info(
            f"Model siap | Kelas: {self.metadata['num_classes']} | "
            f"Device: {self.device} | Acc training: {self.metadata.get('test_accuracy', 'N/A'):.4f}"
        )

    def _build_model_from_state_dict(self, pth_path: Path) -> torch.nn.Module:
        """Rebuild arsitektur EfficientNet-B3 lalu load bobot dari .pth."""
        import torch.nn as nn

        num_classes = self.metadata["num_classes"]

        # Bangun arsitektur yang SAMA dengan notebook training
        model = efficientnet_b3(weights=None)   # tidak perlu download ulang ImageNet weights
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.4, inplace=True),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
            nn.Linear(512, num_classes),
        )

        checkpoint = torch.load(str(pth_path), map_location=self.device)
        # Support dua format: bare state_dict atau dict dengan key 'model_state_dict'
        state_dict = (
            checkpoint["model_state_dict"]
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint
            else checkpoint
        )
        model.load_state_dict(state_dict)
        return model

    # ── Inference ────────────────────────────────────────────────────────────
    def predict(self, image_bytes: bytes, top_k: int = 5) -> dict:
        """
        Terima raw bytes gambar → return dict hasil prediksi.

        Returns:
            {
                "predicted_class": "butterfly",
                "confidence": 0.923,
                "top_predictions": [
                    {"class": "butterfly", "confidence": 0.923},
                    ...
                ]
            }
        """
        if not self._loaded:
            raise RuntimeError("Model belum di-load. Panggil load() terlebih dahulu.")

        # Decode bytes → PIL Image
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Gagal membaca gambar: {e}")

        # Preprocess
        tensor = self.transform(image).unsqueeze(0).to(self.device)  # (1, C, H, W)

        # Inference
        with torch.no_grad():
            logits = self.model(tensor)                       # (1, num_classes)
            probs  = F.softmax(logits, dim=1)[0]              # (num_classes,)

        # Top-K
        k           = min(top_k, len(self.metadata["class_names"]))
        top_probs, top_idx = probs.topk(k)
        class_names = self.metadata["class_names"]

        top_predictions = [
            {
                "class":      class_names[idx.item()],
                "confidence": round(prob.item(), 6),
            }
            for idx, prob in zip(top_idx, top_probs)
        ]

        return {
            "predicted_class": top_predictions[0]["class"],
            "confidence":      top_predictions[0]["confidence"],
            "top_predictions": top_predictions,
        }

    # ── Health ────────────────────────────────────────────────────────────────
    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_model_info(self) -> Optional[dict]:
        """Return informasi model untuk endpoint /health."""
        if not self._loaded or self.metadata is None:
            return None
        return {
            "architecture": self.metadata.get("architecture", "efficientnet_b3"),
            "num_classes":  self.metadata["num_classes"],
            "img_size":     self.metadata["img_size"],
            "test_accuracy": self.metadata.get("test_accuracy"),
        }


# Singleton instance — diimport oleh main.py
ml_service = MLService()
