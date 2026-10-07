# Alur 1 — Blueprint Implementasi (Lanjutan dari `alur.md`)

Dokumen ini adalah turunan teknis dari `alur.md`.

- `alur.md` menetapkan prinsip dan checklist reusable.
- `alur-1.md` menerjemahkan prinsip menjadi struktur implementasi.

Fokus utama: **clean code**, **mudah maintenance**, dan **mencegah file membengkak**.

---

## 1) Arsitektur yang dikunci

Boilerplate ini menggunakan pola:

1. **Modular Monolith** (berbasis domain/fitur).
2. **Layered Architecture**: `router -> service -> repository -> model`.
3. **SSR-first**: FastAPI + Jinja2.
4. **Progressive enhancement**: HTMX (server interaction) + Alpine.js (UI lokal).

Dengan pola ini:
- route tetap tipis,
- business rule terkonsentrasi di service,
- query terkonsentrasi di repository,
- template tetap ringkas lewat partial.

---

## 2) Stack final

| Layer               | Teknologi                    |
|--------------------|------------------------------|
| Backend            | FastAPI                      |
| Template           | Jinja2                       |
| ORM                | SQLAlchemy                   |
| Database           | SQLite                       |
| Migration          | Alembic                      |
| CSS                | Tailwind CSS                 |
| Server interaction | HTMX                         |
| UI interaction     | Alpine.js                    |
| JSON/API khusus    | fetch()                      |
| Auth CMS           | Session-based authentication |
| RBAC               | Role + Permission            |

Prinsip penggunaan:
1. HTMX didahulukan untuk interaksi server.
2. Alpine.js hanya untuk state/interaction lokal komponen.
3. `fetch()` hanya untuk kebutuhan JSON/API khusus.
4. Komponen design system harus dipakai nyata di halaman aplikasi.

---

## 3) Struktur folder proyek (modular)

```text
fast-boiler/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   └── exceptions.py
│   ├── shared/
│   │   ├── constants/
│   │   ├── utils/
│   │   └── dependencies/
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── news/
│   │   │   ├── router_public.py
│   │   │   ├── router_admin.py
│   │   │   ├── router_htmx.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── services/
│   │   ├── pages/
│   │   ├── media/
│   │   └── settings/
│   ├── templates/
│   │   ├── layouts/
│   │   │   ├── public.html
│   │   │   └── admin.html
│   │   ├── components/
│   │   │   ├── buttons/
│   │   │   ├── forms/
│   │   │   ├── cards/
│   │   │   ├── tables/
│   │   │   ├── modals/
│   │   │   ├── alerts/
│   │   │   ├── navigation/
│   │   │   └── pagination/
│   │   ├── public/
│   │   ├── admin/
│   │   │   └── news/
│   │   │       ├── index.html
│   │   │       ├── _table.html
│   │   │       ├── _row.html
│   │   │       ├── _form.html
│   │   │       └── _filters.html
│   │   └── design-system/
│   │       └── index.html
├── static/
│   ├── css/app.css
│   ├── js/app.js
│   └── images/
├── media/
├── data/
│   └── app.db
├── alembic/
├── tests/
│   ├── modules/
│   │   ├── test_auth.py
│   │   ├── test_news_public.py
│   │   ├── test_news_admin.py
│   │   └── test_news_htmx.py
│   └── conftest.py
├── pyproject.toml
├── alembic.ini
├── tailwind.config.js
└── README.md
```

---

## 4) Kontrak layer per modul

Setiap modul domain wajib mengikuti kontrak berikut:

- **router**:
  - validasi input HTTP dasar,
  - panggil service,
  - kembalikan response/template.
- **service**:
  - business rule,
  - orkestrasi repository,
  - keputusan domain (status, workflow, permission action).
- **repository**:
  - operasi query SQLAlchemy,
  - tidak memuat business rule lintas kasus.
- **schemas**:
  - validasi data masuk/keluar.
- **models**:
  - deklarasi tabel dan relasi.

Aturan tambahan:
- router tidak boleh langsung query database,
- template tidak boleh memuat business logic kompleks,
- service tidak boleh menghasilkan HTML.

---

## 5) Modul inti (MVP)

### A. Platform Core
- konfigurasi aplikasi (env-based)
- koneksi DB + session factory
- migration Alembic
- error pages generik (404/500)

### B. Auth + RBAC
- login/logout session-based
- role (`admin`, `editor`)
- permission guard action/resource

### C. Public
- home
- profile page
- news list + detail
- services list + detail
- contact

### D. Admin CMS
- dashboard ringkas
- CRUD news
- CRUD services
- settings situs

### E. Media
- upload image/file
- validasi tipe + ukuran
- media picker reusable

### F. UI System
- design tokens
- reusable components
- complete states (loading/empty/error/disabled)

### G. HTMX + Alpine
- partial update table/form/row/filter
- inline validation feedback
- modal interaction ringan

---

## 6) Urutan build (14 hari)

### Fase 0 (Hari 1) — Fondasi
- bootstrap FastAPI
- setup `core/` + DB
- Alembic init
- layout public/admin

### Fase 1 (Hari 2–3) — Design System
- route `/design-system`
- token + komponen atomik/komposit
- verifikasi komponen dipakai ulang di halaman nyata

### Fase 2 (Hari 4–5) — Modul Public
- implement modul `pages`, `news`, `services` sisi publik
- gunakan kontrak layer per modul

### Fase 3 (Hari 6) — Modul Auth + RBAC
- login/logout
- guard permission per route admin

### Fase 4 (Hari 7–9) — Modul CMS Inti
- `news` admin (CRUD + partial HTMX)
- `services` admin (CRUD + partial HTMX)
- `settings` admin

### Fase 5 (Hari 10–11) — Media + UX Polish
- upload/media picker
- toast + state handling

### Fase 6 (Hari 12–13) — Testing
- test auth
- test public critical routes
- test admin CRUD + HTMX partial

### Fase 7 (Hari 14) — Finalisasi
- seed demo data
- README quick start
- checklist reusable pass

---

## 7) Guardrail clean code (wajib)

Untuk mencegah script membengkak:

1. router target <= 200 baris/file.
2. service/repository target <= 250 baris/file.
3. template halaman target <= 150 baris/file.
4. file yang melewati batas harus dipecah per concern.
5. review PR menolak query di router dan logic berat di template.

---

## 8) Definition of Done

Boilerplate siap dipakai ulang jika:

1. clone -> setup -> migrate -> run < 10 menit.
2. struktur modul konsisten di minimal 2 domain (`news`, `services`).
3. auth + RBAC aktif.
4. minimal 2 CRUD admin stabil.
5. partial HTMX berjalan untuk create/update/list refresh.
6. test dasar jalur kritis lulus.

Lanjutan dokumen:
- detail eksekusi harian: [alur-2.md](E:/python/fast-boiler/alur-2.md)
- quality gate dan readiness rilis: [alur-3.md](E:/python/fast-boiler/alur-3.md)

---

## 9) Flow Contract: PRG + HTMX/fetch + API Standard Response

Bagian ini menjadi aturan operasional agar alur web dan API konsisten, maintainable, dan siap dipakai app lain.

### 9.1 PRG (Post/Redirect/Get) untuk halaman penuh

Wajib digunakan pada submit form non-HTMX yang menghasilkan halaman penuh.

Pola:

1. `GET` menampilkan form.
2. `POST` memproses simpan/update/delete.
3. Setelah sukses, server melakukan redirect (`303 See Other`) ke endpoint `GET`.

Contoh:

- `GET /admin/news/new` -> form create
- `POST /admin/news` -> simpan
- `303 -> GET /admin/news` atau `GET /admin/news/{id}`

Tujuan:
- mencegah double submit saat refresh,
- menjaga URL tetap bersih,
- menyederhanakan alur UX.

### 9.2 HTMX sebagai default interaksi server di web

HTMX adalah default untuk kebutuhan partial update tanpa reload penuh.

Gunakan HTMX untuk:
- filter/search/pagination list,
- refresh tabel/row/section,
- form modal create/edit,
- validasi form inline dari response server.

Standar template partial:
- `_table.html`
- `_row.html`
- `_form.html`
- `_filters.html`

Catatan:
- response HTMX berbentuk HTML partial dari Jinja,
- business logic tetap di service, query tetap di repository.

### 9.3 `fetch()` untuk kebutuhan JSON khusus

`fetch()` tidak dilarang, tetapi bukan default.

Gunakan `fetch()` ketika:
- komponen JavaScript benar-benar membutuhkan JSON,
- ada integrasi lintas layanan yang berbasis data JSON,
- ada use case async non-HTML yang tidak efisien bila dipartial-kan.

Jika use case bisa diselesaikan oleh HTMX + partial Jinja, pilih HTMX.

### 9.4 API publik/internal dengan kontrak response standar

Semua endpoint API yang ditujukan untuk konsumsi app lain wajib berada di prefix:

- `/api/v1/...`

Response sukses standar:

```json
{
  "success": true,
  "message": "OK",
  "data": {},
  "meta": {
    "request_id": "req-123",
    "timestamp": "2026-10-07T08:20:00Z",
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100
    }
  }
}
```

Response error standar:

```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "title",
        "reason": "required"
      }
    ]
  },
  "meta": {
    "request_id": "req-124",
    "timestamp": "2026-10-07T08:20:05Z"
  }
}
```

Aturan API:
- gunakan HTTP status code semantik (`200/201/400/401/403/404/422/500`),
- response shape konsisten lintas modul,
- dokumentasi OpenAPI harus tetap rapi dan dapat diuji,
- service/repository dipakai bersama oleh jalur web dan API (hindari duplikasi rule bisnis).

### 9.5 Pembagian jalur router

Setiap modul domain minimal memiliki:

- `router_public.py` (halaman publik, Jinja)
- `router_admin.py` (halaman admin, Jinja + PRG)
- `router_htmx.py` (partial HTML untuk HTMX)
- `router_api.py` (JSON API `/api/v1/...`)

Dengan pembagian ini, kontrak output menjadi jelas:
- web full page -> HTML + PRG,
- web partial -> HTML partial (HTMX),
- integrasi app lain -> JSON standar (API).
