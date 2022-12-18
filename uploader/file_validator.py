import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from . import config
from .utils import languages

logger = logging.getLogger("md_uploader")

FILE_NAME_REGEX = re.compile(
    r"^(?:\[(?P<artist>.+?)?\])?\s?"  # Artist
    r"(?P<title>.+?)"  # Manga title
    r"(?:\s?\[(?P<language>[a-z]{2}(?:-[a-z]{2})?|[a-zA-Z]{3}|[a-zA-Z]+)?\])?\s-\s"  # Language
    r"(?P<prefix>(?:[c](?:h(?:a?p?(?:ter)?)?)?\.?\s?))?(?P<chapter>\d+(?:\.\d)?)"  # Chapter number and prefix
    r"(?:\s?\((?:[v](?:ol(?:ume)?(?:s)?)?\.?\s?)?(?P<volume>\d+(?:\.\d)?)?\))?"  # Volume number
    r"(?:\s?\((?P<chapter_title>.+)\))?"  # Chapter title
    r"(?:\s?\{(?P<publish_date>\d{4}-[0-1]\d-(?:[0-2]\d|3[0-1]))\})?"  # Publish date
    r"(?:\s?\[(?:(?P<group>.+))?\])?"  # Groups
    r"(?:\s?\{v?(?P<version>\d)?\})?"  # Chapter version
    r"(?:\.(?P<extension>zip|cbz))?$",  # File extension
    re.IGNORECASE,
)


class FileProcesser:
    def __init__(self, to_upload: "Path", names_to_ids: "dict") -> None:
        self.to_upload = to_upload
        self.zip_name = self.to_upload.name
        self.zip_extension = self.to_upload.suffix
        self._names_to_ids = names_to_ids
        self._uuid_regex = re.compile(
            r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
            re.IGNORECASE,
        )
        self._file_name_regex = FILE_NAME_REGEX
        self.oneshot = False

        self._zip_name_match = None
        self.manga_series = None
        self.language = None
        self.chapter_number = None
        self.volume_number = None
        self.groups = None
        self.chapter_title = None
        self.publish_date = None

    def _match_file_name(self) -> "Optional[re.Match[str]]":
        """Check for a full regex match of the file."""
        zip_name_match = self._file_name_regex.match(self.zip_name)
        if not zip_name_match:
            logger.error(f"{self.zip_name} isn't in the correct naming format.")
            print(f"{self.zip_name} not in the correct naming format, skipping.")
            return
        return zip_name_match

    def _get_manga_series(self) -> "Optional[str]":
        """Get the series title, can be a name or uuid,
        use the id map if zip file doesn't have the uuid already."""
        manga_series = self._zip_name_match.group("title")
        if manga_series is not None:
            manga_series = manga_series.strip()
            if not self._uuid_regex.match(manga_series):
                try:
                    manga_series = self._names_to_ids["manga"].get(manga_series, None)
                except KeyError:
                    manga_series = None

        if manga_series is None:
            logger.warning(f"No manga id found for {manga_series}.")
        return manga_series

    def _get_language(self) -> "str":
        """Convert the language specified into the format MangaDex uses (ISO 639-2)."""
        language = self._zip_name_match.group("language")

        # Language is missing in file, upload as English
        if language is None:
            return "en"

        language = language.strip()

        if language.lower() in ("eng", "en"):
            return "en"
        elif len(language) < 2:
            logger.warning(f"Language selected, {language} isn't in ISO format.")
            print("Not a valid language option.")
            return "null"
        # Chapter language already in correct format for MD
        elif re.match(r"^[a-z]{2}(?:-[a-z]{2})?$", language):
            logger.info(f"Language {language} already in ISO-639-2 form.")
            return language
        # Language in iso-639-3 format already
        elif len(language) == 3:
            available_langs = [
                l["two_letter"] for l in languages if l["three_letter"] == language
            ]

            if available_langs:
                return available_langs[0]
            return "null"
        else:
            # Language is a word instead of code, look for language and use that code
            languages_match = [
                l for l in languages if language.lower() in l["name"].lower()
            ]

            if len(languages_match) > 1:
                print(
                    "Found multiple matching languages, please choose the language you want to download from the following options."
                )

                for count, item in enumerate(languages_match, start=1):
                    print(f'{count}: {item["name"]}')

                try:
                    lang = int(
                        input(
                            f"Choose a number matching the position of the language: "
                        ).strip()
                    )
                except ValueError:
                    logger.warning(
                        "Language option selected is not a number, using null as language."
                    )
                    print("That's not a number.")
                    return "null"

                if lang not in range(1, (len(languages_match) + 1)):
                    logger.warning(
                        "Language option selected is not in the accepted range."
                    )
                    print("Not a valid language option.")
                    return "null"

                lang_to_use = languages_match[(lang - 1)]
                return lang_to_use["two_letter"]
            return languages_match[0]["two_letter"]

    def _get_chapter_number(self) -> "Optional[str]":
        """Get the chapter number from the file,
        use None for the number if the chapter is a prefix."""
        chapter_number = self._zip_name_match.group("chapter")
        if chapter_number is not None:
            chapter_number = chapter_number.strip()
            # Split the chapter number to remove the zeropad
            parts = re.split(r"\.|\-|\,", chapter_number)
            # Re-add 0 if the after removing the 0 the string length is 0
            parts[0] = "0" if len(parts[0].lstrip("0")) == 0 else parts[0].lstrip("0")

            chapter_number = ".".join(parts)

        # Chapter is a oneshot
        if self._zip_name_match.group("prefix") is None:
            chapter_number = None
            self.oneshot = True
            logger.info("No chapter number prefix found, uploading as oneshot.")
        return chapter_number

    def _get_volume_number(self) -> "Optional[str]":
        """Get the volume number from the file if it exists."""
        volume_number = self._zip_name_match.group("volume")
        if volume_number is not None:
            volume_number = volume_number.strip().lstrip("0")
            # Volume 0, re-add 0
            if len(volume_number) == 0:
                volume_number = "0"
        return volume_number

    def _get_chapter_title(self) -> "Optional[str]":
        """Get the chapter title from the file if it exists."""
        chapter_title = self._zip_name_match.group("chapter_title")
        if chapter_title is not None:
            # Add the question mark back to the chapter title
            chapter_title = chapter_title.strip().replace(r"{question_mark}", "?")
        return chapter_title

    def _get_publish_date(self) -> "Optional[str]":
        """Get the chapter publish date."""
        publish_date = self._zip_name_match.group("publish_date")
        if publish_date is not None:
            publish_date = publish_date.strip()
            if datetime.fromisoformat(
                    f"{publish_date}T00:00:00"
            ) > datetime.now() + timedelta(weeks=2):
                publish_date_over_2_weeks_error = f"Chosen publish date is over 2 weeks, this might cause an error with the Mangadex API."
                logger.warning(publish_date_over_2_weeks_error)
                print(publish_date_over_2_weeks_error)

            if datetime.fromisoformat(f"{publish_date}T00:00:00") < datetime.now():
                publish_date_before_current_error = f"Chosen publish date is before the current date, not setting a publish date."
                logger.warning(publish_date_before_current_error)
                print(publish_date_before_current_error)
                publish_date = None
        return publish_date

    def _get_groups(self) -> "List[str]":
        """Get the group ids from the file, use the group fallback if the file has no gorups."""
        groups = []
        groups_match = self._zip_name_match.group("group")
        if groups_match is not None:
            # Split the zip name groups into an array and remove any leading/trailing whitespace
            groups_array = groups_match.split("+")
            groups_array = [g.strip() for g in groups_array]

            # Check if the groups are using uuids, if not, use the id map for the id
            for group in groups_array:
                if not self._uuid_regex.match(group):
                    try:
                        group_id = self._names_to_ids["group"].get(group, None)
                    except KeyError:
                        logger.warning(
                            f"No group id found for {group}, not tagging the upload with this group."
                        )
                        group_id = None
                    if group_id is not None:
                        groups.append(group_id)
                else:
                    groups.append(group)

        if not groups:
            logger.warning("Zip groups array is empty, using group fallback.")
            print(f"No groups found, using group fallback.")
            groups = (
                []
                if config["User Set"]["group_fallback_id"] == ""
                else [config["User Set"]["group_fallback_id"]]
            )
            if not groups:
                logger.warning("Group fallback not found, uploading without a group.")
                print("Group fallback not found, uploading without a group.")
        return groups

    def process_zip_name(self) -> "bool":
        """Extract the respective chapter data from the file name."""
        self._zip_name_match = self._match_file_name()
        if self._zip_name_match is None:
            logger.error(f"No values processed from {self.to_upload}, skipping.")
            return False

        self.manga_series = self._get_manga_series()

        if self.manga_series is None:
            logger.error(f"Couldn't find a manga id for {self.zip_name}, skipping.")
            print(f"Skipped {self.zip_name}, no manga id found.")
            return False

        self.language = self._get_language()
        self.chapter_number = self._get_chapter_number()
        self.volume_number = self._get_volume_number()
        self.groups = self._get_groups()
        self.chapter_title = self._get_chapter_title()
        self.publish_date = self._get_publish_date()

        return True

    @property
    def zip_name_match(self):
        return self._zip_name_match
