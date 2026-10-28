from pafplayer_v456_stage1 import edit
from pafplayer_v416_edit import sub

def change(s):
    s=sub(s,"volume.style.width='110px'","volume.style.width='220px'")
    s=sub(s,'grid-template-rows:var(--paf-top-height,54vh)','grid-template-rows:var(--paf-top-height,56vh)',2)
    # Python's HTML is raw text: two JS backslashes were producing literal \n.
    start=s.index('  const orderTip=');end=s.index('\n',start)
    s=s[:start]+s[start:end].replace('\\\\n','\\n\\n')+s[end:]
    s=s.replace('font-size:.78rem;line-height:1.25;white-space:normal;box-shadow:', 'font-size:.78rem;line-height:1.25;white-space:pre-line;box-shadow:')
    s=s.replace('border_color = "#909090" if active else art_transparent','border_color = "#909090" if active else "#626262"',1)
    s=sub(s,'border_frame.configure(background=art_transparent)','border_frame.configure(background="#626262")')
    s=sub(s,'"""Show exactly one OUTER five-pixel art border only while focused.', '"""Keep one outer five-pixel art border visible at every focus state.')
    s=sub(s,'"""FocusOut itself removes the five-pixel border immediately."""','"""Dim the permanent border immediately when focus leaves."""')
    # Integers in milliseconds follow existing web validation and registry schema.
    s=sub(s,'    song_throb_seconds = SONG_RAINBOW_THROB_SECONDS\n    artist_throb_seconds = ARTIST_RAINBOW_THROB_SECONDS', '    throb_settings = load_player_settings()\n    song_throb_seconds = max(100,min(60000,throb_settings.get("SongThrobMs",round(SONG_RAINBOW_THROB_SECONDS*1000))))/1000\n    artist_throb_seconds = max(100,min(60000,throb_settings.get("ArtistThrobMs",round(ARTIST_RAINBOW_THROB_SECONDS*1000))))/1000')
    pos=s.index('PLAYER_SETTING_DEFAULTS: dict[str, int] = {')+len('PLAYER_SETTING_DEFAULTS: dict[str, int] = {')
    s=s[:pos]+'\n    "SongThrobMs": round(SONG_RAINBOW_THROB_SECONDS*1000),\n    "ArtistThrobMs": round(ARTIST_RAINBOW_THROB_SECONDS*1000),'+s[pos:]
    s=sub(s,'        "sliders": [','''        "sliders": [
            {"key":"artist_throb_ms","label":"Act / artist throb period","min":100,"max":60000,"step":1,"suffix":" ms","numeric":True,"theme":"karaoke"},
            {"key":"song_throb_ms","label":"Song-title throb period","min":100,"max":60000,"step":1,"suffix":" ms","numeric":True,"theme":"karaoke"},''')
    s=sub(s,'    ranges = {\n        "visualizer_mode"', '    ranges = {\n        "artist_throb_ms": (100,60000),\n        "song_throb_ms": (100,60000),\n        "visualizer_mode"')
    s=sub(s,'        nonlocal volume, balance, color_notice_until, processing_notice_until', '        nonlocal artist_throb_seconds, song_throb_seconds\n        nonlocal volume, balance, color_notice_until, processing_notice_until')
    s=sub(s,'        elif key == "karaoke_offset_delta":','''        elif key in {"artist_throb_ms","song_throb_ms"}:
            value=max(100,min(60000,value))
            if key=="artist_throb_ms": artist_throb_seconds=value/1000
            else: song_throb_seconds=value/1000
            save_player_setting_value("ArtistThrobMs" if key=="artist_throb_ms" else "SongThrobMs",value)
            if web_server is not None: web_server.publish(**{key:value})
        elif key == "karaoke_offset_delta":''')
    s=sub(s,'                        artwork_seam_strategy=ARTWORK_SEAM_STRATEGY,','                        artist_throb_ms=round(artist_throb_seconds*1000), song_throb_ms=round(song_throb_seconds*1000),\n                        artwork_seam_strategy=ARTWORK_SEAM_STRATEGY,')
    s=sub(s,"    else if(item.key==='artwork_seam_strategy')", "    else if(['artist_throb_ms','song_throb_ms'].includes(item.key)) host=karaoke;\n    else if(item.key==='artwork_seam_strategy')")
    s=sub(s,'  wrap.append(label,input);return wrap;','''  wrap.append(label,input);
  if(item.numeric){const number=document.createElement('input');number.type='number';number.id='num-'+item.key;number.min=item.min;number.max=item.max;number.step=item.step;number.style.width='100px';number.setAttribute('aria-label',item.label+' numeric value');
   const oldInput=input.oninput;input.oninput=()=>{number.value=input.value;oldInput()};
   number.onchange=()=>{const n=Number(number.value);if(!Number.isFinite(n)){number.value=input.value;return}input.value=String(Math.max(item.min,Math.min(item.max,Math.round(n))));number.value=input.value;input.oninput()};wrap.appendChild(number)}return wrap;''')
    s=sub(s,"const wantedLabel=sliderDisplayLabel(item,s[item.key]);", "const number=document.getElementById('num-'+item.key);if(number&&document.activeElement!==number)number.value=wanted;const wantedLabel=sliderDisplayLabel(item,s[item.key]);")
    return s

if __name__=='__main__':edit(change)
