<?php
/*
 * ============================================================================
 *  STUB  -  index.php  (Dashboard)
 * ============================================================================
 *
 *  Mengapa stub ini diperlukan?
 *
 *  Modul login.php dan register.php keduanya mengakhiri alur suksesnya dengan
 *  `header('Location: index.php')`. Pada repository asli file index.php TIDAK
 *  ADA, sehingga jalur sukses kedua modul bermuara ke HTTP 404 dan tidak bisa
 *  diverifikasi. readme.md repository asli pun menyatakan
 *  "Diperlukan Stub untuk menguji modul".
 *
 *  Stub ini menggantikan modul dashboard yang belum dibangun. Ia TIDAK berisi
 *  logika bisnis apa pun - hanya membaca $_SESSION dan mengeksposnya lewat
 *  hook DOM yang stabil supaya skrip Selenium dapat memeriksa:
 *
 *    #stub-dashboard              -> penanda bahwa redirect sukses terjadi
 *    #stub-username               -> isi $_SESSION['username']
 *    body[data-authenticated]     -> "true" / "false"
 *
 *  Stub sengaja dibuat "dumb": tidak memvalidasi, tidak menulis ke database,
 *  dan tidak mengubah session. Dengan begitu setiap kegagalan test tetap
 *  menunjuk ke modul yang diuji, bukan ke stub.
 * ============================================================================
 */

session_start();

$username      = isset($_SESSION['username']) ? $_SESSION['username'] : '';
$authenticated = $username !== '';
?>
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>Dashboard (STUB) - Quiz Pengupil</title>
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" crossorigin="anonymous">
<link rel="stylesheet" href="style.css">
</head>
<body data-authenticated="<?= $authenticated ? 'true' : 'false' ?>">
    <section class="container mt-4">
        <div id="stub-dashboard" class="alert alert-success">
            <h4 class="font-weight-bold">Dashboard (STUB)</h4>
            <p class="mb-1">
                Halaman ini adalah <strong>stub</strong> pengganti modul dashboard
                yang belum tersedia pada repository asli.
            </p>
            <p class="mb-0">
                Session username: <span id="stub-username"><?= htmlspecialchars($username, ENT_QUOTES, 'UTF-8') ?></span>
            </p>
        </div>

        <?php if ($authenticated) { ?>
            <a id="stub-logout" class="btn btn-secondary" href="logout.php">Logout</a>
        <?php } else { ?>
            <div id="stub-anonymous" class="alert alert-warning">
                Tidak ada session aktif - halaman diakses tanpa login.
            </div>
            <a class="btn btn-primary" href="login.php">Login</a>
            <a class="btn btn-link" href="register.php">Register</a>
        <?php } ?>
    </section>
</body>
</html>
