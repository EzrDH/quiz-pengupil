"""
Test case modul REGISTER (register.php).

Setiap test menyatakan perilaku yang SEHARUSNYA terjadi menurut spesifikasi
form, bukan perilaku yang kebetulan dihasilkan kode saat ini. Test yang gagal
karena itu merupakan temuan cacat, bukan test yang salah tulis.
"""

import pytest

import testdata

VALID = testdata.VALID_USER


# ---------------------------------------------------------------------------
#  Jalur positif
# ---------------------------------------------------------------------------
def test_tc_reg_01_registrasi_valid_menyimpan_user(register_page, users):
    """TC-REG-01: Registrasi dengan data lengkap & valid menyimpan user baru."""
    register_page.open().register(
        name="Budi Santoso",
        email="budi@example.com",
        username="budi",
        password="Budi@1234",
    )

    assert users.exists("budi"), "User baru tidak tersimpan di tabel users"


def test_tc_reg_02_registrasi_valid_menyimpan_nama(register_page, users):
    """TC-REG-02: Nama yang diinput harus tersimpan di kolom `name`."""
    register_page.open().register(
        name="Budi Santoso",
        email="budi@example.com",
        username="budi",
        password="Budi@1234",
    )

    row = users.find_one("budi")
    assert row is not None, "User tidak tersimpan sama sekali"
    assert row["name"] == "Budi Santoso", (
        f"Kolom name berisi {row['name']!r}, seharusnya 'Budi Santoso'"
    )


def test_tc_reg_03_registrasi_valid_redirect_ke_dashboard(register_page, dashboard, users):
    """TC-REG-03: Registrasi sukses harus mengarahkan user ke index.php."""
    register_page.open().register(
        name="Budi Santoso",
        email="budi@example.com",
        username="budi",
        password="Budi@1234",
    )

    assert register_page.current_path == "index.php", (
        f"Setelah registrasi sukses masih berada di {register_page.current_path!r}"
    )
    assert dashboard.is_displayed, "Dashboard (stub) tidak tampil setelah registrasi"


def test_tc_reg_04_halaman_bebas_error_php(register_page, users):
    """TC-REG-04: Halaman registrasi tidak boleh membocorkan error/warning PHP."""
    register_page.open().register(
        name="Budi Santoso",
        email="budi@example.com",
        username="budi",
        password="Budi@1234",
    )

    leaked = register_page.php_errors()
    assert leaked == [], f"Error PHP bocor ke halaman: {leaked}"


# ---------------------------------------------------------------------------
#  Validasi input
# ---------------------------------------------------------------------------
def test_tc_reg_05_semua_field_kosong_ditolak(register_page, users):
    """TC-REG-05: Submit dengan semua field kosong menampilkan pesan wajib isi."""
    before = users.total()
    register_page.open().register(name="", email="", username="", password="")

    assert register_page.error_message == testdata.MSG_EMPTY
    assert users.total() == before, "Jumlah user bertambah padahal input kosong"


def test_tc_reg_06_password_tidak_sama_ditolak(register_page, users):
    """TC-REG-06: Password dan Re-Password berbeda harus ditolak."""
    register_page.open().register(
        name="Budi Santoso",
        email="budi@example.com",
        username="budi",
        password="Budi@1234",
        repassword="Budi@9999",
    )

    assert register_page.validate_message == testdata.MSG_PASSWORD_MISMATCH
    assert not users.exists("budi"), "User tersimpan padahal konfirmasi password salah"


def test_tc_reg_07_satu_field_kosong_ditolak(register_page, users):
    """TC-REG-07: Satu field kosong (email) sudah cukup untuk menolak submit."""
    register_page.open().register(
        name="Budi Santoso",
        email="",
        username="budi",
        password="Budi@1234",
    )

    assert register_page.error_message == testdata.MSG_EMPTY
    assert not users.exists("budi")


def test_tc_reg_08_input_hanya_spasi_ditolak(register_page, users):
    """TC-REG-08: Input berisi spasi saja harus diperlakukan sebagai kosong."""
    register_page.open().register(
        name=testdata.WHITESPACE,
        email=testdata.WHITESPACE,
        username=testdata.WHITESPACE,
        password=testdata.WHITESPACE,
    )

    assert register_page.error_message == testdata.MSG_EMPTY


def test_tc_reg_09_email_format_salah_ditolak_server(register_page, users):
    """
    TC-REG-09: Validasi email harus dilakukan di sisi server.

    Atribut HTML5 type="email" hanya melindungi pengguna browser biasa dan
    mudah dilewati, sehingga tidak boleh menjadi satu-satunya validasi.
    """
    page = register_page.open()
    page.disable_html5_validation()
    page.register(
        name="Budi Santoso",
        email="bukan-email",
        username="budi",
        password="Budi@1234",
    )

    assert not users.exists("budi"), (
        "User dengan email 'bukan-email' tersimpan - tidak ada validasi email di server"
    )


# ---------------------------------------------------------------------------
#  Duplikasi username
# ---------------------------------------------------------------------------
def test_tc_reg_10_username_duplikat_ditolak(register_page, users):
    """TC-REG-10: Username yang sudah terdaftar harus ditolak dengan pesan jelas."""
    assert users.exists("irul"), "Prasyarat: user 'irul' harus ada dari seed"

    register_page.open().register(
        name="Nama Berbeda",
        email="lain@example.com",
        username="irul",
        password="Irul@1234",
    )

    assert register_page.error_message == testdata.MSG_USERNAME_TAKEN


def test_tc_reg_11_username_duplikat_tidak_menambah_baris(register_page, users):
    """TC-REG-11: Registrasi duplikat tidak boleh menghasilkan dua baris username sama."""
    register_page.open().register(
        name="Nama Berbeda",
        email="lain@example.com",
        username="irul",
        password="Irul@1234",
    )

    assert users.count("irul") == 1, (
        f"Terdapat {users.count('irul')} baris dengan username 'irul' - username terduplikasi"
    )


# ---------------------------------------------------------------------------
#  Keamanan
# ---------------------------------------------------------------------------
def test_tc_reg_12_sql_injection_tidak_merusak_database(register_page, users):
    """TC-REG-12: Payload SQL injection tidak boleh mengubah struktur/isi tabel."""
    before = users.total()

    register_page.open().register(
        name=testdata.SQLI_PAYLOAD,
        email="inject@example.com",
        username=testdata.SQLI_PAYLOAD,
        password="Inject@1234",
    )

    assert register_page.php_errors() == [], "Payload SQLi memicu error PHP/SQL"
    # Tabel tetap terbaca dan paling banyak bertambah satu baris biasa
    assert users.total() in (before, before + 1)
