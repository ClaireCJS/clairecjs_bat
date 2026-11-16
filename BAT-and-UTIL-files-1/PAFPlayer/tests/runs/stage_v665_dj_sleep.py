from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=(root/'src/PAFPlayer_dj.py').read_text(encoding='utf8')
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
src=once(src,'import hashlib\n','import hashlib\nimport math\nfrom datetime import datetime, timedelta, timezone\n')
src=once(src,"                text_provider='auto', speech_provider='auto', gemini_free_confirmed=False)","                text_provider='auto', speech_provider='auto', gemini_free_confirmed=False,\n                sleep_time='never', wake_time='sunrise', sunrise_zip='22312', sleep_when_locked=False)")
src=once(src,"    if type(value['enabled']) is not bool or type(value['gemini_free_confirmed']) is not bool: raise ValueError('Expected a checkbox')", "    if any(type(value[k]) is not bool for k in ('enabled','gemini_free_confirmed','sleep_when_locked')): raise ValueError('Expected a checkbox')\n    if value['sleep_time']!='never' and not re.fullmatch(r'(?:[01][0-9]|2[0-3]):00',str(value['sleep_time'])): raise ValueError('Invalid DJ sleep time')\n    if value['wake_time']!='sunrise' and not re.fullmatch(r'(?:[01][0-9]|2[0-3]):00',str(value['wake_time'])): raise ValueError('Invalid DJ wake time')\n    if value['sleep_time']!='never' and value['sleep_time']==value['wake_time']: raise ValueError('Sleep and wake times must differ')\n    if not isinstance(value['sunrise_zip'],str) or not re.fullmatch(r'[0-9]{5}',value['sunrise_zip']): raise ValueError('Enter a five-digit US ZIP code')")
anchor='class Controller:\n'
helper='''# The requested default ZIP is available offline; other US ZIPs are looked up
# asynchronously and cached as separate files for offline use on later starts.
DEFAULT_ZIP_COORDINATES = {'22312': (38.8191, -77.1484)}


def sunrise_minutes(day, latitude, longitude, tz):
    """Approximate local sunrise by NOAA fractional-year solar equations."""
    n=day.timetuple().tm_yday
    gamma=2*math.pi/365*(n-1)
    eq=229.18*(0.000075+0.001868*math.cos(gamma)-0.032077*math.sin(gamma)
               -0.014615*math.cos(2*gamma)-0.040849*math.sin(2*gamma))
    decl=(0.006918-0.399912*math.cos(gamma)+0.070257*math.sin(gamma)
          -0.006758*math.cos(2*gamma)+0.000907*math.sin(2*gamma)
          -0.002697*math.cos(3*gamma)+0.00148*math.sin(3*gamma))
    lat=math.radians(float(latitude))
    denominator=math.cos(lat)*math.cos(decl)
    if abs(denominator)<1e-12:return None
    cos_hour=(math.cos(math.radians(90.833))/denominator)-math.tan(lat)*math.tan(decl)
    if not -1<=cos_hour<=1:return None
    hour=math.degrees(math.acos(cos_hour))
    utc_minutes=720-4*(float(longitude)+hour)-eq
    instant=datetime.combine(day,datetime.min.time(),tzinfo=timezone.utc)+timedelta(minutes=utc_minutes)
    local=instant.astimezone(tz)
    if local.date()<day:local=(instant+timedelta(days=1)).astimezone(tz)
    elif local.date()>day:local=(instant-timedelta(days=1)).astimezone(tz)
    return local.hour*60+local.minute+local.second/60


class SunriseLocation:
    def __init__(self,runtime):
        self.root=Path(runtime.root)/'dj-sunrise-cache' if getattr(runtime,'root',None) else None
        self.lock=threading.Lock();self.values=dict(DEFAULT_ZIP_COORDINATES);self.active=set();self.last={}

    def get(self,zipcode):
        with self.lock:
            if zipcode in self.values:return self.values[zipcode]
            if self.root and self.root.is_dir():
                for path in sorted(self.root.glob('zip-'+zipcode+'-*.json'),reverse=True):
                    try:
                        with path.open('r',encoding='utf8') as stream:data=json.load(stream)
                        lat=float(data['lat']);lon=float(data['lon'])
                        if data.get('zip')==zipcode and -90<=lat<=90 and -180<=lon<=180:
                            self.values[zipcode]=(lat,lon);return self.values[zipcode]
                    except (OSError,ValueError,TypeError,KeyError):pass
            if zipcode not in self.active and time.monotonic()-self.last.get(zipcode,-1000)>300:
                self.active.add(zipcode);self.last[zipcode]=time.monotonic()
                threading.Thread(target=self._lookup,args=(zipcode,),name='paf-dj-zip',daemon=True).start()
        return None

    def _lookup(self,zipcode):
        try:
            req=urllib.request.Request('https://api.zippopotam.us/us/'+zipcode,headers={'User-Agent':'PAFPlayer DJ sunrise'})
            with urllib.request.urlopen(req,timeout=10) as response:data=json.loads(response.read(65536))
            place=data['places'][0];lat=float(place['latitude']);lon=float(place['longitude'])
            if not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Invalid coordinates')
            with self.lock:self.values[zipcode]=(lat,lon)
            if self.root:
                self.root.mkdir(parents=True,exist_ok=True)
                fd,path=tempfile.mkstemp(prefix='zip-'+zipcode+'-',suffix='.json',dir=str(self.root))
                with os.fdopen(fd,'w',encoding='utf8') as stream:json.dump({'zip':zipcode,'lat':lat,'lon':lon},stream)
        except (OSError,ValueError,TypeError,KeyError,IndexError):pass
        finally:
            with self.lock:self.active.discard(zipcode)


def sleep_evaluation(opts,now,locked,coordinates):
    """Return sleep reason and a visible fallback note; never perform I/O."""
    if opts['sleep_when_locked'] and locked:return 'screen locked',''
    if opts['sleep_time']=='never':return '',''
    start=int(opts['sleep_time'][:2])*60
    note=''
    if opts['wake_time']=='sunrise':
        wake=sunrise_minutes(now.date(),*coordinates,now.tzinfo) if coordinates else None
        if wake is None:
            wake=420;note='Sunrise unavailable for ZIP; using 7:00 AM until location is available.'
    else:wake=int(opts['wake_time'][:2])*60
    current=now.hour*60+now.minute+now.second/60
    asleep=(start<=current<wake) if start<wake else (current>=start or current<wake)
    return ('scheduled sleep' if asleep else ''),note


'''
src=once(src,anchor,helper+anchor)
src=once(src,"        self.commentary=[]\n        self.play_thread=", "        self.commentary=[]\n        self.sunrise_location=SunriseLocation(runtime)\n        self._sleep_cache_at=-1000.0;self._sleep_cache=('', '');self._last_sleep_reason=''\n        self.play_thread=")
src=once(src,"            self.options=settings({**self.options,**patch},changed);self.serial+=1;self.ready=None;self.forced=False;self.error=''", "            self.options=settings({**self.options,**patch},changed);self.serial+=1;self.ready=None;self.forced=False;self.error='';self._sleep_cache_at=-1000.0")
anchor='    def status(self):\n'
methods='''    def sleep_status(self):
        with self.lock:
            now_mono=time.monotonic()
            if now_mono-self._sleep_cache_at<1:return self._sleep_cache
            opts=dict(self.options);locked=False
            if opts['sleep_when_locked']:
                try:
                    app=getattr(self.runtime,'app',None)
                    probe=getattr(app,'windows_session_is_locked',None)
                    locked=bool(probe()) if callable(probe) else False
                except Exception:locked=False
            coords=None
            if opts['sleep_time']!='never' and opts['wake_time']=='sunrise':coords=self.sunrise_location.get(opts['sunrise_zip'])
            result=sleep_evaluation(opts,datetime.now().astimezone(),locked,coords)
            self._sleep_cache=result;self._sleep_cache_at=now_mono
            if result[0]!=self._last_sleep_reason:
                self.log.write('sleep.changed',sleeping=bool(result[0]),reason=result[0] or 'awake')
                self._last_sleep_reason=result[0]
            if not result[0] and self.error.startswith('AI DJ is asleep:'):self.error=''
            return result

'''
src=once(src,anchor,methods+anchor)
src=once(src,"            private = installed_piper()\n            return {'settings'", "            private = installed_piper()\n            sleep_reason,sleep_notice=self.sleep_status()\n            return {'sleeping':bool(sleep_reason),'sleep_reason':sleep_reason,'sleep_notice':sleep_notice,'settings'")
src=once(src,"'warnings':self.credit_warnings.messages(),", "'warnings':self.credit_warnings.messages()+([sleep_notice] if sleep_notice else []),")
src=once(src,"        with self.lock:return self.credit_warnings.messages()", "        with self.lock:\n            _reason,note=self.sleep_status()\n            return self.credit_warnings.messages()+([note] if note else [])")
src=once(src,"            stage = 'Ready for next song' if self.ready and not self.forced else self.stage", "            reason,_note=self.sleep_status()\n            stage = ('Asleep: '+reason) if reason else ('Ready for next song' if self.ready and not self.forced else self.stage)")
src=once(src,"    def start(self,forced=False,current=None):\n        with self.lock:\n            if self.play_thread", "    def start(self,forced=False,current=None):\n        with self.lock:\n            reason,_note=self.sleep_status()\n            if reason:\n                self.forced=False;self.error='AI DJ is asleep: '+reason\n                self.log.write('job.skipped',reason='sleeping');return False\n            if self.play_thread")
src=once(src,"            with self.lock:return token==self.serial and not self.runtime.stop_event.is_set()", "            with self.lock:return token==self.serial and not self.runtime.stop_event.is_set() and not self.sleep_status()[0]")
src=once(src,"        with self.lock:return bool(self.ready and (self.forced or (self.options['enabled'] and self.count>=self.options['interval'])))", "        with self.lock:return bool(not self.sleep_status()[0] and self.ready and (self.forced or (self.options['enabled'] and self.count>=self.options['interval'])))")
src=once(src,"                    while p.poll() is None:\n                        if self.play_cancel.wait(.1):\n                            p.terminate();break", "                    while p.poll() is None:\n                        if self.play_cancel.wait(.1) or self.sleep_status()[0]:\n                            self.play_cancel.set();p.terminate();break")
compile(src,'candidate','exec');p=root/'tests/runs/PAFPlayer_dj_v665_candidate.py';assert not p.exists();p.write_text(src,encoding='utf8');print(p)
