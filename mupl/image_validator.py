import enum
import io
import logging
import math
import string
import zipfile
from pathlib import Path
from typing import List, Dict, Union, Literal, Optional
from typing import Tuple

import natsort
from PIL import Image, ImageSequence

from mupl.file_validator import FileProcesser
from mupl.utils.config import NUMBER_OF_IMAGES_UPLOAD

logger = logging.getLogger("mupl")

Image.MAX_IMAGE_PIXELS = None


class Format(enum.Enum):
    PNG = 0
    JPG = 1
    GIF = 2

    # Converted to one of the md supported format
    WEBP = 4


class ImageProcessorBase:
    @staticmethod
    def key(x: "tuple") -> "Union[Literal[0], str]":
        """Give a higher priority in sorting for images with their first character a punctuation."""
        if Path(x[0]).name[0].lower() in string.punctuation:
            return 0
        else:
            return x

    @staticmethod
    def get_image_format(image_bytes: "bytes") -> "Optional[Format]":
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

    @staticmethod
    def get_new_format_for_webp(image_bytes: "bytes") -> "str":
        with Image.open(io.BytesIO(image_bytes)) as image:
            # If it has more then 1 frame it's animated so convert to GIF
            try:
                _ = ImageSequence.Iterator(image)[1]
                return "GIF"
            except IndexError:
                pass

            # Lossless WebP and lossy (with alpha) WebP
            if image.mode == "RGBA":
                return "PNG"

            # Otherwise, convert to JPEG
            return "JPEG"

    @staticmethod
    def split_tall_images(image_name: "str", image_bytes: "bytes") -> "List[bytes]":
        with Image.open(io.BytesIO(image_bytes)) as image:
            split_image = []
            width, height = image.size

            if height < 10_000:
                return [image_bytes]

            desired_max_chunk_height = 3000
            min_chunk_height = 1500
            initial_num_chunks = math.ceil(height / desired_max_chunk_height)
            chunk_height = math.ceil(height / initial_num_chunks)
            if chunk_height < min_chunk_height:
                chunk_height = min_chunk_height
                num_chunks = math.ceil(height / chunk_height)
            else:
                num_chunks = initial_num_chunks

            logger.info(f"Split {image_name} into {num_chunks} chunks.")
            print(f"Split {image_name} into {num_chunks} chunks.")
            for i in range(num_chunks):
                left = 0
                upper = i * chunk_height
                right = width
                lower = min((i + 1) * chunk_height, height)
                bbox = (left, upper, right, lower)
                working_slice = image.crop(bbox)

                img_byte_arr = io.BytesIO()
                working_slice.save(img_byte_arr, format=image.format)
                img_byte_arr = img_byte_arr.getvalue()
                split_image.append(img_byte_arr)

            return split_image


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
        self.processed_images: "List[Tuple[str, bytes]]" = []

        self.images_upload_session = NUMBER_OF_IMAGES_UPLOAD

        self.info_list = self._get_valid_images()

    def _is_image_valid(self, image: "str") -> "List[bytes]":
        return self._get_bytes_for_upload(image)

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

    def _get_bytes_for_upload(self, image: "str") -> "Optional[List[bytes]]":
        image_bytes = self._read_image_data(image)
        new_format = None
        current_format = ImageProcessorBase.get_image_format(image_bytes)

        if not current_format:
            return None

        if current_format == Format.WEBP:
            new_format = ImageProcessorBase.get_new_format_for_webp(image_bytes)

        if new_format:
            self.converted_images.update({image: new_format})
            logger.info(f"Converted {image} into {new_format}")
            with Image.open(io.BytesIO(image_bytes)) as image:
                output = io.BytesIO()
                image.save(output, new_format)
                image_bytes = output.getvalue()

        split_image = ImageProcessorBase.split_tall_images(image, image_bytes)
        return split_image

    def _get_valid_images(self):
        """Validate the files in the archive.
        Check if all the files are images.
        Sorts the images using natural sort."""
        if self.folder_upload:
            to_iter = [x.name for x in self.to_upload.iterdir()]
        else:
            to_iter = [x.filename for x in self.myzip.infolist()]

        for image in to_iter:
            image_valid = self._is_image_valid(image)
            if image_valid:
                for count, img in enumerate(image_valid, start=1):
                    self.processed_images.append((f"{image}_{count}", img))

        info_list_images_only = natsort.natsorted(
            self.processed_images, key=ImageProcessorBase.key
        )

        self.valid_images_to_upload = [
            info_list_images_only[l : l + self.images_upload_session]
            for l in range(0, len(info_list_images_only), self.images_upload_session)
        ]
        logger.debug(f"Images to upload: {self.valid_images_to_upload}")
        return info_list_images_only

    def get_images_to_upload(
        self, images_to_read: "List[Tuple[str, bytes]]"
    ) -> "Dict[str, bytes]":
        """Read the image data from the zip as list."""
        logger.debug(f"Reading data for images: {images_to_read}")
        # Dictionary to store the image index to the image bytes
        files: "Dict[str, bytes]" = {}
        for array_index, image in enumerate(images_to_read, start=1):
            image_filename = str(Path(image[0]).name)
            # Get index of the image in the images array
            renamed_file = str(self.info_list.index(image))
            # Keeps track of which image index belongs to which image name
            self.images_to_upload_names.update({renamed_file: image_filename})
            files.update({renamed_file: image[1]})
        return files
