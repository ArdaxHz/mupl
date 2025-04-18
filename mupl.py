import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import natsort

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.uploader.uploader import ChapterUploader
from mupl.updater import check_for_update
from mupl.utils.config import (
    config,
    RATELIMIT_TIME,
    root_path,
    TRANSLATION,
)
import mupl.utils.config as configM

logger = logging.getLogger("mupl")

__all__ = ["upload_directory", "upload_chapter"]


def _get_zips_to_upload(
    upload_dir_path: Path, names_to_ids: "dict", **kwargs
) -> "Optional[List[FileProcesser]]":
    """Get a list of files that end with a zip/cbz extension or are folders for uploading."""
    zips_to_upload: "List[FileProcesser]" = []
    zips_invalid_file_name = []
    zips_no_manga_id = []

    if not upload_dir_path.is_dir():
        logger.error(f"Upload path is not a valid directory: {upload_dir_path}")
        print(TRANSLATION["invalid_folder_to_upload"])
        return None

    for archive in upload_dir_path.iterdir():
        if archive.name.startswith("."):
            logger.debug(f"Skipping hidden file/folder: {archive.name}")
            continue

        zip_obj = FileProcesser(archive, names_to_ids, **kwargs)
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
            f"Skipping {len(zips_invalid_file_name)} files as they don't match the FILE_NAME_REGEX pattern: {[f.name for f in zips_invalid_file_name]}"
        )

    if zips_no_manga_id:
        zips_no_manga_id_skip_message = TRANSLATION[
            "zips_no_manga_id_skip_message"
        ].format(len(zips_no_manga_id))

        logger.warning(
            f"{zips_no_manga_id_skip_message}: {[f.name for f in zips_no_manga_id]}"
        )
        print(
            TRANSLATION["zips_no_manga_id_skip_message_logs"].format(
                zips_no_manga_id_skip_message
            )
        )

    if not zips_to_upload:
        print(TRANSLATION["invalid_folder_to_upload"])
        logger.error(f"Exited due to no valid files being found in {upload_dir_path}.")
        return None

    logger.debug(
        f"Found valid files/folders to upload: {[str(z) for z in zips_to_upload]}"
    )
    return zips_to_upload


def _open_manga_series_map(files_path: "Path") -> "dict":
    """Get the manga-name-to-id map."""
    map_file = files_path.joinpath(config["paths"]["name_id_map_file"])
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
        print(TRANSLATION["check_file_name_to_id"])
        return {"manga": {}, "group": {}}
    except json.JSONDecodeError:
        logger.exception(
            f"Error decoding JSON from {map_file}. Please check its format."
        )
        print(TRANSLATION["check_file_name_to_id"])
        return {"manga": {}, "group": {}}


def _upload_loop(
    zips_to_upload: List[FileProcesser],
    http_client: HTTPClient,
    names_to_ids: dict,
    **kwargs,
) -> List[Path]:
    """Internal loop for processing and uploading a list of FileProcesser objects."""
    failed_uploads: "List[Path]" = []
    for index, file_name_obj in enumerate(zips_to_upload, start=1):
        uploader_process = None
        try:
            print(
                f"\n\n{TRANSLATION['uploading_draft']} {str(file_name_obj)}\n{'-' * 40}"
            )

            uploader_process = ChapterUploader(
                http_client, file_name_obj, names_to_ids, failed_uploads, **kwargs
            )
            uploader_process.upload()

            if not uploader_process.folder_upload and uploader_process.myzip:
                try:
                    uploader_process.myzip.close()
                except Exception as e:
                    logger.warning(
                        f"Could not close zip file handle for {file_name_obj}: {e}"
                    )

            if not http_client.login():
                logger.warning(
                    f"Token refresh/check failed after uploading {file_name_obj}. Continuing..."
                )

            print(
                f"{'-'*10}\n{TRANSLATION['finish_upload']} {str(file_name_obj)}\n{'-' * 10}"
            )

            if index < len(zips_to_upload):
                logger.debug("Sleeping between zip upload.")
                time.sleep(RATELIMIT_TIME * 2)

        except KeyboardInterrupt:
            logger.warning(
                f"Keyboard Interrupt detected during upload of {str(file_name_obj)}"
            )
            print(TRANSLATION["keyboard_interrupt_exit"])
            if uploader_process:
                try:
                    uploader_process.remove_upload_session()
                    if not uploader_process.folder_upload and uploader_process.myzip:
                        uploader_process.myzip.close()
                except Exception as e:
                    logger.error(f"Error during cleanup after KeyboardInterrupt: {e}")
                finally:
                    failed_uploads.append(file_name_obj.to_upload)
            else:
                failed_uploads.append(file_name_obj.to_upload)

            break
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred while processing {str(file_name_obj)}: {e}"
            )
            failed_uploads.append(file_name_obj.to_upload)
            if uploader_process:
                try:
                    uploader_process.remove_upload_session()
                    if not uploader_process.folder_upload and uploader_process.myzip:
                        uploader_process.myzip.close()
                except Exception as cleanup_e:
                    logger.error(
                        f"Error during cleanup after unexpected error: {cleanup_e}"
                    )
            continue
        finally:
            if "uploader_process" in locals() and uploader_process is not None:
                del uploader_process
                import gc

                gc.collect()

    if failed_uploads:
        logger.info(f"Failed uploads: {[f.name for f in failed_uploads]}")
        print(TRANSLATION["failed_uploads"])
        for fail in failed_uploads:
            prefix = (
                TRANSLATION["upload_method_folder"]
                if fail.is_dir()
                else TRANSLATION["upload_method_archive"]
            )
            print("{}: {}".format(prefix, fail.name))

    return failed_uploads


def upload_directory(upload_dir_path: Path, **kwargs) -> List[Path]:
    """
    Uploads all valid chapter files/folders found in the specified directory.

    Args:
        upload_dir_path: The Path object pointing to the directory containing chapters.
        **kwargs: Additional arguments like 'threaded', 'combine', 'widestrip'.

    Returns:
        A list of Path objects for chapters that failed to upload.
    """
    logger.info(f"Starting batch upload from directory: {upload_dir_path}")
    # Use the private helper function
    names_to_ids = _open_manga_series_map(root_path)
    # Use the private helper function
    zips_to_upload = _get_zips_to_upload(upload_dir_path, names_to_ids, **kwargs)

    if not zips_to_upload:
        logger.warning("No valid chapters found to upload in the specified directory.")
        return []

    http_client = HTTPClient()
    if not http_client.login():
        logger.critical("Initial login failed. Cannot proceed with uploads.")
        # Return the list of files that were intended for upload
        return [zip_obj.to_upload for zip_obj in zips_to_upload]

    failed_uploads = _upload_loop(zips_to_upload, http_client, names_to_ids, **kwargs)
    logger.info(
        f"Finished batch upload from directory: {upload_dir_path}. Failed count: {len(failed_uploads)}"
    )
    return failed_uploads


def upload_chapter(
    file_path: Path,
    manga_id: str,
    group_ids: List[str],
    language: str = "en",
    oneshot: Optional[bool] = False,
    chapter_number: Optional[str] = None,
    volume_number: Optional[str] = None,
    chapter_title: Optional[str] = None,
    publish_date: Optional[datetime] = None,
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
        print(f"Error: File or folder not found at {file_path}")
        return False

    http_client = HTTPClient()
    if not http_client.login():
        logger.critical(f"Login failed. Cannot upload single chapter: {file_path.name}")
        print(f"Error: Login failed, cannot upload {file_path.name}")
        return False

    # Create FileProcesser instance and manually set attributes
    # Pass an empty dict for names_to_ids as it's not needed here
    file_name_obj = FileProcesser(file_path, {}, **kwargs)
    file_name_obj.manga_series = manga_id
    file_name_obj.language = language.lower() if language else "en"
    # Handle oneshot logic correctly
    file_name_obj.oneshot = bool(oneshot)
    file_name_obj.chapter_number = None if file_name_obj.oneshot else chapter_number
    file_name_obj.volume_number = None if file_name_obj.oneshot else volume_number
    file_name_obj.groups = group_ids if group_ids else []
    file_name_obj.chapter_title = chapter_title
    file_name_obj.publish_date = publish_date
    # These are set internally by FileProcesser but good to be explicit for this manual case
    file_name_obj.to_upload = file_path
    file_name_obj.zip_name = file_path.name
    file_name_obj.zip_extension = file_path.suffix if file_path.is_file() else None

    failed_uploads = _upload_loop([file_name_obj], http_client, {}, **kwargs)

    success = not bool(failed_uploads)
    logger.info(
        f"Finished single chapter upload for: {file_path.name}. Success: {success}"
    )
    return success


def main():
    """Parses CLI arguments and initiates the upload process."""
    parser = argparse.ArgumentParser(description="MangaDex Upload Tool")

    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Check for program update before running.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase log verbosity (e.g., -v for DEBUG).",
    )
    parser.add_argument(
        "--threaded",
        "-t",
        action="store_true",
        help="Upload the images concurrently using threads.",
    )
    parser.add_argument(
        "--combine",
        "-c",
        action="store_true",
        help="Combine images less than 120px height with adjacent taller images.",
    )
    parser.add_argument(
        "--widestrip",
        "-w",
        action="store_true",
        help="Treat chapters as widestrip images, splitting based on width.",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Specify the directory to upload from, overriding the config file setting.",
    )

    vargs = vars(parser.parse_args())

    if vargs["verbose"] == 0:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    logger.setLevel(log_level)
    configM.VERBOSE = log_level <= logging.DEBUG

    if vargs.get("update", True):
        try:
            updated = check_for_update()
        except Exception as e:
            logger.exception("Update check failed.")
            print(TRANSLATION["not_updating"])

    if vargs["dir"]:
        upload_directory_path = Path(vargs["dir"])
        if not upload_directory_path.is_dir():
            logger.error(
                f"Provided directory does not exist or is not a directory: {upload_directory_path}"
            )
            print(
                f"Error: Invalid directory provided via --dir: {upload_directory_path}"
            )
            sys.exit(1)
        logger.info(f"Using specified upload directory: {upload_directory_path}")
    else:
        try:
            upload_directory_path = Path(config["paths"]["uploads_folder"])
            logger.info(f"Using upload directory from config: {upload_directory_path}")
        except KeyError:
            logger.error(
                "Upload directory path not found in configuration and --dir not specified."
            )
            print(
                "Error: Upload directory not configured. Specify with --dir or in config.json."
            )
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error accessing config for upload directory: {e}")
            print(f"Error reading upload directory from config: {e}")
            sys.exit(1)

    upload_kwargs = {
        k: v for k, v in vargs.items() if k not in ["update", "verbose", "dir"]
    }

    failed_list = upload_directory(upload_directory_path, **upload_kwargs)
    sys.exit(1 if failed_list else 0)


if __name__ == "__main__":
    main()
