from difflib import SequenceMatcher
from pathlib import Path
import re
path=Path(r'C:\logs\PAFPlayer\dj.log')
entries=[x for x in path.read_text(encoding='utf8').split('━━━━━━━━━━━━━━━━━━━━━━') if '⭐DATE:' in x]
texts=[' '.join(re.findall(r'^[👩👨]🗣️ (.*)$',entry,re.M)).casefold() for entry in entries]
for previous,current in zip(texts,texts[1:]):
 print('adjacent_similarity',round(SequenceMatcher(None,previous,current).ratio(),3),'exact',previous==current)
