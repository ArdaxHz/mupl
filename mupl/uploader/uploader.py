import os
import shutil
import time
import logging
from pathlib import Path

from tqdm import tqdm

from mupl.validators import FileProcessor
from mupl.http.client import HTTPClient
from mupl.uploader.handler import ChapterUploaderHandler
from mupl.status import ProgressTracker, SessionManager

logger = logging.getLogger("mupl")


class ChapterUploader(ChapterUploaderHandler):
    def __init__(
        self,
        http_client: "HTTPClient",
        file_name_obj: "FileProcessor",
        names_to_ids: "dict",
        failed_uploads: "list",
        mangadex_api_url: str,
        upload_retry: int,
        uploaded_files: Path,
        ratelimit_time: int,
        translation: dict,
        verbose: bool,
        move_files: bool,
        number_of_images_upload: int,
        widestrip: bool,
        combine: bool,
        home_path: Path,
        **kwargs,
    ):
        self._progress_tracker = ProgressTracker()
        self._session_manager = SessionManager()
        super().__init__(
            http_client,
            file_name_obj,
            failed_uploads,
            verbose,
            mangadex_api_url,
            upload_retry,
            translation,
            move_files,
            number_of_images_upload,
            widestrip,
            combine,
            home_path,
            **kwargs,
        )
        self.names_to_ids = names_to_ids
        self.uploaded_files = uploaded_files
        self.ratelimit_time = ratelimit_time

        if os.path.isabs(self.uploaded_files):
            self.uploaded_files_path = (
                self.uploaded_files
                if isinstance(self.uploaded_files, Path)
                else Path(self.uploaded_files)
            )
        else:
            self.uploaded_files_path = self.home_path.joinpath(self.uploaded_files)
        self.ratelimit_time = self.ratelimit_time
        self.myzip = self.image_uploader_process.myzip

        chapter_metadata = {
            "manga_series": self.file_name_obj.manga_series,
            "chapter_number": self.file_name_obj.chapter_number,
            "volume_number": self.file_name_obj.volume_number,
            "chapter_title": self.file_name_obj.chapter_title,
            "language": self.file_name_obj.language,
            "groups": self.file_name_obj.groups,
            "publish_date": self.file_name_obj.publish_date,
        }
        self._session_manager.set_chapter_metadata(chapter_metadata)

    def get_current_upload_phase(self) -> str:
        """Get the current phase of the upload process."""
        return self._progress_tracker.get_current_phase()

    def get_images_upload_progress(self) -> dict:
        """Get the progress of image uploads."""
        return self._progress_tracker.get_images_progress()

    def get_upload_session_data(self) -> dict:
        """Get the current upload session data."""
        return self._session_manager.get_session_data()

    def get_chapter_metadata(self) -> dict:
        """Get the chapter metadata."""
        return self._session_manager.get_chapter_metadata()

    def get_upload_errors(self) -> list:
        """Get any upload errors that occurred."""
        return self._progress_tracker.get_errors()

    def update_chapter_metadata(self, **metadata_updates) -> None:
        """Update chapter metadata for dependency usage."""
        valid_fields = {
            "manga_series",
            "chapter_number",
            "volume_number",
            "chapter_title",
            "language",
            "groups",
            "publish_date",
        }

        for field, value in metadata_updates.items():
            if field in valid_fields:
                self._session_manager.update_chapter_metadata(**{field: value})
                # Also update the file processor object if possible
                if hasattr(self.file_name_obj, field):
                    setattr(self.file_name_obj, field, value)
            else:
                logger.warning(f"Invalid metadata field: {field}")

    def move_files(self):
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

        new_uploaded_zip_path = shutil.move(
            self.to_upload,
            os.path.join(self.uploaded_files_path, f"{zip_name}{zip_extension}"),
        )
        logger.debug(f"Moved '{self.to_upload}' to '{new_uploaded_zip_path}'")

    def run_image_uploader(self):
        """Run the image uploader."""
        images_to_upload = self.image_uploader_process.get_images_to_upload()

        for i in range(0, len(images_to_upload), self.number_of_images_upload):
            batch = images_to_upload[i : i + self.number_of_images_upload]
            images_dict = {str(j): data for j, (name, data) in enumerate(batch)}
            failed = self._upload_images(images_dict)
            if failed:
                self.failed_image_upload = True

            if self.failed_image_upload:
                break

    def upload(self):
        """Process the zip for uploading."""
        self._progress_tracker.set_current_phase("validating_images")
        self._session_manager.start_session()
        logger.info(f"Uploading chapter: {repr(self.file_name_obj)}")
        print(
            "Manga id: {manga_series}\n"
            "{chapter_number_manga}: {chapter_number}\n"
            "{volume_number_manga}: {volume_number}\n"
            "{chapter_title_manga}: {chapter_title}\n"
            "{language_manga}: {language}\n"
            "{groups_manga}: {groups}\n"
            "{publish_date_manga}: {publish_date}".format(
                manga_series=self.file_name_obj.manga_series,
                chapter_number=self.file_name_obj.chapter_number,
                volume_number=(
                    self.file_name_obj.volume_number
                    if self.file_name_obj.volume_number is not None
                    else self.translation["not_defined_value"]
                ),
                chapter_title=(
                    self.file_name_obj.chapter_title
                    if self.file_name_obj.chapter_title is not None
                    else self.translation["not_defined_value"]
                ),
                language=self.file_name_obj.language.lower(),
                groups=(
                    self.file_name_obj.groups
                    if self.file_name_obj.groups is not None
                    else self.translation["not_defined_value"]
                ),
                publish_date=(
                    self.file_name_obj.publish_date
                    if self.file_name_obj.publish_date is not None
                    else self.translation["not_defined_value"]
                ),
                chapter_number_manga=self.translation["chapter_number_manga"],
                volume_number_manga=self.translation["volume_number_manga"],
                chapter_title_manga=self.translation["chapter_title_manga"],
                language_manga=self.translation["language_manga"],
                groups_manga=self.translation["groups_manga"],
                publish_date_manga=self.translation["publish_date_manga"],
            )
        )

        if not self.image_uploader_process.valid_images_to_upload:
            self._progress_tracker.set_current_phase("failed_validation")
            error_msg = f"No valid images found for {self.zip_name}"
            self._progress_tracker.add_error(error_msg)
            print(self.translation["invalid_images_to_upload"])
            logger.error(error_msg)
            self.failed_uploads.append(self.to_upload)
            return False

        total_images = len(
            [
                item
                for sublist in self.image_uploader_process.valid_images_to_upload
                for item in sublist
            ]
        )
        self._progress_tracker.set_total_images(total_images)
        self._progress_tracker.set_current_phase("authenticating")
        self.http_client.login()

        self._progress_tracker.set_current_phase("creating_upload_session")
        upload_session_response_json = self._create_upload_session()
        if upload_session_response_json is None:
            self._progress_tracker.set_current_phase("failed_session_creation")
            self._progress_tracker.add_error("Failed to create upload session")
            time.sleep(self.ratelimit_time)
            return False

        self.upload_session_id = upload_session_response_json["data"]["id"]
        session_data = {
            "session_id": self.upload_session_id,
            "created_at": time.time(),
            "chapter_name": self.zip_name,
        }
        self._session_manager.update_session_data(**session_data)

        logger.info(
            f"Created upload session: {self.upload_session_id}, {self.zip_name}."
        )
        print(self.translation["draft_create_session"].format(self.upload_session_id))
        if self.verbose:
            print(
                self.translation["images_to_upload"].format(
                    len(
                        [
                            item
                            for sublist in self.image_uploader_process.valid_images_to_upload
                            for item in sublist
                        ]
                    )
                )
            )

        self._progress_tracker.set_current_phase("uploading_images")
        self.tqdm = tqdm(total=len(self.image_uploader_process.valid_images_to_upload))

        if self.verbose:
            print(self.translation["non_threaded_upload_running"])
        self.run_image_uploader()  # Parameter not used
        if self.failed_image_upload:
            self._progress_tracker.set_current_phase("failed_image_upload")
            self._progress_tracker.add_error("Failed to upload images")

        self.tqdm.close()
        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if self.failed_image_upload:
            self._progress_tracker.set_current_phase("cleaning_up_failed_upload")
            print(self.translation["draft_deleting_failed_upload"])
            logger.error(
                f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            )
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            self._progress_tracker.set_current_phase("failed")
            self._session_manager.end_session()
            return False

        self._progress_tracker.set_current_phase("committing_chapter")
        logger.info("Uploaded all of the chapter's images.")
        commit_chapter_resp = self._commit_chapter()

        if commit_chapter_resp:
            self._progress_tracker.set_current_phase("completed_successfully")
            self._session_manager.end_session()
        else:
            self._progress_tracker.set_current_phase("failed_commit")
            self._progress_tracker.add_error("Failed to commit chapter")
            self._session_manager.end_session()

        return commit_chapter_resp
