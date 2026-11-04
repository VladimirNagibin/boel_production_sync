<?php
$id_sdelka = $_REQUEST['ID_SDELKA'];
$id_firma = $_REQUEST['ID_FIRMA'];
$id_shablon = $_REQUEST['ID_SHABLON'];
$srok_oplad = $_REQUEST['SROK_OPLAT'];
$skladstr = $_REQUEST['SKLAD'];
$id_user = $_REQUEST['ID_USER'];
$tipoplstr = $_REQUEST['TIPOPL'];
$formaoplstr = $_REQUEST['FORMA_OPL'];
$paymemtTerm = $_REQUEST['SROK_OPL']; // отсрочка дней число
$nds0 = $_REQUEST['NDS0'];

$bitrixPortal = getenv('BITRIX_PORTAL');
$bitrixToken = getenv('BITRIX_TOKEN');
$bitrixTokenMessage = getenv('BITRIX_TOKEN_MESSAGE');
$ftpPortal = getenv('FTP_PORTAL');
$ftpUser = getenv('FTP_USER');
$ftpPass = getenv('FTP_PASS');

//soobchenie(171, 'START ' . $id_sdelka);
if ($id_sdelka == 56705) {
    //exit();
}
$array_my_company = array('439' => '8923', '441' => '5385', '443' => '5383', '445' => '5381', '447' => '22145', '773' => '23217', '777' => '8897');
include 'main_function.php';

//$id_topic       = $_REQUEST[ID_TOPIC];
//$id_responsible = $_REQUEST[ID_RESPONSIBLE];
//$id_company     = $_REQUEST[ID_COMPANY];
//$id_user        = 'user_171';
//$id_suchnosti   = 5;
$id_suchnosti = 31;
$id_user = str_replace('user_', '', $id_user);
//echo $id_user;
//exit();
//$id_sdelka    = 1153;
//$id_firma     = 5381;
//$id_shablon   = 69;
//$srok_oplad   = '2021-09-22';
//$skladstr     = 'Склад Спб';

if ($skladstr == 'Склад Нск') {
    //$sklad='327';
    //$sklad = '479';
    $sklad = '481';
} elseif ($skladstr == 'Склад Дистр') {
    $sklad = '481';
} elseif ($skladstr == 'Склад Спб') {
    $sklad = '483';
} elseif ($skladstr == 'Склад Кдр') {
    $sklad = '485';
} elseif ($skladstr == 'Склад Мск') {
    $sklad = '487';
} else {
    $sklad = '481';
}

if ($tipoplstr == 'Предоплата') {
    //$tipopl='371';
    $tipopl = '493';
} elseif ($tipoplstr == 'Отсрочка') {
    //$tipopl='373';
    $tipopl = '495';
} elseif ($tipoplstr == 'Частичная') {
    //$tipopl='375';
    $tipopl = '497';
} else {
    $tipopl = '493';
}

if ($formaoplstr == 'Безналичные') {
    //$formaopl='383';
    $formaopl = '489';
} else {
    if ($formaoplstr == 'Наличные') {
        //$formaopl='385';
        $formaopl = '491';
    } else {
        $formaopl = '491';
    }
}

// Проверка цен
$flagpr = 1;

$zapros = 'crm.deal.get';
$parametr = 'id=' . $id_sdelka;
$res = zapros($zapros, $parametr);
if (array_key_exists('error', $res)) {
    echo $res['error_description'];
} else {
    $res2 = $res['result']['UF_CRM_60D2AFAEB32CC'];
    $id_responsible = $res['result']['ASSIGNED_BY_ID'];
    $id_responsible_name = nameuser($id_responsible);
    $id_company = $res['result']['COMPANY_ID'];
    $id_contact = $res['result']['CONTACT_ID'];
    $id_topic = 'Счёт на ' . namefirma($id_company) . ' от ' . namefirma($id_firma);
    $id_stadia = $res['result']['STAGE_ID'];
    $srok_oplad_deal = $res['result']['UF_CRM_1632738230'];
    $tipopl_deal = $res['result']['UF_CRM_1632738315'];
    $commmrnt_deal = $res['result']['COMMENTS'];
    $sourse_deal = $res['result']['SOURCE_ID'];
    $name_deal = $res['result']['TITLE'];
    $id_firma_deal1 = $res['result']['UF_CRM_1650617036']; //439 - Системы, 441 - Элемент, 443 - Торговый дом СР, 445 - ТехТорг, 447 - ИП Гузиков М.Г., 773 - ИП Воробьев Д.В., 777 - Эксперты розлива
    $id_firma_deal = $array_my_company[$id_firma_deal1];
    $id_shipment = $res['result']['UF_CRM_1655141630'];

    $zapros = 'crm.deal.productrows.get';
    $parametr = 'id=' . $id_sdelka;
    $res = zapros($zapros, $parametr);
    $nom = 0;
    $arrmin = array();
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
            $resproduct = array();
        } else {
            $resproduct = $res['result'];
        }

        //soobchenie(171,json_encode($resproduct));
    }
    {
        //Bitrix_help::send_message(215, 'Кол товаров '.' :: '.count($resproduct));
        foreach ($resproduct as &$value) {
            $price = $value['PRICE'];
            $pricemin = prmin($value['PRODUCT_ID']);
            //Bitrix_help::send_message(215, $value['PRODUCT_NAME'].' :: '.$price.' :: '.$pricemin);
            //soobchenie(171,$price.' :: '.$pricemin.' :: '.$value['PRODUCT_NAME']);
            {
                if ($price < $pricemin) {
                    $ress = Bitrix_help::check_permission($id_company, $id_sdelka, $id_firma, $value['PRODUCT_ID'], $tipopl, $price, $paymemtTerm);
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
    }
    //if ($flagpr==0)
    //{
    // if ((checkprice($id_company,  $arrmin, $tipopl))){
    //     $flagpr=1;
    //}

    /*
    if ($res2=='1')
    {
    $flreason = 1;
    $strsoobdat = 'Ухудшились условия сделки после согласования.[BR]';
    // Проверка на изменение условий

    $srok_oplad_deal_str = substr($srok_oplad_deal,0,10);
    //$srok_oplad_invoice_dat = strtotime($srok_oplad.'T00:00:00+00:00');
    //$srok_oplad_deal_dat = strtotime($srok_oplad_deal);

    $srok_oplad_invoice_dat = strtotime($srok_oplad);
    $srok_oplad_deal_dat = strtotime($srok_oplad_deal_str);

    if ($srok_oplad_deal_dat < $srok_oplad_invoice_dat)
    {
    $flreason = 0;
    $strsoobdat = $strsoobdat.'Согласованная дата оплаты: '.$srok_oplad_deal_str.', дата в счёте '.$srok_oplad.'.[BR]';
    }

    {
    if ($tipopl_deal=='377')
    $tipopl_dealstr='Предоплата';
    else
    {
    {
    if ($tipopl_deal=='379')
    $tipopl_dealstr='Отсрочка';
    else
    {
    {
    if ($tipopl_deal=='381')
    $tipopl_dealstr='Частичная';
    else
    $tipopl_dealstr=' ';
    {
    }}}}}}

    if ($tipopl == '495') {                           // Отсрочка
    if ($tipopl_deal <> '379') {                  // Согласована не отсрочка
    $flreason = 0;
    $strsoobdat = $strsoobdat.' Согласованный тип оплаты: '.$tipopl_dealstr.', тип в счёте '.$tipoplstr.'.[BR]';
    }}
    if ($tipopl == '497') {                           // Частичная
    if ($tipopl_deal == '377') {                  // Согласована предоплата
    $flreason = 0;
    $strsoobdat = $strsoobdat.' Согласованный тип оплаты: '.$tipopl_dealstr.', тип в счёте '.$tipoplstr.'.[BR]';
    }}

    if ($flreason == 0) {
    soobchenie($id_user,$strsoobdat.' Нужно либо изменить условия сделки либо запросить разрешение повторно.');
    exit();
    }
    else
    {
    $flagpr = 1;
    }
    // $tipopl_deal >= $tipopl
    //$booll = ($srok_oplad_date<$srok_oplad_deal_date);
    //$strlog = 'срок из сделки//'.$srok_oplad_deal.'//срок из счёта//'.$srok_oplad.'//date deal//'.$srok_oplad_deal_date.'//date invoice//'.$srok_oplad_date.'//';
    //$strlog = 'тип из сделки//'.gettype($tipopl_deal).'//тип из счёта//'.gettype($tipopl);
    //lod_ftp($strlog);
    //echo 'YES';
    //echo '<br/>';
    //$flagpr = true;
    }
    else
    {}
     */
    //}

    if ($id_firma != $id_firma_deal) { // Фирма в Компании и сделке не совпадают

        // Обработка соответствия фирмы отгрузки и договора с компанией
        $rescomp = zapros('crm.company.get', 'id=' . $id_company);
        if (count($rescomp) > 0) {
            $deal_firma = $id_firma_deal;
            $res_comp = $rescomp['result'];
            $tec_contract = $res_comp['UF_CRM_1623915176']; // текущий договор
            $tec_firma = $res_comp['UF_CRM_1631903199']; // тек фирма (компания)  8923 - Системы
            $tec_id_firma = $res_comp['UF_CRM_1631941968']; // ид тек фирмы
            $arr_contract = $res_comp['UF_CRM_1623833623']; // массив договоров
            $tec_name = $res_comp['TITLE'];
            if (($deal_firma == $tec_id_firma) && ($deal_firma == $tec_firma) && ($tec_contract != '')) {
                $fl_find = true; // Фирма совпадает
            } else {
                $fl_find = false;
                //Bitrix_help::send_message(215, 'not f ');
                //Bitrix_help::send_message(215, $arr_contract[0]);
                if (is_array($arr_contract)) {
                    foreach ($arr_contract as &$value) {
                        //send_message(215, $value.' '.$deal_firma.' '.$tec_contract);
                        $arr_value = decompose_contract($value);
                        if (count($arr_value) > 0) {
                            //send_message(215, $arr_value[0].' '.$arr_value[1].' '.$arr_value[0]);
                            if ($arr_value[0] == $deal_firma) { // Устанавливаем текущий договор
                                $rescomp = zapros('crm.company.update', 'id=' . $id_company . '&fields[UF_CRM_1623915176]=' . $arr_value[1] . '&fields[UF_CRM_1631903199]=' . $arr_value[0] . '&fields[UF_CRM_1631941968]=' . $arr_value[0]);
                                $fl_find = true;
                                break;
                            }
                        }
                    }
                    unset($value);
                }
                //Bitrix_help::send_message(215, 'not fuii '.$id_user.'  :: '.$fl_find.'  *** '.$deal_firma);
                //Bitrix_help::send_message(215, 'not fuii ');
                if (!$fl_find) {
                    if ($deal_firma == '8923') {
                        $rescomp = zapros('crm.company.update', 'id=' . $id_company . '&fields[UF_CRM_1623915176]=Договор   от &fields[UF_CRM_1631903199]=8923&fields[UF_CRM_1631941968]=8923');
                    } else {
                        //$assignrd_by_id
                        soobchenie($id_user, 'Фирма в сделке ' . $name_deal . ' и компании ' . namefirma($id_company) . ' не совпадают. Проверьте фирму отгрузки'); //************************************  Поменять адресата сообщения при запуске */
                        $parametr77 = 'id=' . $id_sdelka . '&fields[STAGE_ID]=EXECUTING&fields[UF_CRM_1632738604]=EXECUTING';
                        $res77 = Bitrix_help::request('crm.deal.update', $parametr77);
                        exit();
                    }
                }
            }
        }
    }
    if ($id_shipment==515) {
        $id_dostavka = 543;
    } elseif ($id_shipment==517) {
        $id_dostavka = 545;
    } elseif ($id_shipment==519) {
        $id_dostavka = 547;
    } else {
        $id_dostavka = 543;
    }
    //soobchenie($id_user,'Flag '.$flagpr);
    //echo $flagpr;
    //echo '<br/>';
    $dostavka = '';
    $contract_tec = contractfirma($id_company);
    if ($contract_tec=='Счет-оферта') {
        // Фирма ТТ или ИП Г и предоплата иначе сбросить тек договор и откат
        if ((($id_firma_deal=='5381') or ($id_firma_deal=='22145') or ($id_firma_deal=='23217'))and($tipopl == '493')) {
            if ($id_shipment==515) {
                $dostavka = 'Покупатель забирает товар самовывозом со склада Поставщика.';
            } elseif ($id_shipment==517) {
                $dostavka = 'Доставка осуществляется курьером по указанному Покупателем адресу.';
            } elseif ($id_shipment==519) {
                $dostavka = 'Доставка осуществляется Транспортной компанией по указанному Покупателем адресу.';
            } else {
                $dostavka = 'Покупатель забирает товар самовывозом со склада Поставщика.';
            }
            if ($id_firma_deal=='5381') {
                // техТорг
            $id_shablon = 131; // Шаблон сч-оф
            } elseif ($id_firma_deal=='22145') {
                // ИП Г
            $id_shablon = 127; // Шаблон сч-оф
            } elseif ($id_firma_deal=='23217') {
                // ИП Воробьев Д.В.
            $id_shablon = 161; // Шаблон сч-оф
            }
        } else {
            soobchenie($id_user, 'В сделке ' . $name_deal . ' выставляется счет-оферта только по предоплате по фирмам без НДС.');
            $parametr77 = 'id=' . $id_sdelka . '&fields[STAGE_ID]=EXECUTING&fields[UF_CRM_1632738604]=EXECUTING';
            $res77 = Bitrix_help::request('crm.deal.update', $parametr77);
            exit();
        }
    }
    {
        if (($flagpr == 0) && ($id_sdelka != 70735)) {
            // Отправить запрос на согласование цен
            soobchenie($id_user, 'Цены в сделке ' . $name_deal . ' ниже минимальных. Запрос на согласование отправлен');


            //echo 'Send request in price';
            //echo '<br/>';
            // $arrmin - массив цен ниже
            $nom_shablon = 99;
            $nom_dokument = 1887;
            $text_zapros = 'Цена |Цена мин |Кол-во |Товар';

            $id_responsibldepart = departuser($id_responsible);
            {
                // Нск ***  переписать утверждающих  // Пока всё на Ф
                if (($id_responsibldepart == 421) or ($id_responsibldepart == 423)) {
                    $id_utverd = 169; //Б
                } else {
                    $id_utverd = 169; // ???
                }
            }

            $id_utverd = 215;  // служебный *************************************************************************************TEST************************************************

            foreach ($arrmin as &$value) {
                $pricetec = $value['price'];
                $len = strlen($pricetec);
                if ($len < 7) {
                    for ($i = $len; $i <= 5; $i++) {
                        $pricetec = $pricetec . '  ';
                    }
                }
                $pricemintec = $value['pricemin'];
                $len = strlen($pricemintec);
                if ($len < 10) {
                    for ($i = $len; $i <= 9; $i++) {
                        $pricemintec = $pricemintec . '  ';
                    }
                }
                $pricename = $value['name'];
                $quantitys = $value['quantity'];
                $quantitys = $quantitys . ' ';
                //$text_zapros  = $text_zapros.'[BR]'.$pricetec.'|'.$pricemintec.'|'.$pricename;
//                $text_zapros = $text_zapros . '
//                    ' . $pricetec . '|' . $pricemintec . '|' . $quantitys . '|' . $pricename . '|' . $value['id'];
                $text_zapros = $text_zapros . '%0A' . $pricetec . '|' . $pricemintec . '|' . $quantitys . '|' . $pricename . '|' . $value['id'];
            }
            soobchenie($id_user, $text_zapros);
            $zapros = 'bizproc.workflow.start';
            $parametr = 'TEMPLATE_ID=' . $nom_shablon . '&DOCUMENT_ID[0]=lists&DOCUMENT_ID[1]=BizprocDocument&DOCUMENT_ID[2]=' . $nom_dokument;
            $parametr .= '&PARAMETERS[Zapros]=' . $text_zapros . '&PARAMETERS[IDzapr]=' . $id_responsible . '&PARAMETERS[Otvetstven]=' . $id_responsible_name;
            $parametr .= '&PARAMETERS[IDdeal]=' . $id_sdelka . '&PARAMETERS[IDutverd]=' . $id_utverd . '&PARAMETERS[Dopdan]=' . $id_topic;
            $parametr .= '&PARAMETERS[Tipopl]=' . $tipoplstr . '&PARAMETERS[Datopl]=' . $srok_oplad . '&PARAMETERS[Firma]=' . $id_firma;
            $parametr .= '&PARAMETERS[Compan]=' . $id_company . '&PARAMETERS[Tipoplnumber]=' . $tipopl. '&PARAMETERS[PaymemtTerm]=' . $paymemtTerm;
            //echo $parametr;
            $res = zapros($zapros, $parametr);  //************************************************* Пока отключим запрос  $id_utverd
            //soobchenie(171, $text_zapros);
            {
                if (array_key_exists('error', $res)) {
                    echo $res['error_description'];
                } else {
                }
            }
        } else {
            // Проверка стадии
            if ($id_stadia == 'FINAL_INVOICE') {
                //Создать новый счёт
                $flag_new_invoice = 1;

                //$zapros   = 'crm.invoice.list';
                //$parametr = 'filter[UF_DEAL_ID]='.$id_sdelka.'&select[0]=ID'.'&select[1]=STATUS_ID';

                $zapros = 'crm.item.list';
                $parametr = 'entityTypeId=31' . '&filter[parentId2]=' . $id_sdelka . '&select[0]=id' . '&select[1]=stageId' . '&select[2]=mycompanyId';

                $res = zapros($zapros, $parametr);
                { if (array_key_exists('error', $res)) {
                    echo $res['error_description'];
                } else {
                    $arr_invoice_old = $res['result']['items'];
                    if (count($arr_invoice_old) > 0) {
                        $id_invoice_old = $arr_invoice_old[0]['id'];
                        $status_invoice_old = $arr_invoice_old[0]['stageId'];
                        $firma_invoice_old = $arr_invoice_old[0]['mycompanyId'];
                        // Проверим что не выгружен в 1С
                        if (($status_invoice_old == 'DT31_1:P') or ($status_invoice_old == 'DT31_1:D')) {
                            soobchenie($id_user, 'У сделки ' . $name_deal . ' существует закрытый счёт. Создать новый не возможно.'); //********************************************************************************************************* */
                            $flag_new_invoice = 0;
                        } else {
                            if ($id_firma_deal != $firma_invoice_old) { // Если фирма изменилась - удаляем старый счёт
                                soobchenie($id_user, 'У сделки ' . $name_deal . ' может быть привязан только один счёт. Предыдущий будет удалён.');
                                //$zapros   = 'crm.invoice.delete';
                                $zapros = 'crm.item.delete';
                                $parametr = 'entityTypeId=31' . '&id=' . $id_invoice_old;
                                $res = zapros($zapros, $parametr);
                                {
                                    if (array_key_exists('error', $res)) {
                                        echo $res['error_description'];
                                    } else {
                                        $zapros = 'crm.deal.update';
                                        //$parametr = 'id='.$id_sdelka.'&fields[UF_CRM_1632738230]='.$srok_oplad.'&fields[UF_CRM_1632738315]='.$tipopl2.'&fields[UF_CRM_1632738354]='.'&fields[UF_CRM_1632738559]=';
                                        $parametr = 'id=' . $id_sdelka . '&fields[UF_CRM_1632738230]=' . $srok_oplad . '&fields[UF_CRM_1632738315]=' . '&fields[UF_CRM_1632738354]=' . '&fields[UF_CRM_1632738559]=' . '&fields[UF_CRM_1656582798]=0';
                                        $res = zapros($zapros, $parametr);

                                        if ($status_invoice_old == '1') { //*************************************************************************************************** */
                                            // отправить сообщение об удалении счёта в 1С
                                            {
                                                $text_invoice = '{"VIEW":"DELL_INVOICE","ID":' . $id_invoice_old . '}';

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
                                        }
                                    }
                            }
                            } else { // Запрос на удаление/обновление Фирма не изменилась - удалить счёт вручную /************************************************************************* */
                                $flag_new_invoice = 0;
                                soobchenie($id_user, 'У сделки ' . $name_deal . ' существует счёт по фирме ' . namefirma($id_firma_deal) . '. Правьте существующий счёт. Для заведения нового счёта старый нужно удалить через бизнес процесс');
                            }
                        }
                    }
                }}
                //lod_ftp(flag_new_invoice.' после проверки');
                //****************************** Новый счёт *******************************************************************
    
                if ($id_sdelka == 56705) {
                    //soobchenie(171, 'NEW INVOICE ' . $id_sdelka);
                }
                if ($flag_new_invoice == 1) {
                    // Проверка остатков  $sklad = '481' - НСК  $sklad = '483' - СПБ  $sklad = '485' - КДР  $sklad = '487' - МСК
                    if (count($resproduct) > 0) {
                        foreach ($resproduct as &$value) {
                            $nameProduct = $value['PRODUCT_NAME'];
                            $idProduct = $value['PRODUCT_ID'];
                            $quantityProduct = $value['QUANTITY'];
                            $measureProduct =  $value['MEASURE_NAME'];
                            //Bitrix_help::send_message(215, $value['PRODUCT_NAME'].' :: '.$price.' :: '.$pricemin);
                            $remnantsProduct = Bitrix_help::getRemnantsProductById($idProduct);
                            $remnantsInSklad = $remnantsProduct[$sklad];
                            if ($quantityProduct > $remnantsInSklad) {
                                if ($remnantsInSklad<0) {
                                    $razn = $quantityProduct;
                                } else {
                                    $razn = $quantityProduct - $remnantsInSklad;
                                }
                                $razn = $quantityProduct - $remnantsProduct[$sklad];
                                $textAlert = "На складе $skladstr нехватка $nameProduct $razn$measureProduct (из $quantityProduct)";
                                $textAlert .= '.%0AОстатки по складам: Нск '.$remnantsProduct[481].', Спб '.$remnantsProduct[483].', Кдр '.$remnantsProduct[485].', Мск '.$remnantsProduct[487];
                                $textAlert .= '%0AНужно переместить недостающий товар либо сделать его отгрузку с другого склада.';
                                Bitrix_help::send_message($id_user, $textAlert);
                            }
                            //getStorageName($idStorage)
                        }
                        unset($value); // Сбрасываем значение
                    }



                    //$zapros = 'crm.invoice.add';
                    $zapros = 'crm.item.add';
                    //$parametr = 'fields[RESPONSIBLE_ID]='.$id_responsible.'&fields[UF_COMPANY_ID]='.$id_company.'&fields[UF_CONTACT_ID]=0'.'&fields[UF_MYCOMPANY_ID]='.$id_firma.'&fields[UF_DEAL_ID]='.$id_sdelka.'&fields[ORDER_TOPIC]='.$id_topic.'&fields[PAY_SYSTEM_ID]=1'.'&fields[PERSON_TYPE_ID]=1'.'&fields[STATUS_ID]=N'.'&fields[DATE_PAY_BEFORE]='.$srok_oplad.'&fields[UF_CRM_1631855080]='.$sklad.'&fields[UF_CRM_1632391175]='.$tipopl.'&fields[UF_CRM_1635061325]='.$formaopl.'&fields[UF_CRM_60DAE233DF14B]=1'.'&fields[UF_CRM_1632738507]=N';
                    $parametr = 'entityTypeId=31' . '&fields[assignedById]=' . $id_responsible . '&fields[companyId]=' . $id_company . '&fields[contactId]=' . $id_contact . '&fields[mycompanyId]=' . $id_firma . '&fields[parentId2]=' . $id_sdelka . '&fields[title]=' . $id_topic . '&fields[stageId]=DT31_1:N' . '&fields[closedate]=' . $srok_oplad . '&fields[ufCrm_6260f70671097]=' . $srok_oplad . '&fields[ufCrm_SMART_INVOICE_1651083239729]=' . $sklad . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $tipopl . '&fields[ufCrm_SMART_INVOICE_1651083629638]=' . $formaopl . '&fields[comments]=' . $commmrnt_deal . '&fields[ufCrm_SMART_INVOICE_1651138836085]=Y' . '&fields[ufCrm_SMART_INVOICE_1651509493]=DT31_1:N'; //.'&fields[UF_CRM_1632738507]=N'.'&fields[PAY_SYSTEM_ID]=1'.'&fields[PERSON_TYPE_ID]=1';
                    $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm . '&fields[sourceDescription]=' . $nds0. '&fields[ufCrm_62B53CC5A2EDF]=' . $id_dostavka;
                    if (!(is_null($sourse_deal))) {
                        $parametr = $parametr . '&fields[sourceId]=' . $sourse_deal;
                    }
                    //lod_ftp($parametr);
                    //echo $parametr;
                    //echo '<br/>';
                    //lod_ftp($parametr);
                    $res = zapros($zapros, $parametr);
                    {
                        if (array_key_exists('error', $res)) {
                            echo $res['error_description'];
                            echo '<br/>';
                        } else {
                            $id_schot = $res['result']['item']['id'];
                            //lod_ftp(json_encode($id_schot));
                            $parametr_product = 'ownerType=SI&ownerId=' . $id_schot;
                            $nom = 0;
                            foreach ($resproduct as &$value) {
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][ownerId]=' . $id_schot . '&productRows[' . $nom . '][ownerType]=SI';
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][productId]=' . $value['PRODUCT_ID'] . '&productRows[' . $nom . '][quantity]=' . $value['QUANTITY'] . '&productRows[' . $nom . '][price]=' . $value['PRICE'] . '&productRows[' . $nom . '][taxRate]=' . ($value['TAX_RATE']);
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][taxIncluded]=' . $value['TAX_INCLUDED'] . '&productRows[' . $nom . '][measureCode]=' . $value['MEASURE_CODE'] . '&productRows[' . $nom . '][measureName]=' . $value['MEASURE_NAME'];
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][productName]=' . $value['PRODUCT_NAME'] . '&productRows[' . $nom . '][customized]=' . $value['CUSTOMIZED'];
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][priceExclusive]=' . $value['PRICE_EXCLUSIVE'] . '&productRows[' . $nom . '][priceNetto]=' . $value['PRICE_NETTO'];
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][priceBrutto]=' . $value['PRICE_BRUTTO'] . '&productRows[' . $nom . '][discountTypeId]=' . $value['DISCOUNT_TYPE_ID'];
                                $parametr_product = $parametr_product . '&productRows[' . $nom . '][discountRate]=' . $value['DISCOUNT_RATE'] . '&productRows[' . $nom . '][discountSum]=' . $value['DISCOUNT_SUM'];

                                //$parametr = $parametr.'&fields[PRODUCT_ROWS]['.$nom.'][PRODUCT_ID]='.$value['PRODUCT_ID'].'&fields[PRODUCT_ROWS]['.$nom.'][QUANTITY]='.$value['QUANTITY'].'&fields[PRODUCT_ROWS]['.$nom.'][PRICE]='.$value['PRICE'].'&fields[PRODUCT_ROWS]['.$nom.'][VAT_RATE]='.($value['TAX_RATE']/100);
                                //$parametr = $parametr.'&fields[PRODUCT_ROWS]['.$nom.'][VAT_INCLUDED]='.$value['TAX_INCLUDED'].'&fields[PRODUCT_ROWS]['.$nom.'][MEASURE_CODE]='.$value['MEASURE_CODE'].'&fields[PRODUCT_ROWS]['.$nom.'][MEASURE_NAME]='.$value['MEASURE_NAME'];
                                //$parametr = $parametr.'&fields[PRODUCT_ROWS]['.$nom.'][CATALOG_XML_ID]=FUTURE-1C-CATALOG'.'&fields[PRODUCT_ROWS]['.$nom.'][PRODUCT_NAME]='.$value['PRODUCT_NAME'].'&fields[PRODUCT_ROWS]['.$nom.'][CUSTOMIZED]='.$value['CUSTOMIZED'];
                                //$parametr = $parametr.'&fields[PRODUCT_ROWS]['.$nom.'][PRODUCT_XML_ID]='.pr1C($value['PRODUCT_ID']);
                                // DISCOUNT_PRICE  MODULE

                                $nom = $nom + 1;
                            }
                            unset($value); // Сбрасываем знвчение

                            //lod_ftp($parametr_product);
                            $res_product = zapros('crm.item.productrow.set', $parametr_product);
                            //    echo $id_schot;
                            //    echo '<br/>';

                            //Сгенерить печатную форму
                            $number_invoice = Contracts::get_number_invoice($id_firma, namefirma($id_company), date("d.m.Y"), $id_user);
                            //Bitrix_help::send_message(215, '$number invoice ' . $number_invoice);
                            $zapros = 'crm.documentgenerator.document.add';
                            $parametr = 'templateId=' . $id_shablon . '&entityTypeId=' . $id_suchnosti . '&entityId=' . $id_schot . '&stampsEnabled=1' . '&values[DocumentNum]=' . $number_invoice . '&values[Dostavka]=' . $dostavka;
                            //echo $parametr;
                            //echo '<br/>';
                            $res = zapros($zapros, $parametr);
                            {
                                if (array_key_exists('error', $res)) {
                                    echo $res['error_description'];
                                } else {
                                    $id_schotpech = $res['result']['document'];
                                    //$nomschsh = $id_schotpech['number'];
                                    $nomschsh = $number_invoice;
                                    $ssilkaworld = $id_schotpech['downloadUrlMachine'];
                                    $id_pech_form = $id_schotpech['id'];
                                    //echo $ssilkaworld;
                                }}
                            //Номер печатной формы в номер счёта
                            //$zapros   = 'crm.invoice.update';
                            //$parametr = 'id='.$id_schot.'&fields[ACCOUNT_NUMBER]='.$nomschsh.'&fields[UF_CRM_1633182658]='.$id_pech_form;
                            $zapros = 'crm.item.update';
                            $parametr = 'entityTypeId=31' . '&id=' . $id_schot . '&fields[accountNumber]=' . $nomschsh . '&fields[ufCrm_SMART_INVOICE_1651138396589]=' . $id_pech_form;

                            $res = zapros($zapros, $parametr);
                            {
                                if (array_key_exists('error', $res)) {
                                    echo $res['error_description'];
                                } else {
                                }
                            }
                            // Записать данные счёта в сделку
                            //$id_sdelka  $srok_oplad  $tipopl 'N' '1'
                            $tipopl2 = $tipopl - 116;
                            $zapros = 'crm.deal.update';
                            $parametr = 'id=' . $id_sdelka . '&fields[UF_CRM_1632738230]=' . $srok_oplad . '&fields[UF_CRM_1632738315]=' . $tipopl2 . '&fields[UF_CRM_1632738354]=DT31_1:N' . '&fields[UF_CRM_1656582798]=' . $paymemtTerm;
                            $userPermit = Bitrix_help::getUserPermitShipment($id_schot);
                            $parametr .= "&fields[UF_CRM_1655618547]=$userPermit";
                            //. '&fields[UF_CRM_1632738559]=1' разрешение не устанавливаем
                            $res = zapros($zapros, $parametr);
                            {
                                if (array_key_exists('error', $res)) {
                                    echo $res['error_description'];
                                } else {
                                }
                        }
                        }}
                }
            } //*************************************************************************************************************
            else {
                // Сообщить о несоответствии стадии
                soobchenie($id_user, 'Создавать счёт можно только на стадии ВЫСТАВЛЕНИЕ СЧЁТА');
            }
        }
    }
}
    //{if $flagpr
    //echo 'TRUE';
    //else
    //echo 'FALSE';
    //}

    //echo $flagpr;
    //echo ' <br/>';

function prmin($idproduct)
{
    $result1 = 0;
    $zapros = 'crm.product.get';
    $parametr = 'id=' . $idproduct;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result']['PROPERTY_123']['value'];
        }

        $result1 = str_replace(chr(194) . chr(160), '', $result1);
    }
    return $result1;
}

function pr1C($idproduct)
{
    $result1 = '_';
    $zapros = 'crm.product.get';
    $parametr = 'id=' . $idproduct;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result']['XML_ID'];
        }

    }

    return $result1;
}

function namefirma($idfirma)
{
    $result1 = '_';
    $zapros = 'crm.company.get';
    $parametr = 'id=' . $idfirma;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result']['TITLE'];
        }

    }
    return $result1;
}

function contractfirma($idfirma)
{
    $result1 = '_';
    $zapros = 'crm.company.get';
    $parametr = 'id=' . $idfirma;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result']['UF_CRM_1623915176'];
        }
    }
    return $result1;
}

function nameuser($iduser)
{
    $result1 = '_';
    $zapros = 'user.get';
    $parametr = 'id=' . $iduser;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result'][0]['NAME'] . ' ' . $res['result'][0]['LAST_NAME'];
        }

    }
    return $result1;
}

function departuser($iduser)
{
    $result1 = '_';
    $zapros = 'user.get';
    $parametr = 'id=' . $iduser;
    $res = zapros($zapros, $parametr);
    {
        if (array_key_exists('error', $res)) {
            echo $res['error_description'];
        } else {
            $result1 = $res['result'][0]['UF_DEPARTMENT'][0];
        }

    }
    return $result1;
}

function zapros($zap, $param)
{
    global $bitrixPortal, $bitrixToken;

    $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . '/' . $zap;
    $queryData = $param;

    $curl = curl_init();
    curl_setopt_array($curl, array(
        CURLOPT_SSL_VERIFYPEER => 0,
        CURLOPT_POST => 1,
        CURLOPT_HEADER => 0,
        CURLOPT_RETURNTRANSFER => 1,
        CURLOPT_URL => $queryUrl,
        CURLOPT_POSTFIELDS => $queryData,
    ));
    $result = curl_exec($curl);
    curl_close($curl);
    $result = json_decode($result, 1);
    if (!is_array($result)) {
        return array();
    }
    return $result;
}
function soobchenie($id_us, $soobch)
{
    global $bitrixPortal, $bitrixTokenMessage;

    $queryUrl = $bitrixPortal . '/rest/' . $bitrixTokenMessage . '/im.message.add';
    $queryData = 'USER_ID=' . $id_us . '&message=' . $soobch;
    $curl = curl_init();
    curl_setopt_array($curl, array(
        CURLOPT_SSL_VERIFYPEER => 0,
        CURLOPT_POST => 1,
        CURLOPT_HEADER => 0,
        CURLOPT_RETURNTRANSFER => 1,
        CURLOPT_URL => $queryUrl,
        CURLOPT_POSTFIELDS => $queryData,
    ));
    $result = curl_exec($curl);
    curl_close($curl);
    $result = json_decode($result, 1);
    return $result;
}

function lod_ftp($soobch)
{
    global $ftpPortal, $ftpUser, $ftpPass;

    $conn_id = ftp_connect($ftpPortal);
    if ($conn_id === false) {
        return;
    }

    $login_result = ftp_login($conn_id, $ftpUser, $ftpPass);
    ftp_pasv($conn_id, true);
    ftp_set_option($conn_id, FTP_TIMEOUT_SEC, 30);
    // Создание файла на сервере
    $file1 = fopen('php://temp', 'r+');
    fwrite($file1, $soobch);
    rewind($file1);
    if (@ftp_fput($conn_id, 'Bitrix/log ' . round(microtime(true) * 1000, 0) . '.txt', $file1, FTP_ASCII)) {
        echo 'File create';
    } else {
        echo 'File not create';
    }
    // Закрытие соединения
    ftp_close($conn_id);
}
function decompose_contract($lue)
{ //Фирма: ТехТорг ООО, вид договора: С покупателем,//Договор № 78 от 01.06.2022//, срок действия
    $arr_res = array();
    $arr_dog = explode('//', $lue);
    if (count($arr_dog) > 1) {
        $nac = $arr_dog[0];
        $hel = mb_strpos($nac, ', вид договора');
        $nac = mb_substr($nac, 7, $hel - 7);
        $id_firm = 0;

        switch ($nac) {
            case 'ТехТорг ООО':
                $id_firm = 5381;
                break;
            case 'Элемент':
                $id_firm = 5385;
                break;
            case 'Системы':
                $id_firm = 8923;
                break;
            case 'Торговый дом СР':
                $id_firm = 5383;
                break;
            case 'Гузиков Михаил Геннадьевич ИП':
                $id_firm = 22145;
                break;
            case 'ИП Воробьев Д.В.':
                $id_firm = 23217;
                break;
            case 'Эксперты розлива ООО':
                $id_firm = 8897;
                break;
            case 'ИП Гузиков М.Г.':
                $id_firm = 22145;
                break;
        }
        if ($id_firm > 0) {
            $arr_res[0] = $id_firm;
            $arr_res[1] = $arr_dog[1];
        }
    }
    return $arr_res;
}

//function checkprice($id_company1,  $arrmin1, $tipopl1){//************************************************* Написать */  true - отгрузка разрешена
/*
$arrmin [ name => $value['PRODUCT_NAME'], id => $value['PRODUCT_ID'],  price => $price,  pricemin => $pricemin,  quantity => $value['QUANTITY']]

$tipopl
if ($tipoplstr=='Предоплата')
//$tipopl='371';
$tipopl='493';
else
{
{
if ($tipoplstr=='Отсрочка')
//$tipopl='373';
$tipopl='495';
else
{
{
if ($tipoplstr=='Частичная')
//$tipopl='375';
$tipopl='497';
else
$tipopl='493';
{
}}}}}
 */
//    return false;
//}
