"""Gradio web app for the Photo to Lineart project."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

os.environ.setdefault("GRADIO_TEMP_DIR", tempfile.mkdtemp(prefix="photo-style-"))
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr
from image_input import MAX_FILE_BYTES, load_upload
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


def transform(filename: str | None, style: str, intensity: float, detail: float):
    if filename is None:
        return None, None, "**还没有生成**\n\n请先上传一张 JPG 或 PNG 图片。"
    try:
        image = load_upload(filename)
        result, report = process_image(image, style, intensity, detail)
        # Only return the bounded preview, never a copy of the full-resolution source.
        preview = image.copy()
        preview.thumbnail((800, 800))
        return preview, result, report.to_markdown()
    except (ValueError, TypeError) as exc:
        return None, None, f"**处理失败**\n\n{exc}"
    except Exception:
        return None, None, "**处理失败**\n\n处理服务暂时不可用，请稍后重试。"


def launch_options() -> dict:
    host = os.environ.get("PHOTO_HOST", "127.0.0.1")
    auth = None
    if host not in ("127.0.0.1", "localhost", "::1"):
        user, password = os.environ.get("PHOTO_AUTH_USER"), os.environ.get("PHOTO_AUTH_PASSWORD", "")
        if not user or len(password) < 12:
            raise ValueError("对外监听必须配置PHOTO_AUTH_USER与至少12字符的PHOTO_AUTH_PASSWORD")
        auth = (user, password)
    return dict(server_name=host, server_port=int(os.environ.get("PORT", "7860")),
                auth=auth, share=False, show_error=False, max_file_size=MAX_FILE_BYTES,
                blocked_paths=[str(Path(__file__).resolve().parent / name) for name in (".git", ".env")],
                css=CSS, theme=gr.themes.Soft())


with gr.Blocks(title="图片风格实验室", delete_cache=(60, 900), analytics_enabled=False) as demo:
    with gr.Column(elem_classes="app-shell"):
        gr.Markdown(
            "# 图片风格实验室\n"
            "保留你的照片，再给它一层克制、简约、可分享的视觉语言。\n\n"
            "由运行本应用的 Python 服务处理，无需第三方模型或 GPU。"
            "本机运行时图片传到本机；远程访问时会上传至服务器。"
            "临时文件每分钟清理一次，超过15分钟可被清理；请及时下载结果。",
            elem_classes="hero",
        )
        with gr.Row():
            with gr.Column(elem_classes="panel"):
                input_image = gr.File(type="filepath", file_types=[".jpg", ".jpeg", ".png"], label="上传照片（≤10MiB，≤1200万像素）")
                preview_image = gr.Image(label="原图预览", height=300, interactive=False)
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

        run.click(transform, [input_image, style, intensity, detail], [preview_image, output_image, report], concurrency_limit=1, api_name="apply_style")
        input_image.clear(lambda: (None, None, "图片已从界面清除；服务器临时文件按上述周期清理。"), outputs=[preview_image, output_image, report])

demo.queue(max_size=8, default_concurrency_limit=1, api_open=False)


if __name__ == "__main__":
    demo.launch(**launch_options())
