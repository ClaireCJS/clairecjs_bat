import json
import os
from pathlib import Path
import subprocess
import sys
from image_caption_gender_fixer import imaging

ROOT=Path(os.environ.get('ICGF_TEST_INSTALLATION',Path(__file__).resolve().parents[2]))


def test_redirected_json_is_utf8_with_legacy_windows_encoding(tmp_path):
    launcher=ROOT/'image_caption_gender_fixer.py'
    source=tmp_path/'caption é 日本 😀.png'
    _,_,Image,_,_,_,_,_=imaging.libraries()
    Image.new('RGB',(50,50),'white').save(source)
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    result=subprocess.run([sys.executable,'-B','-I','-S','-X','utf8=0',str(launcher),'rules','explain',source.name,'--json'],
                          cwd=tmp_path,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr.decode('utf-8',errors='replace')
    parsed=json.loads(result.stdout.decode('utf-8'))
    assert source.name in json.dumps(parsed,ensure_ascii=False)
    assert b'\x1b' not in result.stdout
    assert before=={p.name:p.read_bytes() for p in tmp_path.iterdir()}
