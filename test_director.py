import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageDraw
import pytest

from artifact_cache import ArtifactCache
from style_director import analyze_image, build_batch, outline_svg, propose_styles


def shape():
    image=Image.new('RGB',(360,240),(244,239,226))
    draw=ImageDraw.Draw(image)
    draw.rectangle((30,30,150,200),outline=(35,60,80),width=5)
    draw.ellipse((180,45,330,195),fill=(160,95,60),outline=(35,60,80),width=4)
    return image


def test_observations_are_real_pixels_not_invented_labels():
    data=analyze_image(Image.new('RGB',(40,30),'white'))
    assert data['brightness']==1 and data['contrast']==0 and data['edge_density']==0
    assert data['palette']==[{'hex':'#ffffff','share':1.0}]
    assert len(propose_styles(data,'轮廓与线条'))==3
    assert all(row['detail']==.8 for row in propose_styles(data,'轮廓与线条'))
    black=analyze_image(Image.new('RGB',(40,30),'black'))
    assert black['brightness']==0 and black['tone']=='偏暗'
    with pytest.raises(ValueError):
        propose_styles(data,'伪造用途')


def test_dense_texture_gets_a_different_parameter_proposal():
    values=np.indices((240,360)).sum(axis=0)//4%2*255
    image=Image.fromarray(values.astype(np.uint8)).convert('RGB')
    data=analyze_image(image)
    assert data['edge_density']>.12
    assert all(row['detail']==.45 for row in propose_styles(data,'自然与日常'))


def test_svg_is_bounded_editable_geometry_without_embedded_code():
    svg,metadata=outline_svg(shape())
    root=ET.fromstring(svg)
    assert root.tag=='{http://www.w3.org/2000/svg}svg'
    paths=root.findall('.//{http://www.w3.org/2000/svg}path')
    assert 2<=len(paths)<=600 and metadata['vertices']<=16000
    assert all(set(path.attrib)=={'d'} and path.attrib['d'].startswith('M') for path in paths)
    assert not any(token in svg for token in ['<script','<image','href=','onload='])
    _,limited=outline_svg(shape(),max_paths=2,max_vertices=10)
    assert limited['paths']<=2 and limited['vertices']<=10 and limited['truncated']
    white,empty=outline_svg(Image.new('RGB',(20,20),'white'))
    assert empty['paths']==0 and ET.fromstring(white) is not None


@pytest.mark.parametrize('options',[{'max_paths':0},{'max_paths':10000},{'max_vertices':float('inf')},{'max_vertices':True}])
def test_vector_limits_cannot_be_bypassed(options):
    with pytest.raises(ValueError):
        outline_svg(shape(),**options)


def test_generated_kit_has_three_actual_pngs_parameters_and_no_raw_upload(tmp_path):
    source=tmp_path/'private-user-filename.png';shape().save(source)
    folder=tmp_path/'exports';folder.mkdir()
    result=build_batch(str(source),'封面与海报',folder)
    assert len(result['gallery'])==3
    with zipfile.ZipFile(result['archive']) as zipped:
        assert set(zipped.namelist())=={'manifest.json','source-outline.svg','variant-01.png','variant-02.png','variant-03.png'}
        manifest=json.loads(zipped.read('manifest.json'))
        assert manifest['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
        assert source.name not in json.dumps(manifest) and str(tmp_path) not in json.dumps(manifest)
        assert len(manifest['tools'])==4 and all(row['elapsed_ms']>=0 for row in manifest['tools'])
        for row in manifest['variants']:
            with zipped.open(row['filename']) as handle, Image.open(handle) as image:
                assert list(image.size)==row['output_size'] and image.mode=='RGB' and max(image.size)<=1000
    assert len({Path(path).read_bytes() for path,_ in result['gallery']})==3


def test_owned_cache_ttl_and_capacity_never_delete_other_paths(tmp_path):
    clock=[0]
    cache=ArtifactCache(parent=tmp_path,ttl=10,maximum=1,clock=lambda:clock[0],background=False)
    outside=tmp_path/'outside';outside.mkdir();foreign=outside/'keep.txt';foreign.write_text('keep')
    try:
        first=cache.create();(first/'image.png').write_bytes(b'test')
        assert cache.contains(first/'image.png')
        assert not cache.contains(foreign)
        cache.discard(outside)
        assert foreign.read_text()=='keep'
        second=cache.create();assert not first.exists()
        (second/'image.png').write_bytes(b'test');clock[0]=11;cache.purge()
        assert not second.exists() and foreign.exists()
    finally:
        cache.close()
