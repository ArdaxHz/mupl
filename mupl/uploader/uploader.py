import os
import time
import asyncio
import logging
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
    translate_message
)

logger = logging.getLogger("mupl")


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

    def move_files(self):
        """Move the uploaded chapters to a different folder."""
        to_upload_folder_path = Path(config["paths"]["uploads_folder"])
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
        
        def check_to_upload_metod(parts):
            # Define the variables
            language = None
            manga_series = None
            groups = None
            volume_number = None
            chapter_number = None
            chapter_title = None
            
            language = parts[1] # Language
            manga_series = parts[2] # Project name
            groups = parts[3] # Group scan
            
            def volume_number_or_chapter_number(parts):
                volume_number = parts[4][1:].strip() # Volume (without 'v')
                volume_number = volume_number.lstrip('0')
                
                chapter_number = str(parts[5]) # Chapter
                
                # Check if the value is "0000", if so, it's a oneshot
                if chapter_number == "0000":
                    chapter_number = None
                    self.oneshot = True
                else:
                    # Remove all leading zeros
                    chapter_number = chapter_number.lstrip('0')
                    
                return volume_number, chapter_number

            def only_chapter_number(parts):
                # Since there is no Volume part, part 4 is the Chapter.
                chapter_number = parts[4] # Chapter
                
                # Check if the value is "0000", if so, it's a oneshot
                if chapter_number == "0000":
                    chapter_number = None
                    self.oneshot = True
                
                return chapter_number
            
            def chapter_title_and_publish_date(parts, number):
                chapter_title = parts[number] # Title
                return chapter_title
            
            # Check if part 4 (Volume or Chapter) starts with "v" to consider it as Volume
            if parts[4].startswith("v"):
                volume_number, chapter_number = volume_number_or_chapter_number(parts)
                
                # If there are a total of 7 parts (counting "to_upload"), part 6 is the title
                if len(parts) == 7:
                    chapter_title = chapter_title_and_publish_date(parts, 6)
            
            else:
                chapter_number = only_chapter_number(parts)
                
                # If there are a total of 6 parts (counting "to_upload"), part 5 is the title
                if len(parts) == 6:
                    chapter_title = chapter_title_and_publish_date(parts, 5)
                
            return language, manga_series, groups, volume_number, chapter_number, chapter_title

        # Retrieve the parts from "to_upload" and remove everything before "to_upload"
        index_to_upload = self.to_upload.parts.index('to_upload')
        parts = self.to_upload.parts[index_to_upload:]

        # Check the number of parts to determine the method used. If it's 2,
        # use the normal method; if it's more than 3, use the tree method
        if len(parts) > 3:
            language, manga_series, groups, volume_number, chapter_number, chapter_title = check_to_upload_metod(parts)
            
            chapter_number = f"c{chapter_number}" if chapter_number else ""
            volume_number = f" (v{volume_number})" if volume_number else ""
            chapter_title = f" ({chapter_title})" if chapter_title else ""
            groups = f" [{groups}]" if groups else "[0]"
            
            text = f"{manga_series} {language} - {chapter_number}{volume_number}{chapter_title}{groups}"
            
            try:
                new_uploaded_zip_path = self.to_upload.rename(
                    os.path.join(self.uploaded_files_path, f"{text}")
                )
                logger.debug(f"Moved {self.to_upload} to {new_uploaded_zip_path}.")
            except:
                print("File already exists: " + text)
        
            def delete_empty_folders(folder_path):
                # Recursively traverse the directory tree
                for root, dirs, files in os.walk(folder_path, topdown=False):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        
                        # Check if the folder is empty
                        if not os.listdir(dir_path):
                            # Delete the empty folder
                            os.rmdir(dir_path)

            delete_empty_folders(to_upload_folder_path)
            
        else:
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
            print(translate_message['keyboard_interrupt_cancel'])
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
                volume_number=self.file_name_obj.volume_number if self.file_name_obj.volume_number is not None else translate_message['not_defined_value'],
                chapter_title=self.file_name_obj.chapter_title if self.file_name_obj.chapter_title is not None else translate_message['not_defined_value'],
                language=self.file_name_obj.language.upper(),
                groups=self.file_name_obj.groups if self.file_name_obj.groups is not None else translate_message['not_defined_value'],
                publish_date=self.file_name_obj.publish_date if self.file_name_obj.publish_date is not None else translate_message['not_defined_value'],
                chapter_number_manga=translate_message["chapter_number_manga"],
                volume_number_manga=translate_message["volume_number_manga"],
                chapter_title_manga=translate_message["chapter_title_manga"],
                language_manga=translate_message["language_manga"],
                groups_manga=translate_message["groups_manga"],
                publish_date_manga=translate_message["publish_date_manga"]
            )
        )

        if not self.image_uploader_process.valid_images_to_upload:
            print(translate_message['invalid_images_to_upload'])
            logger.error(f"No valid images found for {self.zip_name}")
            self.failed_uploads.append(self.to_upload)
            return

        self.http_client.login()

        upload_session_response_json = self._create_upload_session()
        if upload_session_response_json is None:
            time.sleep(self.ratelimit_time)
            return

        self.upload_session_id = upload_session_response_json["data"]["id"]

        logger.info(
            "Created upload session: {self.upload_session_id}, {self.zip_name}."
        )
        print(f"{translate_message['draft_create_session']}".format(self.upload_session_id))
        if VERBOSE:
            print(
                f"{translate_message['images_to_upload']}".format(
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
            if VERBOSE:
                print(translate_message['threaded_upload_runing'])

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
                print(translate_message['threaded_upload_non_runing'])
            self.run_image_uploader(self.image_uploader_process.valid_images_to_upload)

        self.tqdm.close()
        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if self.failed_image_upload:
            print(translate_message['draft_deleting_failed_uplaod'])
            logger.error(
                f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            )
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            return

        logger.info("Uploaded all of the chapter's images.")
        self._commit_chapter()
