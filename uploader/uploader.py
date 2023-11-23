import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Dict

from uploader.file_validator import FileProcesser
from uploader.http import RequestError
from uploader.http.client import HTTPClient
from uploader.image_validator import ImageProcessor
from uploader.utils.config import config, mangadex_api_url, RATELIMIT_TIME, UPLOAD_RETRY
from uploader.utils.misc import flatten

logger = logging.getLogger("md_uploader")


class ChapterUploader:
    def __init__(
        self,
        http_client: "HTTPClient",
        file_name_obj: "FileProcesser",
        names_to_ids: "dict",
        failed_uploads: "list",
    ):
        self.http_client = http_client
        self.file_name_obj = file_name_obj
        self.to_upload = self.file_name_obj.to_upload
        self.names_to_ids = names_to_ids
        self.failed_uploads = failed_uploads
        self.zip_name = self.to_upload.name
        self.zip_extension = self.to_upload.suffix
        self.folder_upload = False
        # Check if the upload file path is a folder
        if self.to_upload.is_dir():
            self.folder_upload = True
            self.zip_extension = None

        self.uploaded_files_path = Path(config["Paths"]["uploaded_files"])
        self.number_upload_retry = UPLOAD_RETRY
        self.ratelimit_time = RATELIMIT_TIME
        self.md_upload_api_url = f"{mangadex_api_url}/upload"

        # Images to include with chapter commit
        self.images_to_upload_ids: "List[str]" = []
        self.upload_session_id: "Optional[str]" = None
        self.failed_image_upload = False

        self.image_uploader_process = ImageProcessor(
            self.file_name_obj, self.folder_upload
        )
        self.myzip = self.image_uploader_process.myzip

    def _images_upload(self, image_batch: "Dict[str, bytes]"):
        """Upload the images"""
        try:
            image_upload_response = self.http_client.post(
                f"{self.md_upload_api_url}/{self.upload_session_id}",
                files=image_batch,
            )
        except (RequestError,) as e:
            logger.error(e)
            return

        # Some images returned errors
        uploaded_image_data = image_upload_response.data
        successful_upload_data = uploaded_image_data["data"]
        if uploaded_image_data["errors"] or uploaded_image_data["result"] == "error":
            logger.warning(f"Some images errored out.")
            return
        return successful_upload_data

    def _begin_upload_session(self, payload: dict):
        return self.http_client.post(
            f"{self.md_upload_api_url}/begin",
            json=payload,
            tries=1,
        )

    def _commit_upload_session(self, payload: dict):
        return self.http_client.post(
            f"{self.md_upload_api_url}/{self.upload_session_id}/commit", json=payload
        )

    def _upload_images(self, image_batch: "Dict[str, bytes]") -> "bool":
        """Try to upload every 10 (default) images to the upload session."""
        # No images to upload
        if not image_batch:
            return True

        successful_upload_message = "Success: Uploaded page {}, size: {} MB."

        image_batch_list = list(image_batch.keys())
        print(
            f"Uploading images {int(image_batch_list[0]) + 1} to {int(image_batch_list[-1]) + 1}."
        )
        logger.debug(
            f"Uploading images {int(image_batch_list[0]) + 1} to {int(image_batch_list[-1]) + 1}."
        )

        for retry in range(self.number_upload_retry):
            successful_upload_data = self._images_upload(image_batch)

            if successful_upload_data is None:
                print(
                    f"Image upload error for {int(image_batch_list[0]) + 1} to {int(image_batch_list[-1]) + 1}, try {retry + 1}/{self.number_upload_retry}."
                )
                if retry == self.number_upload_retry - 1:
                    return True
                continue

            # Add successful image uploads to the image ids array
            for uploaded_image in successful_upload_data:
                if successful_upload_data.index(uploaded_image) == 0:
                    logger.debug(f"Success: Uploaded images {successful_upload_data}")

                uploaded_image_attributes = uploaded_image["attributes"]
                uploaded_filename = uploaded_image_attributes["originalFileName"]
                file_size = uploaded_image_attributes["fileSize"]

                self.images_to_upload_ids.insert(
                    int(uploaded_filename), uploaded_image["id"]
                )
                original_filename = self.image_uploader_process.images_to_upload_names[
                    uploaded_filename
                ]
                converted_format = self.image_uploader_process.converted_images.get(
                    original_filename
                )
                formatted_name_message = original_filename
                if converted_format is not None:
                    formatted_name_message += f" (converted to {converted_format})"

                print(
                    successful_upload_message.format(
                        formatted_name_message, round(file_size * 0.00000095367432, 2)
                    )
                )

            # Length of images array returned from the api is the same as the array sent to the api
            if len(successful_upload_data) == len(image_batch):
                logger.info(
                    f"Uploaded images {int(image_batch_list[0]) + 1} to {int(image_batch_list[-1]) + 1}."
                )
                return False
            else:
                # Update the images to upload dictionary with the images that failed
                image_batch = {
                    k: v
                    for (k, v) in image_batch.items()
                    if k
                    not in [
                        i["attributes"]["originalFileName"]
                        for i in successful_upload_data
                    ]
                }
                logger.warning(
                    f"Some images didn't upload, retrying. Failed images: {image_batch}"
                )
                self.failed_image_upload = True
                continue

        return True

    def remove_upload_session(self, session_id: "Optional[str]" = None):
        """Delete the upload session."""
        if session_id is None:
            session_id = self.upload_session_id

        if session_id is None:
            logger.warning(f"Tried to delete upload session, but no session id found.")
            return

        try:
            self.http_client.delete(
                f"{self.md_upload_api_url}/{session_id}", successful_codes=[404]
            )
        except (RequestError,) as e:
            logger.error(f"Couldn't delete {session_id}: {e}")
        else:
            logger.debug(f"Sent {session_id} to be deleted.")

    def _delete_exising_upload_session(self):
        """Remove any exising upload sessions to not error out as mangadex only allows one upload session at a time."""
        try:
            existing_session = self.http_client.get(
                f"{mangadex_api_url}/upload", successful_codes=[404]
            )
        except (RequestError,) as e:
            logger.error(e)
        else:
            if existing_session.response.ok:
                logger.debug(f"Existing session: {existing_session.data}")
                self.remove_upload_session(existing_session.data["data"]["id"])
                return

            elif existing_session.status_code == 404:
                logger.debug("No existing upload session found.")
                return

        logger.error("Exising upload session not deleted.")
        raise Exception(f"Couldn't delete existing upload session.")

    def _create_upload_session(self) -> "Optional[dict]":
        """Try create an upload session 3 times."""
        payload = {
            "manga": self.file_name_obj.manga_series,
            "groups": self.file_name_obj.groups,
        }

        try:
            self._delete_exising_upload_session()
        except Exception as e:
            logger.error(e)
        else:
            # Start the upload session
            try:
                upload_session_response = self._begin_upload_session(payload)
            except (RequestError,) as e:
                logger.error(e)
            else:
                if upload_session_response.ok:
                    return upload_session_response.data

        # Couldn't create an upload session, skip the chapter
        upload_session_response_json_message = (
            f"Couldn't create an upload session for {self.zip_name}."
        )
        logger.error(upload_session_response_json_message)
        print(upload_session_response_json_message)
        self.failed_uploads.append(self.to_upload)
        return

    def _commit_chapter(self) -> "bool":
        """Try commit the chapter to mangadex."""
        payload = {
            "chapterDraft": {
                "volume": self.file_name_obj.volume_number,
                "chapter": self.file_name_obj.chapter_number,
                "title": self.file_name_obj.chapter_title,
                "translatedLanguage": self.file_name_obj.language,
            },
            "pageOrder": self.images_to_upload_ids,
        }

        if self.file_name_obj.publish_date is not None:
            payload["chapterDraft"][
                "publishAt"
            ] = f"{self.file_name_obj.publish_date.strftime('%Y-%m-%dT%H:%M:%S')}"

        try:
            chapter_commit_response = self._commit_upload_session(payload)
        except (RequestError,) as e:
            logger.error(e)
        else:
            if chapter_commit_response.ok:
                successful_upload_id = chapter_commit_response.data["data"]["id"]
                print(
                    f"Successfully uploaded: {successful_upload_id}, {self.zip_name}."
                )
                logger.info(
                    f"Successful commit: {successful_upload_id}, {self.zip_name}."
                )
                self._move_files()
                return True

        commit_error_message = (
            f"Failed to commit {self.zip_name}, removing upload draft."
        )
        logger.error(commit_error_message)
        print(commit_error_message)
        self.remove_upload_session()
        self.failed_uploads.append(self.to_upload)
        return False

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

    def start_chapter_upload(self):
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
        print(
            f"{len(flatten(self.image_uploader_process.valid_images_to_upload))} images to upload."
        )

        for images_array in self.image_uploader_process.valid_images_to_upload:
            images_to_upload = self.image_uploader_process.get_images_to_upload(
                images_array
            )
            failed = self._upload_images(images_to_upload)
            if failed:
                self.failed_image_upload = True

            # Don't upload rest of the chapter's images if the images before failed
            if self.failed_image_upload:
                break

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
