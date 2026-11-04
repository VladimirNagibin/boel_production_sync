<?php
include 'main_function.php';
echo 'hello';
echo '</br>';
$bitrixPortal = getenv('BITRIX_PORTAL');
echo $bitrixPortal;
Bitrix_help::send_message(171, 'test');
