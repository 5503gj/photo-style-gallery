# FORM · 影像风格工坊

一个可本地运行的图片处理网站：上传随手拍，应用线稿、胶片、海报和编辑感抽象等风格。

## 项目亮点

- OpenCV确定性滤镜，无第三方模型调用。本机运行时传到本机服务；远程访问时会上传到运行应用的服务器。
- 八种可调风格，包括优先保留原图的“极简保真”、减少杂点的“简约线条”、编辑感抽象、复古胶片和高对比海报
- 支持大图自动缩放
- 风格导演：读取实际亮度、边缘密度与主色，根据用途推荐参数，生成三张真实试片
- 点击试片切换主画布，滑动中线或键盘调节前后对比；支持手动继续微调
- 导出三张PNG、原图轮廓SVG与参数清单ZIP，记录源图SHA256、算法参数和工具耗时
- 暖纸色三栏编辑器，手机布局、焦点反馈与减少动态效果支持
- 配套可复用 `photo-to-lineart-skill`
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
image_input.py                 # 字节/格式/像素限制，在解码前检查
lineart_core.py                # 图像处理核心
test_lineart.py                # 基础测试
skills/photo-to-lineart-skill/ # 可复用 Skill
```

## 验证与部署边界

使用 Python 3.10+。`pip install -r requirements-dev.txt` 后运行 `python -m pytest -q`。
CI在干净环境安装已锁定依赖并执行算法、输入和部署配置回归。

核心参数强度和细节须为0–1有限数，`max_side`须为1–1600整数；非法值明确拒绝。
JPG/PNG上传限制10MiB、1200万像素、最长边16000px，先查实际格式和头部尺寸再解码。
滤镜单任务并发，队列最多8项。透明图以白底合成，尊重EXIF方向。

默认只监听127.0.0.1。若确需对外监听，设置`PHOTO_HOST`，同时设置`PHOTO_AUTH_USER`
和至少12字符的`PHOTO_AUTH_PASSWORD`；缺少配置会拒绝启动。公网部署仍需HTTPS反向代理、
网关上传/速率限制和独立低权限运行账户。内建共享登录不等于企业多租户授权。

上传及结果会进入Gradio临时缓存，清理器每60秒移除年龄超过900秒的文件。
清除界面不保证立即从磁盘擦除，进行中的长任务/关闭进程也可能影响清理时点；敏感数据服务需独立验证留存和删除流程。
不要把`allowed_paths`设成整个项目/磁盘。缓存不是不同用户间的强隔离边界。

回归覆盖矩形与圆轮廓保留、高光单调且不回绕、全部风格基本输出、参数拒绝、PNG头部像素限制、
伪格式/损坏文件、透明和方向处理、网络监听失败关闭。
这些测试证明所测数值和边界行为；真实人像/产品/复杂背景的视觉满意度仍需真实样例盲评，
内存/延迟SLO、并发压力、升级漏洞扫描及生产删除审计仍是企业采用前的条件。

## 参考与原创说明

本项目参考了 OpenCV 素描算法、[LingDong-/linedraw](https://github.com/LingDong-/linedraw) 的线条化思路、[Gradio](https://github.com/gradio-app/gradio) 的交互方式、[ControlNet Lineart](https://github.com/lllyasviel/ControlNet-v1-1-nightly) 的线稿控制概念，以及 [Banuba AI Skills](https://github.com/Banuba/ai-skills) 对图片编辑 Skill 的组织方式。

实现代码、界面、参数设计、测试用例和文档为本项目自行组织，不复制上述仓库的代码或素材。`photo-abstract-editorial` 在本次 GitHub 检索中没有找到准确匹配，因此本项目将“编辑感抽象”作为自定义的本地图像滤镜实现，而不是声称复刻某个现成 Skill。

## 新功能验证与 Skill

`python -m pytest -q`：36项测试，包含真实Gradio上传及两条处理接口、SVG边界、实际ZIP内容、
颜色统计、缓存容量与过期清理。`npm ci`、`npx playwright install chromium`、`npm run test:browser`
验证示例→生成→方案切换→键盘对比→ZIP下载→清除，以及桌面/平板/手机和减少动画。

`style_director.py`负责分析、建议、渲染和导出；`artifact_cache.py`最多保留8批导出源，
15分钟无访问后由后台定时清理。它与Gradio下载缓存是两层缓存，均不等于用户隔离或即时安全擦除。
示例由`scripts/make_demo.py`程序绘制。仓库内的[Style Director Skill](skills/style-director/SKILL.md)
说明维护和扩展方式。设计参考及未引入框架的取舍见[设计参考](docs/DESIGN_REFERENCES.md)。

风格导演是确定性规则工具流程，不调用LLM，也不声称预测审美满意度；SVG为轮廓提取，
并非完整语义矢量化。当前为单图的多风格试片，不是多文件批处理。

## 后续路线

1. 多文件批处理与任务恢复
2. 真实人像/产品/复杂背景的盲评集和延迟基准
3. 可选模型风格增强与费用控制
4. 企业多租户、留存审计与生产部署
