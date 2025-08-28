import re
from datetime import datetime


def parse_contract_info(contract_string: str) -> dict[str, str | None]:
    """
    Разбирает строку с информацией о договоре на составляющие части.

    Args:
        contract_string: строка с информацией о договоре
        for example: "Фирма: Торговый дом СР , вид договора: С покупателем,
                      //Договор № 18/078 от 23.03.2021//, срок действия"
    Returns:
        Словарь с извлеченными данными:
        - firm: название фирмы
        - contract_type: вид договора
        - contract_info: представление договора - номер и дата
        - contract_number: номер договора
        - contract_date: дата договора в формате DD.MM.YYYY
        - contract_term: срок действия договора
    """
    result: dict[str, str | None] = {
        "firm": None,
        "contract_type": None,
        "contract_info": None,
        "contract_number": None,
        "contract_date": None,
        "contract_term": None,
    }

    try:
        # Извлекаем фирму
        firm_match = re.search(r"Фирма:\s*([^,]+)", contract_string)
        if firm_match:
            result["firm"] = firm_match.group(1).strip()

        # Извлекаем вид договора
        contract_type_match = re.search(
            r"вид договора:\s*([^,]+)", contract_string
        )
        if contract_type_match:
            result["contract_type"] = contract_type_match.group(1).strip()

        # Извлекаем информацию о договоре (номер и дату)
        contract_info_match = re.search(r"//([^/]+)//", contract_string)
        if contract_info_match:
            contract_info = contract_info_match.group(1).strip()
            result["contract_info"] = contract_info
            # Извлекаем номер договора
            number_match = re.search(
                r"Договор\s*[№N]?\s*([\d/]+)", contract_info
            )
            if number_match:
                result["contract_number"] = number_match.group(1).strip()

            # Извлекаем дату договора
            date_match = re.search(
                r"от\s*(\d{2}\.\d{2}\.\d{4})", contract_info
            )
            if date_match:
                contract_date = date_match.group(1).strip()

                # Проверяем валидность даты
                try:
                    datetime.strptime(contract_date, "%d.%m.%Y")
                    result["contract_date"] = contract_date
                except ValueError:
                    result["contract_date"] = None

        # Извлекаем срок действия
        term_match = re.search(r"срок действия\s*([^,]+)?$", contract_string)
        if term_match and term_match.group(1):
            result["contract_term"] = term_match.group(1).strip()

    except Exception as e:
        # Логирование ошибки при необходимости
        print(f"Ошибка при разборе строки: {e}")

    return result
