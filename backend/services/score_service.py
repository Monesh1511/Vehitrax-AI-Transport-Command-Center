from datetime import datetime, time


COLLEGE_START_TIME = time(9, 0)
COLLEGE_END_TIME = time(16, 10)


def calculate_punctuality(event_timestamp: datetime):
    """Classify bus arrival/departure and compute score by college timings.

    Rules:
    - Before or at 09:00 -> Enter (on-time / early)
    - After 09:00 up to 16:10 -> Delayed
    - After 16:10 -> Exit
    """
    t = event_timestamp.time()

    if t <= COLLEGE_START_TIME:
        early_seconds = (
            datetime.combine(event_timestamp.date(), COLLEGE_START_TIME)
            - datetime.combine(event_timestamp.date(), t)
        ).total_seconds()
        early_minutes = int(max(0, early_seconds // 60))
        score = min(100, 95 + (early_minutes // 10))
        return {
            "status": "Enter",
            "event_type": "Enter",
            "score": score,
            "early_minutes": early_minutes,
            "late_minutes": 0,
        }

    if t > COLLEGE_END_TIME:
        return {
            "status": "Exit",
            "event_type": "Exit",
            "score": 100,
            "early_minutes": 0,
            "late_minutes": 0,
        }

    late_seconds = (
        datetime.combine(event_timestamp.date(), t)
        - datetime.combine(event_timestamp.date(), COLLEGE_START_TIME)
    ).total_seconds()
    late_minutes = int(max(0, late_seconds // 60))
    score = max(0, 95 - late_minutes)
    return {
        "status": "Delayed",
        "event_type": "Delayed",
        "score": score,
        "early_minutes": 0,
        "late_minutes": late_minutes,
    }
