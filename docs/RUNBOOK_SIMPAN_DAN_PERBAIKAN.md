# Runbook: simpan poligon, jejak audit, dan perbaikan data

Untuk siapa pun yang merawat GEOSTEVIA. Akses server, alamat VPS, token, dan chat id sengaja tidak ditulis di sini; semuanya ada
di catatan operator.

## 1. Dua jalur simpan

| | Simpan penuh | Simpan delta |
|---|---|---|
| Endpoint | `POST /annotations/grid/{id}` (`backend/app/api/annotations.py`, `save_grid_annotations`) | `POST /annotations/grid/{id}/changes` (`backend/app/api/grid_changes.py`) |
| Dipakai oleh | semua mapper kecuali yang di sebelah kanan | admin, `DELTA_PILOT_USER_IDS` di `frontend/src/stores/annotations.js`, dan siapa pun yang mengisi `localStorage geostevia_delta_save = 1` |
| Yang dikirim | seluruh isi grid | hanya yang berubah |
| Penghapusan | baris yang tidak ada di kiriman dihapus, kecuali yang berubah setelah `synced_at` klien (dipertahankan, `preserved_ids`) | hanya yang disebut klien, dengan `version`; kalah konflik bila baris berubah ("server menang") |
| Kunci poligon baru | `_uiId` (di level atas fitur atau di `properties`), dikembalikan lewat `id_map` | `client_uid`, idempoten |
| Pagar kembar | dedupe >85% di dalam kiriman; poligon tanpa id yang mirip (IoU >= 0,9, kelas sama) dengan baris yang berubah setelah sinkron diadopsi, bukan disisipkan | sisipan baru yang kembar kelas-sama (IoU >= 0,9) dengan baris tersimpan dibuang dan dilaporkan di `rejected` |

Peringatan kembar (`duplicate_warnings`, audit `DUPLICATE_SUSPECT`) hanya melapor; kelas yang beda tidak pernah dibuang otomatis.

Aturan yang harus dijaga: **setiap tulis ke baris poligon harus lewat salah satu jalur di atas**, supaya `updated_at` tetap bisa
dipercaya. Tulis langsung yang menggeser `updated_at` di belakang klien (dulu `PUT /{id}/class` dari klik poligon) membuat
poligon yang kemudian dihapus lokal tampak "diubah pihak lain" dan menumpuk di samping penggantinya. `PUT /{id}/class` masih
dipakai jendela "tetapkan kelas" (grid dimuat ulang sesudahnya) dan `AdminQCView` (reviewer).

## 2. Jejak audit

`audit_logs` (`action`, `task_grid_id`, `details` JSON):

| action | isi `details` |
|---|---|
| `SAVE_ANNOTATIONS` | `mode` (`delta` atau `full`), delta: `upserts`, `deletes`, `conflicts`, `dropped_duplicates`, `gone_deletes`; penuh: `payload`, `no_id`, `new`, `adopted`, `preserved`, `dropped`; keduanya: `ctx` |
| `DUPLICATE_SUSPECT` | pasangan (`pairs`: id, kelas, IoU, luas), id baru/dihapus/konflik, `ctx` |
| `DEDUPE_GIANTS`, `RESOLVE_OVERLAPS` | hasil skrip pembersihan |

`ctx` dikirim klien tiap simpan (`frontend/src/services/saveContext.js`): `tab`, `grid`, `loaded_s`, `features`, `no_id`
(poligon di layar tanpa id database) dan `ops` (maksimal 12 operasi terakhir: `split_poly`, `split_line`, `merge`,
`reassign_class`, `undo`, `redo`, `restore_draft`, `edit_vertices`, ..., dengan `ago` detik sebelum simpan).

```sql
-- simpan per mode, 8 jam terakhir
select coalesce(details::json->>'mode','full'), count(*) from audit_logs
 where action='SAVE_ANNOTATIONS' and created_at > now() - interval '8 hours' group by 1;
-- jejak sebelum kembar di satu grid
select created_at, details::json->'ctx'->'ops' from audit_logs
 where action='DUPLICATE_SUSPECT' and task_grid_id = <id> order by id desc limit 5;
```

Waktu server = UTC (WIB = UTC + 7). Jangan jalankan query geometri berat (pasangan seluruh grid, `st_union` per lubang) langsung di
database produksi; pakai `statement_timeout` dan `set max_parallel_workers_per_gather = 0` (memori bersama container kecil).

## 3. Gejala, arti, tindakan

| Gejala | Artinya | Tindakan |
|---|---|---|
| `DUPLICATE_SUSPECT` baru | dua poligon hampir identik di satu grid | baca `ctx.ops`; bersihkan dengan `dedupe_giants.py` |
| "Sisipan kembar ditolak server" | pagar bekerja | tidak perlu tindakan; jelaskan ke mapper |
| `preserved` besar di simpan penuh | klien kehilangan sinkron (tab usang, baris diubah pihak lain) | hard refresh; cek tulis langsung yang menggeser `updated_at` |
| `no_id` naik terus antar simpan | id tidak sampai ke klien (gejala bug `_uiId`, Okt 2026) | jalankan `backend/tests/test_save_flow.py`; periksa `id_map` |
| Konflik versi | baris diubah pihak lain sejak dimuat | mapper melihat toast; minta refresh |
| Laporan Telegram "monitor GAGAL jalan" atau `poll.log` berisi 401 | pemantau atau token bermasalah | periksa cron dan `~/.geostevia_monitor.env` (bagian 5) |

## 4. Skrip pembersihan (`backend/scripts/`)

Semua skrip yang menulis adalah **dry-run secara bawaan**; menulis butuh `--apply`, menolak jalan bila mapper menyimpan grid itu kurang dari
`--idle-min` menit (bawaan 30; simpan admin juga dihitung), membuat snapshot (`grid_snapshots`) dan berakhir dengan satu `commit`.

Urutan satu grid: `dedupe_giants.py` (salinan usang), lalu `resolve_overlaps.py` (poligon lebih kecil menang), lalu `absorb_gaps.py` (celah).

Aturan kerja:
1. Backup baru dulu (`pg_dump -Fc`), lalu `pg_restore -l` pada berkas itu untuk memastikan terbaca.
2. Baca dry-run, lalu terapkan **satu grid per perintah**.
3. Jangan sentuh grid `SUBMITTED` atau `APPROVED`, dan jangan tulis ke grid yang pemiliknya sedang aktif (tab usang bisa menimpa).
4. Jangan jalankan `absorb_gaps.py` pada grid yang sebagian besar areanya belum dipetakan (mis. cakupan 66%): ia akan membuat poligon
   kelas 0 raksasa yang berat.
5. Setelah menulis, ukur ulang dari database (jumlah poligon, jumlah luas, tumpang tindih, kelas 0) dan beri tahu pemilik: hard refresh,
   tutup tab lama, isi kelas 0 yang baru.

Menjalankan (di host VPS): `docker cp <skrip> geoai_backend:/tmp/` lalu
`docker exec -e PYTHONPATH=/app geoai_backend python -W ignore /tmp/<skrip>.py <task_grid_id> [opsi]`.
`/tmp` container terhapus setiap backend dibangun ulang, jadi salin ulang.

## 5. Pemantau Telegram

`backend/scripts/daily_monitor.py`, dipasang di host VPS (`~/geostevia_monitor/`, salinan skrip perbaikan di `fix/`), dijalankan `cron`:
laporan 07:05, 13:05, dan 19:05 WIB, dan polling perintah tiap menit (`--poll`, dijaga `flock`). Hanya membaca database.

- Perintah dari chat yang berwenang saja: `/periksa [jam]` (laporan sekarang), `/fix [grid]` (pilih grid dan tindakan dengan tombol; **hanya dry-run**,
  tidak pernah `--apply`), `/bantuan`.
- Kredensial di `~/.geostevia_monitor.env` (mode 600): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Ganti token: cabut lewat @BotFather,
  isi token baru langsung di berkas itu lewat SSH, kirim `/periksa` untuk menguji.
- Setelah mengubah skrip di repo, salin ulang ke VPS (`scp`), termasuk `fix/*.py` bila skrip perbaikan berubah.

## 6. Deploy

Hanya atas keputusan eksplisit; cek dulu siapa yang sedang menyimpan (`audit_logs`, 10 menit terakhir).

1. Jalankan tes: `backend/venv/bin/python -m pytest backend/tests` dan `node --test "frontend/tests/**/*.test.mjs"` (di `frontend/`).
   Tes yang butuh database terisi dilewati dengan alasan; `REQUIRE_DB_TESTS=1` membuatnya gagal bila database mati.
2. Push ke `main`; di VPS `git pull --ff-only`.
3. Backend: `docker compose -f docker-compose.prod.yml up -d --build --no-deps backend` (restart sekitar 30 detik; build memakai
   `backend/constraints.txt`, semua paket dipin). Frontend: sama dengan `frontend`. Mapper perlu hard refresh agar memakai kode frontend baru.
4. Verifikasi: kontainer `healthy`, kode baru ada di dalam, tidak ada traceback atau 500 di log, simpan setelah restart berstatus 200 dan
   tercatat di audit.
5. Pembatalan: `git revert` commitnya, push, bangun ulang layanan yang sama.

## 7. Riwayat singkat (22-24 Oktober 2026)

Poligon raksasa dan kembar menumpuk di beberapa grid. Penyebab yang terbukti dan perbaikannya:

| Penyebab | Perbaikan |
|---|---|
| Simpan delta: hapus yang kalah konflik versi meninggalkan baris lama di samping penggantinya | pagar sisipan kembar `141741d` |
| Simpan penuh: poligon yang diedit sedikit tanpa id disisipkan di samping baris lamanya | adopsi IoU >= 0,9 `26d40ea` |
| `PUT /{id}/class` dari klik poligon menggeser `updated_at` di belakang klien | dihapus `b0045d6` |
| `_uiId` level atas dibuang server: id poligon hasil potong/merge tidak pernah kembali ke klien, tiap autosave menghapus lalu menyisipkan ulang semuanya (Grid 027: poligon tanpa id 4 menjadi 148 dalam 64 simpan) | alias `_uiId` `ecdb7b5` |

Alat yang ditambahkan: jejak klien `ctx` (`6310273`), pemantau Telegram dan `/periksa` `/fix` (`9c6e7b7`, `8c8109f`), skrip pembersihan (`3305d87`).
Yang belum terbukti: bahwa semua kembar lain berakhir, dan penyebab kelambatan Grid 22 (dugaan: satu poligon 1,85 MB dengan 66.418 titik).
