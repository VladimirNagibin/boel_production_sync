<?php
include 'main_function.php';

// log_ftp("START", 'test');

$bitrixPortal = getenv('BITRIX_PORTAL');
$bitrixToken = getenv('BITRIX_TOKEN');
$bitrixTokenMessage = getenv('BITRIX_TOKEN_MESSAGE');
$grammems_api_key = getenv('GRAMMEMS_API_KEY');

$id     = $_REQUEST['ID'] ?? '';
$slovo1 = $_REQUEST['SLOVO1'] ?? '';
$slovo2 = $_REQUEST['SLOVO2'] ?? '';
$otsrok = $_REQUEST['OTSROK'] ?? '';
$fio    = $_REQUEST['FIO'] ?? '';
$compr  = $_REQUEST['COMPR'] ?? '';
$firm   = $_REQUEST['FIRM'] ?? '';
$firm   = str_replace('CO_','',$firm);
$name   = $_REQUEST['NAME'] ?? '';
$resp   = $_REQUEST['RESP'] ?? ''; 
$sogl   = $_REQUEST['SOGL'] ?? '';
$curCon = $_REQUEST['CURCON'] ?? '';

//Bitrix_help::send_message(215, $hom);     
//$number_new = Contracts::get_number_contract($firm,$name,date("j.n.Y"),$resp);

if (trim($sogl)=="Да") {
   $startP = mb_strpos($curCon, "№"); 
   $endP = mb_strpos($curCon, "от");
   if ($startP !== false && $endP !== false && $endP > $startP) {
       $number_new = trim(mb_substr($curCon, $startP+1, $endP-$startP-1));
   } else {
       $number_new = '';
   }
} else {
$number_new = Contracts::get_number_contract($firm,$name,date("d.m.Y"),$resp); 
}
if ($number_new==''){
   if (trim($sogl)=="Да") {
      Bitrix_help::send_message($resp, 'Нужно запустить <<Выбор договора>> ещё раз'); 
   } else {
       Bitrix_help::send_message($resp, 'Нужно запустить <<Проверку реквизитов договора>> ещё раз'); 
       $result_request = Bitrix_help::request('crm.company.update','id=' . $id . '&fields[UF_CRM_1632315102]=');
   }
}else{
// UF_CRM_1654683828 - номер договора формат НОМЕР/*/ФИРМА   UF_CRM_1631903199 - ФИРМА  UF_CRM_1631941968 - ИД ФИРМЫ

$pol = 's';
$rez_comp_rod = zapros3($compr);
if (count($rez_comp_rod)>0) {
for ($i = 0; $i < count($rez_comp_rod); $i++)
   {
      if ($rez_comp_rod[$i] == 'СР'){
        $pol = 's';
      }
      elseif($rez_comp_rod[$i] == 'МР'){
        $pol = 'm';
      }
      elseif($rez_comp_rod[$i] == 'ЖР'){
        $pol = 'g';
      }
   }    
}
//Bitrix_help::send_message(215, $pol);   
$fioo   = 'declension?s=' . urlencode($fio);
$fio_res = zapros2($fioo);
$fio1   = $fio_res['Р'] ?? $fio;
//send_message(215, $fio1);
$dolgnoct_array = explode(" ", $slovo1);
if (count($dolgnoct_array) == 1)
{
   $dolgnoct = 'declension?s=' . urlencode($slovo1);
   $dolg_res = zapros2($dolgnoct);
   $dolgn = $dolg_res['Р'] ?? $slovo1;
} else
{
   $dolgn = '';
   for ($i = 0; $i < count($dolgnoct_array); $i++)
   {
      $dolgnoct = 'declension?s=' . urlencode($dolgnoct_array[$i]);
      $dolg_res = zapros2($dolgnoct);
      $dolgnTec = $dolg_res['Р'] ?? $dolgnoct_array[$i];
      $dolgn = $dolgn . ' ' . $dolgnTec;
   }
}
$osnovan_array = explode(" ", $slovo2);
if (count($osnovan_array) == 1)
{
   if ($slovo2 == 'ЕГРИП')
   {
      $osnov = 'ЕГРИП';
   } elseif ($slovo2 == 'ОГРН') {
      $osnov = 'ОГРН';
   } elseif ($slovo2 == 'ОГРНИП') {
      $osnov = 'ОГРНИП';
   } else
   {
      $osnovan = 'declension?s=' . urlencode($slovo2); 
      $osnov_res = zapros2($osnovan);
      $osnov = $osnov_res['Р'] ?? $slovo2;
   }
} else
{
   $osnov = '';
   for ($i = 0; $i < count($osnovan_array); $i++)
   {
      if ($osnovan_array[$i] == 'ЕГРИП')
      {
         $osnov = $osnov . ' ' . 'ЕГРИП';
      } elseif ($osnovan_array[$i] == 'ОГРН') {
         $osnov = $osnov . ' ' . 'ОГРН';
      } elseif ($osnovan_array[$i] == 'ОГРНИП') {
         $osnov = $osnov . ' ' . 'ОГРНИП';
      } else
      {
         $osnovan = 'declension?s=' . urlencode($osnovan_array[$i]);
         $osnov_res = zapros2($osnovan);
         $osnovTec = $osnov_res['Р'] ?? $osnovan_array[$i];
         $osnov = $osnov . ' ' . $osnovTec; 
      }
   }
}
//$dolgnoct = 'declension?s='.'Директор';
//$otsrok = 'spell?n='.''.'&unit=рубль';
$otsrok1 = 'spell?n=' . $otsrok . '&unit=рубль';
$otsr_res = zapros2($otsrok1);
$otsr1 = $otsr_res['n']['Р'] ?? $otsrok;
$otsr = $otsrok . '(' . $otsr1 . ')';
//$dolgn = 'Директора'; 
//$osnov = 'Устава';
//$otsr = 'пяти';
$zapros = 'crm.company.update';
$parametr = 'id=' . $id . '&fields[UF_CRM_1632315102]=' . $dolgn . '&fields[UF_CRM_1632315157]=' . $osnov . '&fields[UF_CRM_1632315337]=' . $otsr . '&fields[UF_CRM_1633583719]=' . $fio1. '&fields[UTM_TERM]=' . $pol;
//UF_CRM_1654683828 - номер договора формат НОМЕР/-/ФИРМА   UF_CRM_1631903199 - ФИРМА  UF_CRM_1631941968 - ИД ФИРМЫ
$parametr .= '&fields[UF_CRM_1654683828]=' . $number_new.'|-|'.$firm . '&fields[UF_CRM_1631903199]=' . $firm . '&fields[UF_CRM_1631941968]=' . $firm;
//log_ftp($parametr,'padeg');
$res = zapros($zapros, $parametr); 
{
   if (array_key_exists('error', $res))
      echo $res['error_description'];
   else
   {
   }
}
}
//{           //declension
//  "Р": "Директора",
//  "Д": "Директору",
//  "В": "Директора",
//  "Т": "Директором",
//  "П": "Директоре",
//  "множественное": {
//    "И": "Директора",
//    "Р": "Директоров",
//    "Д": "Директорам",
//    "В": "Директоров",
//    "Т": "Директорами",
//    "П": "Директорах"
//  }
//}

//{          //spell
//  "n": {
//    "И": "пять",
//    "Р": "пяти",
//    "Д": "пяти",
//    "В": "пять",
//    "Т": "пятью",
//    "П": "пяти"
//  },
//  "unit": {
//    "И": "рублей",
//    "Р": "рублей",
//    "Д": "рублям",
//    "В": "рублей",
//    "Т": "рублями",
//    "П": "рублях"
//  }
//}

function zapros($zap, $param) // Выполнение запроса
{
    global $bitrixPortal, $bitrixToken;
    $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . '/' . $zap;

   $queryData = $param;
   $curl = curl_init();
   curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
      CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
      CURLOPT_POSTFIELDS => $queryData, ));
   $result = curl_exec($curl);
   curl_close($curl);
   $result = json_decode($result, 1);
   if (!is_array($result)) {
      return array();
   }
   if (array_key_exists('error', $result))
   {
      echo $result['error_description'];
      log_ftp($zap . ' // ' . $param . ' // ' . $result['error_description'], 'error');
      return array();
   } else
      return $result;
}
function zapros2($param)
{
   $url = 'https://ws3.morpher.ru/russian/' . $param . '&format=json';
   $ch = curl_init($url);
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

   $response = curl_exec($ch);
   curl_close($ch);
   $result = json_decode($response, 1);
   return is_array($result) ? $result : array();
}
function send_message($id_us, $soobch) // Отправить сообщение

{
    global $bitrixPortal, $bitrixTokenMessage;
    $queryUrl = $bitrixPortal . '/rest/' . $bitrixTokenMessage . '/im.message.add';
    $queryData = 'USER_ID=' . $id_us . '&message=' . $soobch; // . '&SYSTEM=Y';
    //echo $queryData;
    $curl = curl_init();
    curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
      CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
      CURLOPT_POSTFIELDS => $queryData, ));
    $result = curl_exec($curl);
    curl_close($curl);
    $result = json_decode($result, 1);
    return $result;
}
function log_ftp($soobch, $fil) // Запись текста в файл по ФТП
{
    global $ftpPortal, $ftpUser, $ftpPass;

    $conn_id = ftp_connect($ftpPortal, 21, 30);
    if ($conn_id === false) {
        echo 'Ошибка подключения к FTP';
        return;
    }

    if (@ftp_login($conn_id, $ftpUser, $ftpPass) === false) {
        echo 'Ошибка авторизации FTP';
        ftp_close($conn_id);
        return;
    }

    @ftp_mkdir($conn_id, 'Bitrix');
    @ftp_mkdir($conn_id, 'Bitrix/Log');

    $remote_file = 'Bitrix/Log/' . $fil . ' ' . round(microtime(true) * 1000, 0) . '.txt';
    $file1 = fopen('php://temp', 'r+');
    fwrite($file1, $soobch);
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
function zapros3($param)
{
    global $grammems_api_key;

   $url = 'https://htmlweb.ru/json/service/grammems/?grammems=' . urlencode($param) . '&api_key=' . urlencode($grammems_api_key);
   $ch = curl_init($url);
   curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

   $response = curl_exec($ch);
   curl_close($ch);
   $result = json_decode($response, 1);
   if (is_array($result) && array_key_exists('info', $result))
   {
       return $result['info']; 
   } else
   {
    log_ftp('https://htmlweb.ru/json/service/grammems/?grammems=' . ' // ' . $param . ' // ' . 'не определился род' , 'error');
    return array();
  }
}
?>
