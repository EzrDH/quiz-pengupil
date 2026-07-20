"""
Test case modul LOGIN (login.php).

Sama seperti modul register, assertion ditulis berdasarkan perilaku yang
seharusnya, sehingga kegagalan test berarti temuan cacat.
"""

import testdata

VALID = testdata.VALID_USER


# ---------------------------------------------------------------------------
#  Jalur positif
# ---------------------------------------------------------------------------
def test_tc_lgn_01_login_valid_redirect_ke_dashboard(login_page, dashboard, users):
    """TC-LGN-01: Kredensial benar mengarahkan user ke index.php."""
    login_page.open().login(VALID["username"], VALID["password"])

    assert login_page.current_path == "index.php", (
        f"Setelah login sukses berada di {login_page.current_path!r}, bukan index.php"
    )
    assert dashboard.is_displayed, "Dashboard (stub) tidak tampil setelah login"


def test_tc_lgn_02_login_valid_membuat_session(login_page, dashboard, users):
    """TC-LGN-02: Login sukses menyimpan username ke dalam session."""
    login_page.open().login(VALID["username"], VALID["password"])

    assert dashboard.is_authenticated, "Session tidak terbentuk setelah login"
    assert dashboard.session_username == VALID["username"]


def test_tc_lgn_03_halaman_login_bebas_error_php(login_page, users):
    """TC-LGN-03: Halaman login tidak boleh membocorkan error/warning PHP."""
    login_page.open().login(VALID["username"], VALID["password"])

    leaked = login_page.php_errors()
    assert leaked == [], f"Error PHP bocor ke halaman: {leaked}"


# ---------------------------------------------------------------------------
#  Validasi input
# ---------------------------------------------------------------------------
def test_tc_lgn_04_field_kosong_ditolak(login_page, users):
    """TC-LGN-04: Username dan password kosong menampilkan pesan wajib isi."""
    login_page.open().login("", "")

    assert login_page.error_message == testdata.MSG_EMPTY


def test_tc_lgn_05_password_kosong_ditolak(login_page, users):
    """TC-LGN-05: Password kosong menampilkan pesan wajib isi."""
    login_page.open().login(VALID["username"], "")

    assert login_page.error_message == testdata.MSG_EMPTY


def test_tc_lgn_06_input_hanya_spasi_ditolak(login_page, users):
    """TC-LGN-06: Input berisi spasi saja diperlakukan sebagai kosong."""
    login_page.open().login(testdata.WHITESPACE, testdata.WHITESPACE)

    assert login_page.error_message == testdata.MSG_EMPTY


# ---------------------------------------------------------------------------
#  Kredensial salah
# ---------------------------------------------------------------------------
def test_tc_lgn_07_username_tidak_terdaftar_pesan_relevan(login_page, users):
    """
    TC-LGN-07: Username tidak terdaftar menampilkan pesan kegagalan LOGIN.

    Pesan tidak boleh menyebut kegagalan registrasi karena menyesatkan
    pengguna yang sedang berada di halaman login.
    """
    login_page.open().login("user_tidak_ada", "Apapun@123")

    message = login_page.error_message
    assert message != "", "Tidak ada pesan error untuk username tidak terdaftar"
    assert message != testdata.MSG_REGISTER_FAILED, (
        f"Pesan yang tampil {message!r} membicarakan registrasi, bukan login"
    )


def test_tc_lgn_08_password_salah_menampilkan_pesan(login_page, users):
    """TC-LGN-08: Password salah harus memberi umpan balik kepada pengguna."""
    login_page.open().login(VALID["username"], "Password@Salah999")

    assert login_page.error_message != "", (
        "Password salah tidak menghasilkan pesan error apa pun - "
        "pengguna tidak tahu penyebab kegagalan"
    )


def test_tc_lgn_09_password_salah_tidak_membuat_session(login_page, dashboard, users):
    """TC-LGN-09: Password salah tidak boleh membentuk session (keamanan)."""
    login_page.open().login(VALID["username"], "Password@Salah999")

    assert login_page.current_path != "index.php", "Login berhasil dengan password salah"

    dashboard.open()
    assert not dashboard.is_authenticated, "Session terbentuk meski password salah"


# ---------------------------------------------------------------------------
#  Keamanan
# ---------------------------------------------------------------------------
def test_tc_lgn_10_sql_injection_tidak_bisa_login(login_page, dashboard, users):
    """TC-LGN-10: Payload SQL injection tidak boleh melewati autentikasi."""
    login_page.open().login(testdata.SQLI_PAYLOAD, testdata.SQLI_PAYLOAD)

    assert login_page.current_path != "index.php", "Autentikasi tertembus SQL injection"
    assert login_page.php_errors() == [], "Payload SQLi memicu error PHP/SQL"

    dashboard.open()
    assert not dashboard.is_authenticated


# ---------------------------------------------------------------------------
#  Session guard
# ---------------------------------------------------------------------------
def test_tc_lgn_11_login_ditutup_saat_sudah_login(logged_in, login_page, users):
    """TC-LGN-11: User yang sudah login tidak boleh melihat form login lagi."""
    login_page.open()

    assert login_page.current_path == "index.php", (
        "Halaman login masih dapat diakses saat session aktif"
    )


def test_tc_lgn_12_register_ditutup_saat_sudah_login(logged_in, register_page, users):
    """TC-LGN-12: User yang sudah login tidak boleh melihat form registrasi lagi."""
    register_page.open()

    assert register_page.current_path == "index.php", (
        "Halaman register masih dapat diakses saat session aktif"
    )
