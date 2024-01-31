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
        
        if len(self.to_upload.parts) > 3:
            parts = self.to_upload.parts
            index_to_upload = parts.index('to_upload')
            parts = parts[index_to_upload:]

            idiom = None
            obra = None
            group = None
            volume = None
            chapter = None
            title = None
            data = None

            idiom = parts[1] # Language
            obra = parts[2] # Project name
            group = parts[3] # Group scan
            
            if parts[4].startswith("v"):
                volume = parts[4][1:].strip() # Volume (without 'v')
                
                chapter = parts[5] # Chapter
                
                if len(parts) == 7:
                    title = parts[6] # Title
                    data_position = title.find("{")  # Encontrar a posição inicial da chave {
    
                    if data_position != -1:
                        data_part = title[data_position:].strip()  # Texto da chave { até o final
                        data_part = data_part.rstrip("}").replace("{", "")  # Remover a chave } do final
                        title = title[:data_position].strip()  # Texto antes da chave {

                    data = data_part if data_position != -1 else None
            
            else:
                chapter = parts[4] # Chapter
                
                if len(parts) == 6:
                    title = parts[5] # Title
                    data_position = title.find("{")  # Encontrar a posição inicial da chave {
    
                    if data_position != -1:
                        data_part = title[data_position:].strip()  # Texto da chave { até o final
                        data_part = data_part.rstrip("}").replace("{", "")  # Remover a chave } do final
                        title = title[:data_position].strip()  # Texto antes da chave {

                    data = data_part if data_position != -1 else None
            
            volume_text = f"(v{volume})" if volume else ""
            title_text = f"({title})" if title else ""
            group_text = f"[{group}]" if group else ""
            text = f"{obra} {idiom} - c{chapter} {volume_text} {title_text} {group_text}"
            
            new_uploaded_zip_path = self.to_upload.rename(
                os.path.join(self.uploaded_files_path, f"{text}")
            )
            logger.debug(f"Moved {self.to_upload} to {new_uploaded_zip_path}.")
            
            def delete_empty_folders(folder_path):
                # Percorre recursivamente a árvore de diretórios
                for root, dirs, files in os.walk(folder_path, topdown=False):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        
                        # Verifica se a pasta está vazia
                        if not os.listdir(dir_path):
                            # Exclui a pasta vazia
                            os.rmdir(dir_path)
            
            delete_empty_folders("to_upload")
        
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
            print(translate_message['uploader_text_1'])
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
            "{uploader_text_2}: {chapter_number}\n"
            "{uploader_text_3}: {volume_number}\n"
            "{uploader_text_4}: {chapter_title}\n"
            "{uploader_text_5}: {language}\n"
            "{uploader_text_6}: {groups}\n"
            "{uploader_text_7}: {publish_date}".format(
                manga_series=self.file_name_obj.manga_series,
                chapter_number=self.file_name_obj.chapter_number,
                volume_number=self.file_name_obj.volume_number if self.file_name_obj.volume_number is not None else translate_message['uploader_text_14'],
                chapter_title=self.file_name_obj.chapter_title if self.file_name_obj.chapter_title is not None else translate_message['uploader_text_14'],
                language=self.file_name_obj.language.upper(),
                groups=self.file_name_obj.groups if self.file_name_obj.groups is not None else translate_message['uploader_text_14'],
                publish_date=self.file_name_obj.publish_date if self.file_name_obj.publish_date is not None else translate_message['uploader_text_14'],
                uploader_text_2=translate_message["uploader_text_2"],
                uploader_text_3=translate_message["uploader_text_3"],
                uploader_text_4=translate_message["uploader_text_4"],
                uploader_text_5=translate_message["uploader_text_5"],
                uploader_text_6=translate_message["uploader_text_6"],
                uploader_text_7=translate_message["uploader_text_7"]
            )
        )

        if not self.image_uploader_process.valid_images_to_upload:
            print(translate_message['uploader_text_8'])
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
        print(f"{translate_message['uploader_text_9']}".format(self.upload_session_id))
        if VERBOSE:
            print(
                f"{translate_message['uploader_text_10']}".format(
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
                print(translate_message['uploader_text_11'])

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
                print(translate_message['uploader_text_12'])
            self.run_image_uploader(self.image_uploader_process.valid_images_to_upload)

        self.tqdm.close()
        if not self.folder_upload:
            self.myzip.close()

        # Skip chapter upload and delete upload session
        if self.failed_image_upload:
            print(translate_message['uploader_text_13'])
            logger.error(
                f"Deleting draft due to failed image upload: {self.upload_session_id}, {self.zip_name}."
            )
            self.remove_upload_session()
            self.failed_uploads.append(self.to_upload)
            return

        logger.info("Uploaded all of the chapter's images.")
        self._commit_chapter()
