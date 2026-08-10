"""Deterministic photo-style processing used by the web app."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


STYLE_DESCRIPTIONS = {
    "极简保真": "保留原图颜色、构图和主体细节，只做克制的质感增强",
    "简约线条": "减少背景纹理和杂点，保留主体轮廓",
    "铅笔素描": "柔和的灰度笔触和纸面质感",
    "黑白线稿": "清晰、对比明确的黑白轮廓",
    "漫画轮廓": "更粗、更醒目的漫画式边缘",
    "编辑感抽象": "大色块、克制色彩和轻微轮廓叠加",
    "复古胶片": "暖色调、轻颗粒和暗角效果",
    "高对比海报": "适合封面和海报的强对比图形",
}

STYLE_NAMES = tuple(STYLE_DESCRIPTIONS)


@dataclass(frozen=True)
class ProcessingReport:
    style: str
    intensity: float
    detail: float
    original_size: tuple[int, int]
    output_size: tuple[int, int]

    def to_markdown(self) -> str:
        return (
            f"**处理完成**\n\n"
            f"- 风格：{self.style}\n"
            f"- 说明：{STYLE_DESCRIPTIONS.get(self.style, '')}\n"
            f"- 强度：{self.intensity:.2f}\n"
            f"- 细节：{self.detail:.2f}\n"
            f"- 尺寸：{self.original_size[0]}×{self.original_size[1]} → "
            f"{self.output_size[0]}×{self.output_size[1]}"
        )


def _resize_for_processing(image: Image.Image, max_side: int = 1600) -> Image.Image:
    image = image.convert("RGB")
    width, height = image.size
    scale = min(1.0, max_side / max(width, height))
    if scale == 1.0:
        return image
    return image.resize(
        (max(1, int(width * scale)), max(1, int(height * scale))),
        Image.Resampling.LANCZOS,
    )


def _rgb_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"))


def _to_gray(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def _pencil_sketch(gray: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    sigma = int(11 + detail * 30)
    if sigma % 2 == 0:
        sigma += 1
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (sigma, sigma), 0)
    dodge = cv2.divide(gray, 255 - blurred, scale=256)
    contrast = 0.75 + intensity * 0.6
    return np.clip((dodge.astype(np.float32) - 128) * contrast + 128, 0, 255).astype(np.uint8)


def _clean_lineart(gray: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    smooth = cv2.bilateralFilter(gray, 9, 55, 55)
    low = 35 + int((1 - detail) * 45)
    high = 120 + int((1 - detail) * 55)
    edges = cv2.Canny(smooth, low, high)
    if intensity > 0.65:
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    return 255 - edges


def _comic_outline(gray: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    threshold = 30 + int((1 - detail) * 50)
    edges = cv2.Canny(gray, threshold, threshold + 110)
    if intensity >= 0.55:
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    canvas = np.full_like(edges, 255)
    canvas[edges > 0] = int(255 - 180 * intensity)
    return canvas


def _minimal_lineart(gray: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    """Produce sparse, clean outlines with reduced texture noise."""
    smooth = cv2.bilateralFilter(gray, 11, 85, 85)
    low = 65 + int((1 - detail) * 65)
    high = 165 + int((1 - detail) * 55)
    edges = cv2.Canny(smooth, low, high)
    edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    if intensity > 0.45:
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    return 255 - edges


def _minimal_fidelity(rgb: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    """Keep the source photo recognizable while adding a restrained editorial finish."""
    smooth = cv2.bilateralFilter(rgb, 9, 35 + detail * 35, 35 + detail * 35)
    step = max(8, int(24 - detail * 10))
    quantized = np.clip((smooth // step) * step + step // 2, 0, 255).astype(np.uint8)
    blend = 0.18 + intensity * 0.18
    result = rgb.astype(np.float32) * (1 - blend) + quantized.astype(np.float32) * blend

    hsv = cv2.cvtColor(np.clip(result, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] *= 1.0 - intensity * 0.18
    result = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)

    gray = _to_gray(rgb)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 100, 190)
    result[edges > 0] *= 1.0 - (0.04 + intensity * 0.08)
    return np.clip(result, 0, 255).astype(np.uint8)


def _editorial_abstract(rgb: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    """Create a muted editorial abstraction without a generative model."""
    height, width = rgb.shape[:2]
    smooth = cv2.bilateralFilter(rgb, 9, 75, 75)
    step = max(16, int(64 - detail * 24))
    quantized = np.clip((smooth // step) * step + step // 2, 0, 255).astype(np.uint8)
    block_w = max(1, width // int(18 - detail * 6))
    block_h = max(1, height // int(18 - detail * 6))
    small = cv2.resize(quantized, (block_w, block_h), interpolation=cv2.INTER_AREA)
    poster = cv2.resize(small, (width, height), interpolation=cv2.INTER_CUBIC)

    edges = cv2.Canny(_to_gray(smooth), 80 + int((1 - detail) * 40), 175)
    result = poster.astype(np.float32)
    result[edges > 0] *= 1 - (0.12 + intensity * 0.25)
    return np.clip(result, 0, 255).astype(np.uint8)


def _retro_film(rgb: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    """Apply a restrained warm grade, grain, and vignette."""
    height, width = rgb.shape[:2]
    result = rgb.astype(np.float32)
    result[:, :, 0] *= 1.0 - 0.08 * intensity
    result[:, :, 2] *= 1.0 + 0.08 * intensity
    result += 4.0 * intensity

    rng = np.random.default_rng(2026)
    grain = rng.normal(0, 2.0 + detail * 4.0, (height, width, 1))
    result += grain

    y, x = np.ogrid[:height, :width]
    distance = np.sqrt(((x - width / 2) / (width / 2)) ** 2 + ((y - height / 2) / (height / 2)) ** 2)
    vignette = np.clip(1.0 - distance * 0.16 * intensity, 0.78, 1.0)[..., None]
    return np.clip(result * vignette, 0, 255).astype(np.uint8)


def _poster(rgb: np.ndarray, intensity: float, detail: float) -> np.ndarray:
    gray = _to_gray(rgb)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    threshold = 105 + int((1 - detail) * 55)
    _, binary = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
    if intensity > 0.6:
        binary = cv2.erode(binary, np.ones((2, 2), np.uint8), iterations=1)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)


def process_image(
    image: Image.Image,
    style: str = "简约线条",
    intensity: float = 0.65,
    detail: float = 0.60,
    max_side: int = 1600,
) -> tuple[Image.Image, ProcessingReport]:
    """Convert a PIL image into one of the registered deterministic styles."""
    if image is None:
        raise ValueError("请先上传一张图片")

    intensity = float(np.clip(intensity, 0.0, 1.0))
    detail = float(np.clip(detail, 0.0, 1.0))
    prepared = _resize_for_processing(image, max_side=max_side)
    rgb = _rgb_array(prepared)
    gray = _to_gray(rgb)

    if style == "极简保真":
        output = _minimal_fidelity(rgb, intensity, detail)
    elif style == "简约线条":
        output = _minimal_lineart(gray, intensity, detail)
        output = cv2.cvtColor(output, cv2.COLOR_GRAY2RGB)
    elif style == "铅笔素描":
        output = cv2.cvtColor(_pencil_sketch(gray, intensity, detail), cv2.COLOR_GRAY2RGB)
    elif style == "黑白线稿":
        output = cv2.cvtColor(_clean_lineart(gray, intensity, detail), cv2.COLOR_GRAY2RGB)
    elif style == "漫画轮廓":
        output = cv2.cvtColor(_comic_outline(gray, intensity, detail), cv2.COLOR_GRAY2RGB)
    elif style == "编辑感抽象":
        output = _editorial_abstract(rgb, intensity, detail)
    elif style == "复古胶片":
        output = _retro_film(rgb, intensity, detail)
    elif style == "高对比海报":
        output = _poster(rgb, intensity, detail)
    else:
        raise ValueError(f"未知风格：{style}")

    result = Image.fromarray(output).convert("RGB")
    report = ProcessingReport(
        style=style,
        intensity=intensity,
        detail=detail,
        original_size=image.convert("RGB").size,
        output_size=result.size,
    )
    return result, report
