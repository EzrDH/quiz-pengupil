<?php
/*
 * ============================================================================
 *  STUB  -  logout.php
 * ============================================================================
 *
 *  Repository asli tidak menyediakan mekanisme logout, padahal beberapa test
 *  case memerlukan transisi dari kondisi "sudah login" ke "belum login"
 *  (mis. TC-LGN-09 dan TC-LGN-10 yang menguji session guard).
 *
 *  Stub ini hanya menghancurkan session lalu kembali ke login.php. Tidak ada
 *  logika bisnis di dalamnya.
 * ============================================================================
 */

session_start();
$_SESSION = array();
session_destroy();
header('Location: login.php');
exit;
