"""Opt-in paired live CPU/CUDA alpha-compositing experiment.

The experiment accelerates the final lyric/shadow composition, including
floating lyrics. Glyph shaping, tone generation and Tk presentation remain
unchanged and are included in observed presentation latency. CPU stays visible
through startup, warm-up, unavailable CUDA, mismatches and failed transfers.
"""
from PAFPlayer_workflows import *


class Benchmark:
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.closed=False; self.started=time.perf_counter(); self.session=uuid.uuid4().hex; self.frame=0; self.good=0
        self.cp=None; self.reason='CUDA warm-up pending'; self.pending={}; self.lock=threading.Lock(); self.records=queue.Queue(maxsize=256); self.dropped=0
        self.writer=threading.Thread(target=self._write,name='paf-cuda-log',daemon=True); self.writer.start()
        self.record({'kind':'session','workload':'lyric-shadow-composite','window_seconds':10,'presentation_clock':'Tk after_idle, not physical display scanout'})
        self.warmup=threading.Thread(target=self._initialize,name='paf-cuda-warmup',daemon=True); self.warmup.start()

    def record(self,data):
        value={'session':self.session,'timestamp':time.time(),**data}
        try: self.records.put_nowait(value)
        except queue.Full: self.dropped+=1

    def _write(self):
        while True:
            record=self.records.get()
            if record is None: self.records.task_done(); return
            try:
                if self.path.exists() and self.path.stat().st_size>32*1024*1024:
                    target=unique(self.path.with_name(self.path.name+'.previous.jsonl'))
                    self.path.rename(target)
                with self.path.open('a',encoding='utf-8') as out: out.write(json.dumps(record,separators=(',',':'))+'\n')
            except OSError as exc: self.reason='Benchmark log unavailable: '+type(exc).__name__
            finally: self.records.task_done()

    def _initialize(self):
        start=time.perf_counter()
        try:
            import cupy as cp
            cp.cuda.runtime.getDeviceCount()
            cp.asnumpy(cp.zeros((2,2),dtype=cp.float32)); cp.cuda.get_current_stream().synchronize()
            self.cp=cp; self.reason=''
        except Exception as exc: self.reason='CUDA unavailable: '+type(exc).__name__
        self.record({'kind':'warmup','milliseconds':(time.perf_counter()-start)*1000,'fallback':self.reason})

    def cuda_composite(self,background,foreground):
        import numpy as np
        from PIL import Image
        cp=self.cp
        start=time.perf_counter()
        bottom=cp.asarray(np.asarray(background),dtype=cp.float32); top=cp.asarray(np.asarray(foreground),dtype=cp.float32)
        cp.cuda.get_current_stream().synchronize(); upload=(time.perf_counter()-start)*1000
        e1=cp.cuda.Event(); e2=cp.cuda.Event(); e1.record()
        a=top[:,:,3:4]/255; b=bottom[:,:,3:4]/255; outa=a+b*(1-a)
        rgb=(top[:,:,:3]*a+bottom[:,:,:3]*b*(1-a))/cp.maximum(outa,1e-10)
        result=cp.concatenate((rgb,outa*255),axis=2)
        result=cp.clip(cp.floor(result+.5),0,255).astype(cp.uint8)
        e2.record(); e2.synchronize(); gpu=float(cp.cuda.get_elapsed_time(e1,e2))
        start=time.perf_counter(); host=cp.asnumpy(result); download=(time.perf_counter()-start)*1000
        return Image.fromarray(host,'RGBA'),{'gpu_ms':gpu,'upload_ms':upload,'download_ms':download}

    def composite(self,background,foreground, *, workload='lyrics',metadata=None):
        from PIL import Image
        import numpy as np
        started=time.perf_counter(); self.frame+=1; frame=self.frame
        cpu_start=time.perf_counter(); cpu=Image.alpha_composite(background,foreground); cpu_ms=(time.perf_counter()-cpu_start)*1000
        desired='cpu' if int((started-self.started)/10)%2==0 else 'cuda'
        row={'kind':'frame','frame':frame,'workload':workload,'size':list(background.size),'desired':desired,'visible':'cpu','cpu_ms':cpu_ms,'cuda_ms':None,'fallback':self.reason,'warmup':self.good<3,'mismatch_pixels':None,'max_channel_error':None,'state':metadata or {},'input_sha256':hashlib.sha256(background.tobytes()+foreground.tobytes()).hexdigest(),'dropped_log_records':self.dropped}
        visible=cpu
        if self.cp is not None:
            try:
                start=time.perf_counter(); gpu,measurements=self.cuda_composite(background,foreground); row['cuda_ms']=(time.perf_counter()-start)*1000; row.update(measurements)
                diff=np.abs(np.asarray(cpu).astype(np.int16)-np.asarray(gpu).astype(np.int16)); row['max_channel_error']=int(diff.max()); row['mismatch_pixels']=int(np.any(diff>1,axis=2).sum())
                if row['mismatch_pixels']==0:
                    self.good+=1
                    if desired=='cuda' and self.good>=3: visible=gpu; row['visible']='cuda'
                else: row['fallback']='Correctness mismatch; CPU retained'
            except Exception as exc: row['fallback']='CUDA frame failed: '+type(exc).__name__
        row['pair_ms']=(time.perf_counter()-started)*1000
        visible.info['paf_benchmark_frame']=(frame,started)
        with self.lock:
            self.pending[frame]=row
            # Non-presented previews are still reported, never silently called presented.
            if len(self.pending)>64:
                key=next(iter(self.pending)); old=self.pending.pop(key); old['presentation']='not observed'; self.record(old)
        return visible

    def present(self,image,window,render_started=None):
        marker=image.info.get('paf_benchmark_frame')
        if not marker: return
        frame,started=marker; before_idle=time.perf_counter()
        def done():
            with self.lock: row=self.pending.pop(frame,None)
            if row is None: return
            end=time.perf_counter(); row['end_to_end_ms']=(end-(render_started or started))*1000
            row['presentation_ms']=(end-before_idle)*1000
            row['missed_frames_60hz']=max(0,int(row['end_to_end_ms']/(1000/60))-1)
            # Remove only the measured shadow path from an explicitly labelled estimate.
            shadow=row['cpu_ms'] if row['visible']=='cuda' else (row['cuda_ms'] or 0)
            row['estimated_without_shadow_ms']=max(0,row['end_to_end_ms']-shadow)
            row['presentation']='tk-idle-observed'; self.record(row)
        window.after_idle(done)

    def close(self):
        if self.closed:return
        self.closed=True
        with self.lock:
            for row in self.pending.values(): row['presentation']='not observed'; self.record(row)
            self.pending.clear()
        self.warmup.join(timeout=1)
        try: self.records.put(None,timeout=1)
        except queue.Full: return
        self.writer.join(timeout=2)


def analyze(path):
    groups={}; fallbacks={}; skipped=0
    with Path(path).open(encoding='utf-8') as source:
        for line in source:
            try: row=json.loads(line)
            except ValueError: skipped+=1; continue
            if row.get('fallback'): fallbacks[row['fallback']]=fallbacks.get(row['fallback'],0)+1
            if row.get('kind')!='frame': continue
            key=row.get('workload','unknown')+' '+str(row.get('size'))
            groups.setdefault(key,[]).append(row)
    result={}
    def stats(values): return {'samples':len(values),'median_ms':statistics.median(values),'worst_ms':max(values)} if values else {'samples':0}
    for key,rows in groups.items():
        eligible=[x for x in rows if not x.get('warmup') and not x.get('mismatch_pixels') and x.get('cuda_ms') is not None]
        cpu=[x['cpu_ms'] for x in eligible]; cuda=[x['cuda_ms'] for x in eligible]
        cpu_e2e=[x['end_to_end_ms'] for x in eligible if x.get('visible')=='cpu' and 'end_to_end_ms' in x]
        cuda_e2e=[x['end_to_end_ms'] for x in eligible if x.get('visible')=='cuda' and 'end_to_end_ms' in x]
        enough=len(cpu_e2e)>=10 and len(cuda_e2e)>=10
        result[key]={'frames':len(rows),'paired_cpu':stats(cpu),'paired_cuda_including_transfers':stats(cuda),'gpu_kernel':stats([x['gpu_ms'] for x in eligible if 'gpu_ms' in x]),'upload':stats([x['upload_ms'] for x in eligible if 'upload_ms' in x]),'download':stats([x['download_ms'] for x in eligible if 'download_ms' in x]),'cpu_visible_end_to_end':stats(cpu_e2e),'cuda_visible_end_to_end':stats(cuda_e2e),'warmup_frames':sum(bool(x.get('warmup')) for x in rows),'correctness_mismatches':sum(bool(x.get('mismatch_pixels')) for x in rows),'missed_frames_60hz':sum(x.get('missed_frames_60hz',0) for x in rows),'cuda_improves_observed_end_to_end':statistics.median(cuda_e2e)<statistics.median(cpu_e2e) if enough else None,'conclusion':'Insufficient matched presentation samples' if not enough else 'Compare measured alternating windows; observed latency includes paired shadow work'}
    return {'log':str(path),'workloads':result,'fallback_reasons':fallbacks,'malformed_records':skipped,'scope':'Final lyric/shadow compositing, including floating lyrics. Tk-idle timing is not physical display scanout.'}
