# 🛰️ GeoAI Sentinel-2 Land Cover Collaborative Platform for Deep Learning U-Net

Platform Web GIS modern dan kolaboratif untuk pembuatan **Training Sample Tutupan Lahan (Land Cover)** berbasis citra satelit **Sentinel-2** menggunakan arsitektur **Deep Learning U-Net** ($256 \times 256$ pixel). Platform ini dirancang khusus untuk kerja tim antara **1 Dosen/Admin** dan **10 Mahasiswa (Annotators)** dengan sistem pembagian tugas Grid Tile, kendali kualitas (QA/QC), dan ekspor dataset 1-klik.

---

## 🌟 Fitur Utama

1. **Skema 12 Kelas Tutupan Lahan Standar Nasional**:
   - `1`: Hutan Lahan Kering (`#006400`)
   - `2`: Hutan Lahan Basah & Mangrove (`#2E8B57`)
   - `3`: Semak & Belukar (`#9ACD32`)
   - `4`: Tanaman Pertanian Lahan Kering (`#FFD700`)
   - `5`: Tanaman Perkebunan (`#808000`)
   - `6`: Infrastruktur & Lahan Terbangun (`#FF0000`)
   - `7`: Lahan Terbuka Bebas Vegetasi (`#D2B48C`)
   - `8`: Wilayah Operasi Tambang (`#8B4513`)
   - `9`: Tubuh Air (`#0000FF`)
   - `10`: Tanaman Padi Lahan Basah (`#00FFFF`)
   - `11`: Savanna (`#F0E68C`)
   - `12`: Tambak (`#008B8B`)
   - `0`: Background / Unannotated

2. **Integrasi Citra Sentinel-2 & Google Earth Engine (GEE)**:
   - Komposit Bebas Awan (Cloud-free median composite) untuk tahun **2017** dan **2026** di wilayah **Sumatera Barat** dan **Kalimantan**.
   - Layer Switcher multi-spektral interaktif:
     - **True Color (RGB 4-3-2)**: Visual alami
     - **False Color NIR (8-4-3)**: Vegetasi tampak merah menyala
     - **Agriculture SWIR (11-8-2)**: Pembeda jelas sawah, sawit, tambang, dan tanah
     - **NDVI Colorized**: Indeks kerapatan kanopi vegetasi

3. **Studio Digitasi Poligon Berbasis Grid Task ($2.56\text{ km} \times 2.56\text{ km}$)**:
   - Area studi dibagi menjadi kotak-kotak grid reguler berukuran tepat $2560\text{ m} \times 2560\text{ m}$ (setara $256 \times 256$ piksel pada resolusi 10m).
   - Dilengkapi tool digitasi **Leaflet-Geoman**: Draw Polygon, Rectangle, Edit, Drag, Snapping otomatis, Cut/Split Polygon, dan Transparansi Opacity dinamis.

4. **Kolaborasi Multi-User & QA/QC Review (1 Dosen + 10 Mahasiswa)**:
   - **Mahasiswa**: Mengakses grid yang ditugaskan, mendigitasi poligon, menyimpan draf, dan menekan tombol *Submit for Review*.
   - **Dosen (Admin)**: Dashboard matriks progres live 10 mahasiswa, antrean review, validasi visual, serta tombol **Approve** atau **Reject with Notes** (catatan revisi).

5. **1-Click Deep Learning U-Net Dataset Exporter**:
   - Otomatis merasterisasi poligon vektor menjadi mask integer ($256 \times 256$ piksel).
   - Membagi data secara spasial (Tile-level split) menjadi:
     - `train/` (70%)
     - `val/` (15%)
     - `test/` (15%)
   - Menghasilkan file gambar citra (tensor spektral), mask label raw integer (PNG), mask visual RGB untuk verifikasi mata, serta `metadata.json`.
   - Mengompresi seluruh dataset menjadi file `.zip` siap download.

---

## 🏗️ Struktur Folder Proyek

```
Training_Sample/
├── backend/                  # Python FastAPI GeoAI Backend
│   ├── app/
│   │   ├── api/              # Endpoint Auth, Tasks, Annotations, GEE, Export
│   │   ├── core/             # Konfigurasi & JWT Security
│   │   ├── db/               # Model SQLAlchemy & Database Seed
│   │   ├── services/         # GEE Service, Grid Generator, Rasterizer Pipeline
│   │   └── main.py           # Entrypoint FastAPI & CORS
│   ├── requirements.txt      # Dependensi GeoAI (Rasterio, GeoPandas, GEE, FastAPI)
│   └── tests/                # Automated Test Suite
│
├── frontend/                 # Vue 3 + Quasar + MapLibre/Leaflet Studio
│   ├── src/
│   │   ├── components/       # ClassPalette, LayerSwitcher, Navbar
│   │   ├── stores/           # Pinia Auth, Tasks, Annotations Store
│   │   ├── views/            # Dashboard, Studio Digitasi, Admin QC, Export
│   │   └── main.js
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Menjalankan Backend (FastAPI)
```bash
# Masuk ke direktori root
cd /Users/danangwijaya/Documents/Danang/PROJECT/CODE/Training_Sample

# Aktifkan virtual environment & jalankan server FastAPI
PYTHONPATH=backend backend/venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> Database SQLite SpatiaLite otomatis di-inisialisasi dan di-seed dengan akun 1 Dosen + 10 Mahasiswa saat server pertama kali menyala!
> Dokumentasi API Swagger dapat diakses di: `http://localhost:8000/docs`

### 2. Menjalankan Frontend (Vue 3 + Vite)
```bash
# Buka terminal baru
cd /Users/danangwijaya/Documents/Danang/PROJECT/CODE/Training_Sample/frontend

npm run dev
```
> Buka web browser di: `http://localhost:5173`

---

## 🔑 Akun Uji Coba Bawaan (Default Accounts)

Platform telah dilengkapi tombol **1-Click Fast Login** di halaman Login dan menu navigasi atas:

| Role | Username | Password | Keterangan |
|---|---|---|---|
| **Dosen / Admin** | `admin` | `admin123` | Dr. Hendra Gunawan (Reviewer QC & Exporter) |
| **Mahasiswa 1** | `mahasiswa1` | `mhs123` | Ahmad Fauzi (Annotator) |
| **Mahasiswa 2** | `mahasiswa2` | `mhs123` | Budi Santoso (Annotator) |
| **Mahasiswa 3 s/d 10** | `mahasiswa3` ... `mahasiswa10` | `mhs123` | Mahasiswa Annotators |

---

## 🛰️ Konfigurasi Google Earth Engine (Opsional)

Jika ingin menghubungkan langsung dengan akun Google Earth Engine Anda:
1. Pastikan Anda telah memiliki Google Cloud Project dengan Earth Engine API aktif.
2. Buat file `.env` di folder `backend/` dengan variabel:
```env
GEE_SERVICE_ACCOUNT=your-sa@project-id.iam.gserviceaccount.com
GEE_PRIVATE_KEY_PATH=/path/to/gee-private-key.json
GEE_PROJECT_ID=your-gcp-project-id
```
*(Catatan: Jika GEE belum dikonfigurasi, sistem secara otomatis mengaktifkan fallback basemap satelit resolusi tinggi sehingga seluruh fungsi digitasi, pembagian tugas, QA/QC, dan ekspor dataset U-Net tetap berjalan 100% lancar).*
