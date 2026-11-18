<?php
include 'main_function.php';
echo 'hello !';
echo '</br>';
# echo $_SERVER['DOCUMENT_ROOT'];
# Bitrix_help::log_ftp('test', 'test');
echo '</br>';
# $result = Contracts::get_number_invoice(1, 'Company', '2021-01-01', '202');
# echo $result;

$ftpPortal = getenv('FTP_PORTAL');
$ftpUser = getenv('FTP_USER');
$ftpPass = getenv('FTP_PASS');

# Bitrix_help::send_invoice_1C_bp_sync(123, 3);

# sendupdate1c(111111, 'gnom', 2);
