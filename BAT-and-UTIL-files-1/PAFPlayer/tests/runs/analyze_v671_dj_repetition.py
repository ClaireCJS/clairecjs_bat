from difflib import SequenceMatcher
from pathlib import Path
import hashlib,json,os,re
path=Path(r'C:\logs\PAFPlayer\dj.log')
if path.is_file():
 entries=[x for x in path.read_text(encoding='utf8').split('━━━━━━━━━━━━━━━━━━━━━━') if '⭐DATE:' in x]
 print('conversation_entries:',len(entries))
 for entry in entries[-8:]:
  date=re.search(r'⭐DATE:\s*(.*)',entry)
  tracks=re.findall(r'^⛧LAST SONG #\d+: (.*)$',entry,re.M)
  turns=re.findall(r'^[👩👨]🗣️ (.*)$',entry,re.M)
  text=' '.join(turns).casefold()
  print(json.dumps({'date':date.group(1) if date else '', 'tracks':len(tracks),'turns':len(turns),'text_digest':hashlib.sha256(text.encode()).hexdigest()[:12],'track_digest':hashlib.sha256('\n'.join(tracks).encode()).hexdigest()[:12]}))
 for a,b in zip(entries[-8:],entries[-7:]):
  extract=lambda e:' '.join(re.findall(r'^[👩👨]🗣️ (.*)$',e,re.M)).casefold()
  print('adjacent_text_similarity:',round(SequenceMatcher(None,extract(a),extract(b)).ratio(),3))
base=Path(os.environ.get('LOCALAPPDATA',''))/'PAFPlayer/workflows/dj-logs'
for f in sorted(base.glob('dj-*.jsonl'),key=lambda p:p.stat().st_mtime,reverse=True)[:2]:
 data=[]
 for line in f.read_text(encoding='utf8').splitlines():
  try:
   event=json.loads(line)
   if event.get('event') in ('job.started','job.joined','job.ready','job.taken','text.provider.success'):data.append({k:event.get(k) for k in ('event','job','provider','count','history_count','forced','audio_files') if k in event})
  except ValueError:pass
 print('recent_session:',json.dumps(data[-25:]))
