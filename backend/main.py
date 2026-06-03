"""
main.py
Entry point FastAPI backend — Smart Insect Identifier.

Endpoints:
  GET  /          → root info
  GET  /health    → status model & gemini
  POST /predict   → upload gambar → prediksi ML + info Gemini

Jalankan:
  uvicorn main:app --reload
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from ml_service import ml_service
from gemini_service import gemini_service

# ─── Setup ───────────────────────────────────────────────────────────────────
load_dotenv()   # Baca .env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Tipe file gambar yang diterima
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/bmp", "image/webp",
}
MAX_FILE_SIZE_MB = 10


# ─── Lifespan (startup & shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model dan inisialisasi Gemini saat server startup."""
    logger.info("=== Server starting up ===")
    try:
        ml_service.load()
        logger.info("✓ ML model loaded")
    except Exception as e:
        logger.error(f"✗ Gagal load ML model: {e}")
        # Server tetap jalan, tapi /predict akan return 503

    try:
        gemini_service.initialize()
        logger.info("✓ Gemini service initialized")
    except Exception as e:
        logger.warning(f"✗ Gemini tidak tersedia: {e}")
        # Fallback mode — prediksi ML tetap jalan

    yield  # Server aktif di sini

    logger.info("=== Server shutting down ===")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Insect Identifier API",
    description="Klasifikasi serangga menggunakan EfficientNet-B3 + Google Gemini 2.5 Flash Lite",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — izinkan frontend (Next.js dev server) mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js dev
        "http://localhost:5173",    # Vite dev (jika pakai Vite)
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Response Schemas ─────────────────────────────────────────────────────────
class PredictionItem(BaseModel):
    class_name:  str
    confidence:  float


class PredictResponse(BaseModel):
    predicted_class:  str
    confidence:        float
    top_predictions:  list[PredictionItem]
    gemini_info:      str | None   # None jika API sedang tidak tersedia
    gemini_available: bool


class HealthResponse(BaseModel):
    status:         str
    model_loaded:   bool
    gemini_ready:   bool
    model_info:     dict | None

    model_config = {
        "protected_namespaces": ()
    }


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Smart Insect Identifier API",
        "docs":    "/docs",
        "health":  "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Cek status model ML dan Gemini."""
    return HealthResponse(
        status       = "ok" if ml_service.is_loaded else "model_not_loaded",
        model_loaded = ml_service.is_loaded,
        gemini_ready = gemini_service.is_available,
        model_info   = ml_service.get_model_info(),
    )


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict(file: UploadFile = File(...)):
    """
    Upload gambar serangga → dapat prediksi kelas + info dari Gemini.

    - **file**: file gambar (JPEG, PNG, BMP, WebP), maks 10 MB
    """
    # ── Validasi file ─────────────────────────────────────────────────────
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Tipe file tidak didukung: {file.content_type}. "
                   f"Gunakan: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()

    if len(image_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File terlalu besar. Maksimum {MAX_FILE_SIZE_MB} MB.",
        )

    # ── ML Inference ──────────────────────────────────────────────────────
    if not ml_service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model ML belum tersedia. Cek artifacts/ dan restart server.",
        )

    try:
        ml_result = ml_service.predict(image_bytes, top_k=5)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Gambar tidak valid: {e}")
    except Exception as e:
        logger.error(f"Error saat inference: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memproses gambar.")

    # ── Gemini Integration (dengan fallback) ──────────────────────────────
    gemini_text = None
    if gemini_service.is_available:
        gemini_text = gemini_service.get_insect_info(
            predicted_class = ml_result["predicted_class"],
            confidence      = ml_result["confidence"],
            top_predictions = ml_result["top_predictions"],
        )
        # gemini_text bisa None jika 503/rate limit → frontend tampilkan pesan fallback

    # ── Build Response ────────────────────────────────────────────────────
    top_predictions = [
        PredictionItem(class_name=p["class"], confidence=p["confidence"])
        for p in ml_result["top_predictions"]
    ]

    return PredictResponse(
        predicted_class  = ml_result["predicted_class"],
        confidence       = ml_result["confidence"],
        top_predictions  = top_predictions,
        gemini_info      = gemini_text,
        gemini_available = gemini_service.is_available,
    )


# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Lihat log server untuk detail."},
    )
