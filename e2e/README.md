# Tes E2E (peramban nyata)

Menjalankan peta GEOSTEVIA yang sebenarnya (Vite dev server dari `../frontend`) terhadap backend lokal dengan database SQLite sementara
(seed membuat akun `admin` dan grid contoh). Tidak menyentuh server produksi.

```
cd e2e
npm install
npx playwright install chromium     # sekali saja, sekitar 80 MB
npm test
```

`BACKEND_PYTHON=/path/ke/python npm test` bila virtualenv backend tidak di `../backend/venv`. Server yang sudah berjalan di port 8000 dan 5173
dipakai ulang; kalau tidak, `playwright.config.js` menyalakannya sendiri dan menghapus database sementara `/tmp/geostevia_e2e.db`.

## Isi

- `tests/save_flow.spec.js`: memotong poligon dua kali lewat peta (jalur simpan penuh, tanpa simpan delta) dan memastikan autosave kedua sudah
  membawa id database untuk potongan pertama. Gagal bila server membuang `_uiId` level atas (bug 22-24 Okt 2026: 3 dari 3 poligon tanpa id) dan lolos
  setelah perbaikan (2 dari 3).

Catatan: alat potong menuntut garis yang melewati kedua tepi poligon, jadi tes memperkecil peta dan mematikan snapping dulu.
