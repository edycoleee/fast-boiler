# Reusable Kit Checklist (Fast Boiler)

Dokumen ini adalah checklist agar boilerplate bisa dipakai ulang untuk banyak aplikasi kecil dengan perubahan minimal.

## Standar arsitektur kode (wajib dipakai)

Untuk menjaga clean code, maintenance mudah, dan mencegah file membengkak, boilerplate ini mengunci pola:

1. **Modular Monolith** per domain/fitur (`news`, `service`, `user`, `media`, dst).
2. **Layered Architecture**: `router -> service -> repository -> model`.
3. **Template Composition**: halaman dirakit dari partial/komponen Jinja, bukan satu file template panjang.
4. **Batas ukuran file**:
   - router: target <= 200 baris
   - service/repository: target <= 250 baris
   - template halaman: target <= 150 baris (lebih dari itu dipecah jadi partial)
5. **Single responsibility** per file: satu file, satu tanggung jawab utama.

## Cara pakai checklist

- `[x]` = sudah siap reusable.
- `[ ]` = belum siap, perlu dirapikan.
- **Wajib Generik** = tidak boleh hardcoded domain.
- **Boleh Spesifik Domain** = boleh menyesuaikan proyek tertentu.

---

## 1) Fondasi Arsitektur

### 1.1 Wajib Generik
- [x] Struktur folder inti stabil (`app/`, `templates/`, `static/`, `tests/`, `alembic/`).
- [x] Struktur domain modular stabil (`app/modules/<domain>/...`) untuk mencegah file gemuk.
- [x] Layer standar diterapkan di setiap domain (`router`, `service`, `repository`, `schemas`).
- [x] Konfigurasi aplikasi berbasis environment (`APP_NAME`, `BASE_URL`, `DB_URL`, `SECRET_KEY`).
- [x] Inisialisasi DB dan migration tidak bergantung nama domain tertentu.
- [x] Error handling (404/500) generik dan reusable.
- [x] Logging dasar aktif (request/error), tanpa pesan hardcoded domain.

### 1.2 Boleh Spesifik Domain
- [ ] Nama proyek akhir.
- [ ] Konfigurasi integrasi pihak ketiga khusus domain (mis. layanan email/WA tertentu).

---

## 2) UI Design System

### 2.1 Wajib Generik
- [x] Design tokens netral: color, spacing, typography, radius, shadow.
- [x] Komponen atomik reusable: button, input, select, textarea, badge, alert.
- [x] Komponen komposit reusable: table, modal, pagination, navbar, footer.
- [x] Semua state tersedia: hover, focus, disabled, loading, error, empty.
- [x] Komponen di `/design-system` berasal dari komponen asli yang dipakai aplikasi.
- [x] Tidak ada label domain hardcoded pada komponen (mis. nama institusi di komponen umum).

### 2.2 Boleh Spesifik Domain
- [ ] Palet brand (warna primer/sekunder proyek).
- [ ] Logo, ikon brand, dan tipografi merek.
- [ ] Hero section dan konten visual landing page.

---

## 3) Template & Routing

### 3.1 Wajib Generik
- [x] `layouts/public.html` dan `layouts/admin.html` reusable untuk semua proyek.
- [x] Pola partial Jinja konsisten (`_table.html`, `_row.html`, `_form.html`).
- [x] Struktur route dipisah: `public/`, `admin/`, `htmx/`.
- [x] Halaman besar dipecah ke partial per section agar panjang file terkendali.
- [x] Penamaan route dan endpoint konsisten, tidak mengunci satu domain.
- [x] Meta title/description punya fallback generik.

### 3.2 Boleh Spesifik Domain
- [ ] Halaman konten khas domain (mis. profil organisasi, unit layanan khusus).
- [ ] Struktur menu publik yang mengikuti kebutuhan proyek.

---

## 4) Auth, Session, dan RBAC

### 4.1 Wajib Generik
- [x] Login/logout session-based reusable.
- [x] Model User/Role/Permission netral dan dapat diperluas.
- [x] Permission guard berbasis action/resource (bukan nama fitur hardcoded).
- [x] Cookie/session security dasar aktif.
- [x] Redirect after login/logout konsisten.

### 4.2 Boleh Spesifik Domain
- [ ] Daftar role default proyek (mis. Admin, Editor, Operator Layanan X).
- [ ] Kebijakan akses khusus unit/fungsi bisnis tertentu.

---

## 5) Modul CMS

### 5.1 Wajib Generik
- [x] Modul konten generik tersedia: Page, Post/News, Media, Settings.
- [x] CRUD pattern seragam (list/create/edit/delete + validasi + feedback).
- [x] Query database ditempatkan di repository, bukan di router.
- [x] Business rules ditempatkan di service, bukan di router/template.
- [x] Komponen tabel/form dipakai lintas modul.
- [x] Dukungan HTMX untuk refresh partial agar UI responsif tanpa SPA.

### 5.2 Boleh Spesifik Domain
- [ ] Modul vertikal khusus (mis. Doctor, Service, Product, Event, Program).
- [ ] Field tambahan domain pada model/CRUD.

---

## 6) Data, Migration, dan Seed

### 6.1 Wajib Generik
- [x] Migration pertama dapat dijalankan di mesin baru tanpa edit manual.
- [x] Seed data minimum tersedia (admin user, role dasar, sample konten).
- [x] Tidak ada seed yang mengandung data sensitif/privat.
- [x] Nama file DB/path data bisa diubah via config.

### 6.2 Boleh Spesifik Domain
- [ ] Seed konten demo sesuai niche (mis. layanan kesehatan, edukasi, UMKM).

---

## 7) Media & Upload

### 7.1 Wajib Generik
- [x] Validasi tipe file dan ukuran file.
- [x] Penamaan file aman/unik.
- [x] Path upload configurable.
- [x] Komponen media picker reusable lintas modul.

### 7.2 Boleh Spesifik Domain
- [ ] Kategori folder media spesifik use case.
- [ ] Rasio/crop default per jenis konten domain.

---

## 8) Interaksi Canvas (Reusable)

### 8.1 Wajib Generik
- [ ] Komponen canvas wrapper reusable (`canvas-container`, `toolbar`, `status bar`).
- [ ] Event handler standar: pointer down/move/up, wheel zoom, pan, reset view.
- [x] State management canvas konsisten (skala, posisi, elemen terpilih, mode aktif).
- [x] Shortcut dasar reusable (undo, redo, delete selection, save).
- [x] Autosave draft untuk mencegah kehilangan perubahan.
- [ ] Validasi boundary agar elemen tidak keluar area kerja secara tidak sengaja.
- [x] Ekspor standar (`png`/`jpg`/`json`) dan impor JSON untuk edit ulang.
- [x] Endpoint backend untuk simpan/muat hasil canvas dipisah dari UI logic.

### 8.2 Boleh Spesifik Domain
- [ ] Jenis elemen canvas khusus domain (stempel, marker medis, node workflow, dll.).
- [ ] Aturan snapping/grid khusus use case.
- [ ] Metadata domain per objek canvas (mis. kode layanan, kategori, prioritas).

---

## 9) Pola CRUD Reusable (Wajib untuk Modul Berulang)

### 9.1 Wajib Generik
- [x] Satu pola endpoint konsisten: `index`, `create`, `store`, `edit`, `update`, `delete`.
- [x] Form schema/validator dipisah dari router agar mudah dipakai lintas modul.
- [x] Komponen partial wajib tersedia: `_table.html`, `_row.html`, `_form.html`, `_filters.html`.
- [x] Fitur default di semua modul CRUD: search, sort, pagination, filter status.
- [x] Umpan balik seragam: success/error flash atau toast, format pesan konsisten.
- [x] Soft delete atau hard delete ditetapkan jelas per modul.
- [x] Audit minimum: `created_at`, `updated_at`, `created_by`, `updated_by`.
- [ ] Import/export data opsional tetapi memakai antarmuka service yang sama.
- [x] HTMX flow seragam (submit form, refresh table row/section, handle validation error inline).

### 9.2 Boleh Spesifik Domain
- [ ] Field khusus setiap entitas.
- [ ] Aturan bisnis validasi khusus domain.
- [ ] Workflow persetujuan (approval) bila dibutuhkan modul tertentu.

---

## 10) Testing & Quality Gate

### 10.1 Wajib Generik
- [x] Test route publik minimal (home, list, detail).
- [x] Test auth dasar (login sukses/gagal, proteksi route admin).
- [x] Test endpoint HTMX partial.
- [x] Test minimal untuk 2 CRUD utama.
- [x] Test CRUD reusable (create/update/delete) dengan skenario valid + invalid.
- [ ] Test canvas endpoint (simpan/muat/ekspor) dan validasi payload.
- [ ] README setup diverifikasi di mesin bersih (<10 menit run).

### 10.2 Boleh Spesifik Domain
- [ ] Test skenario bisnis domain (workflow unik aplikasi tertentu).

---

## 11) Checklist Go-Live Reusable

### 11.1 Wajib Generik
- [ ] Clone project → install deps → migrate → run berhasil.
- [x] Branding bisa diganti tanpa ubah struktur backend.
- [ ] Modul generik dapat dipakai tanpa mengaktifkan modul domain spesifik.
- [ ] Modul canvas bisa dinonaktifkan jika proyek tidak membutuhkan.
- [x] Dokumentasi "mulai proyek baru dari boilerplate" jelas dan langkah demi langkah.

### 11.2 Boleh Spesifik Domain
- [ ] Paket "starter content" untuk domain tertentu.
- [ ] Preset halaman khusus vertical market.

---

## 12) Batasan agar tetap reusable

### Jangan dilakukan (anti-pattern)
- [ ] Hardcode nama domain/proyek di komponen global.
- [x] Menaruh logic bisnis langsung di template.
- [x] Menaruh query DB langsung di router tanpa service layer.
- [x] Menggabungkan router + service + repository dalam satu file panjang.
- [x] Membuat komponen hanya untuk demo, tetapi tidak dipakai aplikasi.
- [x] Mengikat CRUD ke satu model saja tanpa abstraction pattern.
- [x] Menaruh perhitungan koordinat canvas kompleks langsung di template.
- [ ] Menambah JavaScript kompleks jika HTMX + Alpine sudah cukup.

### Prinsip utama
1. SSR-first (FastAPI + Jinja2).
2. HTMX untuk interaksi server.
3. Alpine.js untuk interaksi UI lokal.
4. Komponen reusable dulu, domain-specific belakangan.
5. Satu codebase, banyak turunan aplikasi kecil.

---

## 13) Quick Start saat membuat aplikasi baru dari boilerplate

1. Clone template.
2. Ubah `.env` (nama app, URL, DB, secret).
3. Ganti branding (logo, token warna, font).
4. Pilih modul aktif (nyalakan yang perlu, nonaktifkan sisanya).
5. Jalankan migration + seed.
6. Aktifkan/nonaktifkan modul canvas sesuai kebutuhan.
7. Ganti konten demo dengan konten proyek.
8. Jalankan test minimum.
9. Deploy.
