"""File processing and validation module."""

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict

from .regex_patterns import FILE_NAME_REGEX, UUID_REGEX
from .constants import WINDOWS_ILLEGAL_CHAR_MAP, DEFAULT_IMAGES_UPLOAD_COUNT

logger = logging.getLogger("mupl")


class FileProcessor:
    """Processes and validates manga chapter files."""

    def __init__(
        self,
        to_upload: Path,
        names_to_ids: dict,
        translation: Dict,
        group_fallback_id: Optional[str] = None,
        number_of_images_upload: int = DEFAULT_IMAGES_UPLOAD_COUNT,
        widestrip: bool = False,
        combine: bool = False,
        **kwargs,
    ) -> None:
        """Initialize the FileProcessor.

        Args:
            to_upload: Path to the file to upload
            names_to_ids: Mapping of manga names to IDs
            translation: Translation dictionary
            group_fallback_id: Fallback group ID if none found
            number_of_images_upload: Number of images to upload at once
            widestrip: Whether to use widestrip mode
            combine: Whether to combine small images
        """
        self.to_upload = to_upload
        self.names_to_ids = names_to_ids
        self.translation = translation
        self.group_fallback_id = group_fallback_id
        self.number_of_images_upload = number_of_images_upload
        self.widestrip = widestrip
        self.combine = combine

        self._match = self._match_file_name()
        self.manga_series = self._get_manga_series()
        self.language = self._get_language()
        self.chapter_number = self._get_chapter_number()
        self.volume_number = self._get_volume_number()
        self.chapter_title = self._get_chapter_title()
        self.publish_date = self._get_publish_date()
        self.groups = self._get_groups()

    def _match_file_name(self) -> Optional["re.Match[str]"]:
        """Match the file name against the regex pattern."""
        if not self.to_upload:
            return None
        return FILE_NAME_REGEX.match(self.to_upload.name)

    def _get_manga_series(self) -> Optional[str]:
        """Extract manga series from the file name."""
        if not self._match:
            return None

        manga_series = self._match.group("title")
        if manga_series is not None:
            manga_series = manga_series.strip()
            if not UUID_REGEX.match(manga_series):
                try:
                    manga_series = self.names_to_ids.get("manga", {}).get(
                        manga_series, None
                    )
                except KeyError:
                    manga_series = None

        if manga_series is None:
            logger.warning(f"No manga id found for {manga_series}.")
        return manga_series

    def _get_language(self) -> str:
        """Extract language from the file name."""
        if not self._match:
            return "en"

        language = self._match.group("language")
        if not language:
            return "en"

        return str(language).strip().lower()

    def _get_chapter_number(self) -> Optional[str]:
        """Extract chapter number from the file name."""
        if not self._match:
            return None

        chapter_number = self._match.group("chapter")
        if chapter_number is not None:
            chapter_number = chapter_number.strip()
            # Split the chapter number to remove the zeropad
            parts = re.split(r"\.|\-|\,", chapter_number)
            # Re-add 0 if the after removing the 0 the string length is 0
            parts[0] = "0" if len(parts[0].lstrip("0")) == 0 else parts[0].lstrip("0")

            chapter_number = ".".join(parts)

        # Chapter is a oneshot
        if self._match.group("prefix") is None:
            chapter_number = None
            self.oneshot = True
            logger.info("No chapter number prefix found, uploading as oneshot.")
        return chapter_number

    def _get_volume_number(self) -> Optional[str]:
        """Extract volume number from the file name."""
        if not self._match:
            return None

        volume_number = self._match.group("volume")
        if volume_number is not None:
            volume_number = volume_number.strip().lstrip("0")
            # Volume 0, re-add 0
            if len(volume_number) == 0:
                volume_number = "0"
        return volume_number

    def _get_chapter_title(self) -> Optional[str]:
        """Extract chapter title from the file name."""
        if not self._match:
            return None

        chapter_title = self._match.group("chapter_title")
        if chapter_title is not None:
            chapter_title = chapter_title.strip()
            # Replace illegal characters in the chapter title
            for placeholder, char in WINDOWS_ILLEGAL_CHAR_MAP.items():
                chapter_title = chapter_title.replace(placeholder, char)
        return chapter_title

    def _get_publish_date(self) -> Optional[str]:
        """Extract and validate publish date from the file name."""
        if not self._match:
            return None

        publish_date = self._match.group("publish_date")
        if publish_date is None:
            return

        publish_year = self._match.group("publish_year")
        publish_month = self._match.group("publish_month")
        publish_day = self._match.group("publish_day")
        publish_hour = self._match.group("publish_hour")
        publish_minute = self._match.group("publish_minute")
        publish_microsecond = self._match.group("publish_microsecond")
        publish_offset = self._match.group("publish_offset")
        publish_timezone = self._match.group("publish_timezone")

        if publish_timezone is not None:
            publish_timezone = re.sub(r"[-:]", "", publish_timezone)

        try:
            publish_year = int(publish_year)
        except (ValueError, TypeError):
            publish_year = None
        try:
            publish_month = int(publish_month)
        except (ValueError, TypeError):
            publish_month = None
        try:
            publish_day = int(publish_day)
        except (ValueError, TypeError):
            publish_day = None
        try:
            publish_hour = int(publish_hour)
        except (ValueError, TypeError):
            publish_hour = 0
        try:
            publish_minute = int(publish_minute)
        except (ValueError, TypeError):
            publish_minute = 0
        try:
            publish_microsecond = int(publish_microsecond)
        except (ValueError, TypeError):
            publish_microsecond = 0

        publish_date = datetime(
            year=publish_year,
            month=publish_month,
            day=publish_day,
            hour=publish_hour,
            minute=publish_minute,
            microsecond=publish_microsecond,
        ).isoformat()

        if publish_timezone is not None:
            publish_date += f"{publish_offset}{publish_timezone}"

        publish_date = datetime.fromisoformat(publish_date).astimezone(tz=timezone.utc)

        if publish_date > datetime.now(tz=timezone.utc) + timedelta(weeks=2):
            logger.warning(
                "Chosen publish date is over 2 weeks, this might cause an error with the Mangadex API."
            )

        if publish_date < datetime.now(tz=timezone.utc):
            logger.warning(
                "Chosen publish date is before the current date, not setting a publish date."
            )
            publish_date = None
        return publish_date

    def _get_groups(self) -> List[str]:
        """Extract group IDs from the file name."""
        if not self._match:
            return [self.group_fallback_id] if self.group_fallback_id else []

        groups = []
        groups_match = self._match.group("group")
        if groups_match is not None:
            # Split the zip name groups into an array and remove any leading/trailing whitespace
            groups_array = groups_match.split("+")
            groups_array = [g.strip() for g in groups_array]

            # Check if the groups are using uuids, if not, use the id map for the id
            for group in groups_array:
                if not UUID_REGEX.match(group):
                    try:
                        group_id = self.names_to_ids.get("group", {}).get(group, None)
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
            groups = [] if not self.group_fallback_id else [self.group_fallback_id]
        return groups

    def metadata(self) -> Dict:
        """Get all chapter metadata as a dictionary."""
        return {
            "manga_series": self.manga_series,
            "language": self.language,
            "chapter_number": self.chapter_number,
            "volume_number": self.volume_number,
            "chapter_title": self.chapter_title,
            "publish_date": self.publish_date,
            "groups": self.groups,
        }

    def update_metadata(self, **metadata_updates) -> bool:
        """Update specific metadata fields."""
        valid_fields = {
            "manga_series",
            "language",
            "chapter_number",
            "volume_number",
            "chapter_title",
            "publish_date",
            "groups",
        }

        updated = False
        for field, value in metadata_updates.items():
            if field in valid_fields and hasattr(self, field):
                setattr(self, field, value)
                updated = True
            else:
                logger.warning(f"Invalid metadata field: {field}")

        return updated

    def __hash__(self) -> int:
        """Hash based on file path."""
        return hash(str(self.to_upload))

    def __eq__(self, other) -> bool:
        """Equality based on file path."""
        if not isinstance(other, FileProcessor):
            return False
        return self.to_upload == other.to_upload

    def __str__(self) -> str:
        """String representation."""
        return f"FileProcessor({self.to_upload})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"FileProcessor(to_upload={self.to_upload}, manga_series={self.manga_series})"
