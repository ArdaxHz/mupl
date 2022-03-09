import configparser
import json
import logging
import os
import re
import ssl
import string
import time
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

import natsort
import requests

__version__ = "0.8.93"

languages = [
    {"english": "English", "md": "en", "iso": "eng"},
    {"english": "Japanese", "md": "ja", "iso": "jpn"},
    {"english": "Japanese (Romaji)", "md": "ja-ro", "iso": "jpn"},
    {"english": "Polish", "md": "pl", "iso": "pol"},
    {"english": "Serbo-Croatian", "md": "sh", "iso": "hrv"},
    {"english": "Dutch", "md": "nl", "iso": "dut"},
    {"english": "Italian", "md": "it", "iso": "ita"},
    {"english": "Russian", "md": "ru", "iso": "rus"},
    {"english": "German", "md": "de", "iso": "ger"},
    {"english": "Hungarian", "md": "hu", "iso": "hun"},
    {"english": "French", "md": "fr", "iso": "fre"},
    {"english": "Finnish", "md": "fi", "iso": "fin"},
    {"english": "Vietnamese", "md": "vi", "iso": "vie"},
    {"english": "Greek", "md": "el", "iso": "gre"},
    {"english": "Bulgarian", "md": "bg", "iso": "bul"},
    {"english": "Spanish (Es)", "md": "es", "iso": "spa"},
    {"english": "Portuguese (Br)", "md": "pt-br", "iso": "por"},
    {"english": "Portuguese (Pt)", "md": "pt", "iso": "por"},
    {"english": "Swedish", "md": "sv", "iso": "swe"},
    {"english": "Arabic", "md": "ar", "iso": "ara"},
    {"english": "Danish", "md": "da", "iso": "dan"},
    {"english": "Chinese (Simp)", "md": "zh", "iso": "chi"},
    {"english": "Chinese (Romaji)", "md": "zh-ro", "iso": "chi"},
    {"english": "Bengali", "md": "bn", "iso": "ben"},
    {"english": "Romanian", "md": "ro", "iso": "rum"},
    {"english": "Czech", "md": "cs", "iso": "cze"},
    {"english": "Mongolian", "md": "mn", "iso": "mon"},
    {"english": "Turkish", "md": "tr", "iso": "tur"},
    {"english": "Indonesian", "md": "id", "iso": "ind"},
    {"english": "Korean", "md": "ko", "iso": "kor"},
    {"english": "Korean (Romaji)", "md": "ko-ro", "iso": "kor"},
    {"english": "Spanish (LATAM)", "md": "es-la", "iso": "spa"},
    {"english": "Persian", "md": "fa", "iso": "per"},
    {"english": "Malay", "md": "ms", "iso": "may"},
    {"english": "Thai", "md": "th", "iso": "tha"},
    {"english": "Catalan", "md": "ca", "iso": "cat"},
    {"english": "Filipino", "md": "tl", "iso": "fil"},
    {"english": "Chinese (Trad)", "md": "zh-hk", "iso": "chi"},
    {"english": "Ukrainian", "md": "uk", "iso": "ukr"},
    {"english": "Burmese", "md": "my", "iso": "bur"},
    {"english": "Lithuanian", "md": "lt", "iso": "lit"},
    {"english": "Hebrew", "md": "he", "iso": "heb"},
    {"english": "Hindi", "md": "hi", "iso": "hin"},
    {"english": "Norwegian", "md": "no", "iso": "nor"},
    {"english": "Other", "md": "null", "iso": "null"},
]
http_error_codes = {
    "400": "Bad Request.",
    "401": "Unauthorised.",
    "403": "Forbidden.",
    "404": "Not Found.",
    "429": "Too Many Requests.",
    "500": "Internal Server Error.",
    "502": "Bad Gateway.",
    "503": "Service Unavailable.",
    "504": "Gateway Timeout.",
}


root_path = Path(".")
log_folder_path = root_path.joinpath("logs")
log_folder_path.mkdir(parents=True, exist_ok=True)

logs_path = log_folder_path.joinpath(f"md_uploader_{str(date.today())}.log")
logging.basicConfig(
    filename=logs_path,
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
)

FILE_NAME_REGEX = re.compile(
    r"^(?:\[(?P<artist>.+?)?\])?\s?"  # Artist
    r"(?P<title>.+?)"  # Manga title
    r"(?:\s?\[(?P<language>[a-z]{2}(?:-[a-z]{2})?|[a-zA-Z]{3}|[a-zA-Z]+)?\])?\s-\s"  # Language
    r"(?P<prefix>(?:[c](?:h(?:a?p?(?:ter)?)?)?\.?\s?))?(?P<chapter>\d+(?:\.\d)?)?"  # Chapter number and prefix
    r"(?:\s?\((?:[v](?:ol(?:ume)?(?:s)?)?\.?\s?)?(?P<volume>\d+(?:\.\d)?)?\))?"  # Volume number
    r"(?:\s?\((?P<chapter_title>.+)\))?"  # Chapter title
    r"(?:\s?\{(?P<publish_date>\d{4}-[0-1]\d-(?:[0-2]\d|3[0-1]))\})?"  # Publish date
    r"(?:\s?\[(?:(?P<group>.+))?\])?"  # Groups
    r"(?:\s?\{v?(?P<version>\d)?\})?"  # Chapter version
    r"(?:\.(?P<extension>zip|cbz))?$",  # File extension
    re.IGNORECASE,
)


def load_config_info(config: configparser.RawConfigParser):
    """Check if the config file has the needed data, if not, use the default values."""
    if config["Paths"].get("mangadex_api_url", "") == "":
        logging.warning("Mangadex api path empty, using default.")
        config["Paths"]["mangadex_api_url"] = "https://api.mangadex.org"

    if config["Paths"].get("name_id_map_file", "") == "":
        logging.info("Name id map_file path empty, using default.")
        config["Paths"]["name_id_map_file"] = "name_id_map.json"

    if config["Paths"].get("uploads_folder", "") == "":
        logging.info("To upload files folder path empty, using default.")
        config["Paths"]["uploads_folder"] = "to_upload"

    if config["Paths"].get("uploaded_files", "") == "":
        logging.info("Uploaded files folder path empty, using default.")
        config["Paths"]["uploaded_files"] = "uploaded"

    if config["Paths"].get("mdauth_path", "") == "":
        logging.info("mdauth path empty, using default.")
        config["Paths"]["mdauth_path"] = ".mdauth"

    # Config files can only take strings, convert all the integers to string.

    try:
        int(config["User Set"]["number_of_images_upload"])
    except ValueError:
        logging.warning(
            "Config file number of images to upload is empty or contains a non-number character, using default of 10."
        )
        config["User Set"]["number_of_images_upload"] = str(10)

    try:
        int(config["User Set"]["upload_retry"])
    except ValueError:
        logging.warning(
            "Config file number of image retry is empty or contains a non-number character, using default of 3."
        )
        config["User Set"]["upload_retry"] = str(3)

    try:
        int(config["User Set"]["ratelimit_time"])
    except ValueError:
        logging.warning(
            "Config file time to sleep is empty or contains a non-number character, using default of 2."
        )
        config["User Set"]["ratelimit_time"] = str(2)


def open_config_file(root_path: Path) -> configparser.RawConfigParser:
    """Try to open the config file if it exists."""
    config_file_path = root_path.joinpath("config").with_suffix(".ini")
    # Open config file and read values
    if config_file_path.exists():
        config = configparser.RawConfigParser()
        config.read(config_file_path)
        logging.info("Loaded config file.")
    else:
        logging.critical("Config file not found, exiting.")
        raise FileNotFoundError("Config file not found.")

    load_config_info(config)
    return config


config = open_config_file(root_path)
mangadex_api_url = config["Paths"]["mangadex_api_url"]
RATELIMIT_TIME = int(config["User Set"]["ratelimit_time"])
UPLOAD_RETRY = int(config["User Set"]["upload_retry"])


def convert_json(response_to_convert: requests.Response) -> Optional[dict]:
    """Convert the api response into a parsable json."""
    critical_decode_error_message = (
        "Couldn't convert mangadex api response into a json."
    )

    logging.debug(
        f"Request id: {response_to_convert.headers.get('x-request-id', None)}"
    )

    try:
        converted_response = response_to_convert.json()
    except json.JSONDecodeError:
        logging.critical(critical_decode_error_message)
        print(critical_decode_error_message)
        return
    except AttributeError:
        logging.critical(
            f"Api response doesn't have load as json method, trying to load as json manually."
        )
        try:
            converted_response = json.loads(response_to_convert.content)
        except json.JSONDecodeError:
            logging.critical(critical_decode_error_message)
            print(critical_decode_error_message)
            return

    logging.debug("Convert api response into json.")
    return converted_response


def print_error(
    error_response: requests.Response,
    *,
    show_error: bool = True,
    log_error: bool = False,
) -> str:
    """Print the errors the site returns."""
    status_code = error_response.status_code
    error_converting_json_log_message = (
        "{} when converting the error response into json."
    )
    error_converting_json_print_message = (
        f"{status_code}: Couldn't convert api response into json."
    )
    error_message = ""

    if status_code == 429:
        error_message = f"429: {http_error_codes.get(str(status_code))}"
        if log_error:
            logging.error(error_message)
        if show_error:
            print(error_message)
        time.sleep(RATELIMIT_TIME * 4)
        return error_message

    # Api didn't return json object
    try:
        error_json = error_response.json()
    except json.JSONDecodeError as e:
        logging.error(error_converting_json_log_message.format(e))
        print(error_converting_json_print_message)
        return error_converting_json_print_message
    # Maybe already a json object
    except AttributeError:
        logging.error(f"Error response is already a json.")
        # Try load as a json object
        try:
            error_json = json.loads(error_response.content)
        except json.JSONDecodeError as e:
            logging.error(error_converting_json_log_message.format(e))
            print(error_converting_json_print_message)
            return error_converting_json_print_message

    # Api response doesn't follow the normal api error format
    try:
        errors = [
            f'{e["status"]}: {e["detail"] if e["detail"] is not None else ""}'
            for e in error_json["errors"]
        ]
        errors = ", ".join(errors)

        if not errors:
            errors = http_error_codes.get(str(status_code), "")

        error_message = f"Error: {errors}"
        if log_error:
            logging.warning(error_message)
        if show_error:
            print(error_message)
    except KeyError:
        error_message = f"KeyError {status_code}: {error_json}."
        if log_error:
            logging.warning(error_message)
        if show_error:
            print(error_message)

    return error_message


def make_session(headers: dict = {}) -> requests.Session:
    """Make a new requests session and update the headers if provided."""
    session = requests.Session()
    session.headers.update({"User-Agent": f"md_uploader/{__version__}"})
    session.headers.update(headers)
    return session


def open_manga_series_map(
    config: configparser.RawConfigParser, files_path: Path
) -> dict:
    """Get the manga-name-to-id map."""
    try:
        with open(
            files_path.joinpath(config["Paths"]["name_id_map_file"]), "r"
        ) as json_file:
            names_to_ids = json.load(json_file)
    except FileNotFoundError:
        not_found_error = f"The manga name-to-id json file couldn't be found. Continuing with an empty name-id map."
        logging.error(not_found_error)
        print(not_found_error)
        return {"manga": {}, "group": {}}
    except json.JSONDecodeError:
        corrupted_error = f"The manga name-to-id json file is corrupted. Continuing with an empty name-id map."
        logging.error(corrupted_error)
        print(corrupted_error)
        return {"manga": {}, "group": {}}
    return names_to_ids


class AuthMD:
    def __init__(self, session: requests.Session, config: configparser.RawConfigParser):
        self.session = session
        self.config = config
        self.first_login = True
        self.successful_login = False
        self.refresh_token = None
        self.token_file = root_path.joinpath(config["Paths"]["mdauth_path"])
        self.md_auth_api_url = f"{mangadex_api_url}/auth"

    def _open_auth_file(self) -> Optional[str]:
        try:
            with open(self.token_file, "r") as login_file:
                token = json.load(login_file)

            refresh_token = token["refresh"]
            return refresh_token
        except (FileNotFoundError, json.JSONDecodeError):
            logging.error(
                "Couldn't find the file, trying to login using your account details."
            )
            return None

    def _save_session(self, token: dict):
        """Save the session and refresh tokens."""
        with open(self.token_file, "w") as login_file:
            login_file.write(json.dumps(token, indent=4))
        logging.debug("Saved .mdauth file.")

    def _update_headers(self, session_token: str):
        """Update the session headers to include the auth token."""
        self.session.headers = {"Authorization": f"Bearer {session_token}"}

    def _refresh_token(self) -> bool:
        """Use the refresh token to get a new session token."""
        for i in range(UPLOAD_RETRY):
            try:
                refresh_response = self.session.post(
                    f"{self.md_auth_api_url}/refresh",
                    json={"token": self.refresh_token},
                )
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if refresh_response.status_code in range(200, 300):
                refresh_response_json = convert_json(refresh_response)
                if refresh_response_json is not None:
                    refresh_data = refresh_response_json["token"]

                    self._update_headers(refresh_data["session"])
                    self._save_session(refresh_data)
                    return True
                continue
            elif refresh_response.status_code in (401, 403):
                error = print_error(refresh_response)
                logging.warning(
                    f"Couldn't login using refresh token, logging in using your account. {error}"
                )
                return self._login_using_details()

        error = print_error(refresh_response)
        logging.error(f"Couldn't refresh token. {error}")
        return False

    def _check_login(self) -> bool:
        """Try login using saved session token."""
        for i in range(UPLOAD_RETRY):
            try:
                auth_check_response = self.session.get(f"{self.md_auth_api_url}/check")
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if auth_check_response.status_code in range(200, 300):
                auth_data = convert_json(auth_check_response)
                if auth_data is not None:
                    if auth_data["isAuthenticated"]:
                        logging.info("Already logged in.")
                        return True

            if self.refresh_token is None:
                self.refresh_token = self._open_auth_file()
                if self.refresh_token is None:
                    return self._login_using_details()
            return self._refresh_token()
        return False

    def _login_using_details(self) -> bool:
        """Login using account details."""
        username = self.config["MangaDex Credentials"]["mangadex_username"]
        password = self.config["MangaDex Credentials"]["mangadex_password"]

        if username == "" or password == "":
            critical_message = "Login details missing."
            logging.critical(critical_message)
            raise Exception(critical_message)

        for i in range(UPLOAD_RETRY):
            try:
                login_response = self.session.post(
                    f"{self.md_auth_api_url}/login",
                    json={"username": username, "password": password},
                )
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if login_response.status_code in range(200, 300):
                login_response_json = convert_json(login_response)
                if login_response_json is not None:
                    login_token = login_response_json["token"]
                    self._update_headers(login_token["session"])
                    self._save_session(login_token)
                    return True

        error = print_error(login_response)
        logging.error(
            f"Couldn't login to mangadex using the details provided. {error}."
        )
        return False

    def login(self, check_login=True):
        """Login to MD account using details or saved token."""

        if not check_login and self.successful_login:
            logging.info("Already logged in, not checking for login.")
            return

        logging.info("Trying to login through the .mdauth file.")

        if self.first_login:
            self.refresh_token = self._open_auth_file()
            if self.refresh_token is None:
                logged_in = self._login_using_details()
            else:
                logged_in = self._refresh_token()
        else:
            logged_in = self._check_login()

        if logged_in:
            self.successful_login = True
            if self.first_login:
                logging.info(f"Logged into mangadex.")
                print("Logged in.")
                self.first_login = False
        else:
            logging.critical("Couldn't login.")
            raise Exception("Couldn't login.")


class FileProcesser:
    def __init__(
        self, to_upload: Path, names_to_ids: dict, config: configparser.RawConfigParser
    ) -> None:
        self._to_upload = to_upload
        self._zip_name = to_upload.name
        self._names_to_ids = names_to_ids
        self._config = config
        self._uuid_regex = re.compile(
            r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
            re.IGNORECASE,
        )
        self._file_name_regex = FILE_NAME_REGEX

    def _match_file_name(self) -> Optional[re.Match[str]]:
        """Check for a full regex match of the file."""
        # Check if the zip name is in the correct format
        zip_name_match = self._file_name_regex.match(self._zip_name)
        if not zip_name_match:
            logging.error(f"Zip {self._zip_name} isn't in the correct naming format.")
            print(f"{self._zip_name} not in the correct naming format, skipping.")
            return
        return zip_name_match

    def _get_manga_series(self) -> Optional[str]:
        """Get the series title, use the id map if zip file doesn't have the uuid already."""
        manga_series = self._zip_name_match.group("title")
        if not self._uuid_regex.match(manga_series):
            try:
                manga_series = self._names_to_ids["manga"].get(manga_series, None)
            except KeyError:
                manga_series = None
                logging.warning(f"No manga id found for {manga_series}.")
        return manga_series

    def _get_language(self) -> str:
        """Convert the inputted language into the format MangaDex uses

        Args:
            language (str): Can be the full language name, ISO 639-2 or ISO 639-3 codes.

        Returns:
            str: ISO 639-2 code, which MangaDex uses for languages.
        """
        language = self._zip_name_match.group("language")

        # Chapter language is English
        if language is None:
            return "en"
        elif language.lower() in ("eng", "en"):
            return "en"
        elif len(language) < 2:
            logging.warning(f"Language selected, {language} isn't in ISO format.")
            print("Not a valid language option.")
            return "null"
        # Chapter language already in correct format for MD
        elif re.match(r"^[a-z]{2}(?:-[a-z]{2})?$", language):
            logging.info(f"Language {language} already in ISO-639-2 form.")
            return language
        # Language in iso-639-3 format already
        elif len(language) == 3:
            available_langs = [l["md"] for l in languages if l["iso"] == language]

            if available_langs:
                return available_langs[0]
            return "null"
        else:
            # Language is a word instead of code, look for language and use that
            # code
            languages_match = [
                l for l in languages if language.lower() in l["english"].lower()
            ]

            if len(languages_match) > 1:
                print(
                    "Found multiple matching languages, please choose the language you want to download from the following options."
                )

                for count, item in enumerate(languages_match, start=1):
                    print(f'{count}: {item["english"]}')

                try:
                    lang = int(
                        input(
                            f"Choose a number matching the position of the language: "
                        )
                    )
                except ValueError:
                    logging.warning(
                        "Language option selected is not a number, using null as language."
                    )
                    print("That's not a number.")
                    return "null"

                if lang not in range(1, (len(languages_match) + 1)):
                    logging.warning(
                        "Language option selected is not in the accepted range."
                    )
                    print("Not a valid language option.")
                    return "null"

                lang_to_use = languages_match[(lang - 1)]
                return lang_to_use["md"]
            return languages_match[0]["md"]

    def _get_chapter_number(self) -> Optional[str]:
        """Get the chapter number from the file,
        use None for the number if the chapter is a prefix."""
        chapter_number = self._zip_name_match.group("chapter")
        if chapter_number is not None:
            parts = re.split(r"\.|\-|\,", chapter_number)
            parts[0] = "0" if len(parts[0].lstrip("0")) == 0 else parts[0].lstrip("0")

            chapter_number = ".".join(parts)

        # Chapter is a oneshot
        if self._zip_name_match.group("prefix") is None:
            chapter_number = None
            logging.info("No chapter number prefix found, uploading as oneshot.")
        return chapter_number

    def _get_volume_number(self) -> Optional[str]:
        """Get the volume number from the file if it exists."""
        volume_number = self._zip_name_match.group("volume")
        if volume_number is not None:
            volume_number = volume_number.lstrip("0")
            # Volume 0
            if len(volume_number) == 0:
                volume_number = "0"
        return volume_number

    def _get_chapter_title(self) -> Optional[str]:
        """Get the chapter title from the file if it exists."""
        chapter_title = self._zip_name_match.group("chapter_title")
        if chapter_title is not None:
            # Add the question mark back to the chapter title
            chapter_title = chapter_title.replace(r"{question_mark}", "?")
        return chapter_title

    def _get_publish_date(self):
        """Get the chapter publish date."""
        publish_date = self._zip_name_match.group("publish_date")
        if publish_date is not None:
            if datetime.fromisoformat(
                f"{publish_date}T00:00:00"
            ) > datetime.now() + timedelta(weeks=2):
                publish_date_over_2_weeks_error = f"Chosen publish date is over 2 weeks, this might cause an error with the Mangadex API."
                logging.warning(publish_date_over_2_weeks_error)
                print(publish_date_over_2_weeks_error)

            if datetime.fromisoformat(f"{publish_date}T00:00:00") < datetime.now():
                publish_date_before_current_error = f"Chosen publish date is before the current date, not setting a publish date."
                logging.warning(publish_date_before_current_error)
                print(publish_date_before_current_error)
                publish_date = None
        return publish_date

    def _get_groups(self) -> List[str]:
        """Get the group ids from the file, use the group fallback if the file has no gorups."""
        groups = []
        groups_match = self._zip_name_match.group("group")
        if groups_match is not None:
            # Split the zip name groups into an array and remove any
            # leading/trailing whitespace
            groups_array = groups_match.split("+")
            groups_array = [g.strip() for g in groups_array]

            # Check if the groups are using uuids, if not, use the id map for
            # the id
            for group in groups_array:
                if not self._uuid_regex.match(group):
                    try:
                        group_id = self._names_to_ids["group"].get(group, None)
                    except KeyError:
                        logging.warning(
                            f"No group id found for {group}, not tagging the upload with this group."
                        )
                        group_id = None
                    if group_id is not None:
                        groups.append(group_id)
                else:
                    groups.append(group)

        if not groups:
            logging.warning("Zip groups array is empty, using group fallback.")
            print(f"No groups found, using group fallback.")
            groups = (
                []
                if self._config["User Set"]["group_fallback_id"] == ""
                else [self._config["User Set"]["group_fallback_id"]]
            )
            if not groups:
                logging.warning("Group fallback not found, uploading without a group.")
                print("Group fallback not found, uploading without a group.")
        return groups

    def process_zip_name(self) -> bool:
        """Extract the respective chapter data from the file name."""
        self._zip_name_match = self._match_file_name()
        if self._zip_name_match is None:
            logging.error(f"No values processed from {self._to_upload}, skipping.")
            return False

        self.manga_series = self._get_manga_series()

        if self.manga_series is None:
            logging.error(f"Couldn't find a manga id for {self._zip_name}, skipping.")
            print(f"Skipped {self._zip_name}, no manga id found.")
            return False

        self.language = self._get_language()
        self.chapter_number = self._get_chapter_number()
        self.volume_number = self._get_volume_number()
        self.groups = self._get_groups()
        self.chapter_title = self._get_chapter_title()
        self.publish_date = self._get_publish_date()

        upload_details = f"Manga id: {self.manga_series}, chapter: {self.chapter_number}, volume: {self.volume_number}, title: {self.chapter_title}, language: {self.language}, groups: {self.groups}, publish on: {self.publish_date}."
        logging.info(f"Chapter upload details: {upload_details}")
        print(upload_details)
        return True


class ChapterUploaderProcess:
    def __init__(
        self,
        to_upload: Path,
        session: requests.Session,
        names_to_ids: dict,
        config: configparser.RawConfigParser,
        failed_uploads: list,
        md_auth_object: AuthMD,
    ):

        self.to_upload = to_upload
        self.session = session
        self.names_to_ids = names_to_ids
        self.config = config
        self.failed_uploads = failed_uploads
        self.md_auth_object = md_auth_object
        self.zip_name = to_upload.name
        self.zip_extension = to_upload.suffix
        self.folder_upload = False
        if self.to_upload.is_dir():
            self.folder_upload = True
            self.zip_extension = None

        self.uploaded_files_path = Path(self.config["Paths"]["uploaded_files"])
        self.images_upload_session = int(
            self.config["User Set"]["number_of_images_upload"]
        )
        self.number_upload_retry = UPLOAD_RETRY
        self.ratelimit_time = RATELIMIT_TIME
        self.md_upload_api_url = f"{mangadex_api_url}/upload"

        # Spliced list of lists
        self.valid_images_to_upload: List[List[str]] = []
        # Renamed file to original file name
        self.images_to_upload_names: Dict[str, str] = {}
        # Images to include with chapter commit
        self.images_to_upload_ids: List[str] = []
        self.upload_session_id: Optional[str] = None

        self.myzip = None
        if not self.folder_upload:
            self.myzip = self._read_zip()

        self.info_list = self._get_valid_images()

    def _key(self, x: str) -> Union[Literal[0], str]:
        if Path(x).name[0] in string.punctuation:
            return 0
        else:
            return x

    def _read_image_data(self, image: str) -> bytes:
        if self.folder_upload:
            image_path = self.to_upload.joinpath(image)
            return image_path.read_bytes()
        else:
            with self.myzip.open(image) as myfile:
                return myfile.read()

    def _read_zip(self) -> zipfile.ZipFile:
        # Open zip file and read the data
        return zipfile.ZipFile(self.to_upload)

    def _get_image_mime_type(self, image: str) -> bool:
        """Returns the image type from the first few bytes."""
        image_data = self._read_image_data(image)

        if image_data.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
            return True
        elif image_data[0:3] == b"\xff\xd8\xff" or image_data[6:10] in (
            b"JFIF",
            b"Exif",
        ):
            return True
        elif image_data.startswith(
            (b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")
        ):
            return True
        else:
            return False

    def _get_valid_images(self):
        if self.folder_upload:
            to_iter = [x.name for x in self.to_upload.iterdir()]
        else:
            to_iter = [x.filename for x in self.myzip.infolist()]

        info_list = [image for image in to_iter if self._get_image_mime_type(image)]
        info_list_images_only = natsort.natsorted(info_list, key=self._key)

        self.valid_images_to_upload = [
            info_list_images_only[l : l + self.images_upload_session]
            for l in range(0, len(info_list_images_only), self.images_upload_session)
        ]
        return info_list_images_only

    def _get_images_to_upload(self, images_to_read: List[str]) -> Dict[str, bytes]:
        """Read the image data from the zip as list."""
        logging.info(f"Images to upload: {images_to_read}")
        files: Dict[str, bytes] = {}
        # Read the image data and add to files dict
        for array_index, image in enumerate(images_to_read, start=1):
            image_filename = str(Path(image).name)
            renamed_file = str(self.info_list.index(image))
            self.images_to_upload_names.update({renamed_file: image_filename})
            files.update({renamed_file: self._read_image_data(image)})
        return files

    def _upload_images(self, image_batch: Dict[str, bytes]) -> bool:
        """Try to upload every 10 (default) images to the upload session."""
        if not image_batch:
            return True

        image_batch_list = list(image_batch.keys())
        print(
            f"Uploading images {int(image_batch_list[0])+1} to {int(image_batch_list[-1])+1}."
        )
        logging.debug(
            f"Uploading images {int(image_batch_list[0])+1} to {int(image_batch_list[-1])+1}."
        )

        failed_image_upload = False
        for image_retries in range(self.number_upload_retry):
            # Upload the images
            try:
                image_upload_response = self.session.post(
                    f"{self.md_upload_api_url}/{self.upload_session_id}",
                    files=image_batch,
                )
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if image_upload_response.status_code not in range(200, 300):
                error = print_error(image_upload_response)
                logging.error(f"Error uploading images. {error}")
                failed_image_upload = True
                continue

            # Some images returned errors
            uploaded_image_data = convert_json(image_upload_response)
            succesful_upload_data = uploaded_image_data["data"]
            if (
                uploaded_image_data["errors"]
                or uploaded_image_data["result"] == "error"
            ):
                error = print_error(image_upload_response)
                logging.warning(f"Some images errored out. {error}")

            # Add successful image uploads to the image ids array
            for uploaded_image in succesful_upload_data:
                if succesful_upload_data.index(uploaded_image) == 0:
                    logging.info(f"Success: Uploaded images {succesful_upload_data}")
                uploaded_image_attributes = uploaded_image["attributes"]
                original_filename = uploaded_image_attributes["originalFileName"]
                file_size = uploaded_image_attributes["fileSize"]

                self.images_to_upload_ids.insert(
                    int(original_filename), uploaded_image["id"]
                )
                succesful_upload_message = f"Success: Uploaded page {self.images_to_upload_names[original_filename]}, size: {file_size} bytes."
                print(succesful_upload_message)

            if len(succesful_upload_data) == len(image_batch):
                logging.info(
                    f"Uploaded images {int(image_batch_list[0])+1} to {int(image_batch_list[-1])+1}."
                )
                failed_image_upload = False
                break
            else:
                image_batch = {
                    k: v
                    for (k, v) in image_batch.items()
                    if k
                    not in [
                        i["attributes"]["originalFileName"]
                        for i in succesful_upload_data
                    ]
                }
                logging.warning(
                    f"Some images didn't upload, retrying. Failed images: {image_batch}"
                )
                failed_image_upload = True
                continue

        return failed_image_upload

    def remove_upload_session(self, session_id: Optional[str] = None):
        """Delete the upload session."""
        if session_id is None:
            session_id = self.upload_session_id

        try:
            self.session.delete(f"{self.md_upload_api_url}/{session_id}")
        except (requests.RequestException) as e:
            logging.error(f"Couldn't delete {session_id}: {e}")
        else:
            logging.info(f"Sent {session_id} to be deleted.")
        finally:
            time.sleep(self.ratelimit_time)

    def _delete_exising_upload_session(self, chapter_upload_session_retry: int):
        """Remove any exising upload sessions to not error out as mangadex only allows one upload session at a time."""
        if chapter_upload_session_retry > 0:
            return

        for removal_retry in range(self.number_upload_retry):
            try:
                existing_session = self.session.get(f"{mangadex_api_url}/upload")
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if existing_session.status_code in range(200, 300):
                existing_session_json = convert_json(existing_session)

                if existing_session_json is None:
                    logging.warning(
                        f"Couldn't convert exising upload session response into a json, retrying."
                    )
                else:
                    self.remove_upload_session(existing_session_json["data"]["id"])
                    return

            elif existing_session.status_code == 404:
                logging.info("No existing upload session found.")
                return
            elif existing_session.status_code == 401:
                logging.warning("Not logged in, logging in and retrying.")
                self.md_auth_object.login()
                # self._delete_exising_upload_session(chapter_upload_session_retry)
            else:
                print_error(existing_session, log_error=True)
                logging.warning(
                    f"Couldn't delete the exising upload session, retrying."
                )

            time.sleep(RATELIMIT_TIME)

        logging.error("Exising upload session not deleted.")
        raise Exception(f"Couldn't delete existing upload session.")

    def _create_upload_session(self) -> Optional[dict]:
        """Try create an upload session 3 times."""
        chapter_upload_session_successful = False

        payload = {
            "manga": self.processed_zip_object.manga_series,
            "groups": self.processed_zip_object.groups,
        }

        for chapter_upload_session_retry in range(self.number_upload_retry):
            self._delete_exising_upload_session(chapter_upload_session_retry)
            # Start the upload session
            try:
                upload_session_response = self.session.post(
                    f"{self.md_upload_api_url}/begin",
                    json=payload,
                )
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if upload_session_response.status_code == 401:
                self.md_auth_object.login()
            elif upload_session_response.status_code not in range(200, 300):
                error = print_error(upload_session_response)
                logging.error(
                    f"Couldn't create upload draft for {self.zip_name}. {error}"
                )
                print(f"Error creating draft for {self.zip_name}.")

            if upload_session_response.status_code in range(200, 300):
                upload_session_response_json = convert_json(upload_session_response)

                if upload_session_response_json is not None:
                    chapter_upload_session_successful = True
                    return upload_session_response_json
                else:
                    upload_session_response_json_message = f"Couldn't convert successful upload session creation for {self.to_upload} into a json, retrying."
                    logging.error(upload_session_response_json_message)
                    print(upload_session_response_json_message)

            time.sleep(self.ratelimit_time)

        # Couldn't create an upload session, skip the chapter
        if not chapter_upload_session_successful:
            upload_session_response_json_message = (
                f"Couldn't create an upload session for {self.to_upload}."
            )
            logging.error(upload_session_response_json_message)
            print(upload_session_response_json_message)
            self.failed_uploads.append(self.to_upload)
            return

    def _commit_chapter(self) -> bool:
        """Try commit the chapter to mangadex."""
        succesful_upload = False
        chapter_commit_response: Optional[requests.Response] = None
        payload = {
            "chapterDraft": {
                "volume": self.processed_zip_object.volume_number,
                "chapter": self.processed_zip_object.chapter_number,
                "title": self.processed_zip_object.chapter_title,
                "translatedLanguage": self.processed_zip_object.language,
            },
            "pageOrder": self.images_to_upload_ids,
        }

        logging.debug(f"Payload: {payload}")

        for commit_retries in range(self.number_upload_retry):
            if self.processed_zip_object.publish_date is not None:
                payload["chapterDraft"][
                    "publishAt"
                ] = f"{self.processed_zip_object.publish_date}T{datetime.now().strftime('%H:%M:%S')}"

            try:
                chapter_commit_response = self.session.post(
                    f"{self.md_upload_api_url}/{self.upload_session_id}/commit",
                    json=payload,
                )
            except (requests.exceptions.SSLError, ssl.SSLEOFError) as e:
                logging.error(e)
                continue
            except requests.RequestException as e:
                logging.critical(e)
                break

            if chapter_commit_response.status_code in range(200, 300):
                succesful_upload = True
                chapter_commit_response_json = convert_json(chapter_commit_response)

                if chapter_commit_response_json is not None:
                    succesful_upload_id = chapter_commit_response_json["data"]["id"]
                    print(
                        f"Succesfully uploaded: {succesful_upload_id}, {self.zip_name}."
                    )
                    logging.info(
                        f"Succesful commit: {succesful_upload_id}, {self.zip_name}."
                    )
                else:
                    chapter_commit_response_json_message = f"Couldn't convert successful chapter commit api response into a json"
                    logging.error(chapter_commit_response_json_message)
                    print(chapter_commit_response_json_message)

                # Move the uploaded zips to a different folder
                self.uploaded_files_path.mkdir(parents=True, exist_ok=True)
                if self.folder_upload:
                    zip_name = self.zip_name
                else:
                    zip_name = self.zip_name.rsplit(".", 1)[0]
                zip_extension = self.zip_extension or ""
                zip_path_str = f"{zip_name}{zip_extension}"
                version = 1

                while True:
                    version += 1
                    if zip_path_str in os.listdir(self.uploaded_files_path):
                        if self.folder_upload:
                            zip_name_unformat = self.zip_name
                        else:
                            zip_name_unformat = self.zip_name.rsplit(".", 1)[0]

                        zip_name = f"{zip_name_unformat}{{v{version}}}"
                        zip_path_str = f"{zip_name}{zip_extension}"
                        continue
                    else:
                        break

                new_uploaded_zip_path = self.to_upload.rename(
                    os.path.join(self.uploaded_files_path, f"{zip_name}{zip_extension}")
                )
                logging.info(f"Moved {self.to_upload} to {new_uploaded_zip_path}.")
                break
            elif chapter_commit_response.status_code == 401:
                self.md_auth_object.login()
            else:
                error = print_error(chapter_commit_response)
                commit_fail_message = (
                    f"Failed to commit {self.zip_name}, error {error}, trying again."
                )
                logging.warning(commit_fail_message)
                print(commit_fail_message)

            time.sleep(self.ratelimit_time)

        if not succesful_upload:
            if chapter_commit_response is not None:
                print_error(chapter_commit_response, log_error=True)
            commit_error_message = (
                f"Failed to commit {self.zip_name}, removing upload draft."
            )
            logging.error(commit_error_message)
            print(commit_error_message)
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
        return succesful_upload

    def start_chapter_upload(self):
        """Process the zip for uploading."""
        if not self.valid_images_to_upload:
            no_valid_images_found_error_message = (
                f"{self.zip_name} has no valid images to upload, skipping."
            )
            print(no_valid_images_found_error_message)
            logging.error(no_valid_images_found_error_message)
            return

        self.processed_zip_object = FileProcesser(
            self.to_upload, self.names_to_ids, self.config
        )
        processed_zip = self.processed_zip_object.process_zip_name()
        if not processed_zip:
            return

        self.md_auth_object.login(False)

        upload_session_response_json = self._create_upload_session()
        if upload_session_response_json is None:
            time.sleep(self.ratelimit_time)
            return

        self.upload_session_id = upload_session_response_json["data"]["id"]
        upload_session_id_message = (
            f"Created upload session: {self.upload_session_id}, {self.zip_name}."
        )
        logging.info(upload_session_id_message)
        print(upload_session_id_message)
        failed_image_upload = False

        for images_array in self.valid_images_to_upload:
            images_to_upload = self._get_images_to_upload(images_array)
            failed_image_upload = self._upload_images(images_to_upload)

            if failed_image_upload:
                break

        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if failed_image_upload:
            failed_image_upload_message = f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            print(failed_image_upload_message)
            logging.error(failed_image_upload_message)
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            return

        logging.info("Uploaded all of the chapter's images.")
        successful_upload = self._commit_chapter()


def get_zips_to_upload(config: configparser.RawConfigParser) -> Optional[List[Path]]:
    """Get a list of files that end with a zip/cbz extension for uploading."""
    to_upload_folder_path = Path(config["Paths"]["uploads_folder"])
    zips_to_upload = [
        x
        for x in to_upload_folder_path.iterdir()
        if bool(FILE_NAME_REGEX.match(x.name))
    ]
    zips_to_upload = natsort.os_sorted(zips_to_upload)
    zips_to_not_upload = [
        x for x in to_upload_folder_path.iterdir() if x not in zips_to_upload
    ]

    if zips_to_not_upload:
        logging.warning(
            f"Skipping {len(zips_to_not_upload)} files as they don't match the FILE_NAME_REGEX pattern: {zips_to_not_upload}"
        )

    if not zips_to_upload:
        no_zips_found_error_message = "No valid files found to upload, exiting."
        print(no_zips_found_error_message)
        logging.error(no_zips_found_error_message)
        return

    logging.info(f"Uploading files: {zips_to_upload}")
    return zips_to_upload


def main(config: configparser.RawConfigParser):
    """Run the uploader on each zip."""
    zips_to_upload = get_zips_to_upload(config)
    if zips_to_upload is None:
        return

    session = make_session()
    md_auth_object = AuthMD(session, config)
    names_to_ids = open_manga_series_map(config, root_path)
    failed_uploads = []

    for index, to_upload in enumerate(zips_to_upload, start=1):
        try:
            uploader_process = ChapterUploaderProcess(
                to_upload, session, names_to_ids, config, failed_uploads, md_auth_object
            )
            uploader_process.start_chapter_upload()
            if not uploader_process.folder_upload:
                uploader_process.myzip.close()

            if index % 5 == 0:
                md_auth_object.session = session = make_session()
                md_auth_object.login()

            del uploader_process

            logging.debug("Sleeping between zip upload.")
            time.sleep(RATELIMIT_TIME * 2)
        except KeyboardInterrupt:
            logging.warning("Keyboard Interrupt detected, exiting.")
            print("Keyboard interrupt detected, exiting.")
            try:
                uploader_process.remove_upload_session()
                if not uploader_process.folder_upload:
                    uploader_process.myzip.close()
                del uploader_process
            except UnboundLocalError:
                pass
            else:
                failed_uploads.append(zips_to_upload[zips_to_upload.index(to_upload)])
            break

    if failed_uploads:
        logging.info(f"Failed uploads: {failed_uploads}")
        print(f"Failed uploads:")
        for fail in failed_uploads:
            print(fail)


def check_for_update():
    """Check For any program updates."""
    logging.debug("Looking for program update.")

    # Check the local version is the same as on GitHub
    remote_version_info_response = requests.get(
        "https://raw.githubusercontent.com/Rudoal/mangadex_bulk_uploader/main/md_uploader.py"
    )
    if remote_version_info_response.ok:
        remote_version_info = remote_version_info_response.content.decode()

        ver_regex = re.compile(r"^__version__\s=\s\"(.+)\"$", re.MULTILINE)
        match = ver_regex.search(remote_version_info)
        remote_number = match.group(1)

        local_version = int(__version__.replace(".", ""))
        remote_version = int(remote_number.replace(".", ""))
        logging.warning(
            f"GitHub version: {remote_number}, local version: {__version__}."
        )

        if remote_version > local_version:
            download_update = input(
                f"""Looks like update {remote_number} is available, you're on {__version__}, do you want to download?
                "y" or "n" """
            )

            if download_update.lower() == "y":
                with open(
                    root_path.joinpath(f"{__file__}").with_suffix(".py"), "wb"
                ) as file:
                    file.write(remote_version_info_response.content)

                print(
                    "Downloaded the update, next program run will use the new update."
                )
                logging.info(
                    f"Successfully downloaded {remote_version}, will be used next program run."
                )
            else:
                print("Skipping update, this might result in api errors.")
                logging.warning("Update download skipped.")
    else:
        logging.error(
            f"Error searching for update: {remote_version_info_response.status_code}."
        )


if __name__ == "__main__":

    check_for_update()
    main(config)
