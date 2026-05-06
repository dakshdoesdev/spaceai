from __future__ import annotations

from pathlib import Path


REAL_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
PLACEHOLDER_EXTENSIONS = {".tile"}


class ImageValidationError(ValueError):
    pass


def is_real_image_extension(path: Path) -> bool:
    return path.suffix.lower() in REAL_IMAGE_EXTENSIONS


def infer_image_extension(body: bytes, content_type: str = "") -> str | None:
    normalized = content_type.split(";")[0].strip().lower()
    if normalized == "image/png":
        return ".png"
    if normalized in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    if normalized in {"image/tiff", "image/geotiff", "application/geotiff"}:
        return ".tif"

    if body.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if body.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if body.startswith((b"II*\x00", b"MM\x00*")):
        return ".tif"
    return None


def validate_readable_image(path: Path) -> None:
    if not path.exists():
        raise ImageValidationError(f"image file does not exist: {path}")
    if not is_real_image_extension(path):
        raise ImageValidationError(f"expected a real raster image extension (.png/.jpg/.jpeg/.tif), got: {path}")

    try:
        from PIL import Image, UnidentifiedImageError
    except Exception as exc:
        raise ImageValidationError("Pillow is required to verify image readability") from exc

    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageValidationError(f"file is not a readable image: {path}") from exc
