from pathlib import Path
import ast
h=Path(__file__).parent;d=(h/'PAFPlayer_dj_candidate_v6.py').read_text(encoding='utf8')
old="""            result=subprocess.run([exe,'-m',model,'-f',str(path)],input=line.encode('utf8'),
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or not path.is_file() or path.stat().st_size<=44: raise RuntimeError('Piper speech failed')"""
new="""            process=subprocess.Popen([exe,'-m',model,'-f',str(path)],stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            try:
                process.stdin.write(line.encode('utf8'));process.stdin.close()
                deadline=time.monotonic()+120
                while process.poll() is None:
                    if not valid() or time.monotonic()>=deadline:
                        process.terminate()
                        try:process.wait(timeout=2)
                        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
                        if not valid():raise InterruptedError()
                        raise RuntimeError('Piper speech timed out')
                    time.sleep(.1)
                if process.returncode or not path.is_file() or path.stat().st_size<=44: raise RuntimeError('Piper speech failed')
            finally:
                if process.poll() is None:process.terminate()"""
assert d.count(old)==1;d=d.replace(old,new,1);compile(d,'dj','exec')
with (h/'PAFPlayer_dj_candidate_v7.py').open('x',encoding='utf8',newline='\n') as f:f.write(d)
s=(h/'PAFPlayer_candidate_v8.py').read_text(encoding='utf8');tree=ast.parse(s);v=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[v.lineno-1].encode('utf8');lines[v.lineno-1]=(line[:v.col_offset]+repr(d).encode('utf8')+line[v.end_col_offset:]).decode('utf8');s=''.join(lines);compile(s,'candidate','exec')
with (h/'PAFPlayer_candidate_v9.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
t=(h/'test_providers_final.py').read_text(encoding='utf8').replace('PAFPlayer_dj_candidate_v6.py','PAFPlayer_dj_candidate_v7.py').replace('import importlib.util,json,os,threading,time,unittest','import importlib.util,io,json,os,threading,time,unittest')
a="""  def run(args,**kw):
   output=Path(args[args.index('-f')+1]);
   with output.open('xb') as f:f.write(b'0'*100)
   calls.append(args[args.index('-m')+1]);return SimpleNamespace(returncode=0)"""
b="""  def run(args,**kw):
   output=Path(args[args.index('-f')+1]);
   with output.open('xb') as f:f.write(b'0'*100)
   calls.append(args[args.index('-m')+1]);return SimpleNamespace(returncode=0,stdin=io.BytesIO(),poll=lambda:0)"""
assert t.count(a)==1;t=t.replace(a,b,1).replace("mock.patch.object(d.subprocess,'run',side_effect=run)","mock.patch.object(d.subprocess,'Popen',side_effect=run)")
with (h/'test_providers_final_v2.py').open('x',encoding='utf8',newline='\n') as f:f.write(t)
for old,new in [('test_playback_final.py','test_playback_final_v2.py'),('test_web_final.py','test_web_final_v2.py'),('check_web_final.py','check_web_final_v2.py'),('test_realtime_final.py','test_realtime_final_v2.py')]:
 t=(h/old).read_text(encoding='utf8').replace('PAFPlayer_candidate_v7.py','PAFPlayer_candidate_v9.py').replace('PAFPlayer_dj_candidate_v6.py','PAFPlayer_dj_candidate_v7.py')
 with (h/new).open('x',encoding='utf8',newline='\n') as f:f.write(t)
