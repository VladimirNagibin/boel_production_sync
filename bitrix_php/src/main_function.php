<?php
/**
 * @author BOB_140 
 * @copyright 2021
 */

$bitrixPortal = getenv('BITRIX_PORTAL');
$bitrixToken = getenv('BITRIX_TOKEN');
$bitrixTokenMessage = getenv('BITRIX_TOKEN_MESSAGE');
$ftpPortal = getenv('FTP_PORTAL');
$ftpUser = getenv('FTP_USER');
$ftpPass = getenv('FTP_PASS');
$postgresHost = getenv('POSTGRES_HOST');
$postgresPort = getenv('POSTGRES_PORT');
$postgresUser = getenv('POSTGRES_USER');
$postgresPassword = getenv('POSTGRES_PASSWORD');
$postgresDb = getenv('POSTGRES_DB');

class Function_help
{
    public function zapros($zap, $param)
    {
        global $bitrixPortal, $bitrixToken;
        $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . $zap;
        $queryData = $param;
        $curl = curl_init();
        curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
            CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
            CURLOPT_POSTFIELDS => $queryData));
        $result = curl_exec($curl);
        curl_close($curl);
        $result = json_decode($result, 1);
        if (!is_array($result)) {
            return array();
        }
        if (array_key_exists('error', $result)) {
            echo $result['error_description'];
            $this->log_ftp($zap . ' // ' . $param . ' // ' . $result['error_description'], 'error');
            return array();
        } else {
            return $result;
        }

    }
    public function log_ftp($soobch, $fil)
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
    public function have_right($user_tec)
    {
        $res_right = 0;
        if (($user_tec == '169') or ($user_tec == '35') or ($user_tec == '645') or ($user_tec == '171') or ($this->departuser($user_tec) == '43')) {
            $res_right = 1;
        }

        return $res_right;
    }
    public function send_message($id_us, $soobch)
    {
        global $bitrixPortal, $bitrixTokenMessage;
        $queryUrl = $bitrixPortal . '/rest/' . $bitrixTokenMessage . '/im.message.add';
        $queryData = 'USER_ID=' . $id_us . '&message=' . $soobch; // . '&SYSTEM=Y';
        //echo $queryData;
        $curl = curl_init();
        curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
            CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
            CURLOPT_POSTFIELDS => $queryData));
        $result = curl_exec($curl);
        curl_close($curl);
        $result = json_decode($result, 1);
        return $result;
    }
    public function departuser($iduser)
    {
        $result1 = '_';
        $zapros = 'user.get';
        $parametr = 'id=' . $iduser;
        $res = $this->zapros($zapros, $parametr);
        {
            if (count($res) > 0) {
                $result1 = $res['result'][0]['UF_DEPARTMENT'][0];
            }

        }
        return $result1;
    }
    public function products_upd_deal($product_rows_array1, $product_deal_array1, $iddeal1)
    { // Перегрузить товары из счёта в сделку (запрос)) 1 - есть изменения, 0 - нет
        $result21 = 0; // Записать обновление товаров ($product_rows_array1 - оригинал)
        if (count($product_rows_array1) != count($product_deal_array1)) {
            $result21 = 1;
        } else {
            for ($i = 0; $i < count($product_rows_array1); $i++) {
                //$tektax = $product_rows_array1[$i][VAT_RATE] * 100;
                if (($product_rows_array1[$i]['PRODUCT_ID'] != $product_deal_array1[$i]['PRODUCT_ID']) or ($product_rows_array1[$i]['QUANTITY'] != $product_deal_array1[$i]['QUANTITY'])
                    or ($product_rows_array1[$i]['PRICE'] != $product_deal_array1[$i]['PRICE']) or ($product_rows_array1[$i]['TAX_INCLUDED'] != $product_deal_array1[$i]['TAX_INCLUDED'])
                    or ($product_rows_array1[$i]['TAX_RATE'] != $product_deal_array1[$i]['TAX_RATE']) or ($product_rows_array1[$i]['MEASURE_CODE'] != $product_deal_array1[$i]['MEASURE_CODE'])
                    or ($product_rows_array1[$i]['MEASURE_NAME'] != $product_deal_array1[$i]['MEASURE_NAME']) or ($product_rows_array1[$i]['PRODUCT_NAME'] != $product_deal_array1[$i]['PRODUCT_NAME'])
                    or ($product_rows_array1[$i]['CUSTOMIZED'] != $product_deal_array1[$i]['CUSTOMIZED'])) {
                    $result21 = 1;
                }
            }
        }
        if ($result21 == 1) { // Обновляем
            $zapros = 'crm.deal.productrows.set';
            $parametr = 'id=' . $iddeal1;
            for ($i = 0; $i < count($product_rows_array1); $i++) {
                //$tektax = $product_rows_array1[$i][VAT_RATE] * 100;
                /*$parametr = $parametr . '&rows[' . $i . '][PRODUCT_ID]=' . $product_rows_array1[$i][productId] . '&rows[' . $i . '][QUANTITY]=' . $product_rows_array1[$i][quantity] .
                '&rows[' . $i . '][PRICE]=' . $product_rows_array1[$i][price] . '&rows[' . $i . '][TAX_INCLUDED]=' . $product_rows_array1[$i][taxIncluded] .
                '&rows[' . $i . '][TAX_RATE]=' . $product_rows_array1[$i][taxRate] . '&rows[' . $i . '][MEASURE_CODE]=' . $product_rows_array1[$i][measureCode] .
                '&rows[' . $i . '][MEASURE_NAME]=' . $product_rows_array1[$i][measureName] . '&rows[' . $i . '][PRODUCT_NAME]=' . $product_rows_array1[$i][productName] .
                '&rows[' . $i . '][CUSTOMIZED]=' . $product_rows_array1[$i][customized]. '&rows[' . $i . '][PRICE_EXCLUSIVE]=' . $product_rows_array1[$i][priceExclusive] .
                '&rows[' . $i . '][PRICE_NETTO]=' . $product_rows_array1[$i][priceNetto] . '&rows[' . $i . '][PRICE_BRUTTO]=' . $product_rows_array1[$i][priceBrutto] .
                '&rows[' . $i . '][DISCOUNT_TYPE_ID]=' . $product_rows_array1[$i][discountTypeId] . '&rows[' . $i . '][DISCOUNT_RATE]=' . $product_rows_array1[$i][discountRate] .
                '&rows[' . $i . '][DISCOUNT_SUM]=' . $product_rows_array1[$i][discountSum] ;
                 */
                $parametr = $parametr . '&rows[' . $i . '][PRODUCT_ID]=' . $product_rows_array1[$i]['PRODUCT_ID'] . '&rows[' . $i . '][QUANTITY]=' . $product_rows_array1[$i]['QUANTITY'] .
                    '&rows[' . $i . '][PRICE]=' . $product_rows_array1[$i]['PRICE'] . '&rows[' . $i . '][TAX_INCLUDED]=' . $product_rows_array1[$i]['TAX_INCLUDED'] .
                    '&rows[' . $i . '][TAX_RATE]=' . $product_rows_array1[$i]['TAX_RATE'] . '&rows[' . $i . '][MEASURE_CODE]=' . $product_rows_array1[$i]['MEASURE_CODE'] .
                    '&rows[' . $i . '][MEASURE_NAME]=' . $product_rows_array1[$i]['MEASURE_NAME'] . '&rows[' . $i . '][PRODUCT_NAME]=' . $product_rows_array1[$i]['PRODUCT_NAME'] .
                    '&rows[' . $i . '][CUSTOMIZED]=' . $product_rows_array1[$i]['CUSTOMIZED'] . '&rows[' . $i . '][PRICE_EXCLUSIVE]=' . $product_rows_array1[$i]['PRICE_EXCLUSIVE'] .
                    '&rows[' . $i . '][PRICE_NETTO]=' . $product_rows_array1[$i]['PRICE_NETTO'] . '&rows[' . $i . '][PRICE_BRUTTO]=' . $product_rows_array1[$i]['PRICE_BRUTTO'] .
                    '&rows[' . $i . '][DISCOUNT_TYPE_ID]=' . $product_rows_array1[$i]['DISCOUNT_TYPE_ID'] . '&rows[' . $i . '][DISCOUNT_RATE]=' . $product_rows_array1[$i]['DISCOUNT_RATE'] .
                    '&rows[' . $i . '][DISCOUNT_SUM]=' . $product_rows_array1[$i]['DISCOUNT_SUM'];
            }
            $res = $this->zapros($zapros, $parametr);
            //log_ftp($zapros.' :: '.$parametr, 'product');
            {
                if (count($res) > 0) {}
            }
        }
        return $result21; //
    }
}

class Contracts
{
    // Соединение с FTP
    private static function ftp_connect()
    {
        global $ftpPortal, $ftpUser, $ftpPass;

        $conn_id = ftp_connect($ftpPortal, 21, 30);
        if ($conn_id === false) {
            return false;
        }

        if (@ftp_login($conn_id, $ftpUser, $ftpPass) === false) {
            ftp_close($conn_id);
            return false;
        }

        ftp_set_option($conn_id, FTP_TIMEOUT_SEC, 30);
        ftp_pasv($conn_id, true);

        return $conn_id;
    }
    // Проверка существования файла на FTP
    private static function ftp_file_exists($conn_id, $remote_file)
    {
        return @ftp_size($conn_id, $remote_file) !== -1;
    }
    // Чтение содержимого файла с FTP
    private static function ftp_get_contents($conn_id, $remote_file)
    {
        $stream = fopen('php://temp', 'r+');

        // 1) пассивный режим (адрес из PASV)
        ftp_pasv($conn_id, true);
        $result = @ftp_fget($conn_id, $stream, $remote_file, FTP_ASCII);

        // 2) пассивный режим, IP управляющего соединения
        if (!$result) {
            rewind($stream);
            ftruncate($stream, 0);
            ftp_set_option($conn_id, FTP_USEPASVADDRESS, false);
            $result = @ftp_fget($conn_id, $stream, $remote_file, FTP_ASCII);
        }

        // 3) активный режим
        if (!$result) {
            rewind($stream);
            ftruncate($stream, 0);
            ftp_pasv($conn_id, false);
            $result = @ftp_fget($conn_id, $stream, $remote_file, FTP_ASCII);
        }

        if (!$result) {
            fclose($stream);
            return false;
        }

        rewind($stream);
        $contents = stream_get_contents($stream);
        fclose($stream);

        return $contents;
    }
    // Запись содержимого в файл на FTP
    private static function ftp_put_contents($conn_id, $remote_file, $contents)
    {
        $stream = fopen('php://temp', 'r+');
        fwrite($stream, $contents);
        rewind($stream);

        // 1) пассивный режим (адрес из PASV)
        ftp_pasv($conn_id, true);
        $result = @ftp_fput($conn_id, $remote_file, $stream, FTP_ASCII);

        // 2) пассивный режим, IP управляющего соединения
        if (!$result) {
            rewind($stream);
            ftp_set_option($conn_id, FTP_USEPASVADDRESS, false);
            $result = @ftp_fput($conn_id, $remote_file, $stream, FTP_ASCII);
        }

        // 3) активный режим
        if (!$result) {
            rewind($stream);
            ftp_pasv($conn_id, false);
            $result = @ftp_fput($conn_id, $remote_file, $stream, FTP_ASCII);
        }

        fclose($stream);

        return $result;
    }
    // Удаление файла на FTP
    private static function ftp_delete_file($conn_id, $remote_file)
    {
        return @ftp_delete($conn_id, $remote_file);
    }
    // Разбиение содержимого файла на строки (аналог file())
    private static function file_lines($contents)
    {
        $lines = preg_split('/\r\n|\n|\r/', $contents);

        // Убираем последний пустой элемент, который появляется из-за завершающего перевода строки
        while (count($lines) > 0 && $lines[count($lines) - 1] === '') {
            array_pop($lines);
        }

        return $lines;
    }
    // файл найден - занято(false), файл не найден - свободно(true)
    private static function get_busy_contracts()
    {
        $conn_id = self::ftp_connect();
        if ($conn_id === false) {
            return false; // Нет связи с FTP - считаем, что занято
        }

        $exists = self::ftp_file_exists($conn_id, 'flag.txt');
        ftp_close($conn_id);

        return !$exists;
    }
    // создаём файл-флаг на FTP
    private static function set_busy_contracts()
    {
        $conn_id = self::ftp_connect();
        if ($conn_id === false) {
            return;
        }

        self::ftp_put_contents($conn_id, 'flag.txt', date('Y-m-d H:i:s'));
        ftp_close($conn_id);
    }
    // удаляем файл-флаг с FTP
    private static function set_free_contracts()
    {
        $conn_id = self::ftp_connect();
        if ($conn_id === false) {
            return;
        }

        self::ftp_delete_file($conn_id, 'flag.txt');
        ftp_close($conn_id);
    }
    public static function get_number_contract($firma, $company, $datecontract, $id_us)
    {
        // Bitrix_help::send_message(215, 'Старт ');
        //$function_message = new Function_help();
        $id_us = 215;
        $new_number = '';
        if ($firma == '8923') { // Системы
            $new_number = 'б/н';
        } else {
            $flbusy = self::get_busy_contracts();

            $attempt = 0;
            while (!($flbusy)) {
                $attempt = $attempt + 1;
                sleep(5);
                $flbusy = self::get_busy_contracts();
                if ($attempt > 3) {
                    Bitrix_help::send_message($id_us, 'Реестр договоров занят. Попробуйте ещё раз');
                    self::set_free_contracts();
                    //return '';
                    //break;
                    //exit();
                }
            }
            //Bitrix_help::send_message(215, 'Старт '.$flbusy);
            if ($flbusy) {
                //  $array_my_company = array('439' => '8923', '441' => '5385', '443' => '5383', '445' => '5381', '447' => '8895');
                //  $array_my_company_name = array('439' => 'Системы', '441' => 'Элемент', '443' => 'Торговый дом СР', '445' => 'ТехТорг', '447' => 'ИП Гузиков М.Г.');
                self::set_busy_contracts();
                $filereestr = '';
                $filestart = 'Contracts/';
                if ($firma == '5381') { // ТехТорг
                    $filereestr = $filestart . "RegisterOfContractsTT.txt";
                } elseif ($firma == '5385') { // Элемент
                    $filereestr = $filestart . "RegisterOfContractsEL.txt";
                } elseif ($firma == '5383') { // ТД СР
                    $filereestr = $filestart . "RegisterOfContractsSR.txt";
                } elseif ($firma == '22145') { // ИП Гузиков
                    $filereestr = $filestart . "RegisterOfContractsGZ.txt";
                } elseif ($firma == '8897') { // Эксперты розлива
                    $filereestr = $filestart . "RegisterOfContractsER.txt";
                } elseif ($firma == '23217') { // ИП Воробьев
                    $filereestr = $filestart . "RegisterOfContractsVR.txt";

                } else {
                    //$function_message->send_message($id_us, 'Для фирмы '.$firma.' нет реестра договоров');
                    Bitrix_help::send_message($id_us, 'Для фирмы ' . $firma . ' нет реестра договоров');
                }
                if ($filereestr != '') {
                    $conn_id = self::ftp_connect();
                    if ($conn_id !== false) {
                        $contents = self::ftp_get_contents($conn_id, $filereestr);
                        if ($contents !== false) {
                            $arrcontracts = self::file_lines($contents);
                            if (count($arrcontracts) > 0) {
                                $lastcontract = $arrcontracts[count($arrcontracts) - 1];
                                $arrnumber = explode("/**/", $lastcontract);
                                $lastnumber = $arrnumber[0];
                            } else {
                                $lastnumber = 0;
                            }
                            $lastnumber = str_replace('/54', '', $lastnumber);
                            $lastnumber = str_replace('ЭР', '', $lastnumber);
                            $lastnumber = str_replace('ВР', '', $lastnumber);
                            $new_number = $lastnumber + 1;
                            if ($firma == '5381') { // ТехТорг
                                $new_number = $new_number . '/54';
                            }
                            if ($firma == '8897') { // Эксперты розлива
                                $new_number = 1000000 + $new_number;
                                $new_number = ltrim($new_number, '1');
                                $new_number = 'ЭР' . $new_number;
                            }
                            if ($firma == '23217') { // Воробьёв
                                $new_number = 1000000 + $new_number;
                                $new_number = ltrim($new_number, '1');
                                $new_number = 'ВР' . $new_number;
                            }
                            $strcontract = $new_number . '/**/' . $datecontract . '/**/' . $company;
                            self::ftp_put_contents($conn_id, $filereestr, $contents . PHP_EOL . $strcontract);
                        }
                        ftp_close($conn_id);
                    }
                }
                self::set_free_contracts();
            } else {
                Bitrix_help::send_message($id_us, 'Реестр договоров занят. Попробуйте ещё раз');
            }
        }
        return $new_number;
    }
    public static function get_number_invoice($firma, $company, $datecontract, $id_us)
    {
        $id_us = 215;
        $new_number = '';
        $flbusy = self::get_busy_contracts();
        //Bitrix_help::send_message(215, 'Старт '.$flbusy);
        $attempt = 0;
        while (!($flbusy)) {
            $attempt = $attempt + 1;
            sleep(5);
            $flbusy = self::get_busy_contracts();
            if ($attempt > 1) {
                Bitrix_help::send_message($id_us, 'Реестр номеров счетов занят. Попробуйте ещё раз');
                self::set_free_contracts();
                //return $new_number;
                //break;
                //exit();
            }
        }
        if ($flbusy) {
            //  $array_my_company = array('439' => '8923', '441' => '5385', '443' => '5383', '445' => '5381', '447' => '8895');
            //  $array_my_company_name = array('439' => 'Системы', '441' => 'Элемент', '443' => 'Торговый дом СР', '445' => 'ТехТорг', '447' => 'ИП Гузиков М.Г.');
            self::set_busy_contracts();
            $filereestr = '';
            $filestart = 'Contracts/';
            if ($firma == '5381') { // ТехТорг
                $filereestr = $filestart . "RegisterOfContractsTT1.txt";
            } elseif ($firma == '5385') { // Элемент
                $filereestr = $filestart . "RegisterOfContractsEL1.txt";
            } elseif ($firma == '5383') { // ТД СР
                $filereestr = $filestart . "RegisterOfContractsSR1.txt";
            } elseif ($firma == '22145') { // ИП Гузиков
                $filereestr = $filestart . "RegisterOfContractsGZ1.txt";
            } elseif ($firma == '8897') { // Эксперты розлива
                $filereestr = $filestart . "RegisterOfContractsER1.txt";
            } elseif ($firma == '23217') { // ИП Воробьев
                $filereestr = $filestart . "RegisterOfContractsVR1.txt";
            } elseif ($firma == '8923') { // Системы
                $filereestr = $filestart . "RegisterOfContractsCI1.txt";
            } else {
                //$function_message->send_message($id_us, 'Для фирмы '.$firma.' нет реестра договоров');
                Bitrix_help::send_message($id_us, 'Для фирмы ' . $firma . ' нет реестра номеров счетов');
            }
            if ($filereestr != '') {
                $conn_id = self::ftp_connect();
                if ($conn_id !== false) {
                    $contents = self::ftp_get_contents($conn_id, $filereestr);
                    if ($contents !== false) {
                        $arrcontracts = self::file_lines($contents);
                        if (count($arrcontracts) > 0) {
                            $lastcontract = $arrcontracts[count($arrcontracts) - 1];
                            $arrnumber = explode("/**/", $lastcontract);
                            $lastnumber = $arrnumber[0];
                        } else {
                            $lastnumber = 0;
                        }
                        //ТД000000597   ТД СР
                        //El000000583   Элемент
                        //ТТ000000338   ТехТорг
                        //ГМ000000090   ИП ГМ
                        //СУ000000712   Системы
                        $prefix = '';
                        if ($firma == '5381') { // ТехТорг
                            $prefix = 'ТТ';
                        } elseif ($firma == '5385') { // Элемент
                            $prefix = 'El';
                        } elseif ($firma == '5383') { // ТД СР
                            $prefix = 'ТД';
                        } elseif ($firma == '22145') { // ИП Гузиков
                            $prefix = 'ГМ';
                        } elseif ($firma == '8897') { // Эксперты розлива
                            $prefix = 'ЭР';
                        } elseif ($firma == '23217') { // ИП Воробьев
                            $prefix = 'ВР';                    
                        } elseif ($firma == '8923') { // Системы
                            $prefix = 'СУ';
                        }
                        $tr = $lastnumber;
                        $tr = str_replace($prefix, '', $tr);
                        $tr = $tr + 1;
                        $tr = sprintf("%'.09d", $tr);
                        $new_number = $prefix . $tr;

                        $strcontract = $new_number . '/**/' . $datecontract . '/**/' . $company;
                        self::ftp_put_contents($conn_id, $filereestr, $contents . PHP_EOL . $strcontract);
                    }
                    ftp_close($conn_id);
                }
            }
            self::set_free_contracts();
        } else {
            Bitrix_help::send_message($id_us, 'Реестр номеров счетов занят. Попробуйте ещё раз'); 
        }
        return $new_number;
    }
}

class b24Exception extends Exception
{

}

class Bitrix_help 
{
    private static $nameServiceMan = 121; // А Галанова
    private static $nameObserverService = 215; // Служебный 
    private static $idStorageMan = array('479' => '175', '481' => '175', '483' => '215', '485' => '29', '487' => '319'); // Оля ; Оля ; ??? ; Гузиков ; Коротких 
    private static $nameStorage = array('479' => 'Склад Нск', '481' => 'Склад Нск', '483' => 'Склад Спб', '485' => 'Склад Кдр', '487' => 'Склад Мск');
    
    public static function request($zap, $param)
    {
        global $bitrixPortal, $bitrixToken;
        $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . $zap;

        $queryData = $param;
        $curl = curl_init();
        curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
            CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
            CURLOPT_POSTFIELDS => $queryData));
        $result = curl_exec($curl);
        curl_close($curl);
        $result = json_decode($result, 1);
        if (!is_array($result)) {
            return array();
        }
        if (array_key_exists('error', $result)) {
            //echo $result['error_description'];
            self::log_ftp($zap . ' // ' . $param . ' // ' . $result['error_description'], 'error');
            return array();
        } else {
            //if (array_key_exists('result', $result)) {
            return $result;
            //} else {
            //   return array();
            //}
        }
    }
    public static function executeRequest($zap, $param)
    {
        global $bitrixPortal, $bitrixToken;
        $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . $zap; 
        $queryData = $param;
        $curl = curl_init();
        curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
            CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
            CURLOPT_POSTFIELDS => $queryData));
        $result = curl_exec($curl);
        curl_close($curl);
        $result = json_decode($result, 1);
        if (!is_array($result)) {
            self::log_ftp($zap . ' // ' . $param . ' // ' . 'Ошибка получения ответа Bitrix24 API', 'error');
            throw new b24Exception('Ошибка получения ответа Bitrix24 API');
        }
        if (array_key_exists('error', $result)) {
            //echo $result['error_description'];
            self::log_ftp($zap . ' // ' . $param . ' // ' . $result['error_description'], 'error');
            //throw new b24Exception($result['error_description'], 0, $severity, $filename, $lineno);
            throw new b24Exception($result['error_description']);           
            //return array();
        } else {
            //if (array_key_exists('result', $result)) {
            return $result;
            //} else {
            //   return array();
            //}
        }
    }
    public static function log_ftp($soobch, $fil)
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
    public static function send_message($id_us, $soobch)
    {
        global $bitrixPortal, $bitrixTokenMessage;
        $queryUrl = $bitrixPortal . '/rest/' . $bitrixTokenMessage . '/im.message.add';
        $queryData = 'USER_ID=' . $id_us . '&message=' . $soobch; // . '&SYSTEM=Y';
        //echo $queryData;
        $curl = curl_init();
        curl_setopt_array($curl, array(CURLOPT_SSL_VERIFYPEER => 0, CURLOPT_POST => 1,
            CURLOPT_HEADER => 0, CURLOPT_RETURNTRANSFER => 1, CURLOPT_URL => $queryUrl,
            CURLOPT_POSTFIELDS => $queryData));
        $result = curl_exec($curl);
        curl_close($curl);
        $result = json_decode($result, 1);
        return $result;
    }
    private static $pdo = null;

    private static function getPdo()
    {
        if (self::$pdo instanceof PDO) {
            return self::$pdo;
        }

        global $postgresHost, $postgresPort, $postgresUser, $postgresPassword, $postgresDb;

        $host = $postgresHost ?: 'localhost';
        $port = $postgresPort ?: '5432';

        self::$pdo = new PDO(
            "pgsql:host={$host};port={$port};dbname={$postgresDb}",
            $postgresUser,
            $postgresPassword,
            array(
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            )
        );

        return self::$pdo;
    }

    private static function sql_quote($value)
    {
        return "'" . str_replace("'", "''", (string) $value) . "'";
    }

    public static function request_sql($sql)
    {
        try {
            $stmt = self::getPdo()->query($sql);

            if ($stmt->columnCount() > 0) {
                return $stmt->fetchAll();
            }

            return $stmt->rowCount();
        } catch (PDOException $e) {
            self::log_ftp("Ошибка: Невозможно выполнить запрос к PostgreSQL " . $e->getMessage(), 'sql');
            return array();
        }
    }
    public static function check_permission($id_company, $id_deal, $id_firm, $id_product, $payment_type, $price, $paymemtTerm)
    {
        $fl_permission = false;
        if ($payment_type == 495) { // Отсрочка
            $sql = 'SELECT price, payment_term FROM price_permisson WHERE id_company=' . $id_company . ' AND id_product=' . $id_product . ' AND id_firm=' . $id_firm . ' AND payment_type=' . $payment_type;
            //self::send_message(215, $sql);
            $res = self::request_sql($sql);
            foreach ($res as $row) {
                if (($row['price'] <= $price) && ($row['payment_term'] >= $paymemtTerm)) {
                    $fl_permission = true;
                }
            }
        } elseif ($payment_type == 493) { // Предоплата
            $sql = 'SELECT price FROM price_permisson WHERE id_company=' . $id_company . ' AND id_product=' . $id_product . ' AND id_firm=' . $id_firm;
            $res = self::request_sql($sql);
            foreach ($res as $row) {
                
                if ($row['price'] <= $price) {
                    $fl_permission = true;
                }
            }
        } elseif ($payment_type == 497) { // Частичная
            $sql = 'SELECT price, payment_term FROM price_permisson WHERE id_company=' . $id_company . ' AND id_product=' . $id_product . ' AND id_firm=' . $id_firm . ' AND payment_type=' . $payment_type;
            $res = self::request_sql($sql);
            foreach ($res as $row) {
                if (($row['price'] <= $price) && ($row['payment_term'] >= $paymemtTerm)) {
                    $fl_permission = true;
                }
            }
            if (!$fl_permission) {
                $sql = 'SELECT price, payment_term FROM price_permisson WHERE id_company=' . $id_company . ' AND id_product=' . $id_product . ' AND id_firm=' . $id_firm . ' AND payment_type=495';
                $res = self::request_sql($sql);
                foreach ($res as $row) {
                    if (($row['price'] <= $price) && ($row['payment_term'] >= $paymemtTerm)) {
                        $fl_permission = true;
                    }
                }
            }
        }
        return $fl_permission;
    }
    public static function prmin($idproduct)
    {
        $result1 = 0;
        $zapros = 'crm.product.get';
        $parametr = 'id=' . $idproduct;
        $res = self::request($zapros, $parametr);
        {
            if (array_key_exists('error', $res)) {}
            //echo $res['error_description'];
            else {
                $result1 = $res['result']['PROPERTY_123']['value'];
            }

            $result1 = str_replace(chr(194) . chr(160), '', $result1);
        }
        return $result1;
    }
    public static function departuser($iduser)
    {
        $result1 = '_';
        $zapros = 'user.get';
        $parametr = 'id=' . $iduser;
        $res = self::request($zapros, $parametr);
        {
            if (array_key_exists('error', $res)) {}
            //echo $res['error_description'];
            else {
                $result1 = $res['result'][0]['UF_DEPARTMENT'][0];
            }

        }
        return $result1;
    }
    public static function nameuser($iduser)
    {
        $result1 = '_';
        $zapros = 'user.get';
        $parametr = 'id=' . $iduser;
        $res = self::request($zapros, $parametr);
        {
            if (array_key_exists('error', $res)) {}
            //echo $res['error_description'];
            else {
                $result1 = $res['result'][0]['NAME'] . ' ' . $res['result'][0]['LAST_NAME'];
            }
        }
        return $result1;
    }
    public static function is_empty_value($value)
    {
        if ((is_null($value)) or ($value == '') or ($value == 0) or ($value == '0')) {
            return 0;
        } else {
            return 1;
        }
    }
    public static function getStorageMan($idStorage)
    {
        if (array_key_exists($idStorage, self::$idStorageMan)) {
            return self::$idStorageMan[$idStorage];
        } else {
            return null;
        }
    }
    public static function get_service_man()
    {
        return self::$nameServiceMan;
    }
    public static function setObserverDeal($idDeal, $idUserObserver, $typeAction)
    {
        //if $typeAction = 1 add else delete
        $parameter = 'TEMPLATE_ID=193&DOCUMENT_ID[0]=crm&DOCUMENT_ID[1]=CCrmDocumentDeal&DOCUMENT_ID[2]=DEAL_' . $idDeal;
        $parameter .= '&PARAMETERS[Observer]=user_' . $idUserObserver . '&PARAMETERS[TypeActtion]=' . $typeAction;
        self::request('bizproc.workflow.start', $parameter);
    }
    public static function sendUpdate1c($view, $idEntity)
    {
        global $ftpPortal, $ftpUser, $ftpPass;
        $text_invoice = '{"VIEW":"' . $view . '","ID":' . $idEntity . '}';

        // Установка соединения
        $conn_id = ftp_connect($ftpPortal);
        if ($conn_id === false) {
            return;
        }
        $login_result = ftp_login($conn_id, $ftpUser, $ftpPass);
        ftp_pasv($conn_id, true);
        ftp_set_option($conn_id, FTP_TIMEOUT_SEC, 30);

        // Создание файла на сервере
        $file1 = fopen('php://temp', 'r+');
        fwrite($file1, $text_invoice);
        rewind($file1);

        if (@ftp_fput($conn_id, 'Bitrix/request ' . round(microtime(true) * 1000, 0) . '.txt', $file1, FTP_ASCII)) {
            //echo 'File create';
        } else {
            self::logFtp('File not create ' . $text_invoice, 'Error FTP');
        }
        ftp_close($conn_id);
    }

    public static function sendUpdate1c_($view, $idEntity)
    {
        global $ftpPortal, $ftpUser, $ftpPass;
        $text_invoice = '{"VIEW":"' . $view . '","ID":' . $idEntity . '}';

        // Установка соединения
        $conn_id = ftp_connect($ftpPortal);
        if ($conn_id === false) {
            return false;
        }
        $login_result = ftp_login($conn_id, $ftpUser, $ftpPass);
        ftp_pasv($conn_id, true);
        ftp_set_option($conn_id, FTP_TIMEOUT_SEC, 30);

        // Создание файла на сервере
        $file1 = fopen('php://temp', 'r+');
        fwrite($file1, $text_invoice);
        rewind($file1);

        if (@ftp_fput($conn_id, 'Bitrix/request ' . round(microtime(true) * 1000, 0) . '.txt', $file1, FTP_ASCII)) {
            $res = TRUE;
        } else {
            self::logFtp('File not create ' . $text_invoice, 'Error FTP');
            $res = FALSE;
        }
        ftp_close($conn_id);
        return $res;
    }

    public static function logFtp($soobch, $fil)
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
    public static function getStorageName($idStorage)
    {
        if (array_key_exists($idStorage, self::$nameStorage)) {
            return self::$nameStorage[$idStorage];
        } else {
            return null;
        }
        //return 'Основной склад';
    }
    public static function getObserverService()
    {
        return self::$nameObserverService;
    }
    public static function getCommentsDeal($idDeal)
    {
        $commentDeal = '';
        $sql = 'SELECT comments FROM deal_comments WHERE id_deal = ' . $idDeal;
        $result = self::request_sql($sql);
        foreach ($result as $row) {
            $commentDeal = $row['comments'];
        }
        return $commentDeal;
    }
    public static function setCommentsDeal($idDeal, $comment)
    {
        $sqlDel = 'DELETE FROM deal_comments WHERE id_deal = ' . $idDeal;
        $resultDel = self::request_sql($sqlDel);
        $sql = 'INSERT INTO deal_comments (id_deal, comments) VALUES (' . $idDeal . ', ' . self::sql_quote($comment) . ')';
        $result = self::request_sql($sql);
        return $result;
    }
    public static function getProductsDeal($idDeal)
    {
        // Массив товаров из сделки
        $result21 = array();
        $res = self::request('crm.deal.productrows.get', 'id=' . $idDeal);
        {
            if (count($res) > 0) {
                $result21 = $res['result'];
            }
        }
        return $result21;
    }
    public static function getAdditionalInfoDeal($idDeal)
    {
        $commentDeal = '';
        $sql = 'SELECT additional_info FROM deal_site_additional_info WHERE id_deal = ' . $idDeal;
        $result = self::request_sql($sql);
        foreach ($result as $row) {
            $commentDeal = $row['additional_info'];
        }
        return $commentDeal;
    }
    public static function setAdditionalInfoDeal($idDeal, $comment)
    {
        $sqlDel = 'DELETE FROM deal_site_additional_info WHERE id_deal = ' . $idDeal;
        $resultDel = self::request_sql($sqlDel);
        $sql = 'INSERT INTO deal_site_additional_info (id_deal, additional_info) VALUES (' . $idDeal . ', ' . self::sql_quote($comment) . ')';
        $result = self::request_sql($sql);
        return $result;
    }
    public static function getUserPermitShipment($idInvioce)
    {
        $userPermit = 215; // Служебный пользователь
        $accountUser = 115; // Люба
        $cashNsk = 115; // Люба
        $cashSpb = 11; // Рома
        $cashKdr = 29; // Миша
        $cashMsk = 877; // Шатских
        $headSales = 645; // Ильдар
        $headNsk = 759; // Илья
        $headSpb = 877; // Шатских
        $headKdr = 29; // Миша
        $headMsk = 877; // Шатских
        $headOpt = 31; // Матвеев

        $cashUserStore = array('479' => $cashNsk, '481' => $cashNsk, '483' => $cashSpb, '485' => $cashKdr, '487' => $cashMsk);
        $headUserDepart = array('423' => $headOpt, '417' => $headMsk, '415' => $headSpb, '421' => $headNsk, '419' => $headKdr);

        $res1 = self::request('crm.item.get', "entityTypeId=31&id=$idInvioce");
        if (count($res1) > 0) {
            // Если получены поля счёта тогда обработка
            $res = $res1['result']['item'];
            /*
            $uf_deal_id      = $res[parentId2]; // Ид сделки
            $uf_mycompany_id = $res[mycompanyId]; // Ид нашей фирмы
            $uf_company_id   = $res[companyId]; // Ид покупателя
            $uf_contact_id   = $res[contactId]; // Ид контакта
            $order_topic     = $res[title]; // Заголовок счёта
            $status_id       = $res[stageId]; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
            $tec_stage_prev  = $res[previousStageId]; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
            $xml_id          = $res[xmlId]; // Код из 1С
            $srok_opl        = $res[closedate]; // Срок оплаты
            $srok_opl        = substr($srok_opl, 0, 10); // Оставляем только дату
            $tec_stage       = $res[ufCrmSmartInvoice1651509493]; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
            $check_respit    = $res[ufCrmSmartInvoice1651138836085]; // Разрешение на отгрузку: Да = 1; Нет = 0
            $payments        = $res[ufCrmSmartInvoice1651116689037]; // Платёжки по счёту
            $id_pech_form    = $res[ufCrmSmartInvoice1651138396589]; // Ид сформированной печатной формы
             */
            $responsible_id = $res['assignedById']; // Ответственный
            $tip_opl = $res['ufCrm_SMART_INVOICE_1651114959541']; // Тип оплаты счёта: 493 - Предоплата; 495 - Отсрочка; 497 - Частичная
            $forma_opl = $res['ufCrm_SMART_INVOICE_1651083629638']; // Форма оплаты Нал/Безнал  489 - Безналичные    491    - Наличные
            $idStore = $res['ufCrm_SMART_INVOICE_1651083239729']; // Склад 479 - Склад Нск 481 - Склад Дистр    483 - Склад Спб    485 - Склад Кдр    487 - Склад Мск
            $paymemtTermInv = $res['ufCrm_SMART_INVOICE_1656584515597']; // Отсрочка в счёте Число

            if ($tip_opl == 493) {
                // Предоплата
                if ($forma_opl == 489) {
                    // Безнал
                    $userPermit = $accountUser;
                } else {
                    // Нал
                    if (array_key_exists($idStore, $cashUserStore)) {
                        $userPermit = $cashUserStore[$idStore];
                    }
                }
            } else {
                // Отсрочка
                if ($paymemtTermInv > 14) {
                    $userPermit = $headSales;
                } else {
                    $depart = self::departuser($responsible_id);
                    if (array_key_exists($depart, $headUserDepart)) {
                        $userPermit = $headUserDepart[$depart];
                    }
                }
            }
        }
        return $userPermit;
    }
    public static function namefirma($idfirma)
    {
        $result1 = '_';
        $res = self::request('crm.company.get', 'id=' . $idfirma);
        {
            if (count($res) > 0) {
                $result1 = $res['result']['TITLE'];
            }
        }
        return $result1;
    }
    public static function nameDeal($idDeal)
    {
        $result1 = '_';
        $res = self::request('crm.deal.get', 'id=' . $idDeal);
        {
            if (count($res) > 0) {
                $result1 = $res['result']['TITLE'];
            }
        }
        return $result1;
    }
    public static function checkPermissionShipment($idDeal, $opportunity, $assignedById, $companyId, $mycompanyId, $idStore, $paymemtTerm, $typePayment, $formPayment, $userPermit)
    {
        $permission = false;
        if ($typePayment == 493) {
            // Предоплата
            $sql = "SELECT amount FROM permission_prepayment WHERE id_deal=$idDeal AND id_company=$companyId AND id_mycompany=$mycompanyId AND form_payment=$formPayment";
            $res = self::request_sql($sql);
            foreach ($res as $row) {
                if (($row['amount'] >= $opportunity)) {
                    $permission = true;
                }
            }
        } else {
            // Отсрочка
            $sql = "SELECT term_payment FROM permission_postpayment WHERE type_payment=$typePayment AND id_company=$companyId AND id_mycompany=$mycompanyId AND form_payment=$formPayment";
            $res = self::request_sql($sql);
            foreach ($res as $row) {
                if (($row['term_payment'] >= $paymemtTerm)) {
                    $permission = true;
                }
            }
        }
        return $permission;
    }
    public static function checkPermissionShipmentDeal($idDeal)
    {
        //$opportunity, $assignedById, $companyId, $mycompanyId, $idStore, $paymemtTerm, $typePayment, $formPayment, $userPermit
        $parameter = "entityTypeId=31&filter[parentId2]=$idDeal&select[0]=id";
        $parameter .= '&select[1]=assignedById&select[2]=opportunity&select[3]=companyId&select[4]=mycompanyId';
        $parameter .= '&select[5]=ufCrm_SMART_INVOICE_1651114959541&select[6]=ufCrm_SMART_INVOICE_1651083629638';
        $parameter .= '&select[7]=ufCrm_SMART_INVOICE_1651083239729&select[8]=ufCrm_SMART_INVOICE_1656584515597';
        $parameter .= '&select[9]=accountNumber';
        $res = self::request('crm.item.list', $parameter);
        if (count($res) > 0) {
            $arr_invoice = $res['result']['items'];
            if (count($arr_invoice) > 0) {
                $idInvoice = $arr_invoice[0]['id'];
                $opportunity = $arr_invoice[0]['opportunity']; // Сумма
                $assignedById = $arr_invoice[0]['assignedById']; // Ответственный
                $assignedByName = Bitrix_help::nameuser($assignedById);
                $companyId = $arr_invoice[0]['companyId']; // Компания
                $mycompanyId = $arr_invoice[0]['mycompanyId']; // Наша компания
                $idStore = $arr_invoice[0]['ufCrm_SMART_INVOICE_1651083239729']; // Склад 479 - Склад Нск 481 - Склад Дистр    483 - Склад Спб    485 - Склад Кдр    487 - Склад Мск
                $paymemtTerm = $arr_invoice[0]['ufCrm_SMART_INVOICE_1656584515597']; // Отсрочка в счёте Число
                $typePayment = $arr_invoice[0]['ufCrm_SMART_INVOICE_1651114959541']; // Тип оплаты счёта: 493 - Предоплата; 495 - Отсрочка; 497 - Частичная
                $formPayment = $arr_invoice[0]['ufCrm_SMART_INVOICE_1651083629638']; // Форма оплаты Нал/Безнал  489 - Безналичные    491 - Наличные
                return self::checkPermissionShipment($idDeal, $opportunity, $assignedById, $companyId, $mycompanyId, $idStore, $paymemtTerm, $typePayment, $formPayment, '');
            } else {
                return false;
            }
        } else {
            return false;
        }
    }
    public static function getIdInvoiceByDeal($idDeal)
    {
        $idInvoice = '';
        $result = self::request('crm.item.list', "entityTypeId=31&filter[parentId2]=$idDeal&select[0]=id");
        if (count($result) > 0) {
            $idInvoice = $result['result']['items'][0]['id'];
        }
        return $idInvoice;
    }
    public static function checkprice($product_rows_array9, $product_deal_array9, $uf_company_id9, $uf_deal_id9, $uf_mycompany_id9, $tip_opl9, $paymemtTermInv9)
    {
        // product_deal_array9, uf_deal_id9 - не используются
        // return array();
        $nom = 0;
        $flagpr = 1;
        $arrmin = array();
        foreach ($product_rows_array9 as &$value) {
            $price = $value['PRICE'];
            $pricemin = self::prmin($value['PRODUCT_ID']);
            //Bitrix_help::send_message(215, $value['PRODUCT_NAME'].' :: '.$price.' :: '.$pricemin);
            //soobchenie(171,$price.' :: '.$pricemin.' :: '.$value['PRODUCT_NAME']);
            {
                if ($price < $pricemin) {
                    $ress = self::check_permission($uf_company_id9, $uf_deal_id9, $uf_mycompany_id9, $value['PRODUCT_ID'], $tip_opl9, $price, $paymemtTermInv9);
                    //Bitrix_help::send_message(215, $value['PRODUCT_NAME'].' :: '.$ress);
                    if (!($ress)) {
                        $flagpr = 0;
                        //$arrmin = [$nom => [ name => $value['PRODUCT_NAME'], id => $value['PRODUCT_ID'],  price => $price,  pricemin => $pricemin]];
                        $arrmin[$nom] = ['name' => $value['PRODUCT_NAME'], 'id' => $value['PRODUCT_ID'], 'price' => $price, 'pricemin' => $pricemin, 'quantity' => $value['QUANTITY']];
                        $nom = $nom + 1;
                        //echo $price;
                        //echo '<br/>';
                        //echo $pricemin;
                        //echo '<br/>';
                    }
                }
            }
        }
        unset($value); // Сбрасываем значение
        if (is_array($arrmin)) {
            if (count($arrmin) > 0) {
                return $arrmin;
            } else {
                return array();
            }
        }
    }
    public static function requestPrice($id_responsible, $arrmin1, $id_sdelka1, $name_sdelka1, $tipoplstr1, $srok_oplad1, $id_firma1, $id_company1, $tipopl1, $paymemtTermInv1)
    {
        // $arrmin - массив цен ниже
        $nom_shablon = 99;
        $nom_dokument = 1887;
        $text_zapros = 'Цена |Цена мин |Кол-во |Товар';

        $id_responsibldepart = self::departuser($id_responsible); // Определение утверждающегово
        if (($id_responsibldepart == 421) or ($id_responsibldepart == 423)) {
            $id_utverd = 169; //Б
        } else {
            $id_utverd = 131; // ???
        }

        foreach ($arrmin1 as &$value) {
            $pricetec = $value['price'];
            $len = strlen($pricetec);
            if ($len < 7) {
                for ($i = $len; $i <= 5; $i++) {
                    $pricetec = $pricetec . '  ';
                }}
            $pricemintec = $value['pricemin'];
            $len = strlen($pricemintec);
            if ($len < 10) {
                for ($i = $len; $i <= 9; $i++) {
                    $pricemintec = $pricemintec . '  ';
                }}
            $pricename = $value['name'];
            $quantitys = $value['quantity'];
            $quantitys = $quantitys . ' ';
            //$text_zapros  = $text_zapros.'[BR]'.$pricetec.'|'.$pricemintec.'|'.$pricename;
            //        $text_zapros = $text_zapros . '
            //                    ' . $pricetec . '|' . $pricemintec . '|' . $quantitys . '|' . $pricename . '|' . $value['id'];
            $text_zapros = $text_zapros . '%0A' . $pricetec . '|' . $pricemintec . '|' . $quantitys . '|' . $pricename . '|' . $value['id'];

        }
        $zapros = 'bizproc.workflow.start';
        $id_responsiblyname = self::nameuser($id_responsible);
        //493 - Предоплата; 495 - Отсрочка; 497 - Частичная
        if ($tipopl1 == 493) {
            $tipoplstr1 = 'Предоплата';
        } elseif ($tipopl1 == 495) {
            $tipoplstr1 = 'Отсрочка';
        } elseif ($tipopl1 == 497) {
            $tipoplstr1 = 'Частичная';
        }
        $parametr = 'TEMPLATE_ID=' . $nom_shablon . '&DOCUMENT_ID[0]=lists&DOCUMENT_ID[1]=BizprocDocument&DOCUMENT_ID[2]=' . $nom_dokument;
        $parametr .= '&PARAMETERS[Zapros]=' . $text_zapros . '&PARAMETERS[IDzapr]=' . $id_responsible . '&PARAMETERS[Otvetstven]=' . $id_responsiblyname;
        $parametr .= '&PARAMETERS[IDdeal]=' . $id_sdelka1 . '&PARAMETERS[IDutverd]=' . $id_utverd . '&PARAMETERS[Dopdan]=' . $name_sdelka1;
        $parametr .= '&PARAMETERS[Tipopl]=' . $tipoplstr1 . '&PARAMETERS[Datopl]=' . $srok_oplad1 . '&PARAMETERS[Firma]=' . $id_firma1;
        $parametr .= '&PARAMETERS[Compan]=' . $id_company1 . '&PARAMETERS[Tipoplnumber]=' . $tipopl1 . '&PARAMETERS[PaymemtTerm]=' . $paymemtTermInv1;
        //echo $parametr;
        $res = Bitrix_help::request($zapros, $parametr);
    }
    public static function productsUpdatetDeal($product_rows_array1, $product_deal_array1, $iddeal1)
    {
        // Перегрузить товары из счёта в сделку (запрос)) 1 - есть изменения, 0 - нет
        $result21 = 0; // Записать обновление товаров ($product_rows_array1 - оригинал)
        if (count($product_rows_array1) != count($product_deal_array1)) {
            $result21 = 1;
        } else {
            for ($i = 0; $i < count($product_rows_array1); $i++) {
                //$tektax = $product_rows_array1[$i][VAT_RATE] * 100;
                if (($product_rows_array1[$i]['PRODUCT_ID'] != $product_deal_array1[$i]['PRODUCT_ID']) or ($product_rows_array1[$i]['QUANTITY'] != $product_deal_array1[$i]['QUANTITY'])
                    or ($product_rows_array1[$i]['PRICE'] != $product_deal_array1[$i]['PRICE']) or ($product_rows_array1[$i]['TAX_INCLUDED'] != $product_deal_array1[$i]['TAX_INCLUDED'])
                    or ($product_rows_array1[$i]['TAX_RATE'] != $product_deal_array1[$i]['TAX_RATE']) or ($product_rows_array1[$i]['MEASURE_CODE'] != $product_deal_array1[$i]['MEASURE_CODE'])
                    or ($product_rows_array1[$i]['MEASURE_NAME'] != $product_deal_array1[$i]['MEASURE_NAME']) or ($product_rows_array1[$i]['PRODUCT_NAME'] != $product_deal_array1[$i]['PRODUCT_NAME'])
                    or ($product_rows_array1[$i]['CUSTOMIZED'] != $product_deal_array1[$i]['CUSTOMIZED'])) {
                    $result21 = 1;
                }
            }
        }
        if ($result21 == 1) { // Обновляем
            $zapros = 'crm.deal.productrows.set';
            $parametr = 'id=' . $iddeal1;
            for ($i = 0; $i < count($product_rows_array1); $i++) {
                //$tektax = $product_rows_array1[$i][VAT_RATE] * 100;
                /*$parametr = $parametr . '&rows[' . $i . '][PRODUCT_ID]=' . $product_rows_array1[$i][productId] . '&rows[' . $i . '][QUANTITY]=' . $product_rows_array1[$i][quantity] .
                '&rows[' . $i . '][PRICE]=' . $product_rows_array1[$i][price] . '&rows[' . $i . '][TAX_INCLUDED]=' . $product_rows_array1[$i][taxIncluded] .
                '&rows[' . $i . '][TAX_RATE]=' . $product_rows_array1[$i][taxRate] . '&rows[' . $i . '][MEASURE_CODE]=' . $product_rows_array1[$i][measureCode] .
                '&rows[' . $i . '][MEASURE_NAME]=' . $product_rows_array1[$i][measureName] . '&rows[' . $i . '][PRODUCT_NAME]=' . $product_rows_array1[$i][productName] .
                '&rows[' . $i . '][CUSTOMIZED]=' . $product_rows_array1[$i][customized]. '&rows[' . $i . '][PRICE_EXCLUSIVE]=' . $product_rows_array1[$i][priceExclusive] .
                '&rows[' . $i . '][PRICE_NETTO]=' . $product_rows_array1[$i][priceNetto] . '&rows[' . $i . '][PRICE_BRUTTO]=' . $product_rows_array1[$i][priceBrutto] .
                '&rows[' . $i . '][DISCOUNT_TYPE_ID]=' . $product_rows_array1[$i][discountTypeId] . '&rows[' . $i . '][DISCOUNT_RATE]=' . $product_rows_array1[$i][discountRate] .
                '&rows[' . $i . '][DISCOUNT_SUM]=' . $product_rows_array1[$i][discountSum] ;
                 */
                $parametr = $parametr . '&rows[' . $i . '][PRODUCT_ID]=' . $product_rows_array1[$i]['PRODUCT_ID'] . '&rows[' . $i . '][QUANTITY]=' . $product_rows_array1[$i]['QUANTITY'] .
                    '&rows[' . $i . '][PRICE]=' . $product_rows_array1[$i]['PRICE'] . '&rows[' . $i . '][TAX_INCLUDED]=' . $product_rows_array1[$i]['TAX_INCLUDED'] .
                    '&rows[' . $i . '][TAX_RATE]=' . $product_rows_array1[$i]['TAX_RATE'] . '&rows[' . $i . '][MEASURE_CODE]=' . $product_rows_array1[$i]['MEASURE_CODE'] .
                    '&rows[' . $i . '][MEASURE_NAME]=' . $product_rows_array1[$i]['MEASURE_NAME'] . '&rows[' . $i . '][PRODUCT_NAME]=' . $product_rows_array1[$i]['PRODUCT_NAME'] .
                    '&rows[' . $i . '][CUSTOMIZED]=' . $product_rows_array1[$i]['CUSTOMIZED'] . '&rows[' . $i . '][PRICE_EXCLUSIVE]=' . $product_rows_array1[$i]['PRICE_EXCLUSIVE'] .
                    '&rows[' . $i . '][PRICE_NETTO]=' . $product_rows_array1[$i]['PRICE_NETTO'] . '&rows[' . $i . '][PRICE_BRUTTO]=' . $product_rows_array1[$i]['PRICE_BRUTTO'] .
                    '&rows[' . $i . '][DISCOUNT_TYPE_ID]=' . $product_rows_array1[$i]['DISCOUNT_TYPE_ID'] . '&rows[' . $i . '][DISCOUNT_RATE]=' . $product_rows_array1[$i]['DISCOUNT_RATE'] .
                    '&rows[' . $i . '][DISCOUNT_SUM]=' . $product_rows_array1[$i]['DISCOUNT_SUM'];
            }
            $res = self::request($zapros, $parametr);
            //log_ftp($zapros.' :: '.$parametr, 'product');
            {
                if (count($res) > 0) {}
            }
        }
        return $result21; //
    }
    public static function productsUpdate($product_rows_array1, $product_deal_array1, $id1)
    {
        // Если товары изменились, тогда из сделки ($product_deal_array1) в счёт id1 ид счёта
        $result21 = 0; // Записать обновление товаров ($product_rows_array1 - оригинал)
        if (count($product_rows_array1) != count($product_deal_array1)) {
            $result21 = 1;
        } else {
            for ($i = 0; $i < count($product_rows_array1); $i++) {
                if (($product_rows_array1[$i]['PRODUCT_ID'] != $product_deal_array1[$i]['PRODUCT_ID']) or ($product_rows_array1[$i]['QUANTITY'] != $product_deal_array1[$i]['QUANTITY'])
                    or ($product_rows_array1[$i]['PRICE'] != $product_deal_array1[$i]['PRICE']) or ($product_rows_array1[$i]['TAX_INCLUDED'] != $product_deal_array1[$i]['TAX_INCLUDED'])
                    or ($product_rows_array1[$i]['TAX_RATE'] != $product_deal_array1[$i]['TAX_RATE']) or ($product_rows_array1[$i]['MEASURE_CODE'] != $product_deal_array1[$i]['MEASURE_CODE'])
                    or ($product_rows_array1[$i]['MEASURE_NAME'] != $product_deal_array1[$i]['MEASURE_NAME']) or ($product_rows_array1[$i]['PRODUCT_NAME'] != $product_deal_array1[$i]['PRODUCT_NAME'])
                    or ($product_rows_array1[$i]['CUSTOMIZED'] != $product_deal_array1[$i]['CUSTOMIZED'])) {
                    $result21 = 1;
                }
            }
        }
        if ($result21 == 1) {
            // Обновляем
            $zapros = 'crm.item.productrow.set';
            $parametr = 'ownerType=SI&ownerId=' . $id1;
            for ($nom = 0; $nom < count($product_deal_array1); $nom++) {
                $parametr = $parametr . '&productRows[' . $nom . '][ownerId]=' . $id1 . '&productRows[' . $nom . '][ownerType]=SI';
                $parametr = $parametr . '&productRows[' . $nom . '][productId]=' . $product_deal_array1[$nom]['PRODUCT_ID'] . '&productRows[' . $nom . '][quantity]=' . $product_deal_array1[$nom]['QUANTITY'] . '&productRows[' . $nom . '][price]=' . $product_deal_array1[$nom]['PRICE'] . '&productRows[' . $nom . '][taxRate]=' . $product_deal_array1[$nom]['TAX_RATE'];
                $parametr = $parametr . '&productRows[' . $nom . '][taxIncluded]=' . $product_deal_array1[$nom]['TAX_INCLUDED'] . '&productRows[' . $nom . '][measureCode]=' . $product_deal_array1[$nom]['MEASURE_CODE'] . '&productRows[' . $nom . '][measureName]=' . $product_deal_array1[$nom]['MEASURE_NAME'];
                $parametr = $parametr . '&productRows[' . $nom . '][productName]=' . $product_deal_array1[$nom]['PRODUCT_NAME'] . '&productRows[' . $nom . '][customized]=' . $product_deal_array1[$nom]['CUSTOMIZED'];
                $parametr = $parametr . '&productRows[' . $nom . '][priceExclusive]=' . $product_deal_array1[$nom]['PRICE_EXCLUSIVE'] . '&productRows[' . $nom . '][priceNetto]=' . $product_deal_array1[$nom]['PRICE_NETTO'];
                $parametr = $parametr . '&productRows[' . $nom . '][priceBrutto]=' . $product_deal_array1[$nom]['PRICE_BRUTTO'] . '&productRows[' . $nom . '][discountTypeId]=' . $product_deal_array1[$nom]['DISCOUNT_TYPE_ID'];
                $parametr = $parametr . '&productRows[' . $nom . '][discountRate]=' . $product_deal_array1[$nom]['DISCOUNT_RATE'] . '&productRows[' . $nom . '][discountSum]=' . $product_deal_array1[$nom]['DISCOUNT_SUM'];
            }
            $res = self::request($zapros, $parametr);
            //if (count($res) > 0) {
            //}
        }
        return $result21; //
    }
    public static function checkCloseDeal($idDeal)
    {
        return true;
    }
    public static function getIdAssignedByDeal($idDeal) 
    {
        $assigned = '';
        $result = self::request('crm.deal.get', "id=$idDeal");
        if (count($result) > 0) {
            $assigned = $result['result']['ASSIGNED_BY_ID'];
        }
        return $assigned;
    }
    public static function getRemnantsProductById($idProduct)  
    {
        $assigned = '';
        $result = self::request('crm.product.get', "id=$idProduct");
        if (count($result) > 0) {
            $remnantsSpbReq = $result['result']['PROPERTY_113'];
            if (!empty($remnantsSpbReq)) {
                $remnantsSpb = $remnantsSpbReq['value'];  
            } else {
                $remnantsSpb = 0;  
            }
            $remnantsKdrReq = $result['result']['PROPERTY_115'];
            if (!empty($remnantsKdrReq)) {
                $remnantsKdr = $remnantsKdrReq['value'];  
            } else {
                $remnantsKdr = 0;  
            }
            $remnantsMskReq = $result['result']['PROPERTY_117'];
            if (!empty($remnantsMskReq)) {
                $remnantsMsk = $remnantsMskReq['value'];  
            } else {
                $remnantsMsk = 0;  
            }
            $remnantsNskReq = $result['result']['PROPERTY_119'];
            if (!empty($remnantsNskReq)) {
                $remnantsNsk = $remnantsNskReq['value'];  
            } else {
                $remnantsNsk = 0;  
            }
            $remnantsProduct = array('483' => $remnantsSpb, '485' => $remnantsKdr, '487' => $remnantsMsk, '481' => $remnantsNsk);
        } else {
            $remnantsProduct = array('483' => 0, '485' => 0, '487' => 0, '481' => 0);
        }
        return $remnantsProduct;
    } 
    public static function getIdDiskByUser($idUser)  
    {
        $idDisk = '';
        $idDiskUserArray = array(
        11 => 19413,
        21 => 19415,
        25 => 19417,
        29 => 19419,
        31 => 19421,
        35 => 19427,
        109	=> 19429,
        111 => 19431,
        113 => 19433,
        115	=> 19435,
        117 => 19437,
        121	=> 19439,
        127	=> 19441,
        131 => 19443,
        169 => 19445,
        171 => 19447,
        173	=> 19449,
        215 => 19409,
        227	=> 19451,
        237 => 19453,
        239 => 19455,
        241 => 19457,
        243	=> 19459,
        245 => 19461,
        249 => 19463,
        259 => 19465,
        317	=> 19467,
        319 => 19469,
        389 => 19471,
        393	=> 19473,
        399 => 19475,
        421 => 19477,
        645	=> 29657,
        759 => 36683,
        779 => 37577,
        793 => 39167,
        875 => 47239,
        877 => 47249,
        905 => 50427,
        923 => 53239,
        927 => 53243,
        991 => 86609,
        1039 => 86617,
        1271 => 131269,
        1615 => 191325,   
        1617 => 186931,
        3231 => 245681,
        4147 => 283485,
        3895 => 283497,
        3607 => 283499,
        3729 => 283503,
        3519 => 283505,
        7431 => 368947,
        5747 => 334643,
        9637 => 449449,
        175 => 458727,
        11077 => 492127,
        11661 => 523835,
        11777 => 528839,
        12295 => 562545,
        12433 => 568119,
        13051 => 598859,
        13247 => 611405,
        13617 => 639243,
        13615 => 648679,
    );
        if (array_key_exists($idUser,$idDiskUserArray)){
        $idDisk = $idDiskUserArray[$idUser];
        }  
        return $idDisk;
    }  
    public static function copyFileByIdInFolder($idFile,$folder,$fileName) 
    {
        $res = self::request('disk.file.get', 'id=' . $idFile);
        if (count($res)>0) {
            $downloadFile = $res['result']['DOWNLOAD_URL'];
        } 

        $url = $downloadFile;
        //echo $url.'</br>';
        // Инициализируем сессию cURL
        $ch = curl_init($url);
        // Инициализировать имя каталога, где
        // файл будет сохранен
        $dir = __DIR__ . "/$folder/";
        //echo $dir.'</br>';
        // Используем функцию basename () для возврата
        // базовое имя файла
        //$file_name = basename($url);
        $file_name = $fileName;
        //echo $file_name.'</br>';
        
        // Сохранить файл в папку
        $save_file_loc = $dir . $file_name;
        //echo $save_file_loc.'</br>';
        
        // Открыть файл
        $fp = fopen($save_file_loc, 'wb');
        // Он устанавливает опцию для передачи cURL
        curl_setopt($ch, CURLOPT_FILE, $fp);
        curl_setopt($ch, CURLOPT_HEADER, 0);
        // Выполнить сеанс cURL
        curl_exec($ch);
        // Закрывает сеанс cURL и освобождает все ресурсы
        curl_close($ch);
        // Закрыть файл
        fclose($fp); 
    }    
    public static function getLinkEntity($idEntity, $nameEntity, $entity) 
    {
        global $bitrixPortal;
        $link = '';
        switch ($entity) {
            case 'deal':
              $link = "[url=$bitrixPortal/crm/deal/details/$idEntity/]$nameEntity [/url]";
              break;
            case 'company':
              $link = "[url=$bitrixPortal/crm/company/details/$idEntity/]$nameEntity [/url]";
              break;
          }
        return $link;
    }
    public static function insertProcessingDeal($idDeal, $timestamp)
    {
        $sql = 'INSERT INTO deal_processing (deal_id, timestamp) VALUES (' . $idDeal . ', ' . $timestamp . ')';
        $result = self::request_sql($sql);
        return $result;
    }  
    public static function getProcessingDeal($idDeal, $timestamp)
    {
        $deal_processing_status = -1;
        $sql = 'SELECT status FROM deal_processing WHERE deal_id = ' . $idDeal . ' AND timestamp = ' . $timestamp;
        $result = self::request_sql($sql);
        foreach ($result as $row) {
            $deal_processing_status = $row['status'];
        }
        return  $deal_processing_status;
    }  
    public static function setProcessingDeal($idDeal, $timestamp)
    {
        $sql = 'UPDATE deal_processing SET status = 1 WHERE deal_id = ' . $idDeal . ' AND timestamp = ' . $timestamp ;
        $result = self::request_sql($sql);
        return $result;
    }  
}
