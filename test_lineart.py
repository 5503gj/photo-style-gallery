from PIL import Image, ImageDraw

from lineart_core import STYLE_NAMES, process_image


def make_sample() -> Image.Image:
    image = Image.new("RGB", (320, 240), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 40, 280, 200), outline="black", width=4)
    draw.ellipse((110, 70, 210, 170), outline="black", width=4)
    return image


def test_all_styles_return_rgb_images():
    sample = make_sample()
    for style in STYLE_NAMES:
        output, report = process_image(sample, style)
        assert output.mode == "RGB"
        assert output.size == sample.size
        assert report.style == style


def test_fidelity_style_keeps_source_dimensions():
    sample = make_sample()
    output, report = process_image(sample, "极简保真", intensity=0.35)
    assert output.size == sample.size
    assert report.style == "极简保真"


def test_large_input_is_bounded():
    sample = Image.new("RGB", (4000, 2000), "white")
    output, _ = process_image(sample, max_side=1600)
    assert max(output.size) <= 1600
