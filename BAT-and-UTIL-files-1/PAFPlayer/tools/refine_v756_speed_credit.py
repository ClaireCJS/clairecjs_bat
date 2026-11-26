from pathlib import Path
import datetime,hashlib,shutil
root=Path.cwd()
for raw,folder in [('PAFPlayer.py','releases'),('tests/test_v756_speed_credit.py','tests/backups')]:
 p=root/raw;base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest();dest=root/folder/b.name
 while dest.exists():n+=1;dest=root/folder/(base+f' ({n}).bak')
 b.rename(dest)
 s=p.read_text(encoding='utf-8-sig')
 if raw=='PAFPlayer.py':
  old='''        nonlocal last_drcs_position, last_lyric_index, last_sixel_refresh
        if simple_mode:
            return
'''
  new='''        nonlocal last_drcs_position, last_lyric_index, last_sixel_refresh
        nonlocal status_rendered, last_console_cue_key
        if simple_mode:
            # Only repaint the inline player's own reserved rows after a menu.
            clear_region(HEADER_ROW, max(1, DRCS_ROW - HEADER_ROW))
            status_rendered = False
            last_lyric_index = None
            last_console_cue_key = None
            show_status(current_position, indicator_text)
            return
'''
  assert s.count(old)==1;s=s.replace(old,new,1);compile(s,str(p),'exec')
 else:
  s=s.replace("        self.assertTrue(any('1.333×' in text for text in output))", "        last_menu=max(i for i,text in enumerate(output) if 'Pending: 1.333' in text)\n        self.assertTrue(any('\\033[2K' in text for text in output[last_menu+1:]))\n        self.assertFalse(any('\\033[2J' in text for text in output))\n        self.assertEqual('1.333×',app.format_speed(custom[0]))")
 p.write_text(s,encoding='utf-8')
print('Fixed inline menu repaint without full-screen clearing.')
