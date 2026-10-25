from pathlib import Path
import shutil,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist';OUT.mkdir(exist_ok=True)
shutil.copytree(ROOT/'online',OUT,dirs_exist_ok=True)
with zipfile.ZipFile(OUT/'python-source.zip','w',zipfile.ZIP_DEFLATED) as zipped:
    for name in ('lineart_core.py','image_input.py','style_director.py'):
        zipped.write(ROOT/name,name)
    zipped.write(ROOT/'online/browser_bridge.py','browser_bridge.py')
shutil.copy2(ROOT/'assets/still-life.png',OUT/'still-life.png')
from vendor_pyodide import vendor
vendor(OUT/'runtime',ROOT/'.runtime-cache')
(OUT/'.nojekyll').touch()
