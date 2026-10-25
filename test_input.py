import struct
import zlib

import numpy as np
import pytest
from PIL import Image

import image_input
from image_input import load_upload
from lineart_core import process_image


def test_decoded_pixel_limit_is_checked_before_loading(tmp_path):
    path = tmp_path / "large.png"
    Image.new("RGB", (1, 1)).save(path)
    data = bytearray(path.read_bytes())
    data[16:24] = struct.pack(">II", 4000, 4000)
    data[29:33] = struct.pack(">I", zlib.crc32(data[12:29]))
    path.write_bytes(data)
    with pytest.raises(ValueError, match="1200"):
        load_upload(path)


def test_upload_checks_file_size_and_actual_format(tmp_path, monkeypatch):
    path = tmp_path / "image.jpg"
    Image.new("RGB", (8, 8)).save(path, format="GIF")
    with pytest.raises(ValueError, match="JPG"):
        load_upload(path)
    path.write_bytes(b"x" * 128)
    monkeypatch.setattr(image_input, "MAX_FILE_BYTES", 100)
    with pytest.raises(ValueError, match="10MiB"):
        load_upload(path)


def test_transparent_pixels_are_composited_on_white():
    output, _ = process_image(Image.new("RGBA", (32, 32), (0, 0, 0, 0)), "极简保真")
    assert np.asarray(output).min() >= 250


def test_orientation_is_applied_before_processing():
    image = Image.new("RGB", (80, 40), "white")
    image.getexif()[274] = 6
    output, report = process_image(image)
    assert output.size == (40, 80)
    assert report.original_size == (80, 40)


def test_png_round_trip_and_corrupt_input(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (40, 20), (80, 90, 100)).save(path)
    assert load_upload(path).getpixel((0, 0)) == (80, 90, 100)
    path.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="无效"):
        load_upload(path)


def test_network_binding_fails_closed_without_credentials(monkeypatch):
    from app import launch_options
    monkeypatch.setenv("PHOTO_HOST", "0.0.0.0")
    monkeypatch.delenv("PHOTO_AUTH_USER", raising=False)
    monkeypatch.delenv("PHOTO_AUTH_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="PHOTO_AUTH"):
        launch_options()
    monkeypatch.setenv("PHOTO_HOST", "127.0.0.1")
    assert launch_options()["auth"] is None
    monkeypatch.setenv("PHOTO_HOST", "0.0.0.0")
    monkeypatch.setenv("PHOTO_AUTH_USER", "test-user")
    monkeypatch.setenv("PHOTO_AUTH_PASSWORD", "synthetic-test-password")
    assert launch_options()["auth"][0] == "test-user"
