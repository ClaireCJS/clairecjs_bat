"""Staged AI DJ scheduling primitives; no network or player side effects on import."""
from collections import deque
from dataclasses import dataclass
import threading

@dataclass(frozen=True)
class Settings:
    enabled: bool = False
    history: int = 10
    interval: int = 2
    seconds: int = 90
    speakers: int = 2
    women: int = 2
    men: int = 0

def validate_settings(value, changed=None):
    def number(key, lo, hi, default):
        v=value.get(key,default)
        if isinstance(v,bool): raise ValueError(key)
        try: v=int(v)
        except (TypeError,ValueError): raise ValueError(key)
        if not lo<=v<=hi: raise ValueError(key)
        return v
    enabled=value.get('enabled',False)
    if type(enabled) is not bool: raise ValueError('enabled')
    total=number('speakers',1,10,2)
    men=number('men',0,total,0)
    women=number('women',0,total,total-men)
    if changed=='women': men=total-women
    else: women=total-men
    return Settings(enabled,number('history',1,100,10),number('interval',1,50,2),number('seconds',15,600,90),total,women,men)

class Scheduler:
    """Per-session history and a single generation lease, protected by a lock."""
    def __init__(self, settings=Settings()):
        self.lock=threading.RLock(); self.settings=settings
        self.history=deque(maxlen=100); self.since=0; self.generation=0
        self.working=None; self.ready=None; self.forced=False; self.error=None
    def configure(self, settings):
        with self.lock:
            self.settings=settings; self.generation+=1; self.ready=None; self.forced=False
    def played(self, artist, title):
        with self.lock:
            self.history.append({'artist':str(artist or '')[:300],'title':str(title or '')[:300]})
            self.since+=1
    def begin(self, force=False):
        with self.lock:
            if force:self.forced=True
            if self.ready is not None or self.working is not None:return None
            if not self.history:return None
            if not force and (not self.settings.enabled or self.since<max(1,self.settings.interval-1)):return None
            self.generation+=1; token=self.generation; self.working=token;self.error=None
            return token,list(self.history)[-self.settings.history:],self.settings
    def finish(self, token, result=None, error=None):
        with self.lock:
            if self.working==token:self.working=None
            if token!=self.generation:return False
            self.error=error;self.ready=result if not error else None
            return True
    def take(self):
        with self.lock:
            if self.ready is None:return None
            if not self.forced and (not self.settings.enabled or self.since<self.settings.interval):return None
            result=self.ready;self.ready=None;self.since=0;self.forced=False
            return result
    def cancel(self):
        with self.lock:
            self.generation+=1;self.ready=None;self.forced=False
