---
name: style-director
description: "维护 Photo Style Gallery 的风格导演、图像分析、多风格试片、前后对比与SVG或套装导出。"
---

# style-director

1. 先读 PRODUCT.md、DESIGN.md、style_director.py、image_input.py 与 lineart_core.py。界面位于app.py，数值逻辑独立于Gradio。

2. 分析、风格建议及试片必须来自实际图片和滤镜输出；传统图像算法不冒充生成式模型。解释说明可观测亮度/边缘，不推断人物敏感属性。

3. 保留上传字节、真实格式、解码前像素限制及单并发队列；预览、试片和矢量轮廓均须有尺寸和数量上限。

4. 导出SVG只由程序生成的路径与数字构造，禁止嵌入上传内容的脚本/外链；文件套装带参数、算法版本及来源摘要，不打包原始上传文件。

5. 验证用 python -m pytest -q，覆盖轮廓/亮部回绕原反例、新的试片/导出边界及真实Gradio端到端。

6. 界面验证原图与结果切换、键盘和减少动态效果；远程数据与缓存说明保持准确。

在线版入口与构建见docs/ONLINE.md。浏览器和服务版本共用核心；修改后运行npm run test:online，保留以上在线能力边界，不把浏览器会话标成云端同步。
