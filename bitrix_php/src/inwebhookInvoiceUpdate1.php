<?php 
sleep(10); 
//exit();  
$id = $_REQUEST['ID_SDELKA'];

$bitrixPortal = getenv('BITRIX_PORTAL');
$bitrixToken = getenv('BITRIX_TOKEN');
$bitrixTokenMessage = getenv('BITRIX_TOKEN_MESSAGE');
$ftpPortal = getenv('FTP_PORTAL');
$ftpUser = getenv('FTP_USER');
$ftpPass = getenv('FTP_PASS');

include 'main_function.php'; 
$serviceUser = 215;
$flag_busy_invoice = get_busy_invoice($id); // При начале флаг занят записывается при окончании обработки сбрасывается

if ($flag_busy_invoice) {
    $fl_tec = $flag_busy_invoice;
    $nom_fl_busy = 0;
    while ($fl_tec) {
        $nom_fl_busy = $nom_fl_busy + 1; 
        sleep(5);
        $fl_tec = get_busy_invoice($id);
        if ($nom_fl_busy > 15) {
            send_message($serviceUser, 'Счёт занят !!! ' . $id);
            set_busy_invoice($id, 0); // Освобождаем счёт. Так надолго не должен блочиться
            break;
            exit(); 
        }
    }
}

$res_set = set_busy_invoice($id, 1);
//send_message(171, $id);
//exit(); ///
$array_stage = array('DT31_1:N' => 1, 'DT31_1:S' => 2, 'DT31_1:P' => 3, 'DT31_1:D' => 4);

$parametr = 'entityTypeId=31&id=' . $id;
$res_arr = zapros('crm.item.get', $parametr);
if (count($res_arr) > 0) {
    $userPermit = Bitrix_help::getUserPermitShipment($id);
    // Если получены поля счёта тогда обработка
    $res = $res_arr['result']['item'];
    $flag_obnovlenie = 0;
    $flag_obnovlenie_deal = 0;
    $zapros = 'crm.item.update';
    $zapros_deal = 'crm.deal.update';

    $uf_deal_id      = $res['parentId2']; // Ид сделки
    $responsible_id  = $res['assignedById']; // Ответственный
    $uf_mycompany_id = $res['mycompanyId']; // Ид нашей фирмы
    $uf_company_id   = $res['companyId']; // Ид покупателя
    $uf_contact_id   = $res['contactId']; // Ид контакта
    $order_topic     = $res['title']; // Заголовок счёта
    $status_id       = $res['stageId']; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
    $tec_stage_prev  = $res['previousStageId']; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
    $xml_id          = $res['xmlId']; // Код из 1С
    $srok_opl        = $res['closedate']; // Срок оплаты
    $srok_opl        = substr($srok_opl, 0, 10); // Оставляем только дату
    $tec_stage       = $res['ufCrm_SMART_INVOICE_1651509493']; // Cтадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
    $check_respit    = $res['ufCrm_SMART_INVOICE_1651138836085']; // Разрешение на отгрузку: Да = 1; Нет = 0
    $tip_opl         = $res['ufCrm_SMART_INVOICE_1651114959541']; // Тип оплаты счёта: 493 - Предоплата; 495 - Отсрочка; 497 - Частичная
    $payments        = $res['ufCrm_SMART_INVOICE_1651116689037']; // Платёжки по счёту
    $id_pech_form    = $res['ufCrm_SMART_INVOICE_1651138396589']; // Ид сформированной печатной формы
    $idStore         = $res['ufCrm_SMART_INVOICE_1651083239729']; // Склад
    $paymemtTermInv  = $res['ufCrm_SMART_INVOICE_1656584515597']; // Отсрочка в счёте
    if (empty($paymemtTermInv)) {
        $paymemtTermInv  = 0;  
    }
    $res_arr_product = zapros('crm.productrow.list', 'filter[OWNER_TYPE]=SI&filter[OWNER_ID]=' . $id);
    if (count($res_arr_product) > 0) {
        $product_rows_array = $res_arr_product['result']; // Массив товаров
    } else {
        $product_rows_array = array();
    }

    /*
    productRows['.$nom.'][ownerType]     =SI';
    productRows['.$nom.'][ownerId]       ='.$id_schot.'&
    productRows['.$nom.'][productId]     ='.$value['PRODUCT_ID'].'&
    productRows['.$nom.'][quantity]      ='.$value['QUANTITY'].'&
    productRows['.$nom.'][price]         ='.$value['PRICE'].'&
    productRows['.$nom.'][taxRate]       ='.($value['TAX_RATE']);
    productRows['.$nom.'][taxIncluded]   ='.$value['TAX_INCLUDED'].'&
    productRows['.$nom.'][measureCode]   ='.$value['MEASURE_CODE'].'&
    productRows['.$nom.'][measureName]   ='.$value['MEASURE_NAME'];
    productRows['.$nom.'][productName]   ='.$value['PRODUCT_NAME'].'&
    productRows['.$nom.'][customized]    ='.$value['CUSTOMIZED'];
    productRows['.$nom.'][priceExclusive]='.$value['PRICE_EXCLUSIVE'].'& - цена без НДС
    productRows['.$nom.'][priceNetto]    ='.$value['PRICE_NETTO'];       - тоже что и выше
    productRows['.$nom.'][priceBrutto]   ='.$value['PRICE_BRUTTO'].'&    - цена с налогом
    productRows['.$nom.'][discountTypeId]='.$value['DISCOUNT_TYPE_ID'];  (2) тип скидки
    productRows['.$nom.'][discountRate]  ='.$value['DISCOUNT_RATE'].'&   (0) величина скидки
    productRows['.$nom.'][discountSum]   ='.$value['DISCOUNT_SUM'];      (0) сумма скидки
    SORT
     */

    $parametr_deal = 'id=' . $uf_deal_id;
    $res_arr_deal = zapros('crm.deal.get', $parametr_deal);

    if (count($res_arr_deal) > 0) {
        // Если получены поля сделки
        $res = $res_arr_deal['result'];
        /*
         *
         * $name_deal        = $res[TITLE];
         * $stage_id         = $res[STAGE_ID];             // Стадия: NEW(Не разобрано); PREPAYMENT_INVOICE(Выявление потребности); PREPARATION(Заинтересован);
         *                                                 // EXECUTING(Согласование условий договор); FINAL_INVOICE(Выставление счёта); 1(Сделка успешна); WON(Выиграна); LOSE(Проиграна); APOLOGY(Анализ проигрыша)
         * $type_id          = $res[TYPE_ID];              // Тип сделки: 1 - Продажа СР; 3 - Продажа Колонны ...
         * $category_id      = $res[CATEGORY_ID];          // Ид направления сделки: 0 - общее направление
         *
         * // OPENED "Y" CLOSED "N"
         * $assignrd_by_id   = $res[ASSIGNED_BY_ID];       // Ответственный ИД
         * $modify_by_id     = $res[MODIFY_BY_ID];         // Изменятель ИД
         * $department       = $res[UF_CRM_612463720554B]; // Подразделение: 1 - Продажа СР; 3 - Продажа Колонны ...
         * $tec_stage_id     = $res[UF_CRM_1632738604];    // Текущая стадия
         */
        $inv_stage_id       = $res['STAGE_ID'];
        $deal_check_respit  = $res['UF_CRM_60D2AFAEB32CC']; // Разрешение на отгрузку: Да = 1; Нет = 0
        $inv_srok_opl       = $res['UF_CRM_1632738230']; // Срок оплаты счёта: Дата
        $inv_srok_opl       = substr($inv_srok_opl, 0, 10); // Оставляем только дату
        $inv_tip_opl        = $res['UF_CRM_1632738315']; // Тип оплаты счёта: 377 - Предоплата; 379 - Отсрочка; 381 - Частичная
        $inv_tec_stage      = $res['UF_CRM_1632738354']; // Тек стадия счёта: N - новый; S - отправлен; 1 - выгружен в 1С; P - успешный; D - не оплачен
        $inv_payments       = $res['UF_CRM_1632738424']; // Платёжки по счёту
        $inv_check_respit   = $res['UF_CRM_1632738559']; // Проверка счёта Да = 1; Нет = 0
        $deal_company_id    = $res['COMPANY_ID']; // Ид компании
        $deal_mycompany_id  = firmid($deal_company_id); // Ид нашей фирмы
        $product_deal_array = productdeal($uf_deal_id); // Массив товаров в сделке
        $idDealConnect      = $res['UF_CRM_1655891443']; // Связанная сделка
        $typeShipment       = $res['UF_CRM_1655141630']; // Тип отгрузки
        $type_id            = $res['TYPE_ID'];
        $name_deal          = $res['TITLE'];
        $paymemtTerm        = $res['UF_CRM_1656582798']; // Отсрочка
        $expert             = $res['UF_CRM_1655618547']; // Эксперт
        /**
         *
         * Данные из счёта :
         *
         * $uf_mycompany_id    // Ид нашей фирмы
         * $uf_company_id      // Ид покупателя
         * $status_id          // Cтадия счёта:     DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
         * $tec_stage          // Тек стадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
         * $srok_opl           // Срок оплаты
         * $check_respit       // Разрешение на отгрузку: Да = 1; Нет = 0                                      НЕ ИСПОЛЬЗУЕТСЯ
         * $tip_opl            // Тип оплаты счёта:  493 - Предоплата; 495 - Отсрочка; 497 - Частичная
         * $payments           // Платёжки по счёту
         * $product_rows_array // Массив товаров
         *
         * Данные из сделки :
         *
         * $deal_mycompany_id  // Ид нашей фирмы
         * $deal_company_id    // Ид компании
         * $inv_tec_stage      // Тек стадия счёта: DT31_1:N - новый; DT31_1:S - отправлен; DT31_1:P - успешный; DT31_1:D - не оплачен
         * $inv_srok_opl       // Срок оплаты счёта: Дата
         * $inv_check_respit   // Проверка счёта Да = 1; Нет = 0
         * $inv_tip_opl        // Тип оплаты счёта: 377 - Предоплата; 379 - Отсрочка; 381 - Частичная
         * $inv_payments       // Платёжки по счёту
         * $product_deal_array // Массив товаров в сделке
         *
         * $deal_check_respit // Разрешение на отгрузку сделки: Да = 1; Нет = 0
         *
         * $flag_obnovlenie      = 0;
         * $flag_obnovlenie_deal = 0;
         * $zapros        = 'crm.item.update';
         * $zapros_deal   = 'crm.deal.update';
         * $parametr      = 'id='.$id.'entityTypeId=31';
         * $parametr_deal = 'id='.$uf_deal_id;
         */

        if ($payments != $inv_payments) {
            // Если платёжки правились в счёте - тогда откат данных из сделки
            $payments_update = payments_upd($payments, $inv_payments);
            if ($payments_update != '') {
                $parametr .= $payments_update;
                $flag_obnovlenie = 1;
            }
        }
        if ($array_stage[$status_id] < $array_stage[$inv_tec_stage]) {
            // Возврат назад по воронке - откат
            $flag_obnovlenie = 1;
            $parametr = $parametr . '&fields[stageId]=' . $inv_tec_stage . '&fields[ufCrm_SMART_INVOICE_1651509493]=' . $inv_tec_stage;
            if ($uf_mycompany_id != $deal_mycompany_id) {
                $parametr = $parametr . '&fields[mycompanyId]=' . $deal_mycompany_id;
            }
            if ($uf_company_id != $deal_company_id) {
                $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
            }
            if ($srok_opl != $inv_srok_opl) {
                $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
            }
            if ($paymemtTermInv != $paymemtTerm) {
                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
            }
            if (($tip_opl - 116) != $inv_tip_opl) {
                $inv_tip_opl_correct = ($inv_tip_opl + 116);
                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
            }
            $products_update = products_upd($product_rows_array, $product_deal_array, $id);
            send_message($responsible_id, 'Запрещено двигать счёт ' . $order_topic . ' обратно по воронке. Изменения будут сброшены.');
        } elseif ($array_stage[$status_id] == $array_stage[$inv_tec_stage]) {
            // Правка без изменения стадии
            if ($status_id == 'DT31_1:D') {
                if (($inv_stage_id == 'LOSE')||($inv_stage_id == 'APOLOGY'))  {
                    // Конечная стадия "Не оплачен"- откат  
                    if ($uf_mycompany_id != $deal_mycompany_id) {
                        $parametr = $parametr . '&fields[mycompanyId]=' . $deal_mycompany_id;
                        $flag_obnovlenie = 1;
                    }
                    if ($uf_company_id != $deal_company_id) {
                        $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                        $flag_obnovlenie = 1;
                    }
                    if ($srok_opl != $inv_srok_opl) {
                        $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                        $flag_obnovlenie = 1;
                    }
                    if ($paymemtTermInv != $paymemtTerm) {
                        $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                        $flag_obnovlenie = 1;
                    }
                    if (($tip_opl - 116) != $inv_tip_opl) {
                        $inv_tip_opl_correct = ($inv_tip_opl + 116);
                        $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                        $flag_obnovlenie = 1;
                    }
                    $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                    if (($flag_obnovlenie==1)||($products_update==1)){
                        send_message($responsible_id, 'Счёт ' . $order_topic . ' находится в конечной стадии. Его править нельзя.');
                        }
                } else {
                    Bitrix_help::send_message($serviceUser, "Счёт $id отменён , сделка $uf_deal_id не провалена. Что-то пошло не так.");   
                }
            } else {
                $flag_change_invoice = true;
                if ($status_id == 'DT31_1:P') {
                    // Стадия На сборку. Если сделка закрыта - тогда откат и $flag_change_invoice = FALSE;// ИНАЧЕ возврат сделки на пред этап и сделку на выст счёта
                    if ($inv_stage_id == 'WON')  {
                        if ($uf_mycompany_id != $deal_mycompany_id) {
                            $parametr = $parametr . '&fields[mycompanyId]=' . $deal_mycompany_id;
                            $flag_obnovlenie = 1;
                        }
                        if ($uf_company_id != $deal_company_id) {
                            $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                            $flag_obnovlenie = 1;
                        }
                        if ($srok_opl != $inv_srok_opl) {
                            $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                            $flag_obnovlenie = 1;
                        }
                        if ($paymemtTermInv != $paymemtTerm) {
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                            $flag_obnovlenie = 1;
                        }
                        if (($tip_opl - 116) != $inv_tip_opl) {
                            $inv_tip_opl_correct = ($inv_tip_opl + 116);
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                            $flag_obnovlenie = 1;
                        }
                        $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                        $flag_change_invoice = false;
                        if (($flag_obnovlenie==1)||($products_update==1)){
                            send_message($responsible_id, 'Сделка связанная со счётом ' . $order_topic . ' закрыта. Счёт править нельзя.');
                        }
                    } else {
                        $flag_change_invoice = false;
                        //Bitrix_help::send_message($serviceUser, "Счёт $id на отгрузку, сделка $uf_deal_id не Успешна или На отгрузке. Что-то пошло не так."); //????????????????????????????7  
                    }
                }
                if ($flag_change_invoice) {
                    // Сделка не закрыта
                    //if (($status_id=='N')or($status_id=='S')){    Не конечная стадия - проверка
                    if (($uf_mycompany_id != $deal_mycompany_id) or ($uf_mycompany_id != firmid($uf_company_id))) {
                        // Если наша Фирма поменялась - откат
                        $parametr = $parametr . '&fields[mycompanyId]=' . $deal_mycompany_id;
                        $flag_obnovlenie = 1;
                        if ($uf_company_id != $deal_company_id) {
                            $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                        }
                        if ($srok_opl != $inv_srok_opl) {
                            $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                        }
                        if ($paymemtTermInv != $paymemtTerm) {
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                        }
                        if (($tip_opl - 116) != $inv_tip_opl) {
                            $inv_tip_opl_correct = ($inv_tip_opl + 116);
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                        }
                        $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                        send_message($responsible_id, 'Запрещено менять фирму отгрузки в счёте ' . $order_topic . '. Заведите новый счёт. Изменения будут сброшены.');
                    } else {
                        $arr_check_price = checkprice1($product_rows_array, $product_deal_array, $uf_company_id, $uf_deal_id, $uf_mycompany_id, $tip_opl, $paymemtTermInv);
                        // Проверка на цены: пустой массив - ОК, иначе не прошли в результате массив с проблемными товарами
                        //send_message(215, $check_price);
                        //$arr_check_price = array();   //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=
                        if (count($arr_check_price) == 0) {
                            // Проверка по ценам ОК, обновляем поля в сделке, переформировываем счёт при необходимости, если выгружен в 1С - сигнал об обновлении.
                            if ($uf_company_id != $deal_company_id) {
                                $parametr_deal = $parametr_deal . '&fields[COMPANY_ID]=' . $uf_company_id;
                                $flag_obnovlenie_deal = 1;
                            }
                            if ($srok_opl != $inv_srok_opl) {
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738230]=' . $srok_opl;
                                $flag_obnovlenie_deal = 1;
                            }
                            if ($paymemtTermInv != $paymemtTerm) {
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1656582798]=' . $paymemtTermInv;
                                $flag_obnovlenie_deal = 1;
                            }
                            if (($tip_opl - 116) != $inv_tip_opl) {
                                $flag_obnovlenie_deal = 1;
                                $tip_opl_correct = ($tip_opl - 116);
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738315]=' . $tip_opl_correct;
                            }
                            if ($expert != $userPermit) {
                                $parametr_deal .= "&fields[UF_CRM_1655618547]=$userPermit";
                                $flag_obnovlenie_deal = 1;
                            }
                            $products_update_deal1 = products_upd_deal($product_rows_array, $product_deal_array, $uf_deal_id);
                            if (($status_id == 'DT31_1:S') or ($status_id == 'DT31_1:P')) {
                                sendupdate1c($id, $xml_id, 2); // Отправить флаг об обновлении в 1С
                            }
                            // Переформировываем печатную форму    crm.documentgenerator.document.update Если изменились товары или клиент
                            if (($products_update_deal1 == 1) or ($uf_company_id != $deal_company_id)) {
                                updateprintinvoice($id_pech_form);
                            }
                        } else {
                            // Откат и запрос по ценам
                            $flag_obnovlenie = 1;
                            if ($uf_company_id != $deal_company_id) {
                                $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                            }
                            if ($srok_opl != $inv_srok_opl) {
                                $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                            }
                            if ($paymemtTermInv != $paymemtTerm) {
                                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                            }
                            if (($tip_opl - 116) != $inv_tip_opl) {
                                $inv_tip_opl_correct = ($inv_tip_opl + 116);
                                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                            }
                            $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                            send_message($responsible_id, 'Условия в счёте ' . $order_topic . ' хуже согласованных. Запрос с новыми условиями отправлен.');
                            // Отправить запрос
                            request_price($responsible_id, $arr_check_price, $uf_deal_id, $order_topic, $tip_opl, $srok_opl, $uf_mycompany_id, $uf_company_id, $tip_opl, $paymemtTermInv);
                        }
                    }
                }
            }
        } else {
            // Правка со сдвигом
            if (($uf_mycompany_id != $deal_mycompany_id) or ($uf_mycompany_id != firmid($uf_company_id))) {
                // Если наша Фирма поменялась - откат
                $parametr = $parametr . '&fields[mycompanyId]=' . $deal_mycompany_id;
                $flag_obnovlenie = 1;
                $parametr = $parametr . '&fields[stageId]=' . $inv_tec_stage . '&fields[ufCrm_SMART_INVOICE_1651509493]=' . $inv_tec_stage;
                if ($uf_company_id != $deal_company_id) {
                    $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                }
                if ($srok_opl != $inv_srok_opl) {
                    $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                }
                if ($paymemtTermInv != $paymemtTerm) {
                    $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                }
                if (($tip_opl - 116) != $inv_tip_opl) {
                    $inv_tip_opl_correct = ($inv_tip_opl + 116);
                    $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                }
                $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                send_message($responsible_id, 'Запрещено менять фирму отгрузки в счёте ' . $order_topic . '. Заведите новый счёт. Изменения будут сброшены.');
            } else {
                if ($status_id == 'DT31_1:D') {
                    // Не оплачен - перегрузка из счёта в сделку и в не успешные. В 1С - на удаление.
                    $flag_obnovlenie_deal = 1;
                    $parametr_deal = $parametr_deal . '&fields[STAGE_ID]=LOSE';
                    $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738604]=LOSE';
                    $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738354]=DT31_1:D';
                    if ($uf_company_id != $deal_company_id) {
                        $parametr_deal = $parametr_deal . '&fields[COMPANY_ID]=' . $uf_company_id;
                    }

                    if ($srok_opl != $inv_srok_opl) {
                        $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738230]=' . $srok_opl;
                    }

                    if ($paymemtTermInv != $paymemtTerm) {
                        $parametr_deal = $parametr_deal . '&fields[UF_CRM_1656582798]=' . $paymemtTermInv;
                    }

                    if (($tip_opl - 116) != $inv_tip_opl) {
                        $tip_opl_correct = ($tip_opl - 116);
                        $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738315]=' . $tip_opl_correct;
                    }
                    if ($expert != $userPermit) {
                        $parametr_deal .= "&fields[UF_CRM_1655618547]=$userPermit";
                        //$flag_obnovlenie_deal = 1;
                    }                   
                    $products_update_deal1 = products_upd_deal($product_rows_array, $product_deal_array, $uf_deal_id);
                    send_message($responsible_id, 'Счёт ' . $order_topic . ' переведён в Не оплаченные. Сделка - в проигранные.');
                    sendupdate1c($id, $xml_id, 0); // Отправить флаг об удалении в 1С
                } elseif ($status_id == 'DT31_1:P') {
                    // Если пред. не 1С - откат. Иначе - проверка цен. Успех - перегр сч в сд и сдвиг сделки в успешные, иначе - по ценам не прошли - откат
                    if ($inv_tec_stage != 'DT31_1:S') {
                        // Откат. На стадию Отгрузка можно только со стадии Отправлен
                        $parametr = $parametr . '&fields[stageId]=' . $inv_tec_stage . '&fields[ufCrm_SMART_INVOICE_1651509493]=' . $inv_tec_stage;
                        $flag_obnovlenie = 1;
                        if ($uf_company_id != $deal_company_id) {
                            $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                        }
                        if ($srok_opl != $inv_srok_opl) {
                            $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                        }
                        if ($paymemtTermInv != $paymemtTerm) {
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                        }
                        if (($tip_opl - 116) != $inv_tip_opl) {
                            $inv_tip_opl_correct = ($inv_tip_opl + 116);
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                        }
                        $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                        send_message($responsible_id, 'Переводить счёт ' . $order_topic . ' на стадию Отгрузка разрешена можно только со стадии Отправлен клиенту. Изменения будут сброшены.');
                    } else {
                        $arr_check_price = checkprice1($product_rows_array, $product_deal_array, $uf_company_id, $uf_deal_id, $uf_mycompany_id, $tip_opl, $paymemtTermInv);
                        if (count($arr_check_price) == 0) {
                            // Проверка по ценам ОК, обновляем поля в сделке, переформировываем счёт при необходимости, если выгружен в 1С - сигнал об обновлении.
                            $parametr_deal = $parametr_deal . '&fields[STAGE_ID]=1';
                            $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738604]=1';
                            $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738354]=DT31_1:P';
                            $flag_obnovlenie_deal = 1;
                            if ($uf_company_id != $deal_company_id) {
                                $parametr_deal = $parametr_deal . '&fields[COMPANY_ID]=' . $uf_company_id;
                            }
                            if ($srok_opl != $inv_srok_opl) {
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738230]=' . $srok_opl;
                            }
                            if ($paymemtTermInv != $paymemtTerm) {
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1656582798]=' . $paymemtTermInv;
                            }
                            if (($tip_opl - 116) != $inv_tip_opl) {
                                $tip_opl_correct = ($tip_opl - 116);
                                $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738315]=' . $tip_opl_correct;
                            }
                            if ($expert != $userPermit) {
                                $parametr_deal .= "&fields[UF_CRM_1655618547]=$userPermit";
                                //$flag_obnovlenie_deal = 1;
                            }                            
                            $products_update_deal1 = products_upd_deal($product_rows_array, $product_deal_array, $uf_deal_id);
                            sendupdate1c($id, $xml_id, 2); // Отправить флаг об обновлении в 1С
                            // Переформировываем печатную форму    crm.documentgenerator.document.update Если изменились товары или клиент
                            if (($products_update_deal1 == 1) or ($uf_company_id != $deal_company_id)) {
                                updateprintinvoice($id_pech_form);
                            }

                            // 1. Заведение накладной // Перенесли после сборки // Отменили
                            Bitrix_help::sendUpdate1c('NEW_DEAL', $uf_deal_id);
                            // 2. Заведение сделки на отгрузку, привязка к тек сделке, формирование печатной формы
                            if (empty($idDealConnect)) {
                                $parametrNewDeal = '';
                                //$idStore = getStorageId($uf_deal_id);
                                if (!empty($idStore)) {
                                    $assignrdByIdStorage = Bitrix_help::getStorageMan($idStore);
                                    if (!empty($assignrdByIdStorage)) {
                                        $parametrNewDeal .= "fields[TITLE]=$name_deal отгрузка со склада";
                                        $parametrNewDeal .= '&fields[CATEGORY_ID]=5&fields[STAGE_ID]=C5:NEW';
                                        $parametrNewDeal .= "&fields[TYPE_ID]=$type_id";
                                        $parametrNewDeal .= "&fields[COMPANY_ID]=$uf_company_id";
                                        $parametrNewDeal .= "&fields[CONTACT_ID]=$uf_contact_id";
                                        $parametrNewDeal .= "&fields[ASSIGNED_BY_ID]=$assignrdByIdStorage";
                                        $parametrNewDeal .= "&fields[UF_CRM_1655891443]=$uf_deal_id";
                                        $parametrNewDeal .= "&fields[UF_CRM_1655141630]=$typeShipment";
                                        $parametrNewDeal .= "&fields[UF_CRM_1632738604]=C5:NEW";
                                        $parametrNewDeal .= "&fields[UF_CRM_1657360424]=НОВЫЙ";
                                        $textProduct = '<ul>';
                                        if (count($product_rows_array) > 0) {
                                            foreach ($product_rows_array as $value) {
                                                //$textProduct .= '\r\n\t<li>'.$value['QUANTITY'].' '.$value['MEASURE_NAME'].' || '.$value['PRODUCT_NAME'] .'<br>\r\n </li>';
                                                $productName = $value['PRODUCT_NAME'];
                                                $productName = str_replace('"', '', $productName);
                                                $textProduct .= '<li>' . $value['QUANTITY'] . ' ' . $value['MEASURE_NAME'] . ' || ' . $productName . '<br> </li>';
                                            }
                                            unset($value);
                                        }
                                        $textProduct .= '</ul>';
                                        $parametrNewDeal .= "&fields[COMMENTS]=$textProduct";

                                        $resNewDeal = Bitrix_help::request('crm.deal.add', $parametrNewDeal);
                                        if (count($resNewDeal) > 0) {
                                            $newDealId = $resNewDeal['result'];
                                            Bitrix_help::setCommentsDeal($newDealId, $textProduct);
                                            // $product_rows_array1 - массив товаров
                                            products_upd_deal($product_rows_array, array(), $newDealId);
                                            $store = Bitrix_help::getStorageName($idStore);
                                            $parameterSbor = 'templateId=133&entityTypeId=2&entityId=' . $newDealId;
                                            $parameterSbor .= '&stampsEnabled=0&values[DealName]=' . $name_deal;
                                            $parameterSbor .= '&values[Men]=' . Bitrix_help::nameuser($responsible_id) . '&values[Store]=' . $store;
                                            $resPrint = Bitrix_help::request('crm.documentgenerator.document.add', $parameterSbor);
                                            if (count($resPrint) > 0) {
                                                $id_schotpech = $resPrint['result']['document'];
                                                $id_pech_form = $id_schotpech['id'];
                                                Bitrix_help::request('crm.deal.update', "id=$newDealId&fields[UF_CRM_1656227383]=$id_pech_form");
                                            }
                                            //$responsibleObserver = Bitrix_help::getObserverService();
                                            Bitrix_help::setObserverDeal($newDealId, $responsible_id, 1);
                                            //Bitrix_help::setObserverDeal($newDealId,$responsibleObserver,1);
                                            $parametr_deal .= '&fields[UF_CRM_1655891443]=' . $newDealId; // Добавляем связь с новой сделкой на отгрузку
                                        } else {
                                            // Не создана отгрузка
                                            Bitrix_help::send_message($serviceUser, "Не создана отгрузка :: $id");
                                        }
                                    } else {
                                        // Не найден кладовщик
                                        Bitrix_help::send_message($serviceUser, "Не найден кладовщик :: $id");
                                    }
                                } else {
                                    // Не найден склад отгрузки
                                    Bitrix_help::send_message($serviceUser, "Не найден склад отгрузки :: $id");
                                }
                            } else {
                                // Связанная сделка уже существует
                                Bitrix_help::send_message($serviceUser, "Связанная сделка уже существует :: $id");
                            }
                            // 3. Запрос на отгрузку // Пока не до конца понятна логика // Запуск вручную
                        } else {
                            // Цены ниже запрашиваемых. Исправьте цены в сделке и создайте счёт заново. Откат.
                            $parametr = $parametr . '&fields[stageId]=' . $inv_tec_stage . '&fields[ufCrm_SMART_INVOICE_1651509493]=' . $inv_tec_stage;
                            $flag_obnovlenie = 1;
                            if ($uf_company_id != $deal_company_id) {
                                $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                            }
                            if ($srok_opl != $inv_srok_opl) {
                                $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                            }
                            if ($paymemtTermInv != $paymemtTerm) {
                                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                            }
                            if (($tip_opl - 116) != $inv_tip_opl) {
                                $inv_tip_opl_correct = ($inv_tip_opl + 116);
                                $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                            }
                            $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                            send_message($responsible_id, 'Условия в счёте ' . $order_topic . ' хуже согласованных. Запрос с новыми условиями отправлен.');
                            // Отправить запрос
                            // $arr_check_price
                            //  $uf_company_id,$uf_deal_id,$uf_mycompany_id,ИЗ МАССИВА $id_product, $tip_opl,ИЗ МАССИВА $price
                            request_price($responsible_id, $arr_check_price, $uf_deal_id, $order_topic, $tip_opl, $srok_opl, $uf_mycompany_id, $uf_company_id, $tip_opl, $paymemtTermInv);
                        }
                    }
                } else {
                    //Проверка цен. Ок - обновление, иначе - проверка аналогично. Если на стадию 1С - выгрузка
                    $arr_check_price = checkprice1($product_rows_array, $product_deal_array, $uf_company_id, $uf_deal_id, $uf_mycompany_id, $tip_opl, $paymemtTermInv);
                    if (count($arr_check_price) == 0) {
                        // Проверка по ценам ОК, обновляем поля в сделке, переформировываем счёт при необходимости, если выгружен в 1С - сигнал об обновлении.
                        $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738354]=' . $status_id;
                        $flag_obnovlenie_deal = 1;
                        if ($uf_company_id != $deal_company_id) {
                            $parametr_deal = $parametr_deal . '&fields[COMPANY_ID]=' . $uf_company_id;
                        }
                        if ($paymemtTermInv != $paymemtTerm) {
                            $parametr_deal = $parametr_deal . '&fields[UF_CRM_1656582798]=' . $paymemtTermInv;
                        }
                        if ($srok_opl != $inv_srok_opl) {
                            $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738230]=' . $srok_opl;
                        }
                        if (($tip_opl - 116) != $inv_tip_opl) {
                            $tip_opl_correct = ($tip_opl - 116);
                            $parametr_deal = $parametr_deal . '&fields[UF_CRM_1632738315]=' . $tip_opl_correct;
                        }
                        if ($expert != $userPermit) {
                            $parametr_deal .= "&fields[UF_CRM_1655618547]=$userPermit";
                            //$flag_obnovlenie_deal = 1;
                        }                        
                        $products_update_deal1 = products_upd_deal($product_rows_array, $product_deal_array, $uf_deal_id);
                        if ($status_id == 'DT31_1:S') {
                            sendupdate1c($id, $xml_id, 1); // Отправить флаг об обновлении в 1С
                        } elseif ($status_id == 'DT31_1:P') {
                            sendupdate1c($id, $xml_id, 2); // Отправить флаг об обновлении в 1С
                        }
                        // Переформировываем печатную форму    crm.documentgenerator.document.update Если изменились товары или клиент
                        if (($products_update_deal1 == 1) or ($uf_company_id != $deal_company_id)) {
                            updateprintinvoice($id_pech_form);
                        }
                    } else {
                        // Цены ниже запрашиваемых. Исправьте цены в сделке и создайте счёт заново. Откат.
                        $parametr = $parametr . '&fields[stageId]=' . $inv_tec_stage . '&fields[ufCrm_SMART_INVOICE_1651509493]=' . $inv_tec_stage;
                        $flag_obnovlenie = 1;
                        if ($uf_company_id != $deal_company_id) {
                            $parametr = $parametr . '&fields[companyId]=' . $deal_company_id;
                        }
                        if ($srok_opl != $inv_srok_opl) {
                            $parametr = $parametr . '&fields[closedate]=' . $inv_srok_opl;
                        }
                        if ($paymemtTermInv != $paymemtTerm) {
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1656584515597]=' . $paymemtTerm;
                        }
                        if (($tip_opl - 116) != $inv_tip_opl) {
                            $inv_tip_opl_correct = ($inv_tip_opl + 116);
                            $parametr = $parametr . '&fields[ufCrm_SMART_INVOICE_1651114959541]=' . $inv_tip_opl_correct;
                        }
                        $products_update = products_upd($product_rows_array, $product_deal_array, $id);
                        send_message($responsible_id, 'Условия в счёте ' . $order_topic . ' хуже согласованных. Запрос с новыми условиями отправлен.');
                        // Отправить запрос
                        // $arr_check_price
                        //  $uf_company_id,$uf_deal_id,$uf_mycompany_id,ИЗ МАССИВА $id_product, $tip_opl,ИЗ МАССИВА $price
                        request_price($responsible_id, $arr_check_price, $uf_deal_id, $order_topic, $tip_opl, $srok_opl, $uf_mycompany_id, $uf_company_id, $tip_opl, $paymemtTermInv);
                    }
                }
            }
        }
        if ($flag_obnovlenie == 1) {
            //log_ftp($flag_obnovlenie.' || '.$zapros.' || '.$parametr, 'request_deal');
            zapros($zapros, $parametr);
        }
        if ($flag_obnovlenie_deal == 1) {
            //log_ftp($flag_obnovlenie_deal.' || '.$zapros_deal.' || '.$parametr_deal, 'request_deal');
            zapros($zapros_deal, $parametr_deal);
        }
    } else {
        send_message($serviceUser, 'Не получены поля сделки ' . $uf_deal_id); 
    }
} else {
    send_message($serviceUser, 'Не получены поля счёта ' . $id); 
}
$res_set = set_busy_invoice($id, 0);

function zapros($zap, $param)
{
global $bitrixPortal, $bitrixToken;

    $queryUrl = $bitrixPortal . '/rest/' . $bitrixToken . '/' . $zap;
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
        log_ftp($zap . ' // ' . $param . ' // ' . $result['error_description'], 'error');
        return array();
    } else {
        return $result;
    }
}
function log_ftp($soobch, $fil)
{
    Bitrix_help::log_ftp($soobch, $fil);
    return;
    // Запись текста в файл по ФТП
    // Установка соединения
    $conn_id = ftp_connect('bob140.beget.tech');
    $login_result = ftp_login($conn_id, 'bob140_bitrix', '911BoB140!');
    ftp_pasv($conn_id, true);
    // Создание файла на сервере
    $file1 = fopen('php://temp', 'r+');
    fwrite($file1, $soobch);
    rewind($file1);
    if (ftp_fput($conn_id, 'Bitrix/Log/' . $fil . ' ' . round(microtime(true) * 1000,
        0) . '.txt', $file1, FTP_ASCII)) {
        echo 'File create';
    } else {
        echo 'File not create';
    }
    // Закрытие соединения
    ftp_close($conn_id);
    //fclose($fp); //Закрытие файла
}
function have_right($user_tec)
{
    // Права на правку сделки
    $res_right = 0;
    if (($user_tec == '169') or ($user_tec == '645') or ($user_tec == '171') or (departuser($user_tec) == '43')) {
        // Бобкин В.; Фазылбеков И.; Ногибин В.; Бухгалтерия
        $res_right = 1;
    }

    return $res_right;
}
function send_message($id_us, $soobch)
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
function departuser($iduser)
{
    // ИД отделения пользователя
    $result1 = '_';
    $zapros = 'user.get';
    $parametr = 'id=' . $iduser;
    $res = zapros($zapros, $parametr);
    {
        if (count($res) > 0) {
            $result1 = $res['result'][0]['UF_DEPARTMENT'][0];
        }

    }
    return $result1;
}
function prmin($idproduct)
{
    // Минимальная цена по коду
    $result1 = 0;
    $zapros = 'crm.product.get';
    $parametr = 'id=' . $idproduct;
    $res = zapros($zapros, $parametr);
    {
        if (count($res) > 0) {
            $result1 = $res['result']['PROPERTY_123']['value'];
        }

        //$tu1 = substr($result1, 1, 5);
        //$yu1 = ord($tu1);
        //$tu2 = substr($tu1, 1, 4);
        //$yu2 = ord($tu2);
        //log_ftp($yu1.'|||'.$result1.'||'.$tu1.'  <<>>  '.$yu2.'|||'.$result1.'||'.$tu2, 'kod_pu');

        $result1 = str_replace(chr(194) . chr(160), '', $result1);
    }
    return $result1;
}
function firmid($idcomp)
{
    // Тек фирма (Наша) из Компании
    $result11 = '';
    $zapros = 'crm.company.get';
    $parametr = 'id=' . $idcomp;
    $res = zapros($zapros, $parametr);
    {
        if (count($res) > 0) {
            $result11 = $res['result']['UF_CRM_1631903199'];
        }

    }
    return $result11;
}
function productdeal($iddeal)
{
    // Массив товаров из сделки
    $result21 = array();
    $zapros = 'crm.deal.productrows.get';
    $parametr = 'id=' . $iddeal;
    $res = zapros($zapros, $parametr);
    {
        if (count($res) > 0) {
            $result21 = $res['result'];
        }

    }
    return $result21;
}
function payments_upd($payments1, $inv_payments1)
{
    // Обновить платёжки в счёте, если не равны со сделкой. $inv_payments1 - источник в сделке
    $payments1 = is_array($payments1) ? $payments1 : array();
    $inv_payments1 = is_array($inv_payments1) ? $inv_payments1 : array();

    $result21 = ''; // Записать обновление массива из $inv_payments1 если не пусто
    $count_inv = count($inv_payments1);
    $count_pay = count($payments1);
    if ($count_inv === 0 && $count_pay === 0) {
        return $result21;
    }

    $max = max($count_inv, $count_pay);
    for ($i = 0; $i < $max; $i++) {
        $value = $i < $count_inv ? $inv_payments1[$i] : '';
        $result21 = $result21 . '&fields[UF_CRM_1632738453][' . $i . ']=' . $value;
    }

    return $result21;
}
function products_upd($product_rows_array1, $product_deal_array1, $id1)
{
    // Если товары изменились, тогда из сделки ($product_deal_array1) в счёт (создать строку запроса, если в счёте больше - добавить пустые(пример - в создании счёта)
    return Bitrix_help::productsUpdate($product_rows_array1, $product_deal_array1, $id1);
}
function products_upd_deal($product_rows_array1, $product_deal_array1, $iddeal1)
{
    // Перегрузить товары из счёта в сделку (запрос)) 1 - есть изменения, 0 - нет
    return Bitrix_help::productsUpdatetDeal($product_rows_array1, $product_deal_array1, $iddeal1);
}
function checkprice($product_rows_array1, $product_deal_array1, $deal_check_respit1)
{
    // Проверить цены в счёте - $product_rows_array1 Первая - базовая, Вторая - если Флаг = 1 тогда не ниже из сделки.
    //log_ftp(json_encode($product_rows_array1).' :: '.json_encode($product_deal_array1), 'request');
    $soobch = count($product_rows_array1) . ' ' . count($product_deal_array1);
    $result22 = 1; // 1 - базовая проверка ОК, 0 - проверка не прошла, 2 - проверка по разрешению
    foreach ($product_rows_array1 as &$value) {
        $price = $value['PRICE'];
        $product_id = $value['PRODUCT_ID'];
        $pricemin = prmin($product_id);
        //$nok = ($price < $pricemin);
        //$soobch = $soobch.' ||| '.$price.' // '.$product_id.' / '.$pricemin.' == '.$nok;
        {
            if ($price < $pricemin) {
                if ($deal_check_respit1 == 1) {
                    $flnayden = 0;
                    foreach ($product_deal_array1 as &$value_deal) {
                        if ($product_id == $value_deal['PRODUCT_ID']) {
                            $flnayden = 1;
                            if ($price < $value_deal['PRICE']) {
                                $result22 = 0;
                            } else {
                                if ($result22 != 0) {
                                    $result22 = 2;
                                }
                            }
                        }
                    }
                    unset($value_deal); // Сбрасываем знвчение
                    if ($flnayden == 0) {
                        $result22 = 0;
                    }
                } else {
                    $result22 = 0;
                }
            }
        }
    }
    unset($value); // Сбрасываем знвчение
    //$soobch = $soobch.' ||| '.$result22;
    //log_ftp($soobch, 'check_price');
    return $result22;
}
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
function updateprintinvoice($id_pech_form1)
{
    // Обновить печатную форму счёта
    $result22 = 0; //   id; values; stampsEnabled(1/0)
    // НАПИСАТЬ
    $result1 = '_';
    $zapros5 = 'crm.documentgenerator.document.update';
    $parametr5 = 'id=' . $id_pech_form1 . '&stampsEnabled=1';
    $res = zapros($zapros5, $parametr5);
    {
        if (count($res) > 0) {
            $result22 = 1;
        }
        return $result22;
    }
}
function pr1C($idproduct)
{
    // Код товара из 1С
    $result1 = '_';
    $zapros = 'crm.product.get';
    $parametr = 'id=' . $idproduct;
    $res = zapros($zapros, $parametr);
    {
        if (count($res) > 0) {
            $result1 = $res['result']['XML_ID'];
        }
        return $result1;
    }
}
function get_busy_invoice($id_deal)
{
    $id_deal = (int)$id_deal;
    $flag_busy = false;
    $sql = 'SELECT 1 FROM invoice_busy WHERE id_invoice = ' . $id_deal . ' AND busy LIMIT 1';
    $result = Bitrix_help::request_sql($sql);
    if (is_array($result) && count($result) > 0) {
        $flag_busy = true;
    }
    return $flag_busy;
}
function set_busy_invoice($id_deal, $fl_set)
{
    $id_deal = (int)$id_deal;
    if ($fl_set == 1) {
        $sql = 'INSERT INTO invoice_busy (id_invoice, busy) VALUES (' . $id_deal . ', TRUE) '
             . 'ON CONFLICT (id_invoice) DO UPDATE SET busy = TRUE';
    } else {
        $sql = 'DELETE FROM invoice_busy WHERE id_invoice = ' . $id_deal;
    }
    return Bitrix_help::request_sql($sql);
}
function checkprice1($product_rows_array9, $product_deal_array9, $uf_company_id9, $uf_deal_id9, $uf_mycompany_id9, $tip_opl9, $paymemtTermInv9)
{   
    return Bitrix_help::checkprice($product_rows_array9, $product_deal_array9, $uf_company_id9, $uf_deal_id9, $uf_mycompany_id9, $tip_opl9, $paymemtTermInv9);
}
function request_price($id_responsible, $arrmin1, $id_sdelka1, $name_sdelka1, $tipoplstr1, $srok_oplad1, $id_firma1, $id_company1, $tipopl1, $paymemtTermInv1)
{
    Bitrix_help::requestPrice($id_responsible, $arrmin1, $id_sdelka1, $name_sdelka1, $tipoplstr1, $srok_oplad1, $id_firma1, $id_company1, $tipopl1, $paymemtTermInv1);
}
function getStorageId($idDeal)
{
    $idStorage = null;
    $parametr99 = 'entityTypeId=31' . '&filter[parentId2]=' . $idDeal . '&select[0]=ufCrm_SMART_INVOICE_1651083239729';
    $res99 = Bitrix_help::request('crm.item.list', $parametr99);
    if (count($res99) > 0) {
        $arr_invoice_old99 = $res99['result']['items'];
        if (count($arr_invoice_old99) > 0) {
            $idStorage = $arr_invoice_old99[0]['ufCrm_SMART_INVOICE_1651083239729'];
        }
    }
    return $idStorage;
}
