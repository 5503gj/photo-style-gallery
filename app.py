"""Gradio web app for the Photo to Lineart project."""

from __future__ import annotations

import os

import gradio as gr
from PIL import Image

from lineart_core import STYLE_NAMES, process_image


CSS = """
:root { color-scheme: light; }
body, .gradio-container { background: #f7f7f5 !important; color: #202124 !important; }
.app-shell { max-width: 1180px; margin: 0 auto; }
.hero { padding: 28px 8px 12px; }
.hero h1 { font-size: 42px; letter-spacing: -1px; margin-bottom: 8px; color: #202124; }
.hero p { color: #667085; font-size: 16px; }
.panel { border: 1px solid #e4e7ec; border-radius: 18px; background: #ffffff; padding: 14px; box-shadow: 0 10px 30px rgba(32, 33, 36, 0.05); }
.style-note { border-radius: 12px; background: #f4f4f0; padding: 10px 12px; color: #667085; }
.note { color: #667085; font-size: 13px; }
"""


def transform(image: Image.Image, style: str, intensity: float, detail: float):
    if image is None:
        return None, "**还没有生成**\n\n请先上传一张 JPG 或 PNG 图片。"
    try:
        result, report = process_image(image, style, intensity, detail)
        return result, report.to_markdown()
    except Exception as exc:
        return None, f"**处理失败**\n\n{exc}"


with gr.Blocks(title="图片风格实验室", css=CSS, theme=gr.themes.Soft()) as demo:
    with gr.Column(elem_classes="app-shell"):
        gr.Markdown(
            "# 图片风格实验室\n"
            "保留你的照片，再给它一层克制、简约、可分享的视觉语言。\n\n"
            "当前版本使用本地 OpenCV 处理，不上传图片，也不需要 GPU。",
            elem_classes="hero",
        )
        with gr.Row():
            with gr.Column(elem_classes="panel"):
                input_image = gr.Image(type="pil", label="上传照片", height=420)
                style = gr.Radio(
                    list(STYLE_NAMES),
                    value="极简保真",
                    label="视觉方案",
                )
                gr.Markdown(
                    "**极简保真**：优先保留你的颜色、构图和主体细节；如果想要真正的线条效果，再选择“简约线条”。",
                    elem_classes="style-note",
                )
                intensity = gr.Slider(0.0, 1.0, value=0.45, step=0.05, label="风格强度")
                detail = gr.Slider(0.0, 1.0, value=0.60, step=0.05, label="细节保留")
                run = gr.Button("应用风格", variant="primary")
                gr.Markdown("建议上传 JPG 或 PNG；复杂背景可以选择“简约线条”并降低细节。", elem_classes="note")
            with gr.Column(elem_classes="panel"):
                output_image = gr.Image(type="pil", label="处理结果", height=420)
                report = gr.Markdown("处理参数会显示在这里。")

        run.click(transform, [input_image, style, intensity, detail], [output_image, report])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port, show_error=True)
