<?php
    /*
     * Koneksi database.
     *
     * Berbeda dari versi asli, nilai konfigurasi dibaca dari environment
     * variable terlebih dahulu agar modul yang sama dapat dijalankan di mesin
     * lokal (XAMPP) maupun di runner GitHub Actions tanpa mengubah kode modul
     * yang diuji (login.php / register.php). Nilai default identik dengan
     * versi asli sehingga perilaku di lingkungan lokal tidak berubah.
     */
    $host     = getenv('DB_HOST') ?: 'localhost';
    $user     = getenv('DB_USER') ?: 'root';
    $password = getenv('DB_PASS') !== false ? getenv('DB_PASS') : '';
    $db       = getenv('DB_NAME') ?: 'quiz_pengupil';

    $con = mysqli_connect($host, $user, $password, $db);
    if (!$con) {
        die("Connection failed: " . mysqli_connect_error());
    }
?>
