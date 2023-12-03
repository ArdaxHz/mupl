import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List

import natsort

from uploader.file_validator import FileProcesser
from uploader.http.client import HTTPClient
from uploader.updater import check_for_update
from uploader.uploader import ChapterUploader
from uploader.utils.config import config, RATELIMIT_TIME, root_path
from uploader.utils.misc import open_manga_series_map

logger = logging.getLogger("md_uploader")


def get_zips_to_upload(names_to_ids: "dict") -> "Optional[List[FileProcesser]]":
    """Get a list of files that end with a zip/cbz extension for uploading."""
    to_upload_folder_path = Path(config["Paths"]["uploads_folder"])
    zips_to_upload: "List[FileProcesser]" = []
    zips_invalid_file_name = []
    zips_no_manga_id = []

    for archive in to_upload_folder_path.iterdir():
        zip_obj = FileProcesser(archive, names_to_ids)
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
        zips_no_manga_id_skip_message = (
            f"Skipping {len(zips_no_manga_id)} files as they have a missing manga id"
        )
        logger.warning(f"{zips_no_manga_id_skip_message}: {zips_no_manga_id}")
        print(f"{zips_no_manga_id_skip_message}, check the logs for the file names.")

    if not zips_to_upload:
        no_zips_found_error_message = "No valid files found to upload, exiting."
        print(no_zips_found_error_message)
        logger.error(no_zips_found_error_message)
        return

    logger.debug(f"Uploading files: {zips_to_upload}")
    return zips_to_upload


def main(threaded: "bool" = True):
    """Run the uploader on each zip."""
    names_to_ids = open_manga_series_map(root_path)
    zips_to_upload = get_zips_to_upload(names_to_ids)
    if zips_to_upload is None:
        return

    http_client = HTTPClient()
    failed_uploads: "List[Path]" = []

    for index, file_name_obj in enumerate(zips_to_upload, start=1):
        try:
            uploader_process = ChapterUploader(
                http_client, file_name_obj, names_to_ids, failed_uploads, threaded
            )
            uploader_process.start_chapter_upload()
            if not uploader_process.folder_upload:
                uploader_process.myzip.close()

            http_client.login()

            # Delete to save memory on large amounts of uploads
            del uploader_process

            logger.debug("Sleeping between zip upload.")
            time.sleep(RATELIMIT_TIME * 2)
        except KeyboardInterrupt:
            logger.warning("Keyboard Interrupt detected, exiting.")
            print("Keyboard interrupt detected, exiting.")
            try:
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
        print(f"Failed uploads:")
        for fail in failed_uploads:
            prefix = "Folder" if fail.is_dir() else "Archive"
            print(f"{prefix}: {fail.name}")

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
        default=True,
        const=False,
        nargs="?",
        help="Upload the images concurrently.",
    )

    vargs = vars(parser.parse_args())

    if vargs["verbose"] == 0:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    if vargs.get("update", True):
        try:
            updated = check_for_update()
        except (KeyError, PermissionError, TypeError, OSError, ValueError) as e:
            logger.error(f"Update check error: {e}")
            print(f"Not updating.")

    main(vargs["threaded"])
