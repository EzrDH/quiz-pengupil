"""
============================================================================
 DRIVER PENGUJIAN
============================================================================

Modul login.php dan register.php tidak dapat dipanggil langsung sebagai unit:
keduanya adalah skrip PHP yang membaca $_POST dan menulis ke MySQL. Karena itu
diperlukan sebuah *driver* yang bertugas:

  1. Menyiapkan database ke keadaan awal yang diketahui sebelum SETIAP test
     (TRUNCATE + seed) sehingga test tidak saling mempengaruhi.
  2. Menyediakan sesi browser bersih (cookie/session PHP kosong) per test.
  3. Menyediakan akses baca ke database agar test dapat memverifikasi efek
     samping yang tidak terlihat di UI (mis. apakah baris benar-benar masuk).

Konfigurasi diambil dari environment variable supaya file yang sama berjalan
di XAMPP lokal maupun di GitHub Actions:

  BASE_URL   URL dasar aplikasi          (default http://localhost/quiz-pengupil/)
  DB_HOST    host MySQL                  (default 127.0.0.1)
  DB_USER    user MySQL                  (default root)
  DB_PASS    password MySQL              (default kosong)
  DB_NAME    nama database               (default quiz_pengupil)
  HEADLESS   "0" untuk melihat browser   (default "1")
============================================================================
"""

import os

import pymysql
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import testdata

BASE_URL = os.getenv("BASE_URL", "http://localhost/quiz-pengupil/")
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "quiz_pengupil"),
    "charset": "utf8mb4",
    "autocommit": True,
}


# ---------------------------------------------------------------------------
#  Akses database
# ---------------------------------------------------------------------------
class UserRepository:
    """Pembungkus query yang dipakai test untuk memeriksa state database."""

    def __init__(self, connection):
        self.connection = connection

    def _query(self, sql, params=()):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def _execute(self, sql, params=()):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

    def reset(self):
        """Kembalikan tabel users ke keadaan awal yang deterministik."""
        self._execute("TRUNCATE TABLE users")
        for user in testdata.SEED_USERS:
            self.insert(user["name"], user["username"], user["email"], user["hash"])
        valid = testdata.VALID_USER
        self.insert(valid["name"], valid["username"], valid["email"], valid["hash"])

    def insert(self, name, username, email, password_hash):
        self._execute(
            "INSERT INTO users (name, username, email, password) VALUES (%s, %s, %s, %s)",
            (name, username, email, password_hash),
        )

    def find_all(self, username):
        return self._query("SELECT * FROM users WHERE username = %s", (username,))

    def find_one(self, username):
        rows = self.find_all(username)
        return rows[0] if rows else None

    def count(self, username):
        return len(self.find_all(username))

    def exists(self, username):
        return self.count(username) > 0

    def total(self):
        return self._query("SELECT COUNT(*) AS n FROM users")[0]["n"]


@pytest.fixture(scope="session")
def connection():
    conn = pymysql.connect(**DB_CONFIG)
    yield conn
    conn.close()


@pytest.fixture
def users(connection):
    """Repository user dengan database yang sudah direset untuk test ini."""
    repository = UserRepository(connection)
    repository.reset()
    return repository


# ---------------------------------------------------------------------------
#  Browser
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def driver():
    options = Options()
    if os.getenv("HEADLESS", "1") != "0":
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1366,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # Cegah popup "simpan password" yang bisa menutupi tombol submit
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        },
    )

    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(3)
    browser.set_page_load_timeout(30)
    yield browser
    browser.quit()


# ---------------------------------------------------------------------------
#  Page object siap pakai
# ---------------------------------------------------------------------------
@pytest.fixture
def login_page(driver, base_url):
    from pages import LoginPage

    return LoginPage(driver, base_url)


@pytest.fixture
def register_page(driver, base_url):
    from pages import RegisterPage

    return RegisterPage(driver, base_url)


@pytest.fixture
def dashboard(driver, base_url):
    from pages import DashboardStubPage

    return DashboardStubPage(driver, base_url)


@pytest.fixture
def logged_in(driver, base_url, users, login_page):
    """Kondisi awal: sudah berhasil login sebagai VALID_USER."""
    valid = testdata.VALID_USER
    login_page.open().login(valid["username"], valid["password"])
    return driver
