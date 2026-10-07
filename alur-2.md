# Alur 2 — Execution Spec Bertahap (Implementasi Nyata)

Dokumen ini menurunkan [alur-1.md](E:/python/fast-boiler/alur-1.md) menjadi langkah implementasi harian yang dapat langsung dieksekusi.

---

## 1) Target eksekusi tahap awal

Tahap awal memprioritaskan satu domain penuh sebagai referensi pola:

- domain: `news`
- jalur lengkap: `public + admin + htmx + api`
- arsitektur: `router -> service -> repository -> model`

Jika domain `news` stabil, domain lain (`services`, `pages`, `media`) tinggal menyalin pola yang sama.

---

## 2) Struktur file minimal yang dibuat dulu

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── db.py
│   └── security.py
├── modules/
│   ├── auth/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   └── news/
│       ├── router_public.py
│       ├── router_admin.py
│       ├── router_htmx.py
│       ├── router_api.py
│       ├── service.py
│       ├── repository.py
│       ├── schemas.py
│       └── models.py
└── templates/
    ├── layouts/
    │   ├── public.html
    │   └── admin.html
    ├── public/news/
    │   ├── index.html
    │   └── detail.html
    └── admin/news/
        ├── index.html
        ├── _table.html
        ├── _row.html
        ├── _form.html
        └── _filters.html
```

---

## 3) Kontrak endpoint modul `news`

## 3.1 Public (HTML penuh)

- `GET /news` -> halaman list berita (Jinja full page)
- `GET /news/{slug}` -> halaman detail berita (Jinja full page)

## 3.2 Admin (HTML + PRG)

- `GET /admin/news` -> halaman manajemen berita
- `GET /admin/news/new` -> form create
- `POST /admin/news` -> create (redirect 303 ke `/admin/news`)
- `GET /admin/news/{id}/edit` -> form edit
- `POST /admin/news/{id}` -> update (redirect 303 ke `/admin/news`)
- `POST /admin/news/{id}/delete` -> delete (redirect 303 ke `/admin/news`)

## 3.3 HTMX (partial HTML)

- `GET /admin/news/partials/table` -> `_table.html`
- `GET /admin/news/partials/row/{id}` -> `_row.html`
- `GET /admin/news/partials/form` -> `_form.html`
- `GET /admin/news/partials/filters` -> `_filters.html`

## 3.4 API (`/api/v1/news`)

- `GET /api/v1/news` -> list JSON standar
- `GET /api/v1/news/{id}` -> detail JSON standar
- `POST /api/v1/news` -> create JSON standar
- `PUT /api/v1/news/{id}` -> update JSON standar
- `DELETE /api/v1/news/{id}` -> delete JSON standar

---

## 4) Kontrak schema minimal (Pydantic)

Untuk domain `news`, minimal:

- `NewsCreate`
  - `title: str`
  - `slug: str`
  - `excerpt: str | None`
  - `content: str`
  - `status: Literal["draft", "published"]`
- `NewsUpdate` (field opsional)
- `NewsOut`
  - `id: int`
  - `title: str`
  - `slug: str`
  - `excerpt: str | None`
  - `content: str`
  - `status: str`
  - `published_at: datetime | None`
  - `created_at: datetime`
  - `updated_at: datetime`

Schema pembungkus API:
- `ApiMeta`
- `ApiError`
- `ApiResponse[T]`

---

## 5) Urutan eksekusi harian (14 hari)

## Hari 1 — Bootstrap
- buat struktur folder dasar
- setup virtualenv + dependency awal
- buat `main.py` + health endpoint
- setup `core/config.py` dan `core/db.py`

Kriteria selesai:
- server jalan,
- endpoint `/health` memberi respons 200.

## Hari 2 — Model + Alembic
- buat model `news`
- inisialisasi Alembic
- generate migration pertama
- jalankan migration

Kriteria selesai:
- tabel `news` terbentuk,
- migration bisa diulang di environment baru.

## Hari 3 — Repository + Service
- implement `news/repository.py`
- implement `news/service.py`
- tambah validasi rule bisnis dasar

Kriteria selesai:
- service create/list/get/update/delete berjalan via test unit sederhana.

## Hari 4 — Public Router + Template
- implement `router_public.py`
- buat `public/news/index.html` dan `detail.html`

Kriteria selesai:
- list/detail publik tampil dengan data DB.

## Hari 5 — Admin Router + PRG
- implement `router_admin.py`
- implement flow create/edit/delete dengan PRG (`303`)

Kriteria selesai:
- submit form admin tidak menghasilkan resubmit saat refresh.

## Hari 6 — HTMX Partial
- implement `router_htmx.py`
- buat `_table.html`, `_row.html`, `_form.html`, `_filters.html`

Kriteria selesai:
- filter/search/refresh tabel berjalan tanpa reload penuh.

## Hari 7 — API Router + Response Standar
- implement `router_api.py`
- terapkan `ApiResponse[T]` konsisten sukses/error

Kriteria selesai:
- semua endpoint `/api/v1/news` memakai shape JSON yang sama.

## Hari 8 — Auth + RBAC dasar
- login/logout session
- guard akses admin route

Kriteria selesai:
- route admin tidak bisa diakses user anonim.

## Hari 9 — Design System integrasi
- satukan komponen table/form/button dengan halaman admin news
- verifikasi tidak ada komponen duplikat

Kriteria selesai:
- halaman admin news sepenuhnya menggunakan komponen reusable.

## Hari 10 — Validasi & Error Handling
- konsolidasikan pesan error form
- pastikan HTTP status API semantik

Kriteria selesai:
- validasi invalid payload konsisten di admin dan API.

## Hari 11 — Logging + Request ID
- tambahkan request ID di middleware
- isi `meta.request_id` di response API

Kriteria selesai:
- request ID tampil di log dan response API.

## Hari 12 — Testing end-to-end modul news
- test public list/detail
- test admin PRG flow
- test HTMX partial endpoint
- test API CRUD

Kriteria selesai:
- test modul news lulus.

## Hari 13 — Refactor batas ukuran file
- pecah file yang melebihi batas guardrail di [alur-1.md](E:/python/fast-boiler/alur-1.md)
- rapikan import/dependency

Kriteria selesai:
- seluruh file domain news memenuhi batas baris.

## Hari 14 — Dokumentasi + template readiness
- update README quick start
- tulis checklist “cara menambah domain baru dari pola news”

Kriteria selesai:
- proyek siap dijadikan baseline boilerplate.

---

## 6) Acceptance test minimum per jalur

1. Public:
   - `GET /news` -> 200
   - `GET /news/{slug}` -> 200 / 404 valid
2. Admin:
   - `POST /admin/news` -> 303 redirect
   - setelah redirect, record benar-benar tersimpan
3. HTMX:
   - endpoint partial mengembalikan HTML fragment valid
4. API:
   - success response pakai `success=true`, `data`, `meta`
   - error response pakai `success=false`, `error`, `meta`

---

## 7) Setelah modul `news` stabil

Ulangi pola identik untuk `services`:

- salin kontrak endpoint,
- sesuaikan schema/model,
- pertahankan standar response dan flow PRG/HTMX/API.

Prinsip: domain baru menambah fitur, bukan menambah variasi arsitektur.
