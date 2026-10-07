Tentu. Kalau stack ini dipakai untuk **CMS website rumah sakit**, sebenarnya masing-masing punya tugas yang berbeda. Jangan sampai semuanya dianggap sebagai "framework" yang harus dipakai sekaligus.

```text
FastAPI
   │
   ├── Jinja2
   │
   ├── SQLAlchemy
   │       │
   │       └── SQLite
   │
   ├── Alembic
   │
   └── HTML
         ├── Bootstrap / Tailwind
         ├── HTMX
         └── Alpine.js
```

## 1. FastAPI — otak/backend aplikasi

**Fungsi:** menerima request browser, menjalankan logic, mengambil data database, lalu mengirim response.

Contoh:

```text
Browser
   │
   │ GET /berita
   ▼
FastAPI
   │
   ▼
Database
   │
   ▼
Jinja2
   │
   ▼
HTML
   │
   ▼
Browser
```

Contoh sederhana:

```python
@app.get("/berita")
def berita(request: Request):
    news = get_news()
    return templates.TemplateResponse(
        "news.html",
        {
            "request": request,
            "news": news
        }
    )
```

**FastAPI = backend/server.**

---

# 2. Jinja2 — membuat HTML dinamis

Jinja2 adalah **template engine**.

Misalnya database memiliki:

```text
Judul: Rumah Sakit Mengadakan Seminar Kesehatan
```

Jinja2 bisa memasukkannya ke HTML.

```jinja2
<h1>{{ article.title }}</h1>

<p>{{ article.content }}</p>
```

Untuk banyak berita:

```jinja2
{% for article in articles %}

    <h2>{{ article.title }}</h2>
    <p>{{ article.excerpt }}</p>

{% endfor %}
```

Jadi:

**Jinja2 = penghubung data Python dengan HTML.**

Ini sebenarnya bagian yang paling mirip dengan **Handlebars**.

---

# 3. SQLAlchemy — cara Python berbicara dengan database

Daripada menulis SQL terus:

```sql
SELECT * FROM news WHERE id = 10;
```

Anda bisa menggunakan SQLAlchemy.

Misalnya model:

```python
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    status = Column(String)
```

Kemudian:

```python
news = db.query(News).all()
```

SQLAlchemy yang mengurus komunikasi dengan database.

**SQLAlchemy = ORM/database layer.**

---

# 4. SQLite — database sebenarnya

Ini yang menyimpan data.

Misalnya:

```text
hospital.db
```

isinya:

```text
users
roles
permissions
pages
news
services
doctors
events
banners
gallery
documents
settings
audit_logs
```

SQLite hanya **satu file database**.

Contohnya:

```text
/data/hospital.db
```

Ini yang membuat backup sangat mudah.

```text
hospital.db
       ↓
backup
       ↓
hospital-2026-10-02.db
```

**SQLite = tempat penyimpanan data.**

---

# 5. Alembic — mengatur perubahan struktur database

Ini sering membingungkan.

Misalnya awalnya tabel `news`:

```text
news
├── id
├── title
└── content
```

Kemudian Anda ingin menambahkan:

```text
published_at
```

Jangan mengubah database secara manual.

Alembic membuat migration:

```text
001_initial.py
002_add_published_at.py
003_add_featured_image.py
```

Sehingga database bisa berkembang dengan terkontrol.

Misalnya:

```bash
alembic revision --autogenerate -m "add published_at"
alembic upgrade head
```

**Alembic = version control untuk struktur database.**

Ini sangat berguna ketika project Anda disimpan di GitHub.

---

# 6. Tailwind — tampilan

Keduanya **tidak perlu dipakai bersamaan**.

Ini pilihan:

```text
Tailwind
```

### Tailwind

Lebih fleksibel.

Contoh:

```html
<button class="px-4 py-2 bg-blue-600 text-white rounded">
    Simpan
</button>
```

Bagus kalau Anda ingin desain website yang benar-benar custom.

Tetapi untuk project CMS yang ingin cepat selesai, Bootstrap lebih praktis.

---

# 7. HTMX — membuat website terasa seperti aplikasi

Ini menarik.

Tanpa HTMX:

```text
Klik Edit
   ↓
Browser reload
   ↓
GET /admin/news/10/edit
   ↓
HTML baru
```

Dengan HTMX:

```text
Klik Edit
   ↓
HTMX request
   ↓
FastAPI
   ↓
Jinja2
   ↓
HTML fragment
   ↓
bagian halaman berubah
```

Tidak perlu React.

Misalnya:

```html
<button
    hx-get="/admin/news/10/edit"
    hx-target="#editor">
    Edit
</button>
```

FastAPI mengembalikan HTML:

```html
<form>
    ...
</form>
```

HTMX memasukkannya ke:

```html
<div id="editor"></div>
```

Jadi CMS terasa lebih modern.

**HTMX = interaksi dinamis tanpa harus membuat SPA React.**

---

# 8. Alpine.js — JavaScript kecil-kecilan

HTMX dan Alpine.js bukan hal yang sama.

**HTMX** bagus untuk komunikasi dengan server.

**Alpine.js** bagus untuk interaksi kecil di browser.

Contoh:

### Dropdown

```html
<div x-data="{ open: false }">

    <button @click="open = !open">
        Menu
    </button>

    <div x-show="open">
        Isi menu
    </div>

</div>
```

### Modal

```html
<div x-data="{ show: false }">

    <button @click="show = true">
        Hapus
    </button>

    <div x-show="show">
        Apakah yakin?
    </div>

</div>
```

Tidak perlu React hanya untuk hal seperti ini.

**Alpine.js = JavaScript ringan untuk interaksi UI.**

---

# Jadi pembagian tugasnya

Saya biasanya mengingatnya seperti ini:

```text
┌─────────────────────────────────────┐
│              BROWSER                │
│                                     │
│ Bootstrap/Tailwind → tampilan       │
│ Alpine.js          → interaksi UI  │
│ HTMX               → request AJAX  │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│              FASTAPI                │
│                                     │
│ routing                             │
│ authentication                      │
│ RBAC                                │
│ business logic                      │
└──────────────────┬──────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
      Jinja2           SQLAlchemy
          │                 │
          ▼                 ▼
        HTML             SQLite
                            │
                            ▲
                         Alembic
```

---

# Contoh nyata: Admin membuat berita

Misalnya operator rumah sakit membuka:

```text
/admin/news/create
```

### 1. Bootstrap

Membuat form:

```text
┌───────────────────────────────────┐
│ Tambah Berita                     │
│                                   │
│ Judul                             │
│ [_____________________________]   │
│                                   │
│ Isi Berita                        │
│ [_____________________________]   │
│                                   │
│ Gambar                            │
│ [ Choose File ]                   │
│                                   │
│        [ Simpan ]                 │
└───────────────────────────────────┘
```

### 2. Alpine.js

Menangani preview gambar:

```text
Choose File
     ↓
Preview gambar
```

tanpa request ke server.

### 3. HTMX

Ketika klik:

```text
[Simpan]
```

HTMX bisa mengirim form ke:

```text
POST /admin/news
```

### 4. FastAPI

Menerima:

```text
title
content
image
```

kemudian menjalankan validasi dan logic.

### 5. SQLAlchemy

Menyimpan:

```text
News(
    title=...,
    content=...
)
```

ke SQLite.

### 6. Jinja2

Menampilkan kembali:

```text
Berita berhasil disimpan
```

### 7. SQLite

Data permanen berada di:

```text
hospital.db
```

### 8. Alembic

Kalau enam bulan kemudian Anda menambahkan:

```text
seo_title
seo_description
```

perubahan database dicatat sebagai migration.

---

# Apakah semuanya wajib?

**Tidak.**

Untuk project pertama saya malah menyederhanakan:

### Wajib

```text
FastAPI
Jinja2
SQLAlchemy
SQLite
Alembic
Bootstrap
```

### Opsional

```text
HTMX
Alpine.js
```

Tetapi saya **cukup merekomendasikan HTMX + Alpine.js**, karena keduanya ringan dan bisa menghilangkan kebutuhan React untuk CMS.

---

# Stack final yang saya rekomendasikan untuk Anda

Untuk website RS seperti Sardjito:

```text
Backend
──────────────
FastAPI

Template
──────────────
Jinja2

Database
──────────────
SQLite

ORM
──────────────
SQLAlchemy

Database Migration
──────────────
Alembic

Frontend UI
──────────────
Bootstrap 5

Dynamic UI
──────────────
HTMX
Alpine.js

Web Server
──────────────
Caddy / Nginx

Deployment
──────────────
Ubuntu / Raspberry Pi / VM

Repository
──────────────
GitHub
```

Dan **tidak perlu Node.js**.

Bahkan saya akan menghindari npm kalau tujuan Anda adalah **project CMS yang sederhana, mudah dibaca AI, hemat context/token, dan mudah Anda rawat sendiri**.

Satu catatan: **Tailwind pilih salah satu**


===========================================================================================================


Bisa, dan **justru saya sangat menyarankan itu** sebelum Anda mulai membuat CMS-nya.

Yang Anda maksud sebenarnya adalah membuat **UI Design System / Component Showcase** terlebih dahulu. Jadi Anda memiliki satu halaman khusus yang berisi seluruh komponen visual. Setelah tampilannya disepakati, komponen tersebut baru digunakan oleh halaman publik dan CMS.

### Arsitektur yang saya sarankan

```text
                 DESIGN SYSTEM
                       │
          ┌────────────┴────────────┐
          │                         │
     Public Website              CMS Admin
          │                         │
          └────────────┬────────────┘
                       │
                Shared Components
                       │
              Tailwind + Jinja2
```

Misalnya:

```text
/templates/
│
├── components/
│   ├── buttons.html
│   ├── cards.html
│   ├── forms.html
│   ├── modal.html
│   ├── navbar.html
│   ├── footer.html
│   ├── alerts.html
│   ├── badges.html
│   ├── tables.html
│   ├── pagination.html
│   ├── breadcrumbs.html
│   └── ...
│
├── layouts/
│   ├── public.html
│   └── admin.html
│
└── design-system/
    └── index.html
```

Kemudian satu URL:

```text
/design-system
```

yang isinya **semua komponen**.

---

## Isi halaman `/design-system`

Saya akan membuatnya cukup lengkap:

```text
DESIGN SYSTEM
│
├── 01 Colors
│
├── 02 Typography
│
├── 03 Spacing
│
├── 04 Buttons
│
├── 05 Links
│
├── 06 Icons
│
├── 07 Badges
│
├── 08 Alerts
│
├── 09 Cards
│
├── 10 Forms
│
├── 11 Input
│
├── 12 Select
│
├── 13 Checkbox
│
├── 14 Radio
│
├── 15 Switch
│
├── 16 File Upload
│
├── 17 Search
│
├── 18 Tables
│
├── 19 Pagination
│
├── 20 Breadcrumb
│
├── 21 Tabs
│
├── 22 Accordion
│
├── 23 Modal
│
├── 24 Drawer
│
├── 25 Dropdown
│
├── 26 Tooltip
│
├── 27 Toast
│
├── 28 Popup
│
├── 29 Navbar
│
├── 30 Sidebar
│
├── 31 Hero
│
├── 32 Statistics
│
├── 33 Timeline
│
├── 34 Gallery
│
├── 35 News Card
│
├── 36 Doctor Card
│
├── 37 Service Card
│
├── 38 Footer
│
├── 39 Sticky Elements
│
└── 40 Responsive Test
```

Dengan demikian Anda bisa membuka:

```text
https://domain-anda.com/design-system
```

dan langsung melihat **bahasa visual website Anda**.

---

# Bahkan saya sarankan ada "Interactive Playground"

Misalnya bagian Colors:

```text
COLORS

Primary
┌────────────┐
│            │
│  #0F766E   │
│            │
└────────────┘

Secondary
┌────────────┐
│            │
│  #0EA5E9   │
│            │
└────────────┘

Success
┌────────────┐
│            │
│  #16A34A   │
│            │
└────────────┘
```

Kemudian Typography:

```text
Typography

Heading 1
Rumah Sakit Kami

Heading 2
Pelayanan Unggulan

Heading 3
Informasi Kesehatan

Body
Rumah sakit memberikan pelayanan...

Small
Informasi terakhir diperbarui...
```

---

# Forms juga dibuat lengkap

Misalnya:

```text
FORM COMPONENTS

Text
[ Nama lengkap                         ]

Email
[ user@example.com                    ]

Password
[ •••••••••••                         ]

Select
[ Pilih layanan                 ▼    ]

Date
[ 06/10/2026                       ]

Textarea
┌────────────────────────────────────┐
│                                    │
│                                    │
└────────────────────────────────────┘

Checkbox
☑ Saya menyetujui ketentuan

Radio
◉ Rawat Jalan
○ Rawat Inap

Switch
●────────  Aktif
```

Dan **jangan hanya membuat keadaan normal**.

Buat juga:

```text
Normal
Focus
Hover
Disabled
Error
Success
Loading
Readonly
Required
```

Ini sangat penting untuk CMS.

---

# Button juga dibuat semua state

```text
BUTTONS

[ Primary ]
[ Secondary ]
[ Success ]
[ Danger ]
[ Warning ]
[ Ghost ]
[ Outline ]

States:

[ Normal ]
[ Hover ]
[ Disabled ]
[ Loading... ]

Sizes:

[ Small ]
[ Medium ]
[ Large ]

Icon:

[ + Tambah Berita ]

[ ✏ Edit ]

[ 🗑 Hapus ]
```

Jadi nanti ketika Anda membuat CMS:

```text
Tambah Berita
Edit Berita
Hapus Berita
Simpan
Batal
Publish
Draft
```

semuanya menggunakan komponen yang sama.

---

# Modal

Buat beberapa contoh:

```text
┌─────────────────────────────────────┐
│ Hapus Berita                    ×  │
├─────────────────────────────────────┤
│                                     │
│ Apakah Anda yakin ingin menghapus   │
│ berita ini?                         │
│                                     │
├─────────────────────────────────────┤
│                 [Batal] [Hapus]     │
└─────────────────────────────────────┘
```

Kemudian:

* confirmation modal
* information modal
* form modal
* large modal
* fullscreen modal

---

# Popup / Toast

Contohnya:

```text
                         ┌───────────────────────┐
                         │ ✓ Berita berhasil     │
                         │   disimpan            │
                         └───────────────────────┘
```

Buat:

```text
Success
Info
Warning
Error
```

---

# Sticky

Misalnya website RS:

```text
┌─────────────────────────────────────┐
│ Logo    Profil Layanan Informasi    │ ← sticky
└─────────────────────────────────────┘
```

Kemudian:

```text
                       ↑
                       │
                   Back to top
```

Atau:

```text
┌─────────────────────────────────────┐
│ 📞 Emergency     📅 Appointment    │ ← sticky bottom mobile
└─────────────────────────────────────┘
```

Ini bisa diuji langsung di halaman design system.

---

# Responsive test juga penting

Saya akan membuat satu bagian:

```text
RESPONSIVE

┌──────────────────────────────┐
│ Desktop 1440px              │
│                              │
│                              │
└──────────────────────────────┘

┌────────────────────┐
│ Tablet 768px       │
│                    │
└────────────────────┘

┌──────────────┐
│ Mobile 390px │
│              │
└──────────────┘
```

Kemudian semua komponen harus dicek:

```text
Mobile
Tablet
Desktop
Large Desktop
```

---

# Yang paling penting: jangan hanya membuat halaman demo

Komponennya harus benar-benar menjadi **komponen reusable**.

Misalnya:

```text
components/
    button.html
```

Kemudian di halaman lain:

```jinja2
{% include "components/button.html" %}
```

Atau lebih bagus lagi membuat macro Jinja:

```jinja2
{{ button(
    text="Simpan",
    variant="primary",
    size="md"
) }}
```

Sehingga CMS nanti tidak membuat button dengan CSS sendiri-sendiri.

---

# Design token

Saya juga menyarankan sejak awal membuat:

```text
design-tokens.css
```

misalnya:

```css
:root {
    --color-primary: ...;
    --color-secondary: ...;
    --color-success: ...;
    --color-danger: ...;

    --font-heading: ...;
    --font-body: ...;

    --radius-sm: ...;
    --radius-md: ...;
    --radius-lg: ...;

    --spacing-xs: ...;
    --spacing-sm: ...;
    --spacing-md: ...;
    --spacing-lg: ...;
}
```

Kalau nanti direktur RS mengatakan:

> "Warna hijau terlalu gelap, ubah menjadi warna identitas rumah sakit."

Anda tidak perlu mengubah 100 halaman.

Cukup:

```text
--color-primary
```

dan seluruh website ikut berubah.

---

# Bahkan saya akan membuat dua tema

```text
THEME

○ Light
○ Dark
```

Walaupun website RS mungkin default-nya light.

Kemudian bisa diuji:

```text
Primary
Secondary
Success
Warning
Danger
Background
Surface
Text
Border
```

agar kombinasi warnanya konsisten.

---

# Struktur project akhirnya

Saya akan arahkan seperti ini:

```text
hospital-cms/
│
├── app/
│   ├── main.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   │
│   └── templates/
│       │
│       ├── components/
│       │   ├── button.html
│       │   ├── card.html
│       │   ├── form.html
│       │   ├── modal.html
│       │   ├── table.html
│       │   ├── alert.html
│       │   └── ...
│       │
│       ├── layouts/
│       │   ├── public.html
│       │   └── admin.html
│       │
│       ├── public/
│       ├── admin/
│       │
│       └── design-system/
│           └── index.html
│
├── static/
│   ├── css/
│   │   └── app.css
│   ├── js/
│   └── images/
│
├── media/
├── data/
│   └── hospital.db
│
├── alembic/
├── tests/
│
├── tailwind.config.js
└── README.md
```

## Dan urutan pembangunannya saya ubah sedikit

Jangan langsung membuat CMS.

**Tahap 1 — Design System**

```text
Colors
Typography
Spacing
Buttons
Cards
Forms
Tables
Modal
Navbar
Footer
Popup
Toast
Sticky
Responsive
```

↓

**Tahap 2 — Component Library**

```text
button.html
card.html
modal.html
form.html
table.html
...
```

↓

**Tahap 3 — Public Layout**

```text
Header
Navbar
Hero
Content
Footer
```

↓

**Tahap 4 — CMS Layout**

```text
Sidebar
Topbar
Dashboard
Forms
Tables
Modal
```

↓

**Tahap 5 — Database**

```text
SQLAlchemy
SQLite
Alembic
```

↓

**Tahap 6 — CMS**

```text
Pages
News
Services
Doctors
Events
Gallery
Media
Users
Settings
```

Ya. Saya akan tetapkan rekomendasi arsitekturnya seperti ini untuk **website + CMS rumah sakit** Anda. Fokusnya: sederhana, cepat dikembangkan, mudah dirawat, SSR, dan tidak perlu SPA.

## Rekomendasi final

```text
FastAPI
   │
   ├── Jinja2
   │      └── HTML / reusable components
   │
   ├── SQLAlchemy
   │      └── Database access
   │
   ├── SQLite
   │      └── hospital.db
   │
   └── Alembic
          └── Database migration

Frontend
   │
   ├── Tailwind CSS
   │      └── Design system / responsive UI
   │
   ├── HTMX
   │      └── Server interaction / partial rerender
   │
   └── Alpine.js
          └── Local UI interaction
```

### 1. FastAPI → backend utama

Semua business logic tetap di Python.

```text
Browser
   ↓
FastAPI Router
   ↓
Service
   ↓
SQLAlchemy
   ↓
SQLite
```

Tidak perlu membuat Node.js backend terpisah.

---

## 2. Jinja2 → rendering HTML

Jinja2 menjadi mesin template utama.

Contohnya:

```text
templates/
├── layouts/
├── components/
├── public/
├── admin/
└── design-system/
```

Gunakan **reusable components**, bukan HTML yang berulang-ulang.

Misalnya:

```text
components/
├── button.html
├── card.html
├── modal.html
├── alert.html
├── table.html
├── pagination.html
├── form.html
└── navbar.html
```

---

# 3. HTMX → komunikasi Browser ↔ Server

Ini menjadi bagian penting.

Untuk CMS, **gunakan HTMX sebagai default sebelum `fetch()`**.

Misalnya:

```html
<button
    hx-get="/admin/news/123/edit"
    hx-target="#modal"
    hx-swap="innerHTML">
    Edit
</button>
```

FastAPI mengembalikan HTML Jinja:

```text
FastAPI
   ↓
Jinja2 partial
   ↓
HTML fragment
   ↓
HTMX
   ↓
replace component
```

Jadi tidak perlu membuat JSON hanya untuk mengganti sebuah tabel atau form.

---

# 4. Rerender component → HTMX + Jinja partial

Ini pola yang saya rekomendasikan sebagai standar.

Misalnya:

```text
admin/news/index.html

┌─────────────────────────────┐
│ Daftar Berita               │
│                             │
│ [Tambah]                    │
│                             │
│ ┌─────────────────────────┐ │
│ │ _table.html              │ │
│ │                         │ │
│ │ Berita 1                │ │
│ │ Berita 2                │ │
│ │ Berita 3                │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

Setelah delete:

```text
DELETE /admin/news/123
        ↓
FastAPI
        ↓
database berubah
        ↓
render _table.html
        ↓
HTMX
        ↓
#news-table diganti
```

**Tidak perlu `location.reload()`.**

**Tidak perlu React state.**

**Tidak perlu `fetch()` + manipulasi DOM manual.**

---

# 5. Alpine.js → interaksi lokal browser

Alpine.js jangan digunakan sebagai pengganti HTMX.

Pembagiannya:

### HTMX

```text
Browser ↔ Server
```

Untuk:

* CRUD
* search
* filter
* pagination
* submit form
* delete
* load data
* modal yang datanya dari server
* refresh tabel
* partial rerender

### Alpine.js

```text
Browser ↔ Browser
```

Untuk:

* dropdown
* modal open/close
* tabs
* accordion
* show/hide
* toggle
* mobile menu
* preview sederhana
* state UI kecil

Contoh:

```html
<div x-data="{ open: false }">

    <button @click="open = true">
        Tambah Berita
    </button>

    <div x-show="open">
        ...
    </div>

</div>
```

Tidak ada request server.

---

# 6. `fetch()` → tetap tersedia, tetapi bukan default

Saya tidak menghilangkan `fetch()`.

Gunakan kalau memang membutuhkan **JSON/API**.

Misalnya:

```javascript
const response = await fetch("/api/statistics");
const data = await response.json();
```

Cocok untuk:

* chart
* data JSON
* integrasi API eksternal
* komponen yang benar-benar membutuhkan JavaScript
* modul yang nantinya mungkin menjadi SPA

Tetapi untuk CMS biasa:

```text
POST → simpan → HTML
```

lebih sederhana menggunakan HTMX.

---

# 7. POST harus menggunakan PRG

Ini penting untuk masalah Anda tentang:

> halaman POST direfresh sehingga POST bisa terkirim lagi.

Untuk form biasa:

```text
GET /admin/news/create
        ↓
form
        ↓
POST /admin/news
        ↓
303 Redirect
        ↓
GET /admin/news
```

FastAPI:

```python
return RedirectResponse(
    url="/admin/news",
    status_code=303
)
```

Dengan demikian ketika user menekan Refresh:

```text
GET /admin/news
```

bukan mengulangi:

```text
POST /admin/news
```

**PRG tetap menjadi best practice**, bahkan jika Anda memakai HTMX.

---

# 8. Tailwind CSS → UI utama

Untuk website rumah sakit, saya tetap memilih **Tailwind CSS**.

Alasannya:

* desain lebih bebas
* mudah membuat identitas visual rumah sakit
* responsive
* mudah membuat design system
* tidak terlalu terlihat seperti template Bootstrap standar
* cocok untuk membuat public website dan CMS dengan bahasa visual yang sama

Tetapi gunakan **design tokens** agar tidak menjadi kumpulan class yang tidak konsisten.

Misalnya:

```text
Primary
Secondary
Success
Warning
Danger
Neutral

Typography
Spacing
Radius
Shadow
Container
Breakpoint
```

---

# 9. Design System dibuat paling awal

Ini saya anggap sebagai langkah pertama development.

Buat:

```text
/design-system
```

Isinya:

```text
Colors
Typography
Spacing
Buttons
Links
Badges
Alerts
Cards

Input
Textarea
Select
Checkbox
Radio
Switch
File Upload
Search

Table
Pagination
Tabs
Accordion
Breadcrumb

Modal
Drawer
Dropdown
Tooltip
Toast

Navbar
Sidebar
Hero
Statistics
News Card
Doctor Card
Service Card
Gallery
Footer

Responsive states
Loading
Empty state
Error state
Disabled state
```

Tetapi yang penting:

> **Design System bukan sekadar halaman demo.**

Komponen yang ditampilkan di `/design-system` harus merupakan **komponen yang benar-benar dipakai website**.

---

# 10. Struktur Jinja yang saya rekomendasikan

```text
templates/
│
├── layouts/
│   ├── public.html
│   └── admin.html
│
├── components/
│   ├── buttons/
│   ├── forms/
│   ├── cards/
│   ├── tables/
│   ├── modals/
│   ├── alerts/
│   ├── navigation/
│   └── pagination/
│
├── public/
│   ├── home.html
│   ├── profile.html
│   ├── services.html
│   ├── doctors.html
│   ├── news.html
│   └── contact.html
│
├── admin/
│   ├── dashboard/
│   ├── pages/
│   ├── news/
│   │   ├── index.html
│   │   ├── _table.html
│   │   ├── _form.html
│   │   └── _row.html
│   ├── services/
│   ├── doctors/
│   ├── gallery/
│   ├── documents/
│   └── settings/
│
└── design-system/
    └── index.html
```

Perhatikan pola:

```text
_table.html
_form.html
_row.html
```

Itulah yang nantinya banyak digunakan HTMX.

---

# 11. Arsitektur frontend akhirnya

Saya akan menggunakan aturan sederhana ini:

```text
                    Jinja2
                       │
                       ▼
                    HTML
                       │
          ┌────────────┴────────────┐
          │                         │
        HTMX                    Alpine.js
          │                         │
          ▼                         ▼
   Server interaction          UI interaction
          │                         │
          ▼                         ▼
       FastAPI                  Browser
```

Sedangkan:

```text
fetch()
```

hanya digunakan apabila memang ada kebutuhan **JSON/API dari JavaScript**.

---

# 12. Stack final

Jadi saya akan mengunci rekomendasinya menjadi:

| Layer              | Teknologi                    |
| ------------------ | ---------------------------- |
| Backend            | **FastAPI**                  |
| Template           | **Jinja2**                   |
| ORM                | **SQLAlchemy**               |
| Database           | **SQLite**                   |
| Migration          | **Alembic**                  |
| CSS                | **Tailwind CSS**             |
| Server interaction | **HTMX**                     |
| UI interaction     | **Alpine.js**                |
| JSON/API khusus    | **fetch()**                  |
| Auth CMS           | Session-based authentication |
| RBAC               | Role + Permission            |
| Web server         | Caddy/Nginx                  |
| Deployment         | Ubuntu/Docker                |
| Repository         | GitHub                       |
| Backup             | SQLite + media + config      |

### Prinsip utamanya

```text
Jangan membuat SPA kalau tidak diperlukan.

Jangan menggunakan fetch() kalau HTMX cukup.

Jangan menggunakan Alpine.js untuk komunikasi server.

Jangan menggunakan JavaScript untuk pekerjaan yang bisa dilakukan
server + Jinja2.

Jangan membuat komponen hanya untuk design-system;
buat komponen reusable yang benar-benar dipakai aplikasi.
```

Dengan pendekatan ini, **public website dan CMS tetap terasa modern dan interaktif**, tetapi arsitekturnya jauh lebih sederhana daripada FastAPI + React/Vite. Dan kalau suatu saat ada satu modul yang memang membutuhkan SPA/JavaScript kompleks, modul tersebut bisa ditambahkan tanpa harus mengubah seluruh website.
