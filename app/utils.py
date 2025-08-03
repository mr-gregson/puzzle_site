from datetime import datetime, timezone

def compare_dates(date1, date2):
    if date1 and date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2 and date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    return date1 < date2