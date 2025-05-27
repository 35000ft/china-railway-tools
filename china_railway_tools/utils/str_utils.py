import re
from datetime import datetime


def is_not_blank(input_string) -> bool:
    return bool(input_string and isinstance(input_string, str) and input_string.strip())


def is_blank(input_string) -> bool:
    return not is_not_blank(input_string)


def hhmm_to_datetime(hhmm: str) -> datetime:
    if not isinstance(hhmm, str):
        raise TypeError('hhmm must be a string')
    time_format = "%H:%M"
    hhmm = hhmm.strip()
    fake_date = "2025-01-01"
    accepted_pattern = r'^\d{2}:?\d{2}$'
    if re.match(pattern=accepted_pattern, string=hhmm):
        if ':' not in hhmm:
            time_format = "%H%M"
        return datetime.strptime(f"{fake_date} {hhmm}", f"%Y-%m-%d {time_format}")
    else:
        raise ValueError('hhmm must be in format hh:mm, like 19:00 or 0700')
