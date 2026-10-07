# Alur 3 — Quality Gate & Release Checklist

Dokumen ini melanjutkan [alur-2.md](E:/python/fast-boiler/alur-2.md) dan menjadi gerbang kualitas sebelum boilerplate dianggap siap pakai lintas proyek.

---

## 1) Quality gate wajib lulus

## 1.1 Arsitektur
- [x] Setiap domain memakai pola `router -> service -> repository -> model`.
- [x] Tidak ada query DB langsung di router.
- [x] Tidak ada business logic berat di template Jinja.

## 1.2 Flow contract
- [x] Form admin non-HTMX menggunakan PRG (`303`).
- [x] Endpoint HTMX mengembalikan partial HTML, bukan JSON campuran.
- [x] Endpoint `/api/v1/*` mengembalikan response JSON standar.

## 1.3 Konsistensi response API
- [x] Sukses: `success`, `message`, `data`, `meta`.
- [x] Error: `success`, `message`, `error`, `meta`.
- [x] HTTP status semantik dipakai konsisten.

## 1.4 Guardrail ukuran file
- [x] Router <= 200 baris.
- [x] Service/Repository <= 250 baris.
- [x] Template halaman <= 150 baris.

## 1.5 Keamanan dasar
- [x] Session cookie diset aman sesuai environment.
- [x] Endpoint admin diproteksi auth + permission.
- [x] Upload file tervalidasi tipe dan ukuran.

---

## 2) Test matrix minimum

## 2.1 Public web
- [x] Home/News list/News detail merespons benar.
- [x] 404 page tampil untuk slug/id tidak ditemukan.

## 2.2 Admin web
- [x] Login sukses/gagal teruji.
- [x] Create/Update/Delete via PRG teruji.
- [x] Unauthorized tidak bisa akses route admin.

## 2.3 HTMX
- [x] Partial table/filter/form/row teruji status + isi.
- [x] Validasi error inline teruji pada partial form.

## 2.4 API
- [x] CRUD API lulus seluruh status utama.
- [x] Shape response sukses/error sesuai kontrak.
- [x] Pagination metadata konsisten (jika list dipaginasi).

---

## 3) Dokumen wajib sebelum release boilerplate

- [x] README setup dari nol (install -> migrate -> run).
- [x] README “cara menambah domain baru” dari pola `news`.
- [x] Ringkasan flow contract PRG/HTMX/API untuk developer baru.
- [x] Contoh `.env.example` lengkap dan aman.

---

## 4) Definisi siap rilis

Boilerplate dinyatakan siap rilis internal bila:

1. semua quality gate lulus,
2. test minimum lulus,
3. dokumentasi onboarding lengkap,
4. domain referensi `news` dapat ditiru ke `services` tanpa perubahan arsitektur.

---

## 5) Prosedur evaluasi saat menambah fitur baru

Setiap fitur/domain baru wajib menjawab:

1. Apakah router tetap tipis?
2. Apakah business rule masuk service?
3. Apakah query tetap di repository?
4. Apakah web flow tetap PRG/HTMX sesuai kontrak?
5. Apakah API mengikuti shape standar?

Jika salah satu jawabannya tidak, fitur belum lolos merge.
