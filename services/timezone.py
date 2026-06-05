from datetime import datetime
from zoneinfo import ZoneInfo


MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def get_today_moscow() -> str:
    now = datetime.now(MOSCOW_TZ)
    return now.date().isoformat()
