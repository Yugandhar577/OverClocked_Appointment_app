from datetime import date, timedelta


def expand_recurrence(start: date, recurrence_type: str, occurrences: int, interval: int = 1) -> list[date]:
    if occurrences <= 0:
        return []
    if interval <= 0:
        raise ValueError("interval must be positive")
    dates: list[date] = []
    current = start
    for _ in range(min(occurrences, 120)):
        dates.append(current)
        if recurrence_type == "weekly":
            current = current + timedelta(days=7 * interval)
        elif recurrence_type == "monthly":
            month = current.month - 1 + interval
            year = current.year + month // 12
            month = month % 12 + 1
            day = min(current.day, 28)
            current = date(year, month, day)
        else:
            current = current + timedelta(days=interval)
    return dates
