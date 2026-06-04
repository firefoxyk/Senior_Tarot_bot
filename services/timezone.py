from datetime import datetime
from zoneinfo import ZoneInfo


WARSAW_TZ = ZoneInfo("Europe/Warsaw")


def get_today_warsaw() -> str:
    """
    Возвращает сегодняшнюю дату в Europe/Warsaw в ISO формате (YYYY-MM-DD).
    
    Используется для синхронизации лимитов дневного действия с расписанием
    APScheduler, который работает в Europe/Warsaw.
    
    Returns:
        str: Дата в формате YYYY-MM-DD (например, "2026-06-04")
    """
    now = datetime.now(WARSAW_TZ)
    return now.date().isoformat()
