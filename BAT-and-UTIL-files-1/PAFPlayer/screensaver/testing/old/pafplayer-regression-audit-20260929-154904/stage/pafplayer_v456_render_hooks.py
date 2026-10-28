from pafplayer_v456_stage1 import edit
from pafplayer_v416_edit import sub,ROOT,replace_file

def change(s):
    s=sub(s,'''            saturation: float = 1.0,
        ):
            """Color one lyric mask''','''            saturation: float = 1.0,
            workload: str = "artwork-lyrics",
        ):
            """Color one lyric mask''')
    s=sub(s,'''                    saturation=karaoke_saturation("floating", mode_index),
                )''','''                    saturation=karaoke_saturation("floating", mode_index),
                    workload="floating-lyrics",
                )''',2)
    s=sub(s,'            if shadow <= 0:\n                return field', '''            benchmark = paf_workflows().benchmark
            benchmark_state = {"phase": phase, "mode": mode, "palette": palette_index,
                               "emphasis": emphasis_progress, "timing": timing_type}
            if shadow <= 0:
                if benchmark is not None:
                    return benchmark.composite(Image.new("RGBA", mask.size), field,
                                               workload=workload, metadata=benchmark_state)
                return field''')
    s=sub(s,'            return Image.alpha_composite(shadow_layer, field)', '''            if benchmark is not None:
                return benchmark.composite(shadow_layer, field, workload=workload, metadata=benchmark_state)
            return Image.alpha_composite(shadow_layer, field)''')
    s=sub(s,'                state["floating_lyric_mask"] = mask\n                state["floating_lyric_photo"] = photo', '''                if paf_workflows().benchmark is not None:
                    paf_workflows().benchmark.present(rgba, window, render_started)
                state["floating_lyric_mask"] = mask
                state["floating_lyric_photo"] = photo''')
    s=sub(s,'                floating_canvas.itemconfigure(int(item), image=photo)\n            except Exception as exc:', '''                floating_canvas.itemconfigure(int(item), image=photo)
                if paf_workflows().benchmark is not None:
                    paf_workflows().benchmark.present(rgba, window, animation_started)
            except Exception as exc:''')
    return s

edit(change)
f=ROOT/'PAFPlayer_workflows.py'; s=f.read_text(encoding='utf-8')
s=sub(s,'        if self.monitor: self.monitor.close()', '        if self.monitor: self.monitor.close()\n        if self.benchmark: self.benchmark.close()')
s=sub(s,'                    if old is None or old[0]!=signature: self.pending[key]=(signature,now); continue', '''                    if old is None or old[0]!=signature:
                        self.pending[key]=(signature,now)
                        if dry_run: result.append({'path':str(path),'action':'pending-stability','mode':self.mode})
                        continue''')
# Runtime.log uses the application's diagnostic writer, whose hook fills the ring once.
s=sub(s,'''        with self.lock:
            self.sequence+=1
            self.events.append({'id':self.sequence,'time':time.time(),'level':'ERROR' if 'error' in event else 'INFO','category':event.split('.')[0],'message':redact(event+' '+json.dumps(fields,default=str))})
''','')
s=sub(s,'    text=str(value)\n    text=re.sub', '''    text=str(value)
    if re.search(r'(?i)upload',text): return text.split(' ',1)[0]+' [uploaded-file details redacted]'
    text=re.sub(r'(?i)("(?:token|password|secret|authorization|webhook|filename)"\\s*:\\s*)"[^"\\n]*"',r'\\1"[redacted]"',text)
    text=re.sub''')
replace_file(f,s)
