"""Bounded decoding of actual uploaded JPEG/PNG files, before RGB allocation."""
from pathlib import Path
import warnings

from PIL import Image, UnidentifiedImageError

from lineart_core import validate_size

MAX_FILE_BYTES = 10 * 1024 * 1024


def load_upload(filename: str | Path) -> Image.Image:
    path = Path(filename)
    if not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("请选择不超过10MiB的JPG或PNG文件")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                if image.format not in ("JPEG", "PNG"):
                    raise ValueError("仅支持真实JPG或PNG图片")
                validate_size(image.size)
                image.load()
                return image.copy()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError("图片无效、损坏或超过解码限制") from exc
