"""Image processing and validation module."""

import enum
import io
import logging
import math
import string
import zipfile
from pathlib import Path
from typing import List, Dict, Union, Literal, Optional, Tuple

import natsort
from PIL import Image, ImageSequence

from .constants import MIN_IMAGE_SIZE, MAX_IMAGE_PIXELS

logger = logging.getLogger("mupl")

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class Format(enum.Enum):
    """Image format enumeration."""

    PNG = 0
    JPEG = 1
    GIF = 2
    WEBP = 4


class ImageProcessorBase:
    """Base class for image processing utilities."""

    translation = {}

    @staticmethod
    def key(x) -> Union[Literal[0], str]:
        """Give a higher priority in sorting for images with their first character a punctuation."""
        # Handle both string paths and tuples
        path_str = x[0] if isinstance(x, tuple) else x

        # Check if path string is empty or if filename is empty
        if not path_str or not Path(path_str).name:
            return path_str

        if Path(path_str).name[0].lower() in string.punctuation:
            return 0
        else:
            return path_str

    @staticmethod
    def get_image_format(image_bytes: bytes) -> Optional[Format]:
        """Returns the image type from the first few bytes."""
        if image_bytes.startswith(b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"):
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
    def get_new_format_for_webp(image_bytes: bytes) -> str:
        """Determine the best format to convert WebP images to."""
        with Image.open(io.BytesIO(image_bytes)) as image:
            try:
                _ = ImageSequence.Iterator(image)[1]
                return "GIF"
            except IndexError:
                pass

            if image.mode == "RGBA":
                return "PNG"

            return "JPEG"

    @staticmethod
    def combine_small_images(
        images: List[Tuple[str, bytes]],
        is_widestrip: bool,
        combine: bool,
        min_size: int = MIN_IMAGE_SIZE,
    ) -> List[Tuple[str, bytes]]:
        """Combine images that are smaller than or equal to min_size with the previous image if combine is True."""
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

                if current_image is None:
                    current_image = img.copy()
                    current_name = img_name
                    current_bytes = img_bytes
                    current_format = img.format
                    continue

                # Check if current image should be combined
                if (
                    (is_widestrip and width <= min_size)
                    or (not is_widestrip and height <= min_size)
                ) and combine:
                    # Combine with current image
                    if is_widestrip:
                        # Combine horizontally
                        new_width = current_image.width + width
                        new_height = max(current_image.height, height)
                        combined = Image.new("RGB", (new_width, new_height), "white")
                        combined.paste(current_image, (0, 0))
                        combined.paste(img, (current_image.width, 0))
                    else:
                        # Combine vertically
                        new_width = max(current_image.width, width)
                        new_height = current_image.height + height
                        combined = Image.new("RGB", (new_width, new_height), "white")
                        combined.paste(current_image, (0, 0))
                        combined.paste(img, (0, current_image.height))

                    current_image = combined
                    current_name = f"{current_name}+{img_name}"
                else:
                    # Save current image and start new one
                    if current_image and ImageProcessorBase._is_image_large_enough(
                        current_bytes, min_size
                    ):
                        # Convert current image back to bytes
                        output = io.BytesIO()
                        current_image.save(output, format=current_format or "JPEG")
                        combined_images.append((current_name, output.getvalue()))

                    current_image = img.copy()
                    current_name = img_name
                    current_bytes = img_bytes
                    current_format = img.format

        # Add the last image
        if current_image and ImageProcessorBase._is_image_large_enough(
            current_bytes, min_size
        ):
            output = io.BytesIO()
            current_image.save(output, format=current_format or "JPEG")
            combined_images.append((current_name, output.getvalue()))

        return combined_images

    @staticmethod
    def _is_image_large_enough(img_bytes: bytes, min_size: int) -> bool:
        """Check if image meets minimum size requirements."""
        with Image.open(io.BytesIO(img_bytes)) as img:
            width, height = img.size
            return width >= min_size and height >= min_size

    @staticmethod
    def split_image(
        image_name: str,
        image_bytes: bytes,
        is_widestrip: bool,
    ) -> List[bytes]:
        """Split large images into smaller chunks for processing."""
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size

            # Determine split strategy based on image orientation and mode
            if is_widestrip:
                # Split wide images horizontally
                if width > height * 2:  # Wide image
                    chunks = math.ceil(width / height)
                    chunk_width = width // chunks

                    split_images = []
                    for i in range(chunks):
                        left = i * chunk_width
                        right = min((i + 1) * chunk_width, width)

                        chunk = image.crop((left, 0, right, height))
                        output = io.BytesIO()
                        chunk.save(output, format=image.format or "JPEG")
                        split_images.append(output.getvalue())

                    return split_images
            else:
                # Split tall images vertically
                if height > width * 2:  # Tall image
                    chunks = math.ceil(height / width)
                    chunk_height = height // chunks

                    split_images = []
                    for i in range(chunks):
                        top = i * chunk_height
                        bottom = min((i + 1) * chunk_height, height)

                        chunk = image.crop((0, top, width, bottom))
                        output = io.BytesIO()
                        chunk.save(output, format=image.format or "JPEG")
                        split_images.append(output.getvalue())

                    return split_images

            # Return original if no splitting needed
            return [image_bytes]


class ImageProcessor:
    """Main image processor class for handling manga chapter images."""

    def __init__(
        self,
        to_upload: Path,
        folder_upload: bool,
        translation: dict,
        number_of_images_upload: int,
        widestrip: bool,
        combine: bool = False,
        **kwargs,
    ) -> None:
        """Initialize the ImageProcessor.

        Args:
            to_upload: Path to the file/folder to upload
            folder_upload: Whether uploading a folder or single file
            translation: Translation dictionary
            number_of_images_upload: Number of images to upload at once
            widestrip: Whether to use widestrip mode
            combine: Whether to combine small images
        """
        self.to_upload = to_upload
        self.folder_upload = folder_upload
        self.translation = translation
        self.number_of_images_upload = number_of_images_upload
        self.widestrip = widestrip
        self.combine = combine

        self.valid_images = []
        self.valid_images_to_upload = []
        self.new_to_old_name_map = {}
        self.converted_images = {}

        self.myzip = None
        if not self.folder_upload:
            self.myzip = zipfile.ZipFile(self.to_upload, "r")

        self._get_valid_images()

    def _is_image_valid(self, image: str) -> Optional[List[Tuple[str, bytes]]]:
        """Validate if the image is a supported format."""
        try:
            image_data = self._read_image_data(image)
            if not image_data:
                return None

            # Check if it's a valid image format
            image_format = ImageProcessorBase.get_image_format(image_data)
            if image_format is None:
                logger.warning(f"Unsupported image format: {image}")
                return None

            if image_format == Format.WEBP:
                new_format = ImageProcessorBase.get_new_format_for_webp(image_data)
                self.converted_images.update({image: new_format})
                logger.info(f"Converted {image} into {new_format}")
                with Image.open(io.BytesIO(image_data)) as img:
                    output = io.BytesIO()
                    img.save(output, format=new_format)
                    image_data = output.getvalue()

            return [(image, image_data)]

        except Exception as e:
            logger.error(f"Error validating image {image}: {e}")
            return None

    def _read_image_data(self, image: str) -> bytes:
        """Read image data from file or ZIP."""
        if self.folder_upload:
            image_path = self.to_upload.joinpath(image)
            return image_path.read_bytes()
        else:
            with self.myzip.open(image) as myfile:
                return myfile.read()

    def _get_valid_images(self):
        """Process and validate all images."""
        if self.folder_upload:
            image_files = [x.name for x in self.to_upload.iterdir()]
        else:
            image_files = [x.filename for x in self.myzip.infolist()]

        valid_image_data = []
        for image_file in image_files:
            validated = self._is_image_valid(image_file)
            if validated:
                valid_image_data.extend(validated)

        processed_images = []
        for img_name, img_bytes in valid_image_data:
            split_images = ImageProcessorBase.split_image(
                img_name, img_bytes, self.widestrip
            )

            for i, split_img in enumerate(split_images):
                split_name = (
                    f"{img_name}_part{i}" if len(split_images) > 1 else img_name
                )
                processed_images.append((split_name, split_img))

        if self.combine:
            processed_images = ImageProcessorBase.combine_small_images(
                processed_images, self.widestrip, self.combine
            )

        processed_images = natsort.natsorted(
            processed_images, key=ImageProcessorBase.key
        )
        self.valid_images = [img[0] for img in processed_images]
        self.valid_images_to_upload = processed_images

    def get_images_to_upload(self) -> List[Tuple[str, bytes]]:
        """Get the list of processed images ready for upload."""
        renamed_images = []
        for i, (name, data) in enumerate(self.valid_images_to_upload):
            extension = Path(name).suffix or ".jpg"
            new_name = f"{i+1:04d}{extension}"
            renamed_images.append((new_name, data))
            self.new_to_old_name_map.update({new_name: name})
        return renamed_images

    def get_image_list(self) -> List[Tuple[str, int]]:
        """Get list of image names and their current order."""
        return [(name, i) for i, name in enumerate(self.valid_images)]

    def reorder_images(self, new_order: List[int]) -> bool:
        """Reorder images based on provided list of indices."""
        if len(new_order) != len(self.valid_images_to_upload):
            logger.error(
                f"New order length {len(new_order)} doesn't match images count {len(self.valid_images_to_upload)}"
            )
            return False

        if set(new_order) != set(range(len(self.valid_images_to_upload))):
            logger.error("New order must contain all indices from 0 to n-1")
            return False

        try:
            reordered_images = [self.valid_images[i] for i in new_order]
            reordered_images_to_upload = [
                self.valid_images_to_upload[i] for i in new_order
            ]

            self.valid_images = reordered_images
            self.valid_images_to_upload = reordered_images_to_upload

            logger.info("Images reordered successfully")
            return True

        except (IndexError, TypeError) as e:
            logger.error(f"Error reordering images: {e}")
            return False

    def move_image_to_position(self, from_index: int, to_index: int) -> bool:
        """Move an image from one position to another."""
        if not (0 <= from_index < len(self.valid_images_to_upload)):
            logger.error(f"Invalid from_index: {from_index}")
            return False

        if not (0 <= to_index < len(self.valid_images_to_upload)):
            logger.error(f"Invalid to_index: {to_index}")
            return False

        if from_index == to_index:
            return True  # No change needed

        try:
            # Move in both lists
            image_name = self.valid_images.pop(from_index)
            image_data = self.valid_images_to_upload.pop(from_index)

            self.valid_images.insert(to_index, image_name)
            self.valid_images_to_upload.insert(to_index, image_data)

            logger.info(f"Moved image from position {from_index} to {to_index}")
            return True

        except (IndexError, TypeError) as e:
            logger.error(f"Error moving image: {e}")
            return False

    def get_image_count(self) -> int:
        """Get the total number of valid images."""
        return len(self.valid_images_to_upload)

    def get_processing_stats(self) -> Dict:
        """Get statistics about image processing."""
        return {
            "total_images": len(self.valid_images),
            "widestrip_mode": self.widestrip,
            "combine_enabled": self.combine,
            "upload_batch_size": self.number_of_images_upload,
        }

    def close(self) -> None:
        """Close the ZIP file if it's open."""
        if self.myzip is not None:
            self.myzip.close()
            self.myzip = None

    def __del__(self) -> None:
        """Destructor to ensure ZIP file is closed."""
        self.close()
