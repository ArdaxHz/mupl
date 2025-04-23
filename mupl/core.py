import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import natsort

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.uploader.uploader import ChapterUploader
from mupl.exceptions import MuplException
from mupl.utils.config import load_localisation
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
        mangadex_username: str,
        mangadex_password: str,
        client_id: str,
        client_secret: str,
        cli: bool = False,
        root_path: Path = Path("."),
        translation: Dict = None,
        move_files: bool = True,
        verbose_level: int = 0,
        number_of_images_upload: int = 10,
        upload_retry: int = 3,
        ratelimit_time: int = 2,
        max_log_days: int = 30,
        group_fallback_id: Optional[str] = None,
        number_threads: int = 3,
        language: str = "en",
        name_id_map_file: str = "name_id_map.json",
        uploaded_files: str = "uploaded",
        mangadex_api_url: str = "https://api.mangadex.org",
        mangadex_auth_url: str = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect",
        mdauth_path: str = ".mdauth",
        show_console_message: bool = True,
    ):
        """
        Initializes the Mupl class with explicit parameters.

        Args:
            mangadex_username (str): MangaDex username.
            mangadex_password (str): MangaDex password.
            client_id (str): OAuth client ID.
            client_secret (str): OAuth client secret.
            move_files (bool, optional): Whether to move files after upload. Defaults to True.
            verbose (bool, optional): Whether to print console messages. Defaults to True.
            number_of_images_upload (int): Number of images to upload at once.
            upload_retry (int): Number of retries for failed uploads.
            ratelimit_time (int): Time to wait between API calls.
            max_log_days (int): Maximum number of days to keep logs.
            group_fallback_id (str, optional): Fallback group ID.
            number_threads (int): Number of threads for concurrent uploads.
            language (str): Language for translation file.
            name_id_map_file (str): Path to name-ID mapping file.
            uploaded_files (str): Path to folder for uploaded files.
            mangadex_api_url (str): MangaDex API URL.
            mangadex_auth_url (str): MangaDex auth URL.
            mdauth_path (str): Path to auth token file.
            root_path (Path): Root path of the uploader.
        """
        self.mangadex_username = mangadex_username
        self.mangadex_password = mangadex_password
        self.client_id = client_id
        self.client_secret = client_secret

        self.root_path = root_path
        self.cli = cli
        self.verbose = show_console_message
        self.move_files = move_files
        self.ratelimit_time = ratelimit_time
        self.number_threads = number_threads
        self.number_of_images_upload = number_of_images_upload
        self.max_log_days = max_log_days
        self.group_fallback_id = group_fallback_id
        self.language = language
        self.name_id_map_file = name_id_map_file
        self.uploaded_files = uploaded_files
        self.mangadex_api_url = mangadex_api_url
        self.mangadex_auth_url = mangadex_auth_url
        self.mdauth_path = mdauth_path
        self.upload_retry = upload_retry

        if not self.cli:
            log_folder_path = format_log_dir_path(self.root_path)

            setup_logs(
                logger_name="mupl",
                path=log_folder_path,
                logger_filename="mupl",
                level=verbose_level,
            )

            clear_old_logs(log_folder_path, max_log_days)

        self.translation = translation or load_localisation(self.root_path, language)

        self.http_client = HTTPClient(
            mangadex_username=self.mangadex_username,
            mangadex_password=self.mangadex_password,
            client_id=self.client_id,
            client_secret=self.client_secret,
            mangadex_api_url=self.mangadex_api_url,
            mangadex_auth_url=self.mangadex_auth_url,
            mdauth_path=self.mdauth_path,
            ratelimit_time=self.ratelimit_time,
            root_path=self.root_path,
            translation=self.translation,
            upload_retry=self.upload_retry,
            cli=self.cli,
        )

        if not self.http_client.login():
            raise MuplException("Initial login failed.")

    def _get_zips_to_upload(
        self,
        upload_dir_path: Path,
        names_to_ids: "dict",
        widestrip: bool,
        combine: bool,
        **kwargs,
    ) -> "Optional[List[FileProcesser]]":
        """Get a list of files that end with a zip/cbz extension or are folders for uploading."""
        zips_to_upload: "List[FileProcesser]" = []
        zips_invalid_file_name = []
        zips_no_manga_id = []

        if not upload_dir_path.is_dir():
            logger.error(f"Upload path is not a valid directory: {upload_dir_path}")
            if self.verbose:
                print(
                    self.translation.get(
                        "invalid_folder_to_upload", "Invalid upload folder"
                    )
                )
            return None

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
                "zips_no_manga_id_skip_message", "Skipping {0} files with no manga ID"
            ).format(len(zips_no_manga_id))

            logger.warning(
                f"{zips_no_manga_id_skip_message}: {[f for f in zips_no_manga_id]}"
            )
            if self.verbose:
                print(
                    self.translation.get(
                        "zips_no_manga_id_skip_message_logs", "Check logs: {0}"
                    ).format(zips_no_manga_id_skip_message)
                )

        if not zips_to_upload:
            if self.verbose:
                print(
                    self.translation.get(
                        "invalid_folder_to_upload", "Invalid upload folder"
                    )
                )
            logger.error(
                f"Exited due to no valid files being found in {upload_dir_path}."
            )
            return None

        logger.debug(
            f"Found valid files/folders to upload: {[str(z) for z in zips_to_upload]}"
        )
        return zips_to_upload

    def _open_manga_series_map(self, files_path: "Path") -> "dict":
        """Get the manga-name-to-id map."""

        map_file = files_path.joinpath(self.name_id_map_file)
        try:
            with open(
                map_file,
                "r",
                encoding="utf-8",
            ) as json_file:
                names_to_ids = json.load(json_file)
                if "manga" not in names_to_ids:
                    names_to_ids["manga"] = {}
                if "group" not in names_to_ids:
                    names_to_ids["group"] = {}
                return names_to_ids
        except FileNotFoundError:
            logger.warning(
                f"Manga/Group Name-ID map file not found at {map_file}. Only UUIDs in filenames will work."
            )

            if self.verbose:
                print(
                    self.translation.get(
                        "check_file_name_to_id", "Check name-to-ID mapping file"
                    )
                )
            return {"manga": {}, "group": {}}
        except json.JSONDecodeError:
            logger.exception(
                f"Error decoding JSON from {map_file}. Please check its format."
            )

            if self.verbose:
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
        failed_uploads: "List[Path]" = []
        for index, file_name_obj in enumerate(zips_to_upload, start=1):
            uploader_process = None
            try:
                if self.verbose:
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
                    root_path=self.root_path,
                    **kwargs,
                )

                upload_success = uploader_process.upload()

                if not self.http_client.login():
                    logger.warning(
                        f"Token refresh/check failed after uploading {file_name_obj}. Continuing..."
                    )

                if self.verbose:
                    print(
                        f"{'-'*10}\n{self.translation.get('finish_upload', 'Finished upload')} {str(file_name_obj)}\n{'-' * 10}"
                    )

                if index < len(zips_to_upload):
                    logger.debug("Sleeping between zip upload.")

                    time.sleep(self.ratelimit_time * 2)

            except KeyboardInterrupt:
                logger.warning(
                    f"Keyboard Interrupt detected during upload of {str(file_name_obj)}"
                )

                if self.verbose:
                    print(
                        self.translation.get(
                            "keyboard_interrupt_exit",
                            "Keyboard interrupt detected, exiting",
                        )
                    )
                if uploader_process:
                    try:
                        uploader_process.remove_upload_session()
                        if (
                            not uploader_process.folder_upload
                            and uploader_process.myzip
                        ):
                            uploader_process.myzip.close()
                    except Exception as e:
                        if self.cli:
                            raise e
                    finally:
                        if uploader_process:
                            failed_uploads.append(file_name_obj.to_upload)
                else:
                    if uploader_process:
                        failed_uploads.append(file_name_obj.to_upload)

            except Exception as e:
                logger.exception(
                    f"An unexpected error occurred while processing {str(file_name_obj)}: {e}"
                )
                failed_uploads.append(file_name_obj.to_upload)
                if uploader_process:
                    try:
                        uploader_process.remove_upload_session()
                        if (
                            not uploader_process.folder_upload
                            and uploader_process.myzip
                        ):
                            uploader_process.myzip.close()
                    except Exception as cleanup_e:
                        if self.cli:
                            raise cleanup_e
                    finally:
                        if uploader_process:
                            continue
            finally:
                if "uploader_process" in locals() and uploader_process is not None:
                    del uploader_process
                    import gc

                    gc.collect()

        if failed_uploads:
            logger.info(f"Failed uploads: {[f.name for f in failed_uploads]}")

            if self.verbose:
                print(self.translation.get("failed_uploads", "Failed uploads"))
            for fail in failed_uploads:
                prefix = (
                    self.translation.get("upload_method_folder", "Folder")
                    if fail.is_dir()
                    else self.translation.get("upload_method_archive", "Archive")
                )

                if self.verbose:
                    print("{}: {}".format(prefix, fail.name))

        return failed_uploads

    def upload_directory(
        self,
        upload_dir_path: Path,
        *,
        widestrip: bool,
        combine: bool,
        **kwargs,
    ) -> List[Path]:
        """
        Uploads all valid chapter files/folders found in the specified directory.

        Args:
            upload_dir_path: The Path object pointing to the directory containing chapters.
            **kwargs: Additional arguments like 'threaded', 'combine', 'widestrip'.

        Returns:
            A list of Path objects for chapters that failed to upload.
        """
        logger.info(f"Starting batch upload from directory: {upload_dir_path}")

        names_to_ids = self._open_manga_series_map(self.root_path)

        zips_to_upload = self._get_zips_to_upload(
            upload_dir_path,
            names_to_ids,
            widestrip,
            combine,
            **kwargs,
        )

        if not zips_to_upload:
            logger.warning(
                "No valid chapters found to upload in the specified directory."
            )
            if self.verbose:
                print(
                    self.translation.get(
                        "no_valid_chapters_found",
                        "No valid chapters found to upload in the specified directory.",
                    )
                )
            return []

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
        return failed_uploads

    def upload_chapter(
        self,
        file_path: Path,
        manga_id: str,
        group_ids: List[str],
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

        Args:
            file_path: Path to the chapter file (zip/cbz) or folder.
            manga_id: The UUID of the manga series on MangaDex.
            group_ids: A list of UUIDs for the scanlation group(s).
            language: The language code (e.g., 'en', 'es-la'). Defaults to 'en'.
            oneshot: If the chapter is a oneshot (no chapter/volume number). Defaults to False.
            chapter_number: The chapter number (e.g., '10', '10.5'). Ignored if oneshot is True.
            volume_number: The volume number. Optional.
            chapter_title: The title of the chapter. Optional.
            publish_date: A datetime object for scheduled publishing. Optional.
            **kwargs: Additional arguments like 'threaded', 'combine', 'widestrip'.

        Returns:
            True if the upload was successful, False otherwise.
        """
        logger.info(f"Starting single chapter upload for: {file_path.name}")

        if not file_path.exists():
            logger.error(f"File or folder not found: {file_path}")
            if self.verbose:
                print(
                    self.translation.get(
                        "file_or_folder_not_found",
                        "File or folder not found at {0}",
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
        file_name_obj.language = language.lower() if language else "en"
        file_name_obj.oneshot = bool(oneshot)
        file_name_obj.chapter_number = None if file_name_obj.oneshot else chapter_number
        file_name_obj.volume_number = None if file_name_obj.oneshot else volume_number
        file_name_obj.groups = group_ids if group_ids else []
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
