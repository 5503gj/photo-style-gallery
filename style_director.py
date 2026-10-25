"""Inspectable image tools: analyze, propose, render real variants, export."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import time
import zipfile

import cv2
import numpy as np
from PIL import Image
from image_input import load_upload
from lineart_core import prepare_image, process_image

PURPOSES = ("轮廓与线条", "封面与海报", "自然与日常")
VERSION = "form-director/1"


def analyze_image(image: Image.Image) -> dict:
    bounded = prepare_image(image, 900)
    rgb = np.asarray(bounded)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 80, 170)
    palette_image = bounded.resize((120, 120)).quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    colors = palette_image.getpalette()
    counts = sorted(palette_image.getcolors() or [], reverse=True)
    palette = [{"hex": "#" + "".join(f"{value:02x}" for value in colors[index*3:index*3+3]), "share": round(count/14400, 4)} for count, index in counts]
    brightness, density = float(gray.mean()/255), float(np.count_nonzero(edges)/edges.size)
    return {"original_size": list(image.size), "preview_size": list(bounded.size), "brightness": round(brightness, 4), "contrast": round(float(gray.std()/255), 4), "edge_density": round(density, 4), "tone": "偏暗" if brightness < .28 else "偏亮" if brightness > .78 else "中间调", "texture": "细节较多" if density > .12 else "轮廓较少" if density < .02 else "轮廓适中", "palette": palette}


def propose_styles(analysis: dict, purpose: str) -> list[dict]:
    if purpose not in PURPOSES:
        raise ValueError("请选择有效的用途")
    styles = {"轮廓与线条": ["简约线条", "铅笔素描", "漫画轮廓"], "封面与海报": ["编辑感抽象", "高对比海报", "复古胶片"], "自然与日常": ["极简保真", "复古胶片", "铅笔素描"]}[purpose]
    detail = .45 if analysis["edge_density"] > .12 else .8 if analysis["edge_density"] < .02 else .65
    intensity = .5 if analysis["brightness"] < .28 else .45
    return [{"style": style, "intensity": intensity, "detail": detail, "reason": f"面向{purpose}；画面{analysis['tone']}、{analysis['texture']}，先用{'较低细节减少纹理' if detail < .5 else '较高细节保留轮廓' if detail > .7 else '中等细节建立对照'}。参数是可调整的规则建议，不是满意度预测。"} for style in styles]


def outline_svg(image: Image.Image, max_paths=600, max_vertices=16000) -> tuple[str, dict]:
    if isinstance(max_paths, bool) or not isinstance(max_paths, int) or not 1 <= max_paths <= 600:
        raise ValueError("轮廓数量需在1至600内")
    if isinstance(max_vertices, bool) or not isinstance(max_vertices, int) or not 10 <= max_vertices <= 16000:
        raise ValueError("顶点预算需在10至16000内")
    bounded = prepare_image(image, 1000)
    gray = cv2.cvtColor(np.asarray(bounded), cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 70, 160)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted((contour for contour in contours if cv2.arcLength(contour, True) >= 9), key=lambda contour: cv2.arcLength(contour, True), reverse=True)
    paths, vertices, truncated = [], 0, False
    for contour in contours:
        points = cv2.approxPolyDP(contour, .8, True).reshape(-1, 2)
        if len(points) < 2:
            continue
        if len(paths) >= max_paths or vertices + len(points) > max_vertices:
            truncated = True
            break
        vertices += len(points)
        commands = "M" + " L".join(f"{int(x)},{int(y)}" for x, y in points) + " Z"
        paths.append(f'<path d="{commands}"/>')
    width, height = bounded.size
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><title>FORM image contour</title><desc>Deterministic contour extraction, not semantic tracing.</desc><g fill="none" stroke="#302d29" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round">' + "".join(paths) + "</g></svg>"
    return svg, {"paths": len(paths), "vertices": vertices, "size": [width, height], "truncated": truncated}


def build_batch(filename: str, purpose: str, output_dir: Path, progress=None) -> dict:
    """Write only generated files; never put the raw upload into the export zip."""
    if purpose not in PURPOSES:
        raise ValueError("请选择有效的用途")
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        raise ValueError("导出目录不存在")
    events = []
    def record(tool, label, started, detail):
        events.append({"tool": tool, "label": label, "elapsed_ms": round((time.perf_counter()-started)*1000, 2), "detail": detail})
    started = time.perf_counter()
    if progress:
        progress(.05, desc="读取并校验图片")
    image = load_upload(filename)
    source_hash = hashlib.sha256()
    with Path(filename).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            source_hash.update(chunk)
    analysis = analyze_image(image)
    prepared = prepare_image(image, 1000)
    record("analyze_image", "分析画面", started, f"{analysis['tone']} · {analysis['texture']} · {len(analysis['palette'])}种主色")
    started = time.perf_counter()
    proposals = propose_styles(analysis, purpose)
    record("propose_styles", "选择风格技能", started, "3种方案，参数基于可观测图像特征")
    preview_path = output_dir / "source-preview.png"
    prepared.save(preview_path)
    variants = []
    started = time.perf_counter()
    for index, proposal in enumerate(proposals):
        if progress:
            progress(.2 + index*.2, desc=f"生成试片 {index+1}/3 · {proposal['style']}")
        output, _ = process_image(prepared, proposal["style"], proposal["intensity"], proposal["detail"], max_side=1000)
        filename_out = f"variant-{index+1:02d}.png"
        output.save(output_dir / filename_out)
        variants.append({**proposal, "filename": filename_out, "output_size": list(output.size)})
    record("render_variants", "实际生成试片", started, "3张PNG，最长边1000px")
    started = time.perf_counter()
    svg, vector = outline_svg(prepared)
    (output_dir / "source-outline.svg").write_text(svg, encoding="utf-8")
    record("outline_svg", "生成矢量轮廓", started, f"{vector['paths']}条矢量轮廓，含参数清单")
    manifest = {"version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(), "source_sha256": source_hash.hexdigest(), "purpose": purpose, "analysis": analysis, "variants": variants, "vector": vector, "tools": events, "limits": ["规则图像工具，无生成式模型调用。", "试片最长边1000px；SVG为原图轮廓提取，不是语义矢量重绘。", "原始上传文件和文件名不打入套装，预览与结果仍属于图像数据。"]}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    archive = output_dir / "form-style-kit.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in ["manifest.json", "source-outline.svg"] + [variant["filename"] for variant in variants]:
            zipped.write(output_dir / name, arcname=name)
    if progress:
        progress(1, desc="试片与导出已完成")
    return {"manifest": manifest, "directory": str(output_dir), "preview": str(preview_path), "gallery": [(str(output_dir / variant["filename"]), variant["style"]) for variant in variants], "archive": str(archive), "svg": str(output_dir / "source-outline.svg")}


def analysis_html(analysis: dict) -> str:
    palette = "".join(f'<span class="palette-swatch" style="--swatch:{color["hex"]}" title="{color["hex"]} · {color["share"]:.0%}"><i></i><small>{color["hex"].upper()}</small></span>' for color in analysis["palette"])
    return f'<div class="image-observations"><span>{html.escape(analysis["tone"])}</span><span>{html.escape(analysis["texture"])}</span><span>{analysis["original_size"][0]} × {analysis["original_size"][1]}</span></div><div class="source-palette">{palette}</div><p class="analysis-caption">主色来自当前图片的像素统计，用于选色参考。</p>'


def tools_html(events: list[dict]) -> str:
    return '<ol class="director-trace">' + "".join(f'<li><span>✓</span><div><strong>{html.escape(event["label"])}</strong><small>{html.escape(event["detail"])}</small></div><code>{event["elapsed_ms"]:.0f} ms</code></li>' for event in events) + '</ol>'
