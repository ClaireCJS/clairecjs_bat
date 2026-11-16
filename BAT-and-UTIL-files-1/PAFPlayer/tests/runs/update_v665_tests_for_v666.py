from pathlib import Path
import datetime, hashlib, shutil

root = Path(__file__).resolve().parents[2]
def change(path, old, new):
    text = path.read_text(encoding='utf8')
    assert text.count(old) == 1
    original = path.read_bytes()
    name = path.name + datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
    backup = path.with_name(name); n = 0
    while backup.exists():
        n += 1; backup = path.with_name(name[:-4] + f' ({n}).bak')
    shutil.copy2(path, backup)
    assert hashlib.sha256(original).digest() == hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(text.replace(old, new, 1), encoding='utf8', newline='')
    archive = root/'backups'/backup.name; n = 0
    while archive.exists():
        n += 1; archive = root/'backups'/(backup.stem+f' ({n})'+backup.suffix)
    shutil.move(str(backup),str(archive))
change(root/'tests/test_v665_dj_sleep.py', "  self.assertFalse(c.start(True,current={'artist':'a','title':'b'}));self.assertIn('asleep',c.error)", "  self.assertFalse(c.start(False,current={'artist':'a','title':'b'}));self.assertIn('asleep',c.error)")
change(root/'tests/test_v665_sleep_transition.py', "c.configure({'sleep_when_locked':True});self.assertTrue(c.start(True,current={'artist':'a','title':'b'}));self.assertTrue(started.wait(1))", "c.configure({'sleep_when_locked':True,'enabled':True});c.history.append({'artist':'a','title':'b'});c.count=1;self.assertTrue(c.start(False));self.assertTrue(started.wait(1))")
print('Updated legacy sleep regression tests with verified backups.')
