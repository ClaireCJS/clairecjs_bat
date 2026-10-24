"""Isolated test runner using only this tool's bundled packages."""
import sys
sys.dont_write_bytecode = True
import os
from pathlib import Path
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"environment/packages")]
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"]="1"
os.environ["OMP_THREAD_LIMIT"]="1"
handles=[]
if os.name=="nt":
    for relative in ("environment/packages/numpy.libs","environment/packages/.dlls","environment/packages/PIL","environment/packages/cv2"):
        path=ROOT/relative
        if path.exists(): handles.append(os.add_dll_directory(str(path)))
import pytest

if __name__=="__main__":
    base=Path(tempfile.gettempdir())/("ICGFTests-"+uuid.uuid4().hex)
    report=ROOT/"tests/output"/("results-"+uuid.uuid4().hex+".xml")
    raise SystemExit(pytest.main([str(ROOT/"tests"),"--basetemp",str(base),"-o","cache_dir="+str(ROOT/"tests/output/cache"),"--junitxml="+str(report),*sys.argv[1:]]))
