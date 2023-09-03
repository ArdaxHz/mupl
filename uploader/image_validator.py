import enum
import io
import logging
import string
import zipfile
from pathlib import Path
from typing import List, Dict, Union, Literal, Optional

import natsort
from PIL import Image

from uploader.file_validator import FileProcesser
from uploader.utils.config import NUMBER_OF_IMAGES_UPLOAD
from uploader.utils.converter import get_new_format_for_webp

logger = logging.getLogger("md_uploader")


class Format(enum.Enum):
    PNG = 0
    JPG = 1
    GIF = 2

    # Converted to one of the md supported format
    WEBP = 4


class ImageProcessor:
    def __init__(self, file_name_obj: "FileProcesser", folder_upload: "bool") -> None:
        self.file_name_obj = file_name_obj
        self.to_upload = self.file_name_obj.to_upload
        self.folder_upload = folder_upload

        self.myzip = None
        if not self.folder_upload:
            self.myzip = self._read_zip()

        # Spliced list of lists
        self.valid_images_to_upload: "List[List[str]]" = []
        # Renamed file to original file name
        self.images_to_upload_names: "Dict[str, str]" = {}
        self.converted_images: "Dict[str, str]" = {}

        self.images_upload_session = NUMBER_OF_IMAGES_UPLOAD

        self.info_list = self._get_valid_images()

    def _key(self, x: "str") -> "Union[Literal[0], str]":
        """Give a higher priority in sorting for images with their first character a punctuation."""
        if Path(x).name[0].lower() in string.punctuation:
            return 0
        else:
            return x

    def _read_image_data(self, image: "str") -> "bytes":
        """Read the image data from the zip or from the folder."""
        if self.folder_upload:
            image_path = self.to_upload.joinpath(image)
            return image_path.read_bytes()
        else:
            with self.myzip.open(image) as myfile:
                return myfile.read()

    def _read_zip(self) -> "zipfile.ZipFile":
        """Open zip file in read only mode."""
        return zipfile.ZipFile(self.to_upload)

    @staticmethod
    def _get_image_format(image_bytes: "bytes") -> "Optional[Format]":
        """Returns the image type from the first few bytes."""
        if image_bytes.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
            return Format.PNG

        if image_bytes[0:3] == b"\xff\xd8\xff" or image_bytes[6:10] in (
            b"JFIF",
            b"Exif",
        ):
            return Format.JPG

        if image_bytes.startswith(
            (b"\x47\x49\x46\x38\x37\x61", b"\x47\x49\x46\x38\x39\x61")
        ):
            return Format.GIF

        if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            return Format.WEBP

        return None

    def _is_image_valid(self, image: "str") -> "bool":
        return self._get_image_format(self._read_image_data(image)) is not None

    def _get_bytes_for_upload(self, image: "str") -> bytes:
        image_bytes = self._read_image_data(image)
        current_format = self._get_image_format(image_bytes)
        new_format = None
        if current_format == Format.WEBP:
            new_format = get_new_format_for_webp(image_bytes)

        if not new_format:
            return image_bytes

        self.converted_images.update({image: new_format})
        logger.info(f"Converted {image} into {new_format}")
        with Image.open(io.BytesIO(image_bytes)) as image:
            output = io.BytesIO()
            image.save(output, new_format)
            return output.getvalue()

    def _get_valid_images(self):
        """Validate the files in the archive.
        Check if all the files are images.
        Sorts the images using natural sort."""
        if self.folder_upload:
            to_iter = [x.name for x in self.to_upload.iterdir()]
        else:
            to_iter = [x.filename for x in self.myzip.infolist()]

        info_list = [image for image in to_iter if self._is_image_valid(image)]
        info_list_images_only = natsort.natsorted(info_list, key=self._key)

        self.valid_images_to_upload = [
            info_list_images_only[l : l + self.images_upload_session]
            for l in range(0, len(info_list_images_only), self.images_upload_session)
        ]
        logger.info(f"Images to upload: {self.valid_images_to_upload}")
        return info_list_images_only

    def get_images_to_upload(self, images_to_read: "List[str]") -> "Dict[str, bytes]":
        """Read the image data from the zip as list."""
        logger.info(f"Reading data for images: {images_to_read}")
        # Dictionary to store the image index to the image bytes
        files: "Dict[str, bytes]" = {}
        for array_index, image in enumerate(images_to_read, start=1):
            image_filename = str(Path(image).name)
            # Get index of the image in the images array
            renamed_file = str(self.info_list.index(image))
            # Keeps track of which image index belongs to which image name
            self.images_to_upload_names.update({renamed_file: image_filename})
            files.update({renamed_file: self._get_bytes_for_upload(image)})
        return files
