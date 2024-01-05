import asyncio
import json
import logging
import re
from pathlib import Path
from typing import List

from uploader.utils.config import config

logger = logging.getLogger("md_uploader")


FILE_NAME_REGEX = re.compile(
    r"^(?:\[(?P<artist>.+?)?\])?\s?"  # Artist
    r"(?P<title>.+?)"  # Manga title
    r"(?:\s?\[(?P<language>[a-z]{2}(?:-[a-z]{2})?|[a-zA-Z]{3}|[a-zA-Z]+)?\])?\s-\s"  # Language
    r"(?P<prefix>(?:[c](?:h(?:a?p?(?:ter)?)?)?\.?\s?))?(?P<chapter>\d+(?:\.\d)?)"  # Chapter number and prefix
    r"(?:\s?\((?:[v](?:ol(?:ume)?(?:s)?)?\.?\s?)?(?P<volume>\d+(?:\.\d)?)?\))?"  # Volume number
    r"(?:\s?\((?P<chapter_title>.+)\))?"  # Chapter title
    r"(?:\s?\{(?P<publish_date>(?P<publish_year>\d{4})-(?P<publish_month>\d{2})-(?P<publish_day>\d{2})(?:[T\s](?P<publish_hour>\d{2})[\:\-](?P<publish_minute>\d{2})(?:[\:\-](?P<publish_microsecond>\d{2}))?(?:(?P<publish_offset>[+-])(?P<publish_timezone>\d{2}[\:\-]?\d{2}))?)?)\})?"  # Publish date
    r"(?:\s?\[(?:(?P<group>.+))?\])?"  # Groups
    r"(?:\s?\{v?(?P<version>\d)?\})?"  # Chapter version
    r"(?:\.(?P<extension>zip|cbz))?$",  # File extension
    re.IGNORECASE,
)

UUID_REGEX = re.compile(
    r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
    re.IGNORECASE,
)


def open_manga_series_map(files_path: "Path") -> "dict":
    """Get the manga-name-to-id map."""
    try:
        with open(
            files_path.joinpath(config["paths"]["name_id_map_file"]),
            "r",
            encoding="utf-8",
        ) as json_file:
            names_to_ids = json.load(json_file)
    except FileNotFoundError:
        not_found_error = f"The manga name-to-id json file couldn't be found. Continuing with an empty name-id map."
        logger.error(not_found_error)
        print(not_found_error)
        return {"manga": {}, "group": {}}
    except json.JSONDecodeError:
        corrupted_error = f"The manga name-to-id json file is corrupted. Continuing with an empty name-id map."
        logger.error(corrupted_error)
        print(corrupted_error)
        return {"manga": {}, "group": {}}
    return names_to_ids


def flatten(t: "List[list]") -> "list":
    """Flatten nested lists into one list."""
    return [item for sublist in t for item in sublist]


def create_new_event_loop():
    """Return the event loop, create one if not there is not one running."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError as e:
        if str(e).startswith("There is no current event loop in thread"):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
        else:
            raise
