# Pengujian Modul Login & Register — Quiz Pengujian Piranti Lunak

Pengujian otomatis berbasis **Selenium WebDriver + PyTest** terhadap dua modul
aplikasi web PHP: **Login** dan **Register**, lengkap dengan **Stub**,
**Driver** pengujian, dan **CI/CD pipeline GitHub Actions**.

Aplikasi yang diuji berasal dari <https://github.com/hermanka/quiz-pengupil>.

---

## Ringkasan Hasil

| Metrik | Nilai |
|---|---|
| Total test case | **24** |
| Lulus | **17** |
| Gagal | **7** |
| Cacat unik ditemukan | **7** (6 aktif + 1 laten) |

> Pipeline CI sengaja dibiarkan **merah**. Test ditulis berdasarkan perilaku
> yang *seharusnya* terjadi, bukan perilaku kode saat ini, sehingga kegagalan
> merupakan temuan cacat yang valid — bukan test yang salah tulis. Kode modul
> `login.php` dan `register.php` **tidak diubah sama sekali**.

Rincian lengkap ada pada [docs/Laporan_Pengujian.pdf](docs/Laporan_Pengujian.pdf).

---

## Struktur Repository

```
.
├─ login.php              # SUT — modul Login (tidak diubah dari repo asal)
├─ register.php           # SUT — modul Register (tidak diubah dari repo asal)
├─ koneksi.php            # konfigurasi DB, dibuat env-aware untuk CI
├─ style.css
├─ index.php              # STUB — dashboard, tujuan redirect kedua modul
├─ logout.php             # STUB — pembersih session untuk test session guard
├─ db/quiz_pengupil.sql   # skema + data awal
├─ tests/
│  ├─ conftest.py         # DRIVER — fixture DB, browser, dan data uji
│  ├─ pages.py            # Page Object modul Login, Register, dan stub
│  ├─ testdata.py         # data uji & pesan yang diharapkan
│  ├─ test_login.py       # 12 test case modul Login
│  └─ test_register.py    # 12 test case modul Register
├─ .github/workflows/ci.yml
└─ docs/
   ├─ laporan.md
   └─ Laporan_Pengujian.pdf
```

---

## Stub dan Driver

**Stub — `index.php` dan `logout.php`**

`login.php` dan `register.php` mengakhiri alur suksesnya dengan
`header('Location: index.php')`, tetapi `index.php` **tidak ada** pada
repository asal — jalur sukses kedua modul bermuara ke HTTP 404 dan tidak dapat
diverifikasi. `readme.md` repo asal pun menyatakan *"Diperlukan Stub untuk
menguji modul"*.

`index.php` adalah stub dashboard yang tidak memuat logika bisnis apa pun. Ia
hanya membaca `$_SESSION` dan mengeksposnya lewat hook DOM yang stabil
(`#stub-dashboard`, `#stub-username`, `body[data-authenticated]`) sehingga
skrip Selenium dapat memverifikasi keberhasilan redirect dan pembentukan
session. `logout.php` menyediakan transisi "sudah login → belum login" yang
dibutuhkan test session guard.

**Driver — `tests/conftest.py`**

Kedua modul adalah skrip PHP yang membaca `$_POST` dan menulis ke MySQL,
sehingga tidak dapat dipanggil langsung sebagai unit. Driver bertugas:

1. mengembalikan tabel `users` ke kondisi awal yang deterministik sebelum
   **setiap** test (`TRUNCATE` + seed) agar test tidak saling mempengaruhi;
2. menyediakan sesi browser bersih per test;
3. memberi akses baca ke database lewat `UserRepository`, supaya test dapat
   memverifikasi efek samping yang tidak terlihat di UI — misalnya apakah baris
   benar-benar tersimpan dan apakah kolom `name` terisi.

---

## Menjalankan Pengujian Secara Lokal

**Prasyarat:** XAMPP (Apache + MySQL/MariaDB), Python 3.12+, Google Chrome.

```bash
# 1. Letakkan repository ini di dalam folder htdocs
#    sehingga dapat diakses pada http://localhost/quiz-pengupil/

# 2. Import database
mysql -u root -e "CREATE DATABASE IF NOT EXISTS quiz_pengupil"
mysql -u root quiz_pengupil < db/quiz_pengupil.sql

# 3. Pasang dependency pengujian
pip install -r requirements.txt

# 4. Jalankan seluruh test case
pytest
```

Konfigurasi dapat diubah lewat environment variable:

| Variabel | Default | Keterangan |
|---|---|---|
| `BASE_URL` | `http://localhost/quiz-pengupil/` | URL dasar aplikasi |
| `DB_HOST` | `127.0.0.1` | host MySQL |
| `DB_USER` | `root` | user MySQL |
| `DB_PASS` | *(kosong)* | password MySQL |
| `DB_NAME` | `quiz_pengupil` | nama database |
| `HEADLESS` | `1` | isi `0` untuk melihat jalannya browser |

Menjalankan sebagian test:

```bash
pytest tests/test_login.py          # hanya modul Login
pytest -k "reg_10 or reg_11"        # test case tertentu
HEADLESS=0 pytest tests/test_login.py::test_tc_lgn_08_password_salah_menampilkan_pesan
```

---

## CI/CD Pipeline

`.github/workflows/ci.yml` berjalan pada setiap `push` dan `pull_request` ke
`main`, serta dapat dipicu manual. Tahapannya:

1. menyalakan service container **MariaDB 10.4** dan meng-import
   `db/quiz_pengupil.sql`;
2. menyiapkan **PHP 8.2** dan menjalankan web server bawaan PHP;
3. menyiapkan **Python 3.12**, dependency pengujian, dan **Google Chrome**;
4. menjalankan seluruh test case Selenium secara headless;
5. mengunggah `report.html` sebagai artifact (`if: always()`).

Web server CI dijalankan dengan `-d output_buffering=4096` agar setelan PHP-nya
identik dengan `php.ini` bawaan XAMPP. Tanpa penyamaan ini, dua test case akan
memberi hasil berbeda antara lokal dan CI karena cacat laten **D-07** (lihat
laporan).
