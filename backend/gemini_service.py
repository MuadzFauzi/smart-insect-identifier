"""
gemini_service.py
Bertanggung jawab atas:
  - Integrasi Google Gemini 2.5 falsh
  - ThinkingConfig (extended thinking)
  - Opsional: GoogleSearch grounding
  - Fallback graceful jika API error / 503
"""

import logging
import os
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

logger = logging.getLogger(__name__)

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
GEMINI_MODEL   = "gemini-2.5-flash"
MAX_TOKENS     = 4096


class GeminiService:
    """
    Service untuk query Gemini API dengan:
      - GoogleSearch grounding (opsional, aktifkan via USE_GOOGLE_SEARCH=true di .env)
      - Fallback: jika 503/rate limit → return None, bukan crash
    """

    def __init__(self):
        self._client       = None
        self._model        = None
        self._use_search   = os.getenv("USE_GOOGLE_SEARCH", "false").lower() == "true"
        self._initialized  = False

    # ── Init ─────────────────────────────────────────────────────────────────
    def initialize(self) -> None:
        """Konfigurasi Gemini client. Dipanggil sekali saat startup FastAPI."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning(
                "GEMINI_API_KEY tidak ditemukan di environment. "
                "Gemini integration dinonaktifkan."
            )
            return

        try:
            genai.configure(api_key=api_key)

            # Safety settings — relaxed untuk konten edukatif serangga
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT:        HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH:       HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }

            # Tools: GoogleSearch grounding (aktif jika USE_GOOGLE_SEARCH=true)
            tools = []
            if self._use_search:
                tools.append({"google_search": {}})
                logger.info("GoogleSearch grounding: AKTIF")
            else:
                logger.info("GoogleSearch grounding: NONAKTIF (set USE_GOOGLE_SEARCH=true untuk mengaktifkan)")

            self._model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                safety_settings=safety_settings,
                tools=tools if tools else None,
            )

            self._initialized = True
            logger.info(f"Gemini service siap | Model: {GEMINI_MODEL}")

        except Exception as e:
            logger.error(f"Gagal inisialisasi Gemini: {e}")

    # ── Query ────────────────────────────────────────────────────────────────
    def get_insect_info(
        self,
        predicted_class:  str,
        confidence:        float,
        top_predictions:  list[dict],
    ) -> Optional[str]:
        """
        Kirim query ke Gemini tentang serangga hasil prediksi ML.

        Returns:
            str berisi Markdown response dari Gemini,
            atau None jika API tidak tersedia (trigger fallback di main.py).
        """
        if not self._initialized or self._model is None:
            logger.warning("Gemini belum diinisialisasi, skip query.")
            return None

        prompt = self._build_prompt(predicted_class, confidence, top_predictions)

        try:
            # Gunakan objek GenerationConfig standar bawaan SDK Google
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=MAX_TOKENS,
                temperature=0.3,   # Diturunkan ke 0.3 agar jawaban entomologis lebih konsisten dan faktual
            )

            # Panggil model secara bersih tanpa parameter tambahan yang memicu crash
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            # Ekstrak teks dari response
            result_text = self._extract_text(response)
            return result_text

        except (ResourceExhausted, ServiceUnavailable) as e:
            # 503 / Rate limit — fallback graceful
            logger.warning(f"Gemini API tidak tersedia (503/rate limit): {e}")
            return None

        except Exception as e:
            logger.error(f"Error tak terduga saat query Gemini: {e}")
            return None

    # ── Helper ───────────────────────────────────────────────────────────────
    def _build_prompt(
        self,
        predicted_class: str,
        confidence:       float,
        top_predictions: list[dict],
    ) -> str:
        """Bangun prompt yang informatif untuk Gemini."""
        top_list = "\n".join(
            f"  {i+1}. {p['class']} ({p['confidence']*100:.1f}%)"
            for i, p in enumerate(top_predictions[:5])
        )
        confidence_pct = f"{confidence * 100:.1f}%"

        return f"""Kamu adalah seorang entomologis (ahli serangga) yang ramah dan informatif.

Model Machine Learning telah mengidentifikasi serangga dalam gambar sebagai berikut:
- **Prediksi Utama:** {predicted_class} (kepercayaan: {confidence_pct})
- **Top Prediksi:**
{top_list}

Berikan informasi komprehensif namun padat tentang **{predicted_class}** dalam format Markdown yang rapi, mencakup:

## 🦋 {predicted_class}

### Klasifikasi Ilmiah
(nama ilmiah, ordo, famili)

### Ciri-ciri Utama
(penampilan fisik yang membedakan)

### Habitat & Distribusi
(di mana ditemukan, termasuk Indonesia jika relevan)

### Peran Ekologis
(manfaat/dampak terhadap ekosistem)

### Fakta Menarik
(2-3 fakta unik yang jarang diketahui)

---
*Catatan: Identifikasi dilakukan oleh model AI dengan tingkat kepercayaan {confidence_pct}. Untuk keperluan ilmiah, konfirmasi dari ahli entomologi disarankan.*

Jawab dalam Bahasa Indonesia yang mudah dipahami."""

    @staticmethod
    def _extract_text(response) -> Optional[str]:
        """Ekstrak teks dari GenerateContentResponse, skip thinking blocks."""
        try:
            # Coba akses via .text langsung (paling simple)
            if hasattr(response, "text") and response.text:
                return response.text
            # Fallback: iterasi candidates → parts
            for candidate in response.candidates:
                text_parts = [
                    part.text
                    for part in candidate.content.parts
                    if hasattr(part, "text") and part.text
                ]
                if text_parts:
                    return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Gagal ekstrak teks dari Gemini response: {e}")
        return None

    @property
    def is_available(self) -> bool:
        return self._initialized and self._model is not None


# Singleton instance — diimport oleh main.py
gemini_service = GeminiService()
