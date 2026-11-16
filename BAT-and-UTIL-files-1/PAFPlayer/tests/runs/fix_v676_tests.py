from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def rep(p,s,archive):
 n=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(n);i=0
 while b.exists():i+=1;b=p.with_name(n[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest();p.write_text(s,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
p=root/'tests/test_v673_voice_models.py';s=p.read_text(encoding='utf8');assert 'def synth(model,text,gender,output,root=None):' in s;s=s.replace('def synth(model,text,gender,output,root=None):','def synth(model,text,gender,output,root=None,progress=None):');rep(p,s,root/'backups')
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf8');a=s.index('    def test_v90_editor_handoff_clicks_editor_before_alt_escape_and_focus_restore');b=s.index('    def test_v90_web_defaults_',a);s=s[:a]+'''    def test_editor_handoff_opens_without_changing_other_windows(self) -> None:
        import inspect
        source = inspect.getsource(open_txt_path_then_restore_foreground)
        self.assertIn("open_paths_in_txt_handler", source)
        self.assertNotIn("mouse_event", source)
        self.assertNotIn("keybd_event", source)

'''+s[b:];compile(s,str(p),'exec');rep(p,s,root/'releases');rep(root/'releases/PAFPlayer_v676_dj_model_ui.py',s,root/'releases')
print('Updated regression checks with verified backups.')
