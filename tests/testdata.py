"""
Data uji terpusat untuk seluruh test case.

Hash password sengaja di-hardcode (bukan digenerate saat runtime) supaya data
uji bersifat deterministik dan identik antara mesin lokal dan runner CI.
Hash dibuat dengan PHP `password_hash('Test@1234', PASSWORD_DEFAULT)` sehingga
memakai prefix bcrypt `$2y$` yang dikenali `password_verify()` milik PHP.
"""

# --- Akun yang sudah terdaftar (dipakai untuk skenario login) ---------------
VALID_USER = {
    "name": "Test User",
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "Test@1234",
    "hash": "$2y$10$IUgSxip1EvBVuK0oE1YP/ev/N.QtpkS0LGvhI8UF6ECTkfhBDpo4m",
}

# --- Dua akun bawaan dari dump db/quiz_pengupil.sql -------------------------
# Password aslinya tidak diketahui, jadi akun ini hanya dipakai sebagai
# "username yang sudah terpakai" pada skenario registrasi duplikat.
SEED_USERS = [
    {
        "name": "",
        "username": "irul",
        "email": "irul@irul.com",
        "hash": "$2y$10$D9yc9Mt0t8niCNO9di8ejOUPib46suwHghqFnJRKQJ3Z6uwRDxfw.",
    },
    {
        "name": "",
        "username": "ahmad",
        "email": "ahmad@ahmad.com",
        "hash": "$2y$10$OWez2au.UMnz3yedD0BqH.bsOC374XoV9VhMigepVzLyuq2jETHs2",
    },
]

# --- Payload negatif --------------------------------------------------------
SQLI_PAYLOAD = "' OR '1'='1"
WHITESPACE = "   "

# --- Pesan yang diharapkan muncul di UI ------------------------------------
MSG_EMPTY = "Data tidak boleh kosong !!"
MSG_PASSWORD_MISMATCH = "Password tidak sama !!"
MSG_USERNAME_TAKEN = "Username sudah terdaftar !!"
MSG_REGISTER_FAILED = "Register User Gagal !!"

# --- Penanda error PHP yang tidak boleh bocor ke halaman -------------------
PHP_ERROR_MARKERS = (
    "Warning:",
    "Fatal error:",
    "Parse error:",
    "Notice:",
    "Deprecated:",
    "Uncaught",
)
