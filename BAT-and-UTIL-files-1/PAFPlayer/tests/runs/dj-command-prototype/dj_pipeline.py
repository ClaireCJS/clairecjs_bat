"""Staged synthesis pipeline. All calls run on a background worker."""
import subprocess,tempfile
from pathlib import Path
from dj_backend import text_openai,text_ollama,realtime_speech,create_name

OPENAI_VOICES=('marin','cedar','coral','sage','shimmer','alloy','ash','ballad','echo','fable','nova','onyx','verse')
def synthesize(history,settings,*,ollama_model,piper_command,piper_models,progress=lambda x:None,
               openai_text=text_openai,ollama_text=text_ollama,openai_voice=realtime_speech,run=subprocess.run):
    warnings=[];progress('Writing dialogue')
    try: dialogue=openai_text(history,settings)
    except Exception as exc:
        warnings.append('OpenAI text unavailable: '+type(exc).__name__)
        progress('Writing dialogue with local Ollama')
        dialogue=ollama_text(history,settings,ollama_model)
    if not dialogue:raise RuntimeError('No dialogue')
    output_dir=Path(tempfile.mkdtemp(prefix='PAFPlayer commentary '))
    files=[];local_only=False
    for index,(speaker,line) in enumerate(dialogue):
        progress(f'Synthesizing speaker {index+1} of {len(dialogue)}')
        last=history[-1];path=create_name(output_dir,last.get('artist',''),last.get('title',''))
        if not local_only:
            try:openai_voice(line,OPENAI_VOICES[(speaker-1)%len(OPENAI_VOICES)],path)
            except Exception as exc:
                warnings.append('OpenAI speech unavailable: '+type(exc).__name__);local_only=True
        if local_only:
            if not piper_command or not piper_models:raise RuntimeError('Local Piper speech engine or voice models not configured')
            # A failed cloud write can leave a file: choose a new name, never overwrite.
            path=create_name(output_dir,last.get('artist',''),last.get('title',''))
            model=piper_models[(speaker-1)%len(piper_models)]
            result=run([*piper_command,'-m',str(model),'-f',str(path),'--',line],capture_output=True,timeout=120)
            if result.returncode or not path.is_file() or path.stat().st_size<=44:raise RuntimeError('Local Piper synthesis failed')
        files.append(str(path))
    return {'files':files,'warnings':warnings}
