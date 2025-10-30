from datetime import date, datetime, timedelta


class DateService:
    """Сервис для работы с датами"""

    @staticmethod
    def _normalize_date(dt: datetime) -> date:
        """Приводит datetime к date, игнорируя время"""
        return dt.date()

    @staticmethod
    def _is_weekend(date: date) -> bool:
        """Проверяет, является ли день выходным"""
        return date.weekday() >= 5  # 5 = суббота, 6 = воскресенье

    @staticmethod
    def add_working_days(start_date: datetime, working_days: int) -> datetime:
        """Добавляет указанное количество рабочих дней к дате"""
        current_date = DateService._normalize_date(start_date)
        days_added = 0

        while days_added < working_days:
            current_date += timedelta(days=1)
            if not DateService._is_weekend(current_date):
                days_added += 1
        # Возвращаем datetime с временем 00:00:00
        return datetime.combine(current_date, datetime.min.time())

    @staticmethod
    def get_working_days_diff(start_date: datetime, end_date: datetime) -> int:
        """Вычисляет разницу в рабочих днях между двумя датами"""
        start = DateService._normalize_date(start_date)
        end = DateService._normalize_date(end_date)

        if start > end:
            return 0

        current_date = start
        working_days = 0

        while current_date < end:
            if not DateService._is_weekend(current_date):
                working_days += 1
            current_date += timedelta(days=1)

        return working_days

    @staticmethod
    def get_calendar_days_diff(
        start_date: datetime, end_date: datetime
    ) -> int:
        """
        Вычисляет разницу в календарных днях между двумя датами
        (без учета времени)
        """
        start = DateService._normalize_date(start_date)
        end = DateService._normalize_date(end_date)

        if start > end:
            return 0

        return (end - start).days
