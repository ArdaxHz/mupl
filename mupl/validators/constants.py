"""Constants used across the validation modules."""

WINDOWS_ILLEGAL_CHAR_MAP = {
    "{backslash}": "\\",
    "{slash}": "/",
    "{colon}": ":",
    "{asterisk}": "*",
    "{question_mark}": "?",
    "{quote}": '"',
    "{less_than}": "<",
    "{greater_than}": ">",
    "{pipe}": "|",
}

MIN_IMAGE_SIZE = 128
MAX_IMAGE_PIXELS = None

DEFAULT_IMAGES_UPLOAD_COUNT = 10
DEFAULT_UPLOAD_RETRY = 3
DEFAULT_RATELIMIT_TIME = 2

DEFAULT_MAX_LOG_DAYS = 30
