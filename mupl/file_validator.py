import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List

from mupl.utils.config import config, translate_message

logger = logging.getLogger("mupl")


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


class FileProcesser:
    def __init__(self, to_upload: "Path", names_to_ids: "dict") -> None:
        self.to_upload = to_upload
        self.zip_name = self.to_upload.name
        self.zip_extension = self.to_upload.suffix
        self._names_to_ids = names_to_ids
        self._uuid_regex = UUID_REGEX
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
            print(
                f"{translate_message['file_v_text_1']}".format(self.zip_name)
            )
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

        return str(language).strip().lower()

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
        if publish_date is None:
            return

        publish_year = self._zip_name_match.group("publish_year")
        publish_month = self._zip_name_match.group("publish_month")
        publish_day = self._zip_name_match.group("publish_day")
        publish_hour = self._zip_name_match.group("publish_hour")
        publish_minute = self._zip_name_match.group("publish_minute")
        publish_microsecond = self._zip_name_match.group("publish_microsecond")
        publish_offset = self._zip_name_match.group("publish_offset")
        publish_timezone = self._zip_name_match.group("publish_timezone")

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

    def _get_groups(self) -> "List[str]":
        """Get the group ids from the file, use the group fallback if the file has no groups."""
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
            groups = (
                []
                if not config["options"]["group_fallback_id"]
                else [config["options"]["group_fallback_id"]]
            )
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
            print(f"{translate_message['file_v_text_2']}".format(self.zip_name))
            return False

        self.language = self._get_language()
        self.chapter_number = self._get_chapter_number()
        self.volume_number = self._get_volume_number()
        self.groups = self._get_groups()
        self.chapter_title = self._get_chapter_title()
        self.publish_date = self._get_publish_date()
        return True

    def process_zip_name_extanded(self) -> "bool":
        """Extract the respective chapter data from the file name."""
        
        def match_file(to_upload):
            parts = to_upload.parts
            index_to_upload = parts.index('to_upload')
            parts = parts[index_to_upload:]

            idiom = None
            obra = None
            grup = None
            volume = None
            chapter = None
            title = None
            data = None

            idiom = parts[1] # Language
            obra = parts[2] # Project name
            grup = parts[3] # Group scan
            
            if parts[4].startswith("v"):
                volume = parts[4][1:].strip() # Volume (without 'v')
                volume = volume.lstrip('0')
                
                chapter = str(parts[5]) # Chapter
                
                # Verificar se o valor é "0000"
                if chapter == "0000":
                    chapter = None
                    self.oneshot = True
                else:
                    # Remover todos os zeros à esquerda
                    chapter = chapter.lstrip('0')
                
                if len(parts) == 7:
                    title = parts[6] # Title
                    data_position = title.find("{")  # Encontrar a posição inicial da chave {
    
                    if data_position != -1:
                        data_part = title[data_position:].strip()  # Texto da chave { até o final
                        data_part = data_part.rstrip("}").replace("{", "")  # Remover a chave } do final
                        title = title[:data_position].strip()  # Texto antes da chave {

                    data = data_part if data_position != -1 else None
            
            else:
                chapter = parts[4] # Chapter
                if chapter == "0000":
                    chapter = None
                    self.oneshot = True
                
                if len(parts) == 6:
                    title = parts[5] # Title
                    data_position = title.find("{")  # Encontrar a posição inicial da chave {
    
                    if data_position != -1:
                        data_part = title[data_position:].strip()  # Texto da chave { até o final
                        data_part = data_part.rstrip("}").replace("{", "")  # Remover a chave } do final
                        title = title[:data_position].strip()  # Texto antes da chave {

                    data = data_part if data_position != -1 else None
                
            return idiom, obra, grup, volume, chapter, title, data
        
        self._zip_name_match = match_file(self.to_upload)
        if self._zip_name_match is None:
            logger.error(f"No values processed from {self.to_upload}, skipping.")
            return False

        def get_manga(title):
            manga_series = title
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

        self.manga_series = get_manga(self._zip_name_match[1])

        if self.manga_series is None:
            logger.error(f"Couldn't find a manga id for {self.zip_name}, skipping.")
            print(f"{translate_message['file_v_text_2']}".format(self.zip_name))
            return False
        
        def group_get(group):
            """Get the group ids from the file, use the group fallback if the file has no groups."""
            groups = []
            groups_match = group
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
                groups = (
                    []
                    if not config["options"]["group_fallback_id"]
                    else [config["options"]["group_fallback_id"]]
                )
            return groups


        def publish_get(date):
            if date is None:
                return None
            
            try:
                if '-' in date and ' ' in date:
                    # Processar data no formato "DD-MM-YYYY HH-MM-SS"
                    date_time_parts = date.split(' ')
                    date_parts = date_time_parts[0].split('-')
                    time_parts = date_time_parts[1].split('-')

                    year = int(date_parts[2])
                    month = int(date_parts[1])
                    day = int(date_parts[0])

                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    second = int(time_parts[2])

                    publish_date = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                    return publish_date
                
                else:
                    parts = date.split()
                    total_seconds = 0

                    for part in parts:
                        if part.endswith('d'):
                            total_seconds += int(part[:-1]) * 86400  # 1 dia = 24 horas * 60 minutos * 60 segundos
                        elif part.endswith('h'):
                            total_seconds += int(part[:-1]) * 3600  # 1 hora = 60 minutos * 60 segundos
                        elif part.endswith('m'):
                            total_seconds += int(part[:-1]) * 60  # 1 minuto = 60 segundos
                        elif part.endswith('s'):
                            total_seconds += int(part[:-1])
                        else:
                            raise ValueError("Formato de tempo não reconhecido.")

                    if total_seconds > 1209600:  # 2 semanas em segundos
                        raise ValueError("O tempo máximo permitido é de 2 semanas.")

                    publish_date = datetime.now() + timedelta(seconds=total_seconds)
                    publish_date = publish_date.replace(microsecond=0)
                    publish_date = publish_date.isoformat()
                    publish_date = datetime.fromisoformat(publish_date).astimezone(tz=timezone.utc)

                    return publish_date
            
            except ValueError as e:
                logger.error(f"{self.zip_name} isn't in the correct date format.")
                return None

        self.language = self._zip_name_match[0]
        self.chapter_number = self._zip_name_match[4]
        self.volume_number = self._zip_name_match[3]
        self.groups = group_get(self._zip_name_match[2])
        self.chapter_title = self._zip_name_match[5]
        self.publish_date = publish_get(self._zip_name_match[6])
        return True

    @property
    def zip_name_match(self):
        return self._zip_name_match

    def __hash__(self):
        return hash(self.zip_name)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __str__(self):
        return self.zip_name

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"{self.zip_name}: "
            f"{self.manga_series=}, "
            f"{self.chapter_number=}, "
            f"{self.volume_number=}, "
            f"{self.chapter_title=}, "
            f"{self.language=}, "
            f"{self.groups=}, "
            f"{self.publish_date=}"
            f">"
        )
