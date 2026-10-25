"""FORM image studio, with local image-tool orchestration and real exports."""
from __future__ import annotations
import os
import math
from pathlib import Path
import tempfile

os.environ.setdefault('GRADIO_TEMP_DIR', tempfile.mkdtemp(prefix='photo-style-'))
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')

import gradio as gr
from PIL import Image
from artifact_cache import ArtifactCache
from image_input import MAX_FILE_BYTES, load_upload
from lineart_core import STYLE_NAMES, prepare_image, process_image
from style_director import PURPOSES, analysis_html, build_batch, tools_html

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / 'assets/still-life.png'
CSS = (ROOT / 'studio.css').read_text(encoding='utf-8')
CACHE = ArtifactCache(parent=os.environ['GRADIO_TEMP_DIR'])


def transform(filename: str | None, style: str, intensity: float, detail: float):
    if filename is None:
        return None, None, '**还没有生成**\n\n请先上传一张 JPG 或 PNG 图片。'
    try:
        image = load_upload(filename)
        result, report = process_image(image, style, intensity, detail)
        return prepare_image(image,800), result, report.to_markdown()
    except (ValueError,TypeError) as exc:
        return None, None, f'**处理失败**\n\n{exc}'
    except Exception:
        return None, None, '**处理失败**\n\n处理服务暂时不可用，请稍后重试。'


def comparison_pair(original, result):
    if original is None or result is None:
        return None
    left, right = prepare_image(original,800), prepare_image(result,800)
    if right.size != left.size:
        right = right.resize(left.size,Image.Resampling.LANCZOS)
    return left,right


def comparison_position(value):
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or not 0<=value<=100:
        raise gr.Error('对比位置需为0至100的有限数值')
    return gr.update(slider_position=value)


def source_preview(filename):
    if filename is None:
        return None, None, '<p class="empty-caption">上传后，滑动中线比较原图与结果。</p>'
    try:
        image=prepare_image(load_upload(filename),800)
        return image,(image,image),'<p class="empty-caption">原图已就绪。选择用途，运行风格导演，或手动应用风格。</p>'
    except (ValueError,TypeError) as exc:
        raise gr.Error(str(exc)) from exc


def run_director(filename, purpose, progress=gr.Progress()):
    if not filename:
        raise gr.Error('先上传一张图片，或使用左侧的几何静物示例。')
    directory=CACHE.create()
    try:
        batch=build_batch(filename,purpose,directory,progress)
        manifest=batch['manifest'];first=manifest['variants'][0]
        with Image.open(batch['preview']) as source:
            original=source.copy()
        with Image.open(batch['gallery'][0][0]) as image:
            result=image.copy()
        report=f"**{first['style']}** · 强度 {first['intensity']:.2f} · 细节 {first['detail']:.2f}\n\n{first['reason']}"
        recommendations='\n\n'.join(f"**{index+1:02d} / {row['style']}**\n\n{row['reason']}" for index,row in enumerate(manifest['variants']))
        return batch['gallery'],analysis_html(manifest['analysis']),tools_html(manifest['tools']),recommendations,batch['archive'],batch['svg'],batch,original,result,report,first['style'],first['intensity'],first['detail'],comparison_pair(original,result)
    except (ValueError,TypeError) as exc:
        CACHE.discard(directory)
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        CACHE.discard(directory)
        raise gr.Error('试片生成失败，请重试；原图未修改。') from exc


def select_variant(batch, evt:gr.SelectData):
    index=evt.index
    if not isinstance(index,int) or isinstance(index,bool) or not batch or not 0<=index<len(batch.get('gallery',[])):
        raise gr.Error('请先生成试片，再点击一个方案。')
    source_path,result_path=batch['preview'],batch['gallery'][index][0]
    if not CACHE.contains(source_path) or not CACHE.contains(result_path):
        raise gr.Error('这批试片已过期，请重新运行风格导演。')
    proposal=batch['manifest']['variants'][index]
    with Image.open(source_path) as image:
        original=image.copy()
    with Image.open(result_path) as image:
        result=image.copy()
    return proposal['style'],proposal['intensity'],proposal['detail'],original,result,comparison_pair(original,result),f"**{proposal['style']}**\n\n{proposal['reason']}"


def clear_editor(batch):
    if batch and batch.get('directory'):
        CACHE.discard(batch['directory'])
    return None,None,None,[], '<p class="analysis-empty">生成后，这里显示主色与画面观察。</p>', '<p class="trace-empty">分析 → 选择技能 → 生成试片 → 导出准备</p>', '', None,None,{},'图片已从界面清除；服务器下载缓存仍按周期清理。'


def launch_options() -> dict:
    host=os.environ.get('PHOTO_HOST','127.0.0.1');auth=None
    if host not in ('127.0.0.1','localhost','::1'):
        user,password=os.environ.get('PHOTO_AUTH_USER'),os.environ.get('PHOTO_AUTH_PASSWORD','')
        if not user or len(password)<12:
            raise ValueError('对外监听必须配置PHOTO_AUTH_USER与至少12字符的PHOTO_AUTH_PASSWORD')
        auth=(user,password)
    theme=gr.themes.Base(primary_hue='orange',neutral_hue='stone',font=['system-ui','Microsoft YaHei','sans-serif'])
    return dict(server_name=host,server_port=int(os.environ.get('PORT','7860')),auth=auth,share=False,show_error=False,max_file_size=MAX_FILE_BYTES,blocked_paths=[str(ROOT/name) for name in ('.git','.env')],css=CSS,theme=theme)


with gr.Blocks(title='FORM · 影像风格工坊',delete_cache=(60,900),analytics_enabled=False) as demo:
    batch_state=gr.State({},time_to_live=900)
    with gr.Column(elem_id='form-studio'):
        gr.HTML('<header class="studio-top"><a href="#" class="studio-brand"><b>f.</b><span>FORM<small>影像风格工坊</small></span></a><div class="studio-nav"><span>STYLE STUDIO</span><span class="local-chip"><i></i>本地图像工具</span></div></header><section class="studio-intro"><div><p class="studio-eyebrow">A LITTLE DIFFERENT. STILL YOURS.</p><h1>同一张照片，<br>另一种视觉语言。</h1></div><p>从真实的颜色与轮廓出发，探索三种风格。<br>先看见差别，再找到适合你的那一个。</p></section>')
        with gr.Row(elem_id='editor-layout',equal_height=False):
            with gr.Column(scale=3,min_width=250,elem_id='studio-controls'):
                gr.HTML('<div class="panel-caption">01 / SOURCE & DIRECTION</div><h2 class="studio-section-title">一张图，一个方向</h2>')
                input_image=gr.File(type='filepath',file_types=['.jpg','.jpeg','.png'],label='上传原图',elem_id='source-upload')
                sample_button=gr.Button('试试几何静物示例',variant='secondary',elem_id='sample-button')
                gr.HTML('<p class="control-note">JPG / PNG · ≤10MiB · ≤1200万像素<br>示例为本项目程序绘制，不含外部素材。</p>')
                purpose=gr.Radio(list(PURPOSES),value=PURPOSES[0],label='这张图，想用在哪里？',elem_id='purpose-select')
                director=gr.Button('运行风格导演  ↗',variant='primary',elem_id='director-button')
                with gr.Accordion('自己微调，也很好',open=False,elem_id='manual-controls'):
                    style=gr.Dropdown(list(STYLE_NAMES),value='极简保真',label='风格')
                    intensity=gr.Slider(0,1,value=.45,step=.05,label='风格强度')
                    detail=gr.Slider(0,1,value=.60,step=.05,label='细节保留')
                    run=gr.Button('应用风格',variant='secondary',elem_id='apply-button')
                gr.HTML('<div class="privacy-copy"><span>在你的选择里，保留主导权。</span><p>本地运行时图片传到本机；远程访问时会上传服务器。无需模型、Key 或 GPU。</p></div>')
            with gr.Column(scale=7,min_width=360,elem_id='studio-canvas'):
                gr.HTML('<div class="canvas-heading"><div><span class="panel-caption">02 / SEE THE DIFFERENCE</span><h2 class="studio-section-title">让差别，自己说话。</h2></div><span class="canvas-tip">拖动中线，对比原图</span></div>')
                with gr.Tabs(elem_id='canvas-tabs'):
                    with gr.Tab('前后对比'):
                        comparison=gr.ImageSlider(type='pil',height=430,max_height=500,label='原图 / 当前结果',show_label=False,elem_id='compare-stage',interactive=False)
                    with gr.Tab('单张结果'):
                        output_image=gr.Image(type='pil',label='当前结果',height=430,interactive=False,elem_id='result-image')
                position=gr.Slider(0,100,value=50,step=1,label='对比位置（键盘←/→可调）',elem_id='comparison-position')
                preview_image=gr.Image(type='pil',label='本次处理原图',visible=False)
                stage_note=gr.HTML('<p class="empty-caption">上传一张照片，或使用示例开始。生成后可以拖动中线比较。</p>')
                report=gr.Markdown('所有处理都由实际图像算法完成，风格参数可继续调整。',elem_id='result-report')
                gr.HTML('<div class="trial-heading"><div><span class="panel-caption">03 / TRY THREE WAYS</span><h2 class="studio-section-title">一次探索，三种可能。</h2></div><span>点击试片，切换主画布</span></div>')
                gallery=gr.Gallery(label='风格试片',show_label=False,columns=3,rows=1,height=210,object_fit='contain',allow_preview=False,interactive=False,elem_id='trial-gallery')
            with gr.Column(scale=3,min_width=230,elem_id='director-inspector'):
                gr.HTML('<div class="panel-caption">THE DIRECTOR DESK</div><h2 class="studio-section-title">每一步，都有依据</h2>')
                analysis=gr.HTML('<p class="analysis-empty">生成后，这里显示主色与画面观察。</p>')
                trace=gr.HTML('<p class="trace-empty">分析 → 选择技能 → 生成试片 → 导出准备</p>')
                with gr.Accordion('为什么推荐这些风格？',open=False):
                    recommendations=gr.Markdown('先选择用途并生成试片。')
                gr.HTML('<div class="export-caption">TAKE IT WITH YOU</div>')
                archive=gr.File(label='下载试片套装 · ZIP',interactive=False,elem_id='kit-download')
                svg_file=gr.File(label='原图轮廓 · SVG',interactive=False,elem_id='svg-download')
                gr.HTML('<p class="export-note">套装含三张PNG、SVG和参数清单，不打包原始上传文件。SVG是轮廓提取，适合继续编辑。</p>')
        gr.HTML('<footer class="studio-footer"><span>FORM / 本地图像实验 · 规则工具 Agent</span><p>导出源缓存最多保留最近8批，15分钟无访问后可清理；下载缓存每分钟扫描，清理年龄超过15分钟的文件。界面清除不保证即时磁盘擦除；异常关闭可能影响清理，请及时下载。</p></footer>')
    position.change(comparison_position,position,comparison,queue=False,api_name=False)
    sample_button.click(lambda:str(SAMPLE),outputs=input_image,api_name=False)
    input_image.change(source_preview,input_image,[preview_image,comparison,stage_note],api_name=False)
    run.click(transform,[input_image,style,intensity,detail],[preview_image,output_image,report],concurrency_limit=1,concurrency_id='photo-worker',api_name='apply_style').then(comparison_pair,[preview_image,output_image],comparison,api_name=False)
    director.click(run_director,[input_image,purpose],[gallery,analysis,trace,recommendations,archive,svg_file,batch_state,preview_image,output_image,report,style,intensity,detail,comparison],concurrency_limit=1,concurrency_id='photo-worker',api_name='direct_styles')
    gallery.select(select_variant,batch_state,[style,intensity,detail,preview_image,output_image,comparison,report],api_name=False)
    input_image.clear(clear_editor,batch_state,[preview_image,output_image,comparison,gallery,analysis,trace,recommendations,archive,svg_file,batch_state,report],api_name=False)

demo.queue(max_size=8,default_concurrency_limit=1,api_open=False)
if __name__=='__main__':
    demo.launch(**launch_options())
