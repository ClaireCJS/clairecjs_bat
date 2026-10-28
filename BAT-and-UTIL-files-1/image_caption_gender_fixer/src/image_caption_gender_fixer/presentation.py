"""Terminal presentation only; structured results retain plain original strings."""
import re
import shutil
import sys
import textwrap
from difflib import SequenceMatcher

GREEN='\x1b[92m'
YELLOW='\x1b[93m'
CYAN='\x1b[96m'
RESET='\x1b[0m'

def color(text,code,enabled=None):
    if enabled is None: enabled=sys.stderr.isatty()
    return code+str(text)+RESET if enabled else str(text)

def prompt(message,default=''):
    labels={'c':'cancel','s':'skip','n':'no','y':'yes','o':'once','1':'1'}
    hint='ENTER='+labels.get(default,default or 'keep current / leave blank')
    # Prompts quoting previously recognized text use the source color.
    message=re.sub(r"('[^'\n]*'|\"[^\"\n]*\")",lambda m:color(m.group(),GREEN),message)
    message=re.sub(r'\[[^\]\n]+\]',lambda m:color(m.group(),CYAN),message)
    return message.rstrip()+' '+color('('+hint+')',CYAN)+' '

def comparison(detected,proposed,width=None,enabled=None):
    width=width or shutil.get_terminal_size((120,40)).columns
    if width<64:
        return color('📖 Detected caption\n'+detected,GREEN,enabled)+'\n'+color('✨ Proposed caption\n'+proposed,YELLOW,enabled)
    col=max(12,(width-5)//2)
    out=[color('📖 Detected caption'.ljust(col),GREEN,enabled)+'  │  '+color('✨ Proposed caption',YELLOW,enabled)]
    left=detected.splitlines();right=proposed.splitlines()
    for kind,a,b,c,d in SequenceMatcher(None,left,right,autojunk=False).get_opcodes():
        for i in range(max(b-a,d-c)):
            old=left[a+i] if a+i<b else '';new=right[c+i] if c+i<d else ''
            ls=textwrap.wrap(old,col,replace_whitespace=True) or ['']
            rs=textwrap.wrap(new,col,replace_whitespace=True) or ['']
            for j in range(max(len(ls),len(rs))):
                l=ls[j] if j<len(ls) else '';r=rs[j] if j<len(rs) else ''
                out.append(color(l.ljust(col),GREEN,enabled)+'  │  '+color(r,YELLOW,enabled))
    return '\n'.join(out)

class Initializing:
    """A single bounded status line; never leaves ANSI in pipes or JSON."""
    def __init__(self,enabled): self.enabled=enabled;self.visible=False
    def update(self,message):
        if not self.enabled:return
        width=max(10,shutil.get_terminal_size((80,40)).columns-1)
        sys.stderr.write('\r\x1b[2K'+color(('⏳ '+message)[:width],CYAN,True));sys.stderr.flush();self.visible=True
    def clear(self):
        if self.visible:sys.stderr.write('\r\x1b[2K');sys.stderr.flush();self.visible=False
