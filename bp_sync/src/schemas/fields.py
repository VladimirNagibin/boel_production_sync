from typing import Any

FIELDS_BY_TYPE: dict[str, Any] = {
    "str": [
        # deal
        "TITLE",
        "STAGE_ID",
        # lead
        "STATUS_ID",
    ],
    "str_none": [
        # deal
        "ADDITIONAL_INFO",  # "additional_info",
        "UF_CRM_1656227383",  # "printed_form_id",
        "CURRENCY_ID",  # "currency_id",
        "TYPE_ID",  # "type_id",
        "SOURCE_ID",  # "source_id",
        "UF_CRM_612463720554B",  # "lead_type_id",
        "UF_CRM_1632738354",  # "invoice_stage_id",
        "UF_CRM_1632738604",  # "current_stage_id",
        "UF_CRM_1655618110493",  # "defect_conclusion",
        "UTM_SOURCE",  # "utm_source",
        "UTM_MEDIUM",  # "utm_medium",
        "UTM_CAMPAIGN",  # "utm_campaign",
        "UTM_CONTENT",  # "utm_content",
        "UTM_TERM",  # "utm_term",
        "UF_CRM_MGO_CC_ENTRY_ID",  # "mgo_cc_entry_id",
        "UF_CRM_MGO_CC_CHANNEL_TYPE",  # "mgo_cc_channel_type",
        "UF_CRM_MGO_CC_RESULT",  # "mgo_cc_result",
        "UF_CRM_MGO_CC_ENTRY_POINT",  # "mgo_cc_entry_point",
        "UF_CRM_MGO_CC_TAG_ID",  # "mgo_cc_tag_id",
        "UF_CRM_665F0885515AE",  # "calltouch_site_id",
        "UF_CRM_665F08858FCF0",  # "calltouch_call_id",
        "UF_CRM_665F0885BB4E2",  # "calltouch_request_id",
        "UF_CRM_1739185983784",  # "yaclientid",
        "UF_CRM_63A031829F8E2",  # "wz_instagram",
        "UF_CRM_63A03182BF864",  # "wz_vc",
        "UF_CRM_63A03182D063B",  # "wz_telegram_username",
        "UF_CRM_63A03182DFB0F",  # "wz_telegram_id",
        "UF_CRM_63ABEBD42730D",  # "wz_avito",
        "COMMENTS",  # "comments",
        "SOURCE_DESCRIPTION",  # "source_description",
        "UF_CRM_DCT_SOURCE",  # "source_external",
        "ORIGINATOR_ID",  # "originator_id",
        "ORIGIN_ID",  # "origin_id",
        "UF_CRM_DCT_CITY",  # "city",
        # lead
        "NAME",  # "name:",
        "SECOND_NAME",  # "second_name:",
        "LAST_NAME",  # "last_name:",
        "POST",  # "post:",
        "COMPANY_TITLE",  # "company_title:",
        "STATUS_DESCRIPTION",  # "status_description:",
        "UF_CRM_1629271075",  # "type_id:",
        "UF_CRM_CALLTOUCHT413",  # "calltouch_site_id:",
        "UF_CRM_CALLTOUCH3ZFT",  # "calltouch_call_id:",
        "UF_CRM_CALLTOUCHWG9P",  # "calltouch_request_id:",
        "UF_CRM_1739432591418",  # "yaclientid:",
        "UF_CRM_INSTAGRAM_WZ",  # "wz_instagram:",
        "UF_CRM_VK_WZ",  # "wz_vc:",
        "UF_CRM_TELEGRAMUSERNAME_WZ",  # "wz_telegram_username:",
        "UF_CRM_TELEGRAMID_WZ",  # "wz_telegram_id:",
        "UF_CRM_AVITO_WZ",  # "wz_avito:",
        "ADDRESS",  # "address:",
        "ADDRESS_2",  # "address_2:",
        "ADDRESS_CITY",  # "address_city:",
        "ADDRESS_POSTAL_CODE",  # "address_postal_code:",
        "ADDRESS_REGION",  # "address_region:",
        "ADDRESS_PROVINCE",  # "address_province:",
        "ADDRESS_COUNTRY",  # "address_country:",
        "ADDRESS_COUNTRY_CODE",  # "address_country_code:",
        # contact
        "ORIGIN_VERSION",  # "origin_version",
        "TYPE_ID",  # "type_id",
        "UF_CRM_61236340EA7AC",  # "deal_type_id",
        "UF_CRM_63E1D6D4B8A68",  # "mgo_cc_entry_id",
        "UF_CRM_63E1D6D4C89EA",  # "mgo_cc_channel_type",
        "UF_CRM_63E1D6D4D40E8",  # "mgo_cc_result",
        "UF_CRM_63E1D6D4DFC93",  # "mgo_cc_entry_point",
        "UF_CRM_63E1D6D515198",  # "mgo_cc_tag_id",
        "UF_CRM_CALLTOUCHWWLX",  # "calltouch_site_id",
        "UF_CRM_CALLTOUCHZLRD",  # "calltouch_call_id",
        "UF_CRM_CALLTOUCHZGWC",  # "calltouch_request_id",
        # company
        "BANKING_DETAILS",  # "banking_details",
        "ADDRESS_LEGAL",  # "address_legal",
        "UF_CRM_1596031539",  # "address_company",
        "UF_CRM_1596031556",  # "province_company",
        "UF_CRM_607968CE029D8",  # "city",
        "UF_CRM_607968CE0F3A4",  # "source_external",
        "COMPANY_TYPE",  # "company_type_id",
        "UF_CRM_1637554945",  # "source_id",
        "UF_CRM_61974C16F0F71",  # "deal_type_id",
        "INDUSTRY",  # "industry_id",
        "EMPLOYEES",  # "employees_id",
        "UF_CRM_63F2F6E58EE14",  # "mgo_cc_entry_id",
        "UF_CRM_63F2F6E5A6DE8",  # "mgo_cc_channel_type",
        "UF_CRM_63F2F6E5BEAEE",  # "mgo_cc_result",
        "UF_CRM_63F2F6E5D8B28",  # "mgo_cc_entry_point",
        "UF_CRM_63F2F6E630D9C",  # "mgo_cc_tag_id",
        "UF_CRM_66618114BF72A",  # "calltouch_site_id",
        "UF_CRM_66618115024C3",  # "calltouch_call_id",
        "UF_CRM_66618115280F4",  # "calltouch_request_id",
        "UF_CRM_63F2F6E50BBDC",  # "wz_instagram",
        "UF_CRM_63F2F6E52BC88",  # "wz_vc",
        "UF_CRM_63F2F6E544CDC",  # "wz_telegram_username",
        "UF_CRM_63F2F6E5602C1",  # "wz_telegram_id",
        "UF_CRM_63F2F6E5766C6",  # "wz_avito",
        "UF_CRM_1630507939",  # "position_head",
        "UF_CRM_1630508048",  # "basis_operates",
        "UF_CRM_1632315102",  # "position_head_genitive",
        "UF_CRM_1632315157",  # "basis_operates_genitive",
        "UF_CRM_1632315337",  # "payment_delay_genitive",
        "UF_CRM_1633583719",  # "full_name_genitive",
        "UF_CRM_1623915176",  # "current_contract",
        "UF_CRM_1654683828",  # "current_number_contract",
    ],
    "int": [
        # deal
        "ID",  # "external_id",
        "CATEGORY_ID",  # "category_id" : 0, 1, 2 - funnels
        "ASSIGNED_BY_ID",  # "assigned_by_id",
        "CREATED_BY_ID",  # "created_by_id",
        "MODIFY_BY_ID",  # "modify_by_id",
    ],
    "int_none": [
        # deal
        "PROBABILITY",  # "probability",
        "UF_CRM_1656582798",  # "payment_grace_period",
        "LEAD_ID",  # "lead_id",
        "COMPANY_ID",  # "company_id",
        "CONTACT_ID",  # "contact_id",
        "UF_CRM_1598883361",  # "main_activity_id",
        "UF_CRM_1650617036",  # "shipping_company_id",
        "UF_CRM_1654577096",  # "creation_source_id",
        "UF_CRM_1659326670",  # "warehouse_id",
        "UF_CRM_652940014E9A5",  # "deal_failure_reason_id",
        "LAST_ACTIVITY_BY",  # "last_activity_by",
        "MOVED_BY_ID",  # "moved_by_id",
        "UF_CRM_1655618547",  # "defect_expert_id",
        "UF_CRM_1655891443",  # "parent_deal_id"
        # lead
        "UF_CRM_1598882174",  # "main_activity_id",
        "UF_CRM_1697036607",  # "deal_failure_reason_id",
        "ADDRESS_LOC_ADDR_ID",  # "address_loc_addr_id",
        # contact
        "UF_CRM_1598882745",  # "main_activity_id",
        "UF_CRM_6539DA9518373",  # "deal_failure_reason_id",
        # company
        "UF_CRM_1598882910",  # "main_activity_id",
        "UF_CRM_65A8D8C72059A",  # "deal_failure_reason_id",
        "UF_CRM_1631941968",  # "shipping_company_id",
        "UF_CRM_1631903199",  # "shipping_company ???",
        "UF_CRM_1623833602",  # "parent_company_id",
    ],
    "bool": [  # Y / N
        # deal
        "IS_MANUAL_OPPORTUNITY",  # "is_manual_opportunity",
        "CLOSET",  # "closed",
        "IS_NEW",  # "is_new",
        "IS_RECURRING",  # "is_recurring",
        "IS_RETURN_CUSTOMER",  # "is_return_customer",
        "IS_REPEATED_APPROACH",  # "is_repeated_approach",
        "OPENED",  # "opened",
        # lead
        "HAS_PHONE",  # "has_phone"
        "HAS_EMAIL",  # "has_email"
        "HAS_IMOL",  # "has_imol"
        # contact
        "EXPORT",  # "export",
        # company
        "IS_MY_COMPANY",  # "is_my_company",
    ],
    "bool_none": [  # 1 / 0
        # deal
        "UF_CRM_60D2AFAEB32CC",  # "is_shipment_approved",
        "UF_CRM_1632738559",  # "is_shipment_approved_invoice",
        # lead
        "UF_CRM_1623830089",  # "is_shipment_approved"
        # contact
        "UF_CRM_60D97EF75E465",  # "is_shipment_approved"
        # company
        "UF_CRM_61974C16DBFBF",  # "is_shipment_approved"
    ],
    "datetime": [
        # deal
        "DATE_CREATE",  # "date_create",
        "DATE_MODIFY",  # "date_modify",
        "BEGINDATE",  # "begindate",
        "CLOSEDATE",  # "closedate",
    ],
    "datetime_none": [
        # deal
        "LAST_ACTIVITY_TIME",  # "last_activity_time",
        "LAST_COMMUNICATION_TIME",  # "last_communication_time",
        "MOVED_TIME",  # "moved_time",
        "UF_CRM_1632738230",  # "payment_deadline",
        "UF_CRM_MGO_CC_CREATE",  # "mgo_cc_create",
        "UF_CRM_MGO_CC_END",  # "mgo_cc_end",
        # lead
        "BIRTHDATE",  # "birthdate"
        "DATE_CLOSED",  # "date_closed"
        # contact
        "UF_CRM_63E1D6D4EC444",  # "mgo_cc_create",
        "UF_CRM_63E1D6D5051DE",  # "mgo_cc_end",
        # company
        "UF_CRM_63F2F6E5F1691",  # "mgo_cc_create",
        "UF_CRM_63F2F6E6181EE",  # "mgo_cc_end",
        "UF_CRM_1623835088",  # "date_last_shipment",
    ],
    "float": [
        # deal
        "OPPORTUNITY",  # "opportunity",
        # company
        "REVENUE",  # "revenue",
    ],
    "enums": [
        # deal
        "STAGE_SEMANTIC_ID",  # "stage_semantic_id",
        "UF_CRM_1632738315",  # "payment_type",
        "UF_CRM_1655141630",  # "shipping_type",
        "UF_CRM_1750571370",  # "processing_status",
        # lead
        "STATUS_SEMANTIC_ID",  # "status_semantic_id",
    ],
    "list": [
        # deal
        "UF_CRM_1655615996118",  # "defects",
        "UF_CRM_1658467259",  # "related_deals",
        # lead
        "PHONE",  # "phone",
        "EMAIL",  # "email",
        "WEB",  # "web",
        "IM",  # "im",
        "LINK",  # "link",
        # contact
        "UF_CRM_1629106625",  # "additional_responsables",
        # company
        "UF_CRM_1629106458",  # "additional_responsables",
        "UF_CRM_1623833623",  # "contracts"
    ],
}
