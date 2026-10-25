"""End-to-end upload/queue/processing contract against a real local Gradio server."""
import socket
import json
import zipfile
import numpy as np
from PIL import Image
from gradio_client import Client, handle_file
from test_lineart import make_sample


def test_real_upload_and_style_response(tmp_path):
    import app
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    options=app.launch_options();options.update(server_port=port,prevent_thread_lock=True,quiet=True,ssr_mode=False)
    source=tmp_path/'sample.png';make_sample().save(source)
    try:
        app.demo.launch(**options)
        client=Client(f'http://127.0.0.1:{port}',verbose=False,download_files=str(tmp_path/'results'))
        original,output,report=client.predict(handle_file(str(source)),"简约线条",.45,.60,api_name='/apply_style')
        assert '处理完成' in report
        with Image.open(output) as result:
            assert result.size==(320,240)
            assert np.count_nonzero(np.asarray(result)[:,:,0]<128)>200
        assert original
        batch=client.predict(handle_file(str(source)),"轮廓与线条",api_name='/direct_styles')
        gallery,observations,trace,recommendations,archive,svg,preview,variant,description,style,intensity,detail,comparison=batch
        assert len(gallery)==3 and 'palette-swatch' in observations and 'director-trace' in trace
        assert style=='简约线条' and 0<=intensity<=1 and 0<=detail<=1
        assert preview and variant and len(comparison)==2 and svg.endswith('.svg')
        with zipfile.ZipFile(archive) as zipped:
            manifest=json.loads(zipped.read('manifest.json'))
            assert len(manifest['variants'])==3 and len(manifest['tools'])==4
            assert source.name not in json.dumps(manifest)
        assert '规则建议' in description and '01 /' in recommendations
    finally:
        app.demo.close()
