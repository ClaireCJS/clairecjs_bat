"""V519 guarded, retained baseline/candidate and focused regression checks."""
from pathlib import Path
import datetime,importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
MODULES=('test_v519_transport','test_v485_exact_frames','test_v486_speed')

def child(stage,mode):
    import psutil
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    for key in ('TEMP','TMP','LOCALAPPDATA','APPDATA'):os.environ[key]=str(stage)
    os.environ['PLAY_AUDIO_FILE_HISTORY_DB']=str(stage/'history.sqlite3')
    for key in tuple(os.environ):
        if key.startswith('LASTFM_') or key=='PAFPLAYER_DISCORD_WEBHOOK':os.environ.pop(key)
    tempfile.tempdir=str(stage);sys.path.insert(0,str(ROOT))
    from run_PAFPlayer_tests import install_guards
    sys.path.insert(0,str(stage));os.chdir(stage);install_guards(stage)
    import PAFPlayer
    if mode=='focused':
        suite=unittest.TestSuite()
        for name in MODULES:
            spec=importlib.util.spec_from_file_location(name,stage/'tests'/(name+'.py'))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    else:
        suite=unittest.defaultTestLoader.loadTestsFromModule(PAFPlayer)
        # Keep diagnostics bounded without weakening equality checks.
        def compact(left,right,*a,**k):
            import itertools
            for index,(x,y) in enumerate(itertools.zip_longest(left,right)):
                if x!=y:
                    yield 'First differing line '+str(index);yield '- '+str(x)[:600];yield '+ '+str(y)[:600];return
        unittest.case.difflib.ndiff=compact
    result=unittest.TextTestRunner(verbosity=1,stream=sys.stdout).run(suite)
    value={'mode':mode,'tests':result.testsRun,'failures':[str(t) for t,e in result.failures],
           'errors':[str(t) for t,e in result.errors],'skipped':[str(t) for t,e in result.skipped]}
    print('RESULT_JSON '+json.dumps(value))
    return 0 if result.wasSuccessful() else 1

def main():
    stamp=datetime.datetime.now().strftime('%Y%m%d%H%M%S');results=[]
    base=ROOT/'tests'/('v519-validation-'+stamp);base.mkdir()
    for mode,source in (('baseline',ROOT/'releases/PAFPlayer_v518_lockscreen_stable_lyrics.py'),('candidate',ROOT/'PAFPlayer.py'),('focused',ROOT/'PAFPlayer.py')):
        stage=base/mode;stage.mkdir();shutil.copyfile(source,stage/'PAFPlayer.py')
        if mode=='focused':
            (stage/'tests').mkdir();(stage/'releases').mkdir()
            for name in MODULES:shutil.copyfile(ROOT/'tests'/(name+'.py'),stage/'tests'/(name+'.py'))
            for name in ('PAFPlayer_v485_artwork_fps_and_responsive_bass.py','PAFPlayer_v518_lockscreen_stable_lyrics.py'):shutil.copyfile(ROOT/'releases'/name,stage/'releases'/name)
        report=ROOT/'tests/reports'/('v519-'+mode+'-'+stamp+'.txt')
        with report.open('xb') as log:
            proc=subprocess.run([sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--child',str(stage),mode],stdout=log,stderr=subprocess.STDOUT,timeout=600)
        lines=report.read_text(encoding='utf-8').splitlines()
        matches=[line[len('RESULT_JSON '):] for line in lines if line.startswith('RESULT_JSON ')]
        if not matches:raise RuntimeError('Missing test summary: '+str(report))
        result=json.loads(matches[-1]);result['report']=str(report.relative_to(ROOT));results.append(result)
        print(json.dumps({'mode':mode,'tests':result['tests'],'failures':len(result['failures']),'errors':len(result['errors']),'skipped':len(result['skipped']),'report':str(report)}),flush=True)
    a,b,f=results
    summary={'runs':results,'new_failures':sorted(set(b['failures'])-set(a['failures'])),'new_errors':sorted(set(b['errors'])-set(a['errors'])),'removed_failures':sorted(set(a['failures'])-set(b['failures']))}
    path=ROOT/'tests/reports'/('v519-comparison-'+stamp+'.json')
    with path.open('x',encoding='utf-8') as out:json.dump(summary,out,indent=2)
    print('Comparison:',path)
    return int(bool(summary['new_failures'] or summary['new_errors'] or f['failures'] or f['errors']))

if __name__=='__main__':raise SystemExit(child(Path(sys.argv[2]),sys.argv[3]) if '--child' in sys.argv else main())
