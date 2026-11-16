from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
 while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
voice=(root/'src/PAFPlayer_voice_models.py').read_text(encoding='utf8');compile(voice,'voice-models','exec')
p=root/'PAFPlayer.py';s=p.read_text(encoding='utf8')
anchor='class _PAFBundledFeatures(_paf_import_abc.MetaPathFinder, _paf_import_abc.Loader):'
s=once(s,anchor,"_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = "+repr(voice)+'\n\n'+anchor)
s=once(s,'{"--readiness-check", "--readyness-check", "--install", "--version", "--which-script", "--help", "--usage", "--unit-tests", "-t"}', '{"--readiness-check", "--readyness-check", "--install", "--version", "--which-script", "--help", "--usage", "--unit-tests", "-t", "--dj", "--models", "--model", "--install-models"}')
anchor='''    arguments = list(sys.argv[1:] if argv is None else argv)
    installed_child = bool(arguments[:1] == ["--bootstrap-installed"])'''
new='''    arguments = list(sys.argv[1:] if argv is None else argv)
    model_flags = {"--dj", "--models", "--model", "--install-models"}
    if any(arg in model_flags for arg in arguments):
        if len(arguments) != 1:
            print("The voice model manager option must be used by itself.", file=sys.stderr)
            return 2
        try:
            from PAFPlayer_voice_models import launch_window
            return launch_window()
        except Exception as exc:
            print("Could not open voice model manager: " + str(exc), file=sys.stderr)
            return 2
    installed_child = bool(arguments[:1] == ["--bootstrap-installed"])'''
s=once(s,anchor,new)
anchor='''    if launch:
        try:
            subprocess.Popen([sys.executable, "-B", str(installed), "--bootstrap-installed", *arguments],'''
new='''    if launch and not arguments[:1] == ["--tray-only"] and sys.stdin is not None and sys.stdin.isatty():
        print("\\nOptional voice models: download and compare free local DJ voices in a separate window.")
        try:
            answer = input("Open voice model setup now? [y/N] ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            answer = ''
        if answer in {'y', 'yes'}:
            try:
                subprocess.Popen([sys.executable, '-B', str(installed), '--models'], close_fds=True,
                                 creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0))
                print('Voice model setup opened separately; player startup will continue.')
            except OSError as exc:
                print('Voice model setup could not open: '+str(exc), file=sys.stderr)
    if launch:
        try:
            subprocess.Popen([sys.executable, "-B", str(installed), "--bootstrap-installed", *arguments],'''
s=once(s,anchor,new)
anchor='        usage_line("--install [PLAYBACK ARGS]", "stage a verified copy in a new folder, check it, then launch it")'
s=once(s,anchor,anchor+'\n        usage_line("--models / --model / --install-models / --dj", "open a separate local voice model download and comparison window")')
s=once(s,"'2026-11-12-v672-piper-startup'","'2026-11-12-v673-voice-model-manager'")
s=once(s,"PROGRAM_VERSION                = 'V672'","PROGRAM_VERSION                = 'V673'")
s=once(s,"PROGRAM_RELEASE_LABEL          = 'V672'","PROGRAM_RELEASE_LABEL          = 'V673'");compile(s,str(p),'exec')
release=root/'releases/PAFPlayer_v673_voice_models.py';notes=root/'releases/PAFPlayer_v673_voice_models_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8')
docs=once(docs,'Current release: **V672** — automatic Piper voice preparation and visible setup.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v672_piper_startup_release_notes.md).','Current release: **V673** — local voice model download and comparison window.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v673_voice_models_release_notes.md).')
anchor='## AI Podcaster / DJ';docs=once(docs,anchor,'''## Local voice model setup and comparison

Run `python PAFPlayer.py --models` (also `--model`, `--install-models`, or `--dj`) to open a separate window, including while another player is running. Choose Piper, Kokoro 82M, Qwen3-TTS 0.6B and/or Qwen3-TTS 1.7B, then download the selected models or compare installed models. Initial interactive installation offers this as a skippable separate step. Downloads and their Python dependencies can require several GB. Models use isolated environments under `%LOCALAPPDATA%\\PAFPlayer\\support\\voice-models`; existing Piper installations are reused. The comparison creates matching speech samples, per-sample generation timings and `results.json` in a new comparison folder, then opens that folder for listening. No model is downloaded without selecting it and clicking Download. The comparison does not automatically switch the DJ speech provider; PAFPlayer's DJ currently supports Piper and OpenAI speech. Qwen can use CUDA if its installed PyTorch supports it; otherwise CPU generation may be slow. Voice quality and speed should be judged on the actual machine.

'''+anchor)
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V673 — November 12, 2026\n\nAdd an independent local voice model download and comparison window, with a skippable first-install option and four command-line aliases. [Release notes](../releases/PAFPlayer_v673_voice_models_release_notes.md).\n')
replace(p,s,root/'releases');release.write_text(s,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V673 — Local voice models\n\nThe independent model window downloads selected Piper, Kokoro, and Qwen models and creates comparable local speech samples and timing results. `--dj`, `--models`, `--model`, and `--install-models` open the window. Interactive first-install setup offers it as a skippable step. Model selection for the existing DJ remains Piper or OpenAI; comparison does not change playback settings.\n',encoding='utf8')
print('Published V673 workspace player with verified backups.')
