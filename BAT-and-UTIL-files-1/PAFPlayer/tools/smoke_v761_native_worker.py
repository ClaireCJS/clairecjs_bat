from pathlib import Path
import importlib.util,subprocess,json
root=Path.cwd();s=importlib.util.spec_from_file_location('cache',root/'src/PAFPlayer_startup_cache.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
command=m.audio_worker_command(root/'PAFPlayer.py')
config={'outputs':[],'command':[],'output_channels':2,'sample_rate':48000,'bit_depth':16,'buffer_ms':250}
p=subprocess.run(command,input=json.dumps(config)+'\n',capture_output=True,text=True,timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
report={'compiled_worker': '-c' in command,'exit_code':p.returncode,'status':p.stdout.strip(),'stderr':p.stderr.strip(),'note':'Native runtime worker protocol smoke test with zero output devices and EOF; no audio produced.'}
assert p.returncode==0,report
path=root/'tests/reports/v761-native-worker-protocol.json';assert not path.exists();path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
