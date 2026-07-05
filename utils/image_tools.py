"""
Image compression and image <-> PDF conversion utilities.
"""
import io
from PIL import Image


def compress_image(file_stream, quality=60, max_width=None):
    """
    quality: 1-95 (used for JPEG re-encoding)
    max_width: optional int, resizes proportionally if the image is wider
    Returns (bytes_io, mimetype, ext)
    """
    img = Image.open(file_stream)
    orig_format = (img.format or "JPEG").upper()

    if max_width and img.width > max_width:
        ratio = max_width / float(img.width)
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    out = io.BytesIO()

    if orig_format in ("JPEG", "JPG"):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(out, format="JPEG", quality=quality, optimize=True)
        mimetype, ext = "image/jpeg", "jpg"
    elif orig_format == "PNG":
        img.save(out, format="PNG", optimize=True, compress_level=9)
        mimetype, ext = "image/png", "png"
    elif orig_format == "WEBP":
        img.save(out, format="WEBP", quality=quality)
        mimetype, ext = "image/webp", "webp"
    else:
        # fallback: convert anything else to compressed JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(out, format="JPEG", quality=quality, optimize=True)
        mimetype, ext = "image/jpeg", "jpg"

    out.seek(0)
    return out, mimetype, ext


def images_to_pdf(file_streams, page_size="fit", orientation="portrait"):
    """
    file_streams: list of image file-like objects
    Returns a PDF BytesIO with one page per image.
    """
    images = []
    for stream in file_streams:
        img = Image.open(stream)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        images.append(img)

    if not images:
        raise ValueError("No images provided")

    out = io.BytesIO()
    first, rest = images[0], images[1:]
    first.save(out, "PDF", save_all=True, append_images=rest)
    out.seek(0)
    return out
