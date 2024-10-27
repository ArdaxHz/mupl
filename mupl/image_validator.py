import enum
import io
import logging
import math
import string
import sys
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Union, Literal, Optional
from typing import Tuple

import natsort
from PIL import Image, ImageSequence

from mupl.file_validator import FileProcesser
from mupl.utils.config import NUMBER_OF_IMAGES_UPLOAD, TRANSLATION, root_path


logger = logging.getLogger("mupl")

Image.MAX_IMAGE_PIXELS = None


class Format(enum.Enum):
    PNG = 0
    JPEG = 1
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
            return x[0]

    @staticmethod
    def get_image_format(image_bytes: "bytes") -> "Optional[Format]":
        """Returns the image type from the first few bytes."""
        if image_bytes.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
            return Format.PNG

        if image_bytes[0:3] == b"\xff\xd8\xff" or image_bytes[6:10] in (
            b"JFIF",
            b"Exif",
        ):
            return Format.JPEG

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
    def combine_small_images(
        images: List[Tuple[str, bytes]],
        is_widestrip: bool,
        combine: bool,
        min_size: int = 128,
    ) -> List[Tuple[str, bytes]]:
        """Combine images that are smaller than or equal to min_size with the previous image if combine is True, otherwise skip small images."""
        if len(images) < 2 or not combine:
            return [
                img
                for img in images
                if ImageProcessorBase._is_image_large_enough(img[1], min_size)
            ]

        combined_images = []
        current_image = None
        current_name = None
        current_bytes = None
        current_format = None

        for img_name, img_bytes in images:
            with Image.open(io.BytesIO(img_bytes)) as img:
                width, height = img.size

                if not ImageProcessorBase._is_image_large_enough(img_bytes, min_size):
                    logger.info(
                        f"Skipping {img_name} as it is smaller than {min_size}."
                    )
                    print(TRANSLATION["image_skip"].format(img_name, min_size, "size"))
                    continue

                if current_image is None:
                    current_image = img.copy()
                    current_name = img_name
                    current_bytes = img_bytes
                    current_format = img.format
                elif (width <= min_size or height <= min_size) and (
                    (is_widestrip and height == current_image.height)
                    or (not is_widestrip and width == current_image.width)
                ):
                    logger.info(
                        f"Combining {img_name} to {current_name} as {img_name} is smaller than {min_size}."
                    )
                    print(
                        TRANSLATION["image_combine"].format(
                            img_name, current_name, img_name, min_size
                        )
                    )

                    if is_widestrip:
                        new_width = current_image.width + img.width
                        combined = Image.new(
                            current_image.mode,
                            (new_width, height),
                        )
                        combined.paste(current_image, (0, 0))
                        combined.paste(img, (current_image.width, 0))
                    else:
                        new_height = current_image.height + img.height
                        combined = Image.new(
                            current_image.mode,
                            (width, new_height),
                        )
                        combined.paste(current_image, (0, 0))
                        combined.paste(img, (0, current_image.height))

                    current_image = combined
                    current_name += f"_and_{img_name}"

                    img_byte_arr = io.BytesIO()
                    current_image.save(img_byte_arr, format=current_format)
                    current_bytes = img_byte_arr.getvalue()
                else:
                    combined_images.append((current_name, current_bytes))
                    current_image = img.copy()
                    current_name = img_name
                    current_bytes = img_bytes

        if current_image:
            combined_images.append((current_name, current_bytes))
        return combined_images

    @staticmethod
    def _is_image_large_enough(img_bytes: bytes, min_size: int) -> bool:
        with Image.open(io.BytesIO(img_bytes)) as img:
            width, height = img.size
            return width > min_size and height > min_size

    @staticmethod
    def split_image(
        image_name: "str",
        image_bytes: "bytes",
        is_longstrip: bool,
        is_widestrip: bool,
    ) -> "List[bytes]":
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size

            if height < 10_000 and width < 10_000:
                return [image_bytes]

            if (height >= 10_000 and not is_longstrip) or (
                width >= 10_000 and not is_widestrip
            ):
                logger.warning(
                    f"Image {image_name} exceeds 10000px in {'height' if height >= 10_000 else 'width'} and is not marked as {'longstrip' if height >= 10_000 else 'widestrip'}. Removing from upload."
                )
                print(
                    TRANSLATION["image_split_not_defined"].format(
                        image_name,
                        "height" if height >= 10_000 else "width",
                        "longstrip" if height >= 10_000 else "widestrip",
                    )
                )
                return []

            split_image = []

            if height >= 10_000 and is_longstrip:
                dimension = height
                desired_max_chunk_size = 3000
                min_chunk_size = 1500
                is_tall = True
            else:
                dimension = width
                desired_max_chunk_size = 2500
                min_chunk_size = 1000
                is_tall = False

            initial_num_chunks = math.ceil(dimension / desired_max_chunk_size)
            chunk_size = math.ceil(dimension / initial_num_chunks)
            if chunk_size < min_chunk_size:
                chunk_size = min_chunk_size
                num_chunks = math.ceil(dimension / chunk_size)
            else:
                num_chunks = initial_num_chunks

            logger.info(
                f"Split {'tall' if is_tall else 'wide'} image {image_name} into {num_chunks} chunks."
            )
            print(
                TRANSLATION["image_split"].format(
                    image_name, "tall" if is_tall else "wide", num_chunks
                )
            )

            for i in range(num_chunks):
                if is_tall:
                    bbox = (
                        0,
                        i * chunk_size,
                        width,
                        min((i + 1) * chunk_size, height),
                    )
                else:
                    bbox = (
                        i * chunk_size,
                        0,
                        min((i + 1) * chunk_size, width),
                        height,
                    )

                working_slice = image.crop(bbox)
                img_byte_arr = io.BytesIO()
                working_slice.save(img_byte_arr, format=image.format)
                split_image.append(img_byte_arr.getvalue())
            return split_image


class ImageProcessor:
    def __init__(
        self,
        file_name_obj: "FileProcesser",
        folder_upload: "bool",
        combine: "bool",
    ) -> None:
        self.file_name_obj = file_name_obj
        self.to_upload = self.file_name_obj.to_upload
        self.folder_upload = folder_upload
        self.combine = combine
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

    def _is_image_valid(self, image: "str") -> "Optional[List[Tuple[str, bytes]]]":
        image_bytes = self._read_image_data(image)
        current_format = ImageProcessorBase.get_image_format(image_bytes)

        if not current_format:
            return None

        if current_format == Format.WEBP:
            new_format = ImageProcessorBase.get_new_format_for_webp(image_bytes)
            self.converted_images.update({image: new_format})
            logger.info(f"Converted {image} into {new_format}")
            with Image.open(io.BytesIO(image_bytes)) as imageN:
                output = io.BytesIO()
                imageN.save(output, new_format)
                image_bytes = output.getvalue()

        return [(image, image_bytes)]

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

    def _get_valid_images(self):
        """Validate the files in the archive.
        Check if all the files are images.
        Sorts the images using natural sort."""
        if self.folder_upload:
            to_iter = [x.name for x in self.to_upload.iterdir()]
        else:
            to_iter = [x.filename for x in self.myzip.infolist()]

        processed_images: List[Tuple[str, bytes]] = []
        for image in to_iter:
            image_valid = self._is_image_valid(image)
            if image_valid:
                processed_images.extend(image_valid)

        processed_images = ImageProcessorBase.combine_small_images(
            processed_images, self.file_name_obj.widestrip, self.combine
        )

        split_images: List[Tuple[str, bytes]] = []
        for image_name, image_bytes in processed_images:
            split = ImageProcessorBase.split_image(
                image_name,
                image_bytes,
                self.file_name_obj.longstrip,
                self.file_name_obj.widestrip,
            )
            if split:
                split_images.extend(
                    (f"{image_name}_{i+1}", img) for i, img in enumerate(split)
                )

        info_list_images_only = natsort.natsorted(
            split_images, key=ImageProcessorBase.key
        )

        self.valid_images_to_upload = [
            info_list_images_only[l : l + self.images_upload_session]
            for l in range(0, len(info_list_images_only), self.images_upload_session)
        ]

        logger.debug(f"Images to upload: {[img[0] for img in info_list_images_only]}")
        return info_list_images_only

    def get_images_to_upload(
        self, images_to_read: "List[Tuple[str, bytes]]"
    ) -> "Dict[str, bytes]":
        """Read the image data from the zip as list."""
        logger.debug(f"Reading data for images: {[img[0] for img in images_to_read]}")
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
