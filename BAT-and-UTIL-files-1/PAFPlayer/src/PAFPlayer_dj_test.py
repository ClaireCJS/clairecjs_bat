"""Text-only, read-only DJ comparison using the player's real prompt and tracks."""
import json
import random
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path
import sys
import urllib.request

YELLOW='\033[1;93m'; CYAN='\033[1;96m'; RED='\033[1;91m'; GREEN='\033[1;92m'; ERROR='\033[1;91;3m'; RESET='\033[0m'


def running_playlist(app):
    from PAFPlayer_instance import Instance
    instance=Instance(app.paf_workflows())
    try:
        try:
            response=instance.forward({'dj_test_snapshot':True},timeout=5)
            entries=response.get('entries',[])
            if entries:return [Path(x) for x in entries]
        except (ValueError,OSError):
            # Older players already expose the same read-only queue over their
            # local web status endpoint; no playback or queue edits are sent.
            pass
        url='http://127.0.0.1:'+str(app.WEB_SERVER_PORT)+'/api/workflows/status'
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url,timeout=3) as response:
            data=json.load(response)
        entries=data.get('queue',{}).get('entries',[])
        if entries:return [Path(x) for x in entries]
    except (OSError,ValueError,TypeError):
        pass
    finally:
        instance.close()
    raise ValueError('No running player playlist found. Supply a playlist path; if web access is disabled, restart the running player with this version first.')


def ollama_models():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://127.0.0.1:11434/api/tags',timeout=3) as response:
            data=json.load(response)
        return [str(m['name']) for m in data.get('models',[]) if isinstance(m,dict) and m.get('name')],None
    except Exception:
        return [],'PAFPlayer cannot reach the Ollama API at 127.0.0.1:11434. If Ollama is already running, check its configured host/port and local access; do not reinstall it. Hosted free models can still work.'


def model_directory():
    return Path(os.environ.get('OLLAMA_MODELS') or (Path.home()/'.ollama'/'models'))


def stored_ollama_models():
    root=model_directory()/'manifests'
    try:
        result=[]
        for path in root.glob('*/*/*/*'):
            if not path.is_file(): continue
            registry,namespace,model,tag=path.relative_to(root).parts
            name=("" if namespace=="library" else namespace+"/")+model+":"+tag
            result.append(name)
        return sorted(set(result))
    except OSError:
        return []


def ollama_process_state():
    """Distinguish a running Ollama process from an answering model API."""
    if os.name!='nt':return 'unknown'
    found=[]
    for name in ('ollama.exe','ollama app.exe'):
        try:
            result=subprocess.run(['tasklist','/FI','IMAGENAME eq '+name,'/FO','CSV','/NH'],capture_output=True,text=True,timeout=4,check=False)
            output=(result.stdout+'\n'+result.stderr).casefold()
            if result.returncode or 'access is denied' in output or 'access denied' in output or 'error:' in output:return 'unknown'
            if name.casefold() in result.stdout.casefold():found.append(name)
        except (OSError,subprocess.TimeoutExpired):return 'unknown'
    return ', '.join(found) if found else 'none detected'


def ollama_instructions(args, out=None):
    """Report an evidence-based Ollama state and the next useful repair step."""
    out=out or sys.stdout
    if len(args)>1 or (args and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*',args[0])):
        print(ERROR+'Usage: pafplayer --ollamainstructions [model-name]'+RESET,file=out);return 2
    requested=args[0] if args else None
    visible,warning=ollama_models();stored=stored_ollama_models();root=model_directory()
    process=ollama_process_state();configured=os.environ.get('OLLAMA_MODELS','').strip()
    print('Ollama diagnostics (local checks only; no model is downloaded or generated).',file=out)
    print('Ollama process: '+process,file=out)
    print('Local API: '+('unreachable at http://127.0.0.1:11434' if warning else 'responding at http://127.0.0.1:11434'),file=out)
    print('Model store PAFPlayer checked: '+str(root),file=out)
    print('OLLAMA_MODELS environment: '+(configured or '(not set; Ollama normally uses its user profile model folder)'),file=out)
    print('Models visible to API: '+(', '.join(visible) if visible else 'none'),file=out)
    print('Model manifests found on disk: '+(', '.join(stored) if stored else 'none'),file=out)
    if warning:
        if process not in ('none detected','unknown'):
            print('State: Ollama is running, but its local model API is not reachable by PAFPlayer.',file=out)
            print('Next: check that this process serves 127.0.0.1:11434 and that local firewall/proxy settings allow loopback. Do not reinstall Ollama.',file=out)
        elif process=='none detected':
            print('State: no Ollama process or local API was detected.',file=out)
            print('Next: start the Ollama app once, then rerun this command. Install Ollama only if the app is absent.',file=out)
        else:
            print('State: the API is unreachable and Windows process status could not be checked.',file=out)
            print('Next: check the Ollama app and its server address, then rerun this command.',file=out)
        return 0
    if visible:
        print('State: Ollama is running and has an available model catalog.',file=out)
        hidden=sorted(set(stored)-set(visible))
        if hidden:print('Some on-disk model manifests remain hidden from this server: '+', '.join(hidden)+'. Check OLLAMA_MODELS and permissions.',file=out)
        targets=[requested] if requested else visible
        for model in targets:
            print('\n'+model+':',file=out)
            if model in visible:
                print('  Ready: select Ollama as a text provider and set this exact model name; then run pafplayer --djtest.',file=out)
            elif model in stored:
                print('  Ollama is running, but this model’s manifest is missing from its API catalog.',file=out)
                print('  Check the active server’s OLLAMA_MODELS folder and permissions; restart only after correcting its model-store setting.',file=out)
            else:
                print('  Not installed. To download it, run: ollama pull '+model,file=out)
        return 0
    if stored:
        print('State: Ollama is running and reachable, but its API returns zero models. PAFPlayer found manifests on disk.',file=out)
        print('Next steps:',file=out)
        print('  1. Confirm the Ollama server process uses this same model folder: '+str(root),file=out)
        print('  2. Check OLLAMA_MODELS and folder access for the Windows account that launched the server.',file=out)
        print('  3. After correcting the model-store setting, restart Ollama once and rerun --ollamainstructions.',file=out)
        print('  4. When a model appears above, select Ollama and that exact model in AI DJ settings, then run --djtest.',file=out)
        if requested:print('Requested model '+requested+(' is present in manifests.' if requested in stored else ' was not found in manifests.'),file=out)
        return 0
    print('State: Ollama is running, but its API catalog is empty and this user-profile model folder has no model manifests.',file=out)
    if requested:
        print('Next: install the requested model with `ollama pull '+requested+'`, or open `pafplayer --models` → Text models.',file=out)
    else:
        print('Next: use `pafplayer --models` → Text models to compare or download a model. GPT-OSS 120B needs about 65 GB.',file=out)
    return 0



def ai_self_repair(app, *, input_fn=input, out=None):
    """Read-only AI DJ diagnosis with explicit prompts before setup actions."""
    out=out or sys.stdout
    from PAFPlayer_dj import provider_key, settings as dj_settings, installed_piper, installed_piper_male, TEXT_PRECEDENCE_LABELS
    from PAFPlayer_model_storage import preferred_root
    print('PAFPlayer AI DJ evaluation. No paid model calls are made; an optional text check uses free providers only.',file=out)
    options=dj_settings(app.paf_workflows().settings.get('ai_dj',{}))
    for name,env in (('OpenAI','OPENAI_API_KEY'),('OpenRouter','OPENROUTER_API_KEY'),('Gemini','GEMINI_API_KEY / GOOGLE_API_KEY')):
        configured=bool(provider_key(env.split(' / ')[0]) or (env.endswith('GOOGLE_API_KEY') and provider_key('GOOGLE_API_KEY')))
        print(f'  {name}: '+('key detected (value hidden)' if configured else 'no key detected'),file=out)
    root=preferred_root();print('  Model folder: '+str(root)+(' (exists)' if root.is_dir() else ' (not created yet)'),file=out)
    piper_root=root/'Piper';piper=installed_piper(piper_root);male=installed_piper_male(piper_root)
    print('  Piper: '+('ready · '+piper[0] if piper else 'not installed or incomplete'),file=out)
    print('  Piper voices: '+str(int(bool(piper))+int(bool(male)))+' detected',file=out)
    visible,warning=ollama_models();stored=stored_ollama_models()
    print('  Ollama process: '+ollama_process_state(),file=out)
    print('  Ollama API: '+('unreachable at 127.0.0.1:11434' if warning else 'responding'),file=out)
    print('  Ollama models: '+(', '.join(visible) if visible else 'none reported'),file=out)
    if not visible and stored:print('  Repair hint: Ollama is running, but its API lists zero models while model files exist. Check the active server’s OLLAMA_MODELS folder and permissions; restart only after correcting that setting.',file=out)
    if not any(provider_key(x) for x in ('OPENAI_API_KEY','OPENROUTER_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY')) and not visible:
        print('  Diagnosis: no configured hosted key or reachable local text model; DJ text generation has no working provider.',file=out)
    elif visible or any(provider_key(x) for x in ('OPENAI_API_KEY','OPENROUTER_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY')):
        print('  Diagnosis: at least one text provider is configured or responding. Use --djtest to compare actual generations.',file=out)
    else:print('  Diagnosis: AI DJ providers need setup.',file=out)
    print('  Text precedence: '+' → '.join(TEXT_PRECEDENCE_LABELS[x] for x in options['text_precedence'])+'; Ollama model: '+(options['ollama_model'] or '(automatic)'),file=out)
    print('  Current model folder setting: '+options['model_storage_path'],file=out)
    try:answer=input_fn('Run a real DJ text comparison with free providers and the current playlist? [y/N] ').strip().casefold()
    except (EOFError,KeyboardInterrupt):answer='n'
    if answer in ('y','yes'):
        try:run(app,[])
        except (OSError,ValueError,RuntimeError) as exc:print('Text comparison could not run: '+str(exc),file=out)
    try:answer=input_fn('Open the model download / comparison window to repair local voices or compare text models? [Y/n] ').strip().casefold()
    except (EOFError,KeyboardInterrupt):answer='n'
    if answer not in ('n','no'):
        env=os.environ.copy();env['PAFPLAYER_MODEL_ROOT']=str(root)
        try:
            import subprocess
            subprocess.Popen([sys.executable,'-B',str(Path(app.__file__).resolve()),'--models-window'],close_fds=False,env=env,creationflags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0))
            print('Opened the model manager. Downloading and moving models remain explicit actions there.',file=out,flush=True)
        except OSError as exc:print('Could not open model manager: '+str(exc),file=out)
    print('For model-by-model conversation results, run pafplayer --djtest. For Ollama troubleshooting, run pafplayer --ollamainstructions.',file=out)
    return 0


def model_heading(label, out):
    # DEC double-height lines are meaningful on terminals, but not in files or pipes.
    if not getattr(out,'isatty',lambda:False)():
        print(RED+label+RESET,file=out,flush=True);return
    columns=shutil.get_terminal_size((120,30)).columns
    for part in textwrap.wrap(label,width=max(8,(columns//2)-2)) or ['']:
        print('\033#3'+RED+part+RESET,file=out)
        print('\033#4'+RED+part+RESET,file=out)
    print('\033#5',end='',file=out,flush=True)


def print_track(item, out, prefix=''):
    artist=item.get('artist','')
    print(prefix+(CYAN+artist+RESET+' - ' if artist else '')+YELLOW+item['title']+RESET,file=out,flush=True)


def print_settings(opts, prompt, out):
    print('\nDJ test settings:',file=out)
    print('  Target commentary: approximately '+str(opts['seconds'])+' seconds (text only; no speech is generated in this test)',file=out)
    print('  Speakers: '+str(opts['speakers'])+'; cast: '+str(opts['women'])+' women, '+str(opts['men'])+' men; accent: '+opts['accent'],file=out)
    print('  DJ interval: '+str(opts['interval'])+' songs; history limit: '+str(opts['history'])+' songs',file=out)
    print('  Text precedence: '+' → '.join(TEXT_PRECEDENCE_LABELS[x] for x in opts['text_precedence'])+'; Ollama model: '+(opts['ollama_model'] or '(automatic)'),file=out)
    print('  Speech provider: '+opts['speech_provider']+'; OpenAI speech model: '+opts['speech_model'],file=out)
    print('  Configured OpenAI voice order: '+opts['voices'],file=out)
    print('  Configured Piper voices: '+(opts['piper_voices'].replace('\n',', ') or '(automatic)')+'; executable: '+(opts['piper_executable'] or '(automatic)'),file=out)
    print('  Prompt selection: '+opts['prompt_choice']+'; Gemini free tier confirmed: '+('yes' if opts['gemini_free_confirmed'] else 'no'),file=out)
    print('  DJ enabled: '+('yes' if opts['enabled'] else 'no')+'; sleep: '+opts['sleep_time']+'; wake: '+opts['wake_time']+'; sleep on lock: '+('yes' if opts['sleep_when_locked'] else 'no'),file=out)
    if opts['wake_time']=='sunrise':print('  Sunrise ZIP: '+opts['sunrise_zip'],file=out)
    print('  Actual instructions sent to each model:\n'+prompt,file=out)
    print('\nOptions: --include-paid includes the configured paid OpenAI model; --models opens model setup.',file=out)
    print('Connection help: pafplayer --ollamainstructions [model-name]',file=out,flush=True)


def sample_tracks(paths, count, rng=None):
    if not paths: raise ValueError('The playlist has no playable tracks.')
    rng=rng or random.SystemRandom()
    # A random choice per visit mirrors the player\'s true-random mode.
    return [Path(rng.choice(paths)) for _ in range(count+1)]


def describe_track(app,path,include_lyrics=True):
    try: tags=app.probe_audio_tags(path)
    except Exception: tags={}
    item={'artist':str(tags.get('Artist','') or ''),'title':str(tags.get('Song','') or path.stem)}
    if include_lyrics:
        try:
            cues=app.load_lyrics(path)
            lyric='\n'.join(str(cue[2]) for cue in cues if len(cue)>2 and str(cue[2]).strip())
            if lyric:item['lyrics']=lyric
        except Exception: pass
    return item


def available_models(dj, opts, include_paid=False):
    models=[];warnings=[]
    key=dj.provider_key('OPENROUTER_API_KEY')
    if key:
        models.extend([('OpenRouter: GPT-OSS 120B (free)','router','openai/gpt-oss-120b:free',key),('OpenRouter: free router','router','openrouter/free',key)])
    else:warnings.append('OpenRouter key missing; configure OPENROUTER_API_KEY to test its free models.')
    key=dj.provider_key('GEMINI_API_KEY') or dj.provider_key('GOOGLE_API_KEY')
    if key and opts['gemini_free_confirmed']: models.append(('Gemini Flash Lite (confirmed free tier)','gemini','',key))
    elif key:warnings.append('Gemini skipped: confirm its free tier in AI DJ settings before using it.')
    else:warnings.append('Gemini key missing; configure GEMINI_API_KEY to test Gemini.')
    key=dj.openai_key()
    if include_paid and key:models.append(('OpenAI: '+opts['text_model']+' (may incur charges)','openai',opts['text_model'],key))
    elif include_paid:warnings.append('OpenAI key missing; cannot test the paid OpenAI model.')
    elif key:warnings.append('Paid OpenAI model omitted; add --include-paid if you want to use API credits.')
    local,warning=ollama_models()
    if warning:warnings.append(warning)
    elif not local:
        manifests=model_directory()/'manifests'
        try:
            stored=[path for path in manifests.glob('*/*/*/*') if path.is_file()]
        except OSError:
            stored=[]
        if stored:
            warnings.append('Ollama is running, but its API lists zero models while files exist in '+str(manifests.parent)+'. Check the active server’s OLLAMA_MODELS setting and permissions; restart only after correcting the model-store setting.')
        else:
            warnings.append('No local model files were found in the expected store. Ollama API is responding with an empty catalog. If you want local models, use pafplayer --models → Text models; downloading GPT-OSS 120B needs about 65 GB. You already have Ollama running, so do not install it again.')

    for name in local:models.append(('Ollama: '+name,'ollama',name,''))
    if local and not any('gpt-oss:120b' in x for x in local):warnings.append('Local GPT-OSS 120B is not installed; --models can download it.')
    return models,warnings


def generate(dj, model, prompt, data, speakers):
    label,kind,name,key=model
    if kind=='router':return dj._chat_dialogue('https://openrouter.ai/api/v1/chat/completions',key,name,prompt,data,speakers)
    if kind=='gemini':return dj._gemini_dialogue(key,prompt,data,speakers)
    if kind=='ollama':
        value=dj.post_json('http://127.0.0.1:11434/api/chat',{'model':name,'stream':False,'options':{'num_ctx':4096},'messages':[{'role':'system','content':prompt},{'role':'user','content':data}]},timeout=600)
        return dj.parse_dialogue(value['message']['content'],speakers)
    value=dj.post_json('https://api.openai.com/v1/responses',{'model':name,'instructions':prompt,'input':data},{'Authorization':'Bearer '+key})
    text=''.join(p.get('text','') for item in value.get('output',[]) for p in item.get('content',[]) if p.get('type')=='output_text')
    return dj.parse_dialogue(text,speakers)


def run(app, args, out=None):
    from PAFPlayer_dj import settings, prepare_dialogue_request, TEXT_PRECEDENCE_LABELS
    import PAFPlayer_dj as dj
    out=out or sys.stdout
    include_paid='--include-paid' in args
    args=[x for x in args if x!='--include-paid']
    if len(args)>1 or any(x.startswith('--') for x in args):
        print(ERROR+'Usage: PAFPlayer.py --dj-test [playlist] [--include-paid]'+RESET,file=out);return 2
    try:
        paths=app.load_playlist(Path(args[0]),show_progress=False) if args else running_playlist(app)
        opts=settings(app.paf_workflows().settings.get('ai_dj',{}))
        chosen=sample_tracks(paths,opts['interval'])
        played=[describe_track(app,p) for p in chosen[:-1]]
        upcoming=describe_track(app,chosen[-1],include_lyrics=False)
        history=played[-opts['history']:]
        opts['_new_track_count']=len(history);opts['_upcoming_track']=upcoming
        prompt,data,_previous=prepare_dialogue_request(history,opts)
        print(YELLOW+'Songs simulated ('+str(len(played))+'):'+RESET,file=out,flush=True)
        for item in played:print_track(item,out)
        print_track(upcoming,out,prefix='Next: ')
        print_settings(opts,prompt,out)
        models,warnings=available_models(dj,opts,include_paid)
        for warning in warnings:print('⚠ '+warning,file=out,flush=True)
        if not models:print(ERROR+'No available text models to compare.'+RESET,file=out);return 1
        succeeded=0
        for model in models:
            print(file=out)
            model_heading(model[0],out)
            if model[1]=='ollama':print('Connection help: pafplayer --ollamainstructions '+model[2],file=out,flush=True)
            print('Generating…',file=out,flush=True)
            try:
                for speaker,text in generate(dj,model,prompt,data,opts['speakers']):
                    print(GREEN+str(speaker)+': '+text+RESET,file=out,flush=True)
                succeeded+=1
            except Exception as exc:
                # Avoid printing provider responses, URLs or credentials.
                status=getattr(exc,'code',None)
                print(ERROR+'⚠ Generation failed'+(' (HTTP '+str(status)+')' if status else ' ('+type(exc).__name__+')')+'. Check the provider, model availability, and connection.'+RESET,file=out,flush=True)
            print('─'*48,file=out,flush=True)
        return 0 if succeeded else 1
    except (ValueError,OSError) as exc:
        print(ERROR+'DJ test: '+str(exc)+RESET,file=out);return 2
