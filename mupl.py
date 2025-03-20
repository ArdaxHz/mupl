import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Optional, List

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


def get_zips_to_upload(
    names_to_ids: "dict", **kwargs
) -> "Optional[List[FileProcesser]]":
    """Get a list of files that end with a zip/cbz extension for uploading."""
    to_upload_folder_path = Path(config["paths"]["uploads_folder"])
    zips_to_upload: "List[FileProcesser]" = []
    zips_invalid_file_name = []
    zips_no_manga_id = []

    for archive in to_upload_folder_path.iterdir():
        zip_obj = FileProcesser(archive, names_to_ids, **kwargs)
        zip_name_process = zip_obj.process_zip_name()
        if zip_name_process:
            zips_to_upload.append(zip_obj)

        if zip_obj.zip_name_match is None:
            zips_invalid_file_name.append(archive)

        if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
            zips_no_manga_id.append(archive)

    # Sort the array to mirror your system's file explorer
    zips_to_upload = natsort.os_sorted(zips_to_upload, key=lambda x: x.to_upload)

    if zips_invalid_file_name:
        logger.warning(
            f"Skipping {len(zips_invalid_file_name)} files as they don't match the FILE_NAME_REGEX pattern: {zips_invalid_file_name}"
        )

    if zips_no_manga_id:
        zips_no_manga_id_skip_message = TRANSLATION[
            "zips_no_manga_id_skip_message"
        ].format(len(zips_no_manga_id))

        logger.warning(f"{zips_no_manga_id_skip_message}: {zips_no_manga_id}")
        print(
            TRANSLATION["zips_no_manga_id_skip_message_logs"].format(
                zips_no_manga_id_skip_message
            )
        )

    if not zips_to_upload:
        print(TRANSLATION["invalid_folder_to_upload"])
        logger.error(f"Exited due to {len(zips_to_upload)} zips not being valid.")
        return

    logger.debug(f"Uploading files: {zips_to_upload}")
    return zips_to_upload


def open_manga_series_map(files_path: "Path") -> "dict":
    """Get the manga-name-to-id map."""
    try:
        with open(
            files_path.joinpath(config["paths"]["name_id_map_file"]),
            "r",
            encoding="utf-8",
        ) as json_file:
            names_to_ids = json.load(json_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.exception("Please check your name-to-id file.")
        print(TRANSLATION["check_file_name_to_id"])
        return {"manga": {}, "group": {}}
    return names_to_ids


def main(**kwargs):
    """Run the mupl on each zip."""
    names_to_ids = open_manga_series_map(root_path)
    zips_to_upload = get_zips_to_upload(names_to_ids)
    if zips_to_upload is None:
        return

    http_client = HTTPClient()
    failed_uploads: "List[Path]" = []

    for index, file_name_obj in enumerate(zips_to_upload, start=1):
        try:
            print(
                f"\n\n{TRANSLATION['uploading_draft']} {str(file_name_obj)}\n{'-' * 40}"
            )

            uploader_process = ChapterUploader(
                http_client, file_name_obj, names_to_ids, failed_uploads, **kwargs
            )
            uploader_process.upload()
            if not uploader_process.folder_upload:
                uploader_process.myzip.close()

            http_client.login()

            # Delete to save memory on large amounts of uploads
            del uploader_process

            print(
                f"{'-'*10}\n{TRANSLATION['finish_upload']} {str(file_name_obj)}\n{'-' * 10}"
            )
            logger.debug("Sleeping between zip upload.")
            time.sleep(RATELIMIT_TIME * 2)
        except KeyboardInterrupt:
            logger.warning(
                f"Keyboard Interrupt detected during upload of {str(file_name_obj)}"
            )
            print(TRANSLATION["keyboard_interrupt_exit"])
            try:
                asyncio.get_event_loop().stop()
                asyncio.get_event_loop().close()
                uploader_process.remove_upload_session()
                if not uploader_process.folder_upload:
                    uploader_process.myzip.close()
                del uploader_process
            except UnboundLocalError:
                pass
            else:
                failed_uploads.append(file_name_obj.to_upload)
            break

    if failed_uploads:
        logger.info(f"Failed uploads: {failed_uploads}")
        print(TRANSLATION["failed_uploads"])
        for fail in failed_uploads:
            prefix = (
                TRANSLATION["upload_method_folder"]
                if fail.is_dir()
                else TRANSLATION["upload_method_archive"]
            )
            print("{}: {}".format(prefix, fail.name))

    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--update",
        "-u",
        default=True,
        const=False,
        nargs="?",
        help="Check for program update.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Log verbosity.",
    )
    parser.add_argument(
        "--threaded",
        "-t",
        default=False,
        const=True,
        nargs="?",
        help="Upload the images concurrently.",
    )
    parser.add_argument(
        "--combine",
        "-c",
        default=False,
        const=True,
        nargs="?",
        help="Combine images less than 120px with images that are taller.",
    )
    parser.add_argument(
        "--widestrip",
        "-w",
        default=False,
        const=True,
        nargs="?",
        help="Chapters uploaded have widestrip images, so split based on width.",
    )

    vargs = vars(parser.parse_args())

    if vargs["verbose"] == 0:
        logger.setLevel(logging.INFO)
        configM.VERBOSE = False
    else:
        configM.VERBOSE = True
        logger.setLevel(logging.DEBUG)

    if vargs.get("update", True):
        try:
            updated = check_for_update()
        except (KeyError, PermissionError, TypeError, OSError, ValueError) as e:
            logger.exception("Update check the error stack")
            print(TRANSLATION["not_updating"])

    main(**vargs)
