"""A deterministic style Agent for the photo gallery.

The Agent chooses a safe local processing plan from the user's natural-language
brief, then delegates the actual image operation to ``lineart_core``. It does
not upload images or call an external model, so the project remains runnable
without a database, API key, or GPU.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from lineart_core import STYLE_NAMES, process_image


STYLE_RULES = (
    (("线稿", "轮廓", "勾线"), "简约线条", 0.65, 0.65),
    (("铅笔", "素描", "手绘"), "铅笔素描", 0.55, 0.72),
    (("漫画", "动漫", "二次元"), "漫画轮廓", 0.72, 0.58),
    (("胶片", "复古", "电影"), "复古胶片", 0.55, 0.55),
    (("海报", "封面", "高对比"), "高对比海报", 0.78, 0.52),
    (("抽象", "编辑", "杂志"), "编辑感抽象", 0.62, 0.48),
)


@dataclass(frozen=True)
class StylePlan:
    intent: str
    style: str
    intensity: float
    detail: float
    steps: tuple[str, ...]
    guardrails: tuple[str, ...]


def plan_style(prompt: str = "", requested_style: str = "极简保真",
               intensity: float = 0.45, detail: float = 0.60) -> dict:
    """Turn a natural-language brief into an inspectable processing plan."""
    text = (prompt or "").strip()
    style = requested_style if requested_style in STYLE_NAMES else "极简保真"
    chosen_intensity = float(intensity)
    chosen_detail = float(detail)
    intent = "preserve_source"
    for keywords, candidate, default_intensity, default_detail in STYLE_RULES:
        if any(keyword in text for keyword in keywords):
            style = candidate
            chosen_intensity = default_intensity
            chosen_detail = default_detail
            intent = "natural_language_style_selection"
            break
    if not text:
        intent = "explicit_control_selection"

    plan = StylePlan(
        intent=intent,
        style=style,
        intensity=max(0.0, min(1.0, chosen_intensity)),
        detail=max(0.0, min(1.0, chosen_detail)),
        steps=("parse_brief", "select_local_filter", "process_image", "return_report"),
        guardrails=("local_only", "no_external_upload", "deterministic_filter", "preserve_source_copy"),
    )
    return asdict(plan)


def run_style_agent(image, prompt: str = "", requested_style: str = "极简保真",
                    intensity: float = 0.45, detail: float = 0.60):
    """Execute the plan and return image, report, and trace metadata."""
    plan = plan_style(prompt, requested_style, intensity, detail)
    result, report = process_image(
        image,
        style=plan["style"],
        intensity=plan["intensity"],
        detail=plan["detail"],
    )
    return result, report, plan
