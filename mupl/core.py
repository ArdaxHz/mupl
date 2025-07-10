import asyncio
import json
import os
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Union
from datetime import datetime
import uuid

import natsort

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.uploader.uploader import ChapterUploader
from mupl.exceptions import MuplException, MuplNotAFileError
from mupl.loc.load import download_localisation
from mupl.utils.config import validate_path
from mupl.utils.logs import (
    format_log_dir_path,
    setup_logs,
    clear_old_logs,
)

logger = logging.getLogger("mupl")

__all__ = ["Mupl"]


class Mupl:
    def __init__(
        self,
        mangadex_username: str = None,
        mangadex_password: str = None,
        client_id: str = None,
        client_secret: str = None,
        cli: bool = False,
        translation: Dict = None,
        move_files: bool = True,
        verbose_level: int = 0,
        number_of_images_upload: int = 10,
        upload_retry: int = 3,
        ratelimit_time: int = 2,
        logs_dir_path: str = None,
        max_log_days: int = 30,
        group_fallback_id: Optional[str] = None,
        number_threads: int = 3,
        language: str = "en",
        name_id_map_filename: str = "name_id_map.json",
        uploaded_dir_path: str = "uploaded",
        mangadex_api_url: str = "https://api.mangadex.org",
        mangadex_auth_url: str = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
        mdauth_filename: str = ".mdauth",
        verbose: bool = False,
        **kwargs,
    ):
        r"""
        Initializes the Mupl class with explicit parameters.

        Home path on Unix/Mac is /Users/<>/mupl, on Windows it's C:\Users\<>\mupl.

        Positional, Required Args:
            mangadex_username (str): MangaDex username.
            mangadex_password (str): MangaDex password.
            client_id (str): OAuth client ID.
            client_secret (str): OAuth client secret.

        Keyword, Optional Args:
            move_files (bool, optional): Whether to move files after upload. Defaults to True.
            verbose_level (int, optional): Logs verbosity, 0=INFO, 1=DEBUG.
            number_of_images_upload (int, optional): Number of images to upload at once. Defaults to 10.
            upload_retry (int, optional): Number of retries for failed uploads. Defaults to 3.
            ratelimit_time (int, optional): Time to wait between API calls. Defaults to 2.
            logs_dir_path (str, optional): Directory where to store logs. Defaults to home path. Will create 'logs' folder in this directory.
            max_log_days (int, optional): Maximum number of days to keep logs. Defaults to 30.
            group_fallback_id (str, optional): Fallback group ID. Defaults to None.
            number_threads (int, optional): Number of threads for concurrent uploads. Defaults to 3.
            language (str, optional): Language for mupl localisation. Defaults to "en".
            name_id_map_filename (str): Path to name-ID mapping file. Will check your home directory for this file, if running as a dependency, otherwise will look in the current working directory. Defaults to "name_id_map.json"..
            uploaded_dir_path (str): Path to folder for uploaded files. Will check your home directory for this folder, if running as a dependency, otherwise will look in the current working directory. Defaults to "uploaded".
            mangadex_api_url (str): MangaDex API URL. Defaults to "https://api.mangadex.org".
            mangadex_auth_url (str): MangaDex auth URL. Defaults to "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect".
        """

        self.cli = bool(cli)
        self.verbose = bool(verbose)
        self.move_files = bool(move_files)

        self.mupl_path = Path(__file__).parent
        self.home_path = Path.home().joinpath("mupl")
        if not validate_path(Path.home()):
            self.home_path = self.mupl_path

        if self.cli:
            self.mupl_path = Path.cwd()
            self.home_path = self.mupl_path

        self.number_of_images_upload = max(
            1,
            int(number_of_images_upload) if number_of_images_upload is not None else 10,
        )
        self.upload_retry = max(1, int(upload_retry) if upload_retry is not None else 3)
        self.ratelimit_time = max(
            1, int(ratelimit_time) if ratelimit_time is not None else 2
        )
        self.max_log_days = max(
            1, int(max_log_days) if max_log_days is not None else 30
        )
        self.number_threads = max(
            1, int(number_threads) if number_threads is not None else 3
        )
        verbose_level = max(0, int(verbose_level) if verbose_level is not None else 0)

        self.mangadex_username = (
            str(mangadex_username) if mangadex_username is not None else None
        )
        self.mangadex_password = (
            str(mangadex_password) if mangadex_password is not None else None
        )
        self.client_id = str(client_id) if client_id is not None else None
        self.client_secret = str(client_secret) if client_secret is not None else None

        if group_fallback_id is not None:
            try:
                uuid_obj = uuid.UUID(group_fallback_id)
                self.group_fallback_id = str(uuid_obj)
            except ValueError:
                logger.warning(
                    f"Invalid UUID format for group_fallback_id: {group_fallback_id}. Setting to None."
                )
                self.group_fallback_id = None
        else:
            self.group_fallback_id = None

        self.language = str(language).lower() if language is not None else "en"
        self.name_id_map_file = (
            str(name_id_map_filename)
            if name_id_map_filename is not None
            else "name_id_map.json"
        )
        self.mdauth_filename = (
            str(mdauth_filename) if mdauth_filename is not None else ".mdauth"
        )

        self.mangadex_api_url = (
            str(mangadex_api_url)
            if mangadex_api_url is not None
            else "https://api.mangadex.org"
        )
        if not self.mangadex_api_url.startswith(("http://", "https://")):
            self.mangadex_api_url = "https://" + self.mangadex_api_url

        self.mangadex_auth_url = (
            str(mangadex_auth_url)
            if mangadex_auth_url is not None
            else "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect"
        )
        if not self.mangadex_auth_url.startswith(("http://", "https://")):
            self.mangadex_auth_url = "https://" + self.mangadex_auth_url

        if os.path.isabs(uploaded_dir_path):
            self.uploaded_files = (
                uploaded_dir_path
                if isinstance(uploaded_dir_path, Path)
                else Path(uploaded_dir_path)
            )
        else:
            self.uploaded_files = self.home_path.joinpath(uploaded_dir_path)

        if os.path.isabs(self.mdauth_filename):
            self.mdauth_path = (
                self.mdauth_filename
                if isinstance(self.mdauth_filename, Path)
                else Path(self.mdauth_filename)
            )
        else:
            self.mdauth_path = self.mupl_path.joinpath(self.mdauth_filename)

        if self.mdauth_path.is_dir():
            raise MuplNotAFileError(
                f"mdauth_filename cannot be a directory: {self.mdauth_path.absolute()}"
            )
            self.mdauth_path = self.mdauth_path.joinpath(".mdauth")

        # self.mdauth_path.parent.mkdir(parents=True, exist_ok=True)
        # if not self.mdauth_path.exists():
        #     try:
        #         self.mdauth_path.touch()
        #     except OSError as e:
        #         logger.error(f"Failed to create {self.mdauth_path}: {e}")

        if logs_dir_path:
            if os.path.isabs(logs_dir_path):
                logs_dir_path = (
                    logs_dir_path
                    if isinstance(logs_dir_path, Path)
                    else Path(logs_dir_path)
                )
            else:
                logs_dir_path = self.home_path.joinpath(logs_dir_path)
        else:
            logs_dir_path = self.home_path

        if not self.cli:
            self.log_folder_path = format_log_dir_path(logs_dir_path)

            setup_logs(
                logger_name="mupl",
                path=self.log_folder_path,
                logger_filename="mupl",
                level=verbose_level,
            )

            clear_old_logs(self.log_folder_path, max_log_days)
        else:
            self.log_folder_path = format_log_dir_path(self.mupl_path)

        if os.path.isabs(self.name_id_map_file):
            self.name_id_map_path = (
                self.name_id_map_file
                if isinstance(self.name_id_map_file, Path)
                else Path(self.name_id_map_file)
            )
        else:
            self.name_id_map_path = self.home_path.joinpath(self.name_id_map_file)

        if self.name_id_map_path.is_dir():
            raise MuplNotAFileError(
                f"name_id_map_filename cannot be a directory: {self.name_id_map_path.absolute()}"
            )

        logger.info(f"Log path: {self.logs_path}")
        logger.info(f"Mupl path: {self.root_path}")
        logger.info(f"Home path: {self.user_path}")
        logger.info(f"Uploaded files folder path: {self.uploaded_files_path}")

        if not self.cli:
            logger.info(f"Script path: {Path.cwd().absolute()}")

        self.translation = translation or download_localisation(self.language)
        self.http_client = HTTPClient(
            mangadex_username=self.mangadex_username,
            mangadex_password=self.mangadex_password,
            client_id=self.client_id,
            client_secret=self.client_secret,
            mangadex_api_url=self.mangadex_api_url,
            mangadex_auth_url=self.mangadex_auth_url,
            mdauth_path=self.mdauth_path,
            ratelimit_time=self.ratelimit_time,
            mupl_path=self.mupl_path,
            translation=self.translation,
            upload_retry=self.upload_retry,
            cli=self.cli,
        )

        # if not self.http_client.login():
        #     raise MuplException("Initial login failed.")

    @property
    def logs_path(self) -> Path:
        """Get the path to the logs directory."""
        return self.log_folder_path.absolute()

    @property
    def root_path(self) -> Path:
        """Get the path to the uploaded files directory."""
        return self.mupl_path.absolute()

    @property
    def uploaded_files_path(self) -> Path:
        """Get the path to the uploaded files directory."""
        return self.uploaded_files.absolute()

    @property
    def user_path(self) -> Path:
        """Get the path to the uploaded files directory."""
        return self.home_path.absolute()

    def _get_zips_to_upload(
        self,
        upload_dir_path: Path,
        names_to_ids: Dict,
        widestrip: bool,
        combine: bool,
        **kwargs,
    ) -> Tuple[Optional[List[FileProcesser]], List[Path]]:
        """Get a list of files that end with a zip/cbz extension or are folders for uploading."""
        if not isinstance(upload_dir_path, Path):
            upload_dir_path = Path(str(upload_dir_path))

        if not isinstance(names_to_ids, dict):
            names_to_ids = {}

        widestrip = bool(widestrip)
        combine = bool(combine)

        zips_to_upload: List[FileProcesser] = []
        zips_invalid_file_name = []
        zips_no_manga_id = []

        if not upload_dir_path.is_dir():
            logger.error(f"Upload path is not a valid directory: {upload_dir_path}")
            print(
                self.translation.get(
                    "invalid_folder_to_upload", "Invalid upload folder"
                )
            )
            return None, []

        for archive in upload_dir_path.iterdir():
            if archive.name.startswith("."):
                logger.debug(f"Skipping hidden file/folder: {archive.name}")
                continue

            zip_obj = FileProcesser(
                archive,
                names_to_ids,
                self.translation,
                group_fallback_id=self.group_fallback_id,
                number_of_images_upload=self.number_of_images_upload,
                widestrip=widestrip,
                combine=combine,
                **kwargs,
            )
            zip_name_process = zip_obj.process_zip_name()
            if zip_name_process:
                zips_to_upload.append(zip_obj)
                continue

            if zip_obj.zip_name_match is None:
                zips_invalid_file_name.append(archive)
            elif zip_obj.manga_series is None:
                zips_no_manga_id.append(archive)

        zips_to_upload = natsort.os_sorted(zips_to_upload, key=lambda x: x.to_upload)

        if zips_invalid_file_name:
            logger.warning(
                f"Skipping {len(zips_invalid_file_name)} files as they don't match the FILE_NAME_REGEX pattern: {[f for f in zips_invalid_file_name]}"
            )

        if zips_no_manga_id:
            zips_no_manga_id_skip_message = self.translation.get(
                "zips_no_manga_id_skip_message", "Skipping {} files with no manga ID"
            ).format(len(zips_no_manga_id))

            logger.warning(
                f"{zips_no_manga_id_skip_message}: {[f for f in zips_no_manga_id]}"
            )
            print(
                self.translation.get(
                    "zips_no_manga_id_skip_message_logs", "Check logs: {}"
                ).format(zips_no_manga_id_skip_message)
            )

        if not zips_to_upload:
            print(
                self.translation.get(
                    "invalid_folder_to_upload", "Invalid upload folder"
                )
            )
            logger.error(
                f"Exited due to no valid files being found in {upload_dir_path}."
            )
            return None, zips_invalid_file_name + zips_no_manga_id

        logger.debug(
            f"Found valid files/folders to upload: {[str(z) for z in zips_to_upload]}"
        )
        return zips_to_upload, zips_invalid_file_name + zips_no_manga_id

    def _open_manga_series_map(self) -> Dict:
        """Get the manga-name-to-id map."""
        try:
            with open(
                self.name_id_map_path,
                "r",
                encoding="utf-8",
            ) as json_file:
                names_to_ids = json.load(json_file)
                if not isinstance(names_to_ids, dict):
                    logger.warning(
                        "Name-ID map is not a valid dictionary. Creating a new one."
                    )
                    names_to_ids = {"manga": {}, "group": {}}
                if "manga" not in names_to_ids:
                    names_to_ids["manga"] = {}
                if "group" not in names_to_ids:
                    names_to_ids["group"] = {}
                return names_to_ids
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(
                f"Manga/Group Name-ID map file not found at {self.name_id_map_path}. "
            )

            print(
                self.translation.get(
                    "check_file_name_to_id", "Check name-to-ID mapping file"
                )
            )
            return {"manga": {}, "group": {}}

    def _upload_loop(
        self,
        zips_to_upload: List[FileProcesser],
        names_to_ids: Dict[str, str],
        *,
        widestrip: bool,
        combine: bool,
        **kwargs,
    ) -> List[Path]:
        """Internal loop for processing and uploading a list of FileProcesser objects."""
        if not isinstance(zips_to_upload, list):
            logger.error("zips_to_upload must be a list")
            return []

        if not zips_to_upload:
            logger.warning("No files to upload")
            return []

        if not isinstance(names_to_ids, dict):
            names_to_ids = {}

        widestrip = bool(widestrip)
        combine = bool(combine)

        failed_uploads: List[Path] = []
        for index, file_name_obj in enumerate(zips_to_upload, start=1):
            if not isinstance(file_name_obj, FileProcesser):
                logger.warning(
                    f"Skipping invalid file processor object: {file_name_obj}"
                )
                continue

            uploader_process = None
            try:
                print(
                    f"\n\n{self.translation.get('uploading_draft', 'Uploading draft')} {str(file_name_obj)}\n{'-' * 40}"
                )

                uploader_process = ChapterUploader(
                    self.http_client,
                    file_name_obj,
                    names_to_ids,
                    failed_uploads,
                    verbose=self.verbose,
                    mangadex_api_url=self.mangadex_api_url,
                    upload_retry=self.upload_retry,
                    translation=self.translation,
                    number_threads=self.number_threads,
                    uploaded_files=self.uploaded_files,
                    ratelimit_time=self.ratelimit_time,
                    move_files=self.move_files,
                    number_of_images_upload=self.number_of_images_upload,
                    widestrip=widestrip,
                    combine=combine,
                    cli=self.cli,
                    home_path=self.home_path,
                    **kwargs,
                )

                upload_success = uploader_process.upload()
                del uploader_process

                print(
                    f"{'-'*10}\n{self.translation.get('finish_upload', 'Finished upload')} {str(file_name_obj)}\n{'-' * 10}"
                )
                logger.debug("Sleeping between zip upload.")
                time.sleep(self.ratelimit_time * 2)
            except KeyboardInterrupt as e:
                logger.warning(
                    f"Keyboard Interrupt detected during upload of {str(file_name_obj)}"
                )

                print(
                    self.translation.get(
                        "keyboard_interrupt_exit",
                        "Keyboard interrupt detected, exiting",
                    )
                )
                try:
                    asyncio.get_event_loop().stop()
                    asyncio.get_event_loop().close()
                    uploader_process.remove_upload_session()
                    if not uploader_process.folder_upload and uploader_process.myzip:
                        uploader_process.myzip.close()
                    del uploader_process
                except UnboundLocalError:
                    pass
                finally:
                    failed_uploads.append(file_name_obj.to_upload)
                    raise MuplException(e)
            finally:
                if "uploader_process" in locals() and uploader_process is not None:
                    del uploader_process
                    import gc

                    gc.collect()

        if failed_uploads:
            logger.info(f"Failed uploads: {[f.name for f in failed_uploads]}")

            print(self.translation.get("failed_uploads", "Failed uploads"))
            for fail in failed_uploads:
                prefix = (
                    self.translation.get("upload_method_folder", "Folder")
                    if fail.is_dir()
                    else self.translation.get("upload_method_archive", "Archive")
                )

                print("{}: {}".format(prefix, fail.name))

        return failed_uploads

    def upload_directory(
        self,
        upload_dir_path: Union[Path, str],
        *,
        widestrip: bool = False,
        combine: bool = False,
        **kwargs,
    ) -> Optional[List[Path]]:
        """
        Uploads all valid chapter files/folders found in the specified directory.

        Positional Args:
            upload_dir_path: The Path object pointing to the directory containing chapters.

        Keyword Args:
            widestrip: If the chapter is a widestrip. Defaults to False.
            combine: If small images should be combined with other images (either before or after). Defaults to False.

        Returns:
            '*None*' if no valid chapters were found. Otherwise, a list of Path objects for chapters that failed to upload.
        """
        if not upload_dir_path:
            logger.error("upload_dir_path cannot be empty")
            return None

        upload_dir_path = (
            upload_dir_path
            if isinstance(upload_dir_path, Path)
            else Path(str(upload_dir_path))
        )

        widestrip = bool(widestrip)
        combine = bool(combine)

        logger.info(f"Starting batch upload from directory: {upload_dir_path}")

        names_to_ids = self._open_manga_series_map()
        zips_to_upload, invalid_zips = self._get_zips_to_upload(
            upload_dir_path,
            names_to_ids,
            widestrip,
            combine,
            **kwargs,
        )

        if not zips_to_upload:
            return None if not invalid_zips else invalid_zips

        failed_uploads = self._upload_loop(
            zips_to_upload,
            names_to_ids,
            widestrip=widestrip,
            combine=combine,
            **kwargs,
        )
        logger.info(
            f"Finished batch upload from directory: {upload_dir_path}. Failed count: {len(failed_uploads)}"
        )
        return list(set(failed_uploads + invalid_zips))

    def upload_chapter(
        self,
        file_path: Union[Path, str],
        manga_id: str,
        group_ids: Optional[List[str]] = None,
        *,
        language: str = "en",
        oneshot: Optional[bool] = False,
        chapter_number: Optional[str] = None,
        volume_number: Optional[str] = None,
        chapter_title: Optional[str] = None,
        publish_date: Optional[datetime] = None,
        widestrip: bool = False,
        combine: bool = False,
        **kwargs,
    ) -> bool:
        """
        Uploads a single chapter using provided metadata.

        Positional Args:
            file_path: Path to the chapter file (zip/cbz) or folder.
            manga_id: The UUID of the manga series on MangaDex.
            group_ids: A list of UUIDs for the scanlation group(s).

        Keyword Args:
            language: The language code (e.g., 'en', 'es-la'). Defaults to 'en'.
            oneshot: If the chapter is a oneshot (no chapter/volume number). Defaults to False.
            chapter_number: The chapter number (e.g., '10', '10.5'). Ignored if oneshot is True.
            volume_number: The volume number. Optional.
            chapter_title: The title of the chapter. Optional.
            publish_date: A datetime object for scheduled publishing. Optional.
            widestrip: If the chapter is a widestrip. Defaults to False.
            combine: If small images should be combined with other images (either before or after). Defaults to False.

        Returns:
            True if the upload was successful, False otherwise.
        """
        if not file_path:
            logger.error("file_path cannot be empty")
            return False

        file_path = file_path if isinstance(file_path, Path) else Path(str(file_path))

        if not manga_id:
            logger.error("manga_id cannot be empty")
            return False

        try:
            uuid_obj = uuid.UUID(manga_id)
            manga_id = str(uuid_obj)
        except ValueError:
            logger.error(f"Invalid UUID format for manga_id: {manga_id}")
            print(f"Invalid manga ID format: {manga_id}. Must be a valid UUID.")
            return False

        if not group_ids:
            group_ids = []
        elif not isinstance(group_ids, list):
            if isinstance(group_ids, (str, uuid.UUID)):
                group_ids = [str(group_ids)]
            else:
                logger.error(
                    f"Invalid group_ids format: {group_ids}. Must be a list of UUIDs."
                )
                group_ids = []

        validated_group_ids = []
        for group_id in group_ids:
            try:
                uuid_obj = uuid.UUID(group_id)
                validated_group_ids.append(str(uuid_obj))
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid group ID: {group_id}")

        group_ids = validated_group_ids
        language = str(language).lower() if language else "en"
        oneshot = bool(oneshot)
        widestrip = bool(widestrip)
        combine = bool(combine)

        if chapter_number is not None and not oneshot:
            try:
                float(chapter_number)
                chapter_number = str(chapter_number)
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid chapter number: {chapter_number}. Setting to None."
                )
                chapter_number = None

        if volume_number is not None:
            try:
                float(volume_number)
                volume_number = str(volume_number)
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid volume number: {volume_number}. Setting to None."
                )
                volume_number = None

        if chapter_title is not None:
            chapter_title = str(chapter_title)

        if publish_date is not None and not isinstance(publish_date, datetime):
            logger.warning(f"Invalid publish_date: {publish_date}. Setting to None.")
            publish_date = None

        logger.info(f"Starting single chapter upload for: {file_path.name}")
        if not file_path.exists():
            logger.error(f"File or folder not found: {file_path}")
            print(
                self.translation.get(
                    "file_not_found",
                    "File not found: {}",
                ).format(file_path)
            )
            return False

        file_name_obj = FileProcesser(
            file_path,
            names_to_ids={},
            translation=self.translation,
            number_of_images_upload=self.number_of_images_upload,
            widestrip=widestrip,
            combine=combine,
            **kwargs,
        )
        file_name_obj.manga_series = manga_id
        file_name_obj.language = language
        file_name_obj.oneshot = oneshot
        file_name_obj.chapter_number = None if file_name_obj.oneshot else chapter_number
        file_name_obj.volume_number = volume_number
        file_name_obj.groups = group_ids
        file_name_obj.chapter_title = chapter_title
        file_name_obj.publish_date = publish_date
        file_name_obj.to_upload = file_path
        file_name_obj.zip_name = file_path.name
        file_name_obj.zip_extension = file_path.suffix if file_path.is_file() else None

        failed_uploads = self._upload_loop(
            [file_name_obj],
            names_to_ids={},
            widestrip=widestrip,
            combine=combine,
            **kwargs,
        )

        success = not bool(failed_uploads)
        logger.info(
            f"Finished single chapter upload for: {file_path.name}. Success: {success}"
        )
        return success
