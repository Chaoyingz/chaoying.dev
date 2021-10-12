import math
import re

DEFAULT_WPM = 265  # Medium says they use 275 WPM but they actually use 265
WORD_DELIMITER = re.compile(r"\W+")


def read_time(text: str, wpm: int = DEFAULT_WPM) -> str:
    try:
        num_words = len(re.split(WORD_DELIMITER, text.strip()))
    except (AttributeError, TypeError):
        num_words = 0
    seconds = int(math.ceil(num_words / wpm * 60))
    minutes = int(math.ceil(seconds / 60))
    if minutes < 1:
        minutes = 1
    rv = f"{minutes} min read"
    return rv
