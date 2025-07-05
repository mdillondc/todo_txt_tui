import re
from datetime import datetime


def debug(text):
    with open("debug.txt", "a") as debug_file:
        debug_file.write(f"{text}\n")


def is_valid_date(string):
    # First check if format is exactly YYYY-MM-DD (strict 2-digit month/day)
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', string):
        return False

    try:
        datetime.strptime(string, '%Y-%m-%d')
        return True
    except ValueError:
        return False