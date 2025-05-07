import os
import shutil
import time
import asyncio
import logging
from pathlib import Path

from tqdm import tqdm

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.uploader.handler import ChapterUploaderHandler

logger = logging.getLogger("mupl")


class ChapterUploader(ChapterUploaderHandler):
    def __init__(
        self,
        http_client: "HTTPClient",
        file_name_obj: "FileProcesser",
        names_to_ids: "dict",
        failed_uploads: "list",
        mangadex_api_url: str,
        upload_retry: int,
        number_threads: int,
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
        self.number_threads = number_threads
        self.uploaded_files = uploaded_files
        self.ratelimit_time = ratelimit_time
        self.threaded = kwargs.get("threaded", False)
        if self.number_threads <= 1:
            self.threaded = False

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
            print(self.translation["keyboard_interrupt_cancel"])
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
            print(self.translation["invalid_images_to_upload"])
            logger.error(f"No valid images found for {self.zip_name}")
            self.failed_uploads.append(self.to_upload)
            return False

        self.http_client.login()

        upload_session_response_json = self._create_upload_session()
        if upload_session_response_json is None:
            time.sleep(self.ratelimit_time)
            return False

        self.upload_session_id = upload_session_response_json["data"]["id"]

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

        self.tqdm = tqdm(total=len(self.image_uploader_process.info_list))

        if self.threaded:
            if self.verbose:
                print(self.translation["threaded_upload_running"])

            spliced_images_list = [
                self.image_uploader_process.valid_images_to_upload[
                    elem : elem + self.number_threads
                ]
                for elem in range(
                    0,
                    len(self.image_uploader_process.valid_images_to_upload),
                    self.number_threads,
                )
            ]

            for spliced_images in spliced_images_list:
                self.run_threaded_uploader(spliced_images)
                if self.failed_image_upload:
                    break
        else:
            if self.verbose:
                print(self.translation["non_threaded_upload_running"])
            self.run_image_uploader(self.image_uploader_process.valid_images_to_upload)

        self.tqdm.close()
        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if self.failed_image_upload:
            print(self.translation["draft_deleting_failed_upload"])
            logger.error(
                f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            )
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            return False

        logger.info("Uploaded all of the chapter's images.")
        commit_chapter_resp = self._commit_chapter()
        return commit_chapter_resp
