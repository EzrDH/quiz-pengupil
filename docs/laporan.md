# Laporan Pengujian Perangkat Lunak
## Modul Login dan Register — Aplikasi *Quiz Pengupil*

**Mata Kuliah:** Pengujian Perangkat Lunak
**Objek Uji:** <https://github.com/hermanka/quiz-pengupil>
**Repository Hasil Pengerjaan:** `https://github.com/EzrDH/quiz-pengupil`
**Tanggal Pengujian:** 20 Juli 2026

---

## 1. Pendahuluan

Dokumen ini melaporkan perancangan dan pelaksanaan pengujian otomatis terhadap
dua modul aplikasi web berbasis PHP, yaitu **Login** (`login.php`) dan
**Register** (`register.php`). Pengujian dilakukan pada level *system testing*
melalui antarmuka pengguna menggunakan **Selenium WebDriver**, diorkestrasi oleh
**PyTest**, dan dieksekusi otomatis pada **CI/CD pipeline GitHub Actions**.

### 1.1 Prinsip Penyusunan Test Case

Seluruh *assertion* ditulis berdasarkan perilaku yang **seharusnya** terjadi
menurut spesifikasi form dan pesan yang disediakan modul itu sendiri — bukan
berdasarkan perilaku yang kebetulan dihasilkan kode saat ini. Konsekuensinya,
test yang gagal merupakan **temuan cacat yang valid**, bukan test yang salah
tulis.

Kode kedua modul yang diuji **tidak diubah sama sekali** selama pengujian, agar
hasil pengujian mencerminkan kualitas perangkat lunak apa adanya. Karena itu
pipeline CI berakhir dengan status **merah**, dan hal tersebut memang disengaja.

### 1.2 Ringkasan Hasil

| Metrik | Nilai |
|---|---:|
| Total test case | 24 |
| Lulus (*pass*) | 17 |
| Gagal (*fail*) | 7 |
| Tingkat kelulusan | 70,8 % |
| Cacat unik ditemukan | 7 (6 aktif + 1 laten) |

---

## 2. Objek Pengujian

### 2.1 Deskripsi Modul

| Modul | Berkas | Fungsi |
|---|---|---|
| Register | `register.php` | Pendaftaran akun baru: nama, email, username, password, konfirmasi password |
| Login | `login.php` | Autentikasi pengguna terdaftar dengan username dan password |

Keduanya berbagi `koneksi.php` (koneksi MySQL) dan tabel `users` dengan kolom
`id`, `name`, `username`, `email`, `password`. Password disimpan sebagai hash
bcrypt melalui `password_hash()` dan diverifikasi dengan `password_verify()`.

### 2.2 Alur yang Diharapkan

**Register:** validasi seluruh field terisi → validasi password sama dengan
konfirmasi → validasi username belum terpakai → simpan user → buat session →
arahkan ke `index.php`.

**Login:** validasi username dan password terisi → cari user → verifikasi hash
password → buat session → arahkan ke `index.php`.

---

## 3. Lingkungan Pengujian

| Komponen | Lokal (XAMPP) | CI (GitHub Actions) |
|---|---|---|
| Sistem operasi | Windows 11 | Ubuntu (`ubuntu-latest`) |
| Web server | Apache 2.4.58 | PHP built-in server |
| PHP | 8.2.12 | 8.2 |
| Basis data | MariaDB 10.4.32 | MariaDB 10.4 (service container) |
| Python | 3.12.10 | 3.12 |
| Selenium | 4.44.0 | 4.44.0 |
| PyTest | 9.0.3 | 9.0.3 |
| Peramban | Google Chrome (headless) | Google Chrome stable (headless) |

Satu penyesuaian penting dilakukan agar kedua lingkungan setara: web server pada
CI dijalankan dengan `-d output_buffering=4096`, mengikuti nilai bawaan
`php.ini` XAMPP. Tanpa penyamaan ini, dua test case akan memberi hasil berbeda
antara lokal dan CI akibat cacat laten **D-07** (lihat Bagian 7).

Satu-satunya berkas aplikasi yang dimodifikasi adalah `koneksi.php`: nilai
konfigurasi dibaca dari *environment variable* dengan *default* yang identik
dengan versi asli. Modul yang diuji tidak tersentuh.

---

## 4. Strategi Pengujian

### 4.1 Teknik yang Digunakan

| Teknik | Penerapan |
|---|---|
| *Equivalence Partitioning* | Kelas masukan valid, kosong, hanya spasi, dan format salah |
| *Boundary / Negative Testing* | Field kosong sebagian maupun seluruhnya, password tidak cocok |
| *State-based Testing* | Perilaku modul saat session aktif vs tidak aktif (*session guard*) |
| *Security Testing* | Upaya *SQL injection* pada kedua modul, kebocoran pesan galat PHP |
| *Database Verification* | Pemeriksaan langsung ke tabel `users` untuk efek samping yang tak terlihat di UI |

### 4.2 Cakupan

Verifikasi tidak berhenti pada tampilan halaman. Sejumlah cacat pada modul ini
tidak terlihat sama sekali dari antarmuka — misalnya kolom `name` yang selalu
tersimpan kosong, atau baris duplikat yang terbentuk diam-diam. Karena itu
Driver pengujian juga membuka koneksi langsung ke basis data dan memeriksa isi
tabel setelah setiap aksi.

---

## 5. Stub dan Driver

### 5.1 Stub — `index.php` dan `logout.php`

`login.php` dan `register.php` mengakhiri alur suksesnya dengan
`header('Location: index.php')`, namun **`index.php` tidak tersedia** pada
repository asal. Akibatnya jalur sukses kedua modul bermuara ke HTTP 404 dan
tidak dapat diverifikasi. Berkas `readme.md` repository asal pun secara eksplisit
menyatakan *"Diperlukan Stub untuk menguji modul"*.

**`index.php`** dibuat sebagai *stub* pengganti modul dashboard yang belum
dibangun. Stub ini sengaja dirancang "bodoh": tidak memvalidasi apa pun, tidak
menulis ke basis data, dan tidak mengubah session. Ia hanya membaca `$_SESSION`
lalu mengeksposnya melalui *hook* DOM yang stabil:

| Hook | Kegunaan bagi test |
|---|---|
| `#stub-dashboard` | penanda bahwa *redirect* berhasil terjadi |
| `#stub-username` | isi `$_SESSION['username']` |
| `body[data-authenticated]` | status autentikasi, bernilai `"true"` / `"false"` |

Dengan desain sesederhana itu, setiap kegagalan test tetap menunjuk ke modul
yang diuji, bukan ke stub.

**`logout.php`** adalah stub kedua yang menghancurkan session dan kembali ke
`login.php`. Repository asal tidak menyediakan mekanisme logout, padahal
transisi "sudah login → belum login" dibutuhkan oleh test *session guard*
(TC-LGN-11 dan TC-LGN-12).

### 5.2 Driver — `tests/conftest.py`

Kedua modul adalah skrip PHP yang membaca `$_POST` dan menulis langsung ke
MySQL, sehingga tidak dapat dipanggil sebagai unit yang berdiri sendiri.
Diperlukan sebuah *driver* yang menyiapkan lingkungan, menjalankan modul, dan
mengumpulkan hasilnya. Tanggung jawab driver:

1. **Isolasi data.** Sebelum *setiap* test, tabel `users` di-`TRUNCATE` lalu
   diisi ulang dengan data awal yang deterministik. Tanpa ini, test yang
   membuat user akan mempengaruhi test berikutnya.
2. **Isolasi session.** Setiap test memperoleh instance WebDriver baru sehingga
   cookie dan session PHP selalu bersih.
3. **Verifikasi basis data.** Kelas `UserRepository` menyediakan `exists()`,
   `count()`, `find_one()`, dan `total()` untuk memeriksa efek samping yang
   tidak tampak di antarmuka.
4. **Portabilitas.** Seluruh konfigurasi dibaca dari *environment variable*
   sehingga berkas test yang sama berjalan di XAMPP lokal maupun di runner CI.

Data uji dipusatkan pada `tests/testdata.py`. Hash bcrypt akun uji sengaja
di-*hardcode* — bukan digenerate saat runtime — agar data uji identik di semua
lingkungan. Hash dibuat dengan `password_hash('Test@1234', PASSWORD_DEFAULT)`
milik PHP sehingga memakai prefiks `$2y$` yang dikenali `password_verify()`.

### 5.3 Page Object

`tests/pages.py` memisahkan selektor DOM dari logika pengujian, sehingga berkas
test terbaca sebagai langkah-langkah pengujian, bukan sebagai kode otomasi
peramban. Kelas `LoginPage`, `RegisterPage`, dan `DashboardStubPage` menyediakan
aksi tingkat tinggi seperti `login()`, `register()`, dan properti pembacaan
seperti `error_message` dan `php_errors()`.

Metode `submit()` menunggu secara eksplisit hingga dokumen hasil benar-benar
dimuat (*staleness* elemen lama + `document.readyState === "complete"`). Tanpa
penantian ini, WebDriver dapat kembali sebelum PHP selesai memproses POST,
sehingga *assertion* terhadap basis data berjalan mendahului `INSERT` dan test
menjadi **flaky** — masalah ini benar-benar teramati saat penyusunan dan telah
diperbaiki di sisi harness.

---

## 6. Daftar Test Case dan Hasil Eksekusi

### 6.1 Modul Register

| ID | Skenario | Hasil yang Diharapkan | Status | Cacat |
|---|---|---|:--:|:--:|
| TC-REG-01 | Registrasi dengan seluruh data valid | Baris user baru tersimpan di tabel `users` | LULUS | — |
| TC-REG-02 | Registrasi valid, periksa kolom `name` | Kolom `name` berisi nama yang diinput | **GAGAL** | D-01 |
| TC-REG-03 | Registrasi valid, periksa navigasi | Diarahkan ke `index.php` | LULUS | — |
| TC-REG-04 | Registrasi valid, periksa kebersihan halaman | Tidak ada *warning*/*error* PHP di halaman | LULUS | — |
| TC-REG-05 | Seluruh field dikosongkan | Muncul "Data tidak boleh kosong !!", tidak ada user baru | LULUS | — |
| TC-REG-06 | Password ≠ Re-Password | Muncul "Password tidak sama !!", tidak ada user baru | LULUS | — |
| TC-REG-07 | Hanya field email dikosongkan | Muncul "Data tidak boleh kosong !!" | LULUS | — |
| TC-REG-08 | Seluruh field diisi spasi | Diperlakukan sebagai kosong dan ditolak | LULUS | — |
| TC-REG-09 | Email berformat salah, validasi HTML5 dilewati | Ditolak oleh validasi sisi server | **GAGAL** | D-03 |
| TC-REG-10 | Username sudah terdaftar, nama berbeda | Muncul "Username sudah terdaftar !!" | **GAGAL** | D-02 |
| TC-REG-11 | Username sudah terdaftar, periksa basis data | Tetap hanya ada satu baris untuk username tersebut | **GAGAL** | D-02 |
| TC-REG-12 | Payload SQL injection pada nama dan username | Tidak memicu galat SQL, isi tabel tetap wajar | LULUS | — |

### 6.2 Modul Login

| ID | Skenario | Hasil yang Diharapkan | Status | Cacat |
|---|---|---|:--:|:--:|
| TC-LGN-01 | Login dengan kredensial benar | Diarahkan ke `index.php` | LULUS | — |
| TC-LGN-02 | Login benar, periksa session | `$_SESSION['username']` terisi username yang login | LULUS | — |
| TC-LGN-03 | Login benar, periksa kebersihan halaman | Tidak ada *warning*/*error* PHP di halaman | LULUS | — |
| TC-LGN-04 | Username dan password kosong | Muncul "Data tidak boleh kosong !!" | LULUS | — |
| TC-LGN-05 | Hanya password dikosongkan | Muncul "Data tidak boleh kosong !!" | LULUS | — |
| TC-LGN-06 | Username dan password diisi spasi | Diperlakukan sebagai kosong dan ditolak | LULUS | — |
| TC-LGN-07 | Username tidak terdaftar | Muncul pesan kegagalan **login** yang relevan | **GAGAL** | D-04 |
| TC-LGN-08 | Password salah | Muncul pesan galat yang memberi tahu penyebab kegagalan | **GAGAL** | D-05 |
| TC-LGN-09 | Password salah, periksa session | Session tidak terbentuk, tidak diarahkan ke dashboard | LULUS | — |
| TC-LGN-10 | Payload SQL injection pada kredensial | Autentikasi tidak tertembus, tidak ada galat SQL | LULUS | — |
| TC-LGN-11 | Membuka `login.php` saat session aktif | Diarahkan ke `index.php` | LULUS | — |
| TC-LGN-12 | Membuka `register.php` saat session aktif | Diarahkan ke `index.php` | **GAGAL** | D-06 |

### 6.3 Rekapitulasi

| Modul | Jumlah | Lulus | Gagal |
|---|---:|---:|---:|
| Register | 12 | 8 | 4 |
| Login | 12 | 9 | 3 |
| **Total** | **24** | **17** | **7** |

---

## 7. Laporan Cacat (*Defect Report*)

### D-01 — Nama pengguna tidak pernah tersimpan
| | |
|---|---|
| **Severity** | Major |
| **Lokasi** | `register.php` baris 34 |
| **Ditemukan oleh** | TC-REG-02 |

Perintah `INSERT` menggunakan variabel `$nama`, padahal nilai dari form
ditampung pada variabel `$name`:

```php
$query = "INSERT INTO users (username,name,email, password )
          VALUES ('$username','$nama','$email','$pass')";
```

`$nama` tidak pernah didefinisikan di lingkup tersebut, sehingga PHP
mengevaluasinya menjadi string kosong dan kolom `name` **selalu** terisi `''`.
Cacat ini tidak kasatmata dari antarmuka karena registrasi tetap dilaporkan
berhasil. Bukti pendukung: kedua baris data bawaan pada
`db/quiz_pengupil.sql` juga memiliki kolom `name` kosong — cacat ini sudah
mengotori data produksi.

**Perbaikan yang disarankan:** ganti `$nama` menjadi `$name`.

---

### D-02 — Username dapat terduplikasi
| | |
|---|---|
| **Severity** | Critical |
| **Lokasi** | `register.php` baris 32 dan 54–58 |
| **Ditemukan oleh** | TC-REG-10, TC-REG-11 |

Fungsi `cek_nama()` memeriksa **kolom `username`**, tetapi dipanggil dengan
nilai **nama lengkap**:

```php
if( cek_nama($name,$con) == 0 ){    // seharusnya cek_nama($username,$con)
```

Akibatnya, mendaftar dengan username `irul` (yang sudah ada) tetapi nama
`Nama Berbeda` menghasilkan query `SELECT * FROM users WHERE username = 'Nama
Berbeda'` yang mengembalikan nol baris, sehingga pemeriksaan duplikat lolos dan
baris kedua dengan username `irul` tetap dibuat. Pesan "Username sudah
terdaftar !!" praktis tidak pernah muncul.

Dampaknya serius bagi modul Login: kueri autentikasi
`SELECT * FROM users WHERE username = '$username'` akan mengembalikan lebih dari
satu baris, dan `mysqli_fetch_assoc()` hanya mengambil baris pertama. Pemilik
akun duplikat kedua tidak akan pernah bisa masuk menggunakan password miliknya.

**Perbaikan yang disarankan:** panggil `cek_nama($username, $con)`, dan tambahkan
*constraint* `UNIQUE` pada kolom `username` sebagai pengaman di tingkat basis
data.

---

### D-03 — Tidak ada validasi email di sisi server
| | |
|---|---|
| **Severity** | Major |
| **Lokasi** | `register.php` baris 30 |
| **Ditemukan oleh** | TC-REG-09 |

Satu-satunya validasi format email adalah atribut HTML5 `type="email"` pada
formulir. Validasi tersebut hanya berlaku di peramban dan mudah dilewati — test
membuktikannya cukup dengan menambahkan atribut `novalidate` pada form. Server
hanya memeriksa bahwa field tidak kosong, sehingga nilai `bukan-email` berhasil
tersimpan ke basis data.

**Perbaikan yang disarankan:** tambahkan
`filter_var($email, FILTER_VALIDATE_EMAIL)` pada validasi sisi server.

---

### D-04 — Pesan galat modul Login menyesatkan
| | |
|---|---|
| **Severity** | Minor |
| **Lokasi** | `login.php` baris 33 |
| **Ditemukan oleh** | TC-LGN-07 |

Ketika username tidak ditemukan, modul Login menampilkan
`'Register User Gagal !!'` — pesan yang membicarakan kegagalan **registrasi**
kepada pengguna yang sedang berada di halaman **login**. Pengguna dapat mengira
proses pendaftarannya yang bermasalah, bukan kredensial yang dimasukkannya.

**Perbaikan yang disarankan:** ganti menjadi pesan netral seperti
`'Username atau password salah !!'`.

---

### D-05 — Password salah tidak menghasilkan umpan balik apa pun
| | |
|---|---|
| **Severity** | Major |
| **Lokasi** | `login.php` baris 26–31 |
| **Ditemukan oleh** | TC-LGN-08 |

Blok verifikasi password tidak memiliki cabang `else`:

```php
if(password_verify($password, $hash)){
    $_SESSION['username'] = $username;
    header('Location: index.php');
}
// tidak ada else -> $error tetap kosong
```

Bila username benar tetapi password salah, `$error` tetap bernilai kosong
sehingga halaman login hanya dirender ulang **tanpa pesan apa pun**. Dari sudut
pandang pengguna, tombol Sign In seolah tidak berfungsi.

Sisi positifnya, TC-LGN-09 membuktikan bahwa tidak ada session yang terbentuk —
jadi ini murni cacat kegunaan, bukan celah keamanan.

**Perbaikan yang disarankan:** tambahkan cabang `else` yang mengisi `$error`
dengan pesan yang sama seperti pada D-04, agar penyerang tidak dapat membedakan
"username tidak ada" dari "password salah" (*user enumeration*).

---

### D-06 — Halaman registrasi tetap terbuka bagi pengguna yang sudah login
| | |
|---|---|
| **Severity** | Minor |
| **Lokasi** | `register.php` baris 17 |
| **Ditemukan oleh** | TC-LGN-12 |

*Session guard* pada modul Register memeriksa kunci session yang salah:

```php
if( isset($_SESSION['user']) ) header('Location: index.php');
```

Kunci yang benar-benar diisi saat login maupun registrasi adalah
`$_SESSION['username']`, bukan `$_SESSION['user']`. Kondisi tersebut karenanya
tidak pernah bernilai benar. Sebagai pembanding, `login.php` baris 9 memakai
kunci yang benar — dan TC-LGN-11 pun lulus.

**Perbaikan yang disarankan:** ubah menjadi `isset($_SESSION['username'])`.

---

### D-07 — Ketergantungan tersembunyi pada `output_buffering` *(cacat laten)*
| | |
|---|---|
| **Severity** | Major (laten) |
| **Lokasi** | `register.php` baris 1–13 |
| **Ditemukan oleh** | Investigasi lanjutan atas TC-REG-03 dan TC-REG-04 |

Berbeda dengan `login.php` yang mengawali berkas dengan blok PHP,
`register.php` mengeluarkan **10 baris HTML terlebih dahulu**, baru kemudian
memanggil `session_start()` (baris 13) dan `header('Location: index.php')`
(baris 38). Keduanya membutuhkan header HTTP yang belum terkirim.

Cacat ini **tidak terdeteksi** pada konfigurasi XAMPP karena `php.ini` bawaannya
mengaktifkan `output_buffering = 4096`, sehingga keluaran tertahan di buffer dan
header masih dapat dimodifikasi. TC-REG-03 dan TC-REG-04 karenanya berstatus
LULUS. Namun pada konfigurasi tanpa buffering, modul langsung rusak.

Pembuktian dilakukan dengan menjalankan modul yang sama pada dua konfigurasi
dan mengirim POST registrasi yang identik:

| `output_buffering` | Respons HTTP | Redirect |
|---|---|---|
| `4096` (bawaan XAMPP) | **302** | `index.php` — berfungsi |
| `0` | **200** | tidak terjadi |

Pada konfigurasi tanpa buffering, tiga *warning* muncul di halaman:

```
Warning: session_start(): Session cannot be started after headers have already been sent
Warning: Undefined variable $nama
Warning: Cannot modify header information - headers already sent (output started at register.php:1)
```

Artinya pada server dengan `output_buffering = 0`: registrasi yang berhasil
tidak mengarahkan pengguna ke mana pun, session gagal dibuat, dan pesan galat
internal — termasuk *path* berkas di server — bocor ke pengguna.

Karena inilah web server pada pipeline CI dijalankan dengan
`-d output_buffering=4096`, agar hasil pengujian di CI konsisten dengan hasil
lokal dan cacat ini tidak menimbulkan kegagalan yang menyesatkan.

**Perbaikan yang disarankan:** pindahkan seluruh blok PHP `register.php` ke
bagian paling atas berkas, sebelum `<!DOCTYPE html>`, mengikuti pola yang sudah
benar pada `login.php`.

---

### 7.1 Rekapitulasi Cacat

| ID | Severity | Modul | Ringkasan | Test case |
|---|---|---|---|---|
| D-01 | Major | Register | Kolom `name` selalu tersimpan kosong (`$nama` vs `$name`) | TC-REG-02 |
| D-02 | Critical | Register | Pemeriksaan duplikat memakai argumen salah → username terduplikasi | TC-REG-10, TC-REG-11 |
| D-03 | Major | Register | Format email tidak divalidasi di sisi server | TC-REG-09 |
| D-04 | Minor | Login | Pesan galat menyebut kegagalan registrasi di halaman login | TC-LGN-07 |
| D-05 | Major | Login | Password salah tidak memunculkan pesan apa pun | TC-LGN-08 |
| D-06 | Minor | Register | *Session guard* memakai kunci session yang salah | TC-LGN-12 |
| D-07 | Major (laten) | Register | Output HTML mendahului `session_start()` dan `header()` | TC-REG-03, TC-REG-04 |

Sebaran severity: **1 Critical**, **4 Major**, **2 Minor**.

---

## 8. Aspek yang Terbukti Sudah Baik

Tidak semua hasil bersifat temuan negatif. Pengujian juga mengonfirmasi bahwa
sejumlah aspek penting sudah ditangani dengan benar:

- **Penyimpanan password.** Password di-*hash* dengan `password_hash()` dan
  diverifikasi memakai `password_verify()`; tidak ada penyimpanan *plaintext*.
- **Ketahanan terhadap SQL injection.** TC-REG-12 dan TC-LGN-10 membuktikan
  bahwa kombinasi `stripslashes()` dan `mysqli_real_escape_string()` berhasil
  menetralkan payload `' OR '1'='1`. Autentikasi tidak dapat ditembus.
- **Integritas autentikasi.** TC-LGN-09 membuktikan password salah tidak pernah
  membentuk session, meskipun tidak ada pesan galat yang ditampilkan (D-05).
- **Validasi field kosong.** Penggunaan `trim()` membuat masukan berisi spasi
  saja tetap ditolak dengan benar pada kedua modul.

---

## 9. CI/CD Pipeline

Berkas `.github/workflows/ci.yml` menjalankan seluruh test case secara otomatis
pada setiap `push` dan `pull_request` ke *branch* `main`, serta dapat dipicu
manual melalui `workflow_dispatch`.

### 9.1 Tahapan Pipeline

1. **Service container MariaDB 10.4** dinyalakan dan ditunggu hingga sehat
   melalui *health check*.
2. **Checkout** repository.
3. **Setup PHP 8.2** beserta ekstensi `mysqli`.
4. **Import basis data** dari `db/quiz_pengupil.sql`.
5. **Menjalankan web server** PHP di `127.0.0.1:8000`, lalu menunggu hingga
   `login.php` merespons — bukan sekadar `sleep` dengan durasi tetap.
6. **Setup Python 3.12** dan memasang dependency dari `requirements.txt`.
7. **Setup Google Chrome** stabil beserta ChromeDriver.
8. **Menjalankan seluruh test case** Selenium secara *headless*.
9. **Mengunggah laporan** `report.html` dan `php-server.log` sebagai artifact
   dengan `if: always()`, sehingga laporan tetap tersedia meski pengujian gagal.

### 9.2 Catatan Konfigurasi

Web server CI dijalankan dengan `-d output_buffering=4096` dan
`-d display_errors=1` mengikuti `php.ini` bawaan XAMPP. Penyamaan ini penting:
tanpanya, TC-REG-03 dan TC-REG-04 akan gagal di CI namun lulus di lokal akibat
cacat laten D-07 — perbedaan yang akan menyulitkan interpretasi hasil.

### 9.3 Status Pipeline

Pipeline berakhir dengan status **gagal (merah)** karena 7 test case memang
gagal. Status ini **disengaja dan dipertahankan**: pipeline hijau hanya dapat
dicapai dengan memperbaiki cacat pada modul yang diuji atau dengan melemahkan
*assertion*, dan keduanya akan menyembunyikan hasil pengujian yang sebenarnya.
Artifact `report.html` tetap terunggah sehingga rincian setiap kegagalan dapat
ditelusuri.

---

## 10. Cara Menjalankan Pengujian

**Prasyarat:** XAMPP (Apache + MySQL/MariaDB), Python 3.12+, Google Chrome.

```bash
# 1. Tempatkan repository di dalam folder htdocs
#    agar dapat diakses pada http://localhost/quiz-pengupil/

# 2. Import basis data
mysql -u root -e "CREATE DATABASE IF NOT EXISTS quiz_pengupil"
mysql -u root quiz_pengupil < db/quiz_pengupil.sql

# 3. Pasang dependency pengujian
pip install -r requirements.txt

# 4. Jalankan seluruh test case
pytest
```

Untuk mengamati jalannya peramban secara visual:

```bash
HEADLESS=0 pytest tests/test_register.py::test_tc_reg_10_username_duplikat_ditolak
```

---

## 11. Kesimpulan

Pengujian otomatis terhadap modul Login dan Register menghasilkan **24 test
case**, dengan **17 lulus** dan **7 gagal**, yang bermuara pada **7 cacat unik**
— satu di antaranya berkategori *Critical* dan empat *Major*.

Beberapa hal yang menonjol dari pengujian ini:

**Verifikasi melalui antarmuka saja tidak memadai.** Cacat paling parah yang
ditemukan (D-01 dan D-02) sama sekali tidak terlihat dari layar: registrasi
dilaporkan berhasil, pengguna diarahkan ke dashboard, dan tidak ada pesan galat.
Cacat baru terungkap ketika Driver memeriksa langsung isi tabel `users`. Karena
itu strategi pengujian yang menggabungkan verifikasi UI dengan verifikasi basis
data terbukti bernilai.

**Stub bukan sekadar pelengkap.** Tanpa `index.php`, jalur sukses kedua modul
berakhir di HTTP 404 dan tidak ada satu pun test case jalur positif yang dapat
diverifikasi. Kebutuhan ini bahkan telah diantisipasi oleh penyusun soal melalui
catatan pada `readme.md` repository asal.

**Kondisi lingkungan dapat menyembunyikan cacat.** D-07 menunjukkan bahwa
`register.php` sesungguhnya rusak, namun tertolong oleh setelan
`output_buffering` bawaan XAMPP. Cacat semacam ini hanya terungkap dengan
menjalankan modul pada lebih dari satu konfigurasi — dan justru cacat inilah
yang paling berbahaya ketika aplikasi dipindahkan ke server produksi dengan
setelan berbeda.

**Test yang tidak stabil harus diinvestigasi, bukan diulang.** Saat penyusunan,
TC-REG-01 dan TC-REG-02 sempat memberikan hasil yang bertentangan padahal
melakukan aksi identik. Penelusuran menunjukkan penyebabnya ada pada harness —
WebDriver kembali sebelum PHP selesai memproses POST — bukan pada aplikasi.
Perbaikan berupa penantian eksplisit membuat hasil pengujian konsisten pada
empat kali eksekusi berturut-turut. Seandainya *flakiness* ini dibiarkan, seluruh
laporan cacat menjadi tidak dapat dipercaya.

---

## 12. Lampiran

| Berkas | Isi |
|---|---|
| `tests/conftest.py` | Driver pengujian: fixture basis data, peramban, dan data uji |
| `tests/pages.py` | Page Object modul Login, Register, dan stub dashboard |
| `tests/testdata.py` | Data uji terpusat dan pesan yang diharapkan |
| `tests/test_login.py` | 12 test case modul Login |
| `tests/test_register.py` | 12 test case modul Register |
| `index.php`, `logout.php` | Stub |
| `.github/workflows/ci.yml` | Definisi CI/CD pipeline |

**Repository hasil pengerjaan:** `https://github.com/EzrDH/quiz-pengupil`
