# MODUL PANDUAN PENGGUNA & STANDAR OPERASIONAL PROSEDUR (SOP) DIGITASI ON-SCREEN
## Platform GeoAI STEVIA (Sentinel Training Evaluation & Verification Interface for AI)
**Versi 2.4 — Enterprise Production Edition (2026)**  
**Domain Produksi:** [https://geostevia.id](https://geostevia.id)

---

## 📋 Daftar Isi
1. [BAB 1: Pendahuluan & Gambaran Umum Platform](#bab-1-pendahuluan--gambaran-umum-platform)
2. [BAB 2: Peran Pengguna & Hak Akses (RBAC)](#bab-2-peran-pengguna--hak-akses-rbac)
3. [BAB 3: Alur Kerja Task Manager & Penugasan Grid](#bab-3-alur-kerja-task-manager--penugasan-grid)
4. [BAB 4: Standar Mutu Digitasi On-Screen & Kaidah Kartografi](#bab-4-standar-mutu-digitasi-on-screen--kaidah-kartografi)
5. [BAB 5: Panduan Lengkap Tools Digitasi](#bab-5-panduan-lengkap-tools-digitasi)
6. [BAB 6: Kunci Interpretasi Visual & Analisis Spektral Sentinel-2](#bab-6-kunci-interpretasi-visual--analisis-spektral-sentinel-2)
7. [BAB 7: Quality Control (QC) & Smart Multi-Year Replication](#bab-7-quality-control-qc--smart-multi-year-replication)
8. [BAB 8: Dataset Export & Atribut Vektor (Shapefile / GeoJSON)](#bab-8-dataset-export--atribut-vektor-shapefile--geojson)
9. [BAB 9: Shortcut Keyboard & Troubleshooting](#bab-9-shortcut-keyboard--troubleshooting)

---

## BAB 1: Pendahuluan & Gambaran Umum Platform

### 1.1 Mengenal GeoAI STEVIA
**GeoAI STEVIA** (*Sentinel Training Evaluation & Verification Interface for AI*) adalah sistem komputasi awan geospasial yang dirancang khusus untuk memfasilitasi pembuatan, verifikasi, dan standarisasi data sampel pelatihan (*ground truth training data*) penutupan lahan multi-temporal di Indonesia.

Sistem mengintegrasikan:
- Citra satelit **Sentinel-2 MSI 10-meter** bebas awan (Cloud-Optimized GeoTIFF & Google Earth Engine).
- Basis data spasial relasional **PostgreSQL 16 + PostGIS 3.4** berkinerja tinggi.
- Mesin GIS berbasis browser modern dengan topologi bersih (*gap-free* & *overlap-free*).
- Pipeline otomatis pemotongan citra dan rasterisasi mask untuk arsitektur Deep Learning (seperti U-Net/FPN/SegNet).

---

## BAB 2: Peran Pengguna & Hak Akses (RBAC)

| Peran (Role) | Wewenang Utama | Tanggung Jawab Teknis |
| :--- | :--- | :--- |
| **Annotator / Mapper** | Mengambil grid, memotong poligon, menyimpan draf, mengajukan submit tugas. | Memetakan 100% tutupan lahan di grid hingga tidak ada poligon "Belum Terklasifikasi". |
| **Reviewer / QC** | Memeriksa grid submitted, menyetujui (Approve), menolak (Reject) dengan catatan revisi. | Menguji kesesuaian spektral, kerapatan batas, dan konsistensi kelas sebelum data masuk ke AI. |
| **Superadmin** | Mengelola pengguna, membuat project & grid baru, monitoring progres, export dataset. | Memantau produktivitas nasional dan mengekspor pasangan citra/vektor siap latih. |

---

## BAB 3: Alur Kerja Task Manager & Penugasan Grid

1. **Pilih Wilayah Studi (Study Area):** Misal *Provinsi Sumatera Barat*, *IKN Nusantara*, *Kawasan Restorasi Mangrove Riau*, atau *Danau Toba*.
2. **Pilih Tahun Pengamatan:** Saring grid berdasarkan tahun target: `2025` (terkini), `2022`, `2018`, atau `2017`.
3. **Klaim Penugasan Grid (Self-Assignment):** Klik grid berstatus `Unassigned` lalu klik **Ambil Tugas Ini**.

### Siklus Status Grid:
- **Unassigned (Abu-abu):** Grid tersedia, belum diambil mapper.
- **In Progress (Kuning/Oranye):** Sedang aktif didigitasi oleh mapper (tersimpan sebagai draf).
- **Submitted (Biru):** Selesai 100% oleh mapper, sedang menunggu verifikasi Reviewer.
- **Approved (Hijau):** Lolos uji kualitas dan disetujui sebagai data training resmi.
- **Rejected (Merah):** Dikembalikan untuk diperbaiki mapper sesuai catatan koreksi.

---

## BAB 4: Standar Mutu Digitasi On-Screen & Kaidah Kartografi

### Prinsip Dasar: "Base Polygon Partitioning"
- Grid kerja diawali dengan **1 Poligon Dasar (Base Polygon)** berstatus *Belum Terklasifikasi*.
- Mapper **TIDAK PERLU** membuat poligon dari nol di luar batas grid.
- Mapper cukup **MEMOTONG** poligon dasar menggunakan alat pemotong sesuai kenampakan citra.
- Hasil potongan dijamin berhimpit presisi tanpa ada rongga kosong (*gap*) ataupun tumpang tindih (*overlap*).

### Parameter Standar Mutu:
- **Minimum Mapping Unit (MMU):** 0.25 Hektar (2.500 m² atau setara 5×5 piksel Sentinel-2).
- **Skala Tampilan Kerja:** Zoom level 15–17 (skala 1:5.000 s.d. 1:15.000).
- **Kelengkapan Area:** 100% wajib terklasifikasi sebelum dapat di-submit.

---

## BAB 5: Panduan Lengkap Tools Digitasi

1. **Pilih Poligon (Pointer / Esc):**  
   Klik poligon manapun untuk melihat luas (Ha), kelas aktif, dan membuka popup pilihan kelas instan. Poligon aktif ditandai garis biru indigo tebal.
2. **Potong Garis (Blade):**  
   Tarik garis melintasi poligon dari tepi luar ke tepi luar. Klik ganda untuk menyelesaikan; poligon akan langsung terbelah menjadi 2 bagian mandiri.
3. **Potong Area (Cookie Cutter):**  
   Gambar poligon melingkari objek tertutup (misal pemukiman di tengah hutan atau pulau di danau) untuk membagi area dalam dan luar tanpa tumpang tindih.
4. **Potong Bebas (Lasso Cut):**  
   Tahan tombol kiri mouse dan lingkari area target secara bebas. Garis akan menutup otomatis dan memotong area secara instan.
5. **Gambar Poligon Biasa:**  
   Menggambar poligon titik demi titik. Dilengkapi fitur **Single-Vertex Undo** (`Backspace`/`Delete`) untuk membatalkan 1 titik terakhir tanpa mereset seluruh garis.
6. **Freehand Stream:**  
   Tahan dan geser mouse mengalir mengikuti kelokan sungai atau garis pantai alami.
7. **Gabung Poligon (Merge):**  
   Aktifkan tool Gabung Poligon -> klik 2 atau lebih poligon bertetangga (menyala hijau emerald `#10b981`) -> klik **Satukan Poligon** pada bilah atas.
8. **Edit Titik Sudut:**  
   Klik dan geser titik sudut batas poligon yang telah dibuat untuk penyesuaian presisi.

---

## BAB 6: Kunci Interpretasi Visual & Analisis Spektral Sentinel-2

### 12 Kelas Tutupan Lahan Resmi:
1. **Hutan Lahan Kering (`#006400`):** Kanopi lebat rapat, hijau tua gelap pada TCI, merah tua membara pada NIR.
2. **Hutan Lahan Basah & Mangrove (`#2E8B57`):** Pesisir/rawa pasang-surut, nilai pantulan SWIR rendah karena basah.
3. **Semak dan Belukar (`#9ACD32`):** Vegetasi transisi rendah/terbuka, NDVI sedang.
4. **Pertanian Lahan Kering (`#FFD700`):** Tegalan, ladang jagung/ubi, petak tidak seragam.
5. **Tanaman Perkebunan (`#808000`):** Kelapa sawit, karet, teh. Pola baris tanam (grid) sangat teratur dan seragam.
6. **Infrastruktur / Lahan Terbangun (`#FF0000`):** Atap seng/genteng, jalan aspal, beton, NDBI tinggi.
7. **Lahan Terbuka Bebas Vegetasi (`#D2B48C`):** Tanah gundul, pasir, albedo pantulan tinggi di semua band tampak.
8. **Wilayah Operasi Tambang (`#8B4513`):** Lubang galian terbuka, kolam tailing, kontras tinggi.
9. **Tubuh Air (`#0000FF`):** Danau, sungai lebar, laut. Menyerap seluruh sinar NIR (mendekati 0), biru/hitam pekat.
10. **Tanaman Padi Lahan Basah (`#00FFFF`):** Sawah irigasi teratur, fase genangan air & vegetasi berulang.
11. **Savanna (`#F0E68C`):** Padang rumput terbuka luas dengan pohon sangat jarang (<20%).
12. **Tambak (`#008B8B`):** Kolam ikan/udang pesisir dengan pematang tanah persegi panjang rapi.

### Komposit Band Spektral:
- **True Color (B4-B3-B2):** Warna alami mata manusia (identifikasi kota, tanah, air keruh).
- **False Color NIR (B8-B4-B3):** Vegetasi merah cerah, badan air hitam legam (batas vegetasi tegas).
- **SWIR (B12-B8-B4):** Menembus kabut tipis, mempertegas batas kelembapan air dan bekas tambang.

---

## BAB 7: Quality Control (QC) & Smart Multi-Year Replication

### Smart Multi-Year Copy:
- Saat membuka grid tahun tertentu (misal 2022) yang belum terdigitasi, sistem otomatis mendeteksi apakah tahun lain (misal 2025) sudah selesai.
- Mapper dapat menekan tombol **"Salin Vektor dari Tahun 2025"** untuk menduplikasi seluruh poligon secara instan.
- Mapper kemudian hanya perlu memotong/memperbarui poligon yang mengalami perubahan penutupan lahan (*change detection*), menghemat hingga 70% waktu digitasi.

---

## BAB 8: Dataset Export & Atribut Vektor

### Atribut Tabel Vektor (ESRI Shapefile .shp & GeoJSON):
- `KODE_PL`: Kode angka kelas (0 s.d. 12)
- `NAMA_PL`: Nama penutupan lahan resmi
- `GRID_CODE`: Kode unik grid kerja (contoh: `SB_GRID_014_2025`)
- `TAHUN`: Tahun akuisisi Sentinel-2 (contoh: `2025`)
- `STATUS`: Status validasi (`APPROVED`, `SUBMITTED`, `DRAFT`)
- `MAPPER`: Username kontributor digitasi
- `LUAS_HA`: Luas poligon dalam Hektar
- `LUAS_M2`: Luas poligon dalam Meter Persegi

### AI Dataset Generation:
- Memotong citra Sentinel-2 menjadi patch berukuran **256 × 256 piksel**.
- Menghasilkan pasangan citra dan mask label berformat `.tif` / `.png`.
- Pembagian partisi otomatis: `train/` (70%), `val/` (20%), `test/` (10%).

---

## BAB 9: Shortcut Keyboard & Troubleshooting

| Shortcut | Fungsi Utama |
| :--- | :--- |
| **Spasi (Tahan)** | **Quick Satellite Peek:** Sembunyikan warna poligon sementara untuk mengintip citra satelit asli. |
| **Backspace / Delete** | **Single-Vertex Undo:** Hapus 1 titik sudut terakhir saat menggambar tanpa membatalkan garis. |
| **Ctrl + Z / Cmd + Z** | **Global Undo:** Membatalkan aksi potong/edit sebelumnya (hingga 40 riwayat). |
| **Ctrl + Y / Cmd + Shift + Z**| **Global Redo:** Mengulangi aksi yang sebelumnya dibatalkan. |
| **Esc (Escape)** | Membatalkan alat aktif dan kembali ke mode **Pilih Poligon (Pointer)**. |
