from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
 while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8')
s=once(s,'def reject_repeated_dialogue(lines, previous):',"class RepeatedDJDialogue(ValueError):\n    pass\n\n\ndef reject_repeated_dialogue(lines, previous):")
s=once(s,"            raise ValueError('Provider repeated a recent DJ conversation')","            _dj_event('text.repetition_rejected')\n            raise RepeatedDJDialogue('Provider repeated a recent DJ conversation')")
s=once(s,"data=json.dumps(context,ensure_ascii=False); mode=opts['text_provider']; notices=[];last_error=None", "data=json.dumps(context,ensure_ascii=False); mode=opts['text_provider']; notices=[];last_error=None;repeated_error=None")
s=once(s,"            notices.append('OpenAI text failed');last_error=exc", "            notices.append('OpenAI text failed');last_error=exc\n            if isinstance(exc,RepeatedDJDialogue):repeated_error=exc")
s=once(s,"            notices.append(provider+' text failed');last_error=exc", "            notices.append(provider+' text failed');last_error=exc\n            if isinstance(exc,RepeatedDJDialogue):repeated_error=exc")
s=once(s,"        _dj_event('text.provider.failed',provider='ollama',**_error_fields(exc))\n        raise exc from last_error", "        _dj_event('text.provider.failed',provider='ollama',**_error_fields(exc))\n        if repeated_error and not isinstance(exc,RepeatedDJDialogue):raise repeated_error from exc\n        raise exc from last_error")
a="self.error=(str(exc) if isinstance(exc, PiperSetupError) else ('DJ speech failed; text is available in Help. Check OpenAI and Piper settings' if published else 'DJ text generation failed; check OpenAI and Ollama settings'))"
b="self.error=('AI DJ rejected repeated commentary; try #djforce or change provider' if isinstance(exc,RepeatedDJDialogue) else str(exc) if isinstance(exc, PiperSetupError) else ('DJ speech failed; text is available in Help. Check OpenAI and Piper settings' if published else 'DJ text generation failed; check OpenAI and Ollama settings'))"
s=once(s,a,b);compile(s,str(src),'exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines);compile(text,str(p),'exec')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v671_dj_variety.py',text,root/'releases')
print('Added explicit repetition diagnostics and user-facing failure status.')
