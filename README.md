# 图片风格实验室 · Photo Style Gallery

一个可本地运行的图片处理网站：上传随手拍，应用线稿、胶片、海报和编辑感抽象等风格。

## 项目亮点

- 本地 OpenCV 处理，不上传图片
- 八种可调风格，包括优先保留原图的“极简保真”、减少杂点的“简约线条”、编辑感抽象、复古胶片和高对比海报
- 支持大图自动缩放
- Gradio 网站界面
- 配套可复用 `photo-to-lineart-skill`
- 内置本地风格 Agent：根据自然语言选择滤镜，并返回可解释的执行计划
- 包含基础自动化测试和参数报告
- [图片风格来源与实现目录](docs/image-style-catalog.md)

## 本地运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

浏览器打开 `http://127.0.0.1:7860`。

## 项目结构

```text
app.py                         # Gradio 网站
lineart_core.py                # 图像处理核心
agent/style_agent.py           # 风格意图识别 + 本地滤镜工作流
test_lineart.py                # 基础测试
skills/photo-to-lineart-skill/ # 可复用 Skill
```

## 参考与原创说明

本项目参考了 OpenCV 素描算法、[LingDong-/linedraw](https://github.com/LingDong-/linedraw) 的线条化思路、[Gradio](https://github.com/gradio-app/gradio) 的交互方式、[ControlNet Lineart](https://github.com/lllyasviel/ControlNet-v1-1-nightly) 的线稿控制概念，以及 [Banuba AI Skills](https://github.com/Banuba/ai-skills) 对图片编辑 Skill 的组织方式。

实现代码、界面、参数设计、测试用例和文档为本项目自行组织，不复制上述仓库的代码或素材。`photo-abstract-editorial` 在本次 GitHub 检索中没有找到准确匹配，因此本项目将“编辑感抽象”作为自定义的本地图像滤镜实现，而不是声称复刻某个现成 Skill。

## 后续路线

1. 增加 SVG 导出
2. 增加批量处理
3. 增加图片前后对比滑块
4. 增加可选 AI 风格增强
5. 部署到 Hugging Face Spaces
6. 再评估微信小程序：小程序前端 + 图片处理后端

## Agent 说明

当前风格 Agent 是一个无数据库、无外部 API 的确定性工作流：

```text
自然语言需求 → 风格意图识别 → 选择本地 OpenCV 滤镜 → 生成图片 → 返回执行 Trace
```

它不会把图片上传到第三方，也不会把本地滤镜包装成生成式模型。后续若接入真正的图像模型，可以保留同一层 Agent 编排，再把 `process_image` 替换为受控的图片生成工具。
