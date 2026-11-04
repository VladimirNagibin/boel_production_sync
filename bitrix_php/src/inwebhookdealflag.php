<?php
include 'main_function.php';

$id = $_REQUEST['ID_DEAL'];
$nm = $_REQUEST['ID_NM']; // 1 - цены разрешены, 0 - запрещены
$srock = $_REQUEST['SROCK'];
$tipoplstr = $_REQUEST['TIP'];

$text_request = $_REQUEST['ZAPROS']; 
$tipopl = $_REQUEST['TIP_NUMBER'];
$firm = $_REQUEST['FIRM'];
$company = $_REQUEST['COMPA'];
$paymemtTerm = $_REQUEST['PAYMENT_TERM'];

//Bitrix_help::send_message(215,$id.' :: '.$nm.' :: '.$srock.' :: '.$tipoplstr.' :: '.$tipopl.' :: '.$firm.' :: '.$company);
//Bitrix_help::send_message(215,$text_request); 

//Bitrix_help::send_message(215, $id);
//Bitrix_help::send_message(215, $text_request);
//Bitrix_help::send_message(215, $tipopl);
//Bitrix_help::send_message(215, $firm);
//Bitrix_help::send_message(215, $company);
/*
$nm = 1;
$id = 2597;
$text_request = 'Цена |Цена мин |Кол-во |Товар__                    1050    |1180            |3 |Промывочный щелочной промышленный очиститель "GG5" Средство для внутренней мойки 13кг.|869__                    2000    |2250            |1 |Балка 2, нерж ф88,9, по itap и пегас|75'; 
$tipopl = 495; 
$firm = 8923;
$company = 8939;
*/
//Bitrix_help::send_message(215, $text_request);
if ($nm == 1){
if (mb_strpos($text_request,'__')>0){
   $arr_str = explode('__', $text_request);
}else{
   $arr_str = explode('_', $text_request);  
}
//Bitrix_help::send_message(215, $text_request); 
foreach ($arr_str as &$value) {
   $tec_tov = trim($value);
   if ($tec_tov!='Цена |Цена мин |Кол-во |Товар'){
      $arr_tov = explode('|', $tec_tov);
      $price_request = trim($arr_tov[0]);
      $id_product = trim($arr_tov[4]);
      $ress = Bitrix_help::check_permission($company,$id,$firm,$id_product,$tipopl,$price_request,$paymemtTerm);
      if ($ress){
         //echo  'OK '.trim($arr_tov[4]).' :: '.$price_request.'</br>'; 
      }else{
         //echo  'NO '.trim($arr_tov[4]).' :: '.$price_request.'</br>';   
         $sql1 = 'DELETE FROM price_permisson WHERE id_company = '.$company.' AND id_firm = '.$firm.' AND id_product = '.$id_product.' AND payment_type = '.$tipopl;
         //Bitrix_help::send_message(215, $sql1);    
         Bitrix_help::request_sql($sql1); 
         $sql = 'INSERT INTO price_permisson (id_company, id_deal, id_firm, id_product, payment_type, price, payment_term) VALUES ('.$company.', '.$id.', '.$firm.', '.$id_product.', '.$tipopl.', '.$price_request.', '.$paymemtTerm.')';
         //Bitrix_help::send_message(215, $sql);     
         Bitrix_help::request_sql($sql);
      }
   }
}
unset($value); 
} 
?>