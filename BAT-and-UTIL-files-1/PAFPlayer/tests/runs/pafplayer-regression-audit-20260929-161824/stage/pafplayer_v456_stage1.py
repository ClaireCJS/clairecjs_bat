from pathlib import Path
from pafplayer_v416_edit import ROOT, replace_file, sub

def edit(fn):
    path=ROOT/'PAFPlayer.py'
    raw=path.read_bytes(); s=raw.decode('utf-8').replace('\r\n','\n')
    result=fn(s); compile(result,str(path),'exec')
    replace_file(path,result.replace('\n','\r\n') if b'\r\n' in raw else result)

def change(s):
    s=sub(s,'2026-09-25-v455-web-tabs-beat-timing-and-control-polish','2026-09-25-v456-todo-workflows')
    s=sub(s,'"V455"','"V456"',2)
    s=sub(s,'    return Path(__file__).resolve().with_name(GLOBAL_CONFIG_DCC_FILENAME)', '''    canonical = Path(r"C:\BAT\PAFPlayer.py")
    return (canonical if canonical.is_file() else Path(__file__).resolve()).with_name(GLOBAL_CONFIG_DCC_FILENAME)''')
    s=sub(s,'def _global_config_backup_before_replacement(target: Path) -> None:', 'def _global_config_backup_before_replacement(target: Path) -> Path | None:')
    s=sub(s,'    if not backup.is_file() or backup.stat().st_size != target.stat().st_size:\n        raise OSError(f"Could not verify replacement backup: {backup}")', '''    if not backup.is_file() or hashlib.sha256(backup.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
        raise OSError(f"Could not verify replacement backup: {backup}")
    return backup''')
    s=sub(s,'def _global_config_write_json(path: Path, value: object) -> None:', 'def _global_config_write_json(path: Path, value: object) -> Path | None:')
    s=sub(s,'    _global_config_backup_before_replacement(path)\n    temporary = path.with_name', '    backup = _global_config_backup_before_replacement(path)\n    temporary = path.with_name')
    s=sub(s,'    os.replace(temporary, path)\n\n\ndef _global_config_read_json', '    os.replace(temporary, path)\n    return backup\n\n\ndef _global_config_read_json')
    s=sub(s,'        _global_config_write_json(target, snapshot)\n        return snapshot', '''        backup = _global_config_write_json(target, snapshot)
        return dict(snapshot, saved_path=str(target.resolve()), backup_path=str(backup.resolve()) if backup else None)''')
    s=sub(s,'                                "name": snapshot.get("profile_name", ""),\n                                "profiles":', '                                "name": snapshot.get("profile_name", ""),\n                                "saved_path": snapshot.get("saved_path"),\n                                "backup_path": snapshot.get("backup_path"),\n                                "profiles":')
    s=sub(s,"try{await globalConfigPost({op:'save',developer_choice:true});await refreshGlobalConfigList();globalConfigStatus('Saved Developer’s Choice to PAFPlayer.dcc.')}", "try{const result=await globalConfigPost({op:'save',developer_choice:true});await refreshGlobalConfigList();globalConfigStatus('Saved Developer’s Choice to '+result.saved_path+'. '+(result.backup_path?'Created and verified backup: '+result.backup_path:'No previous file needed a backup.'))}")
    s=sub(s,'    payload = b"\\x1b[0m\\x1b(B\\x1b[?7h\\x1b[?25h"', '    payload = b"\\x1b[0m\\x1b(B\\x1b[?7h\\x1b[?25h\\x1b]112\\x07"')
    s=sub(s,'</style>', '''.emojimax-token{display:inline-block;position:relative;white-space:nowrap;vertical-align:baseline}
.teeny-solutions .emojimax-token::after{content:attr(data-solution);position:absolute;left:50%;top:100%;transform:translateX(-50%);font:var(--teeny-size,20%) sans-serif;line-height:1;white-space:nowrap;color:currentColor;text-shadow:none;pointer-events:none}
#lyric.teeny-solutions{line-height:calc(1.1 + var(--teeny-ratio,.2))!important;padding-bottom:calc(1em * var(--teeny-ratio,.2))!important}
</style>''')
    s=sub(s,'    <label class="tiny-toggle" title="Display-only: restore recognized', '''    <label class="tiny-toggle" id="teenyToggleLabel"><input type="checkbox" id="teenySolutions">Show teeny solutions (experimental)</label>
    <label class="tiny-toggle" id="teenySizeLabel" hidden>Teeny solution size <input type="range" id="teenySize" min="5" max="150" value="20"><output id="teenySizeValue">20%</output></label>
    <label class="tiny-toggle" title="Display-only: restore recognized''')
    s=sub(s,"function updateWebEmojimaxToggle(){const b=document.getElementById('webEmojimaxToggle');if(b)b.checked=!!webKaraokeSettings.emojimax}", '''function updateTeenySolutions(){
 const enabled=!!webKaraokeSettings.emojimax,shown=enabled&&!!webKaraokeSettings.teenySolutions;
 const size=Math.max(5,Math.min(150,Number(webKaraokeSettings.teenySize??20)));
 const host=document.getElementById('lyric');host.classList.toggle('teeny-solutions',shown);host.style.setProperty('--teeny-size',size+'%');host.style.setProperty('--teeny-ratio',String(size/100));
 document.getElementById('teenyToggleLabel').hidden=!enabled;document.getElementById('teenySolutions').checked=shown;
 document.getElementById('teenySizeLabel').hidden=!shown;document.getElementById('teenySize').value=size;document.getElementById('teenySizeValue').textContent=size+'%';
}
function updateWebEmojimaxToggle(){const b=document.getElementById('webEmojimaxToggle');if(b)b.checked=!!webKaraokeSettings.emojimax;updateTeenySolutions()}''')
    s=sub(s,"  chars.forEach((ch,index)=>{const span=", "  let solutionGroup=null,previousAnswer=null;\n  chars.forEach((ch,index)=>{const span=")
    s=sub(s,"}host.appendChild(span);lyricSpans.push(span)});", "}if(answer){if(!solutionGroup||answer!==previousAnswer){solutionGroup=document.createElement('span');solutionGroup.className='emojimax-token';solutionGroup.dataset.solution=answer;host.appendChild(solutionGroup)}solutionGroup.appendChild(span)}else{solutionGroup=null;host.appendChild(span)}previousAnswer=answer;lyricSpans.push(span)});updateTeenySolutions();")
    s=sub(s,"  document.getElementById('editLyrButton').onclick=", "  document.getElementById('teenySolutions').onchange=e=>{webKaraokeSettings.teenySolutions=e.target.checked;saveWebKaraokeSettings();updateTeenySolutions();updateKaraokeReservation()};document.getElementById('teenySize').oninput=e=>{webKaraokeSettings.teenySize=Number(e.target.value);saveWebKaraokeSettings();updateTeenySolutions();updateKaraokeReservation()};\n  document.getElementById('editLyrButton').onclick=")
    return s

if __name__=='__main__': edit(change)
