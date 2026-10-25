# FORM在线工坊部署

公开入口：https://5503gj.github.io/photo-style-gallery/ 。访客不需要安装Python、不需要Key或账号。

浏览器Worker通过Pyodide 0.28.3实际运行原有lineart_core.py、image_input.py和style_director.py，使用NumPy/Pillow/OpenCV生成预览、三款试片、SVG与ZIP。

## 能力与数据边界

首次加载约28MB引擎；资源随Pages托管。图片不上传，原图与结果保留在页面/Worker内存。关闭/清除释放，下载文件由用户保存。低内存设备可能较慢；非多租户云端队列。

原有Python服务不被替换。浏览器版与服务版的存储和连接方式不同，不能把页面会话当作企业持久化、云端同步或身份认证。

## 构建与验证

运行 `python scripts/build_online.py`，再运行 `npm run test:online`。构建目录dist仅包含公开资源，不包含.git、.env或服务端密钥。dist和运行时缓存忽略提交。

工作流 `.github/workflows/test.yml` 在原测试通过后构建、执行在线浏览器回归；仅main推送发布，部署依赖测试成功。浏览器测试以子目录路径提供资源，实际调用工具和导出，验证响应式并检查没有本地API或上传请求。

## Python/WebAssembly运行时

使用[Pyodide官方Worker模式](https://pyodide.org/en/0.28.3/usage/webworker.html)及[包目录](https://pyodide.org/en/0.28.3/usage/packages-in-pyodide.html)，锁定0.28.3。构建时获取运行时与wheel并校验锁文件及包SHA256，随后全部发布在本站，不在访客运行时依赖外部CDN。许可证随runtime/LICENSE提供，各wheel保留自身许可证。

Python算法源码由构建脚本从原模块打包进python-source.zip，避免另写一套近似算法。浏览器版OpenCV等依赖版本由Pyodide锁定，与服务版的像素输出不承诺逐位完全相同。
