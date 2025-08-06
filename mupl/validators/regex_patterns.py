"""Regex patterns for file validation."""

import re

FILE_NAME_REGEX = re.compile(
    r"^(?:\[(?P<artist>.+?)?\])?\s?"  # Artist
    r"(?P<title>.+?)"  # Manga title
    r"(?:\s?\[(?P<language>[a-z]{2}(?:-[a-z]{2})?|[a-zA-Z]{3}|[a-zA-Z]+)?\])?\s-\s"  # Language
    r"(?P<prefix>(?:[c](?:h(?:a?p?(?:ter)?)?)?\.?\s?))?(?P<chapter>\d+(?:\.\d+)?)"  # Chapter number and prefix
    r"(?:\s?\((?:[v](?:ol(?:ume)?(?:s)?)?\.?\s?)?(?P<volume>\d+(?:\.\d+)?)?\))?"  # Volume number
    r"(?:\s?\((?P<chapter_title>.+)?\))?"  # Chapter title
    r"(?:\s?\{(?P<publish_date>(?P<publish_year>\d{4})-(?P<publish_month>\d{2})-(?P<publish_day>\d{2})(?:[T\s](?P<publish_hour>\d{2})[\:\-](?P<publish_minute>\d{2})(?:[\:\-](?P<publish_microsecond>\d{2}))?(?:(?P<publish_offset>[+-])(?P<publish_timezone>\d{2}[\:\-]?\d{2}))?)?)?\})?"  # Publish date
    r"(?:\s?\[(?:(?P<group>.+))?\])?"  # Groups
    r"(?:\s?\{v?(?P<version>\d)?\})?"  # Chapter version
    r"(?:\.(?P<extension>zip|cbz))?$",  # File extension
    re.IGNORECASE,
)

UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
    re.IGNORECASE,
)
