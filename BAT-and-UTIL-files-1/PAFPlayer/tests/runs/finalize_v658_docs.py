from pathlib import Path
import datetime, hashlib, shutil
root=Path(__file__).resolve().parents[2]
def update(path, data, archive):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'); backup=path.with_name(name); i=0
    while backup.exists():
        i+=1; backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup); assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf-8',newline='')
    dest=archive/backup.name; i=0
    while dest.exists():
        i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
readme=root/'docs/README.md'; text=readme.read_text(encoding='utf-8')
old='If cloud text fails, PAFPlayer tries an available local Ollama model (or the configured model).'
new='If cloud text fails, PAFPlayer tries the smallest installed local Ollama model (or the configured model), with a bounded context. Local model loading and generation can take minutes.'
assert old in text; text=text.replace(old,new,1)
old='V657’s cloud and Piper paths passed mocked tests but could not be verified live on this machine: the OpenAI request was unreachable, Ollama was not responding, and Piper was not installed.'
new='On the test machine, a local Ollama model generated dialogue in about 79 seconds after an earlier request timed out. The tested OpenAI key returned HTTP 401 and Piper was not installed; real speech remains unverified.'
assert old in text;text=text.replace(old,new,1);update(readme,text,root/'docs')
notes=root/'releases/PAFPlayer_v658_dj_help_commentary_release_notes.md'; text=notes.read_text(encoding='utf-8')
old='Ollama and local models were detected, but a live text result and real speech are not guaranteed by the automated tests.'
new='A local Ollama model produced real dialogue in approximately 79 seconds after an earlier request timed out. Automatic model selection now chooses the smallest installed model and bounds context size. Speech was not verified live; Piper was not installed.'
assert old in text;text=text.replace(old,new,1);update(notes,text,root/'releases')
print('Recorded live local-generation result and provider limitations.')
