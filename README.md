# Fast Boiler

Reusable FastAPI boilerplate with modular monolith structure and PRG + HTMX + standard API response flow.

## Quick start

1. Create and activate virtual environment.
2. Copy env:
   - Windows PowerShell: `Copy-Item .env.example .env`
3. Install dependencies:
   - `pip install -e .`
   - atau jika Anda biasa pakai requirement file: `pip install -r requirements.txt`
4. Install dependency frontend (Tailwind CLI):
   - `npm install`
5. Build CSS production:
   - `npm run build:css`
6. Untuk development CSS live:
   - `npm run watch:css`
7. (Opsional tapi direkomendasikan) jalankan migration Alembic:
   - `alembic upgrade head`
8. Seed data awal:
   - `python scripts/seed.py`
9. Run app:
   - `uvicorn app.main:app --reload`
10. Open:
   - Landing page: `/`
   - Admin dashboard: `/admin`
   - Design system: `/design-system`
   - Public news: `/news`
   - Public services: `/services`
   - Public pages: `/pages`
   - Admin news: `/admin/news`
   - Admin services: `/admin/services`
   - Admin pages: `/admin/pages`
   - Admin drafts manager: `/admin/drafts`
   - Admin media upload: `/admin/media`
   - Admin canvas editor: `/admin/canvas`
   - Admin logger table: `/admin/logger`
   - Admin settings: `/admin/settings`
   - Login: `/auth/login` (default: `admin` / `admin123`)
   - API docs: `/docs`

## 🔶 Highlight: Penyimpanan Draft & Manajemen Draft

> Fitur ini dirancang agar input admin **tetap aman** saat session expire, browser tertutup, atau user pindah device.

### Draft disimpan di server (bukan hanya local browser)
- Draft form `news` dan `services` di-autosave ke database per user.
- Key draft memakai pola `entity_type + entity_key` (contoh: `news + create:new`, `services + edit:12`).
- Draft bisa dipulihkan lintas login/device selama user sama.

### Endpoint autosave draft
- `POST /api/v1/drafts` → simpan/update draft
- `GET /api/v1/drafts?entity_type=...&entity_key=...` → ambil draft spesifik
- `DELETE /api/v1/drafts?entity_type=...&entity_key=...` → hapus draft saat submit sukses
- `GET /api/v1/drafts/recent?limit=10&entity_type=news` → daftar draft terbaru

### Manajemen draft di admin
- Halaman khusus: `/admin/drafts`
- Fitur: filter entity, sorting newest/oldest, resume draft, delete per item, bulk delete.
- Dashboard admin menampilkan recent drafts untuk quick resume.

### Guardrail performa & retention
- `DRAFT_MAX_PAYLOAD_CHARS` membatasi ukuran payload draft.
- `DRAFT_MIN_SAVE_INTERVAL_SECONDS` mencegah autosave terlalu sering (throttle).
- `DRAFT_RETENTION_DAYS` + script cleanup untuk menghapus draft lama:
  - `python scripts/cleanup_drafts.py`

## Current implemented module

- `news` with:
  - public routes,
  - admin PRG routes,
  - HTMX partial routes,
  - API `/api/v1/news`,
  - admin UX: duplicate item, autoslug, unsaved-changes warning, server-side draft autosave/restore, autosave status indicator, quick resume draft.
  - admin list: search + sort + status filter + pagination controls (prev/next) reusable.
- `services` with:
  - public routes,
  - admin PRG routes,
  - HTMX partial routes,
  - API `/api/v1/services`,
  - admin UX: duplicate item, autoslug, unsaved-changes warning, server-side draft autosave/restore, autosave status indicator, quick resume draft.
  - admin list: search + sort + status filter + pagination controls (prev/next) reusable.
- `auth` with:
  - login/logout session,
  - admin route protection.
- `media` with:
  - API upload endpoint (`/api/v1/media/upload`),
  - API list endpoint (`/api/v1/media/list`),
  - whitelist validasi tipe file (extension + MIME),
  - validasi ukuran file maksimal via env,
  - reusable media picker component dipakai di media/news/services form.
- `pages` with:
  - public routes (`/pages`, `/pages/{slug}`),
  - admin PRG routes (`/admin/pages`),
  - API `/api/v1/pages`,
  - status draft/published + slug uniqueness,
  - admin list: search + sort + status filter + pagination.
- `settings` with:
  - admin settings form (`/admin/settings`) untuk `site_name`, `site_tagline`, `contact_email`,
  - API read/update (`/api/v1/settings/site`),
  - homepage hero membaca nilai settings agar branding bisa diganti tanpa ubah kode template.
- `logger` with:
  - request log persistence ke database (`request_logs`) dari middleware,
  - admin table (`/admin/logger`) dengan pagination + search + filter level + filter status group,
  - delete per item, delete selected, dan delete current page,
  - retention cleanup (hapus log lama berdasarkan `keep_days` dan/atau batasi `max_rows`),
  - export Excel dari tabel logger dengan filter aktif.

## Design system reusable components

- Atomic reusable:
  - button (`.btn-primary`, `.btn-outline`, `.btn-danger`, disabled, loading),
  - input/select/textarea (`.input-base` + focus/error state),
  - form essentials components (`components/forms/*`): input group, checkbox, radio group, switch, file input, date range, multi select,
  - badge/status macro (`components/status/_macros.html`),
  - alert reusable (`components/ui/_alert.html`).
- Composite reusable:
  - navigation (`components/navigation/*`): breadcrumb, tabs,
  - pagination (`components/pagination/_controls.html`),
  - data display (`components/data/*`): stats card, sortable header, timeline/log row, table toolbar (bulk + column toggle),
  - empty state (`components/ui/_empty_state.html`),
  - toast (`components/ui/_toast.html`),
  - skeleton loader (`components/ui/_skeleton.html`),
  - dropdown action menu (`components/ui/_dropdown_menu.html`),
  - confirmation modal pattern (`components/ui/_confirm_action.html`),
  - theme switcher (`components/ui/_theme_switcher.html`),
  - shared footer (`components/ui/_site_footer.html`),
  - modal skeleton (`components/ui/_modal.html`).

Applied examples:
- Admin News memakai breadcrumb + table toolbar utilities (`/admin/news` dan `/admin/news/new`).
- Admin Settings memakai breadcrumb + tabs guidance (`/admin/settings`).
- Admin Services memakai breadcrumb + table toolbar utilities (`/admin/services` dan `/admin/services/new`).
- Admin Pages memakai breadcrumb + table toolbar utilities (`/admin/pages` dan `/admin/pages/new`).
- Setiap tabel admin utama menyediakan tombol Export Excel (news, services, pages, logger, drafts, dashboard recent drafts/canvas).

## Environment variables

Base variables tersedia di [.env.example](E:/python/fast-boiler/.env.example):
- `APP_NAME`
- `APP_ENV`
- `LOG_LEVEL`
- `SECRET_KEY`
- `DB_URL`
- `SESSION_COOKIE_NAME`
- `SESSION_MAX_AGE`
- `SESSION_SAME_SITE`
- `SESSION_HTTPS_ONLY`
- `MEDIA_DIR`
- `MEDIA_MAX_SIZE_BYTES`
- `MEDIA_ALLOWED_EXTENSIONS`
- `MEDIA_ALLOWED_MIME_TYPES`
- `DRAFT_RETENTION_DAYS`
- `DRAFT_MAX_PAYLOAD_CHARS`
- `DRAFT_MIN_SAVE_INTERVAL_SECONDS`
- `CANVAS_MAX_PAYLOAD_CHARS`

Server-side draft API (autosave form admin):
- `POST /api/v1/drafts`
- `GET /api/v1/drafts?entity_type=...&entity_key=...`
- `DELETE /api/v1/drafts?entity_type=...&entity_key=...`
- `GET /api/v1/drafts/recent?limit=10&entity_type=news`

Admin drafts manager:
- `/admin/drafts` untuk filter, sort (newest/oldest), resume, delete manual, dan bulk delete draft terpilih.

Server-side canvas API (save/load JSON):
- `PUT /api/v1/canvas`
- `GET /api/v1/canvas?document_key=default`
- `GET /api/v1/canvas/documents?limit=50`
- `PATCH /api/v1/canvas` (rename key + update title)
- `DELETE /api/v1/canvas?document_key=...`

Canvas admin (`/admin/canvas`) sekarang mendukung multi-document per user, autosave debounce ke server, export/import JSON, manual load/save, rename, dan delete dokumen.
Autosave canvas juga dilindungi conflict guard (HTTP 409) agar perubahan lama dari tab/device lain tidak menimpa versi terbaru tanpa konfirmasi.

Audit fields:
- `news` dan `services` menyimpan `created_by` dan `updated_by` untuk jejak perubahan dari admin.

RBAC canvas:
- `canvas.read` untuk membaca daftar/muatan dokumen.
- `canvas.manage` untuk simpan/rename/delete dokumen canvas.

Logging:
- request/response logging aktif via middleware (status + durasi + request_id).
- exception/validation logging aktif untuk troubleshooting API.

Cleanup expired drafts:
- `python scripts/cleanup_drafts.py`

## Tailwind status

Tailwind sudah aktif via CLI build (tanpa CDN), dengan file utama:
- input: [tailwind.css](E:/python/fast-boiler/assets/css/tailwind.css)
- output: [app.css](E:/python/fast-boiler/static/css/app.css)
- config: [tailwind.config.js](E:/python/fast-boiler/tailwind.config.js)
- scripts: [package.json](E:/python/fast-boiler/package.json)

Tema warna sudah terhubung di layout:
- [public.html](E:/python/fast-boiler/app/templates/layouts/public.html)
- [admin.html](E:/python/fast-boiler/app/templates/layouts/admin.html)

## Ganti warna tema dengan mudah

Ada 2 cara:

1. Ubah token warna runtime lewat `.env` (direkomendasikan per deployment):
   - `THEME_COLOR_PAGE`
   - `THEME_COLOR_SURFACE`
   - `THEME_COLOR_TEXT`
   - `THEME_COLOR_MUTED`
   - `THEME_COLOR_BORDER`
   - `THEME_COLOR_BRAND`
   - `THEME_COLOR_BRAND_FOREGROUND`
2. Tambah preset tema hardcoded dengan selector:
   - `[data-theme="nama-tema"] { ... }`
   - lokasi: [tailwind.css](E:/python/fast-boiler/assets/css/tailwind.css)

Kemudian build ulang:
- `npm run build:css`

### Kapan pakai `.env` vs hardcode?

- Pakai `.env` jika Anda ingin mengganti branding warna per server/proyek tanpa edit template.
- Pakai hardcode di `tailwind.css` untuk preset tema UI (mis. tombol toggle Default/Emerald/Violet) yang memang ingin dibawa di source code.

## Preset tema siap pakai

Saya sudah tambahkan 2 preset `.env` inspirasi visual:
- [sardjito-like](E:/python/fast-boiler/.env.theme-sardjito-like.example)
- [aksara-like](E:/python/fast-boiler/.env.theme-aksara-like.example)
- [corporate-neutral](E:/python/fast-boiler/.env.theme-corporate-neutral.example)

Cara pakai cepat (PowerShell):

1. Pilih preset:
   - `Copy-Item .env.theme-sardjito-like.example .env`
   - atau `Copy-Item .env.theme-aksara-like.example .env`
   - atau `Copy-Item .env.theme-corporate-neutral.example .env`
2. Build ulang CSS:
   - `npm run build:css`
3. Restart server:
   - `uvicorn app.main:app --reload`

Jika ingin tweak kecil, edit langsung nilai `THEME_COLOR_*` di [.env](E:/python/fast-boiler/.env).

## Flow contract (ringkasan developer)

1. **Halaman full web**: gunakan PRG untuk operasi tulis (`POST` -> `303` -> `GET`).
2. **Interaksi parsial web**: gunakan HTMX, response wajib HTML partial.
3. **Integrasi app lain**: gunakan endpoint `/api/v1/*` dengan response JSON standar (`success`, `message`, `data/error`, `meta`).
4. **Business logic** tetap di service dan query tetap di repository, baik untuk web maupun API.

## Cara menambah domain baru dari pola `news`

Contoh domain baru: `events`.

1. Buat folder modul:
   - `app/modules/events/`
2. Buat file layer wajib:
   - `models.py`
   - `schemas.py`
   - `repository.py`
   - `service.py`
   - `router_public.py`
   - `router_admin.py`
   - `router_htmx.py`
   - `router_api.py`
3. Ikuti kontrak endpoint:
   - public page (`/events`, `/events/{slug}`)
   - admin PRG (`/admin/events...`)
   - htmx partial (`/admin/events/partials/...`)
   - api (`/api/v1/events...`)
4. Buat template:
   - `app/templates/public/events/index.html`
   - `app/templates/public/events/detail.html`
   - `app/templates/admin/events/index.html`
   - `app/templates/admin/events/_table.html`
   - `app/templates/admin/events/_row.html`
   - `app/templates/admin/events/_form.html`
   - `app/templates/admin/events/_filters.html`
5. Reuse komponen bersama:
   - page header: `components/marketing/_page_header.html`
   - status badge: `components/status/_macros.html`
   - CTA footer: `components/marketing/_cta_footer.html`
6. Registrasikan router di [main.py](E:/python/fast-boiler/app/main.py).
7. Tambahkan migration untuk tabel baru.
8. Tambahkan test minimum:
   - public list/detail + 404
   - admin auth + PRG create
   - htmx partial response
   - api list/detail + error shape
