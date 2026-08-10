# 图片风格来源与实现目录

这份目录记录本项目从 GitHub 调研到自主实现的过程。参考开源项目的目标是理解能力边界、输入输出和工程组织方式，不复制代码、文案或素材。

| 风格/能力 | GitHub 参考 | 借鉴点 | 本项目实现 |
|---|---|---|---|
| 线条化 | [LingDong-/linedraw](https://github.com/LingDong-/linedraw) | 图片转多段线、轮廓和 SVG 的产品方向 | 当前使用 OpenCV 轮廓处理；SVG 导出列入下一阶段 |
| 铅笔素描 | [OpenCV sketch 示例](https://gist.github.com/SajjadAemmi/74cd7244b8f9a4e3f00910a84da636f1) | 灰度、反相、高斯模糊和 dodge 思路 | 重新组织为可调强度与细节参数 |
| 线稿控制 | [ControlNet Lineart](https://github.com/lllyasviel/ControlNet-v1-1-nightly) | 线稿作为生成条件的产品能力 | 当前不依赖 GPU；后续作为可选 AI 模式 |
| 编辑感抽象 | [T2I-Adapter Lineart](https://github.com/tencentarc/T2I-Adapter) | 结构线和视觉风格可以拆成不同处理阶段 | 当前实现为本地大色块、量化色彩和轮廓叠加 |
| 图片编辑 Skill | [Banuba AI Skills](https://github.com/Banuba/ai-skills) | 将编辑能力、文档和脚手架组织成 Skill | 本项目提供 `skills/photo-to-lineart-skill/SKILL.md` |
| 交互网站 | [Gradio](https://github.com/gradio-app/gradio) | 用 Python 快速搭建上传、参数和输出界面 | 自己设计中文界面和风格注册表 |

## 许可证与使用边界

- 优先参考 MIT、Apache-2.0 等许可证允许的工程思路，并在必要时保留来源链接。
- 不直接复制第三方仓库的实现代码、截图、模型权重、素材或 README 文案。
- 本项目的核心实现位于 `lineart_core.py`，每个风格都是独立函数，方便测试、替换和扩展。
- “photo-abstract-editorial” 不是本次 GitHub 检索中找到的准确仓库或已安装 Skill；本项目把它作为自定义风格命名，而不是声称复刻某个现成产品。

## 风格注册表

当前风格由 `STYLE_DESCRIPTIONS` 统一登记：

1. 极简保真：保留颜色、构图和主体细节，只做克制增强。
2. 简约线条：减少纹理和杂点，保留主体轮廓。
3. 铅笔素描：灰度笔触和柔和明暗。
4. 黑白线稿：清晰的黑白边缘。
5. 漫画轮廓：更粗、更醒目的轮廓。
6. 编辑感抽象：色块、量化色彩和轻微轮廓叠加。
7. 复古胶片：暖色、颗粒和暗角。
8. 高对比海报：适合封面和海报的二值化效果。
