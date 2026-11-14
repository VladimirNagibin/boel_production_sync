<?php
include 'main_function.php';
echo 'hello !';
echo '</br>';
# echo $_SERVER['DOCUMENT_ROOT'];
# Bitrix_help::log_ftp('test', 'test');
echo '</br>';
$result = Contracts::get_number_invoice(1, 'Company', '2021-01-01', '202');
echo $result;

$ftpPortal = getenv('FTP_PORTAL');
$ftpUser = getenv('FTP_USER');
$ftpPass = getenv('FTP_PASS');



# sendupdate1c(111111, 'gnom', 2);


function sendupdate1c($id11, $xml_id11, $fl11)
{
    global $ftpPortal, $ftpUser, $ftpPass;

    // Послать сообщение в 1С об изменении счёта 1 - новый, 2 - изменённый, 0 - удалить Параметры(ид счёта, код 1С, тип события) // Записать JSON по FTP
    $text_invoice = '';
    if ($fl11 == 0) {
        $text_invoice = '{"VIEW":"DELL_INVOICE","ID":' . $id11 . '}';
    } elseif ($fl11 == 1) {
        $text_invoice = '{"VIEW":"NEW_INVOICE","ID":' . $id11 . '}';
    } elseif ($fl11 == 2) {
        $text_invoice = '{"VIEW":"UPDATE_INVOICE","ID":' . $id11 . '}';
    }
   
    // Установка соединения
    $conn_id = ftp_connect($ftpPortal, 21, 30);
    if ($conn_id !== false) {
        if (@ftp_login($conn_id, $ftpUser, $ftpPass) === true) {
            @ftp_mkdir($conn_id, 'Bitrix');

            $remote_file = 'Bitrix/request ' . round(microtime(true) * 1000, 0) . '.txt';
            $file1 = fopen('php://temp', 'r+'); 
            fwrite($file1, $text_invoice);
            rewind($file1);
            ftp_set_option($conn_id, FTP_TIMEOUT_SEC, 30);

            // 1) пассивный режим (адрес из PASV)
            ftp_pasv($conn_id, true);
            $result = @ftp_fput($conn_id, $remote_file, $file1, FTP_ASCII);
            // 2) пассивный режим, IP управляющего соединения
            if (!$result) {
                rewind($file1);
                ftp_set_option($conn_id, FTP_USEPASVADDRESS, false);
                $result = @ftp_fput($conn_id, $remote_file, $file1, FTP_ASCII);
            }
            // 3) активный режим
            if (!$result) {
                rewind($file1);
                ftp_pasv($conn_id, false);
                $result = @ftp_fput($conn_id, $remote_file, $file1, FTP_ASCII);
            }

            if ($result) {
                echo 'File create';
            } else {
                $err = error_get_last();
                echo 'File not create: ' . (isset($err['message']) ? $err['message'] : 'unknown error');
            }

            fclose($file1);
            ftp_close($conn_id);
        }   
    }
}
