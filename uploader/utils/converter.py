import io

from PIL import Image, ImageSequence


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
