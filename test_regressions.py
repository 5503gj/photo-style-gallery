"""Business regressions: preserve contours and prevent clipped highlights wrapping dark."""
import numpy as np
import pytest
from PIL import Image

from lineart_core import process_image
from test_lineart import make_sample


def test_lineart_preserves_the_rectangle_and_circle():
    result, _ = process_image(make_sample(), "简约线条", 0.45, 0.60)
    ink = np.asarray(result)[:, :, 0] < 128
    assert 200 < ink.sum() < ink.size // 4
    # The top of the rectangle and both sides of the circle must survive.
    assert ink[35:47, 50:270].sum() > 100
    assert ink[85:155, 104:117].sum() > 20
    assert ink[85:155, 203:216].sum() > 20


@pytest.mark.parametrize("style", ["极简保真", "编辑感抽象"])
@pytest.mark.parametrize("detail", [0, 0.25, 0.60, 1])
def test_highlights_stay_bright_and_do_not_wrap(style, detail):
    values = []
    for level in [224, 240, 248, 255]:
        out, _ = process_image(Image.new("RGB", (32, 32), (level,) * 3), style, .45, detail)
        values.append(float(np.asarray(out).mean()))
    assert min(values) > 200
    assert all(a <= b for a, b in zip(values, values[1:]))


@pytest.mark.parametrize("name,bad", [("intensity", float("nan")), ("intensity", float("inf")), ("detail", float("-inf")), ("detail", "bad"), ("max_side", 0), ("max_side", -1), ("max_side", 1.5)])
def test_invalid_parameters_are_rejected(name, bad):
    with pytest.raises((ValueError, TypeError)):
        process_image(make_sample(), **{name: bad})


def test_retro_film_is_warm_on_neutral_input():
    result, _ = process_image(Image.new("RGB", (32, 32), (100, 100, 100)), "复古胶片", .8, .6)
    pixel = np.asarray(result)[16,16]
    assert pixel[0] > pixel[2]
