"""
Page Object untuk modul Login dan Register.

Semua selector DOM dikumpulkan di sini supaya test case membaca sebagai
langkah-langkah pengujian, bukan sebagai kode otomasi browser.
"""

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import testdata

TIMEOUT = 10


class BasePage:
    # Alert merah dari variabel $error pada kedua modul
    ERROR_ALERT = (By.CSS_SELECTOR, "div.alert.alert-danger")
    # Teks merah dari variabel $validate
    VALIDATE_TEXT = (By.CSS_SELECTOR, "p.text-danger")
    SUBMIT = (By.CSS_SELECTOR, "button[name='submit']")

    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url.rstrip("/") + "/"

    # --- navigasi ----------------------------------------------------------
    def open(self):
        """
        Buka halaman lalu tunggu sampai dokumen selesai dimuat.

        Berinteraksi dengan halaman yang masih dalam proses muat sesekali
        memicu WebDriverException "unhandled inspector error" karena elemen
        yang sudah ditemukan digantikan oleh dokumen baru. Menunggu
        document.readyState menghilangkan sumber flakiness tersebut.
        """
        self.driver.get(self.base_url + self.PATH)
        self._wait_document_ready()
        return self

    def _wait_document_ready(self):
        WebDriverWait(self.driver, TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    @property
    def current_path(self):
        """Nama file terakhir dari URL saat ini, mis. 'index.php'."""
        return self.driver.current_url.rstrip("/").split("/")[-1].split("?")[0]

    # --- pembacaan pesan ---------------------------------------------------
    def _text_or_empty(self, locator):
        elements = self.driver.find_elements(*locator)
        return elements[0].text.strip() if elements else ""

    @property
    def error_message(self):
        return self._text_or_empty(self.ERROR_ALERT)

    @property
    def validate_message(self):
        return self._text_or_empty(self.VALIDATE_TEXT)

    @property
    def page_source(self):
        return self.driver.page_source

    def php_errors(self):
        """Daftar penanda error PHP yang bocor ke halaman."""
        source = self.driver.page_source
        return [m for m in testdata.PHP_ERROR_MARKERS if m in source]

    # --- aksi --------------------------------------------------------------
    def _type(self, locator, value):
        field = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located(locator)
        )
        field.clear()
        if value:
            field.send_keys(value)

    def submit(self):
        """
        Klik tombol submit lalu TUNGGU sampai dokumen hasil benar-benar dimuat.

        Tanpa penantian eksplisit, WebDriver dapat kembali sebelum PHP selesai
        memproses POST, sehingga assertion terhadap database berjalan mendahului
        INSERT dan test menjadi flaky. Penanda staleness dipakai karena andal
        untuk semua kasus: submit sukses (redirect ke index.php) maupun submit
        gagal (register.php/login.php dirender ulang).
        """
        old_body = self.driver.find_element(By.TAG_NAME, "body")
        self.driver.find_element(*self.SUBMIT).click()

        WebDriverWait(self.driver, TIMEOUT).until(self._body_replaced(old_body))
        self._wait_document_ready()
        return self

    @staticmethod
    def _body_replaced(old_body):
        """
        Predikat staleness yang tahan terhadap error CDP non-standar.

        EC.staleness_of() bawaan Selenium mengandalkan tertangkapnya
        StaleElementReferenceException. Pada beberapa versi Chrome/ChromeDriver
        (teramati pada Chrome 150 di runner GitHub Actions, tidak terjadi pada
        Chrome versi XAMPP lokal), ChromeDriver kadang melempar WebDriverException
        mentah berbunyi "Node with given id does not belong to the document"
        alih-alih StaleElementReferenceException saat elemen diperiksa persis di
        tengah pergantian dokumen. Errornya berarti sama persis: elemen lama
        sudah tidak ada. Predikat ini menangkap keduanya sebagai staleness.
        """
        def _predicate(driver):
            try:
                old_body.is_enabled()
                return False
            except StaleElementReferenceException:
                return True
            except WebDriverException as exc:
                if "does not belong to the document" in str(exc):
                    return True
                raise
        return _predicate

    def disable_html5_validation(self):
        """
        Melewati validasi bawaan browser (mis. input type="email") agar
        validasi SISI SERVER yang benar-benar teruji. Tanpa ini browser akan
        memblokir submit sebelum request sampai ke PHP.
        """
        self.driver.execute_script(
            "document.querySelector('form').setAttribute('novalidate','novalidate');"
        )
        return self


class LoginPage(BasePage):
    PATH = "login.php"

    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "InputPassword")

    def login(self, username, password):
        self._type(self.USERNAME, username)
        self._type(self.PASSWORD, password)
        return self.submit()


class RegisterPage(BasePage):
    PATH = "register.php"

    NAME = (By.ID, "name")
    EMAIL = (By.ID, "InputEmail")
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "InputPassword")
    REPASSWORD = (By.ID, "InputRePassword")

    def fill(self, name="", email="", username="", password="", repassword=None):
        if repassword is None:
            repassword = password
        self._type(self.NAME, name)
        self._type(self.EMAIL, email)
        self._type(self.USERNAME, username)
        self._type(self.PASSWORD, password)
        self._type(self.REPASSWORD, repassword)
        return self

    def register(self, **kwargs):
        return self.fill(**kwargs).submit()


class DashboardStubPage(BasePage):
    """Page object untuk STUB index.php."""

    PATH = "index.php"

    MARKER = (By.ID, "stub-dashboard")
    USERNAME = (By.ID, "stub-username")

    @property
    def is_displayed(self):
        return bool(self.driver.find_elements(*self.MARKER))

    @property
    def session_username(self):
        return self._text_or_empty(self.USERNAME)

    @property
    def is_authenticated(self):
        body = self.driver.find_elements(By.TAG_NAME, "body")
        return bool(body) and body[0].get_attribute("data-authenticated") == "true"
