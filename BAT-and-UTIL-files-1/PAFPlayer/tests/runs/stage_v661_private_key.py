from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=(root/'src/PAFPlayer_dj.py').read_text(encoding='utf8')
anchor='def dialogue(history, opts):\n'
helper='''def dj_key_file():
    """Claire's local secrets file, when available; no bundled credentials."""
    return Path(r'C:\\BAT\\private.env') if os.name == 'nt' else None


def openai_key():
    """Prefer the DJ's private-file key; fall back to the process environment."""
    path = dj_key_file()
    if path is not None:
        try:
            with path.open('r', encoding='utf-8-sig') as stream:
                for line in stream:
                    match = re.match(r'^\\s*(?:export\\s+|set\\s+)?OPENAI_API_KEY\\s*=\\s*(.*?)\\s*$', line)
                    if match:
                        value = match.group(1).strip().strip('"').strip("'")
                        if re.fullmatch(r'sk-[A-Za-z0-9_-]{20,}', value): return value
        except (OSError, UnicodeError):
            pass
    return os.environ.get('OPENAI_API_KEY', '')


'''
assert source.count(anchor)==1;source=source.replace(anchor,helper+anchor,1)
old="    key=os.environ.get('OPENAI_API_KEY',''); warning=''";assert source.count(old)==1;source=source.replace(old,"    key=openai_key(); warning=''",1)
old="    key=os.environ.get('OPENAI_API_KEY','')\n    if not key: raise RuntimeError('OpenAI key unavailable')";assert source.count(old)==1;source=source.replace(old,"    key=openai_key()\n    if not key: raise RuntimeError('OpenAI key unavailable')",1)
compile(source,'candidate','exec');p=root/'tests/runs/PAFPlayer_dj_v661_candidate.py';assert not p.exists();p.write_text(source,encoding='utf8');print(p)
