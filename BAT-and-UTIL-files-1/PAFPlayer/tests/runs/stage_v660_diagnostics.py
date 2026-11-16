from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=(root/'src/PAFPlayer_dj.py').read_text(encoding='utf8')
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
src=once(src,'import urllib.request\n','import urllib.request\nimport urllib.error\n')
anchor='def dialogue(history, opts):\n'
helper='''_DJ_THREAD_CONTEXT = threading.local()


def _dj_event(event, **fields):
    callback = getattr(_DJ_THREAD_CONTEXT, 'log', None)
    if callback:
        try: callback(event, **fields)
        except Exception: pass


def _error_fields(exc):
    # Never record exception messages, response bodies, headers, paths, or keys.
    result = {'error_type': type(exc).__name__}
    if isinstance(exc, urllib.error.HTTPError): result['http_status'] = int(exc.code)
    return result


class DJLog:
    """Private, append-only, per-session diagnostics without track metadata."""
    def __init__(self, runtime):
        self.path = None
        self.lock = threading.Lock()
        root = getattr(runtime, 'root', None)
        if root is None: return
        try:
            directory = Path(root) / 'dj-logs'
            directory.mkdir(parents=True, exist_ok=True)
            fd, path = tempfile.mkstemp(prefix='dj-', suffix='.jsonl', dir=str(directory))
            os.close(fd); self.path = Path(path)
        except OSError: pass

    def write(self, event, **fields):
        if not self.path: return
        record = {'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'event': event, **fields}
        try:
            with self.lock, self.path.open('a', encoding='utf8') as stream:
                stream.write(json.dumps(record, ensure_ascii=True, separators=(',', ':')) + '\\n')
        except (OSError, TypeError, ValueError): pass


'''
src=once(src,anchor,helper+anchor)
src=once(src,"        value=post_json('https://api.openai.com/v1/responses',","        _dj_event('text.provider.start', provider='openai')\n        value=post_json('https://api.openai.com/v1/responses',")
src=once(src,"        result=parse_dialogue(text,opts['speakers'])\n    except Exception:","        result=parse_dialogue(text,opts['speakers'])\n        _dj_event('text.provider.success', provider='openai', turns=len(result))\n    except Exception as exc:\n        _dj_event('text.provider.fallback', provider='openai', **_error_fields(exc))")
src=once(src,"        value=post_json('http://127.0.0.1:11434/api/chat',","        _dj_event('text.provider.start', provider='ollama')\n        value=post_json('http://127.0.0.1:11434/api/chat',")
src=once(src,"        result=parse_dialogue(value['message']['content'],opts['speakers'])\n    return result,warning","        result=parse_dialogue(value['message']['content'],opts['speakers'])\n        _dj_event('text.provider.success', provider='ollama', turns=len(result))\n    return result,warning")
src=once(src,"            try: speech_openai(line,selected_voices[(speaker-1)%len(selected_voices)],opts['accent'],opts['speech_model'],path)\n            except Exception:\n                local=True;warning=", "            try:\n                _dj_event('speech.provider.start', provider='openai', turn=index)\n                speech_openai(line,selected_voices[(speaker-1)%len(selected_voices)],opts['accent'],opts['speech_model'],path)\n            except Exception as exc:\n                _dj_event('speech.provider.fallback', provider='openai', **_error_fields(exc))\n                local=True;warning=")
src=once(src,"        if local:\n            if not exe or not voices:","        if local:\n            _dj_event('speech.provider.start', provider='piper', turn=index)\n            if not exe or not voices:")
src=once(src,"        self.runtime=runtime;self.producer=producer;self.lock=threading.RLock()","        self.runtime=runtime;self.producer=producer;self.lock=threading.RLock()\n        self.log=DJLog(runtime)")
src=once(src,"        self.play_thread=None;self.play_process=None;self.play_cancel=threading.Event();self.play_done=False","        self.play_thread=None;self.play_process=None;self.play_cancel=threading.Event();self.play_done=False\n        self.log.write('controller.start', enabled=self.options['enabled'], interval=self.options['interval'], text_provider=self.options['text_provider'], speech_provider=self.options['speech_provider'])")
src=once(src,"            self.runtime.settings['ai_dj']=dict(self.options);self.runtime.save_settings()","            self.log.write('settings.changed', enabled=self.options['enabled'], interval=self.options['interval'], text_provider=self.options['text_provider'], speech_provider=self.options['speech_provider'])\n            self.runtime.settings['ai_dj']=dict(self.options);self.runtime.save_settings()")
src=once(src,"return {'settings':dict(self.options),'stage':self.stage if self.forced else '',","return {'settings':dict(self.options),'stage':self.stage, 'history_count':len(self.history), 'tracks_since_commentary':self.count,")
src=once(src,"            return (tuple(self.commentary), self.stage, self.error, self.notice, self.options['enabled'])","            stage = self.stage\n            if not stage and self.options['enabled']:\n                stage = f'Waiting for played tracks ({self.count}/{self.options[\"interval\"]})'\n            return (tuple(self.commentary), stage, self.error, self.notice, self.options['enabled'])")
src=once(src,"            self.forced=False\n        if prepare:self.start(False)","            self.forced=False\n            self.log.write('track.recorded', count=self.count, interval=self.options['interval'], prepare=bool(prepare))\n        if prepare:self.start(False)")
src=once(src,"            if self.play_thread and self.play_thread.is_alive():return True\n            if forced:self.forced=True\n            if self.ready or self.working is not None:return True", "            if self.play_thread and self.play_thread.is_alive():\n                self.log.write('job.skipped', reason='playing', forced=bool(forced));return True\n            if forced:self.forced=True\n            if self.ready or self.working is not None:\n                self.log.write('job.joined', forced=bool(forced), ready=bool(self.ready), working=self.working is not None);return True")
src=once(src,"                self.forced=False;self.error='Play a track first';return False","                self.forced=False;self.error='Play a track first';self.log.write('job.skipped', reason='no_history', forced=bool(forced));return False")
src=once(src,"            if not forced and (self.error or not self.options['enabled'] or self.count<max(1,self.options['interval']-1) or self.attempted==self.count):return False", "            if not forced and (self.error or not self.options['enabled'] or self.count<max(1,self.options['interval']-1) or self.attempted==self.count):\n                reason = 'previous_error' if self.error else 'disabled' if not self.options['enabled'] else 'interval' if self.count<max(1,self.options['interval']-1) else 'already_attempted'\n                self.log.write('job.skipped', reason=reason, count=self.count, interval=self.options['interval']);return False")
src=once(src,"            history=history[-self.options['history']:];opts=dict(self.options);self.error='';self.stage='Preparing'","            history=history[-self.options['history']:];opts=dict(self.options);self.error='';self.stage='Preparing'\n            self.log.write('job.started', job=token, forced=bool(forced), history_count=len(history), count=self.count)")
src=once(src,"                if token==self.serial:self.stage=message", "                if token==self.serial:\n                    self.stage=message;self.log.write('job.stage', job=token, stage=message)")
src=once(src,"                    self.commentary=list(lines);published.append(True)","                    self.commentary=list(lines);published.append(True);self.log.write('text.ready', job=token, turns=len(lines))")
src=once(src,"        def work():\n            try:\n                if self.producer is synthesize:","        def work():\n            _DJ_THREAD_CONTEXT.log=self.log.write\n            try:\n                if self.producer is synthesize:")
src=once(src,"                    if valid():self.ready=result;self.notice=warning;self.stage='Ready'\n            except InterruptedError:pass", "                    if valid():\n                        self.ready=result;self.notice=warning;self.stage='Ready';self.log.write('job.ready', job=token, audio_files=len(result))\n            except InterruptedError:\n                self.log.write('job.cancelled', job=token)")
src=once(src,"            except Exception as exc:\n                with self.lock:\n                    if valid():", "            except Exception as exc:\n                self.log.write('job.failed', job=token, text_ready=bool(published), **_error_fields(exc))\n                with self.lock:\n                    if valid():")
src=once(src,"            finally:\n                with self.lock:\n                    if self.working==token:self.working=None", "            finally:\n                _DJ_THREAD_CONTEXT.log=None\n                with self.lock:\n                    if self.working==token:self.working=None")
src=once(src,"            result=self.ready;self.ready=None;self.forced=False;self.count=0;self.stage='';return result", "            result=self.ready;self.ready=None;self.forced=False;self.count=0;self.stage='';self.log.write('job.taken', audio_files=len(result));return result")
src=once(src,"        with self.lock:self.serial+=1;self.forced=False;self.ready=None;self.stage=''", "        with self.lock:\n            self.log.write('job.cancel_requested', working=self.working is not None, ready=bool(self.ready), forced=self.forced)\n            self.serial+=1;self.forced=False;self.ready=None;self.stage=''")
src=once(src,"            self.play_cancel=threading.Event();self.play_done=False\n        def run():", "            self.play_cancel=threading.Event();self.play_done=False\n            self.log.write('play.started', audio_files=len(files))\n        def run():")
src=once(src,"            except Exception:\n                with self.lock:self.error='DJ audio playback failed'", "            except Exception as exc:\n                self.log.write('play.failed', **_error_fields(exc))\n                with self.lock:self.error='DJ audio playback failed'")
src=once(src,"                with self.lock:self.play_process=None;self.play_done=True", "                with self.lock:\n                    self.log.write('play.finished', cancelled=self.play_cancel.is_set())\n                    self.play_process=None;self.play_done=True")
src=once(src,"            if self.forced:\n                self.serial+=1;self.forced=False;self.ready=None;self.stage=''", "            if self.forced:\n                self.log.write('job.cancel_requested', reason='track_changed', forced=True)\n                self.serial+=1;self.forced=False;self.ready=None;self.stage=''")
compile(src,'candidate','exec');out=root/'tests/runs/PAFPlayer_dj_v660_candidate.py';assert not out.exists();out.write_text(src,encoding='utf8');print(out)
