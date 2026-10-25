"""Browser adapter reuses the same image tools as the Python/Gradio application."""
import base64
import io
import json
from pathlib import Path
import shutil
from image_input import load_upload
from lineart_core import prepare_image,process_image,STYLE_NAMES
from style_director import build_batch

OUTPUT=Path('/app/generated')

def encoded(image):
    buffer=io.BytesIO();image.save(buffer,format='PNG')
    return 'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()

def clear():
    if OUTPUT.exists():shutil.rmtree(OUTPUT)
    Path('/app/upload.bin').unlink(missing_ok=True)

def dispatch(raw):
    request=json.loads(raw);action=request['action']
    if action=='clear':clear();return '{}'
    if action=='preview':return json.dumps({'source':encoded(prepare_image(load_upload('/app/upload.bin'),1000))})
    if action=='manual':
        image=load_upload('/app/upload.bin')
        result,report=process_image(image,request['style'],request['intensity'],request['detail'],max_side=1000)
        return json.dumps({'source':encoded(prepare_image(image,1000)),'result':encoded(result),'report':report.to_markdown()})
    if action!='direct':raise ValueError('未知工具')
    if OUTPUT.exists():shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    batch=build_batch('/app/upload.bin',request['purpose'],OUTPUT)
    return json.dumps({'manifest':batch['manifest'],'source':encoded(prepare_image(load_upload('/app/upload.bin'),1000)),
        'variants':[{'image':'data:image/png;base64,'+base64.b64encode(Path(item[0]).read_bytes()).decode(),'style':item[1]} for item in batch['gallery']],
        'zip':base64.b64encode(Path(batch['archive']).read_bytes()).decode(),
        'svg':Path(batch['svg']).read_text(encoding='utf8')},ensure_ascii=False)
