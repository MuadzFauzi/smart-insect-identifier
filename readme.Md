# 🦋 Smart Insect Identifier

> Aplikasi identifikasi serangga berbasis Deep Learning + Google Gemini AI  
> **Final Project — Praktikum Machine Learning**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.3.1-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash%20Lite-4285F4?style=flat-square&logo=google&logoColor=white)

---

## Daftar Isi

- [Deskripsi Proyek](#deskripsi-proyek)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Struktur Folder](#struktur-folder)
- [Prasyarat](#prasyarat)
- [Setup & Instalasi](#setup--instalasi)
  - [1. Training Model](#1-training-model)
  - [2. Backend FastAPI](#2-backend-fastapi)
  - [3. Frontend Next.js](#3-frontend-nextjs)
- [API Endpoints](#api-endpoints)
- [Dataset](#dataset)
- [Arsitektur Model](#arsitektur-model)
- [Referensi](#referensi)

---

## Deskripsi Proyek

Smart Insect Identifier adalah aplikasi web end-to-end yang memungkinkan pengguna mengunggah foto serangga dan mendapatkan:

1. **Klasifikasi otomatis** menggunakan model EfficientNet-B3 yang dilatih dengan transfer learning
2. **Informasi ensiklopedis** tentang serangga yang teridentifikasi, dihasilkan oleh Google Gemini 2.5 Flash dengan *GoogleSearch grounding*

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                │
│  Upload gambar → Preview → Hasil prediksi + Info Gemini │
└────────────────────────┬────────────────────────────────┘
                         │  POST /predict (multipart/form-data)
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│                                                         │
│  ┌──────────────┐      ┌───────────────────────────┐    │
│  │  ml_service  │      │      gemini_service       │    │
│  │              │      │                           │    │
│  │ EfficientNet │      │  Gemini 2.5 Flash         │    │
│  │    -B3       │      │  + GoogleSearch (opsional)│    │
│  │  Top-5 pred  │      │                           │    │
│  └──────────────┘      └───────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         ▲
                         │  Artifacts
┌─────────────────────────────────────────────────────────┐
│                  TRAINING (Jupyter Notebook)            │
│  Dataset Kaggle → EDA → Augmentasi → Training 2 fase    │
│  → Evaluasi → Export (.pt / .pth + metadata.json)       │
└─────────────────────────────────────────────────────────┘
```

---

## Struktur Folder

```
Final-ML-Lab-2026/
│
├── files/
│   └── insect_classifier_training.ipynb   # Training pipeline lengkap
│
├── backend/
│   ├── main.py                            # FastAPI entry point & routing
│   ├── ml_service.py                      # Inference EfficientNet-B3
│   ├── gemini_service.py                  # Integrasi Google Gemini API
│   ├── requirements.txt                   # Dependencies backend
│   ├── env.example                        # Template variabel environment
│   └── artifacts/                         # Hasil training (tidak di-commit)
│       ├── insect_classifier_traced.pt    # TorchScript model (primary)
│       ├── insect_classifier.pth          # State dict (fallback)
│       └── model_metadata.json            # Class names, img_size, dll
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx                 # Root layout + ThemeProvider
    │   │   ├── page.tsx                   # Halaman utama
    │   │   └── globals.css                # CSS variables & global styles
    │   └── components/ui
    │       ├── ThemeToggle.tsx            # Dark/light mode toggle
    │       └── ImageUploader.tsx          # Drag & drop upload + scan anim
    ├── package.json
    ├── ...
    ├── tailwind.config.ts
    └── next.config.mjs
```

---

## Prasyarat

| Komponen | Versi | Catatan |
|---|---|---|
| Python | 3.10 atau 3.11 | Bukan 3.12+ |
| Node.js | 18+ | Untuk frontend |
| NVIDIA GPU | CUDA 11.8+ | Hanya untuk training; backend pakai CPU |
| GEMINI_API_KEY | — | Gratis di [Google AI Studio](https://aistudio.google.com/) |

---

## Setup & Instalasi

### 1. Training Model

> Jalankan di laptop lokal dengan GPU NVIDIA (CUDA)

```bash
# Buat dan aktifkan virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# Install PyTorch dengan CUDA support (WAJIB pakai perintah ini)
pip install torch==2.3.1+cu124 torchvision==0.18.1+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

# Install dependencies lainnya
pip install -r requirements_training.txt

# Jalankan Jupyter
jupyter notebook
```

Buka `insect_classifier_training.ipynb`, sesuaikan path dataset di cell konfigurasi:

```python
DATA_DIR = Path(r'D:\datasets\insects')   # root folder berisi train/ val/ test/
OUTPUT_DIR = Path(r'D:\projects\...\artifacts')
```

Setelah training selesai, salin dua file berikut ke `backend/artifacts/`:

```
insect_classifier_traced.pt   (atau insect_classifier.pth)
model_metadata.json
```
> 📥 **PENTING (Unduh Bobot Model):** Karena ukuran file model biner (`.pt` / `.pth`) terlalu besar untuk GitHub, Anda wajib mengunduh file model dan metadatanya terlebih dahulu melalui tautan berikut:
> 🔗 **[Unduh File Artifacts via Google Drive](https://drive.google.com/drive/folders/1ce7eng3AvrJLalIqZEOrKzdkCoZ36K5R?usp=sharing)**
> 
> Setelah diunduh, ekstrak atau masukkan file `insect_classifier_traced.pt` dan `model_metadata.json` ke dalam folder `backend/artifacts/` sebelum melanjutkan ke langkah di bawah.
---

### 2. Backend FastAPI

```bash
cd backend

# Buat virtual environment terpisah
python -m venv venv
venv\Scripts\activate

# Install dependencies (PyTorch CPU-only, lebih ringan)
pip install -r requirements.txt

# Setup environment variables
copy env.example .env          # Windows
# cp env.example .env          # Linux/macOS
```

Edit file `.env`:

```env
GEMINI_API_KEY=your_api_key_here
USE_GOOGLE_SEARCH=false
```

Jalankan server:

```bash
uvicorn main:app --reload
```

Buka **http://localhost:8000/docs** untuk Swagger UI interaktif.

Verifikasi server siap:

```bash
curl http://localhost:8000/health
```

Respons yang diharapkan:

```json
{
  "status": "ok",
  "model_loaded": true,
  "gemini_ready": true,
  "model_info": {
    "architecture": "efficientnet_b3",
    "num_classes": 10,
    "img_size": 300,
    "test_accuracy": 0.9234
  }
}
```

---

### 3. Frontend Next.js

```bash
cd frontend

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

Buka **http://localhost:3000**

> Pastikan backend sudah berjalan di port 8000 sebelum membuka frontend.

Untuk production build:

```bash
npm run build
npm start
```

---

## API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/` | Info API |
| `GET` | `/health` | Status model ML & Gemini |
| `POST` | `/predict` | Upload gambar → prediksi + info Gemini |

### `POST /predict`

**Request:** `multipart/form-data`

| Field | Tipe | Keterangan |
|---|---|---|
| `file` | `image/*` | JPEG, PNG, BMP, WebP — maks 10 MB |

**Response:**

```json
{
  "predicted_class": "butterfly",
  "confidence": 0.923412,
  "top_predictions": [
    { "class_name": "butterfly", "confidence": 0.923412 },
    { "class_name": "moth",      "confidence": 0.051234 },
    { "class_name": "dragonfly", "confidence": 0.018900 }
  ],
  "gemini_info": "## 🦋 Butterfly\n\n### Klasifikasi Ilmiah\n...",
  "gemini_available": true
}
```

**Error Codes:**

| Kode | Penyebab |
|---|---|
| `400` | File gambar tidak valid / rusak |
| `413` | Ukuran file melebihi 10 MB |
| `415` | Tipe file tidak didukung |
| `503` | Model belum di-load (cek `artifacts/`) |

---

## Dataset

**Sumber:** [Insects Dataset — Kaggle](https://www.kaggle.com/datasets/baxtiyorbotiraliyev/insects)

Struktur folder dataset:

```
insects/
├── train/
│   ├── <kelas_1>/
│   ├── <kelas_2>/
│   └── ...
├── val/
│   └── ...
└── test/
    └── ...
```

---

## Arsitektur Model

| Komponen | Detail |
|---|---|
| **Base Model** | EfficientNet-B3 (pretrained ImageNet) |
| **Input Size** | 300 × 300 px |
| **Classifier Head** | Dropout(0.4) → Linear(1536→512) → ReLU → Dropout(0.3) → Linear(512→N) |
| **Loss Function** | CrossEntropyLoss + Label Smoothing (0.1) |
| **Optimizer** | AdamW (weight decay 1e-4) |
| **Scheduler** | CosineAnnealingLR |
| **Strategi Training** | 2 fase: freeze backbone → full fine-tuning |
| **Regularisasi** | Dropout, WeightedRandomSampler, EarlyStopping (patience=7) |
| **Augmentasi** | RandomCrop, HorizontalFlip, VerticalFlip, Rotation, ColorJitter |
| **Export Format** | TorchScript traced (`.pt`) + state dict (`.pth`) |

---

## Referensi

- Dataset: [baxtiyorbotiraliyev/insects](https://www.kaggle.com/datasets/baxtiyorbotiraliyev/insects) — Kaggle
- Repository Template: [Findney/Final-ML-Lab-2026](https://github.com/Findney/Final-ML-Lab-2026)
- EfficientNet: *Tan & Le, 2019 — EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks*
- Google Gemini: [Google AI Studio](https://aistudio.google.com/)
- FastAPI: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- Next.js: [nextjs.org](https://nextjs.org)