import asyncio
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.uploader.handler import ChapterUploaderHandler
from mupl.utils.config import (
    NUMBER_THREADS,
    VERBOSE,
    config,
    RATELIMIT_TIME,
)

logger = logging.getLogger("md_uploader")


class ChapterUploader(ChapterUploaderHandler):
    def __init__(
        self,
        http_client: "HTTPClient",
        file_name_obj: "FileProcesser",
        names_to_ids: "dict",
        failed_uploads: "list",
        threaded: "bool",
    ):
        super().__init__(http_client, file_name_obj, failed_uploads)
        self.names_to_ids = names_to_ids
        self.threaded = threaded
        if NUMBER_THREADS <= 1:
            self.threaded = False

        self.uploaded_files_path = Path(config["paths"]["uploaded_files"])
        self.ratelimit_time = RATELIMIT_TIME
        self.myzip = self.image_uploader_process.myzip

    @staticmethod
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

    def _move_files(self):
        """Move the uploaded chapters to a different folder."""
        self.uploaded_files_path.mkdir(parents=True, exist_ok=True)
        # Folders don't have an extension
        if self.folder_upload:
            zip_name = self.zip_name
        else:
            zip_name = self.zip_name.rsplit(".", 1)[0]
        zip_extension = self.zip_extension or ""
        zip_path_str = f"{zip_name}{zip_extension}"
        version = 1

        # If a file/folder with that name exists already in the uploaded files path
        # Add a version number to the end before moving
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
        logger.debug(f"Moved {self.to_upload} to {new_uploaded_zip_path}.")

    async def process_images_upload(self, images_array):
        """Start uploading the images, threaded."""
        images_to_upload = self.image_uploader_process.get_images_to_upload(
            images_array
        )
        failed = self._upload_images(images_to_upload)
        if failed:
            self.failed_image_upload = True
            asyncio.get_running_loop().close()

    def run_threaded_uploader(self, spliced_images):
        """Run the threads for upload."""
        tasks = []

        loop = self.create_new_event_loop()
        for images_to_upload in spliced_images:
            task = self.process_images_upload(images_to_upload)
            tasks.append(task)

        gathered = asyncio.gather(*tasks)

        try:
            loop.run_until_complete(gathered)
        except KeyboardInterrupt as e:
            print("Caught keyboard interrupt. Canceling tasks...")
            gathered.cancel()
            self.failed_image_upload = True

    def run_image_uploader(self, images):
        """Run the image mupl ."""
        for images_array in images:
            images_to_upload = self.image_uploader_process.get_images_to_upload(
                images_array
            )
            failed = self._upload_images(images_to_upload)
            if failed:
                self.failed_image_upload = True

            # Don't upload rest of the chapter's images if the images before failed
            if self.failed_image_upload:
                break

            # self.tqdm.update(len(images_to_upload))

    def upload(self):
        """Process the zip for uploading."""
        upload_details = (
            f"Manga id: {self.file_name_obj.manga_series}, "
            f"chapter: {self.file_name_obj.chapter_number}, "
            f"volume: {self.file_name_obj.volume_number}, "
            f"title: {self.file_name_obj.chapter_title}, "
            f"language: {self.file_name_obj.language}, "
            f"groups: {self.file_name_obj.groups}, "
            f"publish on: {self.file_name_obj.publish_date}."
        )
        logger.info(f"Uploading chapter: {upload_details}")
        print(upload_details)

        if not self.image_uploader_process.valid_images_to_upload:
            no_valid_images_found_error_message = (
                f"{self.zip_name} has no valid images to upload, skipping."
            )
            print(no_valid_images_found_error_message)
            logger.error(no_valid_images_found_error_message)
            self.failed_uploads.append(self.to_upload)
            return

        self.http_client.login()

        upload_session_response_json = self._create_upload_session()
        if upload_session_response_json is None:
            time.sleep(self.ratelimit_time)
            return

        self.upload_session_id = upload_session_response_json["data"]["id"]

        upload_session_id_message = (
            f"Created upload session: {self.upload_session_id}, {self.zip_name}."
        )
        logger.info(upload_session_id_message)
        print(upload_session_id_message)
        if VERBOSE:
            print(
                f"{len([item for sublist in self.image_uploader_process.valid_images_to_upload for item in sublist])} images to upload."
            )

        self.tqdm = tqdm(total=len(self.image_uploader_process.info_list))

        if self.threaded:
            if VERBOSE:
                print("Running threaded uploader.")

            spliced_images_list = [
                self.image_uploader_process.valid_images_to_upload[
                    elem : elem + NUMBER_THREADS
                ]
                for elem in range(
                    0,
                    len(self.image_uploader_process.valid_images_to_upload),
                    NUMBER_THREADS,
                )
            ]

            for spliced_images in spliced_images_list:
                self.run_threaded_uploader(spliced_images)
                if self.failed_image_upload:
                    break
        else:
            if VERBOSE:
                print("Running non-threaded uploader.")
            self.run_image_uploader(self.image_uploader_process.valid_images_to_upload)

        self.tqdm.close()
        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if self.failed_image_upload:
            failed_image_upload_message = f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            print(failed_image_upload_message)
            logger.error(failed_image_upload_message)
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            return

        logger.info("Uploaded all of the chapter's images.")
        self._commit_chapter()
