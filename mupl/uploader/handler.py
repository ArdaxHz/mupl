import logging
from pathlib import Path
from typing import List, Optional, Dict

from mupl.file_validator import FileProcesser
from mupl.exceptions import MuplUploadSessionError
from mupl.http import RequestError
from mupl.http.client import HTTPClient
from mupl.image_validator import ImageProcessor


logger = logging.getLogger("mupl")


class ChapterUploaderHandler:
    def __init__(
        self,
        http_client: "HTTPClient",
        file_name_obj: "FileProcesser",
        failed_uploads: "list",
        verbose: bool,
        mangadex_api_url: str,
        upload_retry: int,
        translation: dict,
        move_files: bool,
        number_of_images_upload: int,
        widestrip: bool,
        combine: bool,
        home_path: Path,
        **kwargs,
    ):
        self.http_client = http_client
        self.file_name_obj = file_name_obj
        self.to_upload = self.file_name_obj.to_upload
        self.failed_uploads = failed_uploads
        self.move_files_after_upload = move_files
        self.verbose = verbose
        self.mangadex_api_url = mangadex_api_url
        self.number_upload_retry = upload_retry
        self.translation = translation
        self.combine = combine
        self.widestrip = widestrip
        self.number_of_images_upload = number_of_images_upload
        self.zip_name = self.to_upload.name
        self.zip_extension = self.to_upload.suffix
        self.folder_upload = False
        self.home_path = home_path

        if self.to_upload.is_dir():
            self.folder_upload = True
            self.zip_extension = None

        self.md_upload_api_url = f"{self.mangadex_api_url}/upload"

        self.images_to_upload_ids: "List[str]" = []
        self.upload_session_id: "Optional[str]" = None
        self.failed_image_upload = False

        self.image_uploader_process = ImageProcessor(
            self.to_upload,
            self.folder_upload,
            translation=self.translation,
            number_of_images_upload=self.number_of_images_upload,
            widestrip=self.widestrip,
            combine=self.combine,
            **kwargs,
        )

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
        if not image_batch:
            return True

        image_batch_list = list(image_batch.keys())
        batch_start = int(image_batch_list[0]) + 1
        batch_end = int(image_batch_list[-1]) + 1
        logger.debug(f"Uploading images {batch_start} to {batch_end}.")

        if self.verbose:
            print(self.translation["uploading_images"].format(batch_start, batch_end))

        for retry in range(self.number_upload_retry):
            successful_upload_data = self._images_upload(image_batch)

            if successful_upload_data is None:
                print(
                    self.translation["uploading_images_error"].format(
                        batch_start,
                        batch_end,
                        retry + 1,
                        self.number_upload_retry,
                    )
                )
                if retry == self.number_upload_retry - 1:
                    return True
                continue

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

                if self.verbose:
                    print(
                        self.translation["successful_upload_message"].format(
                            formatted_name_message,
                            round(file_size * 0.00000095367432, 2),
                        )
                    )

            if len(successful_upload_data) == len(image_batch):
                logger.info(
                    f"Uploaded images {int(image_batch_list[0]) + 1} to {int(image_batch_list[-1]) + 1}."
                )
                self.tqdm.update(len(image_batch_list))
                return False
            else:
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
                f"{self.mangadex_api_url}/upload", successful_codes=[404]
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
        raise MuplUploadSessionError(f"Couldn't delete existing upload session.")

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
            try:
                upload_session_response = self._begin_upload_session(payload)
            except (RequestError,) as e:
                logger.error(e)
            else:
                if upload_session_response.ok:
                    return upload_session_response.data

        logger.error("Couldn't create an upload session for {}.".format(self.zip_name))
        print(self.translation["error_create_draft_session"].format(self.zip_name))
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
                    self.translation["uploading_successfully"].format(
                        successful_upload_id, self.zip_name
                    )
                )
                logger.info(
                    f"Successful commit: {successful_upload_id}, {self.zip_name}."
                )

                if self.move_files_after_upload:
                    self.move_files()
                return True

        logger.error(f"Failed to commit {self.zip_name}, removing upload draft.")
        print(self.translation["uploading_failed"].format(self.zip_name))
        self.remove_upload_session()
        self.failed_uploads.append(self.to_upload)
        return False
