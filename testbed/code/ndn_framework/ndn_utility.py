from datetime import datetime, timedelta
from random import randint

def get_datetime() -> datetime:
        time_stamp = datetime.now().timestamp()
        date_time = datetime.fromtimestamp(time_stamp)
        return date_time

def get_time_diff(start: datetime, finish: datetime) -> float:
        if type(start) is not datetime or type(finish) is not datetime:
                return "N/A"
        diff: timedelta = finish - start
        return diff.total_seconds()

def print_time_message(message: str) -> None:
        time = get_datetime()
        print(f"[{time.time()}]: {message}", flush=True)

def generate_random(iters: int) -> int:
        base: int = 0
        date: datetime = get_datetime()
        for item in [date.time().microsecond, date.time().second, date.time().minute, date.time().hour, date.day, date.month, date.year]:
                base += item if base == 0 else item * (10**(len(str(base))))
        for _ in range(iters):
                base /= randint(1, len(str(base)))
                base *= randint(1, len(str(base)))
        return int(base)
